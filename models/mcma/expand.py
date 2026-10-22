"""
Expansion stage of the Pareto-front representation (workflow stage 7, 'expand').

Starts from the solutions stored by ParRep after the cube/SPFR stage and adds Pareto solutions
until the whole Pareto front is covered with the resolution rho (L-inf, achievement scale),
without knowing the front:

* boundary step   : one probe at distance rho outside every non-final facet of the convex hull
                    of the projected PFR; the result is added if it extends the hull by more than
                    expandMargin * rho, otherwise the facet is final;
* interior step   : Delaunay triangulation of the projected PFR; every simplex whose bound
                    beta = dist(F, E) + (U - flat) exceeds rho is probed at its worst point;
* gap repair      : every solution gets a neighbour within rho.

A probe is one ordinary pyMCMA iteration: all criteria active, aspiration and reservation on the
diagonal through the probed location w (a - r proportional to 1), inside the box [N', U] with the
lowered Nadir N' = N - expandLow * (U - N) (used only by the PWL of stage 7).

Variant with dual values: the duals of the link constraints (mc_part.xLink, read by the driver)
give a supporting hyperplane at every probe; the upper envelope U is the minimum of these planes.
Variant without dual values: U is built from the secant planes of all known solutions K; a probe
whose band exceeds rho/2 is a 'shape' probe (kept in K only).  With expandDuals: auto the variant
with duals is used while the solver returns consistent dual values.

Ray-structured variant (expandMode: rays, three criteria): the diagonal probes are used only to discover the
outline of the PF outside the region covered by the previous stages (discovery step: one probe far outside
every edge of the simplified hull of the projected PFR, and a probe at distance rho if the far one does not
extend the hull, then a verification round with probes at distance rho along every edge); the regions found
in this way (pockets, any number of new vertices) are filled by rays of cuboids as in the grid option of the
SPFR: first the chains bounding each pocket, then sweep rays between the two chains (every solution of both
chains is paired with the solution of the other chain at the nearest relative arc length), see expand_rays.py.
The certificate-driven interior step (expandCert: True) is then used only as a final check; the gap repair
runs in both cases.  Pairs of neighbours on rays left farther apart than rho are listed in expandSummary.txt.
A solution worse than the Nadir updates it only if it is not dominated by the PFR (weakly efficient probe
results are ignored), so the Nadir approximation is never worse than the true Nadir.

Configuration keys (cfg.yml, all optional):
    expand: True             run the stage
    expandMode: cert         cert (certificate-driven, default) | rays (ray-structured, three criteria)
    expandCert: True         rays mode: final check by the certificate-driven interior step
    expandCheck: 2           rays mode: spacing (multiple of rho) of the probes checking the hull edges; a part
                             of the PF protruding over an edge and narrower than this spacing may be missed
    expandBoundary: mid      cert mode: mid (one probe per hull facet) | sweep (experimental: probes along
                             the whole facet, expandCheck * rho apart, as in the verification round of rays)
    expandRho: <float>       resolution (default: ParRep cube min_size)
    expandDuals: auto        auto | True | False
    expandBudget: 2000       max number of probes (+ 400 for the gap repair)
    expandLow: 1.0           lowering of the Nadir for the A/R pairs
    expandMargin: 0.25       boundary threshold (fraction of rho)
"""
from collections import deque
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from . import expand_geom as eg
from . import expand_rays as er
from .cube import aCube


# noinspection SpellCheckingInspection
class ParExpand:
    def __init__(self, wflow):
        self.wflow = wflow
        self.mc = wflow.mc
        self.cfg = wflow.cfg
        self.par_rep = wflow.par_rep
        self.verb = self.mc.verb
        opt = self.mc.opt
        self.rho = float(opt('expandRho', self.par_rep.cubes.min_size))
        duals = opt('expandDuals', 'auto')
        self.duals_mode = 'auto' if str(duals).lower() == 'auto' else bool(duals)
        self.use_duals = self.duals_mode is not False
        self.budget = int(opt('expandBudget', 2000))
        self.gap_budget = 400
        self.low = float(opt('expandLow', 1.0))
        self.bmarg = float(opt('expandMargin', 0.25))
        self.shape_frac = 0.5           # band > shape_frac * rho -> shape probe (variant without duals)
        self.tol_new = 1.0              # pyMCMA treats solutions closer than 1.0 (L-inf) as duplicates
        self.tol_K = 0.05               # known points closer than this (achievements) are repetitions
        self.k = self.mc.n_crit
        self.mult = np.array([cr.mult for cr in self.mc.cr], float)
        self.Q = eg.basis(self.k)
        dim = self.k - 1
        self.G = eg.bary_grid(dim, 12)
        self.G2 = eg.bary_grid(dim, 60 if dim <= 2 else 16)
        # state
        self.K = [(self.z(s.vals), s.itr_id) for s in self.par_rep.sols]   # known front points (raw z, itr)
        self.tang = []                  # supporting hyperplanes mu.z <= beta (raw, maximization-oriented)
        self.bad_duals = 0
        self.final, self.dead, self.stuck = set(), set(), set()
        self.queue = deque()
        self.pending = None
        self.phase = 'boundary'
        self.rounds = 0
        self.n_probe = 0
        self.n0 = 0
        self.round_probes = 0
        self.scale = None
        self.n_nadir = 0
        self.n_nadir_skip = 0            # Nadir updates refused: the solution is dominated by the PFR
        self.log = []
        self.stats = dict(boundary=0, interior=0, shape=0, coverage=0, gap=0, discover=0, ray=0)
        self.added = dict(boundary=0, interior=0, coverage=0, gap=0, promoted=0, discover=0, ray=0)
        self.tangent_only = 0
        # ray-structured variant
        self.mode = str(opt('expandMode', 'cert')).lower()
        if self.mode == 'rays' and self.k != 3:
            print(f'Expansion: expandMode rays is implemented for three criteria only ({self.k} defined); '
                  f'using expandMode cert.')
            self.mode = 'cert'
        self.cert_net = bool(opt('expandCert', True))
        self.check = float(opt('expandCheck', 2.0))     # spacing (in rho) of the probes checking the hull edges
        # cert mode, experimental (ablation): boundary step with probes along the whole facet, expandCheck*rho apart
        self.bnd_sweep = str(opt('expandBoundary', 'mid')).lower() == 'sweep'
        self.bnd_left = {}
        self.start_ids = {s.itr_id for s in self.par_rep.sols}     # solutions defining the old hull H0
        self.disc_final = set()         # directed hull edges (sol-id pairs) without an extension
        self.disc_left = {}             # hull edge -> number of its near probes not processed yet
        self.far_done = set()           # hull edges whose far probe did not extend the hull
        self.disc_level = 'far'         # far rounds until the hull is stable, then a near (verification) round
        self.disc_round = 0
        self.round_added = 0
        self.pockets = []               # dicts: C0 (old chain), C1 (new chain): lists of sol ids
        self.rays = {}                  # frozenset(anchor ids) -> dict(id, a, b, kind, members)
        self.ray_done = set()           # pairs of solutions already used for a cuboid
        self.pending_fixed = False      # the current probe fixes a criterion (degenerated cuboid edge)
        if self.mode == 'rays':
            self.phase = 'discover'
        self.rescale()
        self.par_rep.cur_cube = None
        print(f'\nExpansion stage: mode = {self.mode}, rho = {self.rho}, duals = {self.duals_mode}, '
              f'budget = {self.budget}, {len(self.par_rep.sols)} solutions from the previous stages. ============')

    # ------------------------------------------------------------------------- scale and data
    def z(self, vals):
        return self.mult * np.asarray(vals, float)

    def rescale(self):
        """Snapshot of the current Utopia/Nadir (maximization-oriented); True if changed."""
        u = self.mult * np.array([cr.utopia for cr in self.mc.cr], float)
        n = self.mult * np.array([cr.nadir for cr in self.mc.cr], float)
        changed = self.scale is not None and (np.any(np.abs(u - self.scale[0]) > 1e-12 * (1 + np.abs(u)))
                                              or np.any(np.abs(n - self.scale[1]) > 1e-12 * (1 + np.abs(n))))
        self.scale = (u, n)
        return changed

    def ach(self, Z):
        return eg.to_ach(Z, *self.scale)

    def E_raw(self):
        return np.array([self.z(s.vals) for s in self.par_rep.sols])

    def K_raw(self):
        return np.array([z for z, _ in self.K])

    def tangents_ach(self):
        """Tangents in achievements of the current snapshot: lam.y <= b."""
        if not self.tang:
            return np.zeros((0, self.k)), np.zeros(0)
        u, n = self.scale
        TL = np.array([mu * (u - n) / 100.0 for mu, _ in self.tang])
        TB = np.array([beta - mu @ n for mu, beta in self.tang])
        return TL, TB

    @staticmethod
    def key(Zs):
        return tuple(sorted(tuple(np.round(z, 9)) for z in Zs))

    def want_duals(self):
        return self.use_duals

    # ------------------------------------------------------------------------- Nadir update
    def upd_nadir(self):
        """Called by Report.itr() when a stage-7 solution is worse than the current Nadir:
        update the Nadir without restarting the analysis, rescale, recompute achievements."""
        if self.dominated_by_pfr([cr.val for cr in self.mc.cr]):
            self.n_nadir_skip += 1
            print('Expansion: solution worse than the Nadir is dominated by the PFR (weakly efficient); '
                  'the Nadir is not updated.')
            return False
        changed = self.wflow.payoff.update(7)
        if changed:
            self.n_nadir += 1
            self.mc.scale()
            for s in self.par_rep.sols + self.par_rep.clSols:
                s.a_vals = [cr.val2ach(v, warn=False) for cr, v in zip(self.mc.cr, s.vals)]
            print('Expansion: Nadir updated without restart: ' +
                  ', '.join(f'{cr.name} {cr.nadir:.4e}' for cr in self.mc.cr))
        return changed

    def dominated_by_pfr(self, vals):
        """True if a PFR solution is not worse than vals in any criterion and better in at least one (with a
        relative tolerance). Such a (weakly efficient) probe result must not move the Nadir: the Nadir
        approximation is then computed only from Pareto solutions and is never worse than the true Nadir."""
        tol = [1e-6 * max(abs(cr.utopia - cr.nadir), 1e-12) for cr in self.mc.cr]
        for s in self.par_rep.sols:
            d = [cr.mult * (sv - v) for cr, sv, v in zip(self.mc.cr, s.vals, vals)]
            if all(di >= -t for di, t in zip(d, tol)) and any(di > t for di, t in zip(d, tol)):
                return True
        return False

    # ------------------------------------------------------------------------- preferences
    def pref(self):
        """Entry point of an iteration of stage 7: set the A/R of the next probe."""
        if self.pending is not None:        # the previous probe was not solved
            it = self.pending
            if it['purpose'] in ('interior', 'shape', 'coverage'):
                self.dead.add(it['key'])
            elif it['purpose'] == 'boundary':
                self.boundary_done(it['key'])
            elif it['purpose'] == 'gap':
                self.stuck.add(it['key'])
            elif it['purpose'] == 'discover':
                if it['level'] == 'far':
                    self.far_done.add(it['key'])
                else:
                    self.disc_left[it['key']] -= 1
                    if self.disc_left[it['key']] <= 0:
                        self.disc_final.add(it['key'])
            elif it['purpose'] == 'ray':
                self.ray_done.add(it['key'])
            self.pending = None
        item = self.next_item()
        if item is None:
            self.finish()
            self.wflow.cur_stage = 6
            return
        self.pending = item
        if item['purpose'] == 'ray':
            self.set_cube(item)
        else:
            self.pending_fixed = False
            self.set_ar(item['w'])
        self.n_probe += 1
        self.round_probes += 1
        self.stats[item['purpose']] += 1

    def set_ar(self, w):
        """A/R on the diagonal through w (achievements of the snapshot), inside [N', U]."""
        u, n = self.scale
        lo, hi = -100.0 * self.low, 100.0
        c = w @ self.Q
        spread = c.max() - c.min()
        if spread > hi - lo - 1.0:          # the diagonal misses the box: move w towards the centre
            c = c * (hi - lo - 1.0) / spread
        t_r = np.max(lo - c)
        t_a = np.min(hi - c)
        a, r = c + t_a, c + t_r
        self.pending_c = c
        for i, cr in enumerate(self.mc.cr):
            cr.is_active = True
            cr.is_fixed = False
            cr.is_ignored = None
            cr.asp = self.mult[i] * eg.from_ach(a[i], u[i], n[i])
            cr.res = self.mult[i] * eg.from_ach(r[i], u[i], n[i])
            cr.nadir_pwl = cr.nadir - cr.mult * self.low * abs(cr.utopia - cr.nadir)   # N' for the PWL
        if self.verb > 1:
            print(f'Expansion probe ({self.pending["purpose"] if self.pending else ""}) at w = {np.round(w, 2)}: '
                  f'A = {np.round(a, 1)}, R = {np.round(r, 1)}')

    def set_cube(self, item):
        """A/R of the cuboid defined by a pair of neighbour solutions of a ray (as in the grid option)."""
        s1 = self.par_rep.get(item['s'][0])
        s2 = self.par_rep.get(item['s'][1])
        for cr in self.mc.cr:
            cr.nadir_pwl = None         # the cuboid is inside [N, U]: no lowered Nadir needed
            cr.is_ignored = None
        cube = aCube(self.mc, s1, s2)
        cube.setAR()
        self.pending_fixed = any(cr.is_fixed for cr in self.mc.cr)
        if self.verb > 1:
            print(f'Expansion probe (ray {item["ray"]}): cuboid of solutions {item["s"]}, size {cube.size:.2f}')

    # ------------------------------------------------------------------------- planning
    def next_item(self):
        if self.mode == 'rays':
            return self.next_item_rays()
        while True:
            if self.n_probe >= self.budget + self.gap_budget:
                return None
            if self.queue:
                item = self.queue.popleft()
                if self.still_needed(item):
                    return item
                continue
            if self.n_probe >= self.budget and self.phase not in ('gap', 'done'):
                print(f'Expansion: probe budget {self.budget} reached; proceeding to the gap repair.')
                self.phase = 'gap'
            if self.phase == 'boundary':
                self.rounds += 1
                self.rescale()
                self.n0 = len(self.par_rep.sols)
                self.round_probes = 0
                self.queue.extend(self.plan_boundary())
                self.phase = 'after_boundary'
                continue
            if self.phase == 'after_boundary':
                if self.rescale():
                    self.dead = set()
                    self.phase = 'boundary'
                    continue
                self.phase = 'interior'
            if self.phase == 'interior':
                items, done = self.plan_interior()
                if done or (not items and self.round_probes == 0 and len(self.par_rep.sols) == self.n0):
                    self.phase = 'gap'
                    continue
                self.queue.extend(items)
                self.phase = 'after_interior'
                continue
            if self.phase == 'after_interior':
                if self.round_probes == 0 and len(self.par_rep.sols) == self.n0:
                    self.phase = 'gap'          # nothing could be probed in this round
                else:
                    self.phase = 'boundary'
                continue
            if self.phase == 'gap':
                self.rescale()
                item = self.plan_gap()
                if item is not None:
                    return item
                self.phase = 'done'
            return None

    def plan_boundary(self):
        Z = self.E_raw()
        Y = self.ach(Z)
        W = Y @ self.Q.T
        items = []
        for simp, nrm, off in eg.hull_facets(W):
            key = self.key(Z[list(simp)])
            if key in self.final:
                continue
            if self.bnd_sweep and W.shape[1] == 2:     # experimental: probes along the whole facet (as near rounds)
                pa, pb = W[simp[0]], W[simp[1]]
                n = max(1, int(np.ceil(np.linalg.norm(pb - pa) / (self.check * self.rho))))
                self.bnd_left[key] = n
                items += [dict(purpose='boundary', w=pa + (j + 0.5) / n * (pb - pa) + self.rho * nrm, key=key,
                               nrm=nrm, off=off) for j in range(n)]
                continue
            mid = W[list(simp)].mean(axis=0)
            items.append(dict(purpose='boundary', w=mid + self.rho * nrm, key=key, nrm=nrm, off=off))
        if self.verb > 0:
            print(f'Expansion round {self.rounds}: |E| = {len(Z)}, boundary probes: {len(items)}')
        return items

    def boundary_done(self, key):
        """A boundary probe of the facet key did not extend the hull; the facet is final when all its probes
        did not (one probe per facet unless expandBoundary: sweep)."""
        left = self.bnd_left.get(key, 1) - 1
        self.bnd_left[key] = left
        if left <= 0:
            self.final.add(key)

    def bound_data(self, use_secant):
        Z = self.E_raw()
        tree = cKDTree(self.ach(Z))
        if use_secant:
            return tree, eg.SecantEnvelope(self.ach(self.K_raw()), self.Q)
        TL, TB = self.tangents_ach()
        return tree, (TL, TB)

    def sbound(self, Zs, tree, data, G, verts=None):
        Ys = self.ach(Zs)
        if isinstance(data, eg.SecantEnvelope):
            return eg.simplex_bound(Ys, G, tree, self.Q, secant=data, verts=verts)
        return eg.simplex_bound(Ys, G, tree, self.Q, TL=data[0], TB=data[1])

    def plan_interior(self):
        rho = self.rho
        no_dual = not self.use_duals
        tree, data = self.bound_data(no_dual)
        if no_dual:                      # simplices of the known points K; distance to E
            Zv = self.K_raw()
            simplices = data.simplices
        else:                            # simplices of the PFR E
            Zv = self.E_raw()
            simplices = eg.triangulate(self.ach(Zv) @ self.Q.T)
        todo = []
        for simp in simplices:
            Zs = Zv[simp]
            key = self.key(Zs)
            if key in self.dead:
                continue
            b, dd, gg, lam = self.sbound(Zs, tree, data, self.G, simp)
            if b > rho:
                b, dd, gg, lam = self.sbound(Zs, tree, data, self.G2, simp)
            if b > rho:
                todo.append((b, dd, gg, simp, lam, key))
        todo.sort(key=lambda t: -t[0])
        done = not todo and len(self.par_rep.sols) == self.n0
        if self.verb > 0:
            print(f'Expansion round {self.rounds}: {len(simplices)} simplices, not certified: {len(todo)}, '
                  f'probes so far: {self.n_probe}, variant: {"without" if no_dual else "with"} duals')
        items, chosen = [], []
        Y_all = self.ach(Zv)
        W_all = Y_all @ self.Q.T
        for (b, dd, gg, simp, lam, key) in todo:
            w = lam @ W_all[simp]
            if any(eg.linf(w, c) < 0.25 * rho for c in chosen):
                continue
            chosen.append(w)
            item = dict(w=w, key=key, Zs=Zv[simp].copy(), simp=simp, gp=gg, n_tan=len(self.tang))
            if no_dual:
                if gg > self.shape_frac * rho:
                    item['purpose'] = 'shape'
                else:
                    F = lam @ Y_all[simp]
                    j = self.promotable(F)
                    if j is not None:            # a known solution near F: move it to the PFR (no LP)
                        self.promote(j)
                        continue
                    item['purpose'] = 'coverage'
            else:
                item['purpose'] = 'interior'
            items.append(item)
        return items, done

    def promotable(self, F):
        YK = self.ach(self.K_raw())
        YE = self.ach(self.E_raw())
        near = np.max(np.abs(YK - F), axis=1)
        dE = cKDTree(YE).query(YK, p=np.inf)[0]
        cand = np.where((dE > self.tol_new) & (near < 0.25 * self.rho))[0]
        if len(cand) == 0:
            return None
        return int(cand[np.argmin(near[cand])])

    def promote(self, j):
        zj, itr = self.K[j]
        vals = list(self.mult * zj)
        n_before = len(self.par_rep.sols)
        self.par_rep.addSol(itr, vals=vals, origin='promoted')
        if len(self.par_rep.sols) > n_before:
            self.added['promoted'] += 1

    def still_needed(self, item):
        """Re-check an interior item when tangents were added after it was planned."""
        if item['purpose'] == 'ray':        # both solutions still Pareto, pair not used yet
            alive = {s.itr_id for s in self.par_rep.sols}
            return item['s'][0] in alive and item['s'][1] in alive and item['key'] not in self.ray_done
        if item['purpose'] == 'interior' and len(self.tang) > item['n_tan']:
            tree, data = self.bound_data(False)
            if self.sbound(item['Zs'], tree, data, self.G2)[0] <= self.rho:
                return False
        return True

    def plan_gap(self):
        Z = self.E_raw()
        if len(Z) < 2:
            return None
        Y = self.ach(Z)
        d, j = eg.nn_distances(Y)
        for i in np.argsort(-d):
            if d[i] <= self.rho:
                return None
            key = self.key(Z[[i]])
            if key in self.stuck:
                continue
            w = ((Y[i] + Y[j[i]]) / 2.0) @ self.Q.T
            return dict(purpose='gap', w=w, key=key)
        return None

    # ------------------------------------------------------------------------- ray-structured variant
    def next_item_rays(self):
        """Phases: discover -> pockets -> chains -> sweep -> (interior, certificate check) -> gap -> done."""
        n_sols = lambda: len(self.par_rep.sols)
        while True:
            if self.n_probe >= self.budget + self.gap_budget:
                return None
            if self.queue:
                item = self.queue.popleft()
                if self.still_needed(item):
                    return item
                continue
            if self.n_probe >= self.budget and self.phase not in ('gap', 'done'):
                print(f'Expansion: probe budget {self.budget} reached; proceeding to the gap repair.')
                self.phase = 'gap'
            if self.phase == 'discover':
                if self.disc_round > 0:     # the previous round is finished
                    if self.disc_level == 'near' and self.round_added == 0:
                        self.phase = 'pockets'      # the verification round did not extend the hull
                        continue
                    self.disc_level = 'far' if self.round_added > 0 else 'near'
                self.disc_round += 1
                self.round_added = 0
                self.rescale()
                items = self.plan_discover(self.disc_level)
                if not items and self.disc_level == 'far':
                    self.disc_level = 'near'
                    items = self.plan_discover('near')
                if not items:
                    self.phase = 'pockets'
                    continue
                self.queue.extend(items)
                continue
            if self.phase == 'pockets':
                self.rescale()
                self.build_pockets()
                self.phase = 'chains'
                continue
            if self.phase in ('chains', 'sweep'):
                self.rescale()
                items = self.plan_rays(self.phase)
                if items:
                    self.queue.extend(items)
                    continue
                if self.phase == 'chains':
                    self.build_sweep()
                    self.phase = 'sweep'
                    continue
                if self.cert_net:           # final check by the certificate (no boundary step)
                    self.phase = 'interior'
                    self.rounds += 1
                    self.n0, self.round_probes = n_sols(), 0
                else:
                    self.phase = 'gap'
                continue
            if self.phase == 'interior':
                items, done = self.plan_interior()
                if done or (not items and self.round_probes == 0 and n_sols() == self.n0):
                    self.phase = 'gap'
                    continue
                self.queue.extend(items)
                self.phase = 'after_interior'
                continue
            if self.phase == 'after_interior':
                if self.round_probes == 0 and n_sols() == self.n0:
                    self.phase = 'gap'
                else:
                    self.phase = 'interior'
                    self.rounds += 1
                    self.rescale()
                    self.n0, self.round_probes = n_sols(), 0
                continue
            if self.phase == 'gap':
                self.rescale()
                item = self.plan_gap()
                if item is not None:
                    return item
                self.phase = 'done'
            return None

    def ids_W(self):
        """ids of the PFR solutions and their projections (achievements of the current snapshot)."""
        ids = [s.itr_id for s in self.par_rep.sols]
        Y = self.ach(self.E_raw())
        return ids, Y, Y @ self.Q.T

    def far_point(self, mid, nrm):
        """The farthest location mid + L*nrm whose diagonal still fits into the box [N', U]."""
        lo, hi = -100.0 * self.low, 100.0
        fits = lambda L: np.ptp((mid + L * nrm) @ self.Q) <= 0.95 * (hi - lo - 1.0)
        if not fits(0.0):
            return mid
        a, b = 0.0, 400.0
        for _ in range(40):
            m = 0.5 * (a + b)
            a, b = (m, b) if fits(m) else (a, m)
        return mid + a * nrm

    def plan_discover(self, level):
        """Far round: one probe far outside every edge of the simplified hull of the projected PFR that was not
        probed in this way yet; near (verification) round: probes at distance rho outside every edge that is
        not final, at most expandCheck * rho apart along the edge."""
        ids, Y, W = self.ids_W()
        pos = dict(zip(ids, W))
        hv = er.hull_ccw(W, ids)
        if len(hv) >= 3:
            _, hv = er.simplify_closed([pos[i] for i in hv], hv, self.bmarg * self.rho)
        edges = [(hv[i], hv[(i + 1) % len(hv)]) for i in range(len(hv))] if len(hv) >= 3 else \
            ([(hv[0], hv[1]), (hv[1], hv[0])] if len(hv) == 2 else [])
        items = []
        for a, b in edges:
            key = (a, b)
            if key in self.disc_final or (level == 'far' and key in self.far_done):
                continue
            pa, pb = pos[a], pos[b]
            nrm = er.outward_normal(pa, pb)
            mid = 0.5 * (pa + pb)
            base = dict(purpose='discover', key=key, nrm=nrm, off=float(-nrm @ mid), mid=mid)
            if level == 'far':
                items.append(dict(base, level='far', w=self.far_point(mid, nrm)))
            else:
                n = max(1, int(np.ceil(np.linalg.norm(pb - pa) / (self.check * self.rho))))
                self.disc_left[key] = n
                items += [dict(base, level='near', w=pa + (j + 0.5) / n * (pb - pa) + self.rho * nrm)
                          for j in range(n)]
        if self.verb > 0:
            print(f'Expansion discovery round {self.disc_round} ({level}): |E| = {len(ids)}, '
                  f'hull edges {len(edges)}, probes {len(items)}')
        return items

    def new_ray(self, a, b, kind):
        """Ray between solutions a and b; existing PFR solutions close to the segment are adopted."""
        rkey = frozenset((a, b))
        if a == b or rkey in self.rays:
            return self.rays.get(rkey)
        ids, Y, W = self.ids_W()
        pos = dict(zip(ids, W))
        pa, pb = pos[a], pos[b]
        members = {a, b}
        for i, w in pos.items():
            if i not in members and 0.0 < er.seg_param(w, pa, pb) < 1.0 and \
                    er.seg_dist(w, pa, pb) <= self.bmarg * self.rho:
                members.add(i)
        self.rays[rkey] = dict(id=len(self.rays), a=a, b=b, kind=kind, members=members)
        return self.rays[rkey]

    def ray_order(self, ray, frm=None):
        """Alive members of the ray ordered along the segment (from the anchor frm, default ray['a'])."""
        ids, Y, W = self.ids_W()
        pos = dict(zip(ids, W))
        a = ray['a'] if frm is None or frm == ray['a'] else ray['b']
        b = ray['b'] if a == ray['a'] else ray['a']
        if a not in pos or b not in pos:
            return []
        mem = [i for i in ray['members'] if i in pos]
        return sorted(mem, key=lambda i: er.seg_param(pos[i], pos[a], pos[b]))

    def build_pockets(self):
        """Pockets between the old hull H0 (solutions of the previous stages) and the current hull H1."""
        ids, Y, W = self.ids_W()
        pos = dict(zip(ids, W))
        H1 = er.hull_ccw(W, ids)
        S0 = [i for i in ids if i in self.start_ids]
        H0 = er.hull_ccw(np.array([pos[i] for i in S0]), S0) if len(S0) >= 3 else S0
        flags = [i not in self.start_ids for i in H1]
        runs = er.cyclic_runs(flags)
        nearest_H0 = lambda i: i if i in H0 else min(H0, key=lambda j: np.linalg.norm(pos[j] - pos[i]))
        for run in runs:
            n = len(H1)
            if len(run) == n or len(H0) < 2:
                print('Expansion: the new hull has no vertex of the old one; pockets not defined.')
                continue
            a = nearest_H0(H1[(run[0] - 1) % n])
            b = nearest_H0(H1[(run[-1] + 1) % n])
            if a == b:
                continue
            ia, ib = H0.index(a), H0.index(b)
            m = len(H0)
            C0 = [H0[(ia + j) % m] for j in range(((ib - ia) % m) + 1)]
            C1 = [a] + [H1[j] for j in run] + [b]
            self.pockets.append(dict(C0=C0, C1=C1))
            for chain, kind in ((C1, 'new'), (C0, 'old')):
                for u, v in zip(chain[:-1], chain[1:]):
                    self.new_ray(u, v, 'chain-' + kind)
        print(f'Expansion: {len(self.pockets)} pocket(s) between the old and the new hull; new chain vertices: '
              f'{[len(p["C1"]) - 2 for p in self.pockets]}; {len(self.rays)} chain rays.')

    def plan_rays(self, phase):
        """Pairs of neighbour solutions (on the rays of the phase) distant by more than rho, largest first."""
        kinds = ('chain-new', 'chain-old') if phase == 'chains' else ('sweep',)
        ids, Y, W = self.ids_W()
        ach = dict(zip(ids, Y))
        pos = dict(zip(ids, W))
        cand, seen = [], set()
        for rkey, ray in self.rays.items():
            if ray['kind'] not in kinds:
                continue
            order = self.ray_order(ray)
            for p, q in zip(order[:-1], order[1:]):
                key = frozenset((p, q))
                d = eg.linf(ach[p], ach[q])
                if d > self.rho and key not in self.ray_done and key not in seen:
                    seen.add(key)
                    cand.append(dict(purpose='ray', ray=ray['id'], rkey=rkey, s=(p, q), key=key, d=d,
                                     w=0.5 * (pos[p] + pos[q])))
        cand.sort(key=lambda it: -it['d'])
        if self.verb > 0 and cand:
            print(f'Expansion {phase}: {len(cand)} pairs of neighbours on rays distant by more than rho.')
        return cand

    def chain_seq(self, chain):
        """Solutions along a chain (concatenation of its rays, in the chain order)."""
        seq = []
        for u, v in zip(chain[:-1], chain[1:]):
            ray = self.rays.get(frozenset((u, v)))
            part = self.ray_order(ray, frm=u) if ray is not None else [u, v]
            for i in part:
                if not seq or seq[-1] != i:
                    seq.append(i)
        return seq

    def build_sweep(self):
        """Sweep rays between the two (filled) chains of every pocket, paired by the relative arc length;
        every solution of both chains is an end of a sweep ray (unless closer than rho to its partner)."""
        ids, Y, W = self.ids_W()
        ach = dict(zip(ids, Y))
        pos = dict(zip(ids, W))
        n0 = len(self.rays)
        for p in self.pockets:
            A = [i for i in self.chain_seq(p['C1']) if i in pos]
            B = [i for i in self.chain_seq(p['C0']) if i in pos]
            if len(A) < 2 or len(B) < 2:
                continue
            sA = er.arc_length([pos[i] for i in A])
            sB = er.arc_length([pos[i] for i in B])
            # every interior solution of each chain is joined with the solution of the other chain at the nearest
            # relative arc length (both directions: no solution of the shorter chain is skipped; the nearest
            # mapping is monotone, so the rays do not cross)
            pairs = {(i, int(np.argmin(np.abs(sB - sA[i])))) for i in range(1, len(A) - 1)}
            pairs |= {(int(np.argmin(np.abs(sA - sB[j]))), j) for j in range(1, len(B) - 1)}
            for i, j in sorted(pairs):
                u, v = A[i], B[j]
                if u != v and eg.linf(ach[u], ach[v]) > self.rho:
                    self.new_ray(u, v, 'sweep')
        print(f'Expansion: {len(self.rays) - n0} sweep rays defined in {len(self.pockets)} pocket(s).')

    # ------------------------------------------------------------------------- solutions
    def sol(self, itr_id):
        """Process the solution of a stage-7 iteration (criteria values are in mc.cr[i].val)."""
        item, self.pending = self.pending, None
        if item is None:
            return
        vals = [cr.val for cr in self.mc.cr]
        z2 = self.z(vals)
        y2 = self.ach(z2[None])[0]
        weak = False
        if item['purpose'] != 'ray':          # diagonal probe
            c = self.pending_c
            y1 = c + np.min(y2 - c)           # exit point of the diagonal through the probed location
            weak = eg.linf(y2, y1) > 0.05      # probed location outside the efficient domain
        k_new = len(self.K) == 0 or float(cKDTree(self.ach(self.K_raw())).query(y2, p=np.inf)[0]) > self.tol_K
        if k_new:                             # a new known front point (not a repeated solution)
            self.K.append((z2, itr_id))
        if not self.pending_fixed:            # with a fixed criterion the duals do not define a tangent
            self.add_tangent(z2)
        YE = self.ach(self.E_raw())
        dE = float(cKDTree(YE).query(y2, p=np.inf)[0])
        new = dE > self.tol_new
        purpose = item['purpose']
        added = False
        note = ''
        if purpose == 'boundary':
            w2 = y2 @ self.Q.T
            s_out = float(w2 @ item['nrm'] + item['off'])
            note = f's_out={s_out:.2f}'
            if new and s_out > self.bmarg * self.rho:
                added = self.add(itr_id, 'boundary')
            if not added:
                self.boundary_done(item['key'])
        elif purpose == 'interior':
            tree, data = self.bound_data(False)
            b2 = self.sbound(item['Zs'], tree, data, self.G2)[0]
            note = f'beta_after={b2:.2f}'
            if b2 <= self.rho:
                self.tangent_only += 1
            elif new and (not weak or dE > 0.5 * self.rho):
                added = self.add(itr_id, 'interior')
                if not added:                   # rejected by ParRep (duplicate or dominated)
                    self.dead.add(item['key'])
            elif np.isfinite(item['gp']):
                self.dead.add(item['key'])
        elif purpose == 'shape':
            if not k_new:
                self.dead.add(item['key'])      # nothing new about the shape here
        elif purpose == 'coverage':
            if new and (not weak or dE > 0.5 * self.rho):
                added = self.add(itr_id, 'coverage')
            if not added:
                self.dead.add(item['key'])
        elif purpose == 'gap':
            if new:
                added = self.add(itr_id, 'gap')
            if not added:
                self.stuck.add(item['key'])
        elif purpose == 'discover':
            w2 = y2 @ self.Q.T
            s_out = float(w2 @ item['nrm'] + item['off'])
            note = f'{item["level"]}, s_out={s_out:.2f}'
            if new and s_out > self.bmarg * self.rho:
                added = self.add(itr_id, 'discover', parents=item['key'])     # ends of the probed hull edge
                self.round_added += int(added)
            if not added:
                if item['level'] == 'far':      # the edge will be checked in the verification round
                    self.far_done.add(item['key'])
                else:
                    self.disc_left[item['key']] -= 1
                    if self.disc_left[item['key']] <= 0:
                        self.disc_final.add(item['key'])
        elif purpose == 'ray':
            self.ray_done.add(item['key'])
            note = f'ray {item["ray"]}, pair {item["s"]}, d={item["d"]:.2f}'
            if new:
                added = self.add(itr_id, 'ray', parents=item['s'])     # pair spanning the cuboid
                if added:
                    self.rays[item['rkey']]['members'].add(itr_id)
        self.log.append(dict(n=self.n_probe, itr=itr_id, round=self.rounds, purpose=purpose,
                             w=np.round(item['w'], 3).tolist(), y=np.round(y2, 3).tolist(),
                             weak=weak, dist_E=round(dE, 3), added=added, note=note))
        if self.verb > 0:
            print(f'Expansion probe {self.n_probe} ({purpose}): y = {np.round(y2, 2)}, '
                  f'{"added" if added else "not added"} {note}')

    def add(self, itr_id, origin, parents=None):
        n_before = len(self.par_rep.sols)
        self.par_rep.addSol(itr_id, origin=origin, parents=parents)
        ok = len(self.par_rep.sols) > n_before
        if ok:
            self.added[origin] += 1
        return ok

    def add_tangent(self, z2):
        """Supporting hyperplane from the duals of the link constraints (variant with duals)."""
        if not self.use_duals:
            return
        d = self.wflow.link_duals
        if d is None or any(v is None for v in d):
            if self.duals_mode is True:
                print('Expansion: WARNING: the solver returned no dual values; switching to the variant '
                      'without dual values.')
            else:
                print('Expansion: no dual values available; using the variant without dual values.')
            self.use_duals = False
            return
        mu = np.abs(np.asarray(d, float))
        if mu.sum() <= 0:
            return
        beta = float(mu @ z2)
        Z = self.K_raw()
        viol = float(np.max(Z @ mu - beta)) if len(Z) else 0.0
        tol = 1e-6 * (abs(beta) + float(np.abs(Z).max(initial=0.0) * mu.sum())) + 1e-9
        if viol > tol:                      # not a supporting hyperplane: sign convention or degeneracy
            self.bad_duals += 1
            if self.verb > 0:
                print(f'Expansion: dual values rejected (violation {viol:.2e}).')
            if self.bad_duals > 3:
                print('Expansion: dual values repeatedly inconsistent; switching to the variant without duals.')
                self.use_duals = False
            return
        self.tang.append((mu, beta))

    # ------------------------------------------------------------------------- end of the stage
    def finish(self):
        for cr in self.mc.cr:
            cr.nadir_pwl = None
        print(f'\nExpansion finished after {self.n_probe} probes in {self.rounds} rounds. ======================')

    def certificate(self):
        """Certificate of the final PFR: (largest bound, number of simplices, number of simplices
        with bound > rho).  A simplex with bound <= rho is certified: every Pareto solution whose
        projection lies in it is within rho of the PFR (truth-free guarantee)."""
        Z = self.E_raw()
        if len(Z) < self.k:
            return float('nan'), 0, 0
        use_secant = not self.use_duals
        tree, data = self.bound_data(use_secant)
        if use_secant:
            Zv, simplices = self.K_raw(), data.simplices
        else:
            Zv, simplices = Z, eg.triangulate(self.ach(Z) @ self.Q.T)
        b = [self.sbound(Zv[s], tree, data, self.G2, s)[0] for s in simplices]
        if not b:
            return float('nan'), 0, 0
        return max(b), len(b), int(sum(v > self.rho for v in b))

    def uncovered_pairs(self):
        """rays mode: pairs of consecutive solutions on a ray farther apart than rho (L-inf, achievements). The
        cuboid of such a pair returned a duplicate or a dominated solution (or the budget was exhausted), so the
        ray structure does not cover the part of the PF between them."""
        if self.mode != 'rays':
            return []
        ids, Y, W = self.ids_W()
        ach = dict(zip(ids, Y))
        out = []
        for ray in self.rays.values():
            m = self.ray_order(ray)
            for p, q in zip(m, m[1:]):
                d = eg.linf(ach[p], ach[q])
                if d > self.rho:
                    out.append((p, q, round(float(d), 2)))
        return out

    def summary(self, rep_dir):
        self.rescale()
        Z = self.E_raw()
        Y = self.ach(Z)
        d, _ = eg.nn_distances(Y)
        gap = float(d.max()) if len(d) else float('nan')
        umin = float(d.min()) if len(d) else float('nan')
        cv = float(d.std() / d.mean()) if len(d) and d.mean() > 0 else float('nan')
        cert, n_simp, n_unc = self.certificate()
        lines = [f'Expansion stage summary (rho = {self.rho}, mode = {self.mode}' +
                 (f', {len(self.pockets)} pocket(s), {len(self.rays)} rays)' if self.mode == 'rays' else ')'),
                 f'variant: {"with" if self.use_duals else "without"} dual values (requested: {self.duals_mode})',
                 f'rounds: {self.rounds}, probes: {self.n_probe}  ' +
                 ', '.join(f'{k}: {v}' for k, v in self.stats.items()),
                 'added: ' + ', '.join(f'{k}: {v}' for k, v in self.added.items()),
                 f'tangents stored: {len(self.tang)}, rejected dual vectors: {self.bad_duals}, '
                 f'probes certified by their tangent only: {self.tangent_only}',
                 f'Nadir updates without restart: {self.n_nadir}; refused (solution dominated by the PFR): '
                 f'{self.n_nadir_skip}',
                 f'final PFR: kappa = {len(Z)}, gap gamma = {gap:.2f}, min distance u = {umin:.2f}, '
                 f'CV = {cv:.2f}',
                 f'certificate: {n_simp - n_unc} of {n_simp} simplices certified (bound <= rho); '
                 f'largest bound {cert:.2f}' +
                 (f'; {n_unc} not certified (probes there returned no new Pareto solution)' if n_unc else '')]
        if self.mode == 'rays':
            unc = self.uncovered_pairs()
            lines.append(f'pairs of neighbours on rays farther apart than rho: {len(unc)}' +
                         (' (itr ids, L-inf distance): ' + ', '.join(f'[{p}, {q}] {d}' for p, q, d in unc[:20]) +
                          (' ...' if len(unc) > 20 else '') if unc else ''))
        print('\n' + '\n'.join(lines))
        with open(f'{rep_dir}expandSummary.txt', 'w') as f:
            f.write('\n'.join(lines) + '\n')
        pd.DataFrame(self.log).to_csv(f'{rep_dir}expandLog.csv', index=False)
        print(f'Expansion log stored in "{rep_dir}expandLog.csv", summary in "{rep_dir}expandSummary.txt".')

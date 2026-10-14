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

Configuration keys (cfg.yml, all optional):
    expand: True             run the stage
    expandRho: <float>       resolution (default: ParRep cube min_size)
    expandDuals: auto        auto | True | False
    expandBudget: 2000       max number of probes (+ 400 for the gap repair)
    expandLow: 0.3           lowering of the Nadir for the A/R pairs
    expandMargin: 0.25       boundary threshold (fraction of rho)
"""
from collections import deque
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from . import expand_geom as eg


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
        self.low = float(opt('expandLow', 0.3))
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
        self.log = []
        self.stats = dict(boundary=0, interior=0, shape=0, coverage=0, gap=0)
        self.added = dict(boundary=0, interior=0, coverage=0, gap=0, promoted=0)
        self.tangent_only = 0
        self.rescale()
        self.par_rep.cur_cube = None
        print(f'\nExpansion stage: rho = {self.rho}, duals = {self.duals_mode}, budget = {self.budget}, '
              f'{len(self.par_rep.sols)} solutions from the previous stages. ==========================')

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
        changed = self.wflow.payoff.update(7)
        if changed:
            self.n_nadir += 1
            self.mc.scale()
            for s in self.par_rep.sols + self.par_rep.clSols:
                s.a_vals = [cr.val2ach(v, warn=False) for cr, v in zip(self.mc.cr, s.vals)]
            print('Expansion: Nadir updated without restart: ' +
                  ', '.join(f'{cr.name} {cr.nadir:.4e}' for cr in self.mc.cr))
        return changed

    # ------------------------------------------------------------------------- preferences
    def pref(self):
        """Entry point of an iteration of stage 7: set the A/R of the next probe."""
        if self.pending is not None:        # the previous probe was not solved
            it = self.pending
            if it['purpose'] in ('interior', 'shape', 'coverage'):
                self.dead.add(it['key'])
            elif it['purpose'] == 'boundary':
                self.final.add(it['key'])
            elif it['purpose'] == 'gap':
                self.stuck.add(it['key'])
            self.pending = None
        item = self.next_item()
        if item is None:
            self.finish()
            self.wflow.cur_stage = 6
            return
        self.pending = item
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

    # ------------------------------------------------------------------------- planning
    def next_item(self):
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
            mid = W[list(simp)].mean(axis=0)
            items.append(dict(purpose='boundary', w=mid + self.rho * nrm, key=key, nrm=nrm, off=off))
        if self.verb > 0:
            print(f'Expansion round {self.rounds}: |E| = {len(Z)}, boundary probes: {len(items)}')
        return items

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

    # ------------------------------------------------------------------------- solutions
    def sol(self, itr_id):
        """Process the solution of a stage-7 iteration (criteria values are in mc.cr[i].val)."""
        item, self.pending = self.pending, None
        if item is None:
            return
        vals = [cr.val for cr in self.mc.cr]
        z2 = self.z(vals)
        y2 = self.ach(z2[None])[0]
        c = self.pending_c
        y1 = c + np.min(y2 - c)               # exit point of the diagonal through the probed location
        weak = eg.linf(y2, y1) > 0.05          # probed location outside the efficient domain
        k_new = len(self.K) == 0 or float(cKDTree(self.ach(self.K_raw())).query(y2, p=np.inf)[0]) > self.tol_K
        if k_new:                             # a new known front point (not a repeated solution)
            self.K.append((z2, itr_id))
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
                self.final.add(item['key'])
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
        self.log.append(dict(n=self.n_probe, itr=itr_id, round=self.rounds, purpose=purpose,
                             w=np.round(item['w'], 3).tolist(), y=np.round(y2, 3).tolist(),
                             weak=weak, dist_E=round(dE, 3), added=added, note=note))
        if self.verb > 0:
            print(f'Expansion probe {self.n_probe} ({purpose}): y = {np.round(y2, 2)}, '
                  f'{"added" if added else "not added"} {note}')

    def add(self, itr_id, origin):
        n_before = len(self.par_rep.sols)
        self.par_rep.addSol(itr_id, origin=origin)
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

    def summary(self, rep_dir):
        self.rescale()
        Z = self.E_raw()
        Y = self.ach(Z)
        d, _ = eg.nn_distances(Y)
        gap = float(d.max()) if len(d) else float('nan')
        umin = float(d.min()) if len(d) else float('nan')
        cv = float(d.std() / d.mean()) if len(d) and d.mean() > 0 else float('nan')
        cert, n_simp, n_unc = self.certificate()
        lines = [f'Expansion stage summary (rho = {self.rho})',
                 f'variant: {"with" if self.use_duals else "without"} dual values (requested: {self.duals_mode})',
                 f'rounds: {self.rounds}, probes: {self.n_probe}  ' +
                 ', '.join(f'{k}: {v}' for k, v in self.stats.items()),
                 'added: ' + ', '.join(f'{k}: {v}' for k, v in self.added.items()),
                 f'tangents stored: {len(self.tang)}, rejected dual vectors: {self.bad_duals}, '
                 f'probes certified by their tangent only: {self.tangent_only}',
                 f'Nadir updates without restart: {self.n_nadir}',
                 f'final PFR: kappa = {len(Z)}, gap gamma = {gap:.2f}, min distance u = {umin:.2f}, '
                 f'CV = {cv:.2f}',
                 f'certificate: {n_simp - n_unc} of {n_simp} simplices certified (bound <= rho); '
                 f'largest bound {cert:.2f}' +
                 (f'; {n_unc} not certified (probes there returned no new Pareto solution)' if n_unc else '')]
        print('\n' + '\n'.join(lines))
        with open(f'{rep_dir}expandSummary.txt', 'w') as f:
            f.write('\n'.join(lines) + '\n')
        pd.DataFrame(self.log).to_csv(f'{rep_dir}expandLog.csv', index=False)
        print(f'Expansion log stored in "{rep_dir}expandLog.csv", summary in "{rep_dir}expandSummary.txt".')

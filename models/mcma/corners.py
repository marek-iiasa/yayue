# import pandas as pd
from itertools import combinations, permutations
import numpy as np
from scipy.spatial import Delaunay   #, QhullError
# from .cube import ParSol, Cubes, aCube
# noinspection SpellCheckingInspection


# define corners of Pareto set
# noinspection DuplicatedCode
class Corners:
    def __init__(self, wflow):     # initialize corners by regularized selfish solutions
        self.wflow = wflow
        self.mc = wflow.mc
        self.n_crit = self.mc.n_crit
        self.verb = self.mc.opt('verb', 0)
        self.verb = 3          # temporary for debugging
        self.corners = []         # criteria states at the Pareto-set corners
        self.a_corners = []       # corners defined by the achievements
        self.s_corners = []       # id of solution defining the corresponding corner
        self.cur_corner = 0       # seq_no of current corner
        self.n_corners = 0        # number of prepared corners
        self.all_done = False     # set to True, after last corner processed
        self.nSet = self.wflow.corners   # 1: only selfish; 2: second set
        self.curSet = 1           # current set of corners in [1, 2]
        self.mk_corners(self.curSet)      # make list of corners of first set (self.nSet = 1) or both sets (self.nSet = 2)
        if self.nSet == 2:
            self.curSet = 2
            self.mk_corners(self.curSet)
        # self.lst_corners()
        # self.next_corner()      # API for handling next corner, returns True, if the last corner is processed
        # self.set_ar()           # set A/R for the current corner   (moved to mc_blcok() )

    def mk_corners(self, curSet):
        print(f'Corners: {curSet}')
        assert curSet in [1, 2], f'curSet = {curSet} must be either 1 or 2.'
        n = self.n_crit     # number of criteria
        all_ids = range(n)  # ids of all criteria
        pair_lst = list(combinations(range(n), 2))  # pairs of criteria
        for pair in pair_lst:
            ign_ids = []    # ids of crit not belonging to a pair (will be ignored)
            for i in all_ids:
                if i not in pair:
                    ign_ids.append(i)
            print(f'ids of crit ({ign_ids}) to be ignored with two corners defined by permuted pair({pair}).')
            per2 = permutations(pair)   # crit-pair will generate 2 permutations
            twins = list(per2)  # permuted pairs
            print(twins)
            for p in twins:     # list of criteria state: defining a corner
                a_cor = {p[0]: 'a'}   # first criterion active
                a_cor.update({p[1]: 'n'})   # second criterion not active
                for i in ign_ids:
                    a_cor.update({i: 'i'})   # all remaining criteria, if any to be ignored
                self.corners.append(a_cor)
                print(f'p = {p}, a_cor = {a_cor}')
        self.n_corners = len(self.corners)
        if self.verb > 1:
            print(f'Prepared specs of {self.n_corners} corners for {self.n_crit} criteria.')
            self.lst_corners()
            print('--------------------------------------------------------------------')

    # noinspection DuplicatedCode
    def next_corner(self):
        assert self.cur_corner <= self.n_corners, f'requesting {self.cur_corner}-th corner out of {self.n_corners}.'
        if self.verb > 2:
            print(f'setting A/R for {self.cur_corner}-th out of {self.n_corners} corners defined.')
        self.set_ar()       # set A/R for specs in self.corners[self.cur_corner]
        self.cur_corner += 1
        if self.cur_corner == self.n_corners:
            if self.verb > 2:
                print(f'preferences for the last of {self.n_corners} corners generated.')
            self.all_done = True

    # noinspection GrazieInspection
    def set_ar(self):   # set A/R values for the currently requested corner
        corner = self.corners[self.cur_corner]
        if self.verb > 2:
            print(f'AR for corner: {corner}')
        for (i, cr) in enumerate(self.mc.cr):
            cr.is_fixed = False
            cr.is_active = False
            cr.is_ignored = False
            delta = abs(cr.utopia - cr.nadir) / 3.  # take 1/3 of the (utopia, nadir) range
            stat_id = str(corner.get(i))
            # print(f'crit. "{cr.name}", stat_id {stat_id}.')
            if stat_id == 'a':  # selfish sol. for i-th criterion
                if self.verb > 1:
                    print(f'Computing Pareto-front corner: selfish opt. for crit. "{cr.name}".')
                cr.is_active = True
                cr.asp = cr.utopia
                cr.res = cr.utopia - cr.mult * delta
            elif stat_id == 'n':  # criterion in-active for this corner solution
                # print(f'criterion in-active for this corner "{cr.name}".')
                cr.asp = cr.nadir + cr.mult * delta
                cr.res = cr.nadir
            else:       # criterion ignored for this corner solution
                # print(f'criterion ignored for this corner "{cr.name}".')
                cr.is_ignored = True
                # delta2 = abs(cr.utopia - cr.nadir) / 10.  # take 1/10 of the (utopia, nadir) range
                # cr.asp = cr.nadir + cr.mult * delta2
                # the below better appr. Nadir for 4 crit than when using delta2, cf corn40, corn41, respectively
                # also without delta2 defines 3 corners while corn41 defines only 2 corners
                # moreover, with delta2 the water Nadir is not improved during 5000 itrs
                cr.asp = cr.utopia
                cr.res = cr.nadir
            if self.verb > 2:
                print(f'Crit {cr.name}: active {cr.is_active}, ignored {cr.is_ignored}, A {cr.val2ach(cr.asp)}, '
                      f'R {cr.val2ach(cr.res)}')
        pass

    def next_sol(self, is_pareto, n_itr):
        if is_pareto:
            cor = ''
            for (i, cr) in enumerate(self.mc.cr):
                if i > 0:
                    cor = f'{cor}, {cr.name}: {cr.a_val:.1f}'
                else:
                    cor = f'{cr.name}: {cr.a_val:.1f}'
            self.a_corners.append(cor)
            self.s_corners.append(n_itr)
            # todo: add solution id
        else:
            print('Non-Pareto solution ignored in corners definitions.')
        if self.all_done:
            print(f'\nPareto-set {len(self.a_corners)} (unique) corners:        ')
            for (i, cor) in enumerate(self.a_corners):
                print(f'corner {i}, sol_id {self.s_corners[i]}:  ({cor})')
            print(f'Switch to computing Pareto-front representation based on cuboids. ===============================')
        return self.all_done

    def lst_corners(self):
        print(f'n_crit = {self.n_crit}, n_corners = {len(self.corners)}')
        for i, cor in enumerate(self.corners):
            print(f'Corner {i}: {cor}')

    # def prune(self, alive_ids):
    #     """Keep only corners whose solution ids are still alive in ParRep.sols."""
    #     new_a = []
    #     new_s = []
    #     removed = []
    #
    #     for cor, sid in zip(self.a_corners, self.s_corners):
    #         if sid in alive_ids:
    #             new_a.append(cor)
    #             new_s.append(sid)
    #         else:
    #             removed.append(sid)
    #
    #     self.a_corners = new_a
    #     self.s_corners = new_s
    #
    #     if self.verb > 1 and removed:
    #         print(f'Corners::prune(): removed stale corner ids: {removed}')
    #
    #     return new_a, new_s, removed

# define triangles out of non-dominated corners
# noinspection DuplicatedCode
class Triangle:
    def __init__(self, corn):     # initialize triangles (ctor called after all corners are generated)
        self.corners = corn
        self.wflow = corn.wflow
        self.mc = self.wflow.mc
        pass
        self.verb = corn.verb
        # self.scale = self.mc.cafAsp  # upper bound of achievements: [0, scale]
        self.cr_names = [cr.name for cr in self.mc.cr]  # fixed column order = order of criteria
        self.n_crit = len(self.cr_names)
        self.sol_ids = list(corn.s_corners)  # solution id of each corner (row)

        if self.verb > 1:
            print(f'\n----------- Start generations of triangles. -----------\n')

        # parse corners "name: val, name: val, ..." into an (n_corners, n_crit) array
        rows = []
        for cor in corn.a_corners:
            d = {}
            for item in cor.split(','):
                name, val = item.rsplit(':', 1)
                d[name.strip()] = float(val)
            missing = set(self.cr_names) - d.keys()
            assert not missing, f'corner "{cor}" lacks criteria {missing}.'
            rows.append([d[nm] for nm in self.cr_names])
        self.pts = np.array(rows, dtype=float)  # vertices in achievement space
        self.n_pts = self.pts.shape[0]
        # self.pts_n = self.pts / self.scale  # same, normalized to [0, 1] (scale-independent)
        self.pts_n = self.pts       # refrain from further (points already normalized) normalization

        assert self.n_pts >= self.n_crit, \
            f'{self.n_pts} corners are too few to span a {self.n_crit - 1}-dim facet.'
        if self.verb > 1:
            # print(f'Triangle: {self.n_pts} corners x {self.n_crit} criteria (scale {self.scale}):')
            print(f'Triangle: {self.n_pts} corners x {self.n_crit}:')
            for i, row in enumerate(self.pts):
                print(f'  vertex {i} (sol_id {self.sol_ids[i]}): {np.round(row, 1)}')
        self.triangulate()  # triangulate the corners on the (n_crit-1)-dim Pareto surface
        pass
        if self.verb > 1:
            print(f'\n----------- Finished generations of triangles. -----------\n')


       #  raise NotImplementedError('Triangle class is not implemented yet.')

    def triangulate(self, max_edge=None, keep_flat=True):
        """Triangulate the corners (any number >= 3) on the 2-dim Pareto surface (n_crit = 3 only).
        Result: self.simplices, an int array (n_triangles, 3); each row = indices into self.pts.
                self.flat, a bool array (n_triangles,): True for a flat triangle (3 collinear corners).
        max_edge: optional, in achievement units (currently [0, 100]); drops triangles with a longer edge
                  (crude guard against spanning concave notches of the front).
        keep_flat: True (default) keeps flat triangles (flagged in self.flat and printed); False drops them."""

        '''
        # orthonormal basis of the hyperplane orthogonal to the diagonal (1,...,1)
        basis = np.linalg.svd(np.ones((1, n)))[2][1:]  # shape (n-1, n)
        self.proj = (self.pts_n - self.pts_n.mean(axis=0)) @ basis.T  # (n_pts, n-1)

        if n == 2:  # 1-D front: "simplices" are segments between neighbours along the projection
            order = np.argsort(self.proj[:, 0])
            self.simplices = np.column_stack([order[:-1], order[1:]])
        else:
            try:
                self.simplices = Delaunay(self.proj).simplices
            except QhullError as e:
                raise ValueError(f'corners are degenerate in the projected {n - 1}-dim space '
                                 f'(e.g. collinear); cannot triangulate.') from e
        '''

        n = self.n_crit
        basis = np.linalg.svd(np.ones((1, n)))[2][1:]  # (n-1, n), orthogonal to diagonal
        self.proj = (self.pts_n - self.pts_n.mean(axis=0)) @ basis.T  # (n_pts, n-1), centered

        # actual dimension r of the projected point set (handles all-collinear / all-coplanar corners)
        _, sv, vt = np.linalg.svd(self.proj, full_matrices=False)
        tol = 1e-6
        r = int(np.sum(sv > tol)) if sv.size else 0
        self.dim = r
        red = self.proj @ vt[:r].T  # coords in the r-dim subspace

        assert n == 3, f'triangulate() handles only 3 criteria (got {n}).'
        assert r == 2, 'all corners are collinear; cannot triangulate.'

        if self.n_pts == 3:  # minimal case: the 3 corners are the only triangle
            # qhull needs >= 4 points, so the single triangle is built directly
            simp = np.arange(3).reshape(1, -1)
        else:  # QJ: keep every corner as vertex (collinear corners included)
            # no Qz: with QJ it leaks the added point-at-infinity (index n_pts) into simplices
            simp = Delaunay(red, qhull_options='Qbb Qc QJ').simplices
        # flat triangles: near-zero area (3 collinear corners)
        areas = np.array([abs(np.linalg.det(red[t[1:]] - red[t[0]])) / 2 for t in simp])
        flat = areas <= tol * max(areas.max(), tol)
        self.collinear = [t.tolist() for t in simp[flat]]
        for t in self.collinear:
            print(f'Triangle: collinear corners {t} (sol_ids {[self.sol_ids[i] for i in t]}); flat triangle '
                  f'{"kept (flagged)" if keep_flat else "dropped"}.')
        if not keep_flat:
            simp, flat = simp[~flat], flat[~flat]
        self.simplices, self.flat = simp, flat

        if max_edge is not None:  # drop triangles with an overlong edge (in achievement units)
            keep = np.array([max(np.abs(self.pts[t[a]] - self.pts[t[b]]).max()  # Chebyshev, as edge_len
                                 for a, b in ((0, 1), (0, 2), (1, 2))) <= max_edge
                             for t in self.simplices], dtype=bool)
            self.simplices, self.flat = self.simplices[keep], self.flat[keep]

        # safety check: corners not used by any remaining triangle
        unused = sorted(set(range(self.n_pts)) - set(self.simplices.ravel().tolist()))
        if unused:
            print(f'Triangle: corners {unused} (sol_ids {[self.sol_ids[i] for i in unused]}) '
                  f'not in any triangle.')

        if self.verb > 1:
            print(f'Triangle: {len(self.simplices)} triangles on {self.n_pts} corners:')
            for k, t in enumerate(self.simplices):
                print(f'  triangle {k}: vertices {t.tolist()}, sol_ids {[self.sol_ids[i] for i in t]}'
                      f'{"  (flat)" if self.flat[k] else ""}')
        self.mk_edges()
        return self.simplices

    def mk_edges(self):
        """Build the edge (side) table of the current triangulation (self.simplices).
        Triangles are numbered 0..n_tri-1 (rows of self.simplices); edges 0..n_edges-1 (rows of self.edges).
        self.edges:     int (n_edges, 2), corner ids of the edge ends (sorted: a < b)
        self.edge_len:  float (n_edges,), Chebyshev length max_k |pts[a, k] - pts[b, k]| (achievement units)
        self.edge_tris: int (n_edges, 2), triangles sharing the edge; second = -1 for a boundary edge
        self.tri_edges: int (n_tri, 3), edge ids of each triangle; edge k is opposite vertex k"""
        e_id = {}       # (a, b) -> edge id
        edges, e_tris = [], []
        self.tri_edges = np.empty((len(self.simplices), 3), dtype=int)
        for i, t in enumerate(self.simplices):
            for k in range(3):  # edge k: the two vertices other than t[k]
                key = tuple(sorted((int(t[(k + 1) % 3]), int(t[(k + 2) % 3]))))
                j = e_id.get(key)
                if j is None:  # new edge
                    j = e_id[key] = len(edges)
                    edges.append(key)
                    e_tris.append([i, -1])
                else:  # second triangle on this edge
                    assert e_tris[j][1] == -1, f'edge {key} is shared by more than 2 triangles.'
                    e_tris[j][1] = i
                self.tri_edges[i, k] = j
        self.edges = np.array(edges, dtype=int).reshape(-1, 2)
        self.edge_tris = np.array(e_tris, dtype=int).reshape(-1, 2)
        self.edge_len = np.abs(self.pts[self.edges[:, 0]] - self.pts[self.edges[:, 1]]).max(axis=1)
        if self.verb > 1:
            print(f'Triangle: {self.n_edges()} edges ({len(self.shared_edges())} shared):')
            for j in range(self.n_edges()):
                vert, tris, length = self.edge(j)
                print(f'  edge {j}: corners {vert}, triangles {tris}, Chebyshev length {length:.1f}')

    # --- interface for other parts of the code ---
    def n_tri(self):
        """Number of triangles."""
        return len(self.simplices)

    def tri(self, i):
        """i-th triangle: (corner ids [3], edge ids [3], is_flat); edge k is opposite corner k."""
        return self.simplices[i].tolist(), self.tri_edges[i].tolist(), bool(self.flat[i])

    def n_edges(self):
        """Number of edges (sides); each shared edge is counted once."""
        return len(self.edges)

    def edge(self, j):
        """j-th edge: (corner ids [2], triangle ids [1 or 2], Chebyshev length)."""
        tris = [int(i) for i in self.edge_tris[j] if i >= 0]
        return self.edges[j].tolist(), tris, float(self.edge_len[j])

    def shared_edges(self):
        """Ids of the edges shared by two triangles (interior edges)."""
        return np.flatnonzero(self.edge_tris[:, 1] >= 0).tolist()

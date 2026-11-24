# import pandas as pd
from itertools import combinations, permutations
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

# define corners of Pareto set
# noinspection DuplicatedCode
import numpy as np
from scipy.spatial import Delaunay, QhullError
class Triangle:
    def __init__(self, corn):     # initialize triangles (ctor called after all corners are generated)
        self.corners = corn
        self.wflow = corn.wflow
        # self.mc = wflow.mc
        pass
        self.verb = corn.verb
        self.scale = self.mc.cafAsp  # upper bound of achievements: [0, scale]
        self.cr_names = [cr.name for cr in self.mc.cr]  # fixed column order = order of criteria
        self.n_crit = len(self.cr_names)
        self.sol_ids = list(corn.s_corners)  # solution id of each corner (row)

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
        self.pts_n = self.pts / self.scale  # same, normalized to [0, 1] (scale-independent)

        assert self.n_pts >= self.n_crit, \
            f'{self.n_pts} corners are too few to span a {self.n_crit - 1}-dim facet.'
        if self.verb > 1:
            print(f'Triangle: {self.n_pts} corners x {self.n_crit} criteria (scale {self.scale}):')
            for i, row in enumerate(self.pts):
                print(f'  vertex {i} (sol_id {self.sol_ids[i]}): {np.round(row, 1)}')
        self.triangulate()  # triangulate the corners on the (n_crit-1)-dim Pareto surface
        pass


       #  raise NotImplementedError('Triangle class is not implemented yet.')

    def triangulate(self, max_edge=None):
        """Triangulate the corners (any number) on the (n_crit-1)-dim Pareto surface.
        Result: self.simplices, an int array (n_simplices, n_crit); each row = indices into self.pts.
        max_edge: optional, in [0, 1] units of scale; drops simplices with a longer edge
                  (crude guard against spanning concave notches of the front)."""

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

        if r == 0:  # single (or coincident) point: nothing to triangulate
            self.simplices = np.empty((0, 1), dtype=int)
        elif r == 1:  # all collinear: chain of segments ordered along the line
            order = np.argsort(red[:, 0])
            self.simplices = np.column_stack([order[:-1], order[1:]])
        else:  # QJ: keep every point as vertex (collinear boundary points included)
            tri = Delaunay(red, qhull_options='Qbb Qc Qz QJ')
            simp = tri.simplices
            # drop slivers: near-zero r-volume simplices produced by collinear/coplanar subsets
            vols = np.array([abs(np.linalg.det(red[s[1:]] - red[s[0]])) for s in simp])
            self.simplices = simp[vols > tol * max(vols.max(), tol)]
            # report collinear triples (= dropped slivers)
            self.collinear = [s.tolist() for s in simp[vols <= tol * max(vols.max(), tol)]]
            for s in self.collinear:
                print(f'Triangle: collinear corners {s} (sol_ids {[self.sol_ids[i] for i in s]}); '
                      f'flat simplex dropped.')
            # safety check: corners not used by any remaining simplex
            unused = sorted(set(range(self.n_pts)) - set(self.simplices.ravel().tolist()))
            if unused:
                print(f'Triangle: corners {unused} (sol_ids {[self.sol_ids[i] for i in unused]}) '
                      f'not in any simplex.')

        if r < n - 1 and self.verb > 0:
            print(f'Triangle: corners span only {r} of {n - 1} dims; simplices have {r + 1} vertices.')
        if max_edge is not None:  # drop simplices with an overlong edge (in normalized units)
            keep = []
            for s in self.simplices:
                v = self.pts_n[s]
                edges = [np.linalg.norm(v[i] - v[j]) for i in range(len(s)) for j in range(i + 1, len(s))]
                keep.append(max(edges) <= max_edge)
            self.simplices = self.simplices[np.array(keep, dtype=bool)]

        if self.verb > 1:
            print(f'Triangle: {len(self.simplices)} simplices on {self.n_pts} corners:')
            for k, s in enumerate(self.simplices):
                print(f'  simplex {k}: vertices {s.tolist()}, sol_ids {[self.sol_ids[i] for i in s]}')
        return self.simplices

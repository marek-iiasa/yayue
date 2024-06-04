# import pandas as pd
from itertools import combinations, permutations
# from .cube import ParSol, Cubes, aCube
# noinspection SpellCheckingInspection


# define corners of Pareto set
class Corners:
    def __init__(self, mc):     # initialize corners by regularized selfish solutions
        self.mc = mc
        self.n_crit = mc.n_crit
        # self.verb = 3
        self.verb = mc.opt('verb', 0)
        self.corners = []         # criteria states at the Pareto-set corners
        self.a_corners = []       # corners defined by the achievements
        self.cur_corner = 0       # seq_no of current corner
        self.n_corners = 0        # number of prepared corners
        self.all_done = False     # set to True, after last corner processed
        self.mk_corners()         # make list of corners
        # self.lst_corners()
        # self.next_corner()      # API for handling next corner, returns True, if the last corner is processed
        # self.set_ar()           # set A/R for the current corner

    def mk_corners(self):
        n = self.n_crit     # number of criteria
        all_ids = range(n)  # ids of all criteria
        pair_lst = list(combinations(range(n), 2))  # pairs of criteria
        for pair in pair_lst:
            ign_ids = []    # ids of crit not belonging to a pair (will be ignored)
            for i in all_ids:
                if i not in pair:
                    ign_ids.append(i)
            # print(f'ids of crit ({ign_ids}) to be ignored with two corners defined by permuted pair({pair}).')
            per2 = permutations(pair)   # crit-pair will generate 2 permutations
            twins = list(per2)  # permuted pairs
            # print(twins)
            for p in twins:     # list of criteria state: defining a corner
                a_cor = {p[0]: 'a'}   # first criterion active
                a_cor.update({p[1]: 'n'})   # second criterion not active
                for i in ign_ids:
                    a_cor.update({i: 'i'})   # all remaining criteria, if any to be ignored
                self.corners.append(a_cor)
                # print(f'p = {p}, a_cor = {a_cor}')
        self.n_corners = len(self.corners)
        if self.verb > 1:
            print(f'Prepared specs of {self.n_corners} corners for {self.n_crit} criteria.')
            self.lst_corners()
            print('--------------------------------------------------------------------')

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
                # delta2 = abs(cr.utopia - cr.nadir) / 10.  # take 1/10 of the (utopia, nadir) range
                cr.is_ignored = True
                # cr.asp = cr.nadir + cr.mult * delta2
                cr.asp = cr.utopia
                cr.res = cr.nadir
            if self.verb > 2:
                print(f'Crit {cr.name}: active {cr.is_active}, ignored {cr.is_ignored}, A {cr.val2ach(cr.asp)}, '
                      f'R {cr.val2ach(cr.res)}')
        pass

    def next_sol(self, is_pareto):
        if is_pareto:
            cor = ''
            for (i, cr) in enumerate(self.mc.cr):
                if i > 0:
                    cor = f'{cor}, {cr.name}: {cr.a_val:.1f}'
                else:
                    cor = f'{cr.name}: {cr.a_val:.1f}'
            self.a_corners.append(cor)
        else:
            print('Non-Pareto solution skipped in corners definitions.')
        if self.all_done:
            print(f'\nPareto-set {len(self.a_corners)} (unique) corners:        ')
            for (i, cor) in enumerate(self.a_corners):
                print(f'corner {i}:  ({cor})')
            print(f'Switch to computing Pareto-front representation based on cuboids. ===============================')
        return self.all_done

    def lst_corners(self):
        print(f'n_crit = {self.n_crit}, n_corners = {len(self.corners)}')
        for i, cor in enumerate(self.corners):
            print(f'Corner {i}: {cor}')

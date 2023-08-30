# import sys      # needed from stdout
# import os
# import numpy as np


class ParSol:     # one Pareto solution
    def __init__(self, itr_id, vals, sc_vals):
        self.itr_id = itr_id    # iteration id (negative for corners)
        self.vals = vals  # list of criteria values
        self.sc_vals = sc_vals  # list of scaled criteria values
        print(f'Solution of itr {itr_id}: criteria values: {self.vals}, (scaled: {self.sc_vals})')


class Cube:     # defined (in scaled values) by the two given neighbor solutions
    def __init__(self, mc, s1, s2, size):
        self.mc = mc    # CtrMca object
        self.s1 = s1    # first solution defining the cube
        self.s2 = s2    # second solution defining the cube
        self.size = size    # cube size = L1 distance(s1, s2), for scaled crit values
        self.sc_asp = []   # list of scaled A values (used in defining solutions that define the cube)
        self.sc_res = []   # list of scaled R values
        self.asp = []   # list of A values (to be used in the MCMA preferences)
        self.res = []   # list of R values

        # define A/R values for spliting the cuboid (i.e., to find a new solution between s1 and s2)
        for (i, cr) in enumerate(self.mc.cr):
            v1 = s1.vals[i]
            v2 = s2.vals[i]
            if cr.isBetter(v1, v2):     # s1 has better crit. value than s2
                cr.asp = v1
                cr.res = v2
                self.asp.append(v1)
                self.res.append(v2)
                self.sc_asp.append(cr.sc_var * v1)
                self.sc_res.append(cr.sc_var * v2)
            else:           # s2 has better crit. value than s1
                cr.asp = v2
                cr.res = v1
                self.asp.append(v2)
                self.res.append(v1)
                self.sc_asp.append(cr.sc_var * v2)
                self.sc_res.append(cr.sc_var * v1)
            cr.is_active = True
            print(f'New cube A/R values for criterion {cr.name}: A {cr.asp:.3e}, R {cr.res:.3e}')

    def lst(self, seq):
        val1 = ''
        val2 = ''
        for (v1, v2) in zip(self.s1.vals, self.s2.vals):
            val1 += f'{v1:.2e}, '
            val2 += f'{v2:.2e}, '
        print(f'cube[{seq}, size={self.size:.2e}, sol_itrIds: ({self.s1.itr_id}, {self.s2.itr_id}), '
              f'corners: ([{val1}], [{val2}])')

        val1 = ''
        val2 = ''
        for (v1, v2) in zip(self.sc_asp, self.sc_res):
            val1 += f'{v1:.2e}, '
            val2 += f'{v2:.2e}, '
        print(f'\tNext preferences:  A [{val1}],  R [{val2}]')


class ParRep:     # representation of Pareto set
    def __init__(self, mc):
        self.mc = mc    # CtrMca object
        # self.n_crit = mc.n_crit   # number of criteria  (not needed?)
        # self.n_corners = 0   # number of corners (one utopia + other inactive)
        self.sols = []      # Pareto-solutions (ParSol objects)
        self.neigh = []     # list of tuples (itr_id1, itr_id2, distance) to the nearest neighbor
        self.cubes = []     # list of cubes (Cube objects, one cube for each iteration)

        mc.scale()          # (re)define scales for criteria values
        self.ini_corners()  # initialize corner solutions
        self.nearest()      # find pairs of neighbors (nearest solutions)
        # raise Exception(f'ParRep ctor not implemented yet.')

    def cube(self):     # entry point for each iteration
        # define new cube (in ASF space), set A/R (in both ASF and A/R scales)
        # self.nearest()    # called either by ctor or by addSol(); find pairs of neighbors (nearest solutions)
        # find pairs of most distant neighbor solutions, i.e., largest gap in the solutions (to define new cube)
        mx_dis = 0.    # initialize distance
        s1 = None   # initialize solutions to undefined
        s2 = None
        itr1 = None
        itr2 = None
        for (i, n1) in enumerate(self.neigh):
            dis = n1[2]  # distance is the third arg in the list element (itr1, utr2, distanse)
            if dis > mx_dis:
                itr1 = n1[0]    # itr_id of the "from" solution
                itr2 = n1[1]    # itr_id of the "to" solution
                s1 = self.sol_seq(itr1)   # sol_seq of the first solution
                s2 = self.sol_seq(itr2)   # sol_seq of the second solution
                mx_dis = dis
        assert mx_dis > 0., f'ParRep::cube(): empty cube.'
        print(f'Largest cube defined by solutions: {s1} (itr {itr1}), {s2} (itr {itr2}); cube size = {mx_dis}.')
        self.cubes.append(Cube(self.mc, self.sols[s1], self.sols[s2], mx_dis))     # ctor sets A/R values in mc.cr
        print(f'Cube added to ParRep. There are {len(self.cubes)} cubes defined.')
        # raise Exception(f'ParRep::cube() not implemented yet.')

    def addSol(self, itr_id):  # add solution (uses crit-values updated in mc.cr)
        vals = []     # crit values
        sc_vals = []  # scaled crit values
        for cr in self.mc.cr:
            vals.append(cr.val)
            sc_vals.append(cr.sc_var * cr.val)
        self.sols.append(ParSol(itr_id, vals, sc_vals))
        print(f'Solution {itr_id = } added to ParRep. There are {len(self.sols)} Pareto solutions.')
        # todo: implement update while adding new solutions (instead of computing all)
        self.nearest()      # find pairs of neighbors (nearest solutions)
        # raise Exception(f'ParRep::addSol() not implemented yet.')

    def ini_corners(self):  # initialize corner solutions (each composed of one utopia and nadir of all others)
        cur_uto = 0     # index of the current utopia
        for (k, crit) in enumerate(self.mc.cr):     # one corner for each criterion
            vals = []  # crit values
            sc_vals = []  # scaled crit values (one utopia, others nadir)
            itr_id = -1 - k  # itr_id negative, start with -1
            for (i, cr) in enumerate(self.mc.cr):
                if i == cur_uto:
                    val = cr.utopia
                    sc_val = cr.sc_var * val
                else:
                    val = cr.nadir
                    sc_val = cr.sc_var * val
                vals.append(val)
                sc_vals.append(sc_val)
            self.sols.append(ParSol(itr_id, vals, sc_vals))
            cur_uto += 1

    def nearest(self):  # for each solution find distance (in ASF scale) to the nearest neighbor
        # todo: consider update of self.neigh while adding one new solution (instead of computing all)
        self.neigh = []
        mx_gap = 0.     # max gap
        min_gap = float('inf')  # min gap
        no_gap = 0      # number of zero-gaps
        it1 = it2 = it3 = it4 = None
        for (i, s1) in enumerate(self.sols):
            dist = float('inf')
            nearest = None
            for (j, s2) in enumerate(self.sols):
                if i == j:
                    continue
                s2 = self.sols[j]
                d = 0.
                for (a1, a2) in zip(s1.sc_vals, s2.sc_vals):    # loop over scaled values of criteria
                    d += abs(a1 - a2)   # Manhattan (L1) distance in criteria scaled-values
                if d < dist:
                    nearest = j     # seq_no in self.sols
                    dist = d
                else:
                    # print(f'pair of solution_seq ({i}, {j}), dist {d} skipped: current min dist = {dist}')
                    pass
                j += 1
            assert nearest is not None, f'ParRep::nearest(): neighbor not found for {i}-th solution.'
            itr1 = self.sols[i].itr_id
            itr2 = self.sols[nearest].itr_id
            self.neigh.append([itr1, itr2, dist])
            if dist > mx_gap:
                mx_gap = dist
                it1 = itr1
                it2 = itr2
            if dist < min_gap:
                if dist > 0.:
                    min_gap = dist
                    it3 = itr1
                    it4 = itr2
                else:
                    no_gap += 1
        n_lst = ''
        for ne in self.neigh:
            n_lst += f'[{ne[0]}, {ne[1]}, {ne[2]:.2e}], '
        print(f'Distances to nearest sol. (itr_id1, itr_id2, dist): {n_lst}')
        # print(f'\nDistances to nearest sol. (itr_id1, itr_id2, dist): {self.neigh}')
        print(f'Max gap {mx_gap:.2e} for neighbor itr_ids ({it1}, {it2}).')
        print(f'Min non-zero gap {min_gap:.2e} for neighbor itr_ids ({it3}, {it4}).')
        print(f'Number of zero-gaps {no_gap}.')

    def sol_seq(self, itr_id):  # return seq_no in self.sols[] for the itr_id
        for (i, s) in enumerate(self.sols):
            if s.itr_id == itr_id:
                return i
        raise Exception(f'ParRep::sol_seq(): {itr_id} not in the solution set.')

    def lst_cubes(self):  # lisrt cubes
        for (i, c) in enumerate(self.cubes):
            c.lst(i)

    def summary(self):  # summary report
        print('\nList of cubes:')
        self.lst_cubes()
        print('\n')
        raise Exception(f'ParRep::summary() not implemented yet.')

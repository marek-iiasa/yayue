# import sys      # needed from stdout
# import os
# import numpy as np


class ParSol:     # one Pareto solution
    def __init__(self, itr_id, vals, sc_vals):
        self.itr_id = itr_id    # iteration id (negative for corners)
        self.vals = vals  # list of ASF values
        self.sc_vals = sc_vals  # list of scaled criteria values


class Cube:     # defined (in ASF scale) by two neighbor solutions
    def __init__(self, mc, s1, s2, size):
        self.mc = mc    # CtrMca object
        self.s1 = s1    # first solution defining the cube
        self.s2 = s2    # second solution defining the cube
        self.size = size    # cube size = L1 distance(s1, s2), for scaled crit values
        self.sc_asp = []   # list of scaled A values (used in defining solutions that define the cube)
        self.sc_res = []   # list of scaled R values
        self.asp = []   # list of A values (to be used in the MCMA preferences)
        self.res = []   # list of R values

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
            print(f'Criterion {cr.name}: A {cr.asp}, R {cr.res}')


class ParRep:     # representation of Pareto set
    def __init__(self, mc):
        self.mc = mc    # CtrMca object
        # self.n_crit = mc.n_crit   # number of criteria  (not needed?)
        # self.n_corners = 0   # number of corners (one utopia + other inactive)
        self.sols = []      # Pareto-solutions (ParSol objects)
        self.neigh = []     # list of pairs [seq_id and distance to] defining nearest neighbor
        self.cubes = []     # list of cubes (Cube objects, one cube for each iteration)

        mc.scale()          # (re)define scales for criteria values
        self.ini_corners()  # initialize corner solutions
        self.nearest()      # find pairs of neighbors (nearest solutions)
        # raise Exception(f'ParRep ctor not implemented yet.')

    def addSol(self, itr_id):  # add solution (using crit-values updated in mc.cr)
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
        # todo: implement update while adding new solutions (instead of computing all)
        self.neigh = []
        for (i, s1) in enumerate(self.sols):
            dist = float('inf')
            nearest = None
            j = i + 1
            if j == len(self.sols):
                break
            while j < len(self.sols):
                s2 = self.sols[j]
                d = 0.
                for (a1, a2) in zip(s1.sc_vals, s2.sc_vals):    # use scaled values for the disctance calc.
                    d += abs(a1 - a2)
                if d < dist:
                    nearest = j
                    dist = d
                j += 1
            assert nearest is not None, f'ParRep::nearest(): neighbor not foound for {i}-th solution.'
            self.neigh.append([nearest, dist])
        pass

    def cube(self):  # define new cube (in ASF space), set A/R (in both ASF and A/R scales)
        # find pairs of neighbor solutions defining the largest cube
        mx_dis = 0.    # initialize distance
        s1 = None   # initialize solutions to undefined
        s2 = None
        for (i, n1) in enumerate(self.neigh):
            n2 = n1[0]  # nearest solution seq_id
            dis = n1[1]  # distance to the nearest solution
            if dis > mx_dis:
                s1 = i
                s2 = n2
                mx_dis = dis
        assert mx_dis > 0., f'ParRep::cube(): empty cube.'
        print(f'Largest cube is defined by solutions ({s1}, {s2}), cube size = {mx_dis}.')
        self.cubes.append(Cube(self.mc, self.sols[s1], self.sols[s2], mx_dis))     # ctor sets A/R values in mc.cr
        print(f'Cube added to ParRep. There are {len(self.cubes)} cubes defined.')
        # raise Exception(f'ParRep::cube() not implemented yet.')

    def summary(self):  # summary report
        raise Exception(f'ParRep::summary() not implemented yet.')

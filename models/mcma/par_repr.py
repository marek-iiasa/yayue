# import sys      # needed from stdout
# import os
# import numpy as np


class ParSol:     # one Pareto solution
    def __init__(self, itr_id, asf_vals, cr_vals):
        self.itr_id = itr_id    # iteration id (negative for corners)
        self.asf_vals = asf_vals  # list of ASF values
        self.cr_vals = cr_vals  # list of criteria values


class Cube:     # one Pareto solution
    def __init__(self, s1, s2):
        self.s1 = s1    # id of first solution defining the cube
        self.s2 = s2    # id of second solution defining the cube
        self.asp_asf = []   # list of A values in the ASF scale
        self.res_asf = []   # list of R values in the ASF scale
        self.asp_vals = []   # list of A values in the core scale
        self.res_vals = []   # list of R values in the core scale


class ParRep:     # representation of Pareto set
    def __init__(self, mc):
        self.mc = mc    # CtrMca object
        self.n_crit = mc.n_crit   # number of criteria
        self.n_corners = 0   # number of corners (one utopia + other inactive)
        self.sols = []  # Pareto-solutions (ParSol objects)
        self.neigh = []  # list of pairs [seq_id and distance to] defining closest neighbor
        self.cubes = []     # list of cubes (Cube objects, one cube for each iteration)

        self.ini_corners()  # initialize corner solutions
        self.nearest()
        # raise Exception(f'ParRep ctor not implemented yet.')

    def ini_corners(self):  # initialize corner solutions (each composed of one utopia and nadir of all others)
        cur_uto = 0     # index of the current utopia
        for (k, crit) in enumerate(self.mc.cr):     # one corner for each criterion
            asf_vals = []  # values of ASF values
            cr_vals = []  # values of crit (one utopia, others nadir)
            itr_id = -1 - k  # itr_id negative, start with -1
            for (i, cr) in enumerate(self.mc.cr):
                if i == cur_uto:
                    asf_val = self.mc.cafAsp
                    cr_val = cr.utopia
                else:
                    asf_val = 0.
                    cr_val = cr.nadir
                asf_vals.append(asf_val)
                cr_vals.append(cr_val)
            self.sols.append(ParSol(itr_id, asf_vals, cr_vals))
            self.n_corners += 1
            cur_uto += 1

    def nearest(self):  # for each solution find distance (in ASF scale) to the nearest neighbor
        # todo: implement update while adding new solutions (instead of computing all)
        for (i, s1) in enumerate(self.sols):
            dist = float('inf')
            nearest = None
            j = i + 1
            if j == len(self.sols):
                break
            while j < len(self.sols):
                s2 = self.sols[j]
                d = 0.
                for (a1, a2) in zip(s1.asf_vals, s2.asf_vals):
                    d += abs(a1 - a2)
                if d < dist:
                    nearest = j
                    dist = d
                j += 1
            assert nearest is not None, f'ParRep::nearest(): neighbor not foound for {i}-th solution.'
            self.neigh.append([nearest, dist])
        pass

    def cube(self):  # define new cube (in ASF space), set A/R (in both ASF and A/R scales)
        # find pairs of neighbor solutions defining largest cube
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
        assert mx_dis > 0., f'ParRep::cube(): cube is undefined.'
        print(f'Cube is defined by solutions ({s1}, {s2}), cube size = {mx_dis}.')
        raise Exception(f'ParRep::cube() not implemented yet.')

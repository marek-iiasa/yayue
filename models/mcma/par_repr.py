# import sys      # needed from stdout
# import os
# import numpy as np
# import pandas as pd
import math
from par_plot import *

# todo: add to ParSol:
#   prune marker (to close to another solution) to skip (almost) duplictated solutions during cube generation
#   improve info on CAF (global, in [U, N], vs itr in [A, R]


class ParSol:     # one Pareto solution
    def __init__(self, itr_id, vals, a_vals):
        self.itr_id = itr_id    # iter. id: positive indicates cube-seq, negative for Pareto-set corners
        self.vals = vals  # list of (not scaled) criteria values of the itr_id solution
        self.a_vals = a_vals  # list of achievement values
        # self.sc_vals = sc_vals  # list of scaled criteria values
        self.closeTo = None     # None replaced by itr_id of a first solution that is close
        self.distMx = None      # None replaced by L-inf distance for close/duplicated solutions
        # print(f'Solution of itr_id {itr_id}: criteria values: {self.vals}, (scaled: {self.sc_vals})')

    def is_close(self, s2):     # set self.closeTo and return True, if self is close to solution s2
        self.distMx = 0.
        for (a1, a2) in zip(self.a_vals, s2.a_vals):  # loop over scaled values of criteria
            dist = abs(a1 - a2)
            # todo: define a sensible minDist below
            minDist = 0.01
            if dist > minDist:   # L-inf (Tchebyshev) norm used for defining close/duplicated solutions
                self.distMx = None
                return False
            self.distMx = max(self.distMx, dist)
        # scaled values of all criteria differ less than minDist
        self.closeTo = s2.itr_id
        return True


# todo: add to Cube:
#   skip almost duplictated solution during cube generation
#   store diverse distance metrics (L1, L2, L-Inf)
#   storing in a df info on the progress (using diverse metrics)
#   improve control on printouts
#   consider improving cube generation efficiency (store/update info on neigbours, a new sol is in the current cube)


class Cube:     # defined (in scaled values) by the given pair of neighbor solutions
    def __init__(self, mc, s1, s2):
        self.mc = mc    # CtrMca object
        self.s1 = s1    # first solution defining the cube
        self.s2 = s2    # second solution defining the cube
        self.size = 0.      # cube size = currently L1 distance(s1, s2), for scaled crit values
        self.sizeL1 = 0.    # L1-norm size
        self.sizeL2 = 0.    # L2-norm size
        self.sizeLinf = 0.  # Linf (Tchebyshev)-norm size
        self.edges = []     # distance components (lengthes of edges for each criterion)
        self.degen = []     # True, if the corresponding edge was too small
        self.is_degen = False   # set to True, if any edge is too small
        # self.sc_asp = []   # list of scaled A values (used in selecting solutions that define the cube)
        # self.sc_res = []   # list of scaled R values
        self.asp = []   # list of A values in model units (to be used in the MCMA preferences)
        self.res = []   # list of R values in model units
        self.aspAch = []   # list of A values in Achievement scale (used to define self.asp/res)
        self.resAch = []   # list of R values in Achievement scale

        # calculate the cube size, and distance components (diffs for each criterion)
        for (a1, a2) in zip(s1.a_vals, s2.a_vals):  # loop over achievements of criteria
            dist = abs(a1 - a2)
            self.sizeL1 += dist  # Manhattan (L1) distance in criteria scaled-values
            self.sizeL2 += dist * dist  # L2 distance
            self.sizeLinf = max(dist, self.sizeLinf)  # Tchebyshev (Linf) distance
            self.edges.append(dist)
            if dist < mc.minDiff:   # difference between achivements too small --> cube dimension degenered
                self.is_degen = True    # the cube degenerated
                self.degen.append(True)  # current dimension degenerated
            else:
                self.degen.append(False)   # current dimension not degenerated
        self.sizeL2 = math.sqrt(self.sizeL2)     # cube size define by L2
        # diverse norms used for the size
        # self.size = self.sizeL1     # cube size define by L1
        # self.size = self.sizeL2     # cube size define by L2
        self.size = self.sizeLinf   # cube size define by Linf

    # define A/R values for spliting the cuboid (i.e., to find a new solution between s1 and s2)
    def setAR(self):
        for (i, cr) in enumerate(self.mc.cr):
            if not self.degen[i]:   # not degenerated edge
                cr.is_active = True
                v1 = self.s1.vals[i]
                v2 = self.s2.vals[i]
                a1 = self.s1.a_vals[i]
                a2 = self.s2.a_vals[i]
                if cr.isBetter(v1, v2):     # s1 has better crit. value than s2
                    cr.asp = v1
                    cr.res = v2
                    self.aspAch.append(a1)
                    self.resAch.append(a2)
                else:  # s2 has better crit. value than s1
                    cr.asp = v2
                    cr.res = v1
                    self.aspAch.append(a2)
                    self.resAch.append(a1)
            else:   # expand the degenerated edge (only for the AF regularizing term)
                cr.is_active = False
                # todo: the below is ad-hoc fix, needs to be improved
                # oldA = cr.val
                # oldR = cr.val
                oldA = self.s1.vals[i]
                oldR = self.s1.vals[i]
                achiv = self.s1.a_vals[i]   # CAF (same/similar for both solutions)
                expAch = 5.    # A/R expansion-span (in the achivements scale, i.e., [0, 100])
                if achiv < 50.:     # closer to Nadir, move A
                    new_ach = achiv + expAch
                    cr.asp = cr.ach2val(new_ach)     # get A value corresponding to achievement new_ach
                    self.aspAch.append(new_ach)
                    self.resAch.append(achiv)
                else:           # closer to Utopia, move R
                    new_ach = achiv - expAch
                    cr.res = cr.ach2val(new_ach)
                    self.aspAch.append(achiv)
                    self.resAch.append(new_ach)
                print(f'Crit. {cr.name} set to in-active: edge {self.edges[i]:.1f} expanded to {expAch:.1f} by moving:'
                      f'\n\tA from {oldA} to {cr.asp},  R from {oldR} to {cr.res}.')
                '''
                print(f'Crit. {cr.name} set to in-active: edge {self.edges[i]:.2e} expanded to {expAch:.2e} by moving:'
                      f'\n\tA from {oldA:.2e} to {cr.asp:.2e},  R from {oldR:.2e} to {cr.res:.2e}.')
                # old version, not good (too much A/R span
                span = 0.5 * abs(cr.utopia - cr.nadir)  # new span of the degenerated edge
                span2 = span / 2.   # A and R by span2, if possible within [U, N]
                distU = abs(cr.utopia - cr.asp)
                distN = abs(cr.nadir - cr.res)
                if distU < distN:  # empty edge closer to utopia
                    if span2 < distU:   # A can be moved towards U by dist2
                        cr.asp = oldA + cr.mult * span2
                        cr.res = oldR - cr.mult * span2
                    else:       # A can be moved to U by only a part of the dist2, thus R is moved more than span2
                        cr.asp = cr.utopia
                        cr.res = oldR - cr.mult * abs(span - distU)
                else:   # empty edge closer to nadir
                    if span2 < distN:   # R can be moved towards N by dist2
                        cr.asp = oldA + cr.mult * span2
                        cr.res = oldR - cr.mult * span2
                    else:       # R can be moved to N by only a part of the dist2, thus A is moved more than span2
                        cr.res = cr.nadir
                        cr.asp = oldA + cr.mult * abs(span - distN)
                '''
            self.asp.append(cr.asp)
            self.res.append(cr.res)
            # self.sc_asp.append(cr.sc_var * cr.asp)
            # self.sc_res.append(cr.sc_var * cr.res)
            # print(f'New cube A/R values for criterion {cr.name}: A {cr.asp:.3e}, R {cr.res:.3e}')

    # print: itr_ids of solutions defining the cube, cube size, lengths of cube edges (i.e., components of the size),
    # scaled criteria values defining the diameter-corners, scaled A/R values defining preferences for next iter.
    def lst(self, seq):     # seq: externally defined seq_no of the list of cubes
        val1 = ''
        val2 = ''
        for (v1, v2) in zip(self.s1.vals, self.s2.vals):    # criteria values
            val1 += f'{v1:.2e}, '
            val2 += f'{v2:.2e}, '
        edges = '['
        for dim in self.edges:
            edges += f'{dim:.1f} '
        edges += ']'
        print(f'cube[{seq}] sol_itr: ({self.s1.itr_id}, {self.s2.itr_id}), size={self.size:.1f}, '
              f'is_degen {self.is_degen}, edges={edges}, '
              f'\n\tcorners: ([{val1}], [{val2}])')

        # the below are for info only; not-scaled A/R values are used for actual preferences
        val1 = ''
        val2 = ''
        # todo: aspAch, resAch for degenerated criteria
        for (v1, v2) in zip(self.aspAch, self.resAch):    # CAF values for A/R
            val1 += f'{v1:.1f} '
            val2 += f'{v2:.1f} '
        print(f'\tNext preferences:  A [{val1}],  R [{val2}]')

    def lst_size(self, seq):  # seq: externally defined seq_no of the list of cubes
        print(f'cube[{seq}] sol_itr: [{self.s1.itr_id:3d}, {self.s2.itr_id:3d}], '
              f'sizes: L1={self.sizeL1:.2e}, L2={self.sizeL2:.2e}, Linf={self.sizeLinf:.2e}, degen {self.is_degen}')


class ParRep:     # representation of Pareto set
    def __init__(self, mc):         # initialize corners by regularized selfish solutions
        self.mc = mc        # CtrMca object
        self.sols = []      # Pareto-solutions (ParSol objects), exluding duplicated/close solutions
        self.clSols = []    # duplicated/close Pareto-solutions (ParSol objects)
        self.cubes = []     # list of cubes (Cube objects, one cube for each iteration)
        self.df_sol = None  # df with solutions prepared for plots; defined in the self.summary()

        mc.scale()          # (re)define scales for criteria values
        self.ini_corners()  # initialize corner solutions
        # raise Exception(f'ParRep ctor not implemented yet.')

    def pref(self):     # entry point for each iteration
        # define the largest cube (including new A/R definition directly in the mc.cr)

        # explore cubes generated by all pairs of solutions, skip cubes with inside solution(s)
        # fixme: make a list of alredy used cubes, and don't generate them again (the latter causes looping)
        # fixme: don't generate empty/"too small" cubes
        cube_lst = []   # list of all cubes without any solution inside amd not used yet
        for (i, s1) in enumerate(self.sols):
            j = i + 1
            while j < len(self.sols):
                # print(f'checking cube generated by solutions: ({i}, {j}).')
                s2 = self.sols[j]
                if self.cube_used(s1, s2):
                    # print(f'Cube defined by solutions ({s1.itr_id}, {s2.itr_id}) skipped (was already used).')
                    j += 1
                    continue
                is_inside = False   # solution inside the cube exists
                for (k, s) in enumerate(self.sols):     # check, if any solution is inside cube(s1, s2)
                    if k == i or k == j:
                        continue    # skip checking the corners
                    # check, if k-th solution is inside cube generated by solutions (i, j)
                    is_inside = self.chk_inside(s, s1, s2)
                    if is_inside:
                        break   # don't check the remaining solutions
                if not is_inside:
                    cube_lst.append(Cube(self.mc, s1, s2))
                    # print(f'Cube generated by solutions ({i}, {j}) added to the candidates for the largest cube.')
                # else:
                #     # noinspection PyUnboundLocalVariable
                #     print(f'Cube generated by solutions ({i}, {j}) skipped (has {k}-th solution inside).')
                j += 1

        c_best = None    # select from the cube_lst the cube having the largest size
        mx_size = 0.
        for c in cube_lst:
            if c_best is None:
                c_best = c
                mx_size = c.size
            else:
                if c.size > mx_size:
                    # print(f'Cube ({c.s1.itr_id}, {c.s2.itr_id}), size={c.size:.2e} replaces '
                    #       f'cube ({c_best.s1.itr_id}, {c_best.s2.itr_id}), size={c_best.size:.2e}')
                    c_best = c
                    mx_size = c.size
                # else:
                    # print(f'Cube ({c.s1.itr_id}, {c.s2.itr_id}), size={c.size:.2e} not larger than {mx_size:.2e} ')
        if c_best is None:
            raise Exception(f'ParRep::pref(): no cube defined.')
        # print(f'\nCube selected: ({c_best.s1.itr_id}, {c_best.s2.itr_id}), is_degen = {c_best.is_degen}, '
        #       f'size={c_best.size:.2e}')
        print(f'\nChecking the largested generated cube, setting the criteria activity and the A/R.')
        c_best.setAR()  # set in mc.cr the AR (in the solutions scale); store the AR also in the cube
        c_best.lst(len(self.cubes))
        print(f'Proceed to generation of the optimization problem.\n')

        self.cubes.append(c_best)   # add the cube to the list of cubes defining the corresponding iterations
        # print(f'The largest out of {len(cube_lst)} cubes has size = {mx_size:.2e}')

    def cube_used(self, s1, s2):  # check if the cube defined by pair of sols (itr1, itr2) was used
        itr1 = s1.itr_id
        itr2 = s2.itr_id
        for cube in self.cubes:
            i1 = cube.s1.itr_id
            i2 = cube.s2.itr_id
            if (itr1 == i1 and itr2 == i2) or (itr2 == i1 and itr1 == i2):
                # print(f'Cube defined by solutions of itr_id ({itr1}, {itr2}) was already used.')
                return True
        # print(f'Cube defined by solutions of itr_id ({itr1}, {itr2}) was not used yet.')
        return False

    def chk_inside(self, s, s1, s2):    # return True if s is inside cube(s1, s2)
        # it = s.itr_id
        # it1 = s1.itr_id
        # it2 = s2.itr_id
        for (i, cr) in enumerate(self.mc.cr):
            v = s.vals[i]
            v1 = s1.vals[i]
            v2 = s2.vals[i]
            if not min(v1, v2) < v < max(v1, v2):
                # print(f'crit {cr.name}: {v} is outside range of ({v1}, {v2}).')
                return False  # v outside the range [v1, v2]
            # else:
            #     print(f'crit {cr.name}: {v} is in the range of ({v1}, {v2}); continue check.')
        # print(f'solution {it} is between solutions ({it1}, {it2}).')
        return True    # all crit-vals of s are between the corresponding values of s1 and s2
        # raise Exception(f'ParRep::chk_inside() not implemented yeYt.')

    def addSol(self, itr_id):  # add solution (uses crit-values updated in mc.cr)
        vals = []     # crit values
        a_vals = []     # crit values
        # sc_vals = []  # scaled crit values
        for cr in self.mc.cr:
            vals.append(cr.val)
            # sc_vals.append(cr.sc_var * cr.val)
            cr.val2ach()    # compute and set achievement value
            a_vals.append(cr.a_val)
        # for cr in self.mc.cr:   # compute achievement values
        #     sc = self.mc.cafAsp / abs(cr.utopia - cr.nadir)
        #     # if cr.mult == 1:    # maximized crit.
        #     #     a_val = sc * (cr.utopia - cr.val)
        #     # else:
        #     #     a_val = sc * (cr.val - cr.utopia)
        #     # todo: check if correct also for negative U, N
        #     # todo: check consistency a_val and val for all criteria
        #     a_val = abs(cr.mult * sc * (cr.utopia - cr.val))
        #     a_vals.append(a_val)
        #     a_frac = abs(sc * cr.val)  # value as a fraction of the range
            print(f'crit {cr.name} ({cr.attr}): a_val={cr.a_val:.2f}, val={cr.val:.2e}, '  # a_frac={a_frac:.2e}, '
                  f'U {cr.utopia:.2e}, N {cr.nadir:.2e}')
        new_sol = ParSol(itr_id, vals, a_vals)
        is_close = False
        for s2 in self.sols:   # check if the new sol is close to any previous unique (i.e., not-close) sol
            if new_sol.is_close(s2):
                is_close = True
                break
        if is_close:
            self.clSols.append(new_sol)
            print(f'Solution {itr_id = } duplicates itr_id {new_sol.closeTo} (L-inf = {new_sol.distMx:.1e}. '
                  f'There are {len(self.clSols)} duplicated Pareto solutions.')
        else:
            self.sols.append(new_sol)
            print(f'Solution {itr_id = } added to ParRep. There are {len(self.sols)} unique Pareto solutions.')

    def ini_corners(self):  # initialize corner solutions (each composed of one utopia and nadir of all others)
        # todo: consider to additionally run the regularized selfish optimization (also to get values of vars)
        #   this can be done rather in the driver than here.
        print(f'\nGenerating {self.mc.n_crit} virtual solutions (defining corners of the Pareto set).')
        cur_uto = 0     # index of the current utopia
        for (k, crit) in enumerate(self.mc.cr):     # one corner for each criterion
            vals = []  # crit values
            a_vals = []  # achievement values
            # sc_vals = []  # scaled crit values (one utopia, others nadir)
            itr_id = -1 - k  # itr_id negative, start with -1
            for (i, cr) in enumerate(self.mc.cr):
                if i == cur_uto:
                    val = cr.utopia
                    a_val = self.mc.cafAsp  # value of CAF at A
                    # sc_val = cr.sc_var * val
                else:
                    val = cr.nadir
                    a_val = 0.
                    # sc_val = cr.sc_var * val
                vals.append(val)
                a_vals.append(a_val)
                # sc_vals.append(sc_val)
            self.sols.append(ParSol(itr_id, vals, a_vals))
            cur_uto += 1

    def sol_seq(self, itr_id):  # return seq_no in self.sols[] for the itr_id
        for (i, s) in enumerate(self.sols):
            if s.itr_id == itr_id:
                return i
        raise Exception(f'ParRep::sol_seq(): {itr_id} not in the solution set.')

    def lst_cubes(self):  # list cubes
        for (i, c) in enumerate(self.cubes):
            c.lst(i)
        print()
        for (i, c) in enumerate(self.cubes):
            c.lst_size(i)

    def summary(self):  # summary report
        print('\nList of cubes:')
        self.lst_cubes()
        print('\n')

        # prepare df with solutions for plot2D
        cols = ['itr_id']
        for cr in self.mc.cr:   # space for criteria values
            cols.append(cr.name)
        for cr in self.mc.cr:   # space for criteria achievements
            cols.append('a_' + cr.name)
        # self.df_sol = pd.DataFrame(columns=cols)  # not needed, if df created by list of row dictionaries
        rows = []   # each row with crit attributes for a solution
        for s in self.sols:
            new_row = {'itr_id': s.itr_id}
            # for (i, cr) in enumerate(self.mc.cr):     # results in different column seq. than the two loops bellow
            #     new_row.update({cr.name: s.vals[i]})
            #     new_row.update({'a_' + cr.name: s.a_vals[i]})
            for (i, cr) in enumerate(self.mc.cr):   # cols with crit values
                new_row.update({cr.name: s.vals[i]})
            for (i, cr) in enumerate(self.mc.cr):   # cols with crit achievements
                new_row.update({'a_' + cr.name: s.a_vals[i]})
            rows.append(new_row)
            # df2 = pd.DataFrame(new_row, index=list(range(1)))
            # self.df_sol = pd.concat([self.df_sol, df2], axis=0, ignore_index=True)    # results in compatibility warn.
            # self.df_sol.loc[len(self.df_sol)] = new_row   # does not work
            # last = len(self.df_sol)
            # self.df_sol.loc[last] = new_row   # also does not work
            # self.df_sol.append(new_row, ignore_index=True)    # append() removed from pd
        self.df_sol = pd.DataFrame(rows)
        # self.df_sol = pd.DataFrame.from_dict(rows)
        f_name = self.mc.ana_dir + '/df_sol.csv'
        self.df_sol.to_csv(f_name, index=True)
        print(f'{len(self.sols)} unique solutions stored in {f_name}. '
              f'{len(self.clSols)} duplicated solutions not stored.')

        # plot solutions
        # plot2D(self.df_sol, self.mc.cr, self.mc.ana_dir)    # 2D plot
        plot3D(self.df_sol, self.mc.cr, self.mc.ana_dir)    # 3D plot

        # todo: 3D plots need reconfiguration: either the change the pyCharm default browser to chrome or modify the
        #  Safari version to either Safari beta or to Safari technology preview (see the Notes)
        # self.plot3()
        # self.plot3a()
        # raise Exception(f'ParRep::summary() not finished yet.')

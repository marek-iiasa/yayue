# import sys      # needed from stdout
# import os
# import numpy as np
# import pandas as pd
# import math
from cube import *
from plots import *


class ParRep:     # representation of Pareto set
    def __init__(self, mc):         # initialize corners by regularized selfish solutions
        self.mc = mc        # CtrMca object
        self.cfg = mc.cfg        # CtrMca object
        self.sols = []      # Pareto-solutions (ParSol objects), excluding duplicated/close solutions
        self.clSols = []    # duplicated/close Pareto-solutions (ParSol objects)
        self.cubes = Cubes(self)  # the object handling all cubes
        self.cur_cube = None  # cube_id of the last used cube
        self.from_cube = False   # next preferences from a cube
        self.n_corner = 0       # number of already generated selfish solutions
        self.df_sol = None  # df with solutions prepared for plots; defined in the self.summary()
        self.dir_name = self.cfg.get('resDir')

        print('Initializing Pareto-set exploration. --------------------')
        mc.scale()          # (re)define scales for criteria values
        # self.ini_corners()  # selfish solutions must be generated and computed one-by-one
        # print('Initialization completed. Start the exploration --------------------\n')
        # raise Exception(f'ParRep ctor not implemented yet.')

    def pref(self):     # entry point for each new iteration
        if not self.from_cube:  # no cubes yet, generate and compute selfish solution
            for (i, cr) in enumerate(self.mc.cr):
                if i == self.n_corner:  # selfish sol. for i-th criterion
                    print(f'Computing selfish solution for crit: {cr.name}.')
                    cr.is_active = True
                    cr.asp = cr.utopia
                else:
                    cr.is_active = False
                    delta = abs(cr.utopia - cr.nadir) / 2.  # take half of the (utopia, nadir) range
                    cr.asp = cr.utopia - cr.mult * delta
                cr.is_fixed = False
                cr.res = cr.nadir
            self.n_corner += 1
        else:   # all selfish solutions ready
            cube = self.cubes.select()  # the cube defining A/R for new iteration
            if cube is None:
                self.mc.cur_stage = 6  # terminate the analysis
                return
                # raise Exception(f'ParRep::pref(): no cube defined.')
            self.cur_cube = cube.id     # remember cur_cube to attach its id to the solution (after it will be provided)
            # print(f'\nSetting the criteria activity and the A/R for the selected cube.')
            cube.setAR()     # set AR values (directly in the Crit objects)
            cube.lst(self.cur_cube)
            print(f'Proceed to generation of the optimization problem.')
            # print(f'The largest out of {len(cube_lst)} cubes has size = {mx_size:.2e}')

    def is_inside(self, s, s1, s2):    # return False if s is outside cube(s1, s2)
        # it = s.itr_id
        # it1 = s1.itr_id
        # it2 = s2.itr_id
        for (i, cr) in enumerate(self.mc.cr):
            v = s.vals[i]
            v1 = s1.vals[i]
            v2 = s2.vals[i]
            if not min(v1, v2) <= v <= max(v1, v2):
                # print(f'sol {it} is between sols ({it1}, {it2}): crit {cr.name}: {v} is outside ({v1}, {v2}).')
                return False  # v outside the range [v1, v2]
            # else:
            #     print(f'crit {cr.name}: {v} is in the range of ({v1}, {v2}); continue check.')
        # print(f'solution {it} is between solutions ({it1}, {it2}).')
        return True    # all crit-vals of s are between the corresponding values of s1 and s2
        # raise Exception(f'ParRep::chk_inside() not implemented yeYt.')

    def addSol(self, itr_id):  # add solution (uses crit-values updated in mc.cr). called from CtrMca::updCrit()
        assert self.mc.is_opt, f'addSol called for non-optimal solution'
        vals = []     # crit values
        a_vals = []     # crit values
        # sc_vals = []  # scaled crit values
        for cr in self.mc.cr:
            vals.append(cr.val)
            # sc_vals.append(cr.sc_var * cr.val)
            cr.a_val = cr.val2ach(cr.val)    # compute and set achievement value
            a_vals.append(cr.a_val)
            # print(f'crit {cr.name} ({cr.attr}): a_val={cr.a_val:.2f}, val={cr.val:.2e}, '  # a_frac={a_frac:.2e}, '
            #       f'U {cr.utopia:.2e}, N {cr.nadir:.2e}')
        new_sol = ParSol(itr_id, self.cur_cube, vals, a_vals)
        if self.cur_cube is not None:
            c = self.cubes.get(self.cur_cube)     # parent cube
            new_sol.neigh_inf(c)   # info on location within the solutions of the parent cube

        is_close = False
        for s2 in self.sols:   # check if the new sol is close to any previous unique (i.e., not-close) sol
            if new_sol.is_close(s2):
                is_close = True
                break
        if is_close:
            self.clSols.append(new_sol)
            print(f'Solution {itr_id = } duplicates itr_id {new_sol.closeTo} (L-inf = {new_sol.distMx:.1e}). '
                  f'There are {len(self.clSols)} duplicated Pareto solutions.')
        else:   # check dominance with all sols found so far
            is_pareto = True
            for s2 in self.sols:   # check if the new sol is close to any previous unique (i.e., not-close) sol
                cmp_ret = new_sol.cmp(self.mc, s2)
                if cmp_ret == 0:    # is Pareto
                    continue    # check next solution
                elif cmp_ret > 0:   # new_sol dominates s2
                    print(f'\t-------------     current solution[{itr_id}] dominates solution[{s2.itr_id}].')
                    s2.domin = -itr_id      # mark s2 as dominated by the new solution, and continue checking next sol.
                else:           # new_sol is dominated by s2
                    print(f'\t-------------     current solution[{itr_id}] is dominated by solution[{s2.itr_id}].')
                    is_pareto = False
                    break
            if is_pareto:
                self.sols.append(new_sol)
                print(f'Solution {itr_id = } added to ParRep. There are {len(self.sols)} unique Pareto solutions.')
                self.mk_cubes(new_sol)    # define cubes generated by this solution

        if self.n_corner == len(self.mc.cr):
            self.from_cube = True   # next preferences to be generated from cubes

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
            new_sol = ParSol(itr_id, None, vals, a_vals)
            for s2 in self.sols:  # check if the new sol is close to any previous unique (i.e., not-close) sol
                if new_sol.is_close(s2):
                    print(f'Selfish solution {new_sol.itr_id} too close to another selfish solution: {new_sol.closeTo} '
                          f'(L-inf = {new_sol.distMx:.1e}).')
                    raise Exception('The problem not suitable for MCMA.')
            self.sols.append(new_sol)
            print(f'Solution {itr_id = } added to ParRep. There are {len(self.sols)} unique Pareto solutions.')
            self.mk_cubes(new_sol)    # define cubes generated by this solution
            cur_uto += 1

    def mk_cubes(self, s):  # generate cubes defined by the new solution s with each of previous solutions
        # store_all = False
        verb = False
        for s1 in self.sols:
            if s.itr_id == s1.itr_id:
                continue    # skip self (already included in self.sols)
            n_cube = aCube(self.mc, s1, s)
            self.cubes.add(n_cube)  # cubes are made for all pairs of solutions
            if verb:
                print(f'New cube[{n_cube.id}] of sols [{s1.itr_id}, {s.itr_id}], size {n_cube.size:2f}.')
            '''
            n_cube.empty = True
            mark = ''
            for s2 in self.sols:     # check, if s2 is inside new cube(s1, s)
                # check, if the new solution is inside cube generated by solutions [s1, s2]
                if s.itr_id == s2.itr_id or s1.itr_id == s2.itr_id:
                    continue  # skip self (already included in self.sols)
                is_inside = self.chk_inside(s2, s1, s)
                if is_inside:
                    n_cube.empty = False
                    # print(f'Cube generated by solutions [{s1.itr_id}, {s.itr_id}] contains solution [{s2.itr_id}].')
                    mark = 'NOT '
                    break   # don't check the remaining solutions
            if store_all or n_cube.empty:
                self.cubes.add(n_cube)  # cubes are made for all pairs of solutions
                if verb:
                    print(f'New cube generated by solutions [{s1.itr_id}, {s.itr_id}] is {mark}empty.')
        # raise Exception(f'ParRep::mk_cubes() not implemented yet.')
            '''

    def sol_seq(self, itr_id):  # return seq_no in self.sols[] for the itr_id
        for (i, s) in enumerate(self.sols):
            if s.itr_id == itr_id:
                return i
        raise Exception(f'ParRep::sol_seq(): {itr_id} not in the solution set.')

    def summary(self):  # summary report
        # self.cubes.lst_cubes()  # list cubes
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
            cube_id = s.cube_id
            if cube_id is None:     # selfish solutions are not generated from a cube
                new_row.update({'parents': f'[none]'})
            else:
                cube = self.cubes.get(cube_id)  # parent cube
                new_row.update({'parents': f'[{cube.s1.itr_id}, {cube.s2.itr_id}]'})
            new_row.update({'domin': s.domin})
            rows.append(new_row)
            # df2 = pd.DataFrame(new_row, index=list(range(1)))
            # self.df_sol = pd.concat([self.df_sol, df2], axis=0, ignore_index=True)    # results in compatibility warn.
            # self.df_sol.loc[len(self.df_sol)] = new_row   # does not work
            # last = len(self.df_sol)
            # self.df_sol.loc[last] = new_row   # also does not work
            # self.df_sol.append(new_row, ignore_index=True)    # append() removed from pd
        self.df_sol = pd.DataFrame(rows)
        # self.df_sol = pd.DataFrame.from_dict(rows)
        # f_name = self.mc.ana_dir + '/df_sol.csv'
        # f_name = self.mc.ana_dir + '/df_sol1M.csv'
        f_name = f'{self.dir_name}df_sol.csv'
        self.df_sol.to_csv(f_name, index=True)
        print(f'{len(self.sols)} unique solutions stored in {f_name}. '
              f'{len(self.clSols)} duplicated solutions not stored.')

        # plot solutions
        plots = Plots(self.cfg, self.df_sol, self.mc.cr)    # 3D plot
        plots.plot2D()    # 2D plot
        plots.plot3D()    # 3D plot
        plots.plot_parallel() # Parallel coordinates plot

        # todo: 3D plots need reconfiguration: either the change the pyCharm default browser to chrome or modify the
        #  Safari version to either Safari beta or to Safari technology preview (see the Notes)
        # self.plot3()
        # self.plot3a()
        # raise Exception(f'ParRep::summary() not finished yet.')

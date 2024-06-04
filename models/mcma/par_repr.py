import pandas as pd
from operator import itemgetter
from .cube import ParSol, Cubes, aCube
# from .corners import Corners


# noinspection SpellCheckingInspection
# progress in Pareto set representation
class ParProg:
    def __init__(self, parRep):     # initialize corners by regularized selfish solutions
        self.parRep = parRep        # ParRep object
        self.steps = []             # list of reporting steps (max distances between neighbors
        self.cur_step = 0           # index of the current step
        self.neigh = {}             # neighbors for each step
        self.df_stages = None
        #
        self.ini_steps()            # initialize steps

    def ini_steps(self):  # steps of progress
        self.steps = [50, 30, 20, 10, 7, 5, 3, 2, 1]

    def update(self, cube_size, is_last):     # store info of pairs of neighbors waiting for processing
        if cube_size > self.steps[self.cur_step] and not is_last:
            return
        itr = self.parRep.cur_itr
        n_sol = len(self.parRep.sols)
        # pairs = self.parRep.neigh.copy()
        pairs = self.parRep.cubes.cand.copy()
        print(f'itr {itr}; {n_sol} Pareto solutions computed, {len(pairs)} neighbor-pairs remain for processing.')
        if not is_last:
            self.neigh.update({self.cur_step: (itr, n_sol, len(pairs), round(cube_size, 2), pairs)})
            # print(f'List of {len(pairs)} cubes at step {self.cur_step} (distance {cube_size}) stored.')
            self.cur_step += 1
        else:
            self.neigh.update({self.cur_step: (itr, n_sol, len(pairs), round(cube_size, 2), pairs)})
            print(f'cur_step {self.cur_step}, itr {itr}, n_sol {n_sol}.')
            if len(pairs) > 0:
                print(f'{len(pairs)} cubes not processed.')
            else:
                print(f'All cubes were processed.')

    def summary(self):     # proccess info on the computation progress
        cubes = self.parRep.cubes  # object of Cubes class
        n_itrs = self.parRep.cur_itr + 1    # cur_itr counted from 0
        print(f'\nOverall during {n_itrs} itrs {len(self.parRep.sols)} Pareto sols. were computed, '
              f'{len(cubes.all_cubes)} hyper-cubes were generated.')
        print(f'\nSummary data of {len(self.neigh)} computation stages.')
        summary_list = []
        for step, info in self.neigh.items():
            itr = info[0]
            n_sol = info[1]
            n_cubes = info[2]
            mx_cube = info[3]
            summary_list.append((step, itr, self.steps[step], n_sol, n_cubes, mx_cube))
            print(f'Stage {step} (stage_UpBnd {self.steps[step]}, mxCubeSize {mx_cube}): during {itr} itrs '
                  f'{n_sol} sols. computed, {n_cubes} remained for processing.')
            # uncomment only when needed (the below produces a lot of printouts)
            '''
            if step < 6:
                continue
            cubes_id = info[4]
            for cube_id in cubes_id:
                acube = cubes.get(cube_id)
                print(f'Size of cube[{cube_id}]: {round(acube.size, 2)}, mx_cube = {mx_cube}')
            '''

        self.df_stages = pd.DataFrame(summary_list, columns=['step', 'itr', 'upBnd', 'n_sol', 'n_cubes', 'mx_cube'])


# noinspection SpellCheckingInspection
class ParRep:     # representation of Pareto set
    def __init__(self, wflow):         # initialize corners by regularized selfish solutions
        self.wflow = wflow        # CtrMca object
        self.mc = wflow.mc        # CtrMca object
        self.cfg = wflow.cfg   # Config object
        self.sols = []      # Pareto-solutions (ParSol objects), excluding duplicated/close solutions
        self.clSols = []    # duplicated/close Pareto-solutions (ParSol objects)
        self.cubes = Cubes(self)  # the object handling all cubes
        self.progr = ParProg(self)  # the object handling computation progress
        self.cur_cube = None  # cube_id of the last used cube
        self.cur_itr = None   # current itr_id
        self.from_cube = False   # next preferences from a cube
        self.n_corner = 0       # number of already generated selfish solutions
        self.ini_obj = None     # object a class handling initial solutions
        self.df_sol = None  # df with solutions prepared for plots; defined in the self.summary()
        self.dir_name = self.cfg.get('resDir')

        print('Initializing Pareto-set exploration. --------------------')

    def pref(self, neutral=False):     # entry point for each new iteration
        if neutral:     # set A/R for neutral solution
            for cr in self.mc.cr:
                cr.setAR()
        else:   # set preferences from the selected cube
            cube = self.cubes.select()  # the cube defining A/R for new iteration
            if cube is not None:
                self.progr.update(cube.size, False)
            # else:
            #     self.progr.update(0.)
            if cube is None:
                self.wflow.cur_stage = 6  # terminate the analysis
                return
                # raise Exception(f'ParRep::pref(): no cube defined.')
            self.cur_cube = cube.id     # remember cur_cube to attach its id to the solution (after it will be provided)
            # print(f'\nSetting the criteria activity and the A/R for the selected cube.')
            cube.setAR()     # set AR values (directly in the Crit objects)
            cube.lst(self.cur_cube)
            if self.cfg.get('verb') > 1:
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

    def addSol(self, itr_id):  # add solution (uses crit-values updated in mc.cr). called from CtrMca::updCrit()
        assert self.mc.is_opt, f'ParRep::addSol() called for non-optimal solution'
        self.cur_itr = itr_id
        vals = []     # crit values
        a_vals = []     # crit achievements
        # sc_vals = []  # scaled crit values
        for cr in self.mc.cr:
            vals.append(cr.val)
            cr.a_val = cr.val2ach(cr.val)    # compute and set achievement value
            a_vals.append(cr.a_val)
            if self.cfg.get('verb') > 3:
                print(f'crit {cr.name} ({cr.attr}): a_val={cr.a_val:.2f}, val={cr.val:.2e}, '  # a_frac={a_frac:.2e}, '
                      f'U {cr.utopia:.2e}, N {cr.nadir:.2e}')
        new_sol = ParSol(itr_id, self.cur_cube, vals, a_vals)
        if self.cur_cube is not None:   # cur_cube undefined during computation of selfish solutions
            c = self.cubes.get(self.cur_cube)     # parent cube
            new_sol.neigh_inf(c)   # info on location within the solutions of the parent cube

        is_close = False
        for s2 in self.sols:   # check if the new sol is close to any previous unique (i.e., not-close) sol
            if new_sol.is_close(s2):
                is_close = True
                break
        is_pareto = True
        if is_close:
            is_pareto = False
            self.clSols.append(new_sol)
            print(f'Solution[{itr_id}] duplicates sol[{new_sol.closeTo}] (L-inf = {new_sol.distMx:.1e}). '
                  f'There are {len(self.clSols)} duplicated Pareto solutions.')
        else:   # unique solution; check dominance with all Pareto-sols found so far
            toPrune = []    # tmp list of solutions dominated by the current sol
            for s2 in self.sols:   # check if the new sol is close to any previous unique (i.e., not-close) sol
                cmp_ret = new_sol.cmp(s2)
                if cmp_ret == 0:    # is Pareto
                    continue    # check next solution
                elif cmp_ret > 0:   # new_sol dominates s2
                    if self.cfg.get('verb') > -1:
                        print(f'\t-------------     current solution[{itr_id}] dominates solution[{s2.itr_id}].')
                    s2.domin = -itr_id      # mark s2 as dominated by the new solution, and continue checking next sol.
                    toPrune.append(s2)
                else:           # new_sol is dominated by s2
                    if self.cfg.get('verb') > -1:
                        print(f'\t-------------     current solution[{itr_id}] is dominated by solution[{s2.itr_id}].')
                    is_pareto = False
                    break
            if is_pareto:
                self.sols.append(new_sol)   # add to self.sols
                if self.cfg.get('verb') > 1:
                    print(f'Solution {itr_id = } added to ParRep. There are {len(self.sols)} unique Pareto solutions.')
                self.mk_cubes(new_sol)    # define cubes generated by this solution
            for s2 in toPrune:   # remove dominated solutions from self.sols
                print(f'\tsolution[{s2.itr_id}] dominated by solution[{itr_id}] removed from self.sols.')
                self.sols.remove(s2)
        return is_pareto

    def mk_cubes(self, s):  # generate cubes defined by the new solution s with each of previous distinct-solution
        # store_all = False
        verb = self.cfg.get('verb') > 2
        for s1 in self.sols:
            if s.itr_id == s1.itr_id:
                continue    # skip self (already included in self.sols)
            n_cube = aCube(self.mc, s1, s)
            self.cubes.add(n_cube)  # adds to the list only empty and large-enough cubes
            if verb:
                print(f'New cube[{n_cube.id}] of sols [{s1.itr_id}, {s.itr_id}], size {n_cube.size:2f}.')

    def sol_seq(self, itr_id):  # return seq_no in self.sols[] for the itr_id
        for (i, s) in enumerate(self.sols):
            if s.itr_id == itr_id:
                return i
        raise Exception(f'ParRep::sol_seq(): {itr_id} not in the solution set.')

    def summary(self):  # summary report
        # self.cubes.lst_cubes()  # list cubes
        cand = sorted(self.cubes.cand, key=itemgetter(1), reverse=True)  # sort by size (just getting the largest)
        if len(cand) > 0:
            mx_size = cand[0][1]
        else:
            mx_size = 0
        print('\n')
        self.progr.update(mx_size, True)   # store info on the unprocessed cubes, if any remain
        self.progr.summary()   # process info on the computation progress

        # prepare df with solutions for plots and storing as csv
        cols = ['itr_id']
        for cr in self.mc.cr:   # space for criteria values
            cols.append(cr.name)
        for cr in self.mc.cr:   # space for criteria achievements
            cols.append('a_' + cr.name)
        rows = []   # each row with crit attributes for a solution
        for s in self.sols:
            new_row = {'itr_id': s.itr_id}
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
        self.df_sol = pd.DataFrame(rows)

import datetime
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
        self.cubes2proc = {}        # cubes waiting for processing at each (progress) step
        # self.neigh = {}           # neighbors for each step
        self.df_stages = None
        #
        self.ini_steps()            # initialize steps

    def ini_steps(self):  # steps of progress
        self.steps = [50, 30, 20, 10, 7, 5, 3, 2, 1]

    def updCubeInf(self, cube_size, is_last):     # store info on cubes waiting for processing
        if cube_size > self.steps[self.cur_step] and not is_last:
            return
        itr = self.parRep.cur_itr
        n_sol = len(self.parRep.sols)
        # pairs = self.parRep.neigh.copy()
        cubesCand = self.parRep.cubes.cand.copy()
        # add info to the dict
        print(f'itr {itr}; {n_sol} Pareto solutions computed, {len(cubesCand)} cubes remain for processing.')
        self.cubes2proc.update({self.cur_step: (itr, n_sol, len(cubesCand), round(cube_size, 2), cubesCand)})
        if not is_last:
            self.cur_step += 1
        else:
            print(f'cur_step {self.cur_step}, itr {itr}, n_sol {n_sol}.')
            if len(cubesCand) > 0:
                print(f'{len(cubesCand)} cubes not processed.')
            else:
                print(f'All cubes were processed.')

    def summary(self):     # proccess info on the computation progress
        cubes = self.parRep.cubes  # object of Cubes class
        n_itrs = self.parRep.cur_itr + 1    # cur_itr counted from 0
        print(f'\nOverall during {n_itrs} itrs {len(self.parRep.sols)} Pareto sols. were computed, '
              f'{len(cubes.all_cubes)} hyper-cubes were generated.')
        print(f'\nSummary cubes-data at {len(self.cubes2proc)} computation stages.')
        summary_list = []
        for step, info in self.cubes2proc.items():
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
class ParRep:     # representation of the Pareto set
    def __init__(self, wflow):         # initialize corners by regularized selfish solutions
        self.wflow = wflow        # WrkFlow object
        self.mc = wflow.mc        # CtrMca object
        self.cfg = wflow.cfg   # Config object
        self.sols = []      # Pareto-solutions (ParSol objects), excluding duplicated/close solutions
        self.sols_wrk = []  # work-list of solutions (to be used for finding a most distant (in L^inf) sol-pair
        self.clSols = []    # duplicated/close Pareto-solutions (ParSol objects)
        self.cubes = Cubes(self)  # the object handling all cubes
        self.progr = ParProg(self)  # the object handling computation progress
        self.cur_cube = None  # cube_id of the last used cube
        self.cur_itr = None   # current itr_id
        self.sampleSeq = 0    # number of distribution samples stored
        self.neigh = {}       # neighbors in the current solutions set {itr_id1: [itr_id2, dist]} (dominated excluded)
        self.distances = []     # distances between current neighbors
        self.allDist = {}     # copies of distances stored for each sample
        self.neighInf = {}    # key: cur_itr, [max_dist, itr_id1, itr_id2, min_dist]
        self.log_min = 100    # min cube-size in the current block
        self.log_max = 0      # max cube-size in the current block
        self.log_mxCubes = 0  # max number of cubes in the current block
        self.log_block = self.mc.opt('logBlock', 1000)
        self.log_next = self.log_block
        self.log_dict = {}
        self.from_cube = False   # next preferences from a cube
        self.n_corner = 0       # number of already generated selfish solutions
        self.ini_obj = None     # object a class handling initial solutions
        self.df_sol = None  # df with solutions prepared for plots; defined in the self.summary()
        self.dir_name = self.cfg.get('resDir')

        print('Initializing Pareto-set exploration. --------------------')

    def get(self, s_id):    # return the solution by its id
        for s in self.sols:
            if s.itr_id == s_id:
                return s
        raise Exception(f'ParRep::get() - solution id {s_id} not in the set of solutions.')

    def solDistr(self):     # distribution of distances between neighbor solutions, called by sizeLog
        #  Note: neighbor (for each solution) is the closest other solution
        n_sols = len(self.sols)       # number of Pareto-sols computed so far
        self.neigh = {}         # renew the working dict for neighbors
        for ind1 in range(n_sols - 1):  # the last solution has no next to compare with
            self.neigh.update({self.sols[ind1].itr_id: [None, float('inf')]})
        for ind1 in range(n_sols - 1):  # the last solution has no next to compare with
            s1 = self.sols[ind1]
            id1 = s1.itr_id
            # if id1 == 98 or id1 == 119:
            #     print(f'trap s1: {id1 = }, {n_sols = }')
            #     pass
            if s1.domin < 0:
                print(f'dominated solution s1 {id1}i skipped in solDistr().')
                continue    # skip dominated solutions
            neigh = self.neigh[id1]
            s1Dist = neigh[1]     # min Linf-distance between s1 and the other (found so far) closest solutions
            # if id1 == 12:
            #     print('trap')
            #     pass
            # pass
            for ind2 in range(ind1 + 1, n_sols):    # find the closest neighbor
                s2 = self.sols[ind2]
                id2 = s2.itr_id
                # if id1 in [97, 98, 99] and id2 in [118, 119, 120]:
                #     print(f'trap s2: {id1 = }, {id2 = }, {n_sols = }')
                #     pass
                if s2.domin < 0:
                    raise Exception(f'ParRep::solDistr() - dominated solution in self.sols (id: {id2}).')
                # print(f'ind1 {ind1}, ind2 {ind2}: s1.itr_id {s1.itr_id}, s2.itr_id {s2.itr_id}')
                if id1 == id2:
                    raise Exception(f'ParRep::solDistr() - duplicate itr_id: {s1.itr_id}.')
                dist = 0.   # Linf distance between the current pair of solutions
                for (a1, a2) in zip(s1.a_vals, s2.a_vals):  # loop over achievements of criteria
                    edge = abs(a1 - a2)
                    dist = max(dist, edge)      # Linf dist defined by the max edge
                if dist < s1Dist:     # a closer (than any previously found) s1 neighbor found
                    s1Dist = dist     # distance to the closest neighbor
                    self.neigh.update({id1: [id2, s1Dist]})     # update neighbor of s1
                '''
                # The below prevents finding another (say s3) neighbor of s2, if s2 is closer to s1 than s2 to s3.
                s2prev = self.neigh.get(id2)    # previosly found neighbor of s2
                prevDist = s2prev[1]        # previously found distance between s2 and this neighbor
                if dist < prevDist:
                    self.neigh.update({id2: [id1, dist]})     # update previously found s2 neighbor
                '''
                # continue with the next s2
            # continue with the next s1
            pass
        # finished all pairs of Pareto-solutions found so far
        maxDist = 0.    # max distance between closest neighbors
        minDist = float('inf')  # min distance between closest neighbors
        mxPair = [None, None]     # consists of: itr_id the other solution and the distance between them
        self.distances = []     # to clean previous valuees
        for id1, pair in self.neigh.items():
            dist = pair[1]
            # maybe store here the pairs of sols distant by more than the (currently desired?) gap
            self.distances.append(dist)  # distribution of distances (for plots?)
            if dist > maxDist:
                maxDist = dist
                mxPair = [id1, pair[0]]
            if dist < minDist:
                minDist = dist
        #
        self.distances.sort()
        # print(f'Distances between {len(self.distances)} neighbor-pairs: min {self.distances[0]:.2e}, '
        #       f'max {self.distances[-1]:.2e}')
        self.allDist.update({self.cur_itr: self.distances})  # distances stored for each sample
        self.neighInf.update({self.cur_itr: [maxDist, mxPair[0], mxPair[1], minDist]})  # summary inf on all neighbors
        print(f'\nSample {self.sampleSeq} of {len(self.distances)} neighbor solutions: '
              f'maxDist {maxDist:.3f} ({mxPair[0]}, {mxPair[1]}), minDist {minDist:.3f}')
        self.sampleSeq += 1
        pass

    def pref(self, neutral=False):     # entry point for each new iteration
        if neutral:     # set A/R for the neutral solution
            for cr in self.mc.cr:
                cr.setAR()
        elif self.wflow.is_par_rep:   # set preferences from the selected cube
            cube = self.cubes.select()  # the cube defining A/R for new iteration
            if cube is not None:
                self.progr.updCubeInf(cube.size, False)     # check if the next comp-stage was reached
            # else:
            #     self.progr.updCubeInf(0.)
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
        else:       # usr-defined set of AR
            retval = self.mc.usrPref()  # True, if AR set
            if not retval:
                self.wflow.cur_stage = 6  # all ARs processed, terminate the analysis

    def is_inside(self, s, s1, s2):    # return False if s is outside cube(s1, s2)
        if self.mc.opt('neighZN', False):
            it = s.itr_id
            it1 = s1.itr_id
            it2 = s2.itr_id
            r = 0.
            eps = 1.e-4
            for (i, cr) in enumerate(self.mc.cr):
                r = max(r, abs(s1.vals[i] - s2.vals[i]))
            for (i, cr) in enumerate(self.mc.cr):
                v = s.vals[i]
                v1 = s1.vals[i]
                v2 = s2.vals[i]
                if not max(v1, v2) - r <= v + eps <= min(v1, v2) + r:
                    # print(f'sol {it} is outside sols ({it1}, {it2}): crit {cr.name}: r {r:.2f} v {v:.2f}, '
                    #       f'(v1, v2) = ({v1:.2f}, {v2:.2f}).')
                    return False  # v outside the range [v1, v2] --> s in outside cube(s1, s2)
            # print(f'sol {it} {s.vals} is inside sols {it1} {s1.vals} and {it2} {s1.vals}; r {r:.2f}')
            return True     # s is inside the cube(s1, s2)
        #   end of using the ZN definition of neighbors

        # use the standard definition of empty cubes, i.e., no other solution in the cube defined by s1 and s2
        for (i, cr) in enumerate(self.mc.cr):
            v = s.vals[i]
            v1 = s1.vals[i]
            v2 = s2.vals[i]
            if not min(v1, v2) <= v <= max(v1, v2):
                # print(f'sol {it} is outside sols ({it1}, {it2}): crit {cr.name}: {v} is outside ({v1}, {v2}).')
                return False  # v outside the range [v1, v2] --> s in outside cube(s1, s2)
            # else:
            #     print(f'crit {cr.name}: {v} is in the range of ({v1}, {v2}); continue check.')
        # print(f'solution {it} is between solutions ({it1}, {it2}).')
        return True  # s is inside the cube(s1, s2): all its crit-vals are between the corresponding values of s1 and s2

    # todo: improve comments below
    # add solution (uses crit-values updated in mc.cr). called from CtrMca::updCrit()
    def sizeLog(self, cube, final=False):
        itr = self.cur_itr
        if not final:
            self.log_min = min(self.log_min, cube.size)
            self.log_max = max(self.log_max, cube.size)
            self.log_mxCubes = max(self.log_mxCubes, len(self.cubes.cand))
        if itr < self.log_next and not final:
            return      # don't log before log_next
        self.solDistr()     # distribution of distances between neighbor dsolutions
        now = datetime.datetime.now()
        # tm_stamp = now.strftime("%Y-%m-%d %H:%M:%S")
        tm_stamp = now.strftime("%H:%M:%S")
        self.log_dict.update({itr: [self.log_min, self.log_max, self.log_mxCubes, tm_stamp]})
        self.log_next += self.log_block
        self.log_min = 100
        self.log_max = 0
        self.log_mxCubes = 0

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
            c = self.cubes.get(self.cur_cube)     # get parent cube (for its id)
            # todo: add conditional call (only for info-print)
            new_sol.neigh_inf(c)   # info on location within the solutions of the parent cube
            self.sizeLog(c)     # add cube size to the sizeLog

        is_close = False
        s_close = None
        tolClose = self.cfg.get('tolClose', 0.01)
        for s2 in self.sols:   # check if the new sol is close to any previous unique (i.e., not-close) sol
            if new_sol.is_close(s2, tolClose):
                is_close = True
                s_close = s2
                break
        is_pareto = True
        if is_close:
            is_pareto = False
            self.clSols.append(new_sol)
            print(f'Solution[{itr_id}] close to sol[{new_sol.closeTo}] (L-inf = {new_sol.distMx:.1e}). '
                  f'There are {len(self.clSols)} mutually close Pareto solutions.')
            if self.cur_cube is not None:  # cur_cube undefined during computation of selfish solutions
                c = self.cubes.get(self.cur_cube)  # get parent cube (for its id)
                new_sol.neigh_inf(c, True)   # info on location within the solutions of the parent cube
                oldInCube = self.is_inside(s_close, c.s1, c.s2)
                if oldInCube:
                    print('WARNING: old (close to new) solution is in the current cube -------------------------------')
                else:
                    # todo: print info on close (old and new) solutions (belonging to different cubes)
                    pass
                if self.mc.opt('mCube', False):
                    self.mk_aCube(None)  # make a cube from previously available solutions
        else:   # unique solution; check dominance with all Pareto-sols found so far
            toPrune = []    # tmp list of solutions dominated by the current sol
            for s2 in self.sols:   # check if the new sol is close to any previous unique (i.e., not-close) sol
                cmp_ret = new_sol.cmp(s2)
                if cmp_ret == 0:    # is Pareto?
                    continue    # check next solution
                elif cmp_ret > 0:   # new_sol dominates s2
                    if self.cfg.get('verb') > -1:
                        print(f'\t-------------     current solution[{itr_id}] dominates solution[{s2.itr_id}].')
                    s2.domin = -itr_id      # mark s2 as dominated by the new solution and continue checking next sol.
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
                if self.mc.opt('mCube', False):
                    self.mk_aCube(new_sol)    # define cubes candidates, if needed
                else:
                    self.mk_cubes(new_sol)    # define cubes generated by this solution
            for s2 in toPrune:   # remove dominated solutions from self.sols
                print(f'\tsolution[{s2.itr_id}] dominated by solution[{itr_id}] removed from self.sols.')
                self.sols.remove(s2)
        return is_pareto

    def mk_aCube(self, xx):  # find a pair of most distant neighbor solutions and define a cube.cand around them
        n_sols = len(self.sols)
        if n_sols < 2:
            return
        if len(self.cubes.cand):
            print(f'ParRep::mk_aCube(): there are {len(self.cubes.cand)} cubes in the candidate list.')
            return  # do nothing if there are waiting cubes
        mxDist = 0.
        iMax = None
        nAdjoint = 0
        mxPair = [None, None]   # id's of adjoint solutions that are most distant
        for ind1 in range(n_sols - 1):  # the last solution has no next to compare with
            s1 = self.sols[ind1]
            id1 = s1.itr_id
            a1 = s1.a_vals
            for ind2 in range(ind1 + 1, n_sols):    # find the closest neighbor
                s2 = self.sols[ind2]
                id2 = s2.itr_id
                a2 = s2.a_vals
                are_adj = True  # are s1 and s2 adjoint (no other s between them)?
                for s in self.sols:
                    if s.itr_id == id1 or s.itr_id == id2:
                        continue
                    a = s.a_vals
                    is_inside = True
                    for i in range(self.mc.n_crit):
                        if not min(a1[i], a2[i]) <= a[i] <= max(a1[i], a2[i]):
                            is_inside = False     # s is outside the cube[id1, id2]
                            break
                    if is_inside:
                        # print(f'Sol[{s.itr_id}] is between sols[{id1},{id2}].')
                        are_adj = False
                        break  # don't check other solutions, if there is one between
                pass
                if are_adj:     # no sol between s1 and s2
                    # check, if s1 and s2 are most distant
                    dist = 0.   # distance between s1 and s2
                    nAdjoint += 1
                    for i in range(self.mc.n_crit):
                        diff = abs(a1[i] - a2[i])
                        if dist < diff:
                            dist = diff
                            if mxDist < dist:
                                mxDist = dist
                                iMax = i
                                mxPair = [id1, id2]
                                pass
                # end of check, if the current adjoint pair is most distan
                pass
            # end of check of the s2
        # all pairs checked
        print(f'Most distant adjoint solutions (out of {nAdjoint}): sol-ids {mxPair}, dist {mxDist:.2f} crit_id {iMax}')
        s1 = self.get(mxPair[0])
        s2 = self.get(mxPair[1])
        n_cube = aCube(self.mc, s1, s2)
        # print(f'ParRep::mk_aCube(): there are {len(self.cubes.cand)} cubes in the candidate list.')
        # print(f'adding cube defined by sols [{s1.itr_id}, {s2.itr_id}], size {n_cube.size:.2f}')
        # Note: n_cube size might be larger than the mx_diff
        self.cubes.add(n_cube)  # adds to the list only large-enough cubes (assumes empty for 'mCube' option)
        n_cand = len(self.cubes.cand)
        # print(f'ParRep::mk_aCube(): there are {n_cand} cubes in the candidate list.')
        if not n_cand == 1:
            print(f'WARNING: there are {n_cand} cubes in the candidate list.')
            # raise Exception(f'ParRep::mk_aCube() - there are {n_cand} candidate cubes.')
        pass
        pass


    def mk_aCube0(self, s):  # find a pair of most distant neighbor solutions and define a cube.cand around them
        if s is None:
            print('\nWARNING: incomplete representation (handling of close solutions) not implemented yet.)-----------')
            return
        else:
            # add solution to the sol-work list
            item = [s.itr_id]
            for val in s.a_vals:
                item.append(val)
            self.sols_wrk.append(item)
        if len(self.sols_wrk) < 2:  # a single (first) solution is not enough to define a cube
            return
        if len(self.cubes.cand):
            print(f'ParRep::mk_aCube(): there are {len(self.cubes.cand)} cubes in the candidate list.')
            return  # do nothing if there are waiting cubes

        # find the most distant pair of sorted solutions: check neighbors for each criterion separately
        mx_dist = 0.
        mx_crit = None  # index of the criterion having max gap (diff between consecutive sorted values)
        pair_id = []    # sol.itr_id of the pair of the most distant solutions
        n_sols = len(self.sols_wrk)
        for i in range(self.mc.n_crit):
            # sort the list by i-crit value by descresing order
            self.sols_wrk = sorted(self.sols_wrk, key=itemgetter(i + 1), reverse=True)
            pass
            for seq_no in range(n_sols - 1): # the last sol skipped as it has no next to compare with
                diff = self.sols_wrk[seq_no][i + 1] - self.sols_wrk[seq_no + 1][i + 1]
                if mx_dist < diff:
                    mx_dist = diff
                    pair_id = [self.sols_wrk[seq_no][0], self.sols_wrk[seq_no + 1][0]]
                    mx_crit = i
                    pass

        print(f'Largest diff of sorted crit.: sol-ids {pair_id}, diff {mx_dist:.2f} crit_id {mx_crit}')
        s1 = self.get(pair_id[0])
        s2 = self.get(pair_id[1])
        n_cube = aCube(self.mc, s1, s2)
        # print(f'ParRep::mk_aCube(): there are {len(self.cubes.cand)} cubes in the candidate list.')
        print(f'adding cube defined by sols [{s1.itr_id}, {s2.itr_id}], size {n_cube.size:.2f}')
        # Note: n_cube size might be larger than the mx_diff
        self.cubes.add(n_cube)  # adds to the list only large-enough cubes (assumes empty for 'mCube' option)
        n_cand = len(self.cubes.cand)
        # print(f'ParRep::mk_aCube(): there are {n_cand} cubes in the candidate list.')
        if not n_cand == 1:
            print(f'WARNING: there are {n_cand} cubes in the candidate list.')
            # raise Exception(f'ParRep::mk_aCube() - there are {n_cand} candidate cubes.')
        pass

    def mk_cubes(self, s):  # generate cubes defined by the new solution with each previous distinct-solution
        verb = self.cfg.get('verb') > 2
        for s1 in self.sols:
            if s1.domin < 0:
                continue    # skip dominated solutions
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
        self.cubes.lst_cubes()  # list cubes
        cand = sorted(self.cubes.cand, key=itemgetter(1), reverse=True)  # sort by size (just getting the largest)
        if len(cand) > 0:
            mx_size = cand[0][1]
        else:
            mx_size = 0
        print('\n')
        self.progr.updCubeInf(mx_size, True)   # store info on the unprocessed cubes if any remain
        self.progr.summary()   # process info on the computation progress

        self.solDistr()     # generate final sample of distribution of distances between neighbor solutions

        print('\nEnvelops of cube-sizes in iters blocks:')
        self.sizeLog(None, True)
        for itr, sizes in self.log_dict.items():
                print(f'Iter {itr}: min_size {sizes[0]:.2f}, max_size {sizes[1]:.2f}, mxCubes {sizes[2]}, {sizes[3]}')
            # todo: allign itr length (precision does not work)
            # print(f'\nIter {itr:.6d}: {sizes[0]:.2f},{sizes[1]:.2f}')  #int precision not allowed?

        print('\nDistances between neighbor Pareto solutions:')
        for itr, inf in self.neighInf.items():
            print(f'Iter {itr}: maxDist {inf[0]:.2f} ({inf[1]}, {inf[2]}), minDist {inf[3]:.2f}')

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

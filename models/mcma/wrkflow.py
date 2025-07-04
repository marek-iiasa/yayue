""" Control the application work-flow """
# import sys # needed from stdout
# import os
# import math
# from os import R_OK, access
# from os.path import isfile
from .ctr_mca import CtrMca
from .payoff import PayOff
from .report import Report  # organize the results of each iteration into reports
from .corners import Corners
# from .crit import Crit, CrPref
from .par_repr import ParRep
from .neigh import Neigh
from .grid import Grid


# noinspection SpellCheckingInspection
class WrkFlow:   # payoff table: try to download, set A/R for computing, update Nadir and save, decide to reset
    def __init__(self, cfg, m1):   # par_rep False/True controls no/yes Pareto representation mode
        self.cfg = cfg
        self.mc = CtrMca(self)   # initialize criteria
        self.verb = self.mc.verb
        self.payoff = PayOff(self.mc)   # initialiaze PayOff table
        # self.rep = None  # Report ctor
        self.rep = Report(self, m1)  # Report ctor
        self.par_rep = None    # ParRep object, currently always used (not only, if is_par_rep == True)
        self.corner = None  # object handling corners of the PF
        self.cluster = None  # (optional) cluster-object of solutions
        self.grid = None
        #
        self.stages = {'payoff': 1, 'corners': 2, 'neutral': 3, 'parfront': 4, 'reset': 5, 'end': 6} # noqa
        if self.payoff.done():
            # self.rep = Report(self, m1)  # Report ctor
            self.mc.scale()  # (re)define scales for criteria values
            self.par_rep = ParRep(self)  # ParRep object, currently always used (not only, if is_par_rep == True)
            self.corner = Corners(self.mc)  # initialize corners of the Pareto set
            self.cur_stage = 2      # PayOff table uploaded, start with corners of the PF
        else:
            self.cur_stage = 1      # start with computing PayOff table
        self.n_itr = None           # id of current itr (TBD by self.itr_start())
        self.is_opt = None  # indicates True/False avail. of optimal solution (set in driver())
        # self.is_par_rep = cfg.get('parRep')    # if True, then switch to ParetoRepresentation mode
        self.is_par_rep = True    # only ParetoRepresentation mode is avail. (handling usr-specs of A/R not tested)
        self.deg_exp = False    # expansion of degenerated cube dimensions
        self.usrAR = self.mc.opt('usrAR', None)     # optionally defined file with usr-defined AR
        if self.usrAR is not None:
            self.is_par_rep = False
            self.mc.readPref(self.usrAR)    # read usr-defined AR

    def itr_start(self, n_itr):
        self.n_itr = n_itr
        if self.cur_stage == 1:       # start or continue payoff table
            self.payoff.next_pref()
        elif self.cur_stage == 2:     # start or continue computing corners
            self.corner.next_corner()
            # raise Exception(f'WrkFlow::itr_start() not implemented yet for stage: {self.cur_stage}.')
        elif self.cur_stage == 3:     # neutral solution
            self.par_rep.pref(True)     # True implies AR for neutral solution
            # raise Exception(f'WrkFlow::itr_start() not implemented yet for stage: {self.cur_stage}.')
        elif self.cur_stage == 4:     # continue Pareto front
            self.par_rep.pref()     # the default arg False implies AR from: either a selected cube or usr-defined
            # raise Exception(f'WrkFlow::itr_start() not implemented yet for stage: {self.cur_stage}.')
        elif self.cur_stage == 5:  # reset (after Nadir update), restart with Corners
            raise Exception(f'WrkFlow::itr_start() not implemented yet for stage: {self.cur_stage}.')
        # elif self.cur_stage == 6:     # everything done, finish
        #     raise Exception(f'WrkFlow::itr_start() not implemented yet for stage: {self.cur_stage}.')
        else:           # shouldn't come here
            raise Exception(f'WrkFlow::itr_start() implementation error, stage: {self.cur_stage}.')
        return self.cur_stage

    def in_range(self):     # return True, if the value is within the [U, N] range
        ret_val = True
        for cr in self.mc.cr:
            val = cr.val
            if cr.utopia is not None:
                if cr.better(val, cr.utopia):   # strictly (by a margin) better
                    print(f'\tWARNING: crit {cr.name}: solution val {val:.6e} is better than Utopia {cr.utopia:.6e}')
                    ret_val = False
            if cr.nadir is not None:
                if cr.better(cr.nadir, val):   # strictly (by a margin) better
                    # print(f'\tWARNING: crit {cr.name}: the solution val {val:.6e} is worse than Nadir {cr.nadir:.6e}')
                    ret_val = False
        return ret_val

    def itr_sol(self, mc_part):     # process solution, decide stage for next itr
        # extract and store in crit sol.-values, if in U/N range: add info to report
        in_range = self.rep.itr(mc_part)
        if not in_range and self.cur_stage > 1:  # checks/updates run after the PayOff table complete
            changed = self.payoff.update(self.cur_stage)  # update payOff table if a nadir changed
            # double-check if the solution is within U/N after Nadir updated
            out_range = not self.in_range()
            if changed or out_range:
                if out_range:   # should not happen
                    raise Exception(f'Solution outsude U/N range.')
                if changed:
                    self.cur_stage = 5      # reset
                    self.par_rep.neighSol = None    # destroy the neighbors' object
                    self.par_rep.grid = None    # destroy the neighbors' object

        next_stage = self.cur_stage   # by default, continue with the current stage
        if self.cur_stage == 1:       # payoff table
            self.payoff.next_sol()
        elif self.cur_stage == 2:     # corners
            is_pareto = self.par_rep.addSol(self.n_itr)     # store here to get info, it is_Pareto
            all_done = self.corner.next_sol(is_pareto, self.n_itr)  # store info on corners (only by unique Pareto)
            if all_done:
                if self.cfg.get('neutral') is True:
                    next_stage = 3
                else:
                    next_stage = 4     # skip neutral, proceed to Pareto front
                self.par_rep.from_cube = True   # preferences for (optional) neutral and the PF to be generated from cubes
                self.cur_stage = next_stage
        elif self.cur_stage == 3:     # neutral solution
            next_stage = 4  # the neutral done, proceed to Pareto front
            self.cur_stage = next_stage
            # self.par_rep.from_cube = True  # from now on preferences to be generated from cubes
        if self.cur_stage < 4:
            pass    # nothing more to do here
        elif self.cur_stage == 4:     # start or continue Pareto front
            if self.mc.opt('mCube', False):
                if self.par_rep.neighSol is None:
                    self.par_rep.neighSol = Neigh(self.par_rep) # initialize with corners and neutral sol.
                # else:
                #     raise Exception(f'WrkFlow::itr_sol() - duplicated Neigh-object initialization.')
                pass
            elif self.mc.opt('grid', False):
                if self.par_rep.grid is None:
                    self.par_rep.grid = Grid(self) # initialize with corners and neutral sol.
                # else:
                #     raise Exception(f'WrkFlow::itr_sol() - duplicated Grid-object initialization.')
                pass
            # raise Exception(f'WrkFlow::itr_sol() not implemented yet for stage: {self.cur_stage}.')
        elif self.cur_stage == 5:     # reset (after Nadir update)
            print('\nINFO: PayOff table updated; restarting the Pareto-set representation. ---------------------------')
            self.mc.scale()  # (re)define scales for criteria values
            self.corner = Corners(self.mc)  # initialize corners of the Pareto set
            self.par_rep = ParRep(self)  # ParRep object, currently always used (not only, if is_par_rep == True)
            next_stage = 2
            # raise Exception(f'WrkFlow::itr_sol() not implemented yet for stage: {self.cur_stage}.')
        elif self.cur_stage == 6:  # finish; no more cubes to be processed
            return next_stage
        else:           # shouldn't come here
            raise Exception(f'WrkFlow::itr_sol() implementation error, stage: {self.cur_stage}.')

        # todo: suppress storing the previous solution at start of the PF calculation
        if self.cur_stage > 2:  # store solutions only if the PayOff table is available
            self.par_rep.addSol(self.n_itr)

        if self.corner is None and self.payoff.done():  # initialize Corners and ParRep
            # self.rep = Report(self, m1)  # Report ctor
            self.mc.scale()  # (re)define scales for criteria values
            self.par_rep = ParRep(self)  # ParRep object, currently always used (not only, if is_par_rep == True)
            self.corner = Corners(self.mc)  # initialize corners of the Pareto set
            next_stage = 2  # PayOff table uploaded, start with corners of the PF
            self.payoff.prnPayOff()     # print to stdout and save to the file
        if self.cur_stage > 3 and self.par_rep.neighSol is not None:
            if self.par_rep.neighSol.getPair() == (None, None):
                print('\nNo more condidates for making cubes. -------------------------------------------')
                next_stage = 6
        if self.cur_stage > 3 and self.par_rep.grid is not None:  # cur_stage kept at 2 for grid option
            # pair =  self.par_rep.grid.getPair()
            if self.par_rep.grid.getPair() == (None, None):
                print('\nNo more condidates for making cubes. -------------------------------------------')
                next_stage = 6
        self.cur_stage = next_stage
        return next_stage

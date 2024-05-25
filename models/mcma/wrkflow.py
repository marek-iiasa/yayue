""" Control the application work-flow """
# import sys      # needed from stdout
# import os
# import math
# from os import R_OK, access
# from os.path import isfile
from .ctr_mca import CtrMca
from .payoff import PayOff
from .report import Report  # organize results of each iteration into reports
from .corners import Corners
# from .crit import Crit, CrPref
from .par_repr import ParRep


# noinspection SpellCheckingInspection
class WrkFlow:   # payoff table: try to download, set A/R for computing, update Nadir and save, decide to reset
    def __init__(self, cfg, m1):   # par_rep False/True controls no/yes Pareto representation mode
        self.cfg = cfg
        self.mc = CtrMca(self)   # initialize criteria
        self.payoff = PayOff(self.mc)   # initialiaze PayOff table
        # self.rep = None  # Report ctor
        self.rep = Report(self, m1)  # Report ctor
        self.par_rep = None    # ParRep object, currently always used (not only, if is_par_rep == True)
        self.corner = None  # initialize corners of the Pareto set
        #
        self.stages = {'payoff': 1, 'corners': 2, 'neutral': 3, 'parfront': 4, 'reset': 5, 'end': 6} # noqa
        if self.payoff.done():
            # self.rep = Report(self, m1)  # Report ctor
            self.par_rep = ParRep(self)  # ParRep object, currently always used (not only, if is_par_rep == True)
            self.corner = Corners(self.mc)  # initialize corners of the Pareto set
            self.cur_stage = 2      # PayOff table uploaded, start with corners of Pareto set
        else:
            self.cur_stage = 1      # start with computing PayOff table
        self.n_itr = None           # id of current itr (TBD by self.itr_start())
        self.is_opt = None  # indicates True/False avail. of optimal solution (set in driver())
        self.is_par_rep = cfg.get('parRep')    # if True, then switch to ParetoRepresentation mode
        self.deg_exp = False    # expansion of degenerated cube dimensions
        #
        # self.stages = {'ini': 0, 'utop': 1, 'nad1': 2, 'nad2': 3, 'RFPauto': 4, 'RFPuser': 5, 'end': 6} # noqa
        # self.f_payoff = 'payoff.txt'     # file with payoff values
        # self.f_pref = 'pref.txt'     # file with defined preferences' set
        # self.ana_dir = cfg.get('ana_dir')  # wrk dir for the current analysis (not needed; runs in this dir)
        # self.f_crit = 'config.txt'   # file with criteria specification
        # self.cur_itr_id = None  # id of the current iteration
        # self.cr = []        # objects of Crit class, each representing the corresponding criterion
        # self.n_crit = 0     # number of defined criteria == len(self.cr)
        # self.cur_cr = None  # cr_index passed to self.set_pref()
        # self.pay_upd = False  # set to true, if current payOff differs from the store one
        # tolerances
        # self.cafAsp = 100.   # value of CAF at A (if A undefined, then at U)
        # self.critScale = 1000.   # range [utopia, nadir] of scaled values (no longer needed?)
        # self.epsilon = 1.e-6  # fraction of self.cafAsp used for scaling the AF regularizing term
        #
        # self.minDiff = 0.001  # min. relative differences between (U, N), (U, A), (A, R), (R, N) (was 0.01)
        # self.slopeR = 10.    # slope ratio between mid-segment and segments above A and below R
        # diverse
        # self.scVar = self.opt('scVar', True)   # scale core-model vars defining CAFs
        # self.scVar = self.opt('scVar', False)   # scale core-model vars defining CAFs
        # self.verb = self.opt('verb', 1)   # print verbosity: 0 - min., 1 - key, 2 - debug, 3 - detailed
        # self.pref = []    # list of preferences defined for each blocks
        # self.n_pref = 0     # number of blocks of read-in preferences
        # self.cur_pref = 0   # index of currently processed preference
        # self.payOffChange = True    # set to False, after every storing, to True after any nadir modified
        #
        # self.rdCritSpc()    # read criteria specs from the config file
        # self.rd_payoff()    # Load payOff table if previously stored (initialized to undefined by Crit ctor)

    def itr_start(self, n_itr):
        self.n_itr = n_itr
        if self.cur_stage == 1:       # start or continue payoff table
            self.payoff.next_pref()
            # if self.payoff.done():
            #     # self.rep = Report(self, m1)  # Report ctor
            #     self.par_rep = ParRep(self)  # ParRep object, currently always used (not only, if is_par_rep == True)
            #     self.corner = Corners(self.mc)  # initialize corners of the Pareto set
            #     self.cur_stage = 2  # PayOff table uploaded, start with corners of Pareto set
            # return self.cur_stage
        elif self.cur_stage == 2:     # start or continue computing corners
            self.corner.next_corner()
            # raise Exception(f'WrkFlow::itr_start() not implemented yet for stage: {self.cur_stage}.')
        elif self.cur_stage == 3:     # neutral solution
            self.par_rep.pref(True)     # True implies AR for neutral solution
            # raise Exception(f'WrkFlow::itr_start() not implemented yet for stage: {self.cur_stage}.')
        elif self.cur_stage == 4:     # continue Pareto front
            self.par_rep.pref()     # the default arg False implies AR from the selected cube
            # raise Exception(f'WrkFlow::itr_start() not implemented yet for stage: {self.cur_stage}.')
        elif self.cur_stage == 5:  # reset (after Nadir update), restart with Corners
            raise Exception(f'WrkFlow::itr_start() not implemented yet for stage: {self.cur_stage}.')
        # elif self.cur_stage == 6:     # everything done, finish
        #     raise Exception(f'WrkFlow::itr_start() not implemented yet for stage: {self.cur_stage}.')
        else:           # shouldn't come here
            raise Exception(f'WrkFlow::itr_start() implementation error, stage: {self.cur_stage}.')
        return self.cur_stage

    def itr_sol(self, mc_part):     # process solution, decide stage for next itr
        self.rep.itr(mc_part)
        # todo: check Nadir update

        next_stage = self.cur_stage   # by default, continue with the current stage
        if self.cur_stage == 1:       # payoff table
            next_stage = self.payoff.next_sol()
        elif self.cur_stage == 2:     # corners
            all_done = self.corner.next_sol()
            if all_done:
                if self.cfg.get('neutral') is True:
                    next_stage = 3
                else:
                    next_stage = 4     # skip neutral, proceed to Pareto front
                    self.par_rep.from_cube = True   # from now on preferences to be generated from cubes
        elif self.cur_stage == 3:     # neutral solution
            next_stage = 4  # neutral done, proceed to Pareto front
            self.par_rep.from_cube = True  # from now on preferences to be generated from cubes
            # raise Exception(f'WrkFlow::itr_sol() not implemented yet for stage: {self.cur_stage}.')
        elif self.cur_stage == 4:     # start or continue Pareto front
            pass
            # raise Exception(f'WrkFlow::itr_sol() not implemented yet for stage: {self.cur_stage}.')
        elif self.cur_stage == 5:     # reset (after Nadir update)
            raise Exception(f'WrkFlow::itr_sol() not implemented yet for stage: {self.cur_stage}.')
        else:           # shouldn't come here
            raise Exception(f'WrkFlow::itr_sol() implementation error, stage: {self.cur_stage}.')
        if self.cur_stage > 1:  # don't store solutions during PayOff table computations
            # todo: check handling non-optimal solutions (should be earlier?)
            self.par_rep.addSol(self.n_itr)
        self.cur_stage = next_stage
        return next_stage
    '''
    def set_payOff(self, cr_name, utopia, nadir):   # set the previously stored utopia/nadir values
        if utopia is None or nadir is None:
            raise Exception(f'set_payoff("{cr_name}", {utopia=}, {nadir=}): undefined values.')
        utopia = float(utopia)  # read-in words are of type string; have to explicitly converted
        nadir = float(nadir)
        if type(utopia) is not float or type(nadir) is not float:
            print(f'{type(utopia) = }')
            print(f'{type(nadir) = }')
            raise Exception(f'set_payOff("{cr_name}", "{utopia}", "{nadir}"): both values should be of type float.')
        for crit in self.cr:
            if crit.name == cr_name:
                if crit.isBetter(utopia, nadir):
                    crit.utopia = utopia
                    crit.nadir = nadir
                    return
                else:
                    raise Exception(f'set_payoff("{cr_name}", {utopia=}, {nadir=}): inconsistent values.')
        raise Exception(f'set_payoff(): unknown criterion name: "{cr_name}".')

    def rd_payoff(self):    # read stored utopia/nadir values and store them as self.cr attributes
        if os.path.exists(self.f_payoff):
            with open(self.f_payoff, "r") as reader:
                print(f"\nReading payoff table stored in file '{self.f_payoff}':")
                n_def = 0
                for n_line, line in enumerate(reader):
                    line = line.rstrip("\n")
                    # print(f'line {line}') # noqa
                    words = line.split()
                    n_words = len(words)
                    assert n_words == 5, f'line {line} has {n_words} instead of the required five.'
                    self.set_payOff(words[0], words[2], words[4])
                    n_def += 1
            assert (self.n_crit == n_def), f'stored payOff table has {n_def} values for {self.n_crit} defined criteria.'
            self.prnPayOff(True)    # print only (don't write to the file)
            # self.hotStart = True  # if payOff provided, jump to stage==5
            self.cur_stage = 4
            print(f'\nPayOff table provided; skipping its computation. Compute neutral solution.')
        else:
            print(f"\nFile '{self.f_payoff}' with the payoff table not available.")
            # self.hotStart = False  # payOff not provided, shall be computed

    def prnPayOff(self, prn_only=False):   # store current values of utopia/nadir in a file for subsequent use
        # to create a dir: os.makedirs(dir_name, mode=0o755)
        # create file for writing (over-writes previous, if exists)
        if not self.payOffChange:
            # print('payOff table values not changed.')
            return
        print('PayOff table:')
        lines = []
        for crit in self.cr:
            if crit.utopia is not None and crit.nadir is not None:
                line = f'{crit.name}\t U {crit.utopia:.3e}   N {crit.nadir:.3e}'
            else:
                line = f'{crit.name}\t U {crit.utopia}   N {crit.nadir}'
            print(line)
            lines.append(line)
        if prn_only or self.cur_stage < 4:  # don't store payOff table before neutral solution is computed:
            if self.cfg.get('verb') > 1:
                print(f'Current values of the payoff table NOT written to file "{self.f_payoff}":')
        else:
            print(f'Current values of the payoff table written to file "{self.f_payoff}":')
            f_payOff = open(self.f_payoff, "w")
            for line in lines:
                f_payOff.write(line + '\n')
            f_payOff.close()
            self.payOffChange = False

    def chk_utopia(self):    # return crit-index of criterion, whose utopia was not computed yet
        for (i, cr) in enumerate(self.cr):
            if cr.utopia is None:  # old version: if not cr.utopia is wrong (returns True if cr.utopia == 0.)
                return i
        return -1
    '''

    '''
    def set_stage(self):
        """Define and return analysis stage; provide (in self.cur_cr) info for mc.set_pref()."""

        # preferences predefined in stages 1, 2, 3 and 4 (A and R used only in stage 4)
        # stage 5: user-defined preferences by A, R; optionally activity to excl. criterion from the Tchebyshev term
        if self.cur_stage == 0:     # initialization
            print('Initialization finished, checking, if all utopia components computed.')
            self.cur_stage = 1
        if self.cur_stage == 1:     # computing utopia
            i_cr = self.chk_utopia()   # check, if all utopias computed
            if i_cr > -1:   # utopia of i_cr-th criterion needs to be computed
                self.cur_cr = i_cr
                print(f'Utopia of criterion "{self.cr[i_cr].name}" shall be computed.')
            else:   # all utopia computed, start 1st stage of nadir approximation
                print('All utopia components computed. Start first stage of nadir approximation.')
                self.cur_stage = 2
                self.cur_cr = 0     # start with 0-th criterion
            return self.cur_stage   # crit activity set in mc_set_pref()
        elif self.cur_stage == 2:  # 1st approximation of Nadir
            if self.cur_cr + 1 < self.n_crit:   # not all crit used?
                self.cur_cr += 1    # use next (not yet used) criterion
                print(f'Appr. Nadir of crit. other than {self.cr[self.cur_cr].name} (stage {self.cur_stage}).')
            else:   # move to the 2nd stage of nadir appr.
                print('Finished first nadir approximations. Start the 2nd nadir approximation.')
                self.cur_stage = 3
                self.cur_cr = 0     # start 2nd nedir appr with 0-th criterion
                print(f'Appr. Nadir of crit. other than {self.cr[self.cur_cr].name} (stage {self.cur_stage}).')
            return self.cur_stage
        elif self.cur_stage == 3:  # second approximation of Nadir
            if self.cur_cr + 1 < self.n_crit:   # not all crit used?
                self.cur_cr += 1    # use next (not yet used) criterion
                print(f'Appr. Nadir of crit. other than {self.cr[self.cur_cr].name} (stage {self.cur_stage}).')
            else:   # finished the 2nd stage of nadir appr.
                print('Finished 2nd nadir approximation.')
                print('Approximation of PayOff table ready. Compute for neutral solution.')
                self.cur_stage = 4
                self.cur_cr = None     # should no longer be used
                self.neutralDone = True     # declare as done (to prevent repetition at cur_stage==4 below
            return self.cur_stage
        elif self.cur_stage == 4:  # comes here to compute initial Pareto solutions, incl. optionally neutral sol.
            self.cur_cr = None  # should no longer be used
            if not self.iniSolDone:     # set preferences for the initial set of Pareto solutions
                pass        # nothing to do here, ini-solutions controlled in ParRep::pref()
            elif not self.neutralDone:
                pass
            else:  # neutral sol. already computed, switch to handle preferences for Pareto sols
                # print('Finished computation of neutral Pareto solution.')
                print('Switch to generating/using preferences.')
                self.cur_stage = 5
            return self.cur_stage  # return to set pref for neutral solution and compute it
        elif self.cur_stage == 5:  # comes here while processing preferences
            # after debugging, nothing to do here
            # print('Continue to get and handle user preferences.')
            return self.cur_stage
        else:
            raise Exception(f'set_stage(): stage {self.cur_stage} NOT implemented yet.')

        # return self.cur_stage

    def set_pref(self):
        # set automatically (according to programmed rules for each stage) crit attributes:
        # (activity, A/R, possibly adjust nadir app).
        assert self.cur_stage > 0, f'CtrMca::set_pref() should not be called for cur_stage {self.cur_stage}.'
        if self.cur_stage == 1:  # set only currently computed utopia criterion to be active
            for (i, crit) in enumerate(self.cr):
                crit.is_fixed = False
                if self.cur_cr == i:
                    crit.is_active = True
                else:
                    crit.is_active = False
            return
        elif self.cur_stage == 2:     # set one crit active in first appr. of Nadir
            if self.verb > 2:
                print(f'---\nMcma::set_pref(): stage {self.cur_stage}.')
            for (i, crit) in enumerate(self.cr):
                crit.is_fixed = False
                if self.cur_cr == i:
                    crit.is_active = True
                else:
                    crit.is_active = False
            return
        elif self.cur_stage == 3:     # set one crit active in first appr. of Nadir
            if self.verb > 2:
                print(f'---\nMcma::set_pref(): stage: {self.cur_stage}.')
            for (i, crit) in enumerate(self.cr):
                crit.is_fixed = False
                if self.cur_cr == i:
                    crit.is_active = True
                else:
                    crit.is_active = False
            return
        elif self.cur_stage == 4:   # initial solutions (Pareto-corners) and (optional) neutral sol
            if self.is_par_rep and not self.iniSolDone:
                self.par_pref()    # generate preferences for finding next initial solution
            elif not self.neutralDone:     # set A and R for neutral solution
                print(f'---\nMcma::set_pref(): for neutral solution, stage: {self.cur_stage}.')
                for crit in self.cr:    # set AR for neutral solution
                    crit.setAR()
                self.neutralDone = True
            return
        elif self.cur_stage == 5:     # generate pref (for Pareto repr.) or get user-defined preferences
            if self.is_par_rep:
                self.par_pref()    # generate preferences for finding next Pareto-set repr.
            else:
                self.usrPref()    # get user-defined preferences
            return

        sys.stdout.flush()  # needed for printing exception at the output end
        raise Exception(f'Mcma::set_pref() not implemented yet for stage: {self.cur_stage}.')

    def par_pref(self):  # generate preferences for finding next solution in Pareto set representation
        assert self.is_par_rep, f'CtrMca::par_pref() should not be used for usr-def pref.'
        assert self.par_rep is not None, f'CtrMca::par_pref() should be initialized earlier.'
        assert self.cur_stage in [4, 5], f'CtrMca::par_pref() should not be called for cur_stage {self.cur_stage}.'
        self.par_rep.pref()     # define largest cube, set A/R&activity in mc.cr[] in the model (not ASF) scale

    def usrPref(self):  # get user-preferences (if no more pref avail. then set self.cur_stage = 6 for a clean exit)
        # make sure that all criteria are active by default
        for crit in self.cr:
            crit.is_active = True
        if self.n_pref == 0:    # no preferences defined, read them
            self.readPref()
        # print(f'{self.n_pref = }, {self.n_pref == 0}, {self.cur_pref = }, {self.cur_pref >= self.n_pref}')
        print(f'Out of {self.n_pref} user-specified preferences {self.cur_pref} processed.')
        if self.n_pref == 0 or self.cur_pref >= self.n_pref:    # no more user-pref. to handle
            self.cur_stage = 6  # finish analysis
        else:   # use next unprocessed user preference set
            # print(f'Applying {self.cur_pref}-th set of user preferences.')
            items = self.pref[self.cur_pref]
            self.cur_pref += 1
            for item in items:
                c_ind = item.parent
                crit = self.cr[c_ind]
                crit.asp = item.asp
                crit.res = item.res
                crit.is_active = item.is_active
                print(f'Attributes of crit "{crit.name}": A {crit.asp}, R {crit.res}, active {crit.is_active}.')
        return

    def updCrit(self, crit_val):  # update crit attributes (nadir, utopia), called from Report::itr()
        assert self.cur_stage > 0, f'store_sol should not be called for stage {self.cur_stage}.'
        # print(f'Processing criteria values of the current iteration: {crit_val}')
        if self.cur_stage == 1:     # utopia computed for the only one active criterion
            for crit in self.cr:
                val = crit_val.get(crit.name)
                crit.val = val
                if crit.is_active:
                    crit.setUtopia(val)  # utopia computed
                crit.updNadir(self.cur_stage, val, self.minDiff)
        elif 1 < self.cur_stage < 6:  # update nadir values
            if self.verb > 2:
                print(f'---\nMcma::store_sol(): stage {self.cur_stage}.')
            for crit in self.cr:
                val = crit_val.get(crit.name)
                crit.val = val
                crit.a_val = crit.val2ach(crit.val)
                if self.verb > 2:
                    print(f'\tCrit {crit.name}: val {crit.val:.2f}, a_val {crit.a_val:.2f}')
                if crit.is_active and self.cur_stage < 4:  # don't update nadir
                    if self.verb > 2:
                        print(f'NOT updating nadir for active crit "{crit.name}" = {val} at stage {self.cur_stage}.')
                else:   # after payOff definition update nadir for all criteria
                    change = crit.updNadir(self.cur_stage, val, self.minDiff)  # update nadir (depends on stage)
                    if change:
                        self.payOffChange = True
            # if self.par_rep:  # addSol() is now in Report::itr()
            #     self.par_rep.addSol(self.cur_itr_id)   # add solution to ParRep solutions
        else:
            sys.stdout.flush()  # needed for printing exception at the output end
            raise Exception(f'Mcma::store_sol() not implemented yet for stage: {self.cur_stage}.')

    def diffOK(self, i, val1, val2):  # return True if the difference of two values of i-th is large enough
        maxVal = max(abs(self.cr[i].utopia), (abs(self.cr[i].nadir)))  # value used as basis for min-differences
        minDiff = self.minDiff * maxVal
        if abs(val1 - val2) >= minDiff:
            return True
        else:
            return False
    '''

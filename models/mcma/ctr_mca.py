"""
Handle data structure and control flows of the MCMA
"""
import sys      # needed from stdout
import os
import math
from os import R_OK, access
from os.path import isfile
# import numpy as np
from .crit import Crit, CrPref
from .par_repr import ParRep


class CtrMca:
    def __init__(self, cfg):   # par_rep False/True controls no/yes Pareto representation mode
        self.cfg = cfg
        self.ana_dir = cfg.get('ana_dir')  # wrk dir for the current analysis
        self.f_crit = 'config.txt'   # file with criteria specification
        self.f_payoff = 'payoff.txt'     # file with payoff values
        self.f_pref = 'pref.txt'     # file with defined preferences' set
        self.stages = {'ini': 0, 'utop': 1, 'nad1': 2, 'nad2': 3, 'RFPauto': 4, 'RFPuser': 5, 'end': 6} # noqa
        self.cur_stage = 0  # initialization
        self.cur_itr_id = None  # id of the current iteration
        self.cr = []        # objects of Crit class, each representing the corresponding criterion
        self.n_crit = 0     # number of defined criteria == len(self.cr)
        self.is_opt = None  # indicates True/False avail. of optimal solution (set in driver())
        self.is_par_rep = cfg.get('parRep')    # if True, then switch to ParetoRepresentation mode
        self.par_rep = None    # ParRep object (used only, if is_par_rep == True)
        self.deg_exp = False    # expansion of degenerated cube dimensions
        self.cur_cr = None  # cr_index passed to self.set_pref()
        self.pay_upd = False  # set to true, if current payOff differs from the store one
        # tolerances
        self.cafAsp = 100.   # value of CAF at A (if A undefined, then at U)
        self.critScale = 1000.   # range [utopia, nadir] of scaled values (no longer needed?)
        # self.epsilon = 0.0001  # fraction of self.cafAsp used for scaling the AF regularizing term
        self.epsilon = 1.e-6  # fraction of self.cafAsp used for scaling the AF regularizing term
        self.minDiff = 0.001  # min. relative differences between (U, N), (U, A), (A, R), (R, N) (was 0.01)
        self.slopeR = 10.    # slope ratio between mid-segment and segments above A and below R
        # diverse
        # self.scVar = self.opt('scVar', True)   # scale core-model vars defining CAFs
        self.scVar = self.opt('scVar', False)   # scale core-model vars defining CAFs
        self.verb = self.opt('verb', 1)   # print verbosity: 0 - min., 1 - key, 2 - debug, 3 - detailed
        self.pref = []    # list of preferences defined for each blocks
        self.n_pref = 0     # number of blocks of read-in preferences
        self.cur_pref = 0   # index of currently processed preference
        self.payOffChange = True    # set to False, after every storing, to True after any nadir modified
        self.hotStart = None    # if payOff provided, jump to stage==5

        self.rdCritSpc()    # read criteria specs from the config file
        self.rd_payoff()    # Load payOff table if previously stored (initialized to undefined by Crit ctor)

    def opt(self, key_id, def_val):
        val = self.cfg.get(key_id)
        if val is None:
            return def_val
        else:
            return val

    def addCrit(self, cr_name, typ, var_name):
        """
        Add definition of a criterion.

        :param cr_name: criterion name
        :type cr_name:  str
        :param var_name: name of the corresponding model variable
        :type var_name:  str
        :param typ: criterion type (either 'min' or 'max')
        :type typ:  str
        :return:  None
        """
        # todo: verify the check of cr_name duplication
        if self.cr_ind(cr_name, False) == -1:  # add, if the cr_name is not already used
            self.cr.append(Crit(cr_name, var_name, typ))
            self.n_crit = len(self.cr)
        else:
            raise Exception(f'addCrit(): duplicated criterion name: "{cr_name}".')

    def cr_ind(self, cr_name, fatal=True):  # return index (in self.cr) of criterion having name cr_name
        for (i, crit) in enumerate(self.cr):
            if crit.name == cr_name:
                return i
        if fatal:   # raise exception
            raise Exception(f'cr_ind(): unknown criterion name: "{cr_name}".')
        else:   # only inform
            return -1

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
                    # assert(n_words == 3), f'line {line} has {n_words} instead of the required three.'
                    # self.set_payOff(words[0], words[1], words[2])
                    assert n_words == 5, f'line {line} has {n_words} instead of the required five.'
                    self.set_payOff(words[0], words[2], words[4])
                    n_def += 1
            assert (self.n_crit == n_def), f'stored payOff table has {n_def} values for {self.n_crit} defined criteria.'
            self.prnPayOff(True)    # print only (don't write to the file)
            self.hotStart = True  # if payOff provided, jump to stage==5
            self.cur_stage = 5
            print(f'\nPayOff table provided. Skipping its computation. Jump to processing user-defined preferences.')
        else:
            print(f"\nFile '{self.f_payoff}' with stored payoff table not available.")
            self.hotStart = False  # if payOff provided, jump to stage==5

    def prnPayOff(self, prn_only=False):   # store current values of utopia/nadir in a file for subsequent use
        # to create a dir: os.makedirs(dir_name, mode=0o755)
        # create file for writing (over-writes previous, if exists)
        if not self.payOffChange:
            # print('payOff table values not changed.')
            return
        print('PayOff table:')
        lines = []
        for crit in self.cr:
            line = f'{crit.name}\t U {crit.utopia:.3e}   N {crit.nadir:.3e}'
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

    def scale(self):    # define scaling-coeffs (for scaling criteria values to the same range of values)
        print(f'\nDefining criteria scaling coefficients.')
        for cr in self.cr:
            diff = abs(cr.utopia - cr.nadir)
            assert diff > self.minDiff, f'Crit. "{cr.name}" utopia {cr.utopia:.4e} too close to nadir {cr.nadir}:.4e.'
            sc_tmp = self.critScale / diff
            magn = int(math.log10(sc_tmp))
            cr.sc_var = math.pow(10, magn)
            print(f'Criterion "{cr.name}", {cr.attr}: scaling coef. = {cr.sc_var:.1e}, utopia {cr.utopia:.2e}, ' 
                  f'nadir {cr.nadir:.2e}\n\tnot-rounded scaling (to range {self.critScale:.1e}) = {sc_tmp:.4e}.')

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
                # raise Exception(f'set_stage(): nadir2 stage NOT implemented yet.')
            return self.cur_stage
        elif self.cur_stage == 3:  # second approximation of Nadir
            if self.cur_cr + 1 < self.n_crit:   # not all crit used?
                self.cur_cr += 1    # use next (not yet used) criterion
                print(f'Appr. Nadir of crit. other than {self.cr[self.cur_cr].name} (stage {self.cur_stage}).')
            else:   # move to the 2nd stage of nadir appr.
                print('Finished 2nd nadir approximation.')
                print('Approximation of PayOff table ready. Preferences for neutral solution set automatically.')
                self.cur_stage = 4
                self.cur_cr = None     # should no longer be used
            return self.cur_stage
        elif self.cur_stage == 4:  # comes here after computing neutral solution
            print('Finished computation of neutral Pareto solution.')
            print('Switch to get and process user-preferences.')
            self.cur_stage = 5
            self.cur_cr = None  # should no longer be used
            self.hotStart = True
            return self.cur_stage   # return to set pref for gor neutral solution and compute it
        elif self.cur_stage == 5:  # comes here while processing preferences
            # after debugging, nothing to do here
            # print('Continue to get and handle user preferences.')
            return self.cur_stage
        else:
            raise Exception(f'set_stage(): stage {self.cur_stage} NOT implemented yet.')

        # return self.cur_stage

    def set_pref(self):
        # set automatically (acording to programmed rules for each stage) crit attributes:
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
        elif self.cur_stage == 4:     # set A and R for neutral solution
            print(f'---\nMcma::set_pref(): for neutral solution, stage: {self.cur_stage}.')
            for crit in self.cr:
                crit.setAR()
            return
        elif self.cur_stage == 5:     # get user-preferences
            self.usrPref()    # driver() calls setPref() function to access usrPref()
            return

        sys.stdout.flush()  # needed for printing exception at the output end
        raise Exception(f'Mcma::set_pref() not implemented yet for stage: {self.cur_stage}.')

    def par_pref(self):  # generate preferences for finding next solution in Pareto set representation
        assert self.is_par_rep, f'CtrMca::par_pref() is not set to be used.'
        assert self.cur_stage == 5, f'CtrMca::par_pref() should not be called for cur_stage {self.cur_stage}.'
        if self.par_rep is None:
            self.par_rep = ParRep(self)     # initialize Pareto set representation
        self.par_rep.pref()     # define largest cube, set A/R&activity in mc.cr[] in the model (not ASF) scale
        # raise Exception(f'Mcma::par_pref() not implemented yet.')

    def usrPref(self):  # get user-preferences (if no more pref avail. then set self.cur_stage = 6 for a clean exit)
        # todo: make sure that all criteria are active by default
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

    def rdCritSpc(self):    # read specification of criteria
        print(f'\nCreating criteria defined in cfg_usr.yml file.')
        cr_def = self.cfg.get('crit_def')
        assert cr_def is not None, f'Criteria not defined in the cfg_usr.yml file.'
        self.n_crit = len(cr_def)
        for i, cr in enumerate(cr_def):
            n_words = len(cr)  # crit-name, type (min or max), name of core-model var defining the crit.
            assert n_words == 3, f'definition of {i}-th criterion has {n_words} elements instead of the required three.'
            self.addCrit(cr[0], cr[1], cr[2])  # store the criterion specs
        assert (self.n_crit > 1), f'at least two criteria need to be defined, only {self.n_crit} was defined.'
        '''
        print(f"\nCreating criteria defined in file '{self.f_crit}':")
        self.n_crit = 0
        with open(self.f_crit) as reader:  # read and store specs of criteria
            for n_line, line in enumerate(reader):
                line = line.rstrip("\n")
                # print(f'line {line}')
                if line[0] == "*" or len(line) == 0:  # skip commented and empty lines
                    continue
                words = line.split()
                n_words = len(words)    # crit-name, type (min or max), name of core-model var defining the crit.
                assert n_words == 3, f'line {line} has {n_words} instead of the required three.'
                self.addCrit(words[0], words[1], words[2])    # store the criterion specs
        '''

    def readPref(self):  # read preferences provided in file self.f_pref
        # each line defines: cr_name, A, R, optionally activity for a criterion
        # sets of preferences for all criteria should be separated by line having only #-char in first column
        # preferences for criteria not specified in a set are reset to: A=utopia, R=nadir, criterion not-active

        self.n_pref = 0  # number of specified sets of preferences
        if not (isfile(self.f_pref) and access(self.f_pref, R_OK)):
            print(f"\nUser-preferences not defined (file '{self.f_pref}' is not accessible).")
            return
        print(f"\nReading user-preferences defined in file '{self.f_pref}':")
        lines = []
        with open(self.f_pref) as reader:  # read all lines and store for processing next
            for n_line, line in enumerate(reader):
                line = line.rstrip("\n")
                # print(f'line {n_line}: "{line}"')
                if len(line) == 0 or line[0] == '*':    # skip empty or commented lines
                    continue
                if line[0] == "#" or len(line) == 1:  # separator of set of preferences
                    # print(f'marker found in line {n_line}')
                    pass
                else:
                    words = line.split()
                    n_words = len(words)    # crit-name, type (min or max), name of core-model var defining the crit.
                    assert 3 <= n_words <= 4, f'line {line} has {n_words}; required are either three or four.'
                    for i in [1, 2]:
                        assert type(float(words[i])) == float and words[i] is not None, \
                            f'line "{line}": "{words[i]}" should be a float number.'
                lines.append(line)
        line = '#'
        lines.append(line)  # make sure that the last line marks end of a set

        print(f'Process {len(lines)} lines with user preferences.')
        cur_set = []    # current set of preferences (specified in blocks of lines separated by #)
        for n_line, line in enumerate(lines):
            # print(f'processing {n_line}-th line: {line}')
            if line[0] != '#':  # process the line
                words = line.split()    # number of words check above
                c_ind = self.cr_ind(words[0], False)
                if c_ind < 0:
                    raise Exception(f'unknown crit. name "{words[0]}" in {n_line}: "{line}".')
                pref_item = CrPref(c_ind, float(words[1]), float(words[2]), len(words) == 3)
                self.cr[c_ind].chkAR(pref_item, n_line)  # check correctness of A and R values
                for item in cur_set:    # check, if crit. preferences are already defined in the current set
                    if c_ind == item.parent:
                        raise Exception(f'duplicated (in the current set, line {n_line}) preferences for '
                                        f'criterion "{self.cr[c_ind].name}".')
                cur_set.append(pref_item)   # add to the current set
            else:
                n_items = len(cur_set)
                if n_items == self.n_crit:
                    self.pref.append(cur_set)
                else:
                    if n_items > 0:
                        raise Exception(f'{n_items} preference(s) in the block ending at line {n_line} for  '
                                        f'{self.n_crit} defined criteria.')
                    else:
                        print(f'ignoring empty block ending at line {n_line}')
                cur_set = []    # empty for starting a new set

        self.n_pref = len(self.pref)
        print(f'Prepared {self.n_pref} sets of user-defined preferences.')

    '''
    def procPrefSet(self, lines):  # process set of lines defining preferences
        pref_set = []
        for line in lines:
            words = line.split()
            c_ind = self.cr_ind(words[0], False)
            if c_ind < 0:
                print(f'unknown criterion name "{words[0]}", ignoring line {line}.')
                continue
            is_ok = self.cr[c_ind].chkAR(words[1], words[2])  # check correctness of A and R values
            if is_ok:
                # pr_line = words[0] + ' ' + float(words[1]) + ' ' + float(words[2])
                # if len(words) == 4:
                #     pr_line += ' n'     # criterion non-active
                pref_set.append(line)
            else:
                print(f'ignoring inconsistent preferences: {line}.')
        if len(pref_set) > 0:
            self.pref.append(pref_set)
            return True
        else:
            print(f'ignoring empty set of preferences.')
            return False
    '''

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
            if self.par_rep:
                self.par_rep.addSol(self.cur_itr_id)   # add solution to ParRep solutions
        else:
            sys.stdout.flush()  # needed for printing exception at the output end
            raise Exception(f'Mcma::store_sol() not implemented yet for stage: {self.cur_stage}.')
        '''
        elif self.cur_stage == 2:  # update nadir values
            # print(f'---\nMcma::store_sol(): TESTING for stage {self.cur_stage}.')
            for crit in self.cr:
                val = crit_val.get(crit.name)
                crit.val = val
                if crit.is_active:  # nothing to store/update
                    print(f'NOT updating nadir for active crit "{crit.name}" = {val}')
                else:
                    crit.updNadir(self.cur_stage, val)  # update nadir value
        elif self.cur_stage == 3:   # update nadir values
            print(f'---\nMcma::store_sol() in stage {self.cur_stage}.')
            for crit in self.cr:
                val = crit_val.get(crit.name)
                crit.val = val
                if crit.is_active:  # nothing to store/update
                    print(f'NOT updating nadir for active crit "{crit.name}" = {val}')
                else:
                    crit.updNadir(self.cur_stage, val)   # update nadir value
        '''

    def diffOK(self, i, val1, val2):  # return True if the difference of two values of i-th is large enough
        maxVal = max(abs(self.cr[i].utopia), (abs(self.cr[i].nadir)))  # value used as basis for min-differences
        minDiff = self.minDiff * maxVal
        if abs(val1 - val2) >= minDiff:
            return True
        else:
            return False

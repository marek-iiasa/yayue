"""
Handle data structure and control flows of the MCMA
"""
import sys      # needed from stdout
import os
# import numpy as np
from crit import Crit


class CtrMca:
    def __init__(self, ana_dir):
        self.ana_dir = ana_dir  # wrk dir for the current analysis
        self.f_payoff = ana_dir + '/payoff.txt'     # file with payoff values
        self.pay_upd = False  # set to true, if current payOff differs from the store one
        self.cr = []        # objects of Crit class, each representing the corresponding criterion
        self.n_crit = 0     # number of defined criteria == len(self.cr)
        self.stages = {'ini': 0, 'utop': 1, 'nad0': 2, 'nad1': 3, 'pref': 4, 'end': 5}
        self.cur_stage = 0  # initialization
        self.cur_cr = None  # cr_index passed to self.set_pref()
        # self.cur_uto = None   # cr-index of currently computed utopia
        # self.cur_nad = None   # cr-index of currently approximated nadir

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
        # todo: add checking cr_name duplication
        self.cr.append(Crit(cr_name, var_name, typ))
        self.n_crit = len(self.cr)

    def cr_ind(self, cr_name):  # return index (in self.cr) of criterion having name cr_name
        for (i, crit) in enumerate(self.cr):
            if crit.name == cr_name:
                return i
        raise Exception(f'cr_ind(): unknown criterion name: "{cr_name}".')

    def set_payOff(self, cr_name, utopia=None, nadir=None):   # set the provided utopia/nadir values (if not None)
        print(f'Crit. "{cr_name}": checking update of {utopia=}, {nadir=} values.')
        i = self.cr_ind(cr_name)    # get the criterion index in cr[]
        updated = False
        # todo: add tolerances for checks of old and new values
        if utopia:  # value provided
            if self.cr[i].utopia != utopia:
                updated = True
                print(f'Crit. "{cr_name}": utopia value {cr_name.utopia} updated to {utopia}.')
                self.cr[i].utopia = utopia
                self.cr[i].uto_def = True
        if nadir:  # value provided
            if self.cr[i].nadir != nadir:
                updated = True
                print(f'Crit. "{cr_name}": nadir value {cr_name.nadir} updated to {nadir}.')
                self.cr[i].nadir = nadir
                self.cr[i].nad_def = True
        if updated:
            self.pay_upd = True

    def rd_payoff(self):    # read stored utopia/nadir values and store them as self.cr attributes
        if os.path.exists(self.f_payoff):
            with open(self.f_payoff, "r") as reader:
                print(f"\nReading payoff table stored in file '{self.f_payoff}':")
                n_def = 0
                for n_line, line in enumerate(reader):
                    line = line.rstrip("\n")
                    # print(f'line {line}')
                    words = line.split()
                    n_words = len(words)
                    assert(n_words == 3), f'line {line} has {n_words} instead of the required three.'
                    self.set_payOff(words[0], words[1], words[2])
                    n_def += 1
            assert (self.n_crit == n_def), f'stored payOff table has {n_def} values for {self.n_crit} defined criteria.'
            # todo: update values of {uto, nad}_def
        else:
            print(f"\nFile '{self.f_payoff}' with stored payoff table not available.")

    def prn_payoff(self):   # store current values of utopia/nadir in a file for subsequent use
        # to create a dir: os.makedirs(dir_name, mode=0o755)
        # create file for writing (over-writes previous, if exists)
        print(f'\nCurrent values of the payoff table written to file "{self.f_payoff}":')
        f_payOff = open(self.f_payoff, "w")
        for crit in self.cr:
            line = f'{crit.name} {crit.utopia} {crit.nadir}'
            print(line)
            f_payOff.write(line + '\n')
        f_payOff.close()

    def chk_utopia(self):    # return index (in self.cr) of criterion, if its utopia/nadir should be computed
        for (i, crit) in enumerate(self.cr):
            if not crit.utopia:
                return i
        print(f'All utopia components computed.')
        return -1

    def set_stage(self):
        """Define and return analysis stage; provide info (in self.cur_cr) for mc.set_pref() """
        if self.cur_stage == 0:     # initialization
            print('Initialization finished, checking, if all utopia components computed.')
            self.cur_stage = 1
        if self.cur_stage == 1:     # computing utopia
            i_cr = self.chk_utopia()   # check, if all utopias computed
            if i_cr > -1:   # utopia of i_cr-th criterion needs to be computed
                self.cur_cr = i_cr
                print(f'Utopia of criterion "{self.cr[i_cr].name}" shall be computed.')
            else:   # all utopia computed, start first stage of nadir approximation
                print('All utopia components computed. Start first stage of nadir approximation.')
                self.cur_cr = 0     # start first nedir appr with 0-th criterion
                self.cur_stage = 2
                # the belo moved to mc_set_pref()
                # # initialize below crit attributes needed for first stage of nadir app.
                # for crit in self.cr:  # set all criteria to be active
                #     crit.is_active = True
                #     crit.nad_def = False    # reset after stage 1 (nadir value of stage 1 is kept)
            return self.cur_stage
        elif self.cur_stage == 2:  # continue first approximation of Nadir ?
            # i_cr = self.chk_payoff(True)    # check, if all nadirs computed
            # if i_cr == -1:  # all nadir of at current stage computed
            #     self.cur_nad = None
            #     print('Finished first nadir approximations. Start the second approximations.')
            #     self.cur_stage += 1     # move to the second Nadir appr.
            # else:
            #     self.cur_nad = i_cr  # store crit-index of currently approximated nadir
            #     print(f'Appr. Nadir of crit. other than {self.cr[i_cr].name} (stage {self.cur_stage}).')
            #     return self.cur_stage
            if self.cur_cr + 1 < self.n_crit:   # not all crit were used in first stagee of nadir appr.
                self.cur_cr += 1    # use next (not yet used) criterion
                print(f'Appr. Nadir of crit. other than {self.cr[self.cur_cr].name} (stage {self.cur_stage}).')
            else:   # move to the 2nd stage of nadir appr.
                print('Finished first nadir approximations. Start the 2nd nadir approximations.')
                self.cur_cr = 0     # start first nedir appr with 0-th criterion
                self.cur_stage = 3
                raise Exception(f'set_stage(): nadir2 stage NOT implemented yet.')
            return self.cur_stage
        elif self.cur_stage == 3:  # second approximation of Nadir
            raise Exception(f'set_stage(): nadir2 stage NOT implemented yet.')
        elif self.cur_stage > 3:  # second approximation of Nadir
            raise Exception(f'set_stage(): stage {self.cur_stage} NOT implemented yet.')

        print('PayOff table available. Ready to handle preferences.')
        return self.cur_stage

    def set_pref(self):     # set crit attributes (activity, A/R, possibly adjust nadir app).
        assert self.cur_stage > 0, f'CtrMca::set_pref() should not be called for cur_stage {self.cur_stage}.'
        if self.cur_stage == 1:  # set only currently computed utopia criterion to be active
            for (i, crit) in enumerate(self.cr):
                if self.cur_cr == i:
                    crit.is_active = True
                else:
                    crit.is_active = False
            return
        elif self.cur_stage == 2:     # set one crit active in first appr. of Nadir
            print(f'---\nMcma::set_pref(): TESTING for stage: {self.cur_stage}.')
            for (i, crit) in enumerate(self.cr):
                if self.cur_cr == i:
                    crit.is_active = True
                else:
                    crit.is_active = False
            return

        sys.stdout.flush()  # needed for printing exception at the output end
        raise Exception(f'Mcma::set_pref() not implemented yet for stage: {self.cur_stage}.')

    '''
    def upd_nad(self, stage, crit, new_val):    # update nadir appr.
        assert crit.nadir is not None, f'nadir of crit {crit.name} undefined before stage {self.cur_stage}.'
        assert self.cur_stage > 1, f'upd_nad() should not be called in stage {self.cur_stage}.'
        assert self.cur_stage < 3, f'upd_nad() not implemented yet for stage {self.cur_stage}.'
        shift = False
        old_val = crit.nadir
        eps = 1.e-6  # margin to exclude "almost equal"
        # todo: should be tighten in stage 2 (value from stage 1 could be far away) and relaxed in higher stages
        if stage == 2:  # tighten not Pareto nadir computed at stage 1
            if crit.mult == 1:  # max crit.
                if old_val + eps < new_val:  # old might be too small to belong to Pareto set
                    shift = True    # tighten nadir
            else:  # min. crit.
                if old_val - eps > new_val:  # old might be too large to belong to Pareto set
                    shift = True    # tighten nadir
        else:   # after stage 2, nadir should be moved to worse value
            pass
        if shift:
            crit.nadir = new_val
            yes_no = ''
        else:
            yes_no = 'not'
        print(f'nadir appr. of crit {crit.name}: {old_val} {yes_no} changed to {new_val}.')
    '''

    def store_sol(self, crit_val):
        print(f'Processing criteria values of the current iteration: {crit_val}')
        if self.cur_stage == 1:     # utopia computed for the only one active criterion
            for (i, crit) in enumerate(self.cr):
                cr_name = self.cr[i].name
                val = crit_val.get(cr_name)
                crit.val = val
                if crit.is_active:  # utopia computed
                    crit.utopia = val
                # else:   # set/update nadir for not activate
                # store/update nadir for all criteria
                if crit.nadir is None:  # not yet stored: store the current value
                    crit.nadir = val
                    print(f'Storing initial approxation of nadir for crit "{cr_name}" = {val}')
                else:   # store nadir, if the new value is a better appr.
                    self.cr[i].updNadir(self.cur_stage, val)
                    # print(f'Storing subsequent approxation of nadir for crit "{cr_name}" = {val}')
        elif self.cur_stage == 2:   # update nadir values
            print(f'---\nMcma::store_sol(): TESTING for stage {self.cur_stage}.')
            for (i, crit) in enumerate(self.cr):
                cr_name = self.cr[i].name
                val = crit_val.get(cr_name)
                crit.val = val
                if crit.is_active:  # nothing to store/update
                    print(f'NOT updating nadir for active crit "{cr_name}" = {val}')
                    # pass
                else:   # store nadir value
                    self.cr[i].updNadir(self.cur_stage, val)
                    # print(f'Storing subsequent approxation of nadir for crit "{cr_name}" = {val}')
        else:
            sys.stdout.flush()  # needed for printing exception at the output end
            raise Exception(f'Mcma::store_sol() not implemented yet for stage: {self.cur_stage}.')

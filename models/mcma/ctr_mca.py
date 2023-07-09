"""
Handle data structure and control flows of the MCMA
"""
import sys      # needed from stdout
import os
# import numpy as np
from crit import Crit


def nad_appr(crit, val):    # return True, if val is a better nadir appr.
    if crit.nadir is None:
        return True
    if crit.mult == 1:  # max crit.
        if val < crit.nadir:
            return True
    else:       # min. crit.
        if val > crit.nadir:
            return True
    return False


class CtrMca:
    def __init__(self, ana_dir):
        self.ana_dir = ana_dir  # wrk dir for the current analysis
        self.f_payoff = ana_dir + '/payoff.txt'     # file with payoff values
        self.stages = {'ini': 0, 'utop': 1, 'nad0': 2, 'nad1': 3, 'pref': 4, 'end': 5}
        self.cur_stage = 0  # initialization
        self.cur_uto = None   # cr-index of currently computed utopia
        self.cur_nad = None   # cr-index of currently approximated nadir
        self.cr = []    # objects of Crit class, each representing the corresponding criterion
        self.n_crit = 0     # number of defined criteria == len(self.cr)

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

    def payOff(self, cr_name, utopia, nadir):
        i = self.cr_ind(cr_name)    # get the criterion index in cr[]
        if utopia:
            self.cr[i].utopia = utopia
        if nadir:
            self.cr[i].nadir = nadir
        print(f'Criterion "{cr_name}": values of {utopia=}, {nadir=} stored in attributes of self.cr[].')

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
                    self.payOff(words[0], words[1], words[2])
                    n_def += 1
            assert (self.n_crit == n_def), f'stored payOff table has {n_def} values for {self.n_crit} defined criteria.'
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

    def chk_payoff(self, nadir):    # return index (in self.cr) of criterion, if its utopia/nadir should be computed
        for (i, crit) in enumerate(self.cr):
            if nadir:   # check if nadir needs to be computed
                if not crit.nad_def:
                    print(f'Nadir value of criterion {crit.name} shall be computed next.')
                    return i
            else:   # check if utopia needs to be computed
                if not crit.utopia:
                    print(f'Utopia value of criterion "{crit.name}" shall be computed next.')
                    return i
        print(f'All payoff table components computed.')
        return -1   # all utopia/nadir values are computed

    def chk_stage(self):
        """Control the analysis stage; move to next stage if the current is completed.

        :return:  current stage
        :rtype:  int
        """
        if self.cur_stage == 0:     # initialization
            print('Initialization finished, checking, if all utopia components computed.')
            self.cur_stage = 1
        if self.cur_stage == 1:     # computing utopia
            i_cr = self.chk_payoff(False)   # check, if all utopias computed
            if i_cr > -1:   # utopia of i_cr-th criterion needs to be computed
                self.cur_uto = i_cr
                print(f'Utopia of criterion {self.cr[self.cur_uto].name} shall be computed.')
                return self.cur_stage
            else:   # all utopia computed, start first stage of nadir approximation
                print('All utopia components computed. Start first stage of nadir approximation.')
                self.cur_uto = None
                # todo: initialize below crit attributes needed for first stage of nadir app.
                for crit in self.cr:  # set all criteria to be active
                    crit.is_active = True
                self.cur_stage = 2
                # return self.cur_stage

        if self.cur_stage == 2:  # first approximation of Nadir
            i_cr = self.chk_payoff(True)    # check, if all nadirs computed
            if i_cr == -1:  # all nadir of at current stage computed
                self.cur_nad = None
                print('Finished first nadir approximations. Start the second approximations.')
                self.cur_stage += 1     # move to the second Nadir appr.
            else:
                self.cur_nad = i_cr  # store crit-index of currently approximated nadir
                print(f'Nadir appr. of crit. {self.cr[i_cr].name} shall be computed (stage {self.cur_stage}.')
                return self.cur_stage

        if self.cur_stage == 3:  # second approximation of Nadir
            raise Exception(f'chk_stage(): nadir2 stage NOT implemented yet.')

        print('PayOff table available. Ready to handle preferences.')
        return self.cur_stage
    # todo: either update crit.{uto,nad}_def or remove, if they not not really needed

    def set_pref(self):     # set crit attributes (activity, A/R, possibly adjust nadir app).
        assert self.cur_stage > 0, f'CtrMca::set_pref() should not be called for cur_stage {self.cur_stage}.'
        if self.cur_stage == 1:  # set only currently computed utopia criterion to be active
            for (i, crit) in enumerate(self.cr):
                if self.cur_uto == i:
                    crit.is_active = True
                else:
                    crit.is_active = False
            return
        elif self.cur_stage == 2:     # first appr. of Nadir
            raise Exception(f'Mcma::set_pref() not finished for stage: {self.cur_stage}.')
        sys.stdout.flush()  # needed for printing exception at the output end
        raise Exception(f'Mcma::set_pref() not implemented yet for stage: {self.cur_stage}.')

    # noinspection PyMethodMayBeStatic
    def upd_nad(self, stage, crit, val):    # update nadir appr.
        is_better = nad_appr(crit, val)
        yes_no = 'not'
        old_nad = crit.nadir
        if is_better and stage > 3:
            yes_no = ''
            crit.nadir = val
        elif not is_better and stage <= 3:
            yes_no = ''
            crit.nadir = val
        print(f'nadir appr. of crit {crit.name} = {old_nad} {yes_no} changed to {val}')

    def store_sol(self, crit_val):
        print(f'Processing criteria values of the current iteration: {crit_val}')
        if self.cur_stage == 1:     # utopia computed for the only one active criterion
            for (i, crit) in enumerate(self.cr):
                cr_name = self.cr[i].name
                val = crit_val.get(cr_name)
                crit.val = val
                if crit.is_active:  # utopia computed
                    crit.utopia = val
                    crit.uto_def = True
                else:   # store nadir value
                    if crit.nadir is None:  # not yet stored: store the current value
                        crit.nadir = val
                        print(f'Storing first approxation of nadir for crit "{cr_name}" = {val}')
                    else:   # store nadir, if the new value is a better appr.
                        # todo: correct storing intermediate nadir approximation
                        self.upd_nad(self.cur_stage, crit, val)
                        print(f'Storing subsequent approxation of nadir for crit "{cr_name}" = {val}')
        else:
            sys.stdout.flush()  # needed for printing exception at the output end
            raise Exception(f'Mcma::store_sol() not implemented yet for stage: {self.cur_stage}.')

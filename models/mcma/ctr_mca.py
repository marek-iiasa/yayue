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
        self.stages = {'ini': 0, 'utop': 1, 'nad0': 2, 'nad1': 3, 'pref': 4, 'end': 5}
        self.cur_stage = 0  # initialization
        self.nad_cur = None   # cr-index of currently approximated nadir
        self.cr = []    # list of criteria
        self.n_crit = 0

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
        # TODO: add checking cr_name duplication
        self.cr.append(Crit(cr_name, var_name, typ))
        self.n_crit = len(self.cr)

    def cr_ind(self, cr_name):
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
        print(f'Criterion "{cr_name}": defined values of {utopia=}, {nadir=} set in the PayOff table.')

    def rd_payoff(self):
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

    def prn_payoff(self):
        # to create a dir: os.makedirs(dir_name, mode=0o755)
        # create file for writing (over-writes previous, if exists)
        print(f'\nCurrent values of the payoff table written to file "{self.f_payoff}":')
        f_payOff = open(self.f_payoff, "w")
        for crit in self.cr:
            line = f'{crit.name} {crit.utopia} {crit.nadir}'
            print(line)
            f_payOff.write(line + '\n')
        f_payOff.close()

    def chk_payoff(self, nadir):
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
        return -1

    def chk_stage(self):
        """Determine stage of the analysis.

        :return:  current stage
        :rtype:  int
        """
        if self.cur_stage == 0:     # initialization
            print('Initialization finished, check if all utopia components computed.')
            self.cur_stage = 1
        if self.cur_stage == 1:     # computing utopia
            i_cr = self.chk_payoff(False)   # check, if all utopias computed
            if i_cr > -1:   # utopia of i_cr-th criterion needs to be computed
                for (i, crit) in enumerate(self.cr):
                    if i_cr == i:
                        crit.is_active = True
                    else:
                        crit.is_active = False
                return self.cur_stage
            else:   # all utopia computed, start first stage of nadir approximation
                print('All utopia components computed. Start first stage  of nadir approximation.')
                self.cur_stage = 2

        for crit in self.cr:    # set all criteria to be active
            crit.is_active = True

        if 1 < self.cur_stage < 4:     # stages 2 or 3: nadir approximation
            if self.cur_stage == 3:
                raise Exception(f'chk_stage(): nadir2 stage NOT implemented yet.')
            i_cr = self.chk_payoff(True)    # check, if all nadirs computed
            if i_cr == -1:  # all nadir of at current stage computed
                self.nad_cur = None
                if self.cur_stage == 2:
                    print('Finished first nadir approximations. Start the second approximations.')
                else:
                    print('PayOff table available. Ready to handle preferences.')
                self.cur_stage += 1     # move to the next stage
            else:
                self.nad_cur = i_cr  # store crit-index of currently approximated nadir

        return self.cur_stage
    # todo: either update crit.{uto,nad}_def or remove, if they not not really needed

    def set_pref(self):     # set crit attributes (activity, A/R, possibly adjust nadir app.
        if self.cur_stage < 2:     # flow error
            raise Exception(f'Mcma::set_pref() should not be called for stage: {self.cur_stage}.')
        sys.stdout.flush()  # needed for printing exception at the output end
        raise Exception(f'Mcma::set_pref() not implemented yet for stage: {self.cur_stage}.')

    def store_sol(self, crit_val):
        print(f'Processing criteria values of the current iteration: {crit_val}')
        if self.cur_stage == 1:     # utopia computed for the only one active criterion
            for (i, crit) in enumerate(self.cr):
                cr_name = self.cr[i].name
                val = crit_val.get(cr_name)
                if crit.is_active:  # utopia computed
                    crit.utopia = val
                    crit.uto_def = True
                else:   # store value
                    if crit.nadir is None:  # not yet stored: store the current value
                        crit.nadir = val
                        print(f'Storing first approxation of nadir for crit "{cr_name} = {val}')
                    else:   # store the worst of (currently and previously computed)
                        # todo: correct storing intermediate nadir approximation
                        crit.nadir = val
                        print(f'Storing subsequent approxation of nadir for crit "{cr_name} = {val}')
        else:
            sys.stdout.flush()  # needed for printing exception at the output end
            raise Exception(f'Mcma::store_sol() not implemented yet for stage: {self.cur_stage}.')

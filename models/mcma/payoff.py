"""
Handle the Payoff table (computation/read_in, update, saving)
"""
# import sys      # needed from stdout
import os
# import math
# from os import R_OK, access
# from os.path import isfile
# from .crit import Crit, CrPref
# from .par_repr import ParRep


# noinspection SpellCheckingInspection
class PayOff:   # payoff table: try to download, set A/R for computing, update Nadir and save, decide to reset
    def __init__(self, mc):   # par_rep False/True controls no/yes Pareto representation mode
        self.mc = mc
        self.cfg = mc.cfg
        self.cr = mc.cr       # objects of Crit class, each representing the corresponding criterion
        self.n_crit = mc.n_crit     # number of defined criteria == len(self.cr)
        self.f_payoff = 'payoff.txt'     # file with payoff values
        self.stages = {'utop': 1, 'nad1': 2, 'nad2': 3, 'done': 4} # noqa
        self.cur_stage = None    # Load payOff table, if previously stored
        self.cur_cr = None  # cr_index of the criterion to be processed
        # tolerances
        self.minDiff = 0.001  # min. relative differences between (U, N), (U, A), (A, R), (R, N) (was 0.01)
        self.payOffChange = True    # set to False, after every storing, to True after any nadir modified

        self.rd_payoff()    # Load payOff table, if previously stored, sets self.cur_stage accordingly

    def done(self):   # return True if PayOff table ready
        return self.cur_stage == 4

    def next_pref(self):   # set_up preferences for next itr of PayOff table computations
        if self.cur_stage == 1:     # utopia
            i_cr = self.chk_utopia()   # check, if all utopias computed
            if i_cr > -1:   # utopia of i_cr-th criterion needs to be computed
                self.cur_cr = i_cr
                print(f'Utopia of criterion "{self.cr[i_cr].name}" shall be computed.')
                for (i, crit) in enumerate(self.cr):
                    crit.is_fixed = False
                    if self.cur_cr == i:
                        crit.is_active = True
                    else:
                        crit.is_active = False
                return
            else:   # all utopia computed, should not come here
                raise Exception(f'PayOff::next_pref() all crit. already processed in stage: {self.cur_stage}.')
                # print('All utopia components computed. Start first stage of nadir approximation.')
                # self.cur_stage = 2
                # self.cur_cr = 0     # start with 0-th criterion
        if self.cur_stage in [2, 3]:   # nadir apr., stages 1 & 2
            if self.cur_cr >= self.n_crit:   # all crit handled in current stage, change stage
                if self.cur_stage == 2:     # proceed to the 2nd nadir appr. (cur_stage 3)
                    print('Finished first nadir approximations. Start the 2nd nadir approximation.')
                    self.cur_stage = 3
                    self.cur_cr = 0     # start with 0-th criterion
                else:       # in 2nd nadir appr. (cur_stage 3)
                    raise Exception(f'PayOff::next_pref() all crit. already processed in stage: {self.cur_stage}.')

            # only activity set; U/N will be used for (the set as None) A/R
            print(f'Appr. Nadir of crit. other than {self.cr[self.cur_cr].name} (stage {self.cur_stage}).')
            for (i, cr) in enumerate(self.cr):
                cr.is_fixed = False
                if self.cur_cr == i:
                    cr.is_active = True
                else:
                    cr.is_active = False
        else:
            raise Exception(f'PayOff::next_pref() should not be called for stage: {self.cur_stage}.')

    def next_sol(self):   # process results of the current iteration
        if self.cur_stage == 1:     # utopia
            for cr in self.cr:
                val = cr.val
                if cr.is_active:
                    cr.setUtopia(val)  # utopia computed
                cr.updNadir(self.cur_stage, val, self.minDiff)
        else:       # Nadir approx. (both stages)
            print(f'---\nPayoff::next_sol(): stage {self.cur_stage}.')
            for cr in self.cr:
                val = cr.val
                cr.a_val = cr.val2ach(val)
                # print(f'\tCrit {cr.name}: val {cr.val:.2f}, a_val {cr.a_val:.2f}')
                if not cr.is_active:  # update nadir
                    change = cr.updNadir(self.cur_stage, val, self.minDiff)  # update nadir (depends on stage)
                    if change:
                        self.payOffChange = True
                        print(f'Updating nadir for inactive crit "{cr.name}" = {val} at PayOff stage {self.cur_stage}.')
            # raise Exception(f'PayOff::next_sol() not implemented yet for stage: {self.cur_stage}.')

        if self.cur_cr + 1 < self.n_crit:
            self.cur_cr += 1  # point to the next (not yet processed) criterion (now in self.next_sol())
        else:       # payoff stage completed, move to the next stage
            if self.cur_stage in [1, 2]:    # move to the (next) nadir stage
                self.cur_stage += 1
                self.cur_cr = 0
            else:       # payoff stage 3 (2nd nadir appr) completed, thus PayOff completed
                self.cur_stage = 4
        # return self.cur_stage     # PayOff stage is internal, should not be returned

    def set_payOff(self, cr_name, utopia, nadir):   # set the previously stored utopia/nadir values
        if utopia is None or nadir is None:
            raise Exception(f'set_payoff("{cr_name}", {utopia=}, {nadir=}): undefined values.')
        utopia = float(utopia)  # read-in words are of type string; have to explicitly converted
        nadir = float(nadir)
        if type(utopia) is not float or type(nadir) is not float:
            print(f'{type(utopia) = }')
            print(f'{type(nadir) = }')
            raise Exception(f'set_payOff("{cr_name}", "{utopia}", "{nadir}"): both values should be of type float.')
        round_eps = 1.e-4     # relative un-rounding margin
        for cr in self.cr:
            if cr.name == cr_name:
                if cr.better(utopia, nadir):
                    uto_adj = cr.mult * round_eps * utopia    # adjust/un_round abs utopia value
                    nad_adj = cr.mult * round_eps * nadir    # adjust/un_round abs nadir value
                    cr.utopia = utopia + uto_adj
                    cr.nadir = nadir - nad_adj
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
            self.cur_stage = 4
            print(f'\nPayOff table provided; skipping its computation.')
        else:
            self.cur_stage = 1      # start with computing Utopia
            print(f"\nFile '{self.f_payoff}' with the payoff table not available.")

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
                line = f'{crit.name}\t U {crit.utopia:.5e}   N {crit.nadir:.5e}'
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

    def update(self, wrk_stage):  # update payOff table, if a Nadir changed, return True if updated
        changed = False
        if wrk_stage < 2:   # don't update during PayOff: it has a dedicated update implemented separately
            return changed
        for cr in self.cr:
            if self.mc.verb > 1:
                print(f'\tCrit {cr.name}: val {cr.val:.2f}')
                # print(f'\tCrit {cr.name}: val {cr.val:.2f}, a_val {cr.a_val:.2f}')    # a_val may be unavailable
            val = cr.val
            updated = cr.updNadir(self.cur_stage, val, self.minDiff)  # update nadir (depends on stage)
            if updated and not changed:
                changed = True
        if changed:
            self.payOffChange = True
            self.prnPayOff()    # print and store

        return changed

    def diffOK(self, i, val1, val2):  # return True if the difference of two values of i-th is large enough
        maxVal = max(abs(self.cr[i].utopia), (abs(self.cr[i].nadir)))  # value used as basis for min-differences
        minDiff = self.minDiff * maxVal
        if abs(val1 - val2) >= minDiff:
            return True
        else:
            return False

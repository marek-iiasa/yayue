"""
Handle data structure and control flows of the MCMA
"""
# import sys      # needed from stdout
# import os
import math
# from os import R_OK, access
# from os.path import isfile
from .crit import Crit      # , CrPref
# from .par_repr import ParRep


# noinspection SpellCheckingInspection
class CtrMca:   # control flows of MCMA at diverse computations states
    def __init__(self, wflow):   # par_rep False/True controls no/yes Pareto representation mode
        self.wflow = wflow
        self.cfg = wflow.cfg
        self.f_crit = 'config.txt'   # file with criteria specification
        self.cr = []        # objects of Crit class, each representing the corresponding criterion
        self.n_crit = 0     # number of defined criteria == len(self.cr)
        self.deg_exp = False    # expansion of degenerated cube dimensions
        # self.ana_dir = cfg.get('ana_dir')  # wrk dir for the current analysis (mcma runs in ana_dir)
        # self.f_pref = 'pref.txt'     # file with defined preferences' set
        # tolerances
        self.cafAsp = 100.   # value of CAF at A (if A undefined, then at U)
        self.critScale = 1000.   # range [utopia, nadir] of scaled values (no longer needed?)
        self.epsilon = 1.e-6  # fraction of self.cafAsp used for scaling the AF regularizing term
        #
        self.minDiff = 0.001  # min. relative differences between (U, N), (U, A), (A, R), (R, N) (was 0.01)
        self.slopeR = 10.    # slope ratio between mid-segment and segments above A and below R
        # diverse
        # self.scVar = self.opt('scVar', True)   # scale core-model vars defining CAFs
        self.scVar = self.opt('scVar', False)   # scale core-model vars defining CAFs
        self.verb = self.opt('verb', 1)   # print verbosity: 0 - min., 1 - key, 2 - debug, 3 - detailed
        self.pref = []    # list of preferences defined for each blocks
        self.n_pref = 0     # number of blocks of read-in preferences
        self.cur_pref = 0   # index of currently processed preference

        self.epsilon = self.opt('eps', self.epsilon)  # scaling of the AF regularizing term
        print(f'epsilon = {self.epsilon:.1e}')
        do_neutral = self.cfg.get('neutral') is True
        print(f'generate neutral solution = {do_neutral}')
        #
        self.rdCritSpc()    # read criteria specs from the config file

    def opt(self, key_id, def_val):     # return: the cfg value if specified; otherwise the default
        val = self.cfg.get(key_id)
        if val is None:
            return def_val
        else:
            return val

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

    # store crit values from last solution, called from Report::itr(), after check that sol is in the U/N range
    def critVal(self, crit_val):
        for cr in self.cr:
            val = crit_val.get(cr.name)
            cr.val = val
            if self.wflow.cur_stage > 1:
                cr.a_val = cr.val2ach(cr.val)
                if self.verb > 2:
                    print(f'\tCrit {cr.name}: val {cr.val:.2f}, a_val {cr.a_val:.2f}')

    def diffOK(self, i, val1, val2):  # return True if the difference of two values of i-th is large enough
        maxVal = max(abs(self.cr[i].utopia), (abs(self.cr[i].nadir)))  # value used as basis for min-differences
        minDiff = self.minDiff * maxVal
        if abs(val1 - val2) >= minDiff:
            return True
        else:
            return False

    '''
    ++++++++++++++++++++ the below to be adapted for reading and handling user-defined A/R  +++++++++++++++++++++++++
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
    '''

    '''
    def readPref(self):  # read preferences provided in file self.f_pref
        # each line defines: cr_name, A, R, optionally activity for a criterion
        # sets of preferences for all criteria should be separated by line having only #-char in first column
        # preferences for criteria not specified in a set are reset to: A=utopia, R=nadir, criterion not-active

        self.n_pref = 0  # number of specified sets of preferences
        raise Exception('CtrMca::readPref() not adapted yet to the new workflow.')

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
    ++++++++++++++++++++ the above to be adapted for reading and handling user-defined A/R  +++++++++++++++++++++++++
        '''
    '''
    def set_pref(self):     # functionality moved to workflow
        sys.stdout.flush()  # needed for printing exception at the output end
        raise Exception(f'Mcma::set_pref() not implemented yet for stage: {self.cur_stage}.')

    def par_pref(self):  # generate preferences for finding next solution in Pareto set representation
        assert self.is_par_rep, f'CtrMca::par_pref() should not be used for usr-def pref.'
        assert self.par_rep is not None, f'CtrMca::par_pref() should be initialized earlier.'
        assert self.cur_stage in [4, 5], f'CtrMca::par_pref() should not be called for cur_stage {self.cur_stage}.'
        self.par_rep.pref()     # define largest cube, set A/R&activity in mc.cr[] in the model (not ASF) scale
    '''

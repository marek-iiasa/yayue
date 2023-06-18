"""
Data structure and handling of the MCMA
"""
import sys      # needed from stdout
# import os
# import numpy as np


class Crit:     # definition and attributes of a single criterion
    # see: ~/src/mcma/mc_defs.h for the corresponding C++ classes
    def __init__(self, cr_name, var_name, typ):
        self.name = cr_name
        self.var_name = var_name
        if typ == 'min':
            self.attr = 'minimized'
            self.mult = -1.  # multiplier (used for simplifying handling)
        elif typ == 'max':
            self.attr = 'maximized'
            self.mult = 1.
        else:
            raise Exception(f'Unknown criterion type "{typ}" for criterion "{cr_name}".')
        self.uto_def = False     # utopia defined?
        self.nad_def = False     # nadir defined?
        self.sc_var = -1.   # scaling of the var value (for defining the corresponding CAF); negative means undefined
        # the below values shall be defined later (when available)
        self.utopia = None
        self.nadir = None
        self.asp = None     # aspiration value (not scaled)
        self.res = None     # reservation value (not scaled)
        self.is_active = True
        print(f"Criterion initialized: crit_name = '{cr_name}', var_name = '{var_name}', {self.attr}.")


class Mcma:
    def __init__(self):
        self.stages = {'ini': 0, 'utop': 1, 'nad0': 2, 'nad1': 3, 'pref': 4, 'end': 5}
        self.cur_stage = 0  # initialization
        self.cr = []    # list of criteria
        self.n_crit = 0

    def addCrit(self, cr_name, var_name, typ):
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

    def chk_payoff(self, nadir):
        for (i, crit) in enumerate(self.cr):
            if nadir:   # check if nadir needs to be computed
                if not crit.nadir:
                    print(f'Nadir value of criterion {crit.name} shall be computed next.')
                    return i
            else:   # check if utopia needs to be computed
                if not crit.utopia:
                    print(f'Utopia value of criterion "{crit.name}" shall be computed next.')
                    return i
        print(f'All payoff table components computed. Ready for the Asp/Ref-based analysis.')
        return -1

    def chk_stage(self):
        """Determine stage of the analysis.

        :return:  current stage
        :rtype:  int
        """
        i_cr = self.chk_payoff(False)   # check, if all utopias computed
        if i_cr > -1:   # utopia of i_cr-th criterion needs to be computed
            for (i, crit) in enumerate(self.cr):
                if i_cr == i:
                    crit.is_active = True
                else:
                    crit.is_active = False
            self.cur_stage = 1
            return self.cur_stage

        i_cr = self.chk_payoff(True)    # check, if all nadirs computed
        if i_cr > -1:  # nadir of i_cr-th criterion needs to be computed
            if i_cr < 5:
                raise Exception(f'chk_stage(): nadir computations NOT implemented yet.')
            self.cur_stage = 2
            return self.cur_stage

        print('PayOff table available. Ready to hanle preferences.')
        for crit in self.cr:
            crit.is_active = True
        self.cur_stage = 4
        return self.cur_stage
    # todo: either update crit.{uto,nad}_def or remove, if they not not really needed

    def store_sol(self, crit_val):
        print(f'Processing criteria values of the current iteration: {crit_val}')
        sys.stdout.flush()  # needed for printing exception at the output end
        raise Exception('Mcma::store_sol not implemented yet.')

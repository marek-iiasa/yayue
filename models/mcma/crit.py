# import sys      # needed from stdout
# import os
# import numpy as np


class CrPref:     # attributes of item of preference specs
    def __init__(self, parent, asp, res, act=True):
        self.parent = parent  # seq_no (in mc container) of parent crit
        self.asp = asp     # aspiration value (not scaled)
        self.res = res     # reservation value (not scaled)
        self.is_active = act    # activity


class Crit:     # definition and attributes of a single criterion
    # see: ~/src/mcma/mc_defs.h for the corresponding C++ classes
    """Attributes of particular criterion."""
    def __init__(self, cr_name, var_name, typ):
        # Specified at criterion declaration: crit. name, core-model var., min or max.
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
        self.sc_ach = 100.   # U/N scale of achievements [0, sc_ach]
        self.minRange = 0.01  # min U/N range
        # the below values shall be defined/updated when available
        self.sc_var = -1.   # scaling of the var value (for defining the corresponding CAF); negative means undefined
        self.is_active = None
        self.utopia = None  # set only once
        self.nadir = None   # checked, and possibly updated, every iteration, see self.updNadir()
        self.asp = None     # aspiration value (not scaled)
        self.res = None     # reservation value (not scaled)
        self.val = None     # current computed value (from last solution)
        self.a_val = None   # achievement of the current value
        #
        print(f"criterion '{cr_name}' ({self.attr}), core-model variable = '{var_name}'.")

    def val2ach(self, val):   # set a_val corresponding to the current val
        if self.nadir is None:  # don't attempt to compute achievements in initial stages
            self.a_val = 0.
            return self.a_val
        rng = abs(self.utopia - self.nadir)
        assert rng / max(abs(self.utopia), abs(self.nadir)) > self.minRange, f'val2ach(): crit {self.name} has '\
            f'too small difference between U {self.utopia} and N {self.nadir}.'
        a_val = self.sc_ach * abs(val - self.nadir) / rng
        a_val = round(a_val, 2)
        # print(f'val2ach(): crit "{self.name}": {val=:.2e}, {a_val=:.2f}, U {self.utopia:.2e}, N {self.nadir:.2e}')
        return a_val

    def ach2val(self, achiv):   # return criterion value corresponding to CAF = achiv
        rng = abs(self.utopia - self.nadir)
        rng_fr = rng * achiv / self.sc_ach
        val = self.nadir + self.mult * rng_fr
        # print(f'ach2val(): crit "{self.name}": {achiv=:.2f}, {val=:.2e}, U {self.utopia:.2e}, N {self.nadir:.2e}')
        return val

    def setUtopia(self, val):   # to be called only once for each criterion
        assert self.utopia is None, f'utopia of crit {self.name} already set.'
        self.utopia = val
        print(f'utopia of crit "{self.name}" set to {val}.')

    def updNadir(self, stage, val, minDiff):
        """Update nadir value, if val is a better approximation."""
        if self.nadir is None or stage == 0:    # set initial value
            self.nadir = val
            print(f'nadir of crit "{self.name}" set to {val} ({stage = }).')
            return
        shift = False
        eps = 1.e-6     # margin to avoid setting to the same value
        old_val = self.nadir

        # stage 2: first appr. of nadir, regularized selfish opt. for each crit. in a row
        # tigthen (move closer to U) "too bad" value from selfish opt. in stage 1
        if stage == 2:
            delta = 2. * minDiff * max(abs(self.utopia), abs(val))
            if abs(self.utopia - val) < delta:
                v = val     # v only for the below printout
                val = self.utopia - self.mult * delta
                print(f'updNadir(): crit "{self.name}", value {v:.2e} closer to utopia {self.utopia:.2e} '
                      f'than {delta:.2e}; nadir can be moved only to {val:.4e}.')
            if self.mult == 1:  # max-crit, tight to larger values
                if old_val + eps < val:
                    shift = True    # move closer to U
            else:       # min-crit, tight to smaller values
                if old_val - eps > val:
                    shift = True     # move closer to U
        # in stages: 1, 3, and RFP: relax (move away from U) "too tight" values (from previous appr.)
        # in stage 1 (selfish opt.): just collect worst values of each criterion
        # in stage 3: 2nd stage on nadir appr.: apply AF with only one criterion active
        # in stages >= 4: RFP, AF defined by preferences (A, R, activity) set for each criterion
        else:
            if self.mult == 1:  # max-crit, relax to smaller values
                if old_val - eps > val:
                    shift = True     # move away from U
            else:       # min-crit, relax to the larger val
                if old_val + eps < val:
                    shift = True     # move away from U

        if shift:
            # todo: add check to prevent moving (back?) to utopia
            self.nadir = val    # set val as new nadir appr.
            no_yes = ''
        else:
            no_yes = 'not'

        if shift:
            print(f'\tnadir appr. of crit "{self.name}": {old_val:.2e} {no_yes} changed to {val:.2e} (in {stage=}).')
        return shift

    def isBetter(self, val1, val2):   # return true if val1 is better or equal to than val2
        if val1 is None or val2 is None:  # PWL takes care about undefined values
            return True
        if self.mult == 1:  # max criterion
            if val1 >= val2:
                return True
        else:  # min criterion
            if val1 <= val2:
                return True
        return False

    def chkAR(self, pref_item, n_line):   # check correctnes of A and R values
        asp = pref_item.asp
        res = pref_item.res
        # print(f'chkAR(): crit "{self.name}" ({self.attr}), U {self.utopia}, {asp = }, {res = }, N {self.nadir}')
        is_ok = True
        if not self.isBetter(self.utopia, asp):
            # print(f'chkAR(): crit "{self.name}" ({self.attr}): specified A {asp} is better than U {self.utopia}')
            is_ok = False
        if not self.isBetter(asp, res):
            # print(f'chkAR(): crit "{self.name}" ({self.attr}): specified R {res} is better than A {asp}')
            is_ok = False
        if not self.isBetter(res, self.nadir):
            # print(f'chkAR(): crit "{self.name}" ({self.attr}): specified R {res} is worse than N {self.nadir}.')
            is_ok = False
        if not is_ok:
            raise Exception(f'chkAR(): preferences A = {asp}, R = {res} specified in line {n_line} for '
                            f'criterion "{self.name}" are inconsistent.')
        return

    def setAR(self):   # set AR for neutral solution
        self.is_active = True   # make sure the criterion is active
        is_max = self.mult == 1  # 1 for max-crit, -1 for min.
        delta = abs(self.utopia - self.nadir) / 3.  # equal distance between U, A, R, N
        self.asp = self.utopia - self.mult * delta
        self.res = self.asp - self.mult * delta
        print(f"Preferences for neutral solution: cr_name = '{self.name}', {is_max = }, U = {self.utopia}, "
              f"A = {self.asp}, R = {self.res}, N = {self.nadir}.")

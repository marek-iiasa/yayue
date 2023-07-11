"""
attributes structure for handling of the MCMA
"""
# import sys      # needed from stdout
# import os
# import numpy as np


class Crit:     # definition and attributes of a single criterion
    # see: ~/src/mcma/mc_defs.h for the corresponding C++ classes
    """
    Attributes of indivual criterion.
    """
    def __init__(self, cr_name, var_name, typ):
        """
        Specified at criterion declaration: crit. name, core-model var., min or max.
        """
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
        # the below values shall be defined/updated when available
        self.sc_var = -1.   # scaling of the var value (for defining the corresponding CAF); negative means undefined
        self.is_active = True
        self.utopia = None  # set only once
        self.nadir = None   # checked, and possibly updated, every iteration, see self.updNadir()
        self.asp = None     # aspiration value (not scaled)
        self.res = None     # reservation value (not scaled)
        self.val = None     # last computed value
        #
        print(f"Criterion: name = '{cr_name}', var_name = '{var_name}', {self.attr} created.")

        # not needed
        # self.uto_def = False     # utopia defined?
        # self.nad_def = False     # nadir defined?

    def setUtopia(self, val):
        assert self.utopia is None, f'utopia of crit {self.name} already set.'
        self.utopia = val
        print(f'utopia of crit "{self.name}" set to {val}.')

    def updNadir(self, stage, val):
        """Update nadir value, if val is a better approximation."""
        if self.nadir is None or stage == 0:
            self.nadir = val
            print(f'nadir of crit "{self.name}" set to {val} ({stage = }).')
            return
        eps = 1.e-6     # margin used for shifting val to avoid comparing "the same" values
        old_val = self.nadir
        shift = False
        if stage == 2:  # first appr. of nadir: tigthen "too bad" (garbage) value from utopia-calculation stage
            if self.mult == 1:  # max-crit, tight to larger values
                if old_val + eps < val:
                    shift = True
            else:       # min-crit, tight to smaller values
                if old_val - eps > val:
                    shift = True
        else:  # stage 1 and stages > 2: relax "too tight" previously set (from other utopia or stage 2) value
            if self.mult == 1:  # max-crit, relax to smaller values
                if old_val - eps > val:
                    shift = True
            else:       # min-crit, relax to larger values
                if old_val + eps < val:
                    shift = True

        if shift:
            self.nadir = val
            yes_no = ''
        else:
            yes_no = 'not'
        print(f'nadir appr. of crit "{self.name}": {old_val} {yes_no} changed to {val} (in {stage=}).')


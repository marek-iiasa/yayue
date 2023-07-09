"""
Data structure and handling of the MCMA
"""
# import sys      # needed from stdout
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
        self.val = None     # last computed value
        self.is_active = True
        print(f"Criterion initialized: crit_name = '{cr_name}', var_name = '{var_name}', {self.attr}.")
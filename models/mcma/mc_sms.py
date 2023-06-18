"""
Returns the Symbolic model specification (SMS), i.e., the Abstract Model of the MCMA Achievement Function
"""

import pyomo.environ as pe       # more robust than using import *
# from pyomo.environ import *     # used in pyomo book and many tutotials, causes problems
# from sympy import subsets  # explore this to avoid warnings


# noinspection PyUnresolvedReferences
def mk_sms():
    m = pe.AbstractModel(name='Achievement 1.0')

    print('mc_sms(): finished')
    return m

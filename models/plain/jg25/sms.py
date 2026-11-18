# Simple Pyomo model to demonstrate export of concrete model in the dill-format

import sys		# needed for stdout and sys.exit()
from os import R_OK, access
from os.path import isfile
import dill
import pyomo.environ as pe
from pyomo.opt import SolverStatus
from pyomo.opt import TerminationCondition


# Symbolic model specification
def mk_sms():
    m = pe.AbstractModel(name='example 1.0')
    # Parameters
    m.r = pe.Param()
    # Variables
    m.x1 = pe.Var(domain=pe.NonNegativeReals)    # number of work hours
    m.x2 = pe.Var(domain=pe.NonNegativeReals)    # number of leasure hours
    m.x3 = pe.Var(domain=pe.NonNegativeReals)


    # Objective
    @m.Objective(sense=pe.maximize)
    def goalmax(mx):
        return mx.x1
    # Constraints

    @m.Constraint()
    def con1(mx):
        return mx.x1 + mx.x2 + mx.x3 <= mx.r



    return m    # return concrete model


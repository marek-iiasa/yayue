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
    m.s_w = pe.Param()
    m.s_l = pe.Param()
    m.perhour = pe.Param()
    m.work = pe.Param()
    m.leisure = pe.Param()
    m.h_income = pe.Param()
    # Variables
    m.nwork = pe.Var(domain=pe.NonNegativeReals)    # number of work hours
    m.nleisure = pe.Var(domain=pe.NonNegativeReals)    # number of leasure hours
    m.satisf = pe.Var(domain=pe.Reals)
    m.income = pe.Var(domain=pe.Reals)

    # Objective
    @m.Objective(sense=pe.maximize)
    def goalmax(mx):
        return mx.s_w * mx.nwork + mx.s_l * mx.nleisure
    # Constraints

    @m.Constraint()
    def con1(mx):
        return mx.nwork + mx.nleisure <= mx.perhour

    @m.Constraint()
    def con2(mx):
        return mx.nwork >= mx.work

    @m.Constraint()
    def con3(mx):
        return mx.nleisure <= mx.leisure

    @m.Constraint()
    def con4(mx):
        return mx.s_w * mx.nwork + mx.s_l * mx.nleisure == mx.satisf

    @m.Constraint()
    def con5(mx):
        return mx.h_income * mx.nwork == mx.income

    return m    # return concrete model


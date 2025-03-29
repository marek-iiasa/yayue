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
    m = pe.AbstractModel(name='iserman 1.0')
    # Sets
    m.I = pe.Set(domain=pe.PositiveIntegers)
    m.J = pe.Set(domain=pe.PositiveIntegers)
    m.Q = pe.Set(domain=pe.PositiveIntegers)
    # Params
    m.A = pe.Param(m.I, m.J)
    m.C = pe.Param(m.I, m.Q)
    m.b = pe.Param( m.J )
    # Variables
    m.x = pe.Var(m.I,domain=pe.NonNegativeReals)
    m.q = pe.Var(m.Q, domain=pe.Reals)  # criteria
    m.q1 = pe.Var(domain=pe.Reals)  # criterion q1
    m.q2 = pe.Var(domain=pe.Reals)  # criterion q2
    m.q3 = pe.Var(domain=pe.Reals)  # criterion q3
    m.q4 = pe.Var(domain=pe.Reals)  # criterion q4

    # Objective constrainta
    @m.Constraint(m.Q)
    def const0(mx, k):
        return mx.q[k] == sum(mx.C[i,k]*mx.x[i] for i in mx.I )
    # Constraints

    @m.Constraint(m.J)
    def con1(mx, j):
        return sum(mx.A[i,j]*mx.x[i]  for i in mx.I)    <= mx.b[j]

    @m.Constraint()
    def conq1(mx):
        return mx.q1 == mx.q[1]

    @m.Constraint()
    def conq2(mx):
        return mx.q2 == mx.q[2]

    @m.Constraint()
    def conq3(mx):
        return mx.q3 == mx.q[3]

    @m.Constraint()
    def conq4(mx):
        return mx.q4 == mx.q[4]

    # Objective
    @m.Objective(sense=pe.maximize)
    def goalmax(mx):
        # return sum(mx.q[i] for i in mx.I)
        return mx.q[1]

    return m    # return concrete model


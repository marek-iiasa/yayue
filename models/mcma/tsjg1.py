import pyomo.environ as pe       # more robust than using import *


# noinspection PyUnresolvedReferences
def jg1():
    """The sand-box very simple model"""
    m = pe.ConcreteModel(name='Sand-box JG 1.0')

    # variables
    m.x1 = pe.Var(domain=pe.NonNegativeReals, doc='x1')
    m.x2 = pe.Var(domain=pe.NonNegativeReals, doc='x2')
    m.x3 = pe.Var(domain=pe.NonNegativeReals, doc='x3')

    # relation (constraint)
    @m.Constraint()
    def c1(mx):
        return 0, mx.x1 + mx.x2 + mx.x3, 100.

    m.pprint()
    print(f'jg1(): concrete model {m.name} generated.')
    return m

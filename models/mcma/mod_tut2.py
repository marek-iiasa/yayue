
import pyomo.environ as pe       # more robust than using import *


# noinspection PyUnresolvedReferences
def mod_tut2():
    """The sand-box Pipa-like ConcreteModel for testing mcma"""
    m = pe.ConcreteModel(name='Model tutorial JG2 0.1')

    m.T = pe.Set(initialize=[1, 2, 3])
    # variables
    m.act = pe.Var(m.T, domain=pe.NonNegativeReals, doc='variables')


    # outcome variables
    m.q1 = pe.Var(domain=pe.NonNegativeReals, doc='Criterion 1')
    m.q2 = pe.Var(domain=pe.NonNegativeReals, doc='Criterion 2')
    m.q3 = pe.Var(domain=pe.NonNegativeReals, doc='Criterion 3')


    # objective
    @m.Objective(sense=pe.maximize)
    def goal(mx):
        return mx.q1
    """
    @m.Objective(sense=pe.minimize)
    def goal2(mx):
        return mx.income
    m.goal2.deactivate()
    """
    # parameters  (declared in the sequence corresponding to their use in SMS)
    m.s = pe.Param(domain=pe.NonNegativeReals, default=10., doc='sum')



    # relations (constraints)
    @m.Constraint()
    def constr(mx):
        return mx.q1+ mx.q2 + mx.q3 <= mx.s


    # m.pprint()
    print(f"mod_tut2(): concrete model {m.name} generated.")

    return m
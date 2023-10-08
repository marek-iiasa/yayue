
import pyomo.environ as pe       # more robust than using import *


# noinspection PyUnresolvedReferences
def mod_jg1():
    """The sand-box Pipa-like ConcreteModel for testing mcma"""
    m = pe.ConcreteModel(name='Model testowy JG1 0.1')

    # W - working hours
    # L - leisure hours
    m.T = pe.Set(initialize=['W', 'L'])

    # variables
    m.act = pe.Var(m.T, domain=pe.NonNegativeReals, doc='level of activity')
    # m.z = pe.Var(domain=pe.NonNegativeReals, bounds=(0, 100), doc='level of z activity')

    # outcome variables
    m.satisfaction = pe.Var(domain=pe.NonNegativeReals, doc='satisfaction level')
    m.income = pe.Var(domain=pe.NonNegativeReals, doc='income in $')

    # objective
    @m.Objective(sense=pe.maximize)
    def goal(mx):
        return mx.satisfaction

    @m.Objective(sense=pe.minimize)
    def goal2(mx):
        return mx.income
    m.goal2.deactivate()

    # parameters  (declared in the sequence corresponding to their use in SMS)
    m.h = pe.Param(domain=pe.NonNegativeReals, default=10., doc='income per hour')
    m.sp = pe.Param(domain=pe.NonNegativeReals, default=1., doc='satisfaction for work')
    m.sl = pe.Param(domain=pe.NonNegativeReals, default=5., doc='satisfaction for leisure')


    # relations (constraints)
    @m.Constraint()
    def satisfaction(mx):
        return mx.satisfaction == mx.sp * mx.act[1] + mx.sl * mx.act[2]

    @m.Constraint()
    def income(mx):
        return mx.satisfaction == mx.sp * mx.act[1]

    @m.Constraint()
    def con1(mx):
        return mx.act[1] + mx.act[2] <= 14

    @m.Constraint()
    def con2(mx):
        return mx.act[1] >= 5

    @m.Constraint()
    def con3(mx):
        return mx.act[2] <= 8

    # m.pprint()
    print(f"mod_jg1(): concrete model {m.name} generated.")
    return m

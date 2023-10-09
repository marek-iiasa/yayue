
import pyomo.environ as pe       # more robust than using import *


# noinspection PyUnresolvedReferences
def mod_jg1():
    """The sand-box Pipa-like ConcreteModel for testing mcma"""
    m = pe.ConcreteModel(name='Model testowy JG1 0.1')

    # W - working hours
    # L - leisure hours
    m.T = pe.Set(initialize=['W', 'L'])
    # variables
    m.act = pe.Var(m.T, domain=pe.NonNegativeReals, doc='variables')


    # outcome variables
    m.satisfaction = pe.Var(domain=pe.NonNegativeReals, doc='satisfaction level')
    m.income = pe.Var(domain=pe.NonNegativeReals, doc='income in $')

    # objective
    @m.Objective(sense=pe.maximize)
    def goal(mx):
        return mx.satisfaction
    """
    @m.Objective(sense=pe.minimize)
    def goal2(mx):
        return mx.income
    m.goal2.deactivate()
    """
    # parameters  (declared in the sequence corresponding to their use in SMS)
    m.h = pe.Param(domain=pe.NonNegativeReals, default=10., doc='income per hour')
    m.sw = pe.Param(domain=pe.NonNegativeReals, default=1., doc='satisfaction for work')
    m.sl = pe.Param(domain=pe.NonNegativeReals, default=5., doc='satisfaction for leisure')


    # relations (constraints)
    @m.Constraint()
    def satisf(mx):
        return mx.satisfaction == mx.sw.value * mx.act['W'].value + mx.sl.value * mx.act['L'].value
        # return mx.satisfaction == mx.sw * mx.W + mx.sl * mx.L

    @m.Constraint()
    def inc(mx):
        return mx.satisfaction == mx.sw * mx.act['W']
        # return mx.income == mx.h * mx.W

    @m.Constraint()
    def con1(mx):
        return mx.act['P'] + mx.act['W'] <= 14
        # return mx.W + mx.L <= 14

    @m.Constraint()
    def con2(mx):
        return mx.act['P'] >= 5
        # return mx.W >= 5

    @m.Constraint()
    def con3(mx):
        return mx.act['P'] <= 5
        # return mx.L <= 8

    # m.pprint()
    print(f"mod_jg1(): concrete model {m.name} generated.")

    # call solver
    opt = pe.SolverFactory('glpk')
    opt.solve(m)
    # display results
    m.display()
    print('-------------------------')
    print('work=', m.W.value)
    print('leisure=', m.L.value)
    print('satisfaction=', m.satisfaction.value)
    print('income=', m.income.value)
    print('obj=', m.goal.expr.value)
    print('-------------------------')

    return m

model = mod_jg1()
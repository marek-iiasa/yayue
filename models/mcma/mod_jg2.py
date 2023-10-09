
import pyomo.environ as pe       # more robust than using import *


# noinspection PyUnresolvedReferences
def mod_jg2():
    """The sand-box Pipa-like ConcreteModel for testing mcma"""
    m = pe.ConcreteModel(name='Model testowy JG1 0.2')

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
        return mx.satisfaction == mx.sw * mx.act['W'] + mx.sl * mx.act['L']
        # return mx.satisfaction == mx.sw * mx.W + mx.sl * mx.L

    @m.Constraint()
    def inc(mx):
        return mx.income == mx.h * mx.act['W']
        # return mx.income == mx.h * mx.W

    @m.Constraint()
    def con1(mx):
        return mx.act['W'] + mx.act['L'] <= 14
        # return mx.W + mx.L <= 14

    @m.Constraint()
    def con2(mx):
        return mx.act['W'] >= 5
        # return mx.W >= 5

    @m.Constraint()
    def con3(mx):
        return mx.act['L'] <= 8
        # return mx.L <= 8

    # m.pprint()
    print(f"mod_jg1(): concrete model {m.name} generated.")

    # call solver
    opt = pe.SolverFactory('glpk')
    opt.solve(m)


    return m

model = mod_jg2()

# display results
model.display()
print('-------------------------')
print('work=',pe.value(model.act['W']))
print('leisure=',pe.value(model.act['L']))
print('satisfaction=', model.satisfaction.value)
print('income=', model.income.value)
print('obj=', model.goal.expr.value)
print('-------------------------')
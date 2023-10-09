
import pyomo.environ as pyo

# noinspection PyUnresolvedReferences
def mod_jg0():


    model = pyo.ConcreteModel()

    model.T = pyo.Set(initialize=['W', 'L'])
    #model.T = pyo.Set(initialize=[1, 2])

    model.h = pyo.Param(domain=pyo.NonNegativeReals, default=2., doc='income per hour')

    model.x = pyo.Var(model.T, domain=pyo.NonNegativeReals)

    model.OBJ = pyo.Objective(expr=model.h * model.x['W'] + 3 * model.x['L'])

    model.Constraint1 = pyo.Constraint(expr=3 * model.x['W'] + 4 * model.x['L'] >= 1)

    # call solver
    opt = pyo.SolverFactory('glpk')
    opt.solve(model)

    return model


model = mod_jg0()

print(pyo.value(model.x['W']))
print(pyo.value(model.x['L']))

import pyomo.environ as pyo

# noinspection PyUnresolvedReferences
def mod_jg0():


    model = pyo.ConcreteModel()

    # model.T = pyo.Set(initialize=['W', 'L'])
    model.T = pyo.Set(initialize=[1, 2])

    model.x = pyo.Var(model.T, domain=pyo.NonNegativeReals)

    model.OBJ = pyo.Objective(expr=2 * model.x[1] + 3 * model.x[2])

    model.Constraint1 = pyo.Constraint(expr=3 * model.x[1] + 4 * model.x[2] >= 1)

    # call solver
    opt = pyo.SolverFactory('glpk')
    opt.solve(model)

    return model


model = mod_jg0()

print(pyo.value(model.x[1]))
print(pyo.value(model.x[2]))
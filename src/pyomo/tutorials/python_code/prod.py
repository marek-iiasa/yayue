from pyomo.environ import *

model = AbstractModel()

# Se t s
model.P = Set()

# Parameters
model.a = Param(model.P)
model.b = Param()
model.c = Param(model.P)
model.u = Param(model.P)

# Variables
model.X = Var(model.P)

# Objective
def objective_rule(model):
    return summation(model.c, model.X)
model.Total_Profit = Objective(rule=objective_rule, \
                                sense=maximize )

# Time Constraint
def time_rule(model):
    return summation(model.X, denom=model.a ) <= model.b
model.Time = Constraint(rule=time_rule)

# Limit Constraint
def limit_rule(model, j):
    return (0, model.X[j], model.u[j])
model.Limit = Constraint(model.P, rule=limit_rule)


#to remove for command line
data = DataPortal()
data.load(filename='prod.dat')
instance = model.create_instance(data)

instance.pprint()

#call solver
opt = SolverFactory('glpk')
opt.solve(instance)
#display results
instance.display()





"""
Note: This is not the final version of the code, and therefore, it may not work correctly or may contain bugs.
The sole purpose of this code is communication between team members.
This warning will be removed when the entire project is finished.
"""

import pyomo.environ as pyo


def objective(model):
    return sum(model.z[l, k, t] * model.g_k[k] for l in model.L for k in model.K for t in model.T)

# Each customer cannot be picked up more than once.
def pickup_constraint_rule(model, k):
    return sum(model.y[l, k, t] for l in model.L for t in model.T) <= 1

# Each customer cannot be dropped off more than once.
def dropoff_constraint_rule(model, k):
    return sum(model.z[l, k, t] for l in model.L for t in model.T) <= 1

# Each vehicle can move only once per each timestep
def one_move_at_time_rule(model, l, t):
    return sum(model.x[l, i, j, t] for i in model.I for j in model.J) <= 1

# Each vehicle cannot travel more than max time
def travel_distance_constraint_rule(model, l):
    return sum(model.x[l, i, j, t] * model.c[i, j] for i in model.I for j in model.J for t in model.T) <= model.max_t

# This rule guarantee that if vehicle moved to node j in previous timestep, it may continue its movement only from node j
def continuity_constraint_rule(model, l, i, j, t):
    if t == 0:
        return pyo.Constraint.Skip
    return model.x[l, i, j, t - 1] * sum(model.x[l, n, m, t] for n in model.I if n != j for m in model.J) == 0

# This rule guarantee that vehicle wont start moving again after it stops its movement
def continuity_constraint_rule2(model, l, t):
    if t == 0:
        return pyo.Constraint.Skip
    return sum(model.x[l, n, m, t - 1] for n in model.I for m in model.J) >= sum(
        model.x[l, k, r, t] for k in model.I for r in model.J)

# Each customer may be picked up only if the vehicle travels from the same node as customer's current location
def picking_up_rule(model, l, k, t, i, j):
    if i == model.s_k[k]:
        return model.x[l, i, j, t] >= model.y[l, k, t]
    else:
        return pyo.Constraint.Skip

# Each customer may be dropped off only if the vehicle travels to the same node as customer's destination
def dropping_off_rule(model, l, k, t, i, j):
    if j == model.d_k[k]:
        return model.x[l, i, j, t] >= model.z[l, k, t]
    else:
        return pyo.Constraint.Skip

# Each customer may be dropped off only if they were picked up previously
def dropping_off_rule2(model, l, k, t):
    return sum(model.y[l, k, t - dt] for dt in range(0, t + 1)) >= model.z[l, k, t]

# Number of available seats is dependent on previous choices
def capacity_continuity_rule(model, l, t):
    return model.v[l, t] == model.initial_capacity + sum(model.z[l, k, t - dt] for k in model.K for dt in range(0, t + 1))\
           - sum(model.y[l, k, t - dt] for k in model.K for dt in range(0, t + 1))


def sms():
    model = pyo.AbstractModel(name='carpooling')

    # indexes
    model.I = pyo.Set()  # set for place
    model.J = pyo.Set()  # set for every place
    model.K = pyo.Set()  # set for every client
    model.L = pyo.Set()  # set for every vehicle
    model.T = pyo.Set()  # set for every timestep

    # parameters
    model.initial_capacity = pyo.Param(domain=pyo.NonNegativeIntegers)  # max capacity of each vehicle
    model.max_t = pyo.Param(domain=pyo.NonNegativeIntegers)  # max time of which vehicles can work
    model.c = pyo.Param(model.I, model.J, domain=pyo.NonNegativeIntegers)  # matrix of times needed to travel between places
    model.s_k = pyo.Param(model.K, domain=pyo.NonNegativeIntegers)  # vector of start nodes for each customer
    model.d_k = pyo.Param(model.K, domain=pyo.NonNegativeIntegers)  # vector of destination nodes for each customer
    model.g_k = pyo.Param(model.K, domain=pyo.NonNegativeIntegers)  # vector of gain from each customer

    # decision variables
    model.x = pyo.Var(model.L, model.I, model.J, model.T, domain=pyo.Binary,
                      initialize=0)  # if vehicle l travels from node i to node j at timestep t
    model.y = pyo.Var(model.L, model.K, model.T, domain=pyo.Binary,
                      initialize=0)  # if vehicle l picks up customer k at timestep t
    model.z = pyo.Var(model.L, model.K, model.T, domain=pyo.Binary,
                      initialize=0)  # if vehicle l drops off customer k at timestep t

    # auxiliary variables
    model.v = pyo.Var(model.L, model.T, domain=pyo.NonNegativeIntegers, initialize=model.initial_capacity,
                      bounds=(0, model.initial_capacity))  # number of available seats for vehicle l in timestep t

    model.objective = pyo.Objective(rule=objective, sense=pyo.maximize)
    model.pickup_constraint = pyo.Constraint(model.K, rule=pickup_constraint_rule)
    model.dropoff_constraint = pyo.Constraint(model.K, rule=dropoff_constraint_rule)
    model.one_move_at_time = pyo.Constraint(model.L, model.T, rule=one_move_at_time_rule)
    model.travel_distance_constraint = pyo.Constraint(model.L, rule=travel_distance_constraint_rule)
    model.continuity_constraint = pyo.Constraint(model.L, model.I, model.J, model.T, rule=continuity_constraint_rule)
    model.continuity_constraint2 = pyo.Constraint(model.L, model.T, rule=continuity_constraint_rule2)
    model.picking_up = pyo.Constraint(model.L, model.K, model.T, model.I, model.J, rule=picking_up_rule)
    model.dropping_off = pyo.Constraint(model.L, model.K, model.T, model.I, model.J, rule=dropping_off_rule)
    model.dropping_off2 = pyo.Constraint(model.L, model.K, model.T, rule=dropping_off_rule2)
    model.capacity_continuity = pyo.Constraint(model.L, model.T, rule=capacity_continuity_rule)

    return model


def instance(model):
    data = pyo.DataPortal()
    data.load(filename='data.dat')
    instance = model.create_instance(data)
    return instance


if __name__ == '__main__':
    abst = sms()
    model_instance = instance(abst)

    solver = pyo.SolverFactory('cplex')
    results = solver.solve(model_instance, tee=True)

    model_instance.display()

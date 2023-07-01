from __future__ import division
from pyomo.environ import *
import numpy as np
import random
import time
from matplotlib import pyplot as plt

start = time.time()

#   define model
m = ConcreteModel()

#   define index
n = 10 # number of discrete time index
T = range(1, n+1) # range of discrete time index,number of states

random.seed(1)
m.production_capacity_factor = Param(T, within=NonNegativeReals, rule=lambda m,t: np.random.uniform(0, 0.8))


#   define exogenous variables
#   1) energy inflow (power generation)

#   define parameters
m.production_capacity = Param(default=100)  # capacity of production
m.production_number = Param(default=1)   # number of production devices
m.inflow = Param(T, within=NonNegativeReals, rule=
                 lambda m,t: m.production_capacity * m.production_number * m.production_capacity_factor[t])
                # energy inflow (renewable energy generation)
    #   define average inflow as the initial value of decision commitment
mapped_inflow = [m.inflow[t] for t in T]
avg_inflow = np.mean(np.array(mapped_inflow))
m.effin = Param(default=0.9) # efficient, convert inflow electricity to potential energy in the storage
m.effout = Param(default=1) # efficient, convert potential energy in the storage to electricit
m.effself = Param(default=1.0) # efficient, remove self loss
m.fprice = Param(default=1) # contract price for long term electricity supply
m.pf = Param(default=1.5) # factor used to show penalty level,2 means penalty is two times of price
m.pprice = Param(within=NonNegativeReals, rule=lambda m: m.pf * m.fprice)
#m.xmax = Param(rule=2 * max(mapped_inflow))
m.rmax = Param(rule=2 * max(mapped_inflow),mutable=True) # max number of storage capacity, MWh
m.rinitial = Param(default=0) # initial value of storage
m.rpower = Param(default=50) # max energy flow to/out of the storage
m.hdis = Param(default=1.05**(-1/n)) # 5% per year
m.inveffin = Param(rule=lambda m: 1.0 / m.effin) # inverse of efficient effin, used to calculate the amount of energy that will be stored (origin)
m.inveffout = Param(rule=lambda m: 1.0 / m.effin) # inverse of efficient m.effout,W used to calculate the amount of potential energy out of storage
m.uinv = Param(default=100)
b=0
#   print parameters
m.production_capacity_factor.display()
m.inflow.display()
print('fixed price =', value(m.fprice))
print('penalty price =', value(m.pprice))
print('storage efficiency in =', value(m.effin))
print('storage efficiency out =', value(m.effout))
print('self loss efficiency =', value(m.effself))
print('avg_inflow =', avg_inflow)
print('rmax =', value(m.rmax))


#   define rules


def inflow_balance_rule(m, t): # energy balance, inflow point
    return m.dout[t] + m.ins[t] + m.curtail[t] == m.inflow[t]


def outflow_balance_rule(m, t):  # energy balance, outflow point, outflow[t] = x[t]
    return  m.dout[t] + m.outs[t] + m.buy[t] == m.outflow[t]

def dout_rule(m, t): # energy directly used to meet the commitment
    if m.x[t].value >= m.inflow[t]:
        m.dout[t] = m.inflow[t]
    else:
        m.dout[t] = m.x[t]
    return m.dout[t]

def curtail_rule(m, t): # energy directly used to meet the commitment
    if m.x[t].value >= m.inflow[t]:
        m.curtail[t] = 0
    else:
        m.curtail[t] =m.inflow[t] - m.dout[t] - m.ins[t]
    return m.curtail[t]

def dif_rule(m, t): # energy difference between inflow and commitment
    m.dif[t] = abs(m.x[t] - m.inflow[t])
    return m.dif[t]

def outflow_rule(m, t): # energy outflow
    m.outflow[t] = m.dout[t] + m.outs[t] + m.buy[t]
    return m.outflow[t]

def ins_rule(m, t):
    m.ins[t] = 0
    if t == T[0]:
        if m.x[t].value >= m.inflow[t]:
            m.ins[t] = 0
        elif m.x[t].value < m.inflow[t] and (m.effin * m.dif[t].value + m.rinitial) <= m.rmax.value:
            m.ins[t] = m.dif[t]
        elif m.x[t].value < m.inflow[t] and (m.effin * m.dif[t].value + m.rinitial) > m.rmax.value:
            m.ins[t] = m.rmax - m.rinitial
            m.curtail[t] = m.inflow[t] - m.ins[t].value
    else:
        if m.x[t].value >= m.inflow[t]:
            m.ins[t] = 0
        elif m.x[t].value < m.inflow[t] and (m.effin * m.dif[t].value + m.r[t-1].value) <= m.rmax.value:
            m.ins[t] = m.dif[t]
        elif m.x[t].value < m.inflow[t] and (m.effin * m.dif[t].value + m.r[t-1].value) > m.rmax.value:
            m.ins[t] = m.rmax - m.r[t-1]
    return m.ins[t]

def sin_rule(m, t):
    m.sin[t] = m.effin * m.ins[t]
    return m.sin[t]

def sout_rule(m, t):
    m.sout[t] = 0
    if t == T[0]:
        if m.x[t].value <= m.inflow[t]:
            m.sout[t] = 0
        elif m.x[t].value > m.inflow[t] and m.rinitial <= m.inveffout * m.dif[t].value:
            m.sout[t] = m.rinitial
        elif m.x[t].value > m.inflow[t] and m.rinitial > m.inveffout * m.dif[t].value:
            m.sout[t] = m.inveffout * m.dif[t].value
    else:
        if m.x[t].value <= m.inflow[t]:
            m.sout[t] = 0
        elif m.x[t].value > m.inflow[t] and m.r[t-1].value <= m.inveffout * m.dif[t].value:
            m.sout[t] = m.r[t-1]
        elif m.x[t].value > m.inflow[t] and m.r[t-1].value > m.inveffout * m.dif[t].value:
            m.sout[t] = m.inveffout * m.dif[t]
    return m.sout[t]

def outs_rule(m, t):
    m.outs[t] = m.effout * m.sout[t]
    return m.outs[t]

def storage_transition_rule(m, t): # storage state
    if t == T[0] and m.rinitial <= m.rmax.value:
        m.r[t] = m.rinitial
    else:
        if m.effself * m.r[t-1].value + m.sin[t].value - m.sout[t].value <= m.rmax.value:
            m.r[t] = m.effself * m.r[t-1].value + m.sin[t].value - m.sout[t].value
        else:
            m.r[t] = m.rmax
    return  m.r[t]


def buy_rule(m, t):
    m.buy[t] = 0
    if m.x[t].value > m.inflow[t] + m.outs[t].value:
        m.buy[t] = m.x[t].value - m.dout[t] - m.outs[t].value
    else:
        m.buy[t] = 0
    return m.buy[t]

def income_rule(m, t):
    m.income[t] = m.fprice * m.outflow[t]
    return m.income[t]

def penal_rule(m, t):
    m.penal[t] = m.pprice * m.buy[t]
    return m.penal[t]

def inv_rule(m):
    m.inv = m.rmax * m.uinv
    return m.inv

def profit_rule(m, t):
    m.profit[t] = m.income[t]- m.penal[t]
    return m.profit[t]

'''
def x_transition_rule(m, t):
    x_initial <= 1.5 * avg_inflow
    x_initial >= 0.25 * avg_inflow
    if t == T[0]:
        m.x[t] = x_initial
        return Constraint.Skip
    else:
        m.x[t] = m.x[t-1]
        return m.x[t] == m.x[t-1]
'''



#   define variables
    #   decision variables
    #   x: value of expected stable demand
    #   define the initial value of x[1] = avg_inflow and in each stage i, x[i] = average(x[1] : x[i])

m.x = Var(T, within=NonNegativeReals, bounds=(0, 1.5 * max(mapped_inflow)), initialize=b) # initialize=lambda m, i: (sum(m.x[i] for i in range(1, i)) / (i-1)) if i > 1 else avg_inflow)
m.dout = Var(T, within=NonNegativeReals)
m.curtail = Var(T, within=NonNegativeReals)
m.dif = Var(T, within=NonNegativeReals) # the difference between inflow and demand
m.outflow = Var(T, within=NonNegativeReals)
m.r = Var(T, within=NonNegativeReals, bounds=(0, m.rmax), initialize=0)
m.ins = Var(T, within=NonNegativeReals, bounds=(0, m.rpower)) # energy flow into storage
m.outs = Var(T, within=NonNegativeReals) # energy flow out of storage
m.sin = Var(T, within=NonNegativeReals) # energy will be stored in storage
m.sout = Var(T, within=NonNegativeReals, bounds=(0, m.rpower)) # energy drawn from storage
m.buy = Var(T, within=NonNegativeReals)
m.income = Var(T, within=NonNegativeReals)
m.penal = Var(T, within=NonNegativeReals)
m.profit = Var(T, within=Reals)
m.inv = Var(within=Reals)

#   define objective
m.obj = Objective(expr=sum(m.hdis**t * m.profit[t] for t in T ) - m.inv , sense=maximize)

#   define constraints
m.dout_rule = Expression(T, rule=dout_rule)
m.dif_rule = Expression(T, rule=dif_rule)
m.ins_rule = Expression(T, rule=ins_rule)
m.sin_rule = Expression(T, rule=sin_rule)
m.sout_rule = Expression(T, rule=sout_rule)
m.outs_rule = Expression(T, rule=outs_rule)
m.storage_transition = Expression(T, rule=storage_transition_rule)
m.curtail_rule = Expression(T, rule=curtail_rule)
m.buy_rule = Expression(T, rule=buy_rule)
m.outflow_rule = Expression(T, rule=outflow_rule)
m.income_rule = Expression(T, rule=income_rule)
m.penal_rule = Expression(T, rule=penal_rule)
m.inv_rule = Expression(T, rule=inv_rule)
m.profit_rule = Expression(T, rule=profit_rule)

m.inflow_balance = Constraint(T, rule=inflow_balance_rule)
m.outflow_balance = Constraint(T, rule=outflow_balance_rule)
# solve
solver = SolverFactory('glpk')
# solver.options.max_iter = 100
solver.options.mipgap = 1e-4

pre_obj_value = -1e-4
steps = 0.01
x_range = range(round(0.25 * avg_inflow), round(1.5 * avg_inflow))
r_range = range(round(avg_inflow), round(2 * avg_inflow))

for a in r_range:
    c = 0
    for b in x_range:
        for t in range(1, n):
            m.x[t] = b
            m.outflow[t] = m.x[t]
            m.x[t+1] = m.x[t]
        results = solver.solve(m)
        obj_value = value(m.obj)

        if obj_value - pre_obj_value <= 1e-6:
            best_profit = obj_value
            print('best profit =', value(m.obj))
            print('pre profit =', pre_obj_value)
            print('best commitment =', b)
            m.x.display()
            m.outflow.display()
            m.dif.display()
            m.ins.display()
            m.outs.display()
            m.r.display()
            m.buy.display()
            m.dout.display()
            m.penal.display()
            m.curtail.display()
            m.income.display()
            break
        else:
            b += steps
            pre_obj_value = obj_value
            c += 1
    m.rmax = a
    m.inv = m.rmax * m.uinv
    print("investment cost = ", m.inv.value, "rmax = ", m.rmax.value)
    print('best commitment =', b)
    a += 0.5 * avg_inflow



if results.solver.termination_condition == TerminationCondition.optimal:
    end = time.time()
    print('time =', end - start)
    print('well done')

else:
    end = time.time()
    print('time =', end - start)
    print("Solver did not converge to an optimal solution.")


'''
#   plot results
x = []
for t in T:
    x.append(t)

    # inflow
fig, axes = plt.subplots(2, 2)

axes[0, 0].plot(x, [value(m.inflow[t]) for t in T], '-o')
axes[0, 0].set_xlabel('Time')
axes[0, 0].set_ylabel('Inflow')

    # demand
axes[0, 1].plot(x, [value(m.x[t]) for t in T], '-o')
axes[0, 1].set_xlabel('Time')
axes[0, 1].set_ylabel('Commitment')

    # storage
axes[1, 0].plot(x, [value(m.r[t]) for t in T], '-o')
axes[1, 0].set_xlabel('Time')
axes[1, 0].set_ylabel('Storage')

    # profit
axes[1, 1].plot(x, [value(m.profit[t]) for t in T], '-o')
axes[1, 1].set_xlabel('Time')
axes[1, 1].set_ylabel('Profit')

plt.show()
'''

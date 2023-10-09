
import pyomo.environ as pe       # more robust than using import *
from mod_tut1 import mod_tut1 as mod_tut1  # sand-box tiny testing model, developed as concrete (without abstract)

model = mod_tut1()
# call solver
opt = pe.SolverFactory('glpk')
opt.solve(model)

# display results
model.display()
print('-------------------------')
print('work=',pe.value(model.act['W']))
print('leisure=',pe.value(model.act['L']))
print('satisfaction=', model.satisfaction.value)
print('income=', model.income.value)
print('obj=', model.goal.expr.value)
print('-------------------------')
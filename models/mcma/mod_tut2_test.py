
import pyomo.environ as pe       # more robust than using import *
from mod_tut1 import mod_tut1 as mod_tut1  # sand-box tiny testing model, developed as concrete (without abstract)

model = mod_tut2()
# call solver
opt = pe.SolverFactory('glpk')
opt.solve(model)

# display results
model.display()
print('-------------------------')
print('x1=',pe.value(model.act['1']))
print('x2=',pe.value(model.act['2']))
print('x3=',pe.value(model.act['3']))
print('q1=', model.q1.value)
print('q2=', model.q2.value)
print('q3=', model.q3.value)
print('obj=', model.goal.expr.value)
print('-------------------------')
#old
#from coopr.pyomo import *

from pyomo.environ import *
model = ConcreteModel()
# Variables
model.p = Var(within=NonNegativeReals)
model.w = Var(within=NonNegativeReals)
# Objective
model.obj = Objective(expr=model.p+5*model.w,sense=maximize)
# Constraints
model.con1 = Constraint(expr=model.p + model.w  <= 14)
model.con2 = Constraint(expr=model.p  >= 5)
model.con3 = Constraint(expr=model.w <= 8)
#call solver
opt = SolverFactory('glpk')
opt.solve(model)
#display results
model.display()
print('-------------------------')
print('p=', value(model.p))
print('w=', value(model.w))
print('obj=', value(model.obj))
print('-------------------------')

python_file = open("first1.res", "w")
python_file.writelines("%5s %5s %5s \n"%("p","w","obj"))
python_file.writelines("%5.2f %5.2f %5.2f\n"%(value(model.p),value(model.w),value(model.obj)))

python_file.close()


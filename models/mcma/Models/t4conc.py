
import pyomo.environ as pe       # more robust than using import *


# noinspection PyUnresolvedReferences
def mk_conc():
    """The tiny test model, developed as ConcreteModel."""
    m = pe.ConcreteModel(name='tiny test model 1.0')

    # variables
    m.x = pe.Var(domain=pe.NonNegativeReals, doc='level of x activity')
    m.y = pe.Var(domain=pe.NonNegativeReals, doc='level of y activity')
    # m.v = pe.Var(domain=pe.NonNegativeReals, doc='level of v activity')
    m.z = pe.Var(domain=pe.NonNegativeReals, bounds=(0, 100), doc='level of z activity')

    # outcome variables
    m.inc = pe.Var(doc='income')
    m.emi = pe.Var(doc='emission')

    # objective:
    # m.goal = pe.Objective(expr=m.inc, sense=pe.maximize)   # single objective used for testing
    m.goal = pe.Objective(expr=m.emi, sense=pe.minimize)   # single objective used for testing
    m.goal.activate()

    # parameters  (declared in the sequence corresponding to their use in SMS)
    m.lb1 = pe.Param(domain=pe.NonNegativeReals, default=10., doc='lo-bnd for total activity')
    m.ub1 = pe.Param(domain=pe.NonNegativeReals, default=100., doc='up-bnd for total activity')
    m.px = pe.Param(domain=pe.NonNegativeReals, default=10., doc='price of x')
    m.py = pe.Param(domain=pe.NonNegativeReals, default=0.5, doc='price of y')
    m.pz = pe.Param(domain=pe.NonNegativeReals, default=100, doc='price of z')
    m.ex = pe.Param(domain=pe.NonNegativeReals, default=20, doc='unit emission of x')
    m.ey = pe.Param(domain=pe.NonNegativeReals, default=0.5, doc='unit emission of y')
    m.ez = pe.Param(domain=pe.NonNegativeReals, default=100., doc='unit emission of z')

    # relations (constraints)
    # m.con1 = pe.Constraint(expr=(m.b2 <= m.x + m.y + m.z <= m.b1))  # range split into two because results in error
    m.con1 = pe.Constraint(expr=(m.x + m.y + m.z <= m.ub1), doc='up-bnd for production level')
    m.con2 = pe.Constraint(expr=(m.lb1 <= m.x + m.y + m.z), doc='lo-bnd for production level')
    m.incD = pe.Constraint(expr=(m.inc == m.px * m.x + m.py * m.y + m.pz * m.z), doc='specs of income')
    m.emiD = pe.Constraint(expr=(m.emi == m.ex * m.x + m.ey * m.y + m.ez * m.z), doc='specs of emission')

    # m.pprint()
    print(f"mk_conc(): concrete model {m.name} generated.")
    return m

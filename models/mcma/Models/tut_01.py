
import pyomo.environ as pe       # more robust than using import *


# noinspection PyUnresolvedReferences
def tut_01():
    """The sand-box Pipa-like ConcreteModel for testing mcma"""
    m = pe.ConcreteModel(name='Tutorial 0.1')

    m.T = pe.Set(initialize=['BTL', 'STL', 'OTL'])

    # variables
    m.act = pe.Var(m.T, domain=pe.NonNegativeReals, doc='level of activity')
    # m.z = pe.Var(domain=pe.NonNegativeReals, bounds=(0, 100), doc='level of z activity')

    # outcome variables
    m.prod = pe.Var(domain=pe.NonNegativeReals, doc='total production')
    m.emi = pe.Var(domain=pe.NonNegativeReals, doc='emission')
    m.exp = pe.Var(domain=pe.NonNegativeReals, doc='export')

    # objective:
    @m.Objective(sense=pe.maximize)
    def goal(mx):
        return mx.prod

    @m.Objective(sense=pe.minimize)
    def goal2(mx):
        return mx.emi
    m.goal2.deactivate()

    # parameters  (declared in the sequence corresponding to their use in SMS)
    m.capT = pe.Param(domain=pe.NonNegativeReals, default=1000., doc='sum of capacities over all techn.')
    m.frac = pe.Param(domain=pe.NonNegativeReals, default=70., doc='fraction of total cap. available to each tech')
    m.pr = pe.Param(m.T, domain=pe.NonNegativeReals, mutable=True, default=1., doc='unit prod. of act')
    m.em = pe.Param(m.T, domain=pe.NonNegativeReals, mutable=True, default=1., doc='unit emission of act')
    m.ex = pe.Param(m.T, domain=pe.NonNegativeReals, mutable=True, default=0., doc='unit export by act')
    m.pr['BTL'] = 5.
    m.pr['STL'] = 15.
    m.pr['OTL'] = 25.
    m.em['BTL'] = 0.1
    m.em['STL'] = 10.
    m.em['OTL'] = 100.
    m.ex['BTL'] = 50.
    m.ex['STL'] = 10.
    m.ex['OTL'] = 1.

    # relations (constraints)
    @m.Constraint(m.T)
    def actC(mx, t):
        return 0, mx.act[t], mx.frac * mx.capT

    @m.Constraint()
    def actT(mx):
        return 0, sum(mx.act[t] for t in mx.T), 1.0 * mx.capT

    @m.Constraint()
    def prodT(mx):
        return mx.prod == sum(mx.pr[t] * mx.act[t] for t in mx.T)

    @m.Constraint()
    def emiT(mx):
        return mx.emi == sum(mx.em[t] * mx.act[t] for t in mx.T)

    @m.Constraint()
    def expT(mx):
        return mx.exp == sum(mx.ex[t] * mx.act[t] for t in mx.T)

    # m.pprint()
    print(f"sbPipa(): concrete model {m.name} generated.")
    return m

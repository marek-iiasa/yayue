
import pyomo.environ as pe       # more robust than using import *


# noinspection PyUnresolvedReferences
def sbPipa():
    """The sand-box Pipa-like ConcreteModel for testing mcma"""
    m = pe.ConcreteModel(name='Sand-box Pipa 0.1')

    m.T = pe.Set(initialize=['BTL', 'STL', 'OTL'])

    # variables
    m.act = pe.Var(m.T, domain=pe.NonNegativeReals, doc='level of activity')
    # m.z = pe.Var(domain=pe.NonNegativeReals, bounds=(0, 100), doc='level of z activity')

    # outcome variables
    m.prod = pe.Var(domain=pe.NonNegativeReals, doc='total production')
    m.emi = pe.Var(doc='emission')

    # objective:
    @m.Objective(sense=pe.maximize)
    def goal(mx):
        return mx.prod

    @m.Objective(sense=pe.minimize)
    def goal2(mx):
        return mx.emi
    m.goal2.deactivate()

    # parameters  (declared in the sequence corresponding to their use in SMS)
    m.capT = pe.Param(domain=pe.NonNegativeReals, default=1000., doc='sum of capcities of all techn.')
    m.frac = pe.Param(domain=pe.NonNegativeReals, default=70., doc='fraction of total cap. available to each tech')
    m.pr = pe.Param(m.T, domain=pe.NonNegativeReals, mutable=True, default=1., doc='unit prod. of act')
    m.em = pe.Param(m.T, domain=pe.NonNegativeReals, mutable=True, default=1., doc='unit emission of act')
    m.pr['BTL'] = 5.
    m.pr['STL'] = 15.
    m.pr['OTL'] = 25.
    m.em['BTL'] = 0.1
    m.em['STL'] = 10.
    m.em['OTL'] = 100.

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

    m.pprint()
    print(f"sbPipa(): concrete model {m.name} generated.")
    return m

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.
# See PyCharm help at https://www.jetbrains.com/help/pycharm/
# PyCharm > select "File" menu > select "Invalidate Caches / Restart" menu option
#   noinspection PyUnresolvedReferences
#   infty = float('inf')

"""
Prototype of a simple PTL (Power to Liquid) model based on representative data of China
"""
from pyomo.environ import *     # used in pyomo book and many tutotial
# import pyomo.environ as pyo       # for this import pyo has to be used everywhere
# from sympy import subsets  # explore this to avoid warnings

'''
sms(): returns the Symbolic model specification (SMS), i.e., the Abstract Model.
All rules are before sms() to avoid warnings "m shadows name from outer scope". Rules for single (i.e., not populated)
relations are not really needed, provided no iterators are used.
'''


def vlist(p, lifet):
    """
    :param p: index of the period
    :param lifet: capacity life-time (periods after the vitage period)
    :return: list of vitage periods of still available new capacity (composed of at least one period, i.e., p)
    """
    for i in range(0, lifet + 1):
        # print(f'lifet = {lifet}, p = {p}, i = {i}, p - i = {p - i}')
        yield p - i


# initialize the Vp set (V_p)
def vp_init(m):
    return ((p, v) for p in m.P for v in vlist(p, len(m.H)))


# generator of v (vintage periods) for pp (planning period); the pairs stored in the Vp set (V_p)
# filter values: None (yield all), neg (yield only negative v), nonneg (yield only non-negative v)
def vp_lst(m, pp, filt=None):
    for p, v in m.VP:
        if p == pp:
            # print(f'vp_lst: pp = {pp}, p = {p}, v = {v}')
            if filt is None:
                yield v
            elif filt == 'neg':
                if v < 0:
                    yield v
            elif filt == 'nonneg':
                if v >= 0:
                    yield v


def demand_rule(m, f, p):  # demand must be met for each output and period
    exp1 = sum(sum(m.a[t, v, f] * m.act[t, p, v] for v in vp_lst(m, p)) for t in m.T)  # output from V_p & all techn.
    return m.d[f, p], exp1, None


def pcap_rule(m, t, p, v):  # planned capacity at each vintage available for activity within planning periods
    # print(f'pcap_rule: t {t}, p {p}, v {v}')
    if v < 0:   # act constrained by (given) historical new capacity
        return inequality(0., m.act[t, p, v], m.cuf[t, v] * m.hncap[t, v])
    else:   # act constrained by (decision variable) new capacity
        exp1 = m.cuf[t, v] * m.ncap[t, v] - m.act[t, p, v]
        return inequality(0., exp1, None)


def omvar_rule(m):  # variable part of OMC
    return m.omcVar == sum(sum(m.dis[p] * sum(m.vom[t, v] * m.act[t, p, v] for v in vp_lst(m, p, 'nonneg'))
                               for p in m.P) for t in m.T)


def omfixp_rule(m):  # fixed part of OMC
    return m.omcFixP == sum(sum(m.dis[p] * m.fom[t, p] * m.ncap[t, p] for p in m.P) for t in m.T)


def omfixh_rule(m):  # fixed part of OMC
    return m.omcFixH == sum(sum(m.dis[p] * sum(m.fom[t, v] * m.hncap[t, v] for v in m.H) for p in m.P) for t in m.T)


def invcost_rule(m):  # total investment cost (only in planning periods)
    return m.invCost == sum(sum(m.invC[t, v] * m.ncap[t, v] for t in m.T) for v in m.P)


def co2_rule(m):    # total CO2 emission
    return m.co2 == sum(sum(sum(m.ef[t, v] * m.act[t, p, v] for v in vp_lst(m, p)) for p in m.P) for t in m.T)


def sms():
    m = AbstractModel(name='cn_liquid v.1.0')
    # config parameters
    periods = 3   # number of planning periods
    lifet = 1     # life-time, i.e., number of periods capacity remains available after the vintage period
    print(f'Configuration params: planning periods = {periods}, capacity life-time (after vintage) = {lifet}')
    '''
    params cannot be used before they are constructed (in abstract model)
    m.periods = Param(initialize=3)  # number of planning periods
    m.lifet = Param(initialize=0)   # capacity-life in number of periods after the vintage period
    '''
    # sets
    # subsets(expand_all_set_operators=True)  explore this to avoid warnings
    m.P = RangeSet(0, periods - 1)     # planning periods; NOTE: RangeSet(0, 1) has two elements
    # m.P.pprint()
    if value(lifet) > 0:
        m.H = RangeSet(-lifet, -1)     # historical (before the planning) new capacities periods
    else:
        m.H = Set()     # empty set of historical capacities
    # m.H.pprint()
    m.V = m.H | m.P     # vintage (periods when ncap become available)
    # m.V.pprint()
    m.VP = Set(dimen=2, initialize=vp_init)  # V_p (subsets of vintages available at period p)
    # m.VP.pprint()
    m.T = Set()     # technologies
    m.F = Set()     # final commodities/products, i.e., liquid fuel(s)

    # decision variables
    # m.act = Var(m.T, m.V, m.P, within=NonNegativeReals)   # activity level; this specs generates full/dense act matrix
    # m.act = Var(m.T, m.VP, m.P, within=NonNegativeReals)  # wrong: generates 4 indices !
    m.act = Var(m.T, m.VP, within=NonNegativeReals)  # activity level act[t, p, v]
    m.ncap = Var(m.T, m.V, within=NonNegativeReals)   # newly installed capacity

    # outcome variables
    m.cost = Var()   # total cost
    m.invCost = Var()   # total investment
    m.omCost = Var(within=NonNegativeReals)   # total OMC
    m.co2 = Var()   # total CO2 emission (by activities act)
    # auxiliary variables
    # m.inpCost = Var(within=NonNegativeReals)   # total cost of inputs (energy, materials)
    m.omcVar = Var(within=NonNegativeReals)   # variable part of OMC (depends on activities)
    m.omcFix = Var(within=NonNegativeReals)   # variable fixed of OMC (depends on capacities)
    m.omcFixP = Var(within=NonNegativeReals)   # part of omcFix caused by capacities in the planning periods
    m.omcFixH = Var(within=NonNegativeReals)   # part of omcFix caused by capacities in the historical periods

    # objectives: 2 defined, one activate at a time
    m.min_cost = Objective(expr=m.cost, sense=minimize)
    m.min_co2 = Objective(expr=m.co2, sense=minimize)
    m.min_cost.activate()
    m.min_co2.deactivate()
    # m.min_cost.deactivate()
    # m.min_co2.activate()

    # parameters
    m.discr = Param(within=NonNegativeReals, default=1.0)   # discount rate for each period
    m.dis = Param(m.P, mutable=True, within=NonNegativeReals, default=1.0)    # cumulative discount
    m.hncap = Param(m.T, m.H, within=NonNegativeReals, default=0.0)   # capacities installed in historical periods
    m.d = Param(m.F, m.P, within=NonNegativeReals, default=0.0)   # given demand
    m.a = Param(m.T, m.V, m.F, within=NonNegativeReals, default=0.0)   # unit activity output of fuel
    m.cuf = Param(m.T, m.V, within=NonNegativeReals, default=0.0)   # capacity utilization factor
    m.invC = Param(m.T, m.P, within=NonNegativeReals, default=0.0)   # unit inv cost
    m.vom = Param(m.T, m.P, within=NonNegativeReals, default=0.0)   # unit OMC variable cost
    m.fom = Param(m.T, m.V, within=NonNegativeReals, default=0.0)   # unit OMC fixed cost
    m.ef = Param(m.T, m.V, within=NonNegativeReals, default=0.0)   # unit CO2 emission

    # relations
    # single (non-indexed) constraints; expr cannot use iterators, e.g., sum for p in m.P
    m.costC = Constraint(expr=(m.cost == m.invCost + m.omCost))
    m.omCostC = Constraint(expr=(m.omCost == m.omcFix + m.omcVar))
    m.omFixC = Constraint(expr=(m.omcFix == m.omcFixP + m.omcFixH))
    # indexed constraints (require rules defining population; to avoid warnings, rules are defined outside sms()
    m.demandC = Constraint(m.F, m.P, rule=demand_rule)  # demand has to be covered by production by the activity
    m.avAct = Constraint(m.T, m.VP, rule=pcap_rule)  # act is constained by the corresponding available capacity
    m.invCostC = Constraint(rule=invcost_rule)
    m.omcVarC = Constraint(rule=omvar_rule)
    m.omcFixPC = Constraint(rule=omfixp_rule)
    m.omcFixHC = Constraint(rule=omfixh_rule)
    m.co2C = Constraint(rule=co2_rule)
    '''
    def inputs_c(m):    # total cost of inputs (energy, raw materials, etc)
        return m.inpCost == sum(sum(m.inpUcost[i, p] * m.newCap[i, p] for i in m.I) for p in m.P)
    m.inpCostC = Constraint(rule=inputs_c)
    '''

    print('sms(): finished')
    # m.pprint()    # does not work (needs lengths of sets
    return m


# return the model instance (currently the params are in *.dat, i.e., AMPL-like format
def instance(m):
    # data = DataPortal()  # the default arg: (model=model) !
    # data.load(filename='data0.yaml')  # works with DataPortal() and DataPortal(model=m)
    # data.load(filename='data0.json')  # works with DataPortal() and DataPortal(model=m)
    data = DataPortal(model=m)  # parameter (model=m) needed for loading *.dat
    data.load(filename='data0.dat')  # dat-format requires DataPortal(model=m)
    inst = m.create_instance(data)
    for p in m.P:   # define discount rates for each period
        inst.dis[p] = inst.discr ** p
        # print(f'p = {p}, dis = {value(inst.dis[p])}')
    # print('\ninstance.pprint():')
    # inst.pprint()
    # print('-----------------------------------------------------------------')
    # inst.VP.pprint()
    return inst


if __name__ == '__main__':
    abst = sms()        # abstract model (SMS)
    model = instance(abst)  # model instance
    # print('\nmodel display: -----------------------------------------------------------------------------')
    # model.display()     # displays only instance (not abstract model)
    # print('end of model display: ------------------------------------------------------------------------')

    # opt = SolverFactory('gams')  # gams can be used as a solver
    opt = SolverFactory('glpk')
    # print('\nbefore solve():')
    result_obj = opt.solve(model, tee=True)
    print('\nmodel pprint: ----------------------------------------------------------------------------')
    model.pprint()
    print('end of model pprint ------------------------------------------------------------------------')
    print('min_cost = ', value(model.cost))
    print('min_co2 = ', value(model.co2))

    # print('values of indexed variables cannot be accessed by value()')
    # print('act = ', value(model.act))

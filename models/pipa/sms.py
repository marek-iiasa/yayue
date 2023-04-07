"""
sms(): returns the Symbolic model specification (SMS), i.e., the Abstract Model
of the China liquid fuel production model.
All rules are before sms() to avoid warnings "m shadows name from outer scope".
Single (i.e., not populated) relations need rules only, if their expression include iterators (e.g., a sum).
"""

import pyomo.environ as pe       # more robust than using import *
# from pyomo.environ import *     # used in pyomo book and many tutotials, causes problems
# from sympy import subsets  # explore this to avoid warnings


def vlist(p, lifet):
    # noinspection GrazieInspection
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
    for p, v in m.PV:
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


def dem_rule(m, f, p):  # demand must be met for each fuel and period
    exp1 = sum(sum(m.a[t, f] * m.act[t, p, v] for v in vp_lst(m, p)) for t in m.T)  # output from V_p & all techn.
    return m.dem[f, p], exp1, None


def act_rule(m, t, p, v):  # activity cannot exceed the corresponding (cuf * capacity)
    # print(f'pcap_rule: t {t}, p {p}, v {v}')
    if v < 0:   # act constrained by (given) historical new capacity
        return pe.inequality(0., m.act[t, p, v], m.cuf[t] * m.hcap[t, v])
    else:   # act constrained by (decision variable) new capacity
        exp1 = m.cuf[t] * m.cap[t, v] - m.act[t, p, v]
        return pe.inequality(0., exp1, None)


def rawd_rule(m, t, p):  # total amounts of raw material needed for production
    # return m.raw[t, p] - sum(m.rawU[t, v] * m.act[t, p, v] for v in vp_lst(m, p)) == 0
    return m.raw[t, p] == sum(m.rawU[t] * m.act[t, p, v] for v in vp_lst(m, p))  # equivalent to the commented above


def invcd_rule(m, t, p):  # total amounts of raw material needed for production
    return m.invC[t, p] == m.invU[t] * m.cap[t, p]


def rawcd_rule(m, t, p):  # raw material cost
    return m.rawC[t, p] == m.rawP[t] * m.raw[t, p]


def omcd_rule(m, t, p):  # OMC (excl. raw-material) of all (currently available) capacities
    # return m.omC == sum(m.omcU[t, v] * m.act[t, p, v] for v in vp_lst(m, p, 'nonneg'))
    # return m.omC == sum(m.omcU[t, v] * m.act[t, p, v] for v in vp_lst(m, p))  # use for omC(act[]) instead omC(cap[])
    # return m.omC[t, p] == sum(m.omcU[t, v] * m.cap[t, v] for v in vp_lst(m, p))  # doesn't work for v < 0
    omsum = 0.
    for v in vp_lst(m, p):
        if v < 0:
            omsum += m.omcU[t] * m.hcap[t, v]
        else:
            omsum += m.omcU[t] * m.cap[t, v]
    return m.omC[t, p] == omsum


def carbed_rule(m, t, p):
    return m.carbE[t, p] == sum(m.ef[t] * m.act[t, p, v] for v in vp_lst(m, p))


def carbevd_rule(m, t, v):
    # print(f'carbevd start: t = {t}, v = {v} ------------------------------ ')
    sum_act = 0.    # sum act[t, p, v] for all p using act[*, p, v] (v - given)
    for p, vv in m.PV:
        if v == vv:
            sum_act += m.act[t, p, v]
            # print(f'carbed_rule: t = {t}, p = {p}, vv = {vv}, v = {v}, sum changed = {sum_act}')
        else:
            # print(f'carbed: p = {p}, vv = {vv}, v = {v}, sum unchanged')
            pass
    # print(f'carbed_rule: t = {t}, v = {v}, sum_act = {sum_act} ------------------------------ ')
    return m.carbEv[t, v] == m.ef[t] * sum_act


def carbcd_rule(m, t, p):  # cost of carbon emission
    # the old/commented code double-counts carbE[t, v] in costs
    # return m.carbC[t, p] == m.carbU * sum(m.carbE[t, v] for v in vp_lst(m, p))
    return m.carbC[t, p] == m.carbU * m.carbE[t, p]


def carb_rule(m):  # total CO2 emission
    # return m.carb == sum(sum(sum(m.ef[t, v] * m.act[t, p, v] for v in vp_lst(m, p)) for p in m.P) for t in m.T)
    return m.carb == sum(sum(m.carbE[t, p] for p in m.P) for t in m.T)


def costad_rule(m, t, p):  # total annual cost
    return m.costAn[t, p] == m.invC[t, p] + m.rawC[t, p] + m.omC[t, p] + m.carbC[t, p]


def cost_rule(m):  # total cost
    return m.cost == sum(m.dis[p] * sum(m.costAn[t, p] for t in m.T) for p in m.P)


def actSum_rule(m, t, p):  # sum of activities [t] covering demand[p]
    return m.actsv[t, p] == sum(m.act[t, p, v] for v in vp_lst(m, p))


def actSump_rule(m, t):  # sum of activities [t] covering demand over all [p]
    return m.actsvp[t] == sum(m.actsv[t, p] for p in m.P)


def capAva_rule(m, t, p):  # cuf[t, v] * capacities avail. for covering demand[p] by techn. [t]
    capsum = 0.
    for v in vp_lst(m, p):
        if v < 0:
            capsum += m.cuf[t] * m.hcap[t, v]
        else:
            capsum += m.cuf[t] * m.cap[t, v]
    return m.capAva[t, p] == capsum


def capIdle_rule(m, t, p):  # idle (unused) capacities available for covering demans[p]
    return m.capIdle[t, p] == m.capAva[t, p] - m.actsv[t, p]


def capIdleS_rule(m, t):  # sum (over all periods) of idle capacities
    return m.capIdleS[t] == sum(m.capIdle[t, p] for p in m.P)


def capTot_rule(m, t):  # sum (over all periods) of idle capacities
    return m.capTot[t] == sum(m.cap[t, p] for p in m.P)


def oilImp_rule(m):  # sum (over all periods) of idle capacities
    return m.oilImp == sum(m.raw['OTL', p] for p in m.P)


'''
# for ad-hoc testing of upp-bnds for cap
# for a proper/general approach cf: https://pyomo.readthedocs.io/en/stable/pyomo_modeling_components/Variables.html
def bnd_cap(m, t, p):
    if p == 0:
        return (0., 0.)
    elif p == 2:
        return (0., 25.)
    else:
        return (0., None)
'''

# TODO: clarify develop/master


# noinspection PyUnresolvedReferences
def mk_sms():
    m = pe.AbstractModel(name='pipa 1.0')
    # config parameters
    lifet = 3     # life-time, i.e., number of periods capacity remains available after the vintage period # 4
    # print(f'Configuration params: planning periods = {periods}, capacity life-time (after vintage) = {lifet}')
    '''
    params cannot be used before they are constructed (in abstract model)
    m.periods = Param(initialize=3)  # number of planning periods
    m.lifet = Param(initialize=0)   # capacity-life in number of periods after the vintage period
    '''
    # sets
    # subsets(expand_all_set_operators=True)  explore this to avoid warnings
    # TODO: static values of periods are a temporary solution; periods shall be defined in data
    periods = 12   # number of planning periods
    m.P = pe.RangeSet(0, periods - 1)     # planning periods; NOTE: RangeSet(0, 1) has two elements
    # FIXME: the next two commented lines demonstrate error; explore how to use data-defined parameter for
    #   defining the range-set
    # m.periodq = pe.Param(within=pe.PositiveIntegers, default=3)   # number of planning periods
    # m.Q = pe.RangeSet(0, pe.value(m.periodq) - 1)     # doesn't work: evaluates value before concrete model is set
    # m.P.pprint()
    if pe.value(lifet) > 0:
        m.H = pe.RangeSet(-lifet, -1)     # historical (before the planning) new capacities periods
    else:
        m.H = pe.Set()     # empty set of historical capacities
    # m.H.pprint()
    m.V = m.H | m.P     # vintage (periods when ncap become available)
    # m.V.pprint()
    m.PV = pe.Set(dimen=2, initialize=vp_init)  # V_p (subsets of vintages available at period p)
    # m.PV.pprint()
    m.T = pe.Set()     # technologies
    m.F = pe.Set()     # final commodities/products, i.e., liquid fuel(s)

    # decision variables
    # m.act = Var(m.T, m.V, m.P, within=NonNegativeReals)   # activity level; this specs generates full/dense act matrix
    # m.act = Var(m.T, m.PV, m.P, within=NonNegativeReals)  # wrong: generates 4 indices !
    m.act = pe.Var(m.T, m.PV, within=pe.NonNegativeReals)  # activity level act[t, p, v]
    m.cap = pe.Var(m.T, m.P, within=pe.NonNegativeReals)   # newly installed capacity cap[t, p]
    # m.cap = pe.Var(m.T, m.P, within=pe.NonNegativeReals, bounds=bnd_cap)   # newly installed capacity cap[t, p]

    # outcome variables
    m.cost = pe.Var()   # total cost, single-crit objective for the regret-function app.
    m.carb = pe.Var()   # total carbon emission
    m.co2C = pe.Var()   # cost of the total carbon emission
    m.coexco2 = pe.Var()   # cost of the total carbon emission
    m.oilImp = pe.Var()   # total amount of imported oil
    # auxiliary variables, amounts
    m.raw = pe.Var(m.T, m.P, within=pe.NonNegativeReals)   # amount of raw-material (feeadstock)
    m.carbE = pe.Var(m.T, m.P, within=pe.NonNegativeReals)   # CO2 emissions (caused by act covering demand[p]
    m.carbEv = pe.Var(m.T, m.V, within=pe.NonNegativeReals)   # CO2 emissions (by act[t, p, v]) caused by cap[v]
    # auxiliary variables, costs
    m.invC = pe.Var(m.T, m.P, within=pe.NonNegativeReals)   # trajectories of investment costs
    m.rawC = pe.Var(m.T, m.P, within=pe.NonNegativeReals)   # trajectories of raw-material costs
    m.omC = pe.Var(m.T, m.P, within=pe.NonNegativeReals)   # trajectories of OMC (raw-materials excluded)
    m.carbC = pe.Var(m.T, m.P, within=pe.NonNegativeReals)   # trajectories of CO2 emission costs
    m.costAn = pe.Var(m.T, m.P, within=pe.NonNegativeReals)   # trajectories of total costs
    # other auxiliary variables, e.g., sums
    m.actsv = pe.Var(m.T, m.P, within=pe.NonNegativeReals)  # activities summed over v act[t, p]
    m.actsvp = pe.Var(m.T, within=pe.NonNegativeReals)  # total activities (i.e., summed over v and p act[t])
    m.capAva = pe.Var(m.T, m.P, within=pe.NonNegativeReals)  # avail. capacities
    m.capIdle = pe.Var(m.T, m.P, within=pe.NonNegativeReals)  # idle capacities
    m.capIdleS = pe.Var(m.T, within=pe.NonNegativeReals)  # total idle capacities
    m.capTot = pe.Var(m.T, within=pe.NonNegativeReals)  # total capacities (i.e., all cap-investments in techn. t)
    #

    # objectives: two defined for MCA, only one activated at a time
    m.min_cost = pe.Objective(expr=m.cost, sense=pe.minimize)   # single objective used for this case-study
    m.min_carb = pe.Objective(expr=m.carb, sense=pe.minimize)
    m.min_oilimp = pe.Objective(expr=m.oilImp, sense=pe.minimize)
    m.min_cost.activate()
    # m.min_carb.activate()
    # m.min_oilimp.activate()
    #
    # m.min_cost.deactivate()
    m.min_carb.deactivate()
    m.min_oilimp.deactivate()

    # parameters  (declared in the sequence corresponding to their use in SMS)
    m.discr = pe.Param(within=pe.NonNegativeReals, default=0.05)   # discount rate for each period
    m.dis = pe.Param(m.P, mutable=True, within=pe.NonNegativeReals, default=0.9)    # cumulated discount
    #
    m.a = pe.Param(m.T, m.F, within=pe.NonNegativeReals, default=1.0)   # unit activity output of fuel
    m.ef = pe.Param(m.T, within=pe.NonNegativeReals, default=1.0)   # unit CO2 emission
    m.dem = pe.Param(m.F, m.P, within=pe.NonNegativeReals, default=350.0)   # given demand
    m.hcap = pe.Param(m.T, m.H, within=pe.NonNegativeReals, default=0.0)  # capacities installed in historical periods
    m.cuf = pe.Param(m.T, within=pe.NonNegativeReals, default=1.0)   # capacity utilization factor
    m.rawU = pe.Param(m.T, within=pe.NonNegativeReals, default=1.0)   # raw material use per prod.-unit
    m.invU = pe.Param(m.T, within=pe.NonNegativeReals, default=1.0)   # unit inv cost
    m.rawP = pe.Param(m.T, within=pe.NonNegativeReals, mutable=True, default=1.0)   # unit cost of raw material
    m.omcU = pe.Param(m.T, within=pe.NonNegativeReals, default=1.0)   # unit OMC cost (excl. feedstock)
    m.carbU = pe.Param(within=pe.NonNegativeReals, mutable=True, default=1.0)   # unit carbon-emission cost

    # relations  (declared in the sequence corresponding to their use in SMS)
    # single (non-indexed) constraints; expr cannot use iterators, e.g., sum for p in m.P
    # indexed constraints (require rules defining population; to avoid warnings, rules are defined outside sms()
    m.demC = pe.Constraint(m.F, m.P, rule=dem_rule)  # fuel produced by activities covers the demand
    m.actC = pe.Constraint(m.T, m.PV, rule=act_rule)  # act constained by the corresponding available capacity
    m.rawD = pe.Constraint(m.T, m.P, rule=rawd_rule)  # amounts of raw material definitions
    m.invCD = pe.Constraint(m.T, m.P, rule=invcd_rule)  # trajectory of inv cost
    m.rawCD = pe.Constraint(m.T, m.P, rule=rawcd_rule)  # trajectory of raw-material cost
    m.omCD = pe.Constraint(m.T, m.P, rule=omcd_rule)  # trajectory of OM costs (currently of capacities)
    m.carbED = pe.Constraint(m.T, m.P, rule=carbed_rule)    # trajectory of amounts of CO2 emissions caused by dem[p]
    m.carbEvD = pe.Constraint(m.T, m.V, rule=carbevd_rule)    # trajectory of amounts of CO2 emissions caused by cap[v]
    m.carbCD = pe.Constraint(m.T, m.P, rule=carbcd_rule)    # trajectory of costs of CO2 emissions
    m.costAnD = pe.Constraint(m.T, m.P, rule=costad_rule)   # trajectory of annual cost
    m.costD = pe.Constraint(rule=cost_rule)     # total cost
    m.carbD = pe.Constraint(rule=carb_rule)     # total CO2 emission
    m.actSumD = pe.Constraint(m.T, m.P, rule=actSum_rule)
    m.actSumpD = pe.Constraint(m.T, rule=actSump_rule)
    m.capAvailD = pe.Constraint(m.T, m.P, rule=capAva_rule)
    m.capIdleD = pe.Constraint(m.T, m.P, rule=capIdle_rule)
    m.capIdleSD = pe.Constraint(m.T, rule=capIdleS_rule)
    m.capTotD = pe.Constraint(m.T, rule=capTot_rule)
    m.oilImpD = pe.Constraint(rule=oilImp_rule)
    # the below defined without a rule; () in expr are optional
    m.co2CD = pe.Constraint(expr=(m.co2C == m.carbU * m.carb))  # costs of CO2 emission
    m.costexco2D = pe.Constraint(expr=(m.coexco2 == m.cost - m.co2C))  # total costs excl. CO2 emission cost

    print('sms(): finished')
    # m.pprint()    # does not work (needs lengths of sets)
    return m

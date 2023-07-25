"""
sms(): returns the Symbolic model specification (SMS), i.e., the Abstract Model of the Pipa model
Decorations are used for Constraints and Objective to simplify the old/traditional approach based on rules,
which required a separation of rules needed for defining constraints, i.e.:
All rules are before sms() to avoid warnings "m shadows name from outer scope".
Single (i.e., not populated) relations need rules only, if their expression include iterators (e.g., a sum).
"""

import pyomo.environ as pe       # more robust than using import *
# from pyomo.core import AbstractModel (no longer needed)
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
            else:
                raise Exception(f'Unknown value of param filt in vp_lst(): {filt}.')


'''
Rules no longer used (replaced by functions attached to the constraint decorators

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

def costad_rule(m, t, p):  # total annual cost
    return m.costAn[t, p] == m.invC[t, p] + m.rawC[t, p] + m.omC[t, p] + m.carbC[t, p]

def cost_rule(m):  # total cost
    return m.cost == sum(m.dis[p] * sum(m.costAn[t, p] for t in m.T) for p in m.P)

def carb_rule(m):  # total CO2 emission
    # return m.carb == sum(sum(sum(m.ef[t, v] * m.act[t, p, v] for v in vp_lst(m, p)) for p in m.P) for t in m.T)
    return m.carb == sum(sum(m.carbE[t, p] for p in m.P) for t in m.T)

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

    # relations  (declared in the sequence corresponding to their use in SMS)
    # single (non-indexed) constraints; expr cannot use iterators, e.g., sum for p in m.P
    # indexed constraints (require rules defining population; to avoid warnings, rules are defined outside sms()
    # m.demC = pe.Constraint(m.F, m.P, rule=dem_rule)
    # m.actC = pe.Constraint(m.T, m.PV, rule=act_rule)  # act constained by the corresponding available capacity
    # m.rawD = pe.Constraint(m.T, m.P, rule=rawd_rule)  # amounts of raw material definitions
    # m.invCD = pe.Constraint(m.T, m.P, rule=invcd_rule)  # trajectory of inv cost
    # m.rawCD = pe.Constraint(m.T, m.P, rule=rawcd_rule)
    # m.omCD = pe.Constraint(m.T, m.P, rule=omcd_rule)  # trajectory of OM costs (currently of capacities)
    # m.carbED = pe.Constraint(m.T, m.P, rule=carbed_rule)    # trajectory of amounts of CO2 emissions caused by dem[p]
    # m.carbEvD = pe.Constraint(m.T, m.V, rule=carbevd_rule)    # trajectory of CO2 emissions caused by cap[v]
    # m.carbCD = pe.Constraint(m.T, m.P, rule=carbcd_rule)    # trajectory of costs of CO2 emissions
    # m.costAnD = pe.Constraint(m.T, m.P, rule=costad_rule)   # trajectory of annual cost
    # m.costD = pe.Constraint(rule=cost_rule)     # total cost
    # m.carbD = pe.Constraint(rule=carb_rule)     # total CO2 emission
    # m.actSumD = pe.Constraint(m.T, m.P, rule=actSum_rule)
    # m.actSumpD = pe.Constraint(m.T, rule=actSump_rule)
    # m.capAvailD = pe.Constraint(m.T, m.P, rule=capAva_rule)
    # m.capIdleD = pe.Constraint(m.T, m.P, rule=capIdle_rule)
    # m.capIdleSD = pe.Constraint(m.T, rule=capIdleS_rule)
    # m.capTotD = pe.Constraint(m.T, rule=capTot_rule)
    # m.oilImpD = pe.Constraint(rule=oilImp_rule)
    # the below defined without a rule; () in expr are optional
    # m.co2CD = pe.Constraint(expr=(m.co2C == m.carbU * m.carb))  # costs of CO2 emission
    # m.costexco2D = pe.Constraint(expr=(m.coexco2 == m.cost - m.co2C))  # total costs excl. CO2 emission cost
'''

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


# noinspection PyUnresolvedReferences
def mk_sms():
    m: AbstractModel = pe.AbstractModel(name='pipa 1.1')
    # sets
    # subsets(expand_all_set_operators=True)  explore this to avoid warnings
    m.periods = pe.Param(domain=pe.PositiveIntegers, default=3)   # number of planning periods
    # noinspection PyTypeChecker
    # warning: pe.Param used instead of expected int (but a cast to the latter cannot be used in Abstract model)
    m.periods_ = pe.Param(initialize=m.periods-1)   # index of the last planning periods
    m.P = pe.RangeSet(0, m.periods_)  # set of periods; NOTE: RangeSet(0, 1) has two elements, RangeSet(0, -1) is empty
    # life-time, i.e., number of periods capacity remains available after the vintage period
    m.lifet = pe.Param(within=pe.NonNegativeIntegers, default=0)
    m.lifet_ = pe.Param(initialize=-m.lifet)
    # m.H is empty for m.lifet==0, i.e. RangeSet(0, -1) defines an empty set
    m.H = pe.RangeSet(m.lifet_, -1)     # historical (before the planning) new capacities periods
    m.V = m.H | m.P     # vintage (periods when ncap become available)
    m.PV = pe.Set(dimen=2, initialize=vp_init)  # V_p (subsets of vintages available at period p)
    m.T = pe.Set()     # technologies
    m.F = pe.Set()     # final commodities/products, i.e., liquid fuel(s)

    # the below two defs result in warnings, to avoid them m.periods_ and m.lifet_ are used above
    # m.P = pe.RangeSet(0, m.periods - 1)     # planning periods; NOTE: RangeSet(0, 1) has two elements
    # m.H = pe.RangeSet(-m.lifet, -1)     # historical (before the planning) new capacities periods

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

    # objectives: three defined for MCA, only one activated here at a time
    # TODO: clarify error (reported in model display): ERROR: evaluating object as numeric value: goal
    @m.Objective(sense=pe.minimize)
    def goal(mx):
        return mx.cost      # total cost
        # return mx.carb    # total CO2 emission
        # return mx.oilImp  # total oil import
    '''
    m.min_cost = pe.Objective(expr=m.cost, sense=pe.minimize)   # single objective used for testing
    m.min_carb = pe.Objective(expr=m.carb, sense=pe.minimize)
    m.min_oilimp = pe.Objective(expr=m.oilImp, sense=pe.minimize)
    m.min_cost.activate()
    # m.min_carb.activate()
    # m.min_oilimp.activate()
    #
    # m.min_cost.deactivate()
    m.min_carb.deactivate()
    m.min_oilimp.deactivate()
    '''

    # parameters  (declared in the sequence corresponding to their use in SMS)
    m.discr = pe.Param(within=pe.NonNegativeReals, default=0.9)   # discount rate descrease in every period
    m.dis = pe.Param(m.P, mutable=True, within=pe.NonNegativeReals, default=0.9)  # cumulated discount in each period
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

    '''
    demR() works after modifications; therefore these lines are now commented
    # noinspection PyShadowingNames
    # suppressed (for mk_sms()) warning: "shadows 'm' from outr scope" for code readability (to have demR() here)
    # use of m-alias in demR cause error in create_instance: Cannot iterate over AbstractOrderedScalarSet 'PV'
    '''
    @m.Constraint(m.F, m.P)  # fuel produced by activities must cover demand for each fuel at each period
    def demC(mx, f, p):
        exp = sum(sum(mx.a[t, f] * mx.act[t, p, v] for v in vp_lst(mx, p)) for t in mx.T)  # output from V_p & all tech
        return mx.dem[f, p], exp, None

    @m.Constraint(m.T, m.PV)  # activity cannot exceed the corresponding (cuf * capacity)
    def actC(mx, t, p, v):
        # print(f'pcap_rule: t {t}, p {p}, v {v}')
        if v < 0:  # act constrained by (given) historical new capacity
            return pe.inequality(0., mx.act[t, p, v], mx.cuf[t] * mx.hcap[t, v])
        else:  # act constrained by (decision variable) new capacity
            exp1 = mx.cuf[t] * mx.cap[t, v] - mx.act[t, p, v]
            return pe.inequality(0., exp1, None)

    @m.Constraint(m.T, m.P)  # total amounts of raw material needed for production
    def rawD(mx, t, p):
        # return mx.raw[t, p] - sum(mx.rawU[t, v] * mx.act[t, p, v] for v in vp_lst(mx, p)) == 0
        return mx.raw[t, p] == sum(mx.rawU[t] * mx.act[t, p, v] for v in vp_lst(mx, p))  # equivalent to the above

    @m.Constraint(m.T, m.P)  # trajectory of inv cost
    def invCD(mx, t, p):
        return mx.invC[t, p] == mx.invU[t] * mx.cap[t, p]

    @m.Constraint(m.T, m.P)  # trajectory of raw-material cost
    def rawCD(mx, t, p):
        return mx.rawC[t, p] == mx.rawP[t] * mx.raw[t, p]

    @m.Constraint(m.T, m.P)  # OMC (excl. raw-material) of all (currently available) capacities
    def omCD(mx, t, p):
        # return mx.omC == sum(mx.omcU[t, v] * mx.act[t, p, v] for v in vp_lst(mx, p, 'nonneg'))
        # ret mx.omC == sum(mx.omcU[t, v] * mx.act[t, p, v] for v in vp_lst(mx, p))  # use omC(act[]) instead omC(cap[])
        # return mx.omC[t, p] == sum(mx.omcU[t, v] * mx.cap[t, v] for v in vp_lst(mx, p))  # doesn't work for v < 0
        omsum = 0.
        for v in vp_lst(mx, p):
            if v < 0:
                omsum += mx.omcU[t] * mx.hcap[t, v]
            else:
                omsum += mx.omcU[t] * mx.cap[t, v]
        return mx.omC[t, p] == omsum

    @m.Constraint(m.T, m.P)    # trajectory of amounts of CO2 emissions caused by covering dem[p]
    def carbED(mx, t, p):
        return mx.carbE[t, p] == sum(mx.ef[t] * mx.act[t, p, v] for v in vp_lst(mx, p))

    @m.Constraint(m.T, m.V)    # trajectory of amounts of CO2 emissions caused by cap[v]
    def carbEDv(mx, t, v):
        # print(f'carbevd start: t = {t}, v = {v} ------------------------------ ')
        sum_act = 0.  # sum act[t, p, v] for all p using act[*, p, v] (v - given)
        for p, vv in mx.PV:
            if v == vv:
                sum_act += mx.act[t, p, v]
                # print(f'carbed_rule: t = {t}, p = {p}, vv = {vv}, v = {v}, sum changed = {sum_act}')
            else:
                # print(f'carbed: p = {p}, vv = {vv}, v = {v}, sum unchanged')
                pass
        # print(f'carbed_rule: t = {t}, v = {v}, sum_act = {sum_act} ------------------------------ ')
        return mx.carbEv[t, v] == mx.ef[t] * sum_act

    @m.Constraint(m.T, m.P)    # trajectory of costs of CO2 emissions
    def carbCD(mx, t, p):  # cost of carbon emission
        # the old/commented code double-counts carbE[t, v] in costs
        # return mx.carbC[t, p] == mx.carbU * sum(mx.carbE[t, v] for v in vp_lst(mx, p))
        return mx.carbC[t, p] == mx.carbU * mx.carbE[t, p]

    @m.Constraint(m.T, m.P)    # trajectory of annual cost
    def costAnD(mx, t, p):  # total annual cost
        return mx.costAn[t, p] == mx.invC[t, p] + mx.rawC[t, p] + mx.omC[t, p] + mx.carbC[t, p]

    @m.Constraint()    # total cost
    def costD(mx):
        return mx.cost == sum(mx.dis[p] * sum(mx.costAn[t, p] for t in mx.T) for p in mx.P)

    @m.Constraint()    # total CO2 emission
    def carbD(mx):
        # ret mx.carb == sum(sum(sum(mx.ef[t, v] * mx.act[t, p, v] for v in vp_lst(mx, p)) for p in mx.P) for t in mx.T)
        return mx.carb == sum(sum(mx.carbE[t, p] for p in mx.P) for t in mx.T)

    @m.Constraint(m.T, m.P)  # sum of activities [t] covering demand[p]
    def actSumD(mx, t, p):
        return mx.actsv[t, p] == sum(mx.act[t, p, v] for v in vp_lst(mx, p))

    @m.Constraint(m.T)  # sum of activities [t] covering demand over all [p]
    def actSumpD(mx, t):
        return mx.actsvp[t] == sum(mx.actsv[t, p] for p in mx.P)

    @m.Constraint(m.T, m.P)  # sum_v cuf[t] * cap[v] for covering demand[p] by techn. [t]
    def capAvaD(mx, t, p):
        capsum = 0.
        for v in vp_lst(mx, p):
            if v < 0:
                capsum += mx.cuf[t] * mx.hcap[t, v]
            else:
                capsum += mx.cuf[t] * mx.cap[t, v]
        return mx.capAva[t, p] == capsum

    @m.Constraint(m.T, m.P)  # idle (unused) capacities
    def capIdleD(mx, t, p):
        return mx.capIdle[t, p] == mx.capAva[t, p] - mx.actsv[t, p]

    @m.Constraint(m.T)  # sum (over all periods) of idle capacities
    def capIdleSD(mx, t):
        return mx.capIdleS[t] == sum(mx.capIdle[t, p] for p in mx.P)

    @m.Constraint(m.T)  # sum (over all periods) of capacities
    def capTotD(mx, t):
        return mx.capTot[t] == sum(mx.cap[t, p] for p in mx.P)

    @m.Constraint()  # total imported oil
    def oilImpD(mx):  # sum (over all periods) of idle capacities
        return mx.oilImp == sum(mx.raw['OTL', p] for p in mx.P)

    @m.Constraint()  # cost of the total CO2 emission
    def co2CD(mx):
        return mx.co2C == mx.carbU * mx.carb

    @m.Constraint()  # total costs excl. CO2 emission cost
    def costExco2CD(mx):
        return mx.coexco2 == mx.cost - mx.co2C

    print('sms(): finished')
    # m.pprint()    # does not work (needs lengths of sets)
    return m

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
    m: AbstractModel = pe.AbstractModel(name='pipa 1.2.1')  # multiple inputs/outputs to/from technologies
    # sets
    # subsets(expand_all_set_operators=True)  explore this to avoid warnings
    m.T = pe.Set()     # technologies
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
    m.J = pe.Set()     # inputs to technologies
    m.K = pe.Set()     # outputs from technologies (products, commodities) to cover demand or used as inputs
    # m.F = pe.Set()     # final commodities/products, i.e., liquid fuel(s): replaced by O

    # the below two defs result in warnings, to avoid them m.periods_ and m.lifet_ are used above
    # m.P = pe.RangeSet(0, m.periods - 1)     # planning periods; NOTE: RangeSet(0, 1) has two elements
    # m.H = pe.RangeSet(-m.lifet, -1)     # historical (before the planning) new capacities periods

    # decision variables
    # m.act = Var(m.T, m.V, m.P, within=NonNegativeReals)   # activity level; this specs generates full/dense act matrix
    # m.act = Var(m.T, m.PV, m.P, within=NonNegativeReals)  # wrong: generates 4 indices !
    # m.cap = pe.Var(m.T, m.P, within=pe.NonNegativeReals, bounds=bnd_cap)   # newly installed capacity cap[t, p]
    m.act = pe.Var(m.T, m.PV, within=pe.NonNegativeReals)  # activity level act[t, p, v]
    m.cap = pe.Var(m.T, m.P, within=pe.NonNegativeReals)   # newly installed capacity cap[t, p]

    # outcome variables
    m.cost = pe.Var()   # total cost, single-crit objective for the regret-function app.
    m.carb = pe.Var()   # total carbon emission
    m.oilImp = pe.Var()   # total amount of imported oil
    m.carbC = pe.Var()   # cost of the total carbon emission
    m.excarbC = pe.Var()   # total cost excludidng carbon emission cost
    # auxiliary variables, amounts
    m.carbE = pe.Var(m.T, m.P, within=pe.NonNegativeReals)   # CO2 emissions (caused by act covering demand[p]
    m.carbEv = pe.Var(m.T, m.V, within=pe.NonNegativeReals)   # CO2 emissions (by act[t, p, v]) caused by cap[v]
    # auxiliary variables, costs
    m.inpC = pe.Var(m.T, m.P, m.J, within=pe.NonNegativeReals)   # cost of inputs
    m.outC = pe.Var(m.T, m.P, m.K, within=pe.NonNegativeReals)   # cost of outputs
    m.invC = pe.Var(m.T, m.P, within=pe.NonNegativeReals)   # trajectories of investment costs
    m.omC = pe.Var(m.T, m.P, within=pe.NonNegativeReals)   # trajectories of OMC (raw-materials excluded)
    m.carbC = pe.Var(m.T, m.P, within=pe.NonNegativeReals)   # trajectories of CO2 emission costs
    m.costAn = pe.Var(m.T, m.P, within=pe.NonNegativeReals)   # trajectories of total costs
    # other auxiliary variables, e.g., sums
    m.inp = pe.Var(m.T, m.P, m.J, within=pe.NonNegativeReals)   # amounts of inputs
    m.out = pe.Var(m.T, m.P, m.K, within=pe.NonNegativeReals)   # amounts of outputs
    m.actV = pe.Var(m.T, m.P, within=pe.NonNegativeReals)  # activities summed over v act[t, p]
    m.actS = pe.Var(m.T, within=pe.NonNegativeReals)  # total activities (i.e., summed over v and p act[t])
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

    # parameters  (declared in the sequence corresponding to their use in SMS)
    m.discr = pe.Param(within=pe.NonNegativeReals, default=0.04)   # discount rate (param used in calculating m.dis)
    m.dis = pe.Param(m.P, mutable=True, within=pe.NonNegativeReals, default=1.)  # cumulated discount, see mod_instance
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

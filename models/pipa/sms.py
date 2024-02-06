"""
sms(): returns the Symbolic model specification (SMS), i.e., the Abstract Model of the Pipa model
Decorations are used for Constraints and Objective to simplify the old/traditional approach based on rules,
which required a separation of rules needed for defining constraints, i.e.:
All functions used in the m model are defined before mk_sms() to avoid warnings "m shadows name from outer scope".
"""

import pyomo.environ as pe       # more robust than using import *
# from pyomo.core import AbstractModel (no longer needed)
# from pyomo.environ import *     # used in pyomo book and many tutotials, causes problems
# from sympy import subsets  # explore this to avoid warnings


def th_init(m):  # initialize TH set (t, v) of vintage periods prior to p=0 capacities of t-th techn.
    for t in m.T:
        # print(f'th_init(): {t = }, life[t] = {m.life[t]}')
        for v in range(-m.life[t], 0):
            # print(f'{t = }, {v = }')
            yield t, v


def tv_init(m):  # initialize TV set (t, v) of all vintage periods of t-th techn.
    # use of m.periods/m.periods_ does not work: these are objects, not integers
    # print(f'tv_init(): periods = {len(m.P)}')
    periods = len(m.P)
    for t in m.T:
        hlen = m.life[t]
        # print(f'tv_init(): {t = }, hlist_len = {hlen}')
        v_lst1 = list(range(-hlen, 0))
        v_lst2 = list(range(0, periods))
        v_lst = v_lst1 + v_lst2
        # print(f'{v_lst = }')
        for v in v_lst:
            # print(f'tv_init(): {t = }, {v = }')
            yield t, v


def tpv_init(m):  # initialize TPH set (t, p, v) of vintage periods with t-th capacities available at period p
    for t in m.T:
        for p in m.P:
            # print(f'tpv_init(): {t = }, life[t] = {m.life[t]}')
            for i in range(0, m.life[t] + 1):   # vintage period: current p and life[t] previous
                v = p - i
                # print(f'th_init(): {t = },  {p = }, {t = }, {v = }')
                yield t, p, v


# generator of v (vintage periods) for pp (planning period); the pairs stored in the Vp set (V_p)
# filter values: None (yield all), neg (yield only negative v), nonneg (yield only non-negative v)
def vtp_lst(mx, tt, pp, filt=None):
    # el_lst = mx.TPV.value_list    # el_lst: list of (t, p, v) tuples
    for t, p, v in mx.TPV:
        if tt == t and p == pp:
            # print(f'vtp_lst: {tt = }, {t = }, {pp = }, {p = }, {v = }')
            if filt is None:
                yield v
            elif filt == 'neg':
                if v < 0:
                    yield v
            elif filt == 'nonneg':
                if v >= 0:
                    yield v
            else:
                raise Exception(f'Unknown value of param filt in vtp_lst(): {filt}.')


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
    m: AbstractModel = pe.AbstractModel(name='pipa 1.2.3')  # PTX added, inputs/outputs to/from technologies
    # sets
    # subsets(expand_all_set_operators=True)  explore this to avoid warnings
    m.T = pe.Set()     # all technologies
    m.GT = pe.Set()    # subset of GreenFuel technologies (BTL + PTX)
    m.XT = pe.Set()    # subset of PTX technologies (PTX) currently the only to capture CO2
    m.periods = pe.Param(domain=pe.PositiveIntegers, default=3)   # number of planning periods
    # noinspection PyTypeChecker
    # warning: pe.Param used instead of expected int (but a cast to the latter cannot be used in Abstract model)
    m.periods_ = pe.Param(initialize=m.periods-1)   # index of the last planning periods
    m.P = pe.RangeSet(0, m.periods_)  # set of periods; NOTE: RangeSet(0, 1) has two elements, RangeSet(0, -1) is empty
    # life-time, i.e., number of periods capacity remains available after the vintage period
    m.life = pe.Param(m.T, within=pe.NonNegativeIntegers, default=0)    # life-time of cap after vintage period
    m.TH = pe.Set(dimen=2, initialize=th_init)  # (t, v): prior to p=0 vintage periods of capacity of t-th techn.
    m.TV = pe.Set(dimen=2, initialize=tv_init)  # (t, v): all vintage periods of capacity of t-th techn.
    m.TPV = pe.Set(dimen=3, initialize=tpv_init)  # (t, p, v) of vintages available for t=th techn. at period p
    m.J = pe.Set()     # inputs to technologies
    m.K = pe.Set()     # outputs from technologies (products, commodities) to cover demand or to  be used as inputs

    # decision variables
    # m.act = Var(m.T, m.V, m.P, within=NonNegativeReals)   # activity level; this specs generates full/dense act matrix
    m.act = pe.Var(m.TPV, within=pe.NonNegativeReals)  # activity level act[t, (p, v)]
    m.cap = pe.Var(m.T, m.P, within=pe.NonNegativeReals)   # newly installed capacity cap[t, p]

    # outcome variables
    m.cost = pe.Var()   # total cost, single-crit objective for the regret-function app.
    m.carbC = pe.Var()   # cost of the total carbon emission
    m.carb = pe.Var()   # total carbon emission
    m.carbCap = pe.Var()   # total carbon captured
    m.carbBal = pe.Var()   # total carbon (emission - captured)
    m.oilImp = pe.Var()   # total amount of imported oil
    m.water = pe.Var()   # total water used
    m.greenFTot = pe.Var()   # total green fuel produced
    # auxiliary variables, trajectories of amounts
    m.inp = pe.Var(m.T, m.P, m.J, within=pe.NonNegativeReals)   # amounts of inputs of each technology
    m.inpT = pe.Var(m.P, m.J, within=pe.NonNegativeReals)   # amounts of inputs by all technologies
    m.out = pe.Var(m.T, m.P, m.K, within=pe.NonNegativeReals)   # amounts of outputs
    m.carbE = pe.Var(m.T, m.P, within=pe.NonNegativeReals)   # carbon emissions (caused by act covering demand[p]
    m.greenF = pe.Var(m.P, m.K, within=pe.NonNegativeReals)  # green fuel produced
    # auxiliary variables, trajectories of costs
    m.inpC = pe.Var(m.T, m.P, within=pe.NonNegativeReals)   # cost of all inputs
    # m.outC = pe.Var(m.T, m.P, m.K, within=pe.NonNegativeReals)   # value of outputs (undefined, not used)
    m.invC = pe.Var(m.T, m.P, within=pe.NonNegativeReals)   # trajectories of investment costs
    m.omcC = pe.Var(m.T, m.P, within=pe.NonNegativeReals)   # trajectories of OMC (raw-materials excluded)
    m.carbPC = pe.Var(m.T, m.P, within=pe.NonNegativeReals)   # trajectories of carbon emission costs
    m.costAn = pe.Var(m.T, m.P, within=pe.NonNegativeReals)   # trajectories of total costs
    #
    # secondary auxiliary variables
    m.invT = pe.Var()   # total investments
    m.excarbC = pe.Var()   # total cost excludidng carbon emission cost
    m.carbEv = pe.Var(m.TV, within=pe.NonNegativeReals)   # carbon emissions (by act[t, p, v]) caused by cap[v]
    m.actvS = pe.Var(m.T, m.P, within=pe.NonNegativeReals)  # activities summed over v act[t, p]
    m.actS = pe.Var(m.T, within=pe.NonNegativeReals)  # total activities (i.e., summed over v and p act[t])
    m.capAv = pe.Var(m.T, m.P, within=pe.NonNegativeReals)  # avail. capacities
    m.capIdle = pe.Var(m.T, m.P, within=pe.NonNegativeReals)  # idle capacities
    m.capIdleS = pe.Var(m.T, within=pe.NonNegativeReals)  # total idle capacities
    m.capTot = pe.Var(m.T, within=pe.NonNegativeReals)  # total capacities (i.e., all cap-investments in techn. t)
    #

    # objectives: three defined for MCA, only one activated here at a time
    # TODO: clarify error (reported in model display): ERROR: evaluating object as numeric value: goal
    '''
    @m.Objective(sense=pe.minimize)
    def goalmin(mx):
        # return mx.cost      # total cost
        # return mx.carbBal    # total carbon emission
        return mx.water   # total water used
        # return mx.carb    # total carbon emission
        # return mx.invT      # total investments
        # return mx.oilImp  # total oil import  (same/similar solution as carb min.)
    '''
    @m.Objective(sense=pe.maximize)
    def goalmax(mx):
        return mx.greenFTot   # total green fuel produced
        # return mx.carbCap   # total carbon captured

    # parameters  (declared in the sequence corresponding to their use in SMS)
    m.discr = pe.Param(within=pe.NonNegativeReals, default=0.04)   # discount rate (param used in calculating m.dis)
    m.dis = pe.Param(m.P, mutable=True, within=pe.NonNegativeReals, default=.9)  # cumulated discount, see mod_instance
    #
    m.dem = pe.Param(m.P, m.K, within=pe.NonNegativeReals, default=0.0)   # given demand
    m.inpU = pe.Param(m.T, m.J, within=pe.NonNegativeReals, default=1.0)  # input use per prod.-unit
    m.outU = pe.Param(m.T, m.K, within=pe.NonNegativeReals, default=1.0)  # output per unit activity
    m.hcap = pe.Param(m.TH, within=pe.NonNegativeReals, default=0.0)  # capacities installed in historical periods
    m.cuf = pe.Param(m.T, within=pe.NonNegativeReals, default=0.8)         # capacity utilization factor
    m.ef = pe.Param(m.T, within=pe.NonNegativeReals, default=1.0)       # unit carbon emission
    m.ccf = pe.Param(m.XT, within=pe.NonNegativeReals, default=0.0)     # unit carbon capture
    m.watf = pe.Param(m.T, within=pe.NonNegativeReals, default=1.0)     # unit water use
    m.inpP = pe.Param(m.J, within=pe.NonNegativeReals, mutable=True, default=1.0)   # unit cost of input
    m.invP = pe.Param(m.T, within=pe.NonNegativeReals, default=1.0)     # unit inv cost
    m.omcP = pe.Param(m.T, within=pe.NonNegativeReals, default=1.0)     # unit OMC cost (excl. inputs)
    m.carbP = pe.Param(within=pe.NonNegativeReals, mutable=True, default=1.0)   # unit carbon-emission cost

    # Relations
    @m.Constraint(m.P, m.K)  # output from activities of all techn. to cover demand at each period for each output
    def demC(mx, p, k):
        # exp = sum(mx.outU[t, k] * sum(mx.act[t, p, v] for v in vp_lst(mx, p)) for t in mx.T)  # output from activities
        # exp = sum(mx.outU[t, k] * sum(mx.act[t, p, v] for v in vtp_lst(mx, t, p)) for t in mx.T)  # output from activ.
        exp = sum(mx.outU[t, k] * mx.actvS[t, p] for t in mx.T)  # output from activ.
        return mx.dem[p, k], exp, None

    @m.Constraint(m.P, m.K)  # green fuel trajectory (output from XT technologies)
    def greenFC(mx, p, k):
        exp = sum(mx.outU[t, k] * mx.actvS[t, p] for t in mx.GT)  # green fuel from activ. of GT technology
        return mx.greenF[p, k] == exp

    @m.Constraint(m.P, m.K)  # green fuel max (needed for greenFTot selfish optimization)
    def greenFmxC(mx, p, k):
        return 0., mx.greenF[p, k], mx.dem[p, k]

    @m.Constraint()  # total green fuel
    def greenFTC(mx):
        exp = sum(sum(mx.greenF[p, k] for p in mx.P) for k in mx.K)  # sum of periods and fuel types
        return mx.greenFTot == exp

    @m.Constraint()  # total carbon captured (only by XT technologies)
    def carbCapC(mx):
        return mx.carbCap == sum(mx.ccf[t] * sum(mx.actvS[t, p] for p in mx.P) for t in mx.XT)

    @m.Constraint()  # total carbon balance (emission - captured)
    def carbBalC(mx):
        return mx.carbBal == mx.carb - mx.carbCap

    @m.Constraint()  # total water used
    def waterC(mx):
        return mx.water == sum(mx.watf[t] * sum(mx.actvS[t, p] for p in mx.P) for t in mx.T)

    @m.Constraint(m.TPV)  # activity cannot exceed the corresponding (cuf * capacity)
    def actC(mx, t, p, v):
        # print(f'pcap_rule: t {t}, p {p}, v {v}')
        if v < 0:  # act constrained by (given) historical capacity at each relevant v
            return pe.inequality(0., mx.act[t, p, v], mx.cuf[t] * mx.hcap[t, v])
        else:  # act constrained by (decision variable) new capacity at each relevant v
            exp1 = mx.cuf[t] * mx.cap[t, v] - mx.act[t, p, v]
            return pe.inequality(0., exp1, None)

    @m.Constraint(m.T, m.P, m.J)  # total amounts of j-th input needed by t-th technology at period p
    def inpD(mx, t, p, j):
        return mx.inp[t, p, j] == mx.inpU[t, j] * sum(mx.act[t, p, v] for v in vtp_lst(mx, t, p))

    @m.Constraint(m.P, m.J)  # total amounts of j-th input needed by all technologies at period p
    def inpTD(mx, p, j):
        return mx.inpT[p, j] == sum(mx.inp[t, p, j] for t in mx.T)

    @m.Constraint(m.T, m.P)  # trajectory of inv cost for building capacities (in planning periods)
    def invCD(mx, t, p):
        return mx.invC[t, p] == mx.invP[t] * mx.cap[t, p]

    @m.Constraint()  # total investments
    def invTD(mx):
        return mx.invT == sum(mx.invC[t, p] for t in mx.T for p in mx.P)

    @m.Constraint(m.T, m.P)  # trajectory of costs of all inputs to each technology
    def inpCD(mx, t, p):
        return mx.inpC[t, p] == sum(mx.inpP[j] * mx.inp[t, p, j] for j in mx.J)

    @m.Constraint(m.T, m.P)  # OMC (excl. inputs) of all (available at $p$-th period) capacities
    def omcCD(mx, t, p):
        caph = 0.   # historical capacities
        capn = 0.   # new capacities
        for v in vtp_lst(mx, t, p):
            if v < 0:
                caph += mx.hcap[t, v]
            else:
                capn += mx.cap[t, v]
        return mx.omcC[t, p] == mx.omcP[t] * (caph + capn)

    @m.Constraint(m.T, m.P)    # trajectory of amounts of carbon emissions caused by covering dem[p]
    def carbED(mx, t, p):
        return mx.carbE[t, p] == sum(mx.ef[t] * mx.act[t, p, v] for v in vtp_lst(mx, t, p))

    @m.Constraint(m.T, m.P)    # trajectory of costs of carb emissions
    def carbPCD(mx, t, p):
        # the old/commented code double-counts carbE[t, v] in costs
        # return mx.carbC[t, p] == mx.carbP * sum(mx.carbE[t, v] for v in vp_lst(mx, p))
        return mx.carbPC[t, p] == mx.carbP * mx.carbE[t, p]

    @m.Constraint(m.T, m.P)    # trajectory of annual cost
    def costAD(mx, t, p):
        return mx.costAn[t, p] == mx.invC[t, p] + mx.inpC[t, p] + mx.omcC[t, p] + mx.carbPC[t, p]

    @m.Constraint()    # discounted total cost
    def costD(mx):
        # todo: clarify impacts of dis[p] in the three definitions below
        #   also how to correctly compute compound params; use default, from data, and computed
        return mx.cost == sum(mx.dis[p] * sum(mx.costAn[t, p] for t in mx.T) for p in mx.P)
        # return mx.cost == sum(mx.dis[p].value * sum(mx.costAn[t, p] for t in mx.T) for p in mx.P)  # garbage?
        # return mx.cost == sum(sum(mx.costAn[t, p] for t in mx.T) for p in mx.P)  # undiscounted

    @m.Constraint()    # total carb emission
    def carbD(mx):
        return mx.carb == sum(sum(mx.carbE[t, p] for p in mx.P) for t in mx.T)

    @m.Constraint()  # total imported crude-oil
    def oilImpD(mx):
        return mx.oilImp == sum(mx.inpT[p, 'crude'] for p in mx.P)

    @m.Constraint()  # the total (discounted) carbon emission cost
    def carbCD(mx):
        # return mx.carbC == mx.carbP * mx.carb
        return mx.carbC == mx.carbP * sum(mx.dis[p] * sum(mx.carbE[t, p] for t in mx.T) for p in mx.P)

    #
    # auxiliary relations follow:
    @m.Constraint()  # total (discointed) costs excl. carbon emission cost
    def excarbCD(mx):
        return mx.excarbC == mx.cost - mx.carbC

    @m.Constraint(m.TV)    # trajectory of amounts of carbon emissions caused by cap[t, v]
    def carbEDv(mx, t, v):
        # print(f'carbEDv start: t = {t}, v = {v} ------------------------------ ')
        sum_act = 0.  # sum act[t, p, v] for all p using act[*, p, v] (v - given)
        for tt, p, vv in mx.TPV:
            if tt == t and v == vv:
                sum_act += mx.act[t, p, v]
                # print(f'carbEDv: {tt = }, {t = }, {p = }, {vv = }, {v = }, sum changed = {sum_act}')
        # print(f'carbEDv: t = {t}, v = {v}, sum_act = {sum_act} ------------------------------ ')
        return mx.carbEv[t, v] == mx.ef[t] * sum_act

    @m.Constraint(m.T, m.P)  # sum of activities [t] covering demand[p]
    def actvSD(mx, t, p):
        return mx.actvS[t, p] == sum(mx.act[t, p, v] for v in vtp_lst(mx, t, p))

    @m.Constraint(m.T)  # sum of activities [t] covering demand over all [p]
    def actSD(mx, t):
        return mx.actS[t] == sum(mx.actvS[t, p] for p in mx.P)

    @m.Constraint(m.T, m.P)  # sum_v cuf[t] * cap[v] for covering demand[p] by techn. [t]
    def capAvD(mx, t, p):
        capsum = 0.
        for v in vtp_lst(mx, t, p):
            if v < 0:
                capsum += mx.cuf[t] * mx.hcap[t, v]
            else:
                capsum += mx.cuf[t] * mx.cap[t, v]
        return mx.capAv[t, p] == capsum

    @m.Constraint(m.T, m.P)  # idle (unused) capacities
    def capIdlD(mx, t, p):
        return mx.capIdle[t, p] == mx.capAv[t, p] - mx.actvS[t, p]

    @m.Constraint(m.T)  # sum (over all periods) of idle capacities
    def capIdlSD(mx, t):
        return mx.capIdleS[t] == sum(mx.capIdle[t, p] for p in mx.P)

    @m.Constraint(m.T)  # sum (over all periods) of new capacities (excl. historical)
    def capTotD(mx, t):
        return mx.capTot[t] == sum(mx.cap[t, p] for p in mx.P)

    print('mk_sms(): finished')
    # m.display()   # does not work for abstract models
    # m.pprint()    # does not work (needs lengths of sets)
    return m

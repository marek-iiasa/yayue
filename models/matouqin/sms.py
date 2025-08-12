"""
sms(): returns the Symbolic model specification (SMS), i.e., the Abstract Model of the Matouqin model.
All functions used in the m model are defined before mk_sms() to avoid warnings "m shadows name from outer scope".
"""

import pyomo.environ as pe      # more robust than using import *


# noinspection PyTypeChecker
class SMS:
    def __init__(self):
        # create abstract model
        m = pe.AbstractModel(name='Matouqin v. 1.0')   # instance of the concrete model
        self.m = m
        # print(f'Generating AbstractModel model for parameters (version: {p.ver}')

        # declare sets, variables, parameters
        self.sets()
        self.vars()
        self.params()

        # define relations
        # 1) common relations
        self.flow_Cons()        # relations for common energy flow connections
        self.outc_Cons()        # relations defining outcome variables
        self.aux_Cons()         # relations defining auxiliary variables

        # 2) HESS relations
        self.E2X_Cons()         # E2X relations
        self.stor_Cons()        # storage device relations
        self.X2E_Cons()         # X2E relations

        # 3) Objective
        @m.Objective(sense=pe.maximize)
        def obj(mx):
            return mx.revenue

        # self.m.pprint()  # does not work (needs lengths of sets)
        print('mk_sms(): finished')

    def sets(self):
        m = self.m

        # noinspection typeInspection
        m.nHrs = pe.Param(domain=pe.PositiveIntegers)  # the number of time periods
        m.nHrs_ = pe.Param(initialize=m.nHrs - 1)  # index of the last time periods
        m.T = pe.RangeSet(0, m.nHrs_)  # set of time periods
        m.Th = pe.RangeSet(-1, m.nHrs_)  # set of time periods (including initial state 't = -1')

        # noinspection SpellCheckingInspection
        m.R = pe.Set()        # set of energy storage systems (ESSs)
        m.E = pe.Set(m.R)     # set of E2X converter types
        m.S = pe.Set(m.R)     # set of storage device types
        m.X = pe.Set(m.R)     # set of X2E converter types

        # flatten indexed sets
        def re_rule(ms):
            return ((r, e) for r in ms.R for e in ms.E[r])

        def rs_rule(ms):
            return ((r, s) for r in ms.R for s in ms.S[r])

        def rx_rule(ms):
            return ((r, x) for r in ms.R for x in ms.X[r])

        m.E_ = pe.Set(dimen=2, initialize=re_rule)     # flattened (r,e) pairs
        m.S_ = pe.Set(dimen=2, initialize=rs_rule)     # flattened (r,s) pairs
        m.X_ = pe.Set(dimen=2, initialize=rx_rule)     # flattened (r,x) pairs

    def vars(self):
        m = self.m
        # define variables needed for demonstrating decorators
        # 1) decision variables
        m.eNum = pe.Var(m.E_, within=pe.NonNegativeIntegers)  # number of units of s-th storage device.
        m.sNum = pe.Var(m.S_, within=pe.NonNegativeIntegers)      # number of units of s-th storage device.
        m.xNum = pe.Var(m.X_, within=pe.NonNegativeIntegers)  # number of units of s-th storage device.
        # m.sNum = pe.Var(m.P, within=pe.NonNegativeIntegers, bounds=(0, 500))   # bounds on int vars required by cplex.
        m.supply = pe.Var()       # amount of energy committed to be provided in each time period, [MW].

        # 2) control variables
        m.eOut = pe.Var(m.T, within=pe.NonNegativeReals)    # electricity covering the committed supply, [MWh].
        m.eS = pe.Var(m.T, within=pe.NonNegativeReals)      # electricity surplus, [MWh].

        m.eIne = pe.Var(m.E_, m.T, within=pe.NonNegativeReals)   # electricity to e-th E2X converter, [MWh].
        m.eIns = pe.Var(m.S_, m.T, within=pe.NonNegativeReals)   # electricity to s-th storage device, [MWh].
        m.xOute = pe.Var(m.E_, m.T, within=pe.NonNegativeReals)  # energy form from e-th E2X converter.
        m.xIns = pe.Var(m.S_, m.T, within=pe.NonNegativeReals)   # energy form inflow to s-th storage device.
        m.xVol = pe.Var(m.S_, m.Th, within=pe.NonNegativeReals)   # energy form stored in s-th storage device.
        m.xOuts = pe.Var(m.S_, m.T, within=pe.NonNegativeReals)  # energy form outflow from s-th storage device.
        m.xInx = pe.Var(m.X_, m.T, within=pe.NonNegativeReals)  # energy form inflow to x-th X2E converter.
        m.eOutx = pe.Var(m.X_, m.T, within=pe.NonNegativeReals)  # energy form outflow from x-th X2E converter.
        m.eB = pe.Var(m.T, within=pe.NonNegativeReals)        # electricity purchase on the market, [MWh].

        # 3)outcome variables
        m.income = pe.Var(within=pe.Reals)      # annual income from providing the committed supply.
        m.storCost = pe.Var(within=pe.Reals)    # annual cost of HESS.
        m.invCost = pe.Var(within=pe.Reals)     # annualized investment cost of HESS.
        m.OMC = pe.Var(within=pe.Reals)         # annual operation and maintenance costs of HESS.
        m.balCost = pe.Var(within=pe.Reals)     # annual management cost of electricity surplus and shortage.
        m.splsCost = pe.Var(within=pe.Reals)    # annual electricity surplus cost.
        m.buyCost = pe.Var(within=pe.Reals)     # annual electricity purchase cost.
        m.revenue = pe.Var(within=pe.Reals)     # annual revenue of the system.

        # 4)auxiliary variables
        m.eCap = pe.Var(m.E_, within=pe.NonNegativeReals)  # total capacity of e-th type of E2X converter.
        m.sCap = pe.Var(m.S_, within=pe.NonNegativeReals)  # total capacity of s-th type of storage device.
        m.xCap = pe.Var(m.X_, within=pe.NonNegativeReals)  # total capacity of x-th type of X2E converter.
        m.eInHess = pe.Var(m.T, within=pe.NonNegativeReals)    # electricity inflow to HESS, [MWh].
        m.eOutHess = pe.Var(m.T, within=pe.NonNegativeReals)  # electricity outflow from HESS, [MWh].
        m.eInr = pe.Var(m.R, m.T, within=pe.NonNegativeReals)  # electricity inflow to r-th ESS, [MWh].
        m.eOutr = pe.Var(m.R, m.T, within=pe.NonNegativeReals)  # electricity outflow from r-th ESS, [MWh].
        m.eIneSum = pe.Var(m.R, m.T, within=pe.NonNegativeReals)  # electricity slit to all E2X in r-th ESS, [MWh].
        m.eInsSum = pe.Var(m.R, m.T, within=pe.NonNegativeReals)  # electricity slit to all storage in r-th ESS, [MWh].
        m.xIn = pe.Var(m.R, m.T, within=pe.NonNegativeReals)  # energy form produced by all E2X converters in r-th ESS.
        m.xOut = pe.Var(m.R, m.T, within=pe.NonNegativeReals)  # energy form from all storage devices in r-th ESS.
        m.xMxIn = pe.Var(m.S_, within=pe.NonNegativeReals)   # maximum energy form inflow to s-th storage device.
        m.xMxOut = pe.Var(m.S_, within=pe.NonNegativeReals)  # maximum energy form from s-th storage device.
        m.xInit = pe.Var(m.S_, within=pe.NonNegativeReals)    # total amount of initial energy form in storge.
        m.eSurplus = pe.Var(within=pe.NonNegativeReals)                   # annual electricity surplus, [MWh].
        m.eBought = pe.Var(within=pe.NonNegativeReals)                    # annual electricity purchase, [MWh].
        m.rInv = pe.Var(m.R, within=pe.NonNegativeReals)          # annual investment cost of r-th ESS, k-CNY.
        m.rOMC = pe.Var(m.R, within=pe.NonNegativeReals)          # annual OMC of r-th ESS, k-CNY.

    # define parameters
    def params(self):
        m = self.m

        m.intv = pe.Param(domain=pe.NonNegativeReals)                         # duration time in one period, [hrs].
        m.inflow = pe.Param(m.T, domain=pe.NonNegativeReals)          # amount of electricity incoming to the site.

        m.emxCap = pe.Param(m.E_, domain=pe.NonNegativeReals)      # unit capacity of an E2X converter, MW.
        m.smxCap = pe.Param(m.S_, domain=pe.NonNegativeReals)  # unit capacity of a storage device, MW/others.
        m.xmxCap = pe.Param(m.X_, domain=pe.NonNegativeReals)  # unit capacity of a X2E converter, MW/others.

        m.e2x = pe.Param(m.E_, domain=pe.NonNegativeReals)     # E2X conversion factor, [xxx/MWh].
        m.e2s = pe.Param(m.S_, domain=pe.NonNegativeReals)     # electricity consumption factor, [MWh/xxx].
        m.mxsIn = pe.Param(m.S_, domain=pe.NonNegativeReals)   # maximum energy form inflow to the storage device.
        m.mxsOut = pe.Param(m.S_, domain=pe.NonNegativeReals)  # maximum energy form from the storage device.
        m.sini = pe.Param(m.S_, domain=pe.NonNegativeReals)    # percentage of initial energy form in device.
        m.xRes = pe.Param(m.S_, domain=pe.NonNegativeReals)    # energy form retention rate.
        m.xCh = pe.Param(m.S_, domain=pe.NonNegativeReals)     # charging efficiency.
        m.xDis = pe.Param(m.S_, domain=pe.NonNegativeReals)    # discharging efficiency.
        m.x2e = pe.Param(m.X_, domain=pe.NonNegativeReals)     # X2E conversion factor, [MWh/xxx]

        m.ePrice = pe.Param(domain=pe.NonNegativeReals)             # electricity annual contract price, [k~CNY/MWh].
        m.eBprice = pe.Param(domain=pe.NonNegativeReals)            # electricity purchase price, [k~CNY/MWh].
        m.eSprice = pe.Param(domain=pe.Reals)                       # electricity surplus price, [k~CNY].

        m.eInv = pe.Param(m.E_, domain=pe.NonNegativeReals)  # annual investment cost of an E2X converter, [k~CNY].
        m.sInv = pe.Param(m.S_, domain=pe.NonNegativeReals)  # annual  investment cost of a storage device, [k~CNY].
        m.xInv = pe.Param(m.X_, domain=pe.NonNegativeReals)  # annual  investment cost of a X2E converter, [k~CNY].
        m.eOMC = pe.Param(m.E_, domain=pe.NonNegativeReals)  # annual  OMC of an E2X converter, [k~CNY].
        m.sOMC = pe.Param(m.S_, domain=pe.NonNegativeReals)  # annual  OMC of a storage device, [k~CNY].
        m.xOMC = pe.Param(m.X_, domain=pe.NonNegativeReals)  # annual  OMC of a X2E converter, [k~CNY].

    # relations for processes (E2X, storage, X2E) connections
    def flow_Cons(self):
        m = self.m

        # inflow relations
        @m.Constraint(m.T)          # energy inflow is divided into 3 energy flows
        def inflowBal(mx, t):
            return mx.inflow[t] == mx.eOut[t] + mx.eInHess[t] + mx.eS[t]

        # supply relations
        @m.Constraint(m.T)      # committed supply is composed of three parts: direct, storage, purchase
        def supplyBal(mx, t):
            return mx.supply == mx.eOut[t] + mx.eOutHess[t] + mx.eB[t]

        # energy flow relations between processes
        @m.Constraint(m.T)     # total electricity to the storage system is split between different storage systems
        def eInHessC(mx, t):
            return mx.eInHess[t] == sum(mx.eInr[r, t] for r in mx.R)

        @m.Constraint(m.T)      # total electricity from storage system is defined by the sum of outflows from each ESS
        def eOutHessC(mx, t):
            return mx.eOutHess[t] == sum(mx.eOutr[r, t] for r in mx.R)

        @m.Constraint(m.R, m.T)     # flow connection in/out E2X process
        def EmptyE2X(mx, r, t):
            if mx.E[r]:
                return pe.Constraint.Skip
            return mx.eInr[r, t] == mx.xIn[r, t]

        @m.Constraint(m.R, m.T)     # flow connection through empty storage device
        def EmptyS(mx, r, t):
            if mx.S[r]:
                return pe.Constraint.Skip
            return mx.xIn[r, t] == mx.xOut[r, t]

        @m.Constraint(m.R, m.T)     # flow connection through empty X2E converter
        def EmptyX2E(mx, r, t):
            if mx.X[r]:
                return pe.Constraint.Skip
            return mx.xOut[r, t] == mx.eOutr[r, t]

    # relations defining outcome variables
    def outc_Cons(self):
        m = self.m

        @m.Constraint()     # income from supplying
        def incomeC(mx):
            return mx.income == mx.ePrice * mx.supply

        @m.Constraint()     # annual cost of all storage system
        def storCostC(mx):
            return mx.storCost == mx.invCost + mx.OMC

        @m.Constraint()     # annualized investment cost of HESS
        def invCostC(mx):
            return mx.invCost == sum(mx.rInv[r] for r in mx.R)

        @m.Constraint(m.R)  # annualized investment cost of r-th ESS
        def rInvC(mx, r):
            return (mx.rInv[r] == sum(mx.eInv[r, e] * mx.eNum[r, e] for e in mx.E[r])
                    + sum(mx.sInv[r, s] * mx.sNum[r, s] for s in mx.S[r])
                    + sum(mx.xInv[r, x] * mx.xNum[r, x] for x in mx.X[r]))

        @m.Constraint()     # operation and maintenance cost of HESS
        def OMCC(mx):
            return mx.OMC == sum(mx.rOMC[r] for r in mx.R)

        @m.Constraint(m.R)  # annualized investment cost of r-th ESS
        def rOMCC(mx, r):
            return (mx.rOMC[r] == sum(mx.eOMC[r, e] * mx.eNum[r, e] for e in mx.E[r])
                    + sum(mx.sOMC[r, s] * mx.sNum[r, s] for s in mx.S[r])
                    + sum(mx.xOMC[r, x] * mx.xNum[r, x] for x in mx.X[r]))

        @m.Constraint()     # cost of balancing surplus and purchase
        def balCostC(mx):
            return mx.balCost == mx.splsCost + mx.buyCost

        @m.Constraint()     # cost of handling surplus
        def splsCostC(mx):
            return mx.splsCost == mx.eSprice * mx.eSurplus

        @m.Constraint()     # cost of handling purchase
        def buyCostC(mx):
            return mx.buyCost == mx.eBprice * mx.eBought

        @m.Constraint()     # total revenue of the system
        def revenueC(mx):
            return mx.revenue == mx.income - mx.storCost - mx.balCost

    # relations defining auxiliary variables
    def aux_Cons(self):
        m = self.m

        @m.Constraint(m.E_)  # total capacity of e-type E2X converter
        def eCapC(mx, r, e):
            return mx.eCap[r, e] == mx.emxCap[r, e] * mx.eNum[r, e]

        @m.Constraint(m.S_)  # total capacity of s-type storage device
        def sCapC(mx, r, s):
            return mx.sCap[r, s] == mx.smxCap[r, s] * mx.sNum[r, s]

        @m.Constraint(m.X_)  # total capacity of x-type X2E converter
        def xCapC(mx, r, x):
            return mx.xCap[r, x] == mx.xmxCap[r, x] * mx.xNum[r, x]

        @m.Constraint(m.S_)  # maximum X inflow to s-th storage device
        def xMxInC(mx, r, s):
            return mx.xMxIn[r, s] == mx.intv * mx.mxsIn[r, s] * mx.sNum[r, s]

        @m.Constraint(m.S_)  # maximum X outflow from s-th storage device
        def xMxOutC(mx, r, s):
            return mx.xMxOut[r, s] == mx.intv * mx.mxsOut[r, s] * mx.sNum[r, s]

        @self.m.Constraint(m.S_)  # initial energy carrier in s-th container
        def xInitC(mx, r, s):
            return mx.xInit[r, s] == mx.sini[r, s] * mx.sCap[r, s]

        @m.Constraint()             # annual amount of electricity surplus
        def eSurplusBal(mx):
            return mx.eSurplus == sum(mx.eS[t] for t in mx.T)

        @m.Constraint()             # annual amount of electricity purchase
        def eBoughtBal(mx):
            return mx.eBought == sum(mx.eB[t] for t in mx.T)

    # E2X relations
    def E2X_Cons(self):
        m = self.m

        @m.Constraint(m.R, m.T)  # electricity to an ESS split by flows to E2X and storage device
        def eInrC(mx, r, t):
            if not mx.E[r]:
                return pe.Constraint.Skip
            return mx.eInr[r, t] == mx.eIneSum[r, t] + mx.eInsSum[r, t]

        @m.Constraint(m.R, m.T)  # electricity used for E2X conversion
        def eIneSumC(mx, r, t):
            if not mx.E[r]:      # skip constraint for ESS with no E2X converter
                return pe.Constraint.Skip
            return mx.eIneSum[r, t] == sum(mx.eIne[r, e, t] for e in mx.E[r])

        @m.Constraint(m.E_, m.T)  # all inflow to E2X converters <= sum of their processing capability
        def eIneC(mx, r, e, t):
            return mx.eIne[r, e, t] <= mx.intv * mx.eCap[r, e]

        @m.Constraint(m.E_, m.T)  # x converted from e-th E2X converter
        def xOuteC(mx, r, e, t):
            return mx.xOute[r, e, t] == mx.e2x[r, e] * mx.eIne[r, e, t]

        @m.Constraint(m.R, m.T)  # the amount of x produced by all E2X converters
        def XIn1(mx, r, t):
            if not mx.E[r]:
                return pe.Constraint.Skip
            return mx.xIn[r, t] == sum(mx.xOute[r, e, t] for e in mx.E[r])

    # storage device relations
    def stor_Cons(self):
        m = self.m

        @m.Constraint(m.R, m.T)  # produced X is split between storage devices
        def XIn2(mx, r, t):
            if not mx.S[r]:
                return pe.Constraint.Skip
            return mx.xIn[r, t] == sum(mx.xIns[r, s, t] for s in mx.S[r])

        @m.Constraint(m.R, m.T)  # total amount of additional electricity used for storing X
        def eInsSumC(mx, r, t):
            return mx.eInsSum[r, t] == sum(mx.eIns[r, s, t] for s in mx.S[r])

        @m.Constraint(m.S_, m.T)  # additional electricity used for storing X in a storage device
        def eInsC(mx, r, s, t):
            return mx.eIns[r, s, t] == mx.e2s[r, s] * mx.xIns[r, s, t]

        @m.Constraint(m.S_, m.T)   # amount of X in x-th storage device
        def xVolC(mx, r, s, t):
            return (mx.xVol[r, s, t] == mx.xRes[r, s] * mx.xVol[r, s, (t - 1)]
                    + mx.xCh[r, s] * mx.xIns[r, s, t] - mx.xOuts[r, s, t] / mx.xDis[r, s])

        @m.Constraint(m.S_)  # amount of X at the first period
        def xVolSt(mx, r, s):
            return mx.xVol[r, s, -1] == mx.xInit[r, s]

        @m.Constraint(m.S_)  # amount of X at the last period
        def xVolEnd(mx, r, s):
            return mx.xVol[r, s, mx.nHrs_] == mx.xInit[r, s]

        # @m.Constraint(m.S_, m.T)    # lower and upper constraint of X in s-th storage device
        # def xVolBal(mx, r, s, t):
        #     return pe.inequality(0, mx.xVol[r, s, t], mx.sCap[r, s])

        @m.Constraint(m.S_, m.T)    # lower constraint of X in s-th storage device
        def xVolBal1(mx, r, s, t):
            return mx.xVol[r, s, t] >= 0

        @m.Constraint(m.S_, m.T)    # upper constraint of X in s-th storage device
        def xVolBal2(mx, r, s, t):
            return mx.xVol[r, s, t] <= mx.sCap[r, s]

        @m.Constraint(m.S_, m.T)   # maximum inflow to s-th storage device
        def xInsC(mx, r, s, t):
            return mx.xIns[r, s, t] <= mx.xMxIn[r, s]

        @m.Constraint(m.S_, m.T)  # maximum outflow from s-th storage device
        def xOutsC(mx, r, s, t):
            return mx.xOuts[r, s, t] <= mx.xMxOut[r, s]

        @m.Constraint(m.R, m.T)  # total X flow from all storage device
        def xOut1(mx, r, t):
            if not mx.S[r]:
                return pe.Constraint.Skip
            return mx.xOut[r, t] == sum(mx.xOuts[r, s, t] for s in mx.S[r])

    # X2E relations
    def X2E_Cons(self):
        m = self.m

        @m.Constraint(m.R, m.T)  # total X flow is split between X2E converters
        def xOut2(mx, r, t):
            if not mx.X[r]:
                return pe.Constraint.Skip
            return mx.xOut[r, t] == sum(mx.xInx[r, x, t] for x in mx.X[r])

        @m.Constraint(m.X_, m.T)  # electricity outflow from a X2E converter
        def eOutxC(mx, r, x, t):
            return mx.eOutx[r, x, t] == mx.x2e[r, x] * mx.xInx[r, x, t]

        @m.Constraint(m.X_, m.T)  # upper constraint of electricity outflow from a X2E converter
        def eOutxUp(mx, r, x, t):
            return mx.eOutx[r, x, t] <= mx.intv * mx.xCap[r, x]

        @m.Constraint(m.R, m.T)  # electricity from all X2E converters
        def eOutrC(mx, r, t):
            if not mx.X[r]:
                return pe.Constraint.Skip
            return mx.eOutr[r, t] == sum(mx.eOutx[r, x, t] for x in mx.X[r])

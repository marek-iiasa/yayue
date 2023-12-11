"""
sms(): returns the Symbolic model specification (SMS), i.e., the Abstract Model of the Matouqin model.
All functions used in the m model are defined before mk_sms() to avoid warnings "m shadows name from outer scope".
"""

import pyomo.environ as pe      # more robust than using import *


# noinspection PyTypeChecker
def mk_sms():      # p: model parameters prepared in the Params class
    m = pe.AbstractModel(name='Matouqin v. 0.1')   # instance of the concrete model
    # print(f'Generating AbstractModel model for parameters (version: {p.ver}')

    # print(f'Dictionary of prepared parameters contains  {len(p.cat)} items.')

    # print(f'xx = {p.xx}')

    # sets
    # noinspection SpellCheckingInspection
    m.Se = pe.Set()
    m.Sh = pe.Set()
    m.Sc = pe.Set()

    # noinspection ClassSet. The union function works.
    m.S = pe.Set(initialize=m.Se | m.Sh | m.Sc)
    # m.nHrs = pe.Param()
    # m.nHrs_ = pe.Param()
    m.nHrs = pe.Param(domain=pe.PositiveIntegers)       # the number of hours (time periods) in a year

    # noinspection typeInspection on line31
    m.nHrs_ = pe.Param(initialize=m.nHrs - 1)     # index of the last time periods (hour)
    m.T = pe.RangeSet(0, m.nHrs_)       # set of time periods (hour)

    # define variables needed for demonstrating decorators

    # decision variables
    m.sNum = pe.Var(m.S, within=pe.NonNegativeIntegers)      # number of units of s-th storage device
    m.supply = pe.Var()       # energy committed to be provided in each hour, [MWh]

    # todo: Variables check

    # control variables
    m.dOut = pe.Var(m.T, within=pe.NonNegativeReals)        # electricity directly meet the commitment, [MWh]
    m.sIn = pe.Var(m.T, within=pe.NonNegativeReals)     # electricity inflow redirected to storage, [MWh]
    m.ePrs = pe.Var(m.T, within=pe.NonNegativeReals)        # electricity used to make high pressure, [MWh]
    m.sOut = pe.Var(m.T, within=pe.NonNegativeReals)        # electricity from storage to meet commitment, [MWh]
    m.eIn = pe.Var(m.Se, m.T, within=pe.NonNegativeReals)       # electricity inflow to each electrolyzer,[MWh].
    m.eSurplus = pe.Var(m.T, within=pe.NonNegativeReals)        # the loss of electricity while overproduction.
    m.eBought = pe.Var(m.T, within=pe.NonNegativeReals)  # amount of electricity bought on the market
    m.hIn = pe.Var(m.Sh, m.T, within=pe.NonNegativeReals)       # hydrogen inflow to each hydrogen tank, [kg]
    m.hOut = pe.Var(m.Sh, m.T, within=pe.NonNegativeReals)      # hydrogen outflow from each hydrogen tank, [kg]
    m.hVol = pe.Var(m.Sh, m.T, within=pe.NonNegativeReals)      # amount of hydrogen stored in s-th device
    m.hInc = pe.Var(m.Sc, m.T, within=pe.NonNegativeReals)      # hydrogen inflow to each fuel cell, [kg]
    m.cOut = pe.Var(m.Sc, m.T, within=pe.NonNegativeReals)      # electricity outflow from each fuel cell, [MWh]

    # Outcome variables
    m.revenue = pe.Var(within=pe.Reals)     # the annual revenue of the system
    m.income = pe.Var(within=pe.Reals)      # the annual income from satisfying the commitment
    m.invCost = pe.Var(within=pe.Reals)     # the annualized investment cost of the storage system
    m.overCost = pe.Var(within=pe.Reals)    # the cost of management of surplus
    m.buyCost = pe.Var(within=pe.Reals)     # the cost of management of shortage
    m.balCost = pe.Var(within=pe.Reals)     # the cost of management of electricity surplus and shortage
    m.OMC = pe.Var(within=pe.Reals)     # the operation and maintenance costs

    # Auxiliary variables
    m.sCap = pe.Var(m.S, within=pe.NonNegativeReals)        # total capacity of ，总容量 s-th type of storage devices
    m.hMin = pe.Var(m.Sh, within=pe.NonNegativeReals)       # the lowest hydrogen needed in s-th type of tank
    m.mxIn = pe.Var(m.S, within=pe.NonNegativeReals)        # the maximum hydrogen inflow of s-th tank (per hour)
    m.mxOut = pe.Var(m.S, within=pe.NonNegativeReals)       # the maximum hydrogen outflow of s-th tank (per hour)
    m.h2T = pe.Var(m.T, within=pe.NonNegativeReals)     # total amount of hydrogen produced by all electrolyzer
    m.h2C = pe.Var(m.T, within=pe.NonNegativeReals)     # total amount of hydrogen from hydrogen tanks to fuel cells

    # parameters
    m.inflow = pe.Param(m.T, domain=pe.NonNegativeReals)     # amount of electricity incoming to the site
    m.mxCap = pe.Param(m.S, domain=pe.NonNegativeReals)     # unit storage capacity of each storage device
    m.hMxIn = pe.Param(m.Sh, domain=pe.NonNegativeReals)       # maximum hydrogen incoming to the tank [kg]
    m.hMxOut = pe.Param(m.Sh, domain=pe.NonNegativeReals)       # maximum hydrogen outflow from the tank [kg]
    m.hmi = pe.Param(m.Sh, domain=pe.NonNegativeReals)      # minimum hydrogen needed in hydrogen tank [kg]
    m.eh2 = pe.Param(m.Se, domain=pe.NonNegativeReals)      # converting electricity to hydrogen, [kg/MWh]
    m.eph2 = pe.Param(m.Sh, domain=pe.NonNegativeReals)     # making high pressure, [MWh/kg]
    m.h2Res = pe.Param(m.Sh, domain=pe.NonNegativeReals)        # hydrogen retention rate, unit in percentage
    m.h2e = pe.Param(m.Sc, domain=pe.NonNegativeReals)      # converting hydrogen to electricity [MWh/kg]
    # m.Hrs = pe.Param(domain=pe.NonNegativeIntegers)     # the during of decision time (hour)
    # m.ann = pe.Param(m.S, domain=pe.NonNegativeReals)       # annualization factor
    m.ePrice = pe.Param(domain=pe.NonNegativeReals)     # contract price
    m.eBprice = pe.Param(domain=pe.NonNegativeReals)     # purchase price of buying electricity, [million RMB/MW]
    m.eOver = pe.Param(domain=pe.NonNegativeReals)       # unit price of electricity surplus, [million RMB]
    m.sInv = pe.Param(m.S, domain=pe.NonNegativeReals)      # per unit investment cost of storage, [million RMB]
    m.sOmc = pe.Param(m.S, domain=pe.NonNegativeReals)       # per unit operation cost of storage, [million RMB]

    # Relations defining auxiliary variables
    @m.Constraint(m.S)     # Total capacity of s-th type of storage device
    def sCapC(mx, s):
        return mx.sCap[s] == mx.mxCap[s] * mx.sNum[s]

    @m.Constraint(m.Sh)      # Lowest amount of hydrogen needed in s-th of tank
    def hMinC(mx, s):
        return mx.hMin[s] == mx.hmi[s] * mx.sNum[s]

    @m.Constraint(m.Sh)     # Maximum hydrogen inflow of s-th tank (per hour)
    def mxInC(mx, s):
        return mx.mxIn[s] == mx.hMxIn[s] * mx.sNum[s]

    @m.Constraint(m.Sh)
    def mxOutC(mx, s):
        return mx.mxOut[s] == mx.hMxOut[s] * mx.sNum[s]

    @m.Constraint(m.T)
    def eSurplusC(mx, t):
        return mx.eSurplus[t] == mx.inflow[t] - mx.dOut[t] - mx.sIn[t] - mx.ePrs[t]

    @m.Constraint(m.T)
    def eBoughtC(mx, t):
        return mx.eBought[t] == mx.supply - mx.dOut[t] - mx.sOut[t]

    # relations defining energy flows
    @m.Constraint(m.T)      # energy inflow is divided into four energy flows
    def inflow_blc(mx, t):
        return mx.inflow[t] == mx.dOut[t] + mx.sIn[t] + mx.ePrs[t] + mx.eSurplus[t]

    @m.Constraint(m.T)      # total electricity used to store hydrogen equal to the sum of inflows to electrolyzers
    def sIn_blc(mx, t):
        return mx.sIn[t] == sum(mx.eIn[s, t] for s in mx.Se)

    @m.Constraint(m.Se, m.T)        # Inflows to all electrolyzers are constrained by the sum of their capacities
    def eIn_upper(mx, s, t):
        return mx.eIn[s, t] <= mx.sCap[s]

    @m.Constraint(m.T)      # The amount of hydrogen produced by all electrolyzers
    def h2t_blc1(mx, t):
        return mx.h2T[t] == sum(mx.eh2[s] * mx.eIn[s, t] for s in mx.Se)

    @m.Constraint(m.T)      # Produced hydrogen is split between tanks
    def h2t_blc2(mx, t):
        return mx.h2T[t] == sum(mx.hIn[s, t] for s in mx.Sh)

    @m.Constraint(m.T)      # The amount of electricity used for pressure control of all hydrogen tanks
    def ePrs_blc(mx, t):
        return mx.ePrs[t] == sum(mx.eph2[s] * mx.hIn[s, t] for s in mx.Sh)

    @m.Constraint(m.Sh, m.T)        # Amount of hydrogen in each tank type
    def hVol_bal(mx, s, t):
        if t == 0:
            return mx.hVol[s, t] == mx.hMin[s]
        else:
            return mx.hVol[s, t] == mx.h2Res[s] * mx.hVol[s, (t-1)] + mx.hIn[s, t] - mx.hOut[s, t]

    @m.Constraint(m.Sh, m.T)        # Amount of hydrogen in tanks of each type
    def hVol_lower(mx, s, t):
        return mx.hVol[s, t] >= mx.hMin[s]

    @m.Constraint(m.Sh, m.T)        # Amount of hydrogen in tanks of each type
    def hVol_upper(mx, s, t):
        return mx.hVol[s, t] <= mx.sCap[s]

    @m.Constraint(m.Sh, m.T)        # Maximum flow to each type of tank
    def hIn_upper(mx, s, t):
        return mx.hIn[s, t] <= mx.hMxIn[s]

    @m.Constraint(m.Sh, m.T)        # Maximum flow from each type of tank to fuel cells
    def hOut_upper(mx, s, t):
        return mx.hOut[s, t] <= mx.hMxOut[s]

    # @m.Constraint(m.Sh, m.T)      # Constraint on one tank cannot support inflow and outflow at the same time
    # def htankC(mx, s, t):
    #    return mx.hIn[s, t] * mx.hOut[s, t] == 0

    @m.Constraint(m.T)      # Hydrogen flow from tanks to all fuel cells
    def h2C_blc1(mx, t):
        return mx.h2C[t] == sum(mx.hOut[s, t] for s in mx.Sh)

    @m.Constraint(m.T)      # Hydrogen flow from tanks is split between fuel cells
    def h2C_blc2(mx, t):
        return mx.h2C[t] == sum(mx.hInc[s, t] for s in mx.Sc)

    @m.Constraint(m.T)      # The committed supply is composed of three parts
    def supply_blc(mx, t):
        return mx.supply == mx.dOut[t] + mx.sOut[t] + mx.eBought[t]

    @m.Constraint(m.T)      # electricity outflow from the storage is defined by the sum of outflows from fuel cells
    def sOut_blc(mx, t):
        return mx.sOut[t] == sum(mx.cOut[s, t] for s in mx.Sc)

    @m.Constraint(m.Sc, m.T)        # The electricity from fuel cells
    def cOut_blc(mx, s, t):
        return mx.cOut[s, t] == mx.h2e[s] * mx.hInc[s, t]

    @m.Constraint(m.Sc, m.T)        # The electricity outflow from the fuel cell
    def cOut_upper(mx, s, t):
        return mx.cOut[s, t] <= mx.sCap[s]

    # relations defining outcome variables
    @m.Constraint()     # Income from supplying
    def incomeC(mx):
        return mx.income == mx.ePrice * mx.nHrs * mx.supply

    @m.Constraint()     # Annualized investment cost of the storage system
    def invCostC(mx):
        return mx.invCost == sum(mx.sInv[s] * mx.sNum[s] for s in mx.S)

    @m.Constraint()     # Operation and maintenance cost of the storage system
    def OMCC(mx):
        return mx.OMC == sum(mx.sOmc[s] * mx.sNum[s] for s in mx.S)

    @m.Constraint()      # Cost of handling surplus
    def overCostC(mx):
        return mx.overCost == mx.eOver * sum(mx.eSurplus[t] for t in mx.T)

    @m.Constraint()  # Cost of handling surplus
    def buyCostC(mx):
        return mx.buyCost == mx.eBprice * sum(mx.eBought[t] for t in mx.T)

    @m.Constraint()     # Cost of balancing surplus and deficit
    def balCostC(mx):
        return mx.balCost == mx.overCost + mx.buyCost

    @m.Constraint()     # Total revenue of the system
    def revenueC(mx):
        return mx.revenue == mx.income - mx.invCost - mx.OMC - mx.balCost

    @m.Objective(sense=pe.maximize)     # Revenue (used as a Goal-Function/Objective in single-criterion analysis)
    def obj(mx):
        return mx.revenue

    print('mk_sms(): finished')
    # m.pprint()    # does not work (needs lengths of sets)

    return m

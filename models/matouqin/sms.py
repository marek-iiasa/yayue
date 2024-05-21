"""
sms(): returns the Symbolic model specification (SMS), i.e., the Abstract Model of the Matouqin model.
All functions used in the m model are defined before mk_sms() to avoid warnings "m shadows name from outer scope".
"""

import pyomo.environ as pe      # more robust than using import *


# noinspection PyTypeChecker
def mk_sms():      # p: model parameters prepared in the Params class
    m = pe.AbstractModel(name='Matouqin v. 0.1')   # instance of the concrete model
    # print(f'Generating AbstractModel model for parameters (version: {p.ver}')

    # sets
    # noinspection SpellCheckingInspection
    m.Se = pe.Set()     # set of electrolizers types
    m.Sh = pe.Set()     # set of hydrogen tanks types
    m.Sc = pe.Set()     # set of fuel cells types

    # noinspection ClassSet. The union function works.
    m.S = pe.Set(initialize=m.Se | m.Sh | m.Sc)     # set of types of storage devices

    # noinspection typeInspection
    m.nHrs = pe.Param(domain=pe.PositiveIntegers)       # the number of hours (time periods) in a year
    m.nHrs_ = pe.Param(initialize=m.nHrs - 1)     # index of the last time periods (hour)
    m.T = pe.RangeSet(0, m.nHrs_)       # set of time periods (hour)

    # define variables needed for demonstrating decorators
    # 1) decision variables
    # m.sNum = pe.Var(m.S, within=pe.NonNegativeReals)         # number of units of s-th storage device
    # m.sNum = pe.Var(m.S, within=pe.NonNegativeIntegers)      # number of units of s-th storage device
    m.sNum = pe.Var(m.S, within=pe.NonNegativeIntegers, bounds=(0, 500))   # bounds on int vars required by cplex
    m.supply = pe.Var()       # energy committed to be provided in each hour, [MW]

    # 2) control variables
    m.dOut = pe.Var(m.T, within=pe.NonNegativeReals)        # electricity directly meet the commitment, [MW]
    m.sIn = pe.Var(m.T, within=pe.NonNegativeReals)     # electricity inflow redirected to storage, [MW]
    m.ePrs = pe.Var(m.T, within=pe.NonNegativeReals)        # electricity used to make high pressure, [MW]
    m.sOut = pe.Var(m.T, within=pe.NonNegativeReals)        # electricity from storage to meet commitment, [MW]
    m.eIn = pe.Var(m.Se, m.T, within=pe.NonNegativeReals)       # electricity inflow to each electrolyzer,[MW].
    m.eS = pe.Var(m.T, within=pe.NonNegativeReals)              # loss of electricity while overproduction [MW].
    m.eB = pe.Var(m.T, within=pe.NonNegativeReals)              # electricity purchase on the market [MW].
    m.hIn = pe.Var(m.Sh, m.T, within=pe.NonNegativeReals)       # hydrogen inflow to hydrogen tank, [100kg]
    m.hOut = pe.Var(m.Sh, m.T, within=pe.NonNegativeReals)      # hydrogen outflow from hydrogen tank, [100kg]
    m.hVol = pe.Var(m.Sh, m.T, within=pe.NonNegativeReals)      # amount of hydrogen stored in s-th device
    m.hInc = pe.Var(m.Sc, m.T, within=pe.NonNegativeReals)      # hydrogen inflow to each fuel cell, [100kg]
    m.cOut = pe.Var(m.Sc, m.T, within=pe.NonNegativeReals)      # electricity outflow from each fuel cell, [MWh]

    # Outcome variables
    m.revenue = pe.Var(within=pe.Reals)     # the annual revenue of the system
    m.income = pe.Var(within=pe.Reals)      # the annual income from satisfying the commitment
    m.invCost = pe.Var(within=pe.Reals)     # the annualized investment cost of the storage system
    m.surpCost = pe.Var(within=pe.Reals)    # the cost of management of surplus
    m.buyCost = pe.Var(within=pe.Reals)     # the cost of management of shortage
    m.balCost = pe.Var(within=pe.Reals)     # the cost of management of electricity surplus and shortage
    m.OMC = pe.Var(within=pe.Reals)     # the operation and maintenance costs

    # Auxiliary variables
    m.sCap = pe.Var(m.S, within=pe.NonNegativeReals)        # total capacity of ，总容量 s-th type of storage devices
    m.mxIn = pe.Var(m.S, within=pe.NonNegativeReals)        # the maximum hydrogen inflow of s-th tank (per hour)
    m.mxOut = pe.Var(m.S, within=pe.NonNegativeReals)       # the maximum hydrogen outflow of s-th tank (per hour)
    m.hInit = pe.Var(m.Sh, within=pe.NonNegativeReals)  # total amount of initial hydrogen in s-th tank
    m.h2T = pe.Var(m.T, within=pe.NonNegativeReals)     # total amount of hydrogen produced by all electrolyzer
    m.h2C = pe.Var(m.T, within=pe.NonNegativeReals)     # total amount of hydrogen from hydrogen tanks to fuel cells
    m.eSurplus = pe.Var(within=pe.NonNegativeReals)   # total amount of electricity surplus
    m.eBought = pe.Var(within=pe.NonNegativeReals)   # total amount of electricity purchase

    # parameters
    m.inflow = pe.Param(m.T, domain=pe.NonNegativeReals)     # amount of electricity incoming to the site
    m.mxCap = pe.Param(m.S, domain=pe.NonNegativeReals)     # unit storage capacity of each storage device, MW or 100kg
    m.hMxIn = pe.Param(m.Sh, domain=pe.NonNegativeReals)       # maximum hydrogen incoming to the tank [100kg]
    m.hMxOut = pe.Param(m.Sh, domain=pe.NonNegativeReals)       # maximum hydrogen outflow from the tank [100kg]
    m.hini = pe.Param(m.Sh, domain=pe.NonNegativeReals)      # initial hydrogen available in hydrogen tank [100kg]
    m.eh2 = pe.Param(m.Se, domain=pe.NonNegativeReals)      # converting electricity to hydrogen, [100kg/MWh]
    m.eph2 = pe.Param(m.Sh, domain=pe.NonNegativeReals)     # making high pressure, [MWh/100kg]
    m.h2Res = pe.Param(m.Sh, domain=pe.NonNegativeReals)        # hydrogen retention rate, unit in percentage
    m.h2e = pe.Param(m.Sc, domain=pe.NonNegativeReals)      # converting hydrogen to electricity [MWh/100kg]
    m.ePrice = pe.Param(domain=pe.NonNegativeReals)     # contract price, [thousand RMB/MW]
    m.eBprice = pe.Param(domain=pe.NonNegativeReals)     # purchase price of buying electricity, [thousand RMB/MW]
    m.eSprice = pe.Param(domain=pe.Reals)       # unit price of electricity surplus, [thousand RMB]
    m.sInv = pe.Param(m.S, domain=pe.NonNegativeReals)      # per unit investment cost of storage, [thousand RMB]
    m.sOmc = pe.Param(m.S, domain=pe.NonNegativeReals)       # per unit operation cost of storage, [thousand RMB]

    @m.Constraint(m.T)      # energy inflow is divided into four energy flows
    def inflowBal(mx, t):
        return mx.inflow[t] == mx.dOut[t] + mx.sIn[t] + mx.ePrs[t] + mx.eS[t]

    @m.Constraint(m.T)      # total electricity used to store hydrogen equal to the sum of inflows to electrolyzers
    def sInBal(mx, t):
        return mx.sIn[t] == sum(mx.eIn[s, t] for s in mx.Se)

    @m.Constraint(m.Se, m.T)        # Inflows to all electrolyzers are constrained by the sum of their capacities
    def eInUpper(mx, s, t):
        return mx.eIn[s, t] <= mx.sCap[s]

    @m.Constraint(m.T)      # The amount of hydrogen produced by all electrolyzers
    def h2tBal1(mx, t):
        return mx.h2T[t] == sum(mx.eh2[s] * mx.eIn[s, t] for s in mx.Se)

    @m.Constraint(m.T)      # Produced hydrogen is split between tanks
    def h2tBal2(mx, t):
        return mx.h2T[t] == sum(mx.hIn[s, t] for s in mx.Sh)

    @m.Constraint(m.T)      # The amount of electricity used for pressure control of all hydrogen tanks
    def ePrsBal(mx, t):
        return mx.ePrs[t] == sum(mx.eph2[s] * mx.hIn[s, t] for s in mx.Sh)
    # Relations defining auxiliary variables

    @m.Constraint(m.Sh, m.T)  # Amount of hydrogen in each tank type
    def hVolBal(mx, s, t):
        if t == 0:
            return mx.hVol[s, t] == mx.hInit[s] + mx.hIn[s, t] - mx.hOut[s, t]
        else:
            return mx.hVol[s, t] == mx.h2Res[s] * mx.hVol[s, (t - 1)] + mx.hIn[s, t] - mx.hOut[s, t]

    @m.Constraint(m.Sh, m.T)  # Amount of hydrogen in tanks of each type
    def hVolLower(mx, s, t):
        # return mx.hVol[s, t] >= mx.hMin[s]
        return mx.hVol[s, t] >= 0

    @m.Constraint(m.Sh, m.T)  # Amount of hydrogen in tanks of each type
    def hVolUpper(mx, s, t):
        return mx.hVol[s, t] <= mx.sCap[s]

    # @m.Constraint(m.Sh)  # Amount of hydrogen at the last period
    # def hVolEnd(mx, s):
    #     return mx.hVol[s, mx.nHrs_] == mx.hInit[s]

    @m.Constraint(m.Sh, m.T)        # Maximum flow from each type of tank to fuel cells
    def hInUpper(mx, s, t):
        return mx.hIn[s, t] <= mx.mxIn[s]

    @m.Constraint(m.Sh, m.T)        # Maximum flow from each type of tank to fuel cells
    def hOutUpper(mx, s, t):
        return mx.hOut[s, t] <= mx.mxOut[s]

    @m.Constraint(m.T)      # Hydrogen flow from tanks to all fuel cells
    def h2CBal1(mx, t):
        return mx.h2C[t] == sum(mx.hOut[s, t] for s in mx.Sh)

    @m.Constraint(m.T)  # Hydrogen flow from tanks is split between fuel cells
    def h2CBal2(mx, t):
        return mx.h2C[t] == sum(mx.hInc[s, t] for s in mx.Sc)

    @m.Constraint(m.T)      # The committed supply is composed of three parts
    def supplyBal(mx, t):
        return mx.supply == mx.dOut[t] + mx.sOut[t] + mx.eB[t]

    @m.Constraint(m.T)      # electricity outflow from the storage is defined by the sum of outflows from fuel cells
    def sOutBal(mx, t):
        return mx.sOut[t] == sum(mx.cOut[s, t] for s in mx.Sc)

    @m.Constraint(m.Sc, m.T)        # The electricity from fuel cells
    def cOutBal(mx, s, t):
        return mx.cOut[s, t] == mx.h2e[s] * mx.hInc[s, t]

    @m.Constraint(m.Sc, m.T)        # The electricity outflow from the fuel cell
    def cOutUpper(mx, s, t):
        return mx.cOut[s, t] <= mx.sCap[s]

    # relations defining outcome variables
    @m.Constraint()     # Income from supplying
    def incomeC(mx):
        return mx.income == mx.ePrice * mx.supply

    @m.Constraint()     # Annualized investment cost of the storage system
    def invCostC(mx):
        return mx.invCost == sum(mx.sInv[s] * mx.sNum[s] for s in mx.S)

    @m.Constraint()     # Operation and maintenance cost of the storage system
    def OMCC(mx):
        return mx.OMC == sum(mx.sOmc[s] * mx.sNum[s] for s in mx.S)
        # return mx.OMC == sum(mx.sOmc[s] * mx.sNum[s] for s in mx.S) + mx.varCost

    @m.Constraint()      # Cost of handling surplus
    def surpCostC(mx):
        return mx.surpCost == mx.eSprice * mx.eSurplus

    @m.Constraint()  # Cost of handling surplus
    def buyCostC(mx):
        return mx.buyCost == mx.eBprice * mx.eBought

    @m.Constraint()     # Cost of balancing surplus and deficit
    def balCostC(mx):
        return mx.balCost == mx.surpCost + mx.buyCost

    @m.Constraint()     # Total revenue of the system
    def revenueC(mx):
        return mx.revenue == mx.income - mx.invCost - mx.OMC - mx.balCost

    # Relations defining auxiliary variables
    @m.Constraint(m.S)
    def sCapC(mx, s):
        return mx.sCap[s] == mx.mxCap[s] * mx.sNum[s]

    @m.Constraint(m.Sh)  # Maximum hydrogen inflow of s-th tank (per hour)
    def mxInC(mx, s):
        return mx.mxIn[s] == mx.hMxIn[s] * mx.sNum[s]

    @m.Constraint(m.Sh)
    def mxOutC(mx, s):
        return mx.mxOut[s] == mx.hMxOut[s] * mx.sNum[s]

    @m.Constraint(m.Sh)
    def hInitC(mx, s):
        return mx.hInit[s] == mx.hini[s] * mx.sNum[s]

    @m.Constraint()
    def eSurplusBal(mx):
        return mx.eSurplus == sum(mx.eS[t] for t in mx.T)

    @m.Constraint()
    def eBoughtBal(mx):
        return mx.eBought == sum(mx.eB[t] for t in mx.T)

    @m.Objective(sense=pe.maximize)     # Revenue (used as a Goal-Function/Objective in single-criterion analysis)
    def obj(mx):
        return mx.revenue

    print('mk_sms(): finished')
    # m.pprint()    # does not work (needs lengths of sets)

    return m

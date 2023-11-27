"""Matouqin model generator"""
import pyomo.environ as pe      # more robust than using import *
import sys


class Model:
    def __init__(self, verb=True):
        self.verb = verb        # output verbosity
        # self.mc = mc      # define persistent elements if desired for running the model with modified params

    # noinspection PyTypeChecker
    def mk_model(self, p):      # p: model parameters prepared in the Params class
        m = pe.AbstractModel('Matouqin v. 0.1')   # instance of the concrete model
        # print(f'Generating AbstractModel model for parameters (version: {p.ver}')

        # print(f'Dictionary of prepared parameters contains  {len(p.cat)} items.')

        # print(f'xx = {p.xx}')
        '''
        @m.Constraint(m.C)
        def xLink(mx, ii):  # link the corresponding m1 and mc_core variables
            return mx.x[ii] == p.eff.get('el2h') * mx.y[ii]
        # def link_rule(m, i):  # traditional (without decorations) constraint using a rule, just for illustration
        #     return m.x[i] == m.m1_cr_vars[i]
        # m.xLink = pe.Constraint(m.C, rule=link_rule)

        # AF and m1_vars defined above
        m.caf = pe.Var(m.C)    # CAF value
        m.cafMin = pe.Var()     # min of CAFs

        @m.Constraint(m.C)
        def cafMinD(mx, ii):
            return mx.cafMin <= mx.caf[ii]

        @m.Objective(sense=pe.maximize)
        def obj(mx):
            return mx.cafMin

        if self.verb:
            m.pprint()
        '''

        # sets
        m.Se = pe.Set()     # set of electrolyzers
        m.Sh = pe.Set()     # set of hydrogen tanks
        m.Sc = pe.Set()     # set of fuel cell
        m.S = pe.Set()      # a composed set of storage devices
        m.nHrs = pe.Param(domain=pe.PositiveIntegers, default=10)       # the number of hours (time periods) in a year
        m.nHrs_ = pe.Param(initialize=m.nHrs-1)     # index of the last time periods (hour)
        m.T = pe.RangeSet(0, m.nHrs_)       # set of time periods (hour)

        # define variables needed for demonstrating decorators
        # decision variables
        m.Num = pe.Var(m.S, within=pe.NonNegativeIntegers)      # number of units of s-th storage device
        m.supply = pe.Var(within=pe.NonNegativeReals)       # energy committed to be provided in each hour, [MWh]

        # control variables
        m.dOut = pe.Var(m.T, within=pe.NonNegativeReals)        # electricity directly meet the commitment, [MWh]
        m.sIn = pe.Var(m.T, within=pe.NonNegativeReals)     # electricity inflow redirected to storage, [MWh]
        m.ePrs = pe.Var(m.T, within=pe.NonNegativeReals)        # electricity used to make high pressure, [MWh]
        m.sOut = pe.Var(m.T, within=pe.NonNegativeReals)        # electricity from storage to meet commitment, [MWh]
        m.eIn = pe.Var(m.Se, m.T, within=pe.NonNegativeReals)       # electricity inflow to each electrolyzer,[MWh].
        m.eSurplus = pe.Var(m.T, within=pe.NonNegativeReals)        # the loss of electricity while overproduction.
        m.eBought = pe.Var(m.T, within=pe.NonNegativeReals)     # amount of electricity bought on the market
        m.hIn = pe.Var(m.Sh, m.T, within=pe.NonNegativeReals)       # hydrogen inflow to each hydrogen tank, [kg]
        m.hOut = pe.Var(m.Sh, m.T, within=pe.NonNegativeReals)      # hydrogen outflow from each hydrogen tank, [kg]
        m.hVol = pe.Var(m.Sh, m.T, within=pe.NonNegativeReals)      # amount of hydrogen stored in s-th device
        m.hInc = pe.Var(m.Sc, m.T, within=pe.NonNegativeReals)      # hydrogen inflow to each fuel cell, [kg]
        m.cOut = pe.Var(m.Sc, m.T, within=pe.NonNegativeReals)      # electricity outflow from each fuel cell, [MWh]

        # Outcome variables
        m.revenue = pe.Var(within=pe.Reals)     # the annual revenue of the system
        m.income = pe.Var(within=pe.Reals)      # the annual income from satisfying the commitment
        m.invCost = pe.Var(within=pe.Reals)     # the annualized investment cost of the storage system
        m.balCost = pe.Var(within=pe.Reals)     # the cost of management of electricity surplus and shortage
        m.OMC = pe.Var(within=pe.Reals)     # the operation and maintenance costs

        # Auxiliary variables
        m.sCap = pe.Var(m.S, within=pe.NonNegativeReals)        # total capacity of ，总容量 s-th type of storage devices
        m.hMin = pe.Var(m.Sh, within=pe.NonNegativeReals)       # the lowest hydrogen needed in s-th type of tank
        m.mxIn = pe.Var(m.S, within=pe.NonNegativeReals)        # the maximum hydrogen inflow of s-th tank (per hour)
        m.mxOut = pe.Var(m.S, within=pe.NonNegativeReals)       # the maximum hydrogen outflow of s-th tank (per hour)
        m.h2T = pe.Var(m.T, within=pe.NonNegativeReals)     # total amount of hydrogen produced by all electrolyzers
        m.h2C = pe.Var(m.T, within=pe.NonNegativeReals)     # total amount of hydrogen from hydrogen tanks to fuel cells

        # parameters
        m.inflow = pe.Param(domain=pe.NonNegativeReals)     # amount of electricity incoming to the site
        m.mxCap = pe.Param(m.S, domain=pe.NonNegativeReals)     # unit storage capacity of each storage device
        m.hMxIns = pe.Param(m.Sh, domain=pe.NonNegativeReals)       # maximum hydrogen incoming to the tank [kg]
        m.hMxOut = pe.Param(m.Sh, domain=pe.NonNegativeReals)       # maximum hydrogen outflow from the tank [kg]
        m.hmi = pe.Param(m.Sh, domain=pe.NonNegativeReals)      # minimum hydrogen needed in hydrogen tank [kg]
        m.eh2 = pe.Param(m.Sh, domain=pe.NonNegativeReals)      # converting electricity to hydrogen, [kg/MWh]
        m.eph2 = pe.Param(m.Sh, domain=pe.NonNegativeReals)     # making high pressure, [MWh/kg]
        m.h2Res = pe.Param(m.Sh, domain=pe.NonNegativeReals)        # hydrogen retention rate, unit in percentage
        m.h2e = pe.Param(m.Se, domain=pe.NonNegativeReals)      # converting hydrogen to electricity [MWh/kg]
        m.Hrs = pe.Param(domain=pe.NonNegativeIntegers)     # the number of hours in a year
        m.ann = pe.Param(m.S, domain=pe.NonNegativeReals)       # annualization factor
        m.ePrice = pe.Param(domain=pe.NonNegativeReals)     # purchase price of buying electricity, [million RMB/MWh]
        m.overCost = pe.Param(domain=pe.NonNegativeReals)       # unit price of electricity surplus, [million RMB]
        m.sInv = pe.Param(m.S, domain=pe.NonNegativeReals)      # per unit investment cost of storage, [million RMB]
        m.Omc = pe.Param(m.S, domain=pe.NonNegativeReals)       # per unit operation cost of storage, [million RMB]

        # relations defining energy flows
        @m.Constraint(m.T)      # energy inflow is divided into four energy flows
        def inflow_blc(m, t):
            return m.inflow[t] == m.dOut[t] + m.sIn[t] + m.Prs[t] + m.Surplus[t]

        @m.Constraint(m.T)      # total electricity used to store hydrogen equal to the sum of inflows to electrolyzers
        def sin_blc(m, t):
            return m.sIn[t] == sum(m.eIn[s, t] for s in m.Se)

        @m.Constraint(m.Se, m.T)        # Inflows to all electrolyzers are constrained by the sum of their capacities
        def ein_upper(m, s, t):
            return m.eIn[s, t] <= m.sCap[s]

        @m.Constraint(m.T)      # The amount of hydrogen produced by all electrolyzers
        def h2t_blc1(m, t):
            return m.h2T[t] == sum(m.eh2[s] * m.eIn[s, t] for s in m.Se)

        @m.Constraint(m.T)      # Produced hydrogen is split between tanks
        def h2t_blc2(m, t):
            return m.h2T[t] == sum(m.hIn[s, t] for s in m.Sh)

        @m.Constraint(m.T)      # The amount of electricity used for pressure control of all hydrogen tanks
        def ePrs_blc(m, t):
            return m.ePrs[t] == sum(m.eph2[s] * m.hIn[s, t] for s in m.Sh)

        @m.Constraint(m.Sh, m.T)        # Amount of hydrogen in each tank type
        def hVol_bal(m, s, t):
            return m.hVol[s, t] == m.h2Res[s] * m.hVol[s, (t-1)] + m.hIn[s, t] - m.hOut[s, t]

        @m.Constraint(m.Sh, m.T)        # Amount of hydrogen in tanks of each type
        def hVol_bon(m, s, t):
            return m.hMin[s] <= m.hVol[s, t] <= m.sCap[s]

        @m.Constraint(m.Sh, m.T)        # Maximum flow to each type of tank
        def hIn_upper(m, s, t):
            return m.hIn[s, t] <= m.mxIn[s]

        @m.Constraint(m.Sh, m.T)        # Maximum flow from each type of tank to fuel cells
        def hOut_upper(m, s, t):
            return m.hOut[s, t] <= m.mxOut[s]

        @m.Constraint(m.T)      # Hydrogen flow from tanks to all fuel cells
        def h2C_blc1(m, t):
            return m.h2C[t] == sum(m.hOut[s, t] for s in m.Sh)

        @m.Constraint(m.T)      # Hydrogen flow from tanks is split between fuel cells
        def h2C_blc2(m, t):
            return m.h2C[t] == sum(m.hInc[s, t] for s in m.Sc)

        @m.Constraint(m.T)      # The committed supply is composed of three parts
        def supply_blc(m, t):
            return m.supply == m.dOut[t] + m.sOut[t] + m.eBought[t]

        @m.Constraint(m.T)      # electricity outflow from the storage is defined by the sum of outflows from fuel cells
        def sOut_blc(m, t):
            return m.sOut[t] == sum(m.cOut[s, t] for s in m.Sc)

        @m.Constraint(m.Sc, m.T)        # The electricity from fuel cells
        def cOut_blc(m, s, t):
            return m.cOut[s, t] == m.h2e[s] * m.hInc[s, t]

        @m.Constraint(m.Sc, m.T)        # The electricity outflow from the fuel cell
        def eOut_upper(m, s, t):
            return m.cOut[s, t] <= m.sCap[s]

        # relations defining outcome variables
        @m.Constraint()     # Income from supplying
        def incomeC(m):
            return m.income == m.ePrice * m.nHrs * m.supply

        @m.Constraint()     # Annualized investment cost of the storage system
        def invCostC(m):
            return m.invCost == sum(m.ann[s] * m.sInv[s] * m.sNum[s] for s in m.S)

        @m.Constraint()     # Operation and maintenance cost of the storage system
        def OMCC(m):
            return m.OMC == sum(m.sOmc[s] * m.sNum[s] for s in m.S)

        @m.Constraint()     # Cost of balancing surplus and deficit
        def balCostC(m):
            return m.balCost == m.overCost * m.Hrs * sum(m.eSurplus[t] for t in m.T) + m.eBprice * m.Hrs * sum(m.eBought[t] for t in m.T)

        @m.Objective(sense=pe.maximize)     # Revenue (used as a Goal-Function/Objective in single-criterion analysis)
        def obj(m):
            return m.revenue == m.income - m.invCost - m.OMC - m.balCost

        print('mk_sms(): finished')



        return m


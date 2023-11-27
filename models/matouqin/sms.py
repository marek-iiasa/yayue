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
        m.Num = pe.Var(m.S, within=pe.NonNegativeIntegers)
        m.supply = pe.Var(within=pe.NonNegativeReals)

        # control variables
        m.dOut = pe.Var(m.T, within=pe.NonNegativeReals)
        m.sIn = pe.Var(m.T, within=pe.NonNegativeReals)
        m.ePrs = pe.Var(m.T, within=pe.NonNegativeReals)
        m.sOut = pe.Var(m.T, within=pe.NonNegativeReals)
        m.eIn = pe.Var(m.Se, m.T, within=pe.NonNegativeReals)
        m.eSurplus = pe.Var(m.T, within=pe.NonNegativeReals)
        m.eBought = pe.Var(m.T, within=pe.NonNegativeReals)
        m.hIn = pe.Var(m.Sh, m.T, within=pe.NonNegativeReals)
        m.hOut = pe.Var(m.Sh, m.T, within=pe.NonNegativeReals)
        m.hVol = pe.Var(m.Sh, m.T, within=pe.NonNegativeReals)
        m.hInc = pe.Var(m.Sc, m.T, within=pe.NonNegativeReals)
        m.cOut = pe.Var(m.Sc, m.T, within=pe.NonNegativeReals)

        # Outcome variables
        m.revenue = pe.Var(within=pe.Reals)
        m.income = pe.Var(within=pe.Reals)
        m.invCost = pe.Var(within=pe.Reals)
        m.balCost = pe.Var(within=pe.Reals)
        m.OMC = pe.Var(within=pe.Reals)

        # Auxiliary variables
        m.sCap = pe.Var(m.S, within=pe.NonNegativeReals)
        m.hMin = pe.Var(m.Sh, within=pe.NonNegativeReals)
        m.mxIn = pe.Var(m.S, within=pe.NonNegativeReals)
        m.mxOut = pe.Var(m.S, within=pe.NonNegativeReals)
        m.h2T = pe.Var(m.T, within=pe.NonNegativeReals)
        m.h2C = pe.Var(m.T, within=pe.NonNegativeReals)

        # parameters
        m.inflow = pe.Param(domain=pe.NonNegativeReals)     # amount of electricity incoming to the site
        m.mxCap = pe.Param(m.S, domain=pe.NonNegativeReals)     # unit storage capacity of each storage device
        m.hMxIns = pe.Param(m.Sh, domain=pe.NonNegativeReals)       # maximum hydrogen incoming to the tank [kg]
        m.hMxOut = pe.Param(m.Sh, domain=pe.NonNegativeReals)       # maximum hydrogen outflow from the tank [kg]
        m.hmi = pe.Param(m.Sh, domain=pe.NonNegativeReals)      # minimum hydrogen needed in hydrogen tank [kg]
        m.eh2 = pe.Param(m.Sh, domain=pe.NonNegativeReals)      #
        m.eph2 = pe.Param(m.Sh, domain=pe.NonNegativeReals)     #
        m.h2Res = pe.Param(m.Sh, domain=pe.NonNegativeReals)
        m.h2e = pe.Param(m.Se, domain=pe.NonNegativeReals)
        m.Hrs = pe.Param(domain=pe.NonNegativeIntegers)
        m.ann = pe.Param(m.S, domain=pe.NonNegativeReals)
        m.ePrice = pe.Param(domain=pe.NonNegativeReals)
        m.overCost = pe.Param(domain=pe.NonNegativeReals)
        m.sInv = pe.Param(m.S, domain=pe.NonNegativeReals)
        m.Omc = pe.Param(m.S, domain=pe.NonNegativeReals)

        # relations defining energy flows
        @m.Constraint(m.T)
        def inflow_blc(m, t):
            return m.inflow[t] == m.dOut[t] + m.sIn[t] + m.Prs[t] + m.Surplus[t]

        @m.Constraint(m.T)
        def sin_blc(m, t):
            return m.sIn[t] == sum(m.eIn[s, t] for s in m.Se)

        @m.Constraint(m.Se, m.T)
        def ein_upper(m, s, t):
            return m.eIn[s, t] <= m.sCap[s]

        @m.Constraint(m.T)
        def h2t_blc1(m, t):
            return m.h2T[t] == sum(m.eh2[s] * m.eIn[s, t] for s in m.Se)

        @m.Constraint(m.T)
        def h2t_blc2(m, t):
            return m.h2T[t] == sum(m.hIn[s, t] for s in m.Sh)

        @m.Constraint(m.T)
        def ePrs_blc(m, t):
            return m.ePrs[t] == sum(m.eph2[s] * m.hIn[s, t] for s in m.Sh)

        @m.Constraint(m.Sh, m.T)
        def hVol_bal(m, s, t):
            return m.hVol[s, t] == m.h2Res[s] * m.hVol[s, (t-1)] + m.hIn[s, t] - m.hOut[s, t]

        @m.Constraint(m.Sh, m.T)
        def hVol_bon(m, s, t):
            return m.hMin[s] <= m.hVol[s, t] <= m.sCap[s]

        @m.Constraint(m.Sh, m.T)
        def hIn_upper(m, s, t):
            return m.hIn[s, t] <= m.mxIn[s]

        @m.Constraint(m.Sh, m.T)
        def hOut_upper(m, s, t):
            return m.hOut[s, t] <= m.mxOut[s]

        @m.Constraint(m.T)
        def h2C_blc1(m, t):
            return m.h2C[t] == sum(m.hOut[s, t] for s in m.Sh)

        @m.Constraint(m.T)
        def h2C_blc2(m, t):
            return m.h2C[t] == sum(m.hInc[s, t] for s in m.Sc)

        @m.Constraint(m.T)
        def supply_blc(m, t):
            return m.supply == m.dOut[t] + m.sOut[t] + m.eBought[t]

        @m.Constraint(m.T)
        def sOut_blc(m, t):
            return m.sOut[t] == sum(m.cOut[s, t] for s in m.Sc)

        @m.Constraint(m.Sc, m.T)
        def cOut_blc(m, s, t):
            return m.cOut[s, t] == m.h2e[s] * m.hInc[s, t]

        @m.Constraint(m.Sc, m.T)
        def eOut_upper(m, s, t):
            return m.cOut[s, t] <= m.sCap[s]

        # relations defining outcome variables
        @m.Constraint()
        def incomeC(m):
            return m.income == m.ePrice * m.nHrs * m.supply

        @m.Constraint()
        def invCostC(m):
            return m.invCost == sum(m.ann[s] * m.sInv[s] * m.sNum[s] for s in m.S)

        @m.Constraint()
        def OMCC(m):
            return m.OMC == sum(m.sOmc[s] * m.sNum[s] for s in m.S)

        @m.Constraint()
        def balCostC(m):
            return m.balCost == m.overCost * m.Hrs * sum(m.eSurplus[t] for t in m.T) + m.eBprice * m.Hrs * sum(m.eBought[t] for t in m.T)

        @m.Objective(sense=pe.maximize)
        def obj(m):
            return m.revenue == m.income - m.invCost - m.OMC - m.balCost


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

        return m


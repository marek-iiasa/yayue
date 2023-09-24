"""Matouqin model generator"""
import pyomo.environ as pe       # more robust than using import *


class Model:
    def __init__(self, verb=True):
        self.verb = verb        # output verbosity
        # self.mc = mc    # define persistent elements if desired for running the model with modified params

    def mk_model(self, p):  # p: model parameters prepared in the Params class
        m = pe.ConcreteModel('Matouqin v. 0.1')   # instance of the concrete model
        print(f'Generating concrete model for paramets (version: {p.ver}')

        print(f'Distionary of prepared parameters contains  {len(p.cat)} items.')

        print(f'pprice = {p.pPrice}')
        # print(f'xx = {p.xx}')

        # define variables needed for demonstrating decorators
        m.T = pe.RangeSet(0, 5)   # set of all criteria indices
        m.supply = pe.Var(m.T, within=pe.NonNegativeReals)
        m.sCap1 = pe.Var(within=pe.NonNegativeReals)
        m.sCap2 = pe.Var(within=pe.NonNegativeReals)
        m.sCap3 = pe.Var(within=pe.NonNegativeReals)
        m.dOut = pe.Var(m.T, within=pe.NonNegativeReals)
        m.surplus = pe.Var(m.T, within=pe.NonNegativeReals)
        m.sIn = pe.Var(m.T, within=pe.NonNegativeReals)
        m.sOut = pe.Var(m.T, within=pe.NonNegativeReals)
        m.deficit = pe.Var(m.T, within=pe.NonNegativeReals)
        m.r = pe.Var(m.T, within=pe.NonNegativeReals)
        m.rev = pe.Var()
        m.mc = pe.Var()
        m.inv = pe.Var()

        @m.Constraint(m.T)
        def inflowBlc(m, t):
            return m.dOut[t] + m.sIn[t] + m.surplus[t] == m.inflow[t]

        @m.Constraint(m.T)
        def supplyBlc(m, t):
            return m.dOut[t] + m.sOut[t] + m.deficit[t] == m.supply

        @m.Constraint(m.T)
        def storageTrans(m, t):
            if t == 0:
                return m.r[t] == 0
            else:
                return m.r[t] == m.loss * m.r[t-1] + m.toH * m.sIn[t] - m.toE * m.sOut[t]

        @m.Constraint(m.T)
        def storageCap(m, t):
            return m.r[t] <= m.sCap2

        @m.Constraint(m.T)
        def elctlyzCap(m, t):
            return m.sIn[t] <= m.sCap1

        @m.Constraint(m.T)
        def storageFlowin(m, t):
            return m.sIn[t] <= m.sPower

        @m.Constraint(m.T)
        def storageFlowout(m, t):
            return m.toE * m.sOut[t] <= m.sPower

        @m.Constraint(m.T)
        def fullcellCap(m, t):
            return m.toE[t] * m.sOut[t] <= m.sCap3

        @m.Objective(sense=pe.maximize)
        def obj(m):
            return m.rev == m.p0 * m.supply + m.p1 * m.sCap1 + m.p2 * m.sCap2 + m.p3 * m.sCap3


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


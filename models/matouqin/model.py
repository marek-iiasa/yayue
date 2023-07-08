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
        m.C = pe.RangeSet(0, 1)   # set of all criteria indices
        m.x = pe.Var(m.C)
        m.y = pe.Var(m.C)

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

        return m

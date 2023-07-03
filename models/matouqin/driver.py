"""
Prototype of the Matouqin driver
"""
# import os.path

import sys		# needed for sys.exit()
# import os
# import pandas as pd
import pyomo.environ as pe
from pyomo.opt import SolverStatus
from pyomo.opt import TerminationCondition
from model import Model  # handles submodel/block of AF and links to the core/substantive model
from params import Params
from report import report


def chk_sol(res):  # check status of the solution
    print(f'solver status: {res.solver.status}, termination condition: {res.solver.termination_condition}.')
    if ((res.solver.status != SolverStatus.ok) or
            (res.solver.termination_condition != TerminationCondition.optimal)):
        print(f'{res.solver.termination_condition = }')
        sys.stdout.flush()  # desired for assuring printing exception at the output end
        if res.solver.termination_condition == TerminationCondition.infeasible:
            raise Exception('Optimization problem is infeasible.')
        elif res.solver.termination_condition == TerminationCondition.unbounded:
            raise Exception('Optimization problem is unbounded.')
        else:
            raise Exception('Optimization failed.')


def driver():
    model = Model(False)    # initialize Model class that generates model instance (ConcreteModel)
    par = Params()  # prepare all model parameter
    m = model.mk_model(par)
    print(f'\nAnalysing instance of model {m.name}.')

    m.pprint()

    print('\nsolving --------------------------------')
    # select solver
    opt = pe.SolverFactory('glpk')
    # opt = pe.SolverFactory('ipopt') # solves both LP and NLP
    # opt = SolverFactory('gams')  # gams can be used as a solver
    results = opt.solve(m, tee=False)   # True to pipe output to the terminal
    chk_sol(results)  # check the status of the solution
    # todo: clarify exception (uncomment next line) while loading the results
    # m.load(results)  # Loading solution into results object

    print('\nprocessing solution --------------------------------')
    report(m)

    # opt = SolverFactory('gams')  # gams can be used as a solver

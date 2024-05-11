"""
Prototype of the Matouqin driver
"""
# import os.path

import sys		# needed for sys.exit()
import os
# import pandas as pd
# import pyomo.environ as pe
from pyomo.opt import SolverStatus
from pyomo.opt import TerminationCondition
from inst import *
from sms import *  # handles sub model/block of AF and links to the core/substantive model
# from dat_process import Params  # data processing
from report import *    # report all variables and needed results for plotting
from plot import *      # plot needed variables


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
    path = '.'
    data_dir = f'{path}/Data/'      # repository of data
    res_dir = f'{path}/Results/'    # repository of results
    fig_dir = f'{path}/Figures/'  # repository of figures

    # check repository
    if not os.path.exists(res_dir):
        os.makedirs(res_dir, mode=0o755)
        print(f'Directory {res_dir} created')

    if not os.path.exists(fig_dir):
        os.makedirs(fig_dir, mode=0o755)
        print(f'Directory {fig_dir} created')

    # make model
    abst = mk_sms()    # initialize Model class that generates model instance (ConcreteModel)

    # f_data = f'{data_dir}dat1.dat'     # real data test by ZZ
    f_data = f'{data_dir}test1.dat'     # small scale data for testing the model
    # f_data = f'{data_dir}test2.dat'     # small scale data for testing the model

    model = inst(abst, f_data)
    print(f'\nAnalysing instance of model {model.name}.')

    # print the model
    model.pprint()

    # select solver
    print('\nsolving --------------------------------')

    # glpk settings
    opt = pe.SolverFactory('glpk')
    opt.options['log'] = f'{res_dir}glpk_log.txt'
    opt.options['wmps'] = f'{res_dir}glpk.mps'  # glpk
    results = opt.solve(model, tee=True)  # True to pipe output to the terminal

    # cplex settings
    # opt = pe.SolverFactory('gams')  # gams can be used as a solver
    # results = opt.solve(model, solver='cplex', symbolic_solver_labels=True, tee=True,
    #                     add_options=['GAMS_MODEL.optfile = 1;', '$onecho > cplex.opt', 'mipkappastats 1', '$offecho'])

    # other solvers
    # opt = pe.SolverFactory('ipopt')  # solves both LP and NLP
    # results = opt.solve(model, tee=True)

    chk_sol(results)  # check the status of the solution

    # todo: clarify exception (uncomment next line) while loading the results
    # model.load(results)  # Loading solution into results object

    print('\nprocessing solution --------------------------------')

    # reporting results
    rep_vars = ['sNum', 'sCap', 'supply', 'revenue', 'income', 'invCost', 'OMC', 'overCost', 'buyCost', 'balCost',
                'dOut', 'sIn', 'ePrs', 'sOut', 'eIn', 'eSurplus', 'eBought', 'hIn', 'hOut', 'hVol', 'hInc', 'cOut']
    print(f'Values of the following variables will be extracted from the solution and stored in the df:\n{rep_vars}')

    rep = Report(model, res_dir, rep_vars)      # report results
    rep.var_vals()  # extract from the solution values of the requested variables
    rep.summary()  # store the extracted values in a df
    # rep.check()  # check storage flow results
    # rep.toExcel()   # store the extracted values in Excel for plotting

    print(f'\nPlace holder for report results of model {model.name}.')
    rep.analyze()  # analyze the results

    # print('\nPlotting begins ----------------------------------------------------------------')
    # fig = Plot(res_dir, fig_dir)
    #
    # fig.plot_flow('hourly', True)         # Flow overview, 'hourly', 'daily', 'weekly', 'monthly' flows
    # fig.plot_flow('daily', True)
    # fig.plot_flow('weekly', False)
    # fig.plot_flow('monthly', False)
    #
    # fig.plot_overview()  # Finance and storage overview
    # fig.plot_dv_flow(3, 'week')     # Detailed flow of storage system, unit: 'day', 'week'
    #
    # # fig.plot_finance()      # Finance overview
    # # fig.plot_capacity()     # Storage capacity
    #
    # show_figs()     # show figures

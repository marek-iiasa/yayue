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
# from sms1_1 import *  # handles sub model/block of AF and links to the core/substantive model
from sms2 import *  # handles sub model/block of AF and links to the core/substantive model
from dat_process import *  # data processing
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

    # prepare parameters
    # data processing (if needed; if not, comment from 'f_data_base' to 'modify_periods')
    # f_data_base = f'{data_dir}test_base.dat'         # select the base data with whole periods
    # f_data = f'{data_dir}test1680.dat'              # parameter file for creating model instance
    # modify_periods(f_data_base, f_data, 1680)     # data processing, select the time period

    # f_data = f'{data_dir}dat1.dat'              # real data test by ZZ
    # f_data = f'{data_dir}test1.dat'           # small scale data for testing the model
    f_data = f'{data_dir}sms2.dat'           # small scale data for testing the model
    # f_data = f'{path}/Local/test2.dat'          # test data for sms1_1
    # f_data = f'{path}/Local/sms2.dat'          # test data
    # f_data = f'{path}/Local/sms2.1.1.dat'          # test data

    # data processing by Excel
    # f_data_base = f'{dat_dir}Raw/dat_base.xlsx'       # original data from Excel
    # f_data = f'{data_dir}dat_base.dat'                # prepare ample format file
    # par = Params(dat_dir, f_data, af_name, 8760)  # prepare all model parameters or select certain time periods
    # par.write_to_excel()      # write all parameters to Excel

    model = inst(abst, f_data)      # create model

    # add energy storage systems
    ess = Storage(model)
    ess.set_ess()

    # print the model
    print(f'\nAnalysing instance of model {model.name}.')
    # model.pprint()

    # select solver
    print('\nsolving --------------------------------')

    # glpk settings
    # opt = pe.SolverFactory('glpk')
    # opt.options['log'] = f'{res_dir}glpk_log.txt'
    # # opt.options['wmps'] = f'{res_dir}glpk.mps'  # glpk
    # results = opt.solve(model, tee=True)  # True to pipe output to the terminal

    # cplex settings
    opt = pe.SolverFactory('gams')  # gams can be used as a solver
    results = opt.solve(model, solver='cplex', symbolic_solver_labels=True, tee=True,
                        add_options=['GAMS_MODEL.optfile = 1;', '$onecho > cplex.opt', 'mipkappastats 1', '$offecho'])

    # opt = pe.SolverFactory('cplex')     # cplex can be used as a solver
    # results = opt.solve(model, tee=True)     # True to pipe output to the terminal

    # other solvers
    # opt = pe.SolverFactory('gurobi')
    # # opt.options['LogFile'] = f'{res_dir}gurobi.log'  # save log file
    # results = opt.solve(model, tee=True)
    # # opt = pe.SolverFactory('ipopt')  # solves both LP and NLP

    chk_sol(results)  # check the status of the solution

    # todo: clarify exception (uncomment next line) while loading the results
    # model.load(results)  # Loading solution into results object

    print('\nprocessing solution --------------------------------')

    # reporting results
    rep_vars = ['sNum', 'sCap', 'supply', 'revenue', 'income',
                'storCost', 'balCost',
                'invCost', 'OMC', 'splsCost', 'buyCost',
                # 'eBought', 'eSurplus',
                # 'dOut', 'sIn', 'sInb', 'sInc', 'sIna',
                # 'sOut', 'sOutb', 'sOutc', 'sOuta',
                # 'eSurplus', 'eBought', 'eVol', 'ecVol'
                ]
    print(f'Values of the following variables will be extracted from the solution and stored in the df:\n{rep_vars}')

    rep = Report(model, res_dir, rep_vars)      # report results
    rep.var_vals()  # extract from the solution values of the requested variables
    rep.summary()  # store the extracted values in a df
    # rep.check()  # check storage flow results
    # # rep.toExcel()   # store the extracted values in Excel for plotting
    # rep.toCsv()     # store the extracted values in the csv file for plotting
    #
    # print(f'\nPlace holder for report results of model {model.name}.')
    # rep.decision_var()  # show the decision variable
    # rep.analyze()  # analyze the results
    #
    # print('\nPlotting begins ----------------------------------------------------------------')
    # fig = Plot(res_dir, fig_dir, f_data)
    # #
    # # # Flow overview, 'hourly', 'daily', 'weekly', 'monthly', 'original' flows; 'original' use for model test results
    # # # 'kaleido' is needed for fig_save: True
    # fig.plot_supply('hourly', False, True, False)
    # fig.plot_inflow('hourly', False, True, False)
    # fig.plot_supply('daily', False, True, False)
    # fig.plot_inflow('daily', False, True, False)
    # #
    # # # fig.plot_flow('original', True, True, True)
    # # # fig.plot_flow('hourly', True, True, True)
    # # # fig.plot_flow('daily', fig_show=True)
    # # # fig.plot_flow('weekly', fig_show=True)
    # # # fig.plot_flow('monthly', fig_show=True)
    # #
    # # # Finance and storage investment overview
    # # fig.plot_overview_sep()
    #
    # fig.plot_overview()
    #
    # # # Detailed flow, unit: 'day', 'week'
    # # # fig.plot_dv_flow(100, 'day')
    # # # fig.plot_dv_flow(15, 'week')
    # #
    # show_figs()  # show figures

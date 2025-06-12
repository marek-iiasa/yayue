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
from sms3 import *      # symbolic model specification
# from dat_process import *  # data preprocessing
from report import *    # report all variables and needed results for plotting
from plot import *      # plot needed variables
from stor_dur import *  # analyze storage duration


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
    abst = SMS()    # initialize model class that generates model instance

    # prepare parameters
    # data processing (if needed; if not, comment from

    # f_data = f'{data_dir}sms3_1.dat'           # small grout data for sms3.py
    # f_data = f'{data_dir}sms3_CAES.dat'  # ESS with CAESS data for sms3.py
    f_data = f'{data_dir}sms3_all.dat'  # small grout data for sms3.py

    # data processing by Excel
    # f_data_base = f'{dat_dir}Raw/dat_base.xlsx'       # original data from Excel
    # f_data = f'{data_dir}dat_base.dat'                # prepare ample format file
    # par = Params(dat_dir, f_data, af_name, 8760)  # prepare all model parameters or select certain time periods
    # par.write_to_excel()      # write all parameters to Excel

    model = inst(abst.m, f_data)      # create model

    # ess = Storage(model)        # revise storage
    # ess.revise()

    # print the model
    print(f'\nAnalysing instance of model {model.name}.')
    # model.pprint()    # print model var, params, constraints...

    # select solver
    # print('\nsolving --------------------------------')

    # cplex
    opt = pe.SolverFactory('cplex')  # cplex can be used as a solver
    results = opt.solve(model, tee=True)  # True to pipe output to the terminal

    # glpk settings
    # opt = pe.SolverFactory('glpk')
    # opt.options['log'] = f'{res_dir}glpk_log.txt'
    # # opt.options['wmps'] = f'{res_dir}glpk.mps'  # glpk
    # results = opt.solve(model, tee=True)  # True to pipe output to the terminal

    # Gams settings
    # opt = pe.SolverFactory('gams')  # gams can be used as a solver
    # results = opt.solve(model, solver='cplex', symbolic_solver_labels=True, tee=True,
    #                     add_options=['GAMS_MODEL.optfile = 1;', '$onecho > cplex.opt', 'mipkappastats 1', '$offecho'])
    # use cplex through gams, save cplex's Kappa stats, analyze the numerical stability of the model.

    # other solvers
    # opt = pe.SolverFactory('gurobi')
    # opt.options['LogFile'] = f'{res_dir}gurobi.log'  # save log file
    # results = opt.solve(model, tee=True)

    # # opt = pe.SolverFactory('ipopt')  # solves both LP and NLP

    chk_sol(results)  # check the status of the solution

    print('\nprocessing solution --------------------------------')
    # reporting results
    # rep_vars = ['sNum', 'sCap', 'supply', 'revenue', 'income',
    #             'invCost', 'OMC', 'splsCost', 'buyCost',
    #             ]
    rep_vars = ['eNum', 'eCap', 'sNum', 'sCap', 'xNum', 'xCap', 'supply', 'revenue', 'income',
                'storCost', 'invCost', 'OMC', 'balCost', 'splsCost', 'buyCost',
                ]
    print(f'Values of the following variables will be extracted from the solution and stored in the df:\n{rep_vars}')

    rep = Report(model, res_dir, rep_vars)      # report results
    rep.var_vals()  # extract from the solution values of the requested variables
    rep.summary()   # store the extracted values in a df
    rep.check()     # check storage flow results

    print(f'\nPlace holder for report results of model {model.name}.')
    rep.decision_var()  # show the decision variable
    rep.analyze()  # analyze the results

    plt_fin = ['revenue', 'income', 'storCost', 'balCost', 'invCost', 'OMC', 'splsCost', 'buyCost',]
    plt_stor = ['rInv', 'rOMC']
    plt_bal = ['Spls', 'Buy']
    plt_cap = ['eNum', 'eCap', 'sNum', 'sCap', 'xNum', 'xCap']
    plt_sup = ['supply', 'avg_inf', 'tot_eOut', 'tot_eInHess', 'tot_eOutHess', 'eSurplus', 'eBought']
    plt_flow = ['inflow', 'eOut', 'eInHess', 'eS', 'eOutHess', 'eB']  # only indexed by t
    plt_flow_dev = ['eInr', 'eOutr', 'eIne', 'eIns', 'xOute', 'xIns', 'xVol', 'xOuts', 'xInx', 'eOutx']

    print(f'Values of the plotting variables will be extracted from the solution and stored in the df:')

    rep.to_plt_df(plt_fin, plt_stor, plt_bal, plt_cap, plt_sup, plt_flow, plt_flow_dev)   # store vals for plotting
    rep.to_Excel()  # store the extracted values
    rep.sflow_toCsv()
    # rep.toCsv()     # store the extracted values in the csv file for plotting

    print(f'\n ESSs storage duration analysis begins -----------------------------------------')
    sflow_file = 'flow_s.csv'
    sdur_file = 'sDur.csv'
    dur_df = stor_dur(res_dir, sflow_file)
    ess_dur = sum_stor_dur(dur_df)

    # print(dur_df.head(5))
    print(f'ESSs storage duration: {ess_dur}')

    dur_df.to_csv(f'{res_dir}{sdur_file}', index=False)
    print(f'\nStorage duration time is stored in {res_dir}{sdur_file}.')

    print(f'\nPlotting begins ----------------------------------------------------------------')
    fig = Plot(res_dir, fig_dir, f_data)
    sdate = '2024-01-01 00:00'

    fig.plot_finance()      # Finance overview, Income-Cost-Revenue
    fig.plot_CS_3()         # Cost structure
    # # fig.plot_cap_tab()      # Storage capacity table (Latex)

    # Flow overview, 'hourly', 'daily', 'weekly', 'monthly', 'original' flows; 'original' use for model test results
    # 'kaleido' is needed for fig_save: True
    fig.plot_flow('daily', sdate, False, True, True)
    # fig.plot_supply('daily', sdate, False, True, False)
    # fig.plot_inflow('daily', sdate, False, True, False)
    fig.plot_inflow('monthly', sdate, True, True, True)
    fig.plot_ESS_stor(sdate, 'Annual')
    fig.plot_ESS_stor(sdate, 'Monthly')

    # Fig.plot_dev_flow(10, 'week')  # Detailed flow of storage system, unit: 'day', 'week'

    show_figs()  # show figures

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
from dat_process import Params  # data processing
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
    if not os.path.exists(fig_dir):
        os.makedirs(fig_dir, mode=0o755)
        print(f'Directory {fig_dir} created')

    # make model
    abst = mk_sms()    # initialize Model class that generates model instance (ConcreteModel)
    # f_data = f'{data_dir}dat1.xlsx'      # test by ZZ
    # af_name = f'dat1'       # define filename of ampl format data file
    f_data = f'{data_dir}test1.xlsx'  # constant inflow test by ZZ
    af_name = f'test1'

    # data processing: select the number of hours the model runs by changing n_periods
    par = Params(data_dir, f_data, af_name, 8760)  # prepare all model parameters
    # par = Params(data_dir, f_data, af_name, 8760)  # Optimization failed by using glpk
    par.write_to_ampl()     # write model parameters to ampl format file
    par.write_to_excel()    # write model parameters to excel file

    af_data = f'{data_dir}{af_name}.dat'    # test by ZZ
    # f_data = f'{data_dir}tst1.dat'    # test by MM
    model = inst(abst, af_data)
    print(f'\nAnalysing instance of model {model.name}.')

    # model.pprint()

    print('\nsolving --------------------------------')
    # select solver

    # opt = pe.SolverFactory('glpk')
    # opt.options['write'] = f'{res_dir}model.nps'  # glpk

    opt = pe.SolverFactory('ipopt')  # solves both LP and NLP
    # opt = pe.SolverFactory('gams')  # gams can be used as a solver
    # results = opt.solve(model, tee=True, options={'solnFile': 'cplex.sol'}) # gams solver configuration
    results = opt.solve(model, tee=True)   # True to pipe output to the terminal
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
    rep.check()  # check storage flow results
    rep.toExcel()   # store the extracted values in Excel for plotting

    print(f'\nPlace holder for report results of model {model.name}.')
    rep.analyze()  # analyze the results

    print('\nPlotting begins ----------------------------------------------------------------')
    fig = Plot(res_dir, fig_dir)
    fig.plot_overview()     # Finance and storage overview
    fig.plot_flow()         # Flow overview
    # fig.plot_finance()      # Finance overview
    # fig.plot_capacity()     # Storage capacity
    fig.plot_dv_flow()      # Detailed flow of storage system
    # plt.show()
    # plt.close()

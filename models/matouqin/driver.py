"""
Prototype of the Matouqin driver
"""
# import os.path

import sys		# needed for sys.exit()
# import os
# import pandas as pd
# import pyomo.environ as pe
from pyomo.opt import SolverStatus
from pyomo.opt import TerminationCondition
from inst import *
from sms import *  # handles sub model/block of AF and links to the core/substantive model
# from params import Params
from report import *
from test import *


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
    fig_dir = f'{path}/Figures/'    # repository of figures

    # make model
    abst = mk_sms()    # initialize Model class that generates model instance (ConcreteModel)
    # par = Params()  # prepare all model parameters
    f_data = f'{data_dir}dat1.dat'    # test by ZZ
    # f_data = f'{data_dir}tst1.dat'    # test by MM
    model = inst(abst, f_data)
    print(f'\nAnalysing instance of model {model.name}.')

    # model.pprint()

    print('\nsolving --------------------------------')
    # select solver
    opt = pe.SolverFactory('glpk')
    # opt = pe.SolverFactory('ipopt') # solves both LP and NLP
    # opt = SolverFactory('gams')  # gams can be used as a solver
    # opt = SolverFactory('gams')  # gams can be used as a solver
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
    rep.var_vals()  # extract from the solution values of the requessted variables
    rep.summary()  # store the extracted values in a df

    # flow_vars = ['hVol']
    # flow = Report(model, res_dir, flow_vars)
    # flow.flow_report()
    # flow.summary()

    print(f'\nPlace holder for report results of model {model.name}.')
    # revenue = f'{pe.value(model.revenue):.3e}'      # scientific counting method, accurate to three decimal place
    print('\nValues of inflow ----------------------------------------------------------------------------')
    # m.inflow.display()
    ave_inflow = sum(model.inflow[t] for t in model.T) / model.nHrs
    print(f'Average inflow = {ave_inflow} MW')

    print('\nValues of decision variables ------------------------------------------------------------------------')
    print(f'Supply = {pe.value(model.supply)} MW')
    # for i in model.sNum_index:
    #    print(f'sNum[{i}] = {pe.value(m.sNum[i])}')
    # for i in model.sCap_index:
    #    print(f'sCap[{i}] = {pe.value(m.sCap[i])}')
    model.sNum.display()
    model.sCap.display()
    # print(f'Numbers of storage devices = {pe.value(m.sNum)}')

    # print('\nEnergy flows ------------------------------------------------------------------------')
    # model.supply.display()
    # model.eSurplus.display()
    # model.eBought.display()
    # model.dOut.display()
    # model.eIn.display()
    # model.hIn.display()
    # model.hOut.display()
    # model.ePrs.display()
    # model.mxIn.display()
    # model.hVol.display()
    # model.cOut.display()

    print('\nValues of outcome variables -------------------------------------------------------------------------')
    print(f'Total revenue  = {pe.value(model.revenue)} million RMB')
    print(f'Income  = {pe.value(model.income)} million RMB')
    print(f'Investment cost  = {pe.value(model.invCost)} million RMB')
    print(f'Operation and maintenance cost  = {pe.value(model.OMC)} million RMB')
    print(f'Surplus cost  = {pe.value(model.overCost)} million RMB')
    print(f'Shortage cost  = {pe.value(model.buyCost)} million RMB')
    print(f'Balance cost  = {pe.value(model.balCost)} million RMB')

# ----------------------------------------------------------------
# plotting
    Plot(model, fig_dir)

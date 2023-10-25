# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.
# See PyCharm help at https://www.jetbrains.com/help/pycharm/
# PyCharm > select "File" menu > select "Invalidate Caches / Restart" menu option
#   noinspection PyUnresolvedReferences
#   infty = float('inf')

""" Prototype of the Pipa model. """
import sys		# needed for stdout and sys.exit()
# import os
# import pandas as pd
from os import R_OK, access
from os.path import isfile
import dill
from datetime import datetime as dt
# from datetime import timedelta as td

from pyomo.opt import SolverStatus
from pyomo.opt import TerminationCondition
from sms import *       # returns SMS; NOTE: pyomo has to be imported in sms (otherwise is unknown there)
from inst import *      # return model instance
from report import *    # report and store results


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


# noinspection SpellCheckingInspection
if __name__ == '__main__':
    tstart = dt.now()
    # print('Started at:', str(tstart))
    # directories/folders
    # path = '/Users/marek/Documents/Github/yayue/models/pipa/'
    path = '.'
    os.chdir(path)
    out_dir = './Out_dir/'
    data_dir = f'{path}/Data/'
    mod_dir = f'{path}/Models/'     # repository of dll-format model instances
    res_dir = f'{path}/Results/'    # repository of results
    for sdir in [out_dir, mod_dir, res_dir]:
        if not os.path.exists(sdir):
            os.makedirs(sdir, mode=0o755)
            print(f'Directory "{sdir} created.')
    m_name = 'pipa'     # model name (used for the dll-format file-name
    # files
    f_out = f'{out_dir}stdout.txt'    # optionally redirected stdout
    f_data = f'{data_dir}dat3.dat'    # data for defining the model instance
    f_mod = f'{mod_dir}{m_name}.dll'  # concrete model in dill format

    assert isfile(f_data) and access(f_data, R_OK), f'Data file {f_data} not readable.'

    redir_stdo = False  # optional redirection of stdout to out_dir/stdout.txt
    default_stdout = sys.stdout
    if redir_stdo:
        assert not os.path.exists(f_out), f'Rename/remove the already used file for redirecting stdout: "{f_out}"'
        print(f'Stdout redirected to: {f_out}')
        redir_out = open(f_out, 'w')
        sys.stdout = redir_out
    else:
        redir_out = None

    # noinspection SpellCheckingInspection
    abst = mk_sms()         # generate abstract model (SMS)
    model = inst(abst, f_data)  # generate model instance
    # model.P.pprint()
    # model.H.pprint()
    # print('Values of the discount factor for each planning period:')
    for p in model.P:   # define discount rates for each period
        model.dis[p] = (1. - model.discr) ** p
        # print(f'p = {p}, dis = {pe.value(model.dis[p]):.3f}')

    # print('\nmodel display: -----------------------------------------------------------------------------')
    # # (populated) variables with bounds, objectives, constraints (with bounds from data but without definitions)
    # model.display()     # displays only instance (not abstract model)
    # print('end of model display: ------------------------------------------------------------------------\n')
    # members of sets, then param values, then (populated by set-members) relations with actual coef-values
    # print('\n model.pprint() follows:      -----------------------------------------------------------------')
    # model.pprint()
    # print('end of model printout          -----------------------------------------------------------------\n')

    with open(f_mod, 'wb') as f:  # Serialize and save the Pyomo model
        dill.dump(model, f)
    print(f'Model "{m_name}" generated and dill-dumpped to: {f_mod}')

    # vars to be reported and stored in df (the list may include any variable name defined in the SMS)
    rep_vars = ['cost', 'invT', 'oilImp', 'carb', 'actS', 'act', 'actvS', 'cap']
    print(f'Values of the following variables will be extracted from the solution and stored in the df:\n{rep_vars}')
    # report ctor
    rep = Report(model, res_dir, rep_vars)  # Report ctor

    # opt = SolverFactory('ipopt')  # IPM solver might be better for large & sparse or NL problems
    opt = pe.SolverFactory('glpk')
    print(f'\nSolving the optimization problem.   ------------')
    results = opt.solve(model, tee=False)
    chk_sol(results)  # check the status of the solution

    cost = f'{pe.value(model.cost):.3e}'
    invT = f'{pe.value(model.invT):.3e}'
    oil_imp = f'{pe.value(model.oilImp):.3e}'
    carb = f'{pe.value(model.carb):.3e}'  # amount of carbon emission
    carbC = f'{pe.value(model.carbC):.3e}'  # discounted cost of carbon emission
    print('\nValues of outcome variables -----------------------------------------------------------------------------')
    print(f'Total cost  = {cost}')
    print(f'Total investments  = {invT}')
    print(f'Imported crude oil = {oil_imp}')
    print(f'Carbon emission = {carb}')
    print(f'Carbon emission (discounted) cost = {carbC}')

    rep.var_vals()  # extract from the solution values of the requessted variables
    rep.summary()   # store the extracted values in a df

    tend = dt.now()
    print('\nStarted at: ', str(tstart))
    print('Finished at:', str(tend))
    time_diff = tend - tstart
    print(f'Wall-clock execution time: {time_diff.seconds} sec.')

    if redir_stdo:  # close the redirected output
        redir_out.close()
        sys.stdout = default_stdout
        print(f'\nRedirected stdout stored in {f_out}.\nNow writing to the console.')
        print('\nStarted at: ', str(tstart))
        print('Finished at:', str(tend))
        print(f'Wall-clock execution time: {time_diff.seconds} sec.')

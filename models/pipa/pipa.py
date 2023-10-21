# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.
# See PyCharm help at https://www.jetbrains.com/help/pycharm/
# PyCharm > select "File" menu > select "Invalidate Caches / Restart" menu option
#   noinspection PyUnresolvedReferences
#   infty = float('inf')

""" Prototype of the Pipa model. """
import sys		# needed for sys.exit()
import os
# import pandas as pd
import dill
from datetime import datetime as dt
# from datetime import timedelta as td

from sms import *       # returns SMS; NOTE: pyomo has to be imported in sms (otherwise is unknown there)
from inst import *      # return model instance
from report import *    # report and store results

# noinspection SpellCheckingInspection
if __name__ == '__main__':
    tstart = dt.now()
    # print('Started at:', str(tstart))
    path = '/Users/marek/Documents/Github/yayue/models/pipa/'
    os.chdir(path)
    out_dir = './Out_dir/'

    redir_stdo = False  # optional redirection of stdout to out_dir/stdout.txt
    default_stdout = sys.stdout
    if redir_stdo:
        if not os.path.exists(out_dir):
            os.makedirs(out_dir, mode=0o755)
        fn_out = out_dir + 'stdout.txt'  # file for redirected stdout
        print(f'Stdout redirected to: {fn_out}')
        f_out = open(fn_out, 'w')
        sys.stdout = f_out
    else:
        fn_out = None
        f_out = None

    # noinspection SpellCheckingInspection
    abst = mk_sms()        # abstract model (SMS)
    model = instance(abst)  # model instance
    # model.P.pprint()
    # model.H.pprint()
    # print('Values of the discount factor for each planning period:')
    for p in model.P:   # define discount rates for each period
        model.dis[p] = (1. - model.discr) ** p
        # print(f'p = {p}, dis = {pe.value(model.dis[p]):.3f}')

    # model.write('test.lp')
    # model.write('test.mps')
    # model.write('test.gms')
    # model.write('test2.lp', symbolic_solver_labels=True)  # illegal param: symbolic...

    # print('\nmodel display: -----------------------------------------------------------------------------')
    # # (populated) variables with bounds, objectives, constraints (with bounds from data but without definitions)
    # model.display()     # displays only instance (not abstract model)
    # print('end of model display: ------------------------------------------------------------------------\n')
    print('\n model.pprint() follows:      -----------------------------------------------------------------')
    # members of sets, then param values, then (populated by set-members) relations with actual coef-values
    model.pprint()
    print('end of model printout          -----------------------------------------------------------------\n')

    m_name = 'pipa'
    f_name = f'{m_name}.dll'
    with open(f_name, 'wb') as f:  # Serialize and save the Pyomo model
        dill.dump(model, f)
    print(f'Model "{m_name}" generated and dill-dumpped to: {f_name}')

    # report ctor
    rep_vars = ['cost', 'oilImp', 'carb']  # list of variables to be reported and stored in df
    rep = Report(model, './Rep', rep_vars)

    # opt = SolverFactory('gams')  # gams can be used as a solver
    opt = pe.SolverFactory('glpk')
    result_obj = opt.solve(model, tee=True)
    cost = f'{pe.value(model.cost):.3e}'
    oil_imp = f'{pe.value(model.oilImp):.3e}'
    carb = f'{pe.value(model.carb):.3e}'  # amount of carbon emission
    carbC = f'{pe.value(model.carbC):.3e}'  # discounted cost of carbon emission
    print('\nValues of outcome variables -----------------------------------------------------------------------------')
    print(f'Total cost  = {cost}')
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
        f_out.close()
        sys.stdout = default_stdout
        print(f'\nRedirected stdout stored in {fn_out}.\nNow writing to the console.')
        print('\nStarted at: ', str(tstart))
        print('Finished at:', str(tend))
        print(f'Wall-clock execution time: {time_diff.seconds} sec.')

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.
# See PyCharm help at https://www.jetbrains.com/help/pycharm/
# PyCharm > select "File" menu > select "Invalidate Caches / Restart" menu option
#   noinspection PyUnresolvedReferences
#   infty = float('inf')

"""
Prototype of the China liquid fuel production model.
The prototype is in the initial development stage.
Substantial changes are forthcoming; therefore, please use it with care.
"""
import sys		# needed for sys.exit()
import os
# import pandas as pd
from datetime import datetime as dt
# from datetime import timedelta as td

from sms import *       # returns SMS; NOTE: pyomo has to be imported in sms (otherwise is unknown there)
from inst import *      # return model instance

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
    # print('Values of discount rates for each planning period:')
    # for p in model.P:   # define discount rates for each period
    #     model.dis[p] = model.discr ** p
    #     print(f'p = {p}, dis = {pe.value(model.dis[p]):.3f}')

    # model.write('test.lp')
    # model.write('test.mps')
    # model.write('test.gms')
    # model.write('test2.lp', symbolic_solver_labels=True)  # illegal param: symbolic...

    # print('\nmodel display: -----------------------------------------------------------------------------')
    # # (populated) variables with bounds, objectives, constraints (with bounds from data but without definitions)
    # model.display()     # displays only instance (not abstract model)
    # print('end of model display: ------------------------------------------------------------------------\n')
    # print('\n model.pprint() follows:      -----------------------------------------------------------------')
    # # members of sets, then param values, then (populated by set-members) relations with actual coef-values
    # model.pprint()
    # print('end of model printout          -----------------------------------------------------------------\n')

    # opt = SolverFactory('gams')  # gams can be used as a solver
    opt = pe.SolverFactory('glpk')
    result_obj = opt.solve(model, tee=True)
    cost = f'{pe.value(model.cost):.5e}'
    co2 = f'{pe.value(model.carb):.5e}'  # carbon emission
    oil_imp = f'{pe.value(model.oilImp):.5e}'
    print('\nValues of outcome variables -----------------------------------------------------------------------------')
    print(f'Total cost  = {cost}')
    print(f'CO2 emission = {co2}')
    print(f'Imported crude oil = {oil_imp}')

    # TODO: add storing selected (tdb which are needed) variables

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

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
# PyCharm > select "File" menu > select "Invalidate Caches / Restart" menu option
#   noinspection PyUnresolvedReferences
#   infty = float('inf')

"""
Prototype of the MCMA
"""
# import sys		# needed for sys.exit()
import os
# import pandas as pd
from datetime import datetime as dt
# from datetime import timedelta as td

from driver import *  # driver (run the analysis set-up and iterations)

# import from remote dir does no work
# sys.path.append('/Users/marek/Documents/GitHub/yayue/models/pipa/pipa0')
# sys.path.append('../pipa/pipa0')
# import sms as pipa_sms  # pipa, initial versions
# from inst import instance as pipa_ins  # ditto
# the below imports work, if files are in the same dir, the above needs to be explored/modified
# todo: explore robust import from remote dir
# from sms import mk_sms as pipa_sms  # pipa, initial versions
# from inst import instance as pipa_ins  # ditto
# from t3sms import mk_sms as sms3  # tiny, testing model
# from t3inst import mk_inst as ins3  # ditto
from t4conc import mk_conc as conc4  # tiny testing model, developed as concrete (without abstract)


def mk_mod1():  # generate the core model
    # abst = pipa_sms()  # pipa abstract model (SMS)
    # mod1 = pipa_ins(abst)  # pipa model instance
    # abst = sms3()  # tiny test abstract model (SMS)
    # mod1 = ins3(abst)  # tiny test model instance
    mod1 = conc4()  # tiny test model instance (without its abstract model)
    return mod1


# noinspection SpellCheckingInspection
if __name__ == '__main__':
    tstart = dt.now()
    # print('Started at:', str(tstart))
    # wrk_dir = '/Users/marek/Documents/GitHub/yayue/models/mcma'
    wrk_dir = './'  # might be modified by each user
    os.chdir(wrk_dir)
    print(f'wrk_dir: {wrk_dir}')
    out_dir = './Out_dir/'

    redir_stdo = False  # optoional redirection of stdout to out_dir/stdout.txt
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

    print(f'\nGenerating instance of the core model.')
    m1 = mk_mod1()  # generate core model: first an abstract model and then the corresponding concerete model
    # print('\ncore model display: -----------------------------------------------------------------------------')
    # m1.pprint()
    # print('end of model display: ------------------------------------------------------------------------\n')

    # todo: find name/object of the objective, its name is had-coded
    m1.goal.deactivate()    # the goal name is hard-coded
    print(f'core model objective (named: goal) deactivated.')
    # none of the attempts commented below work
    # m1_obj = m1.component_map(ctype=pe.Objective)  # all objectives of the m1 (core model)
    # print(f'{m1_obj=}')
    # print(f'm1_obj = {m1_obj}')
    # print(f'{type(m1_obj)=}')
    # m1_obj.display()
    # m1_obj.pprint()
    # m1_obj.print()
    # print(f'{m1_obj.name=}, {m1_obj=}')

    driver(m1, './Data/test1')

    tend = dt.now()
    print('\nStarted at: ', str(tstart))
    print('Finished at:', str(tend))
    time_diff = tend - tstart
    print(f'Wall-clock execution time: {time_diff.seconds} sec.')

    if redir_stdo:  # close the redirected output
        f_out.close()
        sys.stdout = default_stdout
        print(f'\nRedirected stdout stored in {fn_out}. Now writing to the console.')
        print('\nStarted at: ', str(tstart))
        print('Finished at:', str(tend))
        print(f'Wall-clock execution time: {time_diff.seconds} sec.')

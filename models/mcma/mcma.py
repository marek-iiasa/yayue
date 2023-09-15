# See PyCharm help at https://www.jetbrains.com/help/pycharm/
# PyCharm > select "File" menu > select "Invalidate Caches / Restart" menu option
#   noinspection PyUnresolvedReferences
#   infty = float('inf')

"""
Prototype of the MCMA
"""
# import sys		# needed for sys.exit()
import os
from os import R_OK, access
from os.path import isfile
# import pandas as pd
# import pickle     # pickle does not process relations defined with decorations (without decorations processed ok)
import dill     # stores and retrieves pyomo models into/from binary file (porting between different OSs not tested yet)
from datetime import datetime as dt
# from datetime import timedelta as td

from driver import *  # driver (run the analysis set-up and iterations)

# import from remote dir does no work
# sys.path.append('/Users/marek/Documents/GitHub/yayue/models/pipa/pipa0')
# sys.path.append('../pipa/pipa0')
# from sms import mk_sms as pipa_sms  # pipa, initial versions
# from inst import instance as pipa_ins  # ditto
# the below imports work, if files are in the same dir, the above needs to be explored/modified
# todo: explore robust import from remote dir
# from sms import mk_sms as pipa_sms  # pipa, initial versions
# from inst import instance as pipa_ins  # ditto
# from t3sms import mk_sms as sms3  # tiny, testing model
# from t3inst import mk_inst as ins3  # ditto
# from t4conc import mk_conc as conc4  # tiny testing model, developed as concrete (without abstract)
from tspipa import sbPipa as sbPipa  # sand-box tiny Pipa testing model, developed as concrete (without abstract)


def mk_mod1():  # generate the core model
    # abst = pipa_sms()  # pipa abstract model (SMS)
    # mod1 = pipa_ins(abst)  # pipa model instance
    # abst = sms3()  # tiny test abstract model (SMS)
    # mod1 = ins3(abst)  # tiny test model instance
    # mod1 = conc4()  # tiny test (Pipa-like) model instance (without its abstract model)
    mod1 = sbPipa()  # tiny test (Pipa-like) model instance (without its abstract model)
    return mod1
    # raise Exception(f'mk_mod1(): no model specified.')


# noinspection SpellCheckingInspection
if __name__ == '__main__':
    tstart = dt.now()
    # print('Started at:', str(tstart))
    # wrk_dir = '/Users/marek/Documents/GitHub/yayue/models/mcma'
    wrk_dir = './'  # might be modified by each user
    os.chdir(wrk_dir)
    print(f'wrk_dir: {wrk_dir}')
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

    print(f'\nLoading or generating instance of the core model.')
    # m1 = mk_mod1()  # generate core model: first an abstract model and then the corresponding concerete model
    m_name = 'sbPipa'
    # m_name = 'pipa0'
    f_name = f'Models/{m_name}.dll'     # alternatively the 'dill' file extension is used
    if not (isfile(f_name) and access(f_name, R_OK)):   # generate and store the model, if not yet stored
        m2store = mk_mod1()  # generate core model:
        # Serialize and save the Pyomo model
        with open(f_name, 'wb') as f:
            dill.dump(m2store, f)
        print(f'Model "{m_name}" generated and dumpped to: {f_name}')
    # Load the serialized Pyomo model
    with open(f_name, 'rb') as f:
        m1 = dill.load(f)
    print(f'\nThe stored model "{m_name}" loaded from {f_name}')

    '''
    # exploring storing the model by pickle; negative:
    # pickle.dump(m2store, f)
    # AttributeError: Can't pickle local object 'sbPipa.<locals>.actC'
    # if hasattr(m2store, 'goal'):  # not needed, if m2store specified without decorations
    #     del m2store.goal
    #     print('Objective function removed from the model to be stored by pickle.')
    with open("m1.pkl", "wb") as f:     # store for testing
        pickle.dump(m2store, f)

    # retrieve (just for testing)
    with open("m1.pkl", "rb") as f:
        m1 = pickle.load(f)
    '''
    print('\ncore model display: -----------------------------------------------------------------------------')
    m1.pprint()
    print('end of model display: ------------------------------------------------------------------------\n')

    for obj in m1.component_data_objects(pe.Objective):
        print(f'Objective "{obj}" deactivated.')
        obj.deactivate()
    '''
    # the below loop deactivates the objectives, can also be adapted for finding types of any model objects
    for component_name, component in m1.component_map().items():
        c_type = str(type(component))
        # print(f'Component: name = {component_name}, type: {c_type}')
        # if str(type(component)) == "<class 'pyomo.core.base.objective.SimpleObjective'>": # GPT (wrong) suggestion
        if str(type(component)) == "<class 'pyomo.core.base.objective.ScalarObjective'>":   # corrected GPT suggestion
            print(f'objective name: "{component_name}" deactivated.')
            component.deactivate()
    # obj_name = 'goal'
    # if hasattr(m1, obj_name):
    #     print(f'Objective function {obj_name} removed from the core model')
    #     del m1.obj_name
    '''

    driver(m1, './Data/test2')  # m1 - core model, str: persistent data repository (dedicated for each MC-analysis)
    # driver(m1, './Data/test2')  # m1 - core model, str: persistent data repository (dedicated for each MC-analysis)

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

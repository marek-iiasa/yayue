# import sys		# needed for sys.exit()
# import os
from os import R_OK, access
from os.path import isfile
import dill     # stores and retrieves pyomo models into/from binary file (porting between different OSs not tested yet)
import pyomo.environ as pe       # more robust than using import *
# import pandas as pd
# import pickle     # pickle does not process relations defined with decorations (without decorations processed ok)
# from datetime import datetime as dt
# from datetime import timedelta as td

# import from remote dir does no work
# sys.path.append('/Users/marek/Documents/GitHub/yayue/models/pipa/pipa0')
# sys.path.append('../pipa/pipa0')
# from sms import mk_sms as pipa_sms  # pipa, initial versions
# from inst import instance as pipa_ins  # ditto
# the below imports work, if files are in the same dir, the above needs to be explored/modified
# from sms import mk_sms as pipa_sms  # pipa, initial versions
# from inst import instance as pipa_ins  # ditto
# from t3sms import mk_sms as sms3  # tiny, testing model
# from t3inst import mk_inst as ins3  # ditto
# from t4conc import mk_conc as conc4  # tiny testing model, developed as concrete (without abstract)
# from tspipa import sbPipa as sbPipa  # sand-box tiny Pipa testing model, developed as concrete (without abstract)
# from tsjg1 import jg1 as jg1  # sand-box tiny jg1 model


def mk_mod():  # load or generate the core model
    # abst = pipa_sms()  # pipa abstract model (SMS)
    # mod1 = pipa_ins(abst)  # pipa model instance
    # abst = sms3()  # tiny test abstract model (SMS)
    # mod1 = ins3(abst)  # tiny test model instance
    # mod1 = conc4()  # tiny test (Pipa-like) model instance (without its abstract model)
    # mod1 = sbPipa()  # tiny test (Pipa-like) model instance (without its abstract model)
    # mod1 = jg1()  # tiny test (Pipa-like) model instance (without its abstract model)
    # return mod1   # return model instance
    raise Exception(f'mk_mod1(): no model specified.')


def rd_inst(cfg):  # load the core model
    # m_name = f"{cfg.get('modDir')}{cfg.get('model_id')}"
    m_name = f"{cfg.get('model_id')}"
    # print(f'\nLoading or generating instance of the core model "{m_name}".')
    f_name = f'{m_name}.dll'     # alternatively the 'dill' file extension is used
    # if not (isfile(f_name) and access(f_name, R_OK)):   # generate and store the model, if not yet stored
    #     m2store = mk_mod()  # generate core model
    #     with open(f_name, 'wb') as f:   # Serialize and save the Pyomo model
    #         dill.dump(m2store, f)
    #     print(f'Model "{m_name}" generated and dill-dumpped to: {f_name}')
    # Load the serialized Pyomo model
    assert isfile(f_name) and access(f_name, R_OK), f'Model "{f_name}" not accessible'
    with open(f_name, 'rb') as f:
        m1 = dill.load(f)
    print(f'\nThe stored model "{m_name}" loaded from the dill file "{f_name}"')

    # print('\ncore model display: -----------------------------------------------------------------------------')
    # m1.pprint()
    # print('end of model display: ------------------------------------------------------------------------\n')

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

    return m1

from os import R_OK, access
from os.path import isfile

# import cloudpickle     # stores/retrieves pyomo models into/from binary file (porting between OSs not tested yet)
import dill     # stores/retrieves pyomo models into/from binary file (porting between OSs not tested yet)
import pyomo.environ as pe       # more robust than using import *
import sms
from inst import inst      # return model instance

def ex_inst(m_name, m_data):  # load the core model
    f_name = f'{m_name}.dll'     # alternatively the 'dill' file extension is used
    # files
    f_data = f'{m_data}.dat'    # data for defining the model instance
    f_mod = f'{m_name}.dll'     # concrete model in dill format
    assert isfile(f_data) and access(f_data, R_OK), f'Data file {f_data} not readable.'
    #
    abst = sms.mk_sms()         # generate abstract model (SMS)
    model = inst(abst, f_data)  # generate model instance

    with open(f_mod, 'wb') as f:  # Serialize and save the Pyomo model
        dill.dump(model, f, byref=False, recurse=True)
    print(f'Model "{m_name}" generated and dill-dumpped to: {f_mod}')

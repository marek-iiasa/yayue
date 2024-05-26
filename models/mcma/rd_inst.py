from os import R_OK, access
from os.path import isfile
# import cloudpickle     # stores/retrieves pyomo models into/from binary file (porting between OSs not tested yet)
import dill     # stores/retrieves pyomo models into/from binary file (porting between OSs not tested yet)
import pyomo.environ as pe       # more robust than using import *


def rd_inst(cfg):  # load the core model
    m_name = f"{cfg.get('model_id')}"
    f_name = f'{m_name}.dll'     # alternatively the 'dill' file extension is used
    assert isfile(f_name) and access(f_name, R_OK), f'Model "{f_name}" not accessible'
    with open(f_name, 'rb') as f:
        # m1 = cloudpickle.load(f)
        m1 = dill.load(f)
    print(f'\nModel "{m1.name}" loaded from the dill-format file "{f_name}"')

    if cfg.get('verb') > 3:
        print('\ncore model display: -----------------------------------------------------------------------------')
        m1.pprint()
        print('end of model display: ------------------------------------------------------------------------\n')

    for obj in m1.component_data_objects(pe.Objective):
        print(f'Objective "{obj}" deactivated.')
        obj.deactivate()

    return m1

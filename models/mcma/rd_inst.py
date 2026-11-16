from os import R_OK, access
from os.path import isfile
# import cloudpickle     # stores/retrieves pyomo models into/from binary file (porting between OSs not tested yet)
import dill     # stores/retrieves pyomo models into/from binary file (porting between OSs not tested yet)
import pyomo.environ as pe       # more robust than using import *
import time


def rd_inst(cfg):  # load the core model
    '''
    a = 1
    b = 2
    time.sleep(a+b)
    print(a+b)
    '''
    m_name = f"{cfg.get('model_id')}"
    f_name = f'{m_name}.dll'     # alternatively the 'dill' file extension is used
    assert isfile(f_name) and access(f_name, R_OK), f'Model "{f_name}" not accessible'
    with open(f_name, 'rb') as f:
        # m1 = cloudpickle.load(f)
        m1 = dill.load(f)
    print(f'\nModel "{m1.name}" loaded from the dill-format file "{f_name}"')

    if cfg.get('verb') > 0:
        print('\ncore model display: -----------------------------------------------------------------------------')
        m1.pprint()
        print('end of model display: ------------------------------------------------------------------------\n')

    for obj in m1.component_data_objects(pe.Objective):
        print(f'Objective "{obj}" deactivated.')
        obj.deactivate()

    for c in m1.component_objects(pe.Constraint, active=True):
        for idx in c:
            con = c[idx]
            try:
                con.to_bounded_expression(True)
            except Exception:
                    print(f"OFFENDING: {con.name}  nargs={len(con.expr.args)}  type={type(con.expr)}")
                    print(f"  expr: {con.expr}")
#     return m1

#    for c in m.core_model.component_objects(pe.Constraint, active=True):
    for c1 in m1.component_objects(pe.Constraint, active=True):
        for idx in c1:
            con = c1[idx]
            print(f"--- {con.name}")
            print(f"    type(con)      = {type(con)}")
            print(f"    type(con.expr) = {type(con.expr)}")
            print(f"    con.expr       = {con.expr}")
            print(f"    nargs          = {len(con.expr.args)}")
            for attr in ('lower', 'upper', 'body', 'equality'):
                try:
                    print(f"    con.{attr:9s} = {getattr(con, attr)}")
                except Exception as e:
                    print(f"    con.{attr:9s} -> {e!r}")
    print('\n------------------- just before returning the model instance m1 from rd_inst()\n')
    return m1

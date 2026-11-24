from os import R_OK, access
from os.path import isfile
# import cloudpickle     # stores/retrieves pyomo models into/from binary file (porting between OSs not tested yet)
import dill     # stores/retrieves pyomo models into/from binary file (porting between OSs not tested yet)
import pyomo.environ as pe       # more robust than using import *
import pyomo


# noinspection unused-local
def rd_inst(cfg):  # load the core model
    # print('\n--- start rd_inst() ---')
    m_name = f"{cfg.get('model_id')}"
    f_name = f'{m_name}.dll'     # alternatively the 'dill' file extension is used
    assert isfile(f_name) and access(f_name, R_OK), f'Model "{f_name}" not accessible'
    '''
     old version below, using cloudpickle, kept for reference
    with open(f_name, 'rb') as f:
        # m1 = cloudpickle.load(f)
        m1 = dill.load(f)
    '''

    with open(f_name, 'rb') as f:
        payload = dill.load(f)
        if payload['pyomo_version'] != pyomo.version.version:
            raise RuntimeError(
                f"model written with Pyomo {payload['pyomo_version']}, "
                f"running {pyomo.version.version} — regenerate the .dll")
        m1 = payload['model']
    print(f'\nModel "{m1.name}" loaded from the dill-format file "{f_name}"')

    if cfg.get('verb') > 6:
        print('\ncore model display: -----------------------------------------------------------------------------')
        m1.pprint()
        print('end of model display: ------------------------------------------------------------------------\n')

    for obj in m1.component_data_objects(pe.Objective):
        print(f'Objective "{obj}" deactivated.')
        obj.deactivate()

    dllchk = False
    if not dllchk:
        return m1

    nerr = 0
    seq = 0
    print('\n------Constraint check: first loop')
    for c in m1.component_objects(pe.Constraint, active=True):
        seq += 1
        print(f"--- seq = {seq}")
        for idx in c:
            con = c[idx]
            try:
                con.to_bounded_expression(True)
                print(f"\tOK: {con.name}  nargs={len(con.expr.args)}  type={type(con.expr)}")
                print(f"\t\texpr: {con.expr}")
            except Exception:
                    nerr += 1
                    print(f"\tOFFENDING: {con.name}  nargs={len(con.expr.args)}  type={type(con.expr)}")
                    print(f"\t\texpr: {con.expr}")

    print('\n------Constraint check: second loop')
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
                    nerr += 1
                    print(f"    con.{attr:9s} -> {e!r}")

    if nerr > 0:
        # print(f'\nConstraint check failed: {nerr} errors found.')
        print(f'\n')
        assert nerr == 0, f'\n Processing of {m1.name}.dll failed: {nerr} errors.'

    # print('\n------------------- just before returning the model instance m1 from rd_inst()\n')
    return m1

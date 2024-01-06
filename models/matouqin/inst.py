import pyomo.environ as pe       # more robust than using import *


# return the model instance (currently the params are in *.dat, i.e., AMPL-like format
def inst(m, f_data):    # m: abstract/symbolic model, f_data: parameters in AMPL-like format
    # data = DataPortal()  # the default arg: (model=model) !
    # data.load(filename='data0.yaml')  # works with DataPortal() and DataPortal(model=m)
    # data.load(filename='data0.json')  # works with DataPortal() and DataPortal(model=m)
    data = pe.DataPortal(model=m)  # parameter (model=m) needed for loading *.dat
    # dat-format requires DataPortal(model=m)
    print(f'Applying data defined in "{f_data}".')
    data.load(filename=f_data)
    mod = m.create_instance(data)

    print('\n instance.pprint() follows      -----------------------------------------------------------------')
    mod.pprint()
    print('end of instance printout          -----------------------------------------------------------------\n')
    return mod

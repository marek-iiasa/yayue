# return the model instance (currently the params are in *.dat, i.e., AMPL-like format

import pyomo.environ as pe       # more robust than using import *


def instance(m):
    # data = DataPortal()  # the default arg: (model=model) !
    # data.load(filename='data0.yaml')  # works with DataPortal() and DataPortal(model=m)
    # data.load(filename='data0.json')  # works with DataPortal() and DataPortal(model=m)
    data = pe.DataPortal(model=m)  # parameter (model=m) needed for loading *.dat
    # dat-format requires DataPortal(model=m)
    data.load(filename='Data/dat3.dat')  # dat3 prepared by JZ, Oct 21, 2023
    inst = m.create_instance(data)

    # # add here other precomputed parameters, if they will be introduced
    # for p in inst.P:   # define discount rates for each period
    #     inst.dis[p] = (1. - inst.discr) ** p
    #     print(f'p = {p}, {inst.discr.value = }, dis = {inst.dis[p].value}')

    # print('\n instance.pprint() follows      -----------------------------------------------------------------')
    # inst.pprint()
    # print('end of instance printout          -----------------------------------------------------------------\n')
    return inst

# return the model instance (currently the params are in *.dat, i.e., AMPL-like format

import pyomo.environ as pe       # more robust than using import *


def instance(m):
    # data = DataPortal()  # the default arg: (model=model) !
    # data.load(filename='data0.yaml')  # works with DataPortal() and DataPortal(model=m)
    # data.load(filename='data0.json')  # works with DataPortal() and DataPortal(model=m)
    data = pe.DataPortal(model=m)  # parameter (model=m) needed for loading *.dat
    # dat-format requires DataPortal(model=m)
    data.load(filename='Data/dat2.dat')
    inst = m.create_instance(data)
    # todo: check and activate computation of dis[p]
    # todo: check eiyh cost specs (eq 13), if dis[p] is needed

    # from pyomo.environ import *     # used in pyomo book and many tutotial
    # for p in m.P:   # define discount rates for each period
    #     inst.dis[p] = inst.discr ** p
    #   print(f'p = {p}, dis = {value(inst.dis[p])}')

    # print('\n instance.pprint() follows      -----------------------------------------------------------------')
    # inst.pprint()
    # print('end of instance printout          -----------------------------------------------------------------\n')
    return inst

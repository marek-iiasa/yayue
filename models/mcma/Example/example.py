# Generate simple example model

import sys		# needed for stdout and sys.exit()
import os
from os import R_OK, access
from os.path import isfile
import dill
import pyomo.environ as pe
from pyomo.opt import SolverStatus
from pyomo.opt import TerminationCondition


# --------------------------------------------
# Symbolic model specification
def mk_sms():
    m = pe.AbstractModel(name='example 1.0')
    # Parameters
    m.s_w = pe.Param()
    m.s_l = pe.Param()
    m.hour = pe.Param()
    m.work = pe.Param()
    m.leisure = pe.Param()
    m.h_income = pe.Param()
    # Variables
    m.w = pe.Var(domain = pe.NonNegativeReals)
    m.l = pe.Var(domain = pe.NonNegativeReals)
    m.obj1 = pe.Var(domain = pe.Reals)
    m.obj2 = pe.Var(domain = pe.Reals)
    # Objective
    m.obj = pe.Objective(expr=m.s_w * m.w+m.s_l*m.l,sense=pe.maximize)
    # Constraints
    m.con1 = pe.Constraint(expr=m.w + m.l <= m.hour)
    m.con2 = pe.Constraint(expr=m.w  >= m.work)
    m.con3 = pe.Constraint(expr=m.l <= m.leisure)
    m.con4 = pe.Constraint(expr=m.s_w * m.w + m.s_l * m.l == m.obj1)
    m.con5 = pe.Constraint(expr=m.h_income * m.w == m.obj2)
    return m
# --------------------------------------------
# return the model instance (currently the params are in *.dat, i.e., AMPL-like format

def inst(m, f_data):    # m: abstract/symbolic model, f_data: parameters in AMPL-like format
    # data = DataPortal()  # the default arg: (model=model) !
    # data.load(filename='data0.yaml')  # works with DataPortal() and DataPortal(model=m)
    # data.load(filename='data0.json')  # works with DataPortal() and DataPortal(model=m)
    data = pe.DataPortal(model=m)  # parameter (model=m) needed for loading *.dat
    # dat-format requires DataPortal(model=m)
    data.load(filename=f_data)  # dat3 prepared by JZ, Oct 21, 2023
    mod = m.create_instance(data)

    print('\n instance.pprint() follows      -----------------------------------------------------------------')
    mod.pprint()
    print('end of instance printout          -----------------------------------------------------------------\n')
    return mod


def chk_sol(res):  # check status of the solution
    print(f'solver status: {res.solver.status}, termination condition: {res.solver.termination_condition}.')
    if ((res.solver.status != SolverStatus.ok) or
            (res.solver.termination_condition != TerminationCondition.optimal)):
        print(f'{res.solver.termination_condition = }')
        sys.stdout.flush()  # desired for assuring printing exception at the output end
        if res.solver.termination_condition == TerminationCondition.infeasible:
            raise Exception('Optimization problem is infeasible.')
        elif res.solver.termination_condition == TerminationCondition.unbounded:
            raise Exception('Optimization problem is unbounded.')
        else:
            raise Exception('Optimization failed.')


# noinspection SpellCheckingInspection
if __name__ == '__main__':
    path = '.'
    data_dir = f'{path}/'
    mod_dir = f'{path}/'
    out_dir = f'{path}/'
    os.chdir(path)
    m_name = 'Example'     # model name (used for the dll-format file-name
    # files
    f_data = f'{data_dir}example.dat'    # data for defining the model instance
    f_mod = f'{mod_dir}{m_name}.dll'     # concrete model in dill format
    f_out = f'{out_dir}stdout.txt'       # optionally redirected stdout
    assert isfile(f_data) and access(f_data, R_OK), f'Data file {f_data} not readable.'

    default_stdout = sys.stdout

    # noinspection SpellCheckingInspection
    abst = mk_sms()         # generate abstract model (SMS)
    model = inst(abst, f_data)  # generate model instance

    # ad-hoc dll atore
    with open(f_mod, 'wb') as f:  # Serialize and save the Pyomo model
        dill.dump(model, f)
    print(f'Model "{m_name}" generated and dill-dumpped to: {f_mod}')

    opt = pe.SolverFactory('glpk')
    print(f'\nSolving the optimization problem.   ------------')
    results = opt.solve(model, tee=False)
    chk_sol(results)  # check the status of the solution

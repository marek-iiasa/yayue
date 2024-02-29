# Simple Pyomo model to demonstrate export of concrete model in the dill-format

import sys		# needed for stdout and sys.exit()
from os import R_OK, access
from os.path import isfile
import dill
import pyomo.environ as pe
from pyomo.opt import SolverStatus
from pyomo.opt import TerminationCondition


# Symbolic model specification
def mk_sms():
    m = pe.AbstractModel(name='example 1.0')
    # Parameters
    m.s_w = pe.Param()
    m.s_l = pe.Param()
    m.perhour = pe.Param()
    m.work = pe.Param()
    m.leisure = pe.Param()
    m.h_income = pe.Param()
    # Variables
    m.nwork = pe.Var(domain=pe.NonNegativeReals)    # number of work hours
    m.nleisure = pe.Var(domain=pe.NonNegativeReals)    # number of leasure hours
    m.satisf = pe.Var(domain=pe.Reals)
    m.income = pe.Var(domain=pe.Reals)

    # Objective
    @m.Objective(sense=pe.maximize)
    def goalmax(mx):
        return mx.s_w * mx.nwork + mx.s_l * mx.nleisure
    # Constraints

    @m.Constraint()
    def con1(mx):
        return mx.nwork + mx.nleisure <= mx.perhour

    @m.Constraint()
    def con2(mx):
        return mx.nwork >= mx.work

    @m.Constraint()
    def con3(mx):
        return mx.nleisure <= mx.leisure

    @m.Constraint()
    def con4(mx):
        return mx.s_w * mx.nwork + mx.s_l * mx.nleisure == mx.satisf

    @m.Constraint()
    def con5(mx):
        return mx.h_income * mx.nwork == mx.income

    return m    # return concrete model


# return the model instance
def inst(m, f_dat):    # m: abstract/symbolic model, f_data: parameters in AMPL-like format
    data = pe.DataPortal(model=m)  # parameter (model=m) needed for loading *.dat
    data.load(filename=f_dat)  # dat3 prepared by JZ, Oct 21, 2023
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
    m_name = 'example'     # model name (used for the dll-format file-name)
    # files
    f_data = 'example.dat'    # data for defining the model instance
    f_mod = f'{m_name}.dll'     # concrete model in dill format
    assert isfile(f_data) and access(f_data, R_OK), f'Data file {f_data} not readable.'
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

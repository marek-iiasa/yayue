# Simple Pyomo model to demonstrate export of concrete model in the dill-format

import sys		# needed for stdout and sys.exit()
from os import R_OK, access
from os.path import isfile
import dill
import pyomo.environ as pe
from pyomo.opt import SolverStatus
from pyomo.opt import TerminationCondition
import sms_benson
# from sms_LP import mk_sms
from inst_LP import inst      # return model instance

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
    m_name = 'benson'     # model name (used for the dll-format file-name)
    # files
    f_data = 'dat_benson.dat'    # data for defining the model instance
    f_mod = f'{m_name}.dll'     # concrete model in dill format
    assert isfile(f_data) and access(f_data, R_OK), f'Data file {f_data} not readable.'
    # noinspection SpellCheckingInspection
    abst = sms_benson.mk_sms()         # generate abstract model (SMS)
    model = inst(abst, f_data)  # generate model instance

    # ad-hoc dll atore
    with open(f_mod, 'wb') as f:  # Serialize and save the Pyomo model
        dill.dump(model, f, byref=False, recurse=True)
    print(f'Model "{m_name}" generated and dill-dumpped to: {f_mod}')

    opt = pe.SolverFactory('glpk')
    print(f'\nSolving the optimization problem.   ------------')
    results = opt.solve(model, tee=False)
    chk_sol(results)  # check the status of the solution
    model.display()
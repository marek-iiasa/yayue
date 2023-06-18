# See PyCharm help at https://www.jetbrains.com/help/pycharm/
# PyCharm > select "File" menu > select "Invalidate Caches / Restart" menu option
#   noinspection PyUnresolvedReferences
#   infty = float('inf')

"""
Prototype of the MCMA
"""
# import sys		# needed for sys.exit()
import os
# import pandas as pd
from datetime import datetime as dt
# from datetime import timedelta as td

from mca import *  # MCMA class handling MCMA structure and data
from mc_part import *  # returns MC_model instance
from pyomo.opt import SolverStatus
from pyomo.opt import TerminationCondition

# from t3sms import mk_sms as sms3  # tiny, testing model
# from t3inst import mk_inst as ins3  # ditto
from t4conc import mk_conc as conc4  # tiny testing model, developed as concrete (without abstract)


def mk_mod1():  # generate the core model
    # abst = sms3()  # abstract model (SMS)
    # mod1 = ins3(abst)  # model instance
    mod1 = conc4()  # model instance (without the abstract model)
    return mod1


def chk_sol(res):  # check status of the solution
    print(f'\nSolver status: {res.solver.status}, termination condition: {res.solver.termination_condition}.')
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
    tstart = dt.now()
    # print('Started at:', str(tstart))
    path = '/Users/marek/Documents/GitHub/pymmWrk/mcma'
    print(path)
    os.chdir(path)
    out_dir = './Out_dir/'

    redir_stdo = False  # optoional redirection of stdout to out_dir/stdout.txt
    default_stdout = sys.stdout
    if redir_stdo:
        if not os.path.exists(out_dir):
            os.makedirs(out_dir, mode=0o755)
        fn_out = out_dir + 'stdout.txt'  # file for redirected stdout
        print(f'Stdout redirected to: {fn_out}')
        f_out = open(fn_out, 'w')
        sys.stdout = f_out
    else:
        fn_out = None
        f_out = None

    # select solver
    opt = pe.SolverFactory('glpk')
    # opt = pe.SolverFactory('ipopt') # solves both LP and NLP

    print(f'\nGenerating instance of the core model.')
    m1 = mk_mod1()  # generate core model: first an abstract model and then the corresponding concerete model
    # print('\ncore model display: -----------------------------------------------------------------------------')
    # m1.pprint()
    # print('end of model display: ------------------------------------------------------------------------\n')
    # print('solving core model')
    # m1_obj = m1.component_map(ctype=pe.Objective)  # all objectives of the m1 (core model)
    # print(f'{m1_obj=}')
    # print(f'm1_obj = {m1_obj}')
    # print(f'{type(m1_obj)=}')
    # m1_obj.display()
    # m1_obj.pprint()
    # m1_obj.print()
    # print(f'{m1_obj.name=}, {m1_obj=}')
    # results = opt.solve(m1, tee=True)
    # chk_sol(results)    # check the status of the solution
    # todo: clarify exception while loading the results
    # m1.load(results)  # Loading solution into results object
    # print('end of core model solving: ------------------------------------------------------------------------\n')

    # todo: find name/object of the objective
    m1.goal.deactivate()
    print(f'core model objective (named: goal) deactivated.')

    print(f'\nInitializing criteria:')
    mc = Mcma()
    mc.addCrit('income', 'inc', 'max')
    mc.addCrit('emission', 'emi', 'min')
    # print(f'Criteria:\n{mc.cr}')  # prints only the object id
    mc.payOff('income', None, None)
    mc.payOff('emission', None, None)
    i_stage = mc.chk_stage()    # analysis stage
    n_iter = 0
    while i_stage < 6:   # MCA iterations
        print(f'\nStart iteration {n_iter}  -----------------------------------------------------------------------')
        print(f'Analysis stage: {i_stage}.')
        m = pe.ConcreteModel()
        # m1.goal.deactivate()
        # m.m1 = m1   # replaced by add_component()  (works but gives warning)
        m.add_component('core_model', m1)
        # m.m1.goal.deactivate()    not needed, deactivated above
        # model instance of the MC-part
        print(f'\nGenerating instance of the MC-part model (representing the MCMA Achievement Function).')
        mc_gen = McMod(mc, m1)
        mc_part = mc_gen.mc_itr()        # model of the MC-part
        # m.mc_part = mc_part   # replaced by add_component()  (works but gives warning)
        m.add_component('mc_part', mc_part)
        # m.pprint()
        results = opt.solve(m, tee=True)
        chk_sol(results)  # check the status of the solution
        # todo: clarify exception (uncomment next line) while loading the results
        # m1.load(results)  # Loading solution into results object

        # get crit. values, store them via calling mc.store_sol(), return values of rep_vars
        rep_vars = ['x', 'y', 'z']  # list of variables, values of which shall be returned
        val_vars = mc_gen.mc_sol(rep_vars)
        print(f'Values of the selected variables:\n{val_vars}.')
        m.del_component(m.core_model)   # must be deleted (otherwise would have to be generated every iteration
        print(f'\nFinished itr {n_iter}, updating the analysis stage.')
        i_stage = mc.chk_stage()    # check analysis stage
        n_iter += 1
        if n_iter > 2:
            print('\nMax iters reached; breaking the iteration loop.')
            break

    # noinspection SpellCheckingInspection
    # model = mc_mod(abst)  # model instanceo

    # model.write('test.lp')
    # model.write('test.mps')
    # model.write('test.gms')
    # model.write('test2.lp', symbolic_solver_labels=True)  # illegal param: symbolic...

    # print('\nmodel display: -----------------------------------------------------------------------------')
    # model.display()     # displays only instance (not abstract model)
    # print('end of model display: ------------------------------------------------------------------------\n')

    # opt = SolverFactory('gams')  # gams can be used as a solver

    tend = dt.now()
    print('\nStarted at: ', str(tstart))
    print('Finished at:', str(tend))
    time_diff = tend - tstart
    print(f'Wall-clock execution time: {time_diff.seconds} sec.')

    if redir_stdo:  # close the redirected output
        f_out.close()
        sys.stdout = default_stdout
        print(f'\nRedirected stdout stored in {fn_out}. Now writing to the console.')
        print('\nStarted at: ', str(tstart))
        print('Finished at:', str(tend))
        print(f'Wall-clock execution time: {time_diff.seconds} sec.')

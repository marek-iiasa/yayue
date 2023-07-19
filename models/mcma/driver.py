"""
Prototype of the MCMA driver
"""
# import os.path

import sys		# needed for sys.exit()
# import os
# import pandas as pd
import pyomo.environ as pe
from ctr_mca import CtrMca  # handling MCMA structure and data, uses Crit class
from mc_block import McMod  # handles submodel/block of AF and links to the core/substantive model
from pyomo.opt import SolverStatus
from pyomo.opt import TerminationCondition


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


def driver(m1, ana_dir):
    print(f'\nAnalysing instance of model {m1.name}.')

    # todo: define mc.verb level and gradually implementing controlling printouts according to mc.verb
    #   (instead of currenly used statement commonting/uncommenting)
    mc = CtrMca(ana_dir)    # CtrMca ctor
    mc.rdCritSpc()      # read criteria definition from the corresponding file

    # Load payOff table if previously stored (initialized to undefined by Crit ctor)
    # mc.rd_payoff()    # supressed for testing
    # todo: modify prn_payoff() to store in the file only if changed (modify prn_payoff)
    # mc.prn_payoff()   # no need to store the table just read

    # todo: open .../log.txt either for 'w' or 'a'
    # todo: get itr-id from length of log.txt

    # select solver
    opt = pe.SolverFactory('glpk')
    # opt = pe.SolverFactory('ipopt') # solves both LP and NLP
    # opt = SolverFactory('gams')  # gams can be used as a solver

    i_stage = 0
    n_iter = 1
    while i_stage < 6:   # MCA iterations (common loop for all analysis stages)
        print(f'\nStart iteration {n_iter}  -----------------------------------------------------------------------')
        i_stage = mc.set_stage()  # define/check current analysis stage
        # print(f'Analysis stage: {i_stage}.')

        m = pe.ConcreteModel()  # model instance to be composed of two blocks: (1) core model and (2) mc_part
        m.add_component('core_model', m1)  # m.m1 = m1  assign works but (due to warning) replaced by add_component()

        mc.set_pref()   # set preferences (crit activity, optionally A/R values)
        if mc.cur_stage == 6:
            print(f'\nFinished the analysis for all specified preferences.')
            break
        # model instance of the MC-part
        # print(f'\nGenerating instance of the MC-part model (representing the MCMA Achievement Function).')
        mc_gen = McMod(mc, m1)
        mc_part = mc_gen.mc_itr()        # model of the MC-part
        # print('mc-part generated.\n')
        # mc_part.pprint()
        m.add_component('mc_part', mc_part)  # add_component() used instead of simple assignment
        if mc.verb > 2:
            print('core-model and mc-part blocks added to the model instance; ready for optimization.')
            m.pprint()

        # solve the model instance composed of two blocks
        print('\nsolving --------------------------------')
        # results = opt.solve(m, tee=True)
        results = opt.solve(m, tee=False)
        chk_sol(results)  # check the status of the solution
        # todo: clarify exception (uncomment next line) while loading the results
        # m1.load(results)  # Loading solution into results object

        print('\nprocessing solution --------------------------------')
        # get crit. values, store them via calling mc.store_sol(), return values of rep_vars
        rep_vars = []  # list of variables, values of which shall be returned
        # rep_vars = ['x', 'y', 'z']  # list of variables, values of which shall be returned
        val_vars = mc_gen.mc_sol(rep_vars)  # process solution
        if len(rep_vars):
            print(f'Values of the selected variables:\n{val_vars}.')
        m.del_component(m.core_model)   # must be deleted (otherwise would have to be generated every iteration)
        # m.del_component(m.mc_part)   # must be deleted (otherwise would have to be generated every iteration)
        mc.prn_payoff()     # store current criteria values in the file
        # todo: add print to a log

        print(f'\nFinished itr {n_iter}.')
        n_iter += 1
        max_itr = 20
        if n_iter > max_itr:
            print(f'\nMax iters {max_itr} reached; breaking the iteration loop.')
            break
    # iterations end here
    # todo: clearing-house (logs, report, etc) waits for implementation
    raise Exception(f'driver(): clearing-house not yet implemented.')

# below are diverse, potentially useful, notes
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

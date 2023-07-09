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

    mc = CtrMca(ana_dir)
    fname = ana_dir + '/config.txt'     # criteria definition file
    print(f"\nInitializing criteria defined in file '{fname}':")
    n_cr_def = 0
    with open(fname) as reader:
        for n_line, line in enumerate(reader):
            line = line.rstrip("\n")
            # print(f'line {line}')
            if line[0] == "*" or len(line) == 0:  # skip commented and empty lines
                continue
            words = line.split()
            n_words = len(words)
            assert(n_words == 3), f'line {line} has {n_words} instead of the required three.'
            mc.addCrit(words[0], words[1], words[2])
            n_cr_def += 1

    assert (n_cr_def > 1), f'at least two criteria need to be defined, only {n_cr_def} was defined.'

    # Load payOff table if previously stored (initialized to undefined by Crit ctor)
    # mc.rd_payoff()    # supressed for testing
    mc.prn_payoff()

    # todo: open .../log.txt either for 'w' or 'a'
    # todo: get itr-id from length of log.txt

    # select solver
    opt = pe.SolverFactory('glpk')
    # opt = pe.SolverFactory('ipopt') # solves both LP and NLP
    # opt = SolverFactory('gams')  # gams can be used as a solver

    i_stage = mc.chk_stage()    # define/check current analysis stage
    n_iter = 1
    while i_stage < 6:   # MCA iterations (common loop for all analysis stages)
        print(f'\nStart iteration {n_iter}  -----------------------------------------------------------------------')
        print(f'Analysis stage: {i_stage}.')

        m = pe.ConcreteModel()  # model instance to be composed of two blocks: (1) core model and (2) mc_part
        m.add_component('core_model', m1)  # m.m1 = m1  assign works but (due to warning) replaced by add_component()

        mc.set_pref()   # set preferences (crit activity, optionally A/R values)
        # model instance of the MC-part
        # print(f'\nGenerating instance of the MC-part model (representing the MCMA Achievement Function).')
        mc_gen = McMod(mc, m1)
        mc_part = mc_gen.mc_itr()        # model of the MC-part
        # print('mc-part generated.\n')
        # mc_part.pprint()
        m.add_component('mc_part', mc_part)  # add_component() used instead of simple assignment
        print('core-model and mc-part blocks added to the model instance; ready for optimization.')
        # m.pprint()

        # solve the model instance composed of two blocks
        print('\nsolving --------------------------------')
        # results = opt.solve(m, tee=True)
        results = opt.solve(m, tee=False)
        chk_sol(results)  # check the status of the solution
        # todo: clarify exception (uncomment next line) while loading the results
        # m1.load(results)  # Loading solution into results object

        print('\nprocessing solution --------------------------------')
        # get crit. values, store them via calling mc.store_sol(), return values of rep_vars
        rep_vars = ['x', 'y', 'z']  # list of variables, values of which shall be returned
        val_vars = mc_gen.mc_sol(rep_vars)
        print(f'Values of the selected variables:\n{val_vars}.')
        m.del_component(m.core_model)   # must be deleted (otherwise would have to be generated every iteration)
        # m.del_component(m.mc_part)   # must be deleted (otherwise would have to be generated every iteration)
        print(f'\nFinished itr {n_iter}, updating the analysis stage.')
        i_stage = mc.chk_stage()    # check analysis stage
        mc.prn_payoff()

        n_iter += 1
        max_itr = 3
        if n_iter > max_itr:
            print(f'\nMax iters {max_itr} reached; breaking the iteration loop.')
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

"""
Prototype of the MCMA driver
"""
# import os.path

import sys		# needed for sys.exit()
# import os
# import pandas as pd
import pyomo.environ as pe
from pyomo.opt import SolverStatus
from pyomo.opt import TerminationCondition
from ctr_mca import CtrMca  # handling MCMA structure and data, uses Crit class
from mc_block import McMod  # handles submodel/block of AF and links to the core/substantive model
from report import Report  # handles submodel/block of AF and links to the core/substantive model


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


def driver(m1, ana_dir):    # m1 (core model) defined in main (mcma.py)
    print(f'\nAnalysing instance of model {m1.name}.')

    is_par_rep = True   # switch to Pareto-representation mode (comment this line for standard MCMA use)
    # is_par_rep = False   # uncomment for standard MCMA use
    mc = CtrMca(ana_dir, is_par_rep)    # CtrMca ctor
    # todo: improve handling og verbosity levels
    mc.verb = 1    # verbosity (affecting mainly message-printouts) level

    rep_vars = ['prod', 'emi', 'act']  # list of variables, values of which shall be included in the report
    # rep_vars = ['act']  # list of variables, values of which shall be returned
    rep = Report(mc, m1, rep_vars)    # Report ctor
    # rep_vars = []  # list of variables, values of which shall be returned
    # todo: current version the report works only for indexded vars

    # select solver
    opt = pe.SolverFactory('glpk')
    # opt = pe.SolverFactory('ipopt') # solves both LP and NLP
    # opt = SolverFactory('gams')  # gams can be used as a solver

    # todo: implement scaling of vars defining criteria.
    # todo: consider log (complementary to *csv); open .../log.txt either for 'w' or 'a'
    # todo: implement rounding of floats (in printouts only or of all/most computed values?)
    n_iter = 1
    # max_itr = 16
    max_itr = 7
    while n_iter <= max_itr:   # just for safety; should not be needed now
        i_stage = mc.set_stage()  # define/check current analysis stage
        print(f'\nAnalysis stage: {i_stage}, start iteration {n_iter}  -----------------------------------------------')

        m = pe.ConcreteModel()  # model instance to be composed of two blocks: (1) core model and (2) mc_part
        m.add_component('core_model', m1)  # m.m1 = m1  assign works but (due to warning) replaced by add_component()

        if mc.is_par_rep:
            print('Generate preferences for further exploration of Pareto set representation.')
            mc.par_pref()   # set preferences in Pareto reprentation mode
        else:
            print('Continue to get and handle user preferences.')
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
        rep.itr(mc_part)    # update crit. attr. {nadir, utopia, payOff}, handle storing itr-info
        # get crit. values, store them via calling mc.store_sol(), return values of rep_vars
        # val_vars = mc_gen.mc_sol(rep_vars)  # extracting values of vars to be reported moved rep.itr()
        # if len(rep_vars):
        #     print(f'Values of the selected variables:\n{val_vars}.')
        m.del_component(m.core_model)   # must be deleted (otherwise would have to be generated every iteration)
        # m.del_component(m.mc_part)   # need not be deleted

        print(f'Finished current itr, count: {n_iter}.')
        n_iter += 1
        if n_iter > max_itr:
            print(f'\nMax iters {max_itr} reached; breaking the iteration loop.\n')
            break
    # iterations end here
    # todo: clearing-house (logs, report, etc) waits for implementation
    rep.summary()
    if mc.par_rep:
        mc.par_rep.summary()
    # raise Exception(f'driver(): clearing-house not yet implemented.')

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

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
from mk_inst import mk_inst  # model instance provider
from mc_block import McMod  # handles submodel/block of AF and links to the core/substantive model
from report import Report  # handles submodel/block of AF and links to the core/substantive model


def chk_sol(res):  # check status of the solution
    # print(f'solver status: {res.solver.status}, termination condition: {res.solver.termination_condition}.')
    if ((res.solver.status != SolverStatus.ok) or
            (res.solver.termination_condition != TerminationCondition.optimal)):
        print(f'optimization failed; termination condition: {res.solver.termination_condition}')
        sys.stdout.flush()  # desired for assuring printing exception at the output end
        '''
        if res.solver.termination_condition == TerminationCondition.infeasible:
            raise Exception('Optimization problem is infeasible.')
        elif res.solver.termination_condition == TerminationCondition.unbounded:
            raise Exception('Optimization problem is unbounded.')
        else:
            raise Exception('Optimization failed.')
        '''
        return False     # optimization failed
    else:
        return True     # optimization OK


def driver(cfg):
    m1 = mk_inst(cfg)    # upload or generate m1 (core model)
    print(f'MCMA of the core-model instance: {m1.name}.')

    # is_par_rep = True   # switch to Pareto-representation mode (set to False for providing preferences in a file)
    # is_par_rep = False   # uncomment for providing user-preferences in a file
    mc = CtrMca(cfg)    # CtrMca ctor
    # todo: improve handling og verbosity levels

    # list of variables, values of which shall be included in the report
    # rep_vars = ['cost', 'carb', 'co2C', 'oilImp']
    # rep_vars = ['x1', 'x2', 'x3']
    # rep_vars = ['prod', 'emi', 'exp', 'act']
    # rep_vars = ['act']
    # rep_vars = ['x']
    # rep_vars = []
    rep = Report(cfg, mc, m1)    # Report ctor

    # select solver
    opt = pe.SolverFactory('glpk')
    # opt = pe.SolverFactory('ipopt') # solves both LP and NLP

    # todo: implement scaling of vars defining criteria.
    # todo: consider log (complementary to *csv); open .../log.txt either for 'w' or 'a'
    # todo: implement rounding of floats (in printouts only or of all/most computed values?)
    n_iter = 0
    max_itr = cfg.get('mxIter')
    # max_itr = 4
    # max_itr = 9
    # max_itr = 16
    # max_itr = 100
    # max_itr = 35020
    # todo: payoff table not stored!
    while n_iter < max_itr:   # just for safety; should not be needed for a proper stop criterion
        i_stage = mc.set_stage()  # define/check current analysis stage
        print(f'\nStart iteration {n_iter}, analysis stage {i_stage} -----------------------------------------------')

        m = pe.ConcreteModel()  # model instance to be composed of two blocks: (1) core model and (2) mc_part
        m.add_component('core_model', m1)  # m.m1 = m1  assign works but (due to warning) replaced by add_component()

        # the MC-part model-block (based on preferences: either generated by the MCMA or uploaded)
        if mc.is_par_rep and mc.hotStart:
            print('Generate preferences for exploration of the Pareto set representation.')
            mc.par_pref()   # set preferences in Pareto reprentation mode
        else:
            if i_stage < 4:
                print('Setting preferences for next step in Payoff table computations.')
            elif i_stage == 4:
                # todo: move/remove solutions (mostly dominated!) from payoff computation.
                #   currently these solutions are used for generating cubes!
                print('Setting preferences for computing neutral solution.')
            else:
                print('Get user preferences provided in a file.')
            mc.set_pref()   # set preferences (crit activity, optionally A/R values)
        if mc.cur_stage == 6:   # cur_stage is set to 6 (by par_pref() or set_pref()), if all preferences are processed
            print(f'\nFinished the analysis for all specified preferences.')
            break       # exit the iteration loop
        # print(f'\nGenerating instance of the MC-part model (representing the MCMA Achievement Function).')
        mc_gen = McMod(mc, m1)      # McMod ctor (model representing the MC-part, i.e. the Achievement Function of MCMA)
        mc_part = mc_gen.mc_itr()   # concrete model of the MC-part (based on the current preferences)
        # print('mc-part generated.\n')
        # mc_part.pprint()
        m.add_component('mc_part', mc_part)  # add_component() used instead of simple assignment
        if mc.verb > 2:
            print('core-model and mc-part blocks added to the model instance; ready for optimization.')
            m.pprint()

        # solve the model instance composed of two blocks: (1) core model m1, (2) MC-part (Achievement Function)
        # print('\nsolving --------------------------------')
        # results = opt.solve(m, tee=True)
        results = opt.solve(m, tee=False)
        # todo: clarify exception (uncomment next line) while loading the results
        # m1.load(results)  # Loading solution into results object
        mc.is_opt = chk_sol(results)  # solution status: True, if optimal, False otherwise
        if mc.is_opt:  # optimal solution found
            # print(f'\nOptimal solution found.')
            pass
        else:   # optimization failed
            # todo: process correctly iterations with failed optimization
            #   done but check/tests still needed
            print(f'\nOptimization failed, solution disregarded.         --------------------------------------------')
        # print('processing solution ----')
        rep.itr(mc_part)  # update crit. attr. {N, U, payOff}, reporting; checks domination & close solutions
        m.del_component(m.core_model)  # must be deleted (otherwise m1 would have to be generated at every iteration)
        # m.del_component(m.mc_part)   # need not be deleted (a new mc_part needs to be generated for new preferences)

        # print(f'Finished current itr, count: {n_iter}.')
        n_iter += 1
        if n_iter > max_itr:
            print(f'\nMax iters {max_itr} reached; breaking the iteration loop.\n')
            break
    # the iteration loop ends here

    print(f'\nFinished {n_iter} analysis iterations. Summary report follows.')

    # reports,
    rep.summary()
    if mc.par_rep:
        # todo: consider to integrate the below into rep.summary()
        mc.par_rep.summary()    # plots of Pareto-set representation

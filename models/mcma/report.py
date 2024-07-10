"""
Reporting results of the MCMA iterations. Handling core-model is generic, i.e., any variable can be selected for report.
"""

import warnings
import pandas as pd
import pyomo.environ as pe  # more robust than using import *
from .plots import Plots
from .cluster import Cluster  # cluster object


# noinspection SpellCheckingInspection
class Report:
    def __init__(self, wflow, m1):
        self.wflow = wflow    # WorkFlow
        self.m1 = m1    # core-model (used only for extracting solutions in stage one
        self.cfg = wflow.mc.cfg
        self.mc = wflow.mc    # CtrMca
        self.rep_dir = self.cfg.get('resDir')  # repository of MCMA analysis instance configuration and results
        self.cr_names = []   # names of all criteria
        self.var_names = []  # names of mc_block variables defining criteria
        # crit-attributes: v: value, Y: y/n is_active marker, M: 1/-1 (max/min mult.)
        self.id_attr = ['_U', '_A', '_v', '_R', '_N', '_M', '_Y']
        self.cols = ['itr_id', 'af', 'cafMin', 'cafReg']
        for crit in self.mc.cr:
            self.cr_names.append(crit.name)
            self.var_names.append(crit.var_name)
            for idx in self.id_attr:
                self.cols.append(crit.name + idx)
        self.itr_df = pd.DataFrame(columns=self.cols)   # df containing crit.-attributes values for each iteration.
        self.rep_vars = self.mc.opt('rep_vars', [])    # names of the core-model variables to be included in the report
        self.sol_vars = []  # rows with values of vars in self.sol_vars, each row for one solution/iteration
        self.df_vars = None     # df with values (for each iter) of the vars defined in self.sol_vars
        self.f_iters = f'{self.rep_dir}iters.csv'  # info on iterations
        self.f_vars = f'{self.rep_dir}modelVars.csv'  # values of requested variables
        self.f_pareto = f'{self.rep_dir}parFront.csv'  # values of requested variables
        #
        self.itr_id = -1
        self.prev_itr = 0   # number of previously made iters
        self.cur_itr = 0   # number of currently made iters
        self.plots = None

        print(f'\nReport ctor; results/plots dir: "{self.rep_dir}".     -------------')
        print(f'Core-model variables to be reported: {self.rep_vars}')

    # driver of processing of each solution
    def itr(self, m):   # m: current mc_block (invariant core-model linked in the ctor)
        """Process values of criteria and other vars in the current solution."""
        # formatting doc: https://docs.python.org/3/library/string.html#formatstrings

        self.itr_id += 1    # itr_id inilialized at -1
        self.mc.cur_itr_id = self.itr_id
        # print(f'Extracting current solution values from model {m.name}, iter_id {self.itr_id}.')

        if not self.mc.is_opt:
            return  # refrain from handling/storing non-optimal solutions

        cri_val = {}    # all criteria values in current solution
        # cri_ach = {}    # achievemtns cannot be defined before checking, if the solution is in the U/N range
        m_vars = self.m1.component_map(ctype=pe.Var)  # only core model uses var-names associated with criteria
        for (i, var_name) in enumerate(self.var_names):  # extract m.vars defining criteria
            m_var = m_vars[var_name]
            val = m_var.value
            cr = self.mc.cr[i]
            cr.val = val        # has to be stored here because it is needed in in_range()
            cri_val.update({cr.name: val})  # add to the dict of crit. values of the current solution
            if self.mc.verb > 2:
                print(f'Value of variable "{var_name}" defining criterion "{cr.name}" = {val:.2e}')
        if self.mc.verb > 2:
            print(f'Values of criteria {cri_val}')

        in_range = True
        if self.wflow.cur_stage > 1:   # check, if crit-vals are within U/N range (only after the PayOff tab is avail.)
            in_range = self.wflow.in_range()
            if not in_range:
                return in_range

        # store crit values, also CAF for wflow.cur_stage > 1 (except of PayOff comp.)
        self.mc.critVal(cri_val)
        self.itr_inf(m)     # store one-line info on each iteration

        if self.wflow.cur_stage < 2:   # don't store solutions during payOff table computations
            return in_range

        if len(self.rep_vars):
            self.req_vals()     # extract and store values of the core-model variables requested to be reported

        return in_range

    def itr_inf(self, m):    # add to self.itr_df one row with values of all attributes for each criterion
        af = pe.value(m.af)
        af = round(af, 1)
        if self.wflow.payoff.cur_stage > 1:     # after utopia computed
            cafMin = pe.value(m.cafMin)
            cafReg = pe.value(m.cafReg)
            if self.mc.verb > 2:
                print(f'af = {af:.3e}, cafMin = {cafMin:3e}, cafReg = {cafReg:3e}')
            cafMin = round(cafMin, 1)
            cafReg = round(cafReg, 1)
            new_row = {'itr_id': self.itr_id, 'af': af, 'cafMin': cafMin, 'cafReg': cafReg}
        else:   # cafMin, cafReg not defined while computing utopia
            new_row = {'itr_id': self.itr_id, 'af': af}
        cur_col = 4
        for crit in self.mc.cr:
            new_row.update({self.cols[cur_col]: crit.utopia})
            cur_col += 1
            asp = crit.asp
            if asp is not None:
                asp = round(asp, 1)
            if self.wflow.cur_stage < 2:  # cannot calculate achievements before PayOff is completed
                new_row.update({self.cols[cur_col]: asp})
            else:
                new_row.update({self.cols[cur_col]: crit.val2ach(asp)})
            cur_col += 1
            if self.wflow.cur_stage < 2:  # cannot calculate achievements before PayOff is completed
                new_row.update({self.cols[cur_col]: round(crit.val, 1)})
            else:
                new_row.update({self.cols[cur_col]: crit.a_val})
            cur_col += 1
            res = crit.res
            if res is not None:
                if self.wflow.cur_stage < 2:  # cannot calculate achievements before PayOff is completed
                    res = round(res, 1)
                else:
                    res = round(crit.val2ach(res), 1)
            new_row.update({self.cols[cur_col]: res})
            cur_col += 1
            new_row.update({self.cols[cur_col]: crit.nadir})
            cur_col += 1
            new_row.update({self.cols[cur_col]: crit.mult})
            cur_col += 1
            marker = 'y'
            if not crit.is_active:
                marker = 'n'
            new_row.update({self.cols[cur_col]: marker})
            cur_col += 1
        df2 = pd.DataFrame(new_row, index=list(range(1)))
        with warnings.catch_warnings():  # suppress the pd.concat() warning
            warnings.filterwarnings("ignore", category=FutureWarning)
            self.itr_df = pd.concat([self.itr_df, df2], axis=0, ignore_index=True)

    # extract and store values of the variables to be included in the report
    def req_vals(self):
        vals = []   # tmp list of lists, each for one var: [var_name, is_indexed, val(s)]
        m1_vars = self.m1.component_map(ctype=pe.Var)  # all variables of the m1 (core model)
        for var_name in self.rep_vars:     # loop over m1.vars of all requested var-names
            m1_var = m1_vars[var_name]
            if m1_var is None:
                raise Exception(f'Variable {var_name} is not defined in the core model.')
            if m1_var.is_indexed():
                val_dict = m1_var.extract_values()  # values returned in dict (indexes as keys)
                vals.append([var_name, True, val_dict])
                # print(f'Values of indexed variable {var_name} = {val_dict}')
            else:
                val = m1_var.value
                vals.append([var_name, False, val])
                # print(f'Value of the report variable {var_name} = {val}')

        # parse the extracted values into entries of a row to be included by the self.summary() in the df_vars
        new_row = {'itr': self.itr_id}
        for item in vals:
            if item[1] is False:    # simple (not indexed) var
                new_row.update({item[0]: f'{item[2]:.2e}'})
            else:       # indexed var
                d_item = item[2]    # dict with values of indexed var
                for (ind, val) in d_item.items():
                    idx = f'{item[0]}_{ind}'
                    new_row.update({idx: f'{val:.2e}'})
        self.sol_vars.append(new_row)   # append to the list of rows

    # generate and store dfs with info on criteria and the variables requested for report/plots
    def summary(self):
        if self.wflow.par_rep is None:  # Pareto-front summary
            print('No report information collected.')
            return

        self.wflow.par_rep.summary()    # prepare df_sol (solutions: itr, crit_val, cafs, info)
        # print(f'\nResults of {self.cur_itr} iters added to results of {self.prev_itr} previously made.')
        self.itr_df.to_csv(self.f_iters, index=True)
        print(f'\nCriteria attributes at each iteration are stored in the DataFrame "{self.f_iters}" file.')
        self.df_vars = pd.DataFrame(self.sol_vars)
        self.df_vars.to_csv(self.f_vars, index=True)
        print(f'Values of core-model variables requested to be reported are stored in the DataFrame '
              f'"{self.f_vars}" file.')

        if self.wflow.par_rep is None:  # return if Pareto-front is not computed
            return

        df = self.wflow.par_rep.df_sol
        for cr in self.wflow.mc.cr:   # format criteria values
            df[cr.name] = df[cr.name].apply(lambda x: f'{x:.4e}')   # apply() returns series (a column)
        f_name = self.f_pareto
        df.to_csv(f_name, index=True)
        print(f'{len(df)} unique solutions stored in {f_name}. '
              f'{len(self.wflow.par_rep.clSols)} duplicated solutions skipped.')

        # clustering solutions
        n_clust = self.wflow.mc.opt('nClust', 0)
        if n_clust > 0:
            self.wflow.cluster = Cluster(self.wflow.rep)
            self.wflow.cluster.mk_clust(n_clust)
        elif n_clust < 0:
            raise Exception(f'negative ({n_clust}) number of clusters not allowed.')

        # plot solutions
        self.plots = Plots(self.wflow, self.df_vars)    # plots
        self.plots.plot3D()    # 3D plot
        self.plots.plot2D()    # 2D plots
        self.plots.parallel()  # Parallel coordinates plot
        # plots.sol_stages()  # solutions & itr vs stage, cube-sizes vs stages
        # plots.kde_stages()  # KDE + histograms vs stages
        # plots.vars('actS')    # plot the requested model variables
        # plots.vars_alternative()

        # plot clusters
        if self.wflow.cluster is not None:
            self.wflow.cluster.plots()

        # todo: AS: add saving the (optionally generated) plots of clusters
        self.plots.save_figures()
        # todo: AS: verify/fix showing plots after the cluster-plots were added
        if self.plots.show_plot:
            self.plots.show_figures()

        # todo: 3D plots need reconfiguration: either the change the pyCharm default browser to chrome or modify the
        #  Safari version to either Safari beta or to Safari technology preview (see the Notes)
        #  generation of 3D plots is suppressed until this problem will be solved.
        # self.plot3()
        # self.plot3a()
        # raise Exception(f'ParRep::summary() not finished yet.')

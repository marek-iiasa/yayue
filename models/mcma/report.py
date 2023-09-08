"""
Reporting results of iterations of the regret function applied to the China liquid fuel production model.
"""

import warnings
import pandas as pd
import pyomo.environ as pe       # more robust than using import *
# from ctr_mca import CtrMca
# from crit import Crit

'''
import os
import numpy as np
# from sklearn.cluster import KMeans
# import collections   # for Counter()
import matplotlib.pyplot as plt
# from mpl_toolkits import mplot3d
# from mpl_toolkits.mplot3d import Axes3D     # needed by Axes3D()
from matplotlib import cm
from matplotlib import colors
# from matplotlib.ticker import LinearLocator    # needed for ax.set_major_locator
import seaborn as sns
sns.set()   # settings for seaborn plotting style
'''


class Report:
    # cf regret::report() for extensive processing
    def __init__(self, mc, m1, rep_vars):
        self.mc = mc    # CtrMca
        self.m1 = m1    # core-model (used only for extracting solutions in stage one
        self.rep_dir = mc.ana_dir  # repository of MCMA analysis instance configuration and results
        self.cr_names = []   # names of all criteria
        self.var_names = []  # names of mc_block variables defining criteria
        # crit-attributes: v: value, Y: y/n is_active marker, M: 1/-1 (max/min mult.)
        self.id_attr = ['_U', '_A', '_v', '_R', '_N', '_M', '_Y']
        self.cols = ['itr_id', 'af', 'cafMin', 'cafReg']
        for crit in mc.cr:
            self.cr_names.append(crit.name)
            self.var_names.append(crit.var_name)
            for idx in self.id_attr:
                self.cols.append(crit.name + idx)
        self.itr_df = pd.DataFrame(columns=self.cols)   # df containing crit.-attributes values for each iteration.
        self.f_itr_df = mc.ana_dir + '/df_itr.csv'  # file name of the stored df
        self.rep_vars = rep_vars    # names of the core-model variables to be included in the report
        self.sol_vars = []  # rows with values of vars in self.sol_vars, each row for one solution/iteration
        self.df_vars = None     # df with values (for each iter) of the vars defined in self.sol_vars
        self.f_df_vars = mc.ana_dir + '/df_vars.csv'  # file name of the stored df

        #
        self.itr_id = -1
        self.prev_itr = 0   # number of previosly made iters
        self.cur_itr = 0   # number of currently made iters

        # todo: implement hot start
        # todo: get itr-id from length of log.txt

        # todo: initialize self.itr_df with previously stored df, if exists
        #   modify self.itr_id to a subsequent number

        print(f'\nReport ctor: handling results MCMA iters.     -------------')

        '''
        # data space for the summary df with values of each iteration (to be used in the summary report)
        cols = ['itr_id'] + self.par_id + ['cost', 'CO2', 'oilImp']     # 'slope', 'marker'
        self.sum_df = pd.DataFrame(columns=cols)

        # container of lists, each list a space for values of each requested variable
        # sol_cont: list of lists, list each for values of one variable (for all params values)
        self.sol_cont = []   # container of df's, each to hold extracted values of a variable for all params
        model_vars = m.component_map(ctype=pe.Var)
        # check, if each req_var is defined, make space for values
        tmp_lst = var_lst.copy()    # must use copy(), assignement is a reference
        for req_var in tmp_lst:     # use var_lst here would corrupt the loop, if the list element is removed
            if req_var in model_vars:
                # append empty list to mk_space in the container for df's with values of the req_var;
                # each df appended in add_itr() for the corresponding iter defined by value(s) of one or more params
                self.sol_cont.append([])
                # print(f'space allocated for pd.df with values of the requested var {req_var}.')
            else:   # the requested var is not defined in the SMS; remove it from the reported-vars list
                self.var_lst.remove(req_var)
                print(f'requested var {req_var} not defined in the model: its values will not be reported.')
                print(f'modified list of the vars to be reported: {self.var_lst}.')

        # declarations of data shared by functions of the summary report
        self.costs = self.sum_df['cost']    # assignments here are to empty df, must be reassigned in summary(self)
        self.prices = self.sum_df[self.par_id]

        print('\nReport ctor finished.                                           --------------------------------')
        '''

    def itr(self, m):   # m: current mc_block (invariant core-model linked in the ctor)
        """Process values of criteria and other vars in the current solution."""
        # formatting doc: https://docs.python.org/3/library/string.html#formatstrings

        self.itr_id += 1
        self.mc.cur_itr_id = self.itr_id
        print(f'Extracting current solution values from model {m.name}, iter_id {self.itr_id}.')

        cri_val = {}    # all criteria values in current solution
        '''
        if self.mc.cur_stage > 1:
            mx = m  # use the current mc_core model for accesing solution
            m_vars = m.component_map(ctype=pe.Var)  # all variables of the mc_block
        else:
            mx = self.m1  # use the core-model for accesing solution
        '''
        m_vars = self.m1.component_map(ctype=pe.Var)  # only core model uses var-names associated with criteria
        for (i, var_name) in enumerate(self.var_names):  # extract m.vars defining criteria
            m_var = m_vars[var_name]
            val = m_var.value
            cr_name = self.cr_names[i]
            cri_val.update({cr_name: val})  # add to the dict of crit. values of the current solution
            if self.mc.verb > 2:
                print(f'Value of variable "{var_name}" defining criterion "{cr_name}" = {val:.2e}')
        if self.mc.verb > 1:
            print(f'Values of criteria {cri_val}')

        self.mc.updCrit(cri_val)    # update crit attributes (value, optionally: nadir, utopia)
        self.mc.prnPayOff()     # print, and optionally store payOff table

        # add to self.itr_df one row with values of all attributes for each criterion
        af = pe.value(m.af)
        af = round(af, 1)
        if self.mc.cur_stage > 1:
            cafMin = pe.value(m.cafMin)
            cafReg = pe.value(m.cafReg)
            print(f'af = {af:.3e}, cafMin = {cafMin:3e}, cafReg = {cafReg:3e}')
            cafMin = round(cafMin, 1)
            cafReg = round(cafReg, 1)
            new_row = {'itr_id': self.itr_id, 'af': af, 'cafMin': cafMin, 'cafReg': cafReg}
        else:   # cafMin, cafReg not defined in stage 1
            print(f'af = {af:.3e}')
            new_row = {'itr_id': self.itr_id, 'af': af}
        cur_col = 4
        for crit in self.mc.cr:
            new_row.update({self.cols[cur_col]: crit.utopia})
            cur_col += 1
            asp = crit.asp
            if asp is not None:
                asp = round(asp, 1)
            new_row.update({self.cols[cur_col]: asp})
            cur_col += 1
            new_row.update({self.cols[cur_col]: round(crit.val, 1)})
            cur_col += 1
            res = crit.res
            if res is not None:
                res = round(res, 1)
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
        # print(f'current itr_df in report():\n{self.itr_df}')

        if len(self.rep_vars):
            self.req_vals()     # extract and store values of the core-model variables requested to be reported

    # exctract and store values of the variables to be included in the report
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
        print(f'Values of (the to be reported) core-model variables for the current iter:\n{new_row}.')

        # sign-off
        print(f'Report::itr_id({self.itr_id}) finished.')

    # generate and store df's with info on criteria and the variables requested for report/plots
    def summary(self):
        # todo: correct info on current and previous iterations
        # print(f'\nResults of {self.cur_itr} iters added to results of {self.prev_itr} previously made.')
        self.itr_df.to_csv(self.f_itr_df, index=True)
        print(f'Criteria attributes at each iteration are stored in the DataFrane "{self.f_itr_df}" file.')
        self.df_vars = pd.DataFrame(self.sol_vars)
        self.df_vars.to_csv(self.f_df_vars, index=True)
        print(f'Values of core-model variables requested to be reported are stored in the DataFrane '
              f'"{self.f_df_vars}" file.')
        # raise Exception(f'Report::summary() not implemented yet.')

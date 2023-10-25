"""
Reporting results of iterations of the regret function applied to the China liquid fuel production model.
"""

# import warnings
import os
import pandas as pd
import pyomo.environ as pe       # more robust than using import *

'''
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
    def __init__(self, m1, rep_dir, rep_vars):
        self.m1 = m1    # core-model (used for extracting from solutions values of variables)
        self.rep_dir = rep_dir  # repository for storing results
        self.rep_vars = rep_vars    # names of the core-model variables to be included in the report
        self.sol_vars = []  # rows with values of vars in self.sol_vars, each row for one solution/iteration
        self.df_vars = None     # df with values (for each iter) of the vars defined in self.sol_vars
        self.f_df_vars = f'{rep_dir}/df_vars.csv'  # file name of the stored df

        # todo: create, if needed, rep_dir
        if not os.path.exists(self.rep_dir):
            os.makedirs(self.rep_dir, mode=0o755)

        print(f'\nReport ctor: handling results of the Pipa model.     -------------')

    # extract and store values of the variables to be included in the report
    def var_vals(self):
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
        new_row = {}
        for item in vals:
            if item[1] is False:    # simple (not indexed) var
                new_row.update({item[0]: f'{item[2]:.2e}'})
            else:       # indexed var
                d_item = item[2]    # dict with values of indexed var
                for (ind, val) in d_item.items():
                    idx = f'{item[0]}_{ind}'
                    new_row.update({idx: f'{val:.2e}'})
        self.sol_vars.append(new_row)   # append to the list of rows
        # print(f'Values of (the to be reported) core-model variables for the current iter:\n{new_row}.')

        # sign-off
        # print(f'Report::itr_id({self.itr_id}) finished.')

    # generate and store df's with info on criteria and the variables requested for report/plots
    def summary(self):
        self.df_vars = pd.DataFrame(self.sol_vars)
        self.df_vars.to_csv(self.f_df_vars, index=True)
        print(f'\nValues of core-model variables requested to be reported are stored in the DataFrane '
              f'"{self.f_df_vars}" file.')

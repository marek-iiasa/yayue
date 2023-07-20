"""
Reporting results of iterations of the regret function applied to the China liquid fuel production model.
"""

import pyomo.environ as pe       # more robust than using import *
'''
import os
import numpy as np
import pandas as pd
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


# from ctr_mca import CtrMca
# from crit import Crit

class Report:
    def __init__(self, mc):
        self.mc = mc    # CtrMca
        self.rep_dir = mc.ana_dir  # repository of MCMA analysis instance configuration and results

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

    def add_itr(self, m, itr):   # extract and store values of requested vars for the current itr
        # formatting doc: https://docs.python.org/3/library/string.html#formatstrings
        print(f'Extracting solution values of iter. {itr} from model {m.name}.')
        af = f'{pe.value(m.af):.3e}'
        print(f'AF  = {af}')

        '''
        # add to the summary df: oil price and the total cost
        # cost = round(pe.value(m.cost), 0)
        # new_row = {'itr_id': self.itr_id, 'co_price': op, 'cost': cost, 'CO2': co2, 'oilImp': oil_imp}
        new_row = {'itr_id': self.itr_id, 'cost': cost, 'CO2': co2, 'oilImp': oil_imp}
        for indx, idx in enumerate(self.par_id):
            new_row.update({idx: val[indx]})
        df2 = pd.DataFrame(new_row, index=list(range(1)))
        # print(f'df2 in report():\n{df2}')
        self.sum_df = pd.concat([self.sum_df, df2], axis=0, ignore_index=True)
        # print(f'current sum_df in report():\n{self.sum_df}')

        # extract values of the requested variables and store them in the corresponding lists of sequences
        model_vars = m.component_map(ctype=pe.Var)
        for seq_req, req_var in enumerate(self.var_lst):  # loop over the list of the variables to be processed
            print(f'\nProcessing values of variable: {req_var}')
            try:
                assert(req_var in model_vars)
            except AssertionError:
                print(f'The requested var {req_var} undefined in the model (it should have been removed by the ctor).')
                raise

            # get the model variable with the req_var name
            # for k in model_vars.keys():  # this is a map of {name:pyo.Var}
            #     print(f'checking model var: {k}')
            #     if k == req_var:
            #         m_var = model_vars[k]
            #         break
            m_var = model_vars[req_var]     # instead of the above loop
            # make a pd.Series of the variable's values (with the corresponding indices)
            s = pd.Series(m_var.extract_values(), index=m_var.extract_values().keys())
            # s = s.round(5)  # replace small numbers by zeros

            # if the series is multi-indexed we need to unstack it...
            if type(s.index[0]) == tuple:  # the series is multi-indexed
                print(f'multi-indexed series s[{req_var}] before unstack:\n{s}')
                s = s.unstack(level=0)  # df-cols defined by technologies
                # multi-index the columns (hierarchical column indexing, no longer used)
                # s.columns = pd.MultiIndex.from_tuples([(pr_id, t) for t in s.columns])
                # print(f'df[{req_var}] after series-index unstack and conversion of series to df:\n{s}')
            else:   # the series indexed by technologies only
                # print(f'var: {m_var} has one index, the series not unstacked (but converted to df):\n{s}')
                d1 = s.to_frame()
                s = d1.transpose()  # convert tech-indices into columns (the df has one row only)

            eps = 0.000001
            # s[(-eps < s and s < eps)] = 0    # replace small numbers by zeros
            # s[s.all(-eps < s < eps)] = 0    # replace small numbers by zeros
            # s.bool(-eps < s < eps) = 0    # replace small numbers by zeros
            # all of the above result in error
            # s.where(-eps < s < eps, 0.)
            # s.where(-eps < s < eps) =  0.
            # TODO: test the below
            # TODO: fix the below to handle also s < -eps
            s[s < eps] = 0    # replace small numbers by zeros
            s.insert(0, 'itr_id', self.itr_id)  # add itr_id col to uniformly index both one and two param's value(s)
            # print(f'\nMultiIndex of the df with values of {req_var} and of param {pr_id}:\n{s.columns}')

            # print(f'\nsol_cont before appending var({req_var}, seq {seq_req}):\n{self.sol_cont[seq_req]}')
            self.sol_cont[seq_req].append(s)
            # print(f'\nsol_cont after append var: {req_var} (seq in sol_cont: {seq_req}):\n{self.sol_cont[seq_req]}\n')

        print('--------------------------------------------------------------------------------')
        # end of add_itr()
        '''
"""
Reporting results
"""
# import os.path

# import sys		# needed for sys.exit()
# import os
import pandas as pd
import pyomo.environ as pe  # needed for extracting elements of the solution


class Report:
    # cf regret::report() for extensive processing
    def __init__(self, m1, rep_dir, rep_vars):
        self.m1 = m1    # core-model (used for extracting from solutions values of variables)
        self.rep_dir = rep_dir  # repository for storing results
        self.rep_vars = rep_vars    # names of the core-model variables to be included in the report
        self.sol_vars = []  # rows with values of vars in self.sol_vars, each row for one solution/iteration
        self.df_vars = None     # df with values (for each iter) of the vars defined in self.sol_vars
        self.f_df_vars = f'{rep_dir}/df_vars.csv'  # file name of the stored df

        print(f'\nReport ctor: handling results of the Matouqin model.     -------------')

        # set default datastructures
        self.supply_df = pd.DataFrame()
        self.finance_df = pd.DataFrame()
        self.cap_df = pd.DataFrame(index=self.m1.S)
        self.flow_df = pd.DataFrame(index=self.m1.T)
        self.dvflow_df = pd.DataFrame(index=self.m1.T)

    # extract and store values of the variables to be included in the report
    # parse indexed and un-indexed variable, rewrite the values
    def var_vals(self):
        vals = []   # tmp list of lists, each for one var: [var_name, is_indexed, val(s)]
        m1_vars = self.m1.component_map(ctype=pe.Var)  # all variables of the m1 (core model)
        for var_name in self.rep_vars:     # loop over m1.vars of all requested var-names
            m1_var = m1_vars[var_name]
            if m1_var is None:
                raise Exception(f'Variable {var_name} is not defined in the core model.')
            if m1_var.is_indexed():
                val_dict = m1_var.extract_values()  # values returned in dict (indexes as keys)
                vals.append([var_name, True, val_dict])     # True: if m1_var is indexed
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
                for (ind, val) in d_item.items():       # for example: sCap_cell1 : 50
                    idx = f'{item[0]}_{ind}'
                    new_row.update({idx: f'{val:.2e}'})
        self.sol_vars.append(new_row)   # append to the list of rows

    # generate and store df's with info on criteria and the variables requested for report/plots
    def summary(self):
        self.df_vars = pd.DataFrame(self.sol_vars)
        self.df_vars.to_csv(self.f_df_vars, index=True)
        print(f'\nValues of core-model variables requested to be reported are stored in the DataFrane '
              f'"{self.f_df_vars}" file.')

    # generate and store needed results in df's in excel file for plotting
    def toExcel(self):
        print('Get results')

        # finance related results
        self.finance_df.loc[0, 'Revenue'] = pe.value(self.m1.revenue)
        self.finance_df.loc[0, 'Income'] = pe.value(self.m1.income)
        self.finance_df.loc[0, 'InvCost'] = pe.value(self.m1.invCost)
        self.finance_df.loc[0, 'OMC'] = pe.value(self.m1.OMC)
        self.finance_df.loc[0, 'OverCost'] = pe.value(self.m1.overCost)
        self.finance_df.loc[0, 'BuyCost'] = pe.value(self.m1.buyCost)
        self.finance_df.loc[0, 'BuyCost'] = pe.value(self.m1.balCost)

        # capacity related results
        for s in self.m1.sNum:
            self.cap_df.loc[s, 'sNum'] = round(pe.value(self.m1.sNum[s]), 0)
        for s in self.m1.sCap:
            self.cap_df.loc[s, 'sCap'] = round(pe.value(self.m1.sCap[s]), 0)

        # supply and average inflows
        supply = pe.value(self.m1.supply)
        avg_inflow = sum(self.m1.inflow[t] for t in self.m1.T) / self.m1.nHrs

        self.supply_df['supply'] = [supply]
        self.supply_df['avg_inflow'] = [avg_inflow]

        # flows results
        for t in self.m1.T:
            self.flow_df.loc[t, 'inflow'] = round(pe.value(self.m1.inflow[t]), 2)
            self.flow_df.loc[t, 'dOut'] = round(pe.value(self.m1.dOut[t]), 2)
            self.flow_df.loc[t, 'sIn'] = -round(pe.value(self.m1.sIn[t]), 2)
            self.flow_df.loc[t, 'sOut'] = round(pe.value(self.m1.sOut[t]), 2)
            self.flow_df.loc[t, 'ePrs'] = -round(pe.value(self.m1.ePrs[t]), 2)
            self.flow_df.loc[t, 'eSurplus'] = -round(pe.value(self.m1.eSurplus[t]), 2)
            self.flow_df.loc[t, 'eBought'] = round(pe.value(self.m1.eBought[t]), 2)

        for t in self.m1.T:
            for dv in self.m1.Se:
                self.dvflow_df.loc[t, f'eIn_{dv}'] = round(pe.value(self.m1.eIn[dv, t]), 2)
            for dv in self.m1.Sh:
                self.dvflow_df.loc[t, f'hIn_{dv}'] = round(pe.value(self.m1.hIn[dv, t]), 2)
                self.dvflow_df.loc[t, f'hOut_{dv}'] = round(pe.value(self.m1.hOut[dv, t]), 2)
                self.dvflow_df.loc[t, f'hVol_{dv}'] = round(pe.value(self.m1.hVol[dv, t]), 2)
            for dv in self.m1.Sc:
                self.dvflow_df.loc[t, f'hInc_{dv}'] = round(pe.value(self.m1.hInc[dv, t]), 2)
                self.dvflow_df.loc[t, f'cOut_{dv}'] = round(pe.value(self.m1.cOut[dv, t]), 2)

        # print(f'Finance results:\n {self.finance_df} \n')
        # print(f'Capacity results:\n {self.cap_df} \n')
        # print(f'Flow results:\n {self.flow_df} \n')
        # print(f'Dv_flow results:\n {self.dvflow_df} \n')

        with pd.ExcelWriter(f'{self.rep_dir}plot_vars.xlsx', engine='openpyxl') as writer:
            self.finance_df.to_excel(writer, sheet_name='finance')
            self.cap_df.to_excel(writer, sheet_name='capacity', index=True)
            self.supply_df.to_excel(writer, sheet_name='supply', index=True)
            self.flow_df.to_excel(writer, sheet_name='flow', index=True)
            self.dvflow_df.to_excel(writer, sheet_name='dvflow', index=True)

        print(f'Variables for plotting are saved to: {self.rep_dir}plot_vars.xlsx')

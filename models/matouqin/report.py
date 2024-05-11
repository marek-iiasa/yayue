"""
Reporting results
"""
# import os.path

# import sys		# needed for sys.exit()
# import os
import pandas as pd
import pyomo.environ as pe  # needed for extracting elements of the solution
import logging


class Report:
    # cf regret::report() for extensive processing
    def __init__(self, m1, rep_dir, rep_vars):
        self.m1 = m1    # core-model (used for extracting from solutions values of variables)
        self.rep_dir = rep_dir  # repository for storing results
        self.rep_vars = rep_vars    # names of the core-model variables to be included in the report
        self.sol_vars = []  # rows with values of vars in self.sol_vars, each row for one solution/iteration
        self.df_vars = None     # df with values (for each iter) of the vars defined in self.sol_vars
        self.f_df_vars = f'{rep_dir}/df_vars.csv'  # file name of the stored df
        self.check_df_vars = f'{rep_dir}/check_vars.csv'    # file name of abnormal value
        self.check_df_hy = f'{rep_dir}/check_hy.csv'  # file name of abnormal value of hydrogen tank

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
        print(f'\nValues of core-model variables requested to be reported are stored in the DataFrame '
              f'"{self.f_df_vars}" file.')

    # generate and store needed results in df's in Excel file for plotting
    def toExcel(self):
        print(f'\nGet results')

        # finance related results
        self.finance_df.loc[0, 'Revenue'] = pe.value(self.m1.revenue)
        self.finance_df.loc[0, 'Income'] = pe.value(self.m1.income)
        self.finance_df.loc[0, 'InvCost'] = pe.value(self.m1.invCost)
        # self.finance_df.loc[0, 'VarCost'] = pe.value(self.m1.varCost)
        self.finance_df.loc[0, 'OMC'] = pe.value(self.m1.OMC)
        self.finance_df.loc[0, 'OverCost'] = pe.value(self.m1.overCost)
        self.finance_df.loc[0, 'BuyCost'] = pe.value(self.m1.buyCost)
        self.finance_df.loc[0, 'BuyCost'] = pe.value(self.m1.balCost)

        # capacity related results
        for s in self.m1.sNum:
            self.cap_df.loc[s, 'sNum'] = round(pe.value(self.m1.sNum[s]), 0)
        for s in self.m1.sCap:
            self.cap_df.loc[s, 'sCap'] = round(pe.value(self.m1.sCap[s]), 1)

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
                self.dvflow_df.loc[t, f'hOut_{dv}'] = -round(pe.value(self.m1.hOut[dv, t]), 2)
                self.dvflow_df.loc[t, f'hVol_{dv}'] = round(pe.value(self.m1.hVol[dv, t]), 2)
            for dv in self.m1.Sc:
                self.dvflow_df.loc[t, f'hInc_{dv}'] = round(pe.value(self.m1.hInc[dv, t]), 2)
                self.dvflow_df.loc[t, f'cOut_{dv}'] = -round(pe.value(self.m1.cOut[dv, t]), 2)

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

    def check(self):
        print(f'\nResults check')

        # Check inflow and outflow from storage system
        check = []
        for t in self.m1.T:
            sin = round(pe.value(self.m1.sIn[t]), 2)
            sout = round(pe.value(self.m1.sOut[t]), 2)
            value = sin * sout

            if value != 0:
                check.append({'T': t, 'sIn': sin, 'sOut': sout, 'value': value})

        if check:
            check_df = pd.DataFrame(check)
            check_df.to_csv(self.check_df_vars, index=False)
            print(f'Store and release at the same time, please check csv file: {self.check_df_vars}')

            # Check inflow and outflow of hydrogen tanks
            check_hy = []
            for s in self.m1.Sh:
                for t in self.m1.T:
                    hin = round(pe.value(self.m1.hIn[s, t]), 2)
                    hout = round(pe.value(self.m1.hOut[s, t]), 2)
                    hvol = round(pe.value(self.m1.hVol[s, t]), 2)
                    value = hin * hout

                    if value != 0:
                        check_hy.append({'S': s, 'T': t, 'hIn': hin, 'hOut': hout, 'hVol': hvol, 'value': value})

            if check_hy:
                check_hy = pd.DataFrame(check)
                check_hy.to_csv(self.check_df_hy, index=False)
                print(f'Store and release hydrogen at the same time, please check csv file: {self.check_df_hy}')
            else:
                print(f'Hydrogen tank flows correct')

        else:
            print(f'Storage correct')

    def analyze(self):
        # logging.basicConfig(level=logging.INFO,
        #                     # format='%(asctime)s - %(levelname)s - %(message)s',
        #                     handlers=[
        #                         logging.FileHandler(f'{self.rep_dir}output.log'),
        #                         logging.StreamHandler()
        #                     ])
        #
        # logging.info(f'\nResults analysis')

        print('1) Values of inflow -----------------------------------------------------------------------')
        ave_inflow = round((sum(self.m1.inflow[t] for t in self.m1.T) / self.m1.nHrs), 2)
        print(f'Average inflow = {ave_inflow} MW per hour')

        print('\n2) Values of decision variables ------------------------------------------------')
        print('2.1 Supply ------------------------------------------------------------------------')
        supply = round(pe.value(self.m1.supply), 2)
        r_sa = round((supply / ave_inflow), 2)
        print(f'Supply = {supply} MW per hour, {r_sa} times of average inflow')

        print('\n2.2 Storage investment ---------------------------------------------')
        for s in self.m1.S:
            num = pe.value(self.m1.sNum[s])
            if num == 0:
                continue
            else:
                mxcap = self.m1.mxCap[s]
                sinv = self.m1.sInv[s]
                snum = pe.value(self.m1.sNum[s])
                scap = round(pe.value(self.m1.sCap[s]), 2)
                inv = round((sinv * num), 2)     # yearly investment of storage devices

            print(f'\nInvestment of {s}:')
            print(f'Unit capacity of {s} is {mxcap} MW')
            print(f'Investment for one {s} is {sinv} million RMB')
            print(f'Numbers of {s} = {snum}')
            print(f'Total capacity = {scap} MW')
            print(f'Total investment cost of {s} = {inv} million RMB')

        print('\n3) Overview of outcome variables -------------------------------------------------------------------')
        revenue = round(pe.value(self.m1.revenue), 4)
        income = round(pe.value(self.m1.income), 2)
        invcost = round(pe.value(self.m1.invCost), 2)
        omc = round(pe.value(self.m1.OMC), 2)
        overcost = round(pe.value(self.m1.overCost), 2)
        buycost = round(pe.value(self.m1.buyCost), 2)
        balcost = round(pe.value(self.m1.balCost), 2)

        print(f'Total revenue  = {revenue} million RMB')
        print(f'Income  = {income} million RMB')
        print(f'Balance cost  = {balcost} million RMB')
        print(f'Investment cost  = {invcost} million RMB')
        print(f'Operation and maintenance cost  = {omc} million RMB')
        print(f'Surplus cost  = {overcost} million RMB')
        print(f'Shortage cost  = {buycost} million RMB')

        cost = invcost + omc + balcost
        storcost = invcost + omc

        if income != 0:
            r_ci = round((cost / income * 100), 2)
        else:
            r_ci = 0

        print(f'\nRevenue and cost analysis:')
        if revenue > 0:
            r_ir = round((income / revenue), 2)
            print(f'Income is {r_ir} times of revenue')
            print(f'Total cost is {cost} million RMB, the cost-income ratio is {r_ci}%')
        else:
            r_ic = round((income / cost), 2)
            r_cr = round((cost / revenue), 2)
            print(f'\nIncome is {r_ic} times of revenue')
            print(f'\nTotal cost is {cost} million RMB, the cost-revenue ratio is {r_cr}%')

        print(f'\nCost structure:')
        if cost != 0:
            r_sc = round((storcost / cost * 100), 2)
            r_invc = round((invcost / cost * 100), 2)
            r_oc = round((omc / cost * 100), 2)
            r_bc = round((balcost / cost * 100), 2)

            print(f'Investment cost accounts for {r_invc}% of total cost')
            print(f'Operation and Maintenance cost accounts for {r_oc}% of total cost')
            print(f'Total storage cost is {r_sc} of total cost, and balance cost accounts for {r_bc}% of total cost')

            r_overc = round((overcost / cost * 100), 2)
            r_buyc = round((buycost / cost * 100), 2)

            if balcost != 0:
                r_ob = round((overcost / balcost * 100), 2)
                r_bb = round((buycost / balcost * 100), 2)
                print(f'Electricity loss accounts for {r_overc}% of total cost, and {r_ob}% of balance cost')
                print(f'Electricity purchase accounts for {r_buyc}% of total cost, and {r_bb}% of balance cost')
            else:
                print(f'Electricity loss accounts for {r_overc}% of total cost.')
                print(f'Electricity purchase accounts for {r_buyc}% of total cost.')

        print(f'\n4) Overview of energy flows ----------------------------------------------------------------')
        inflow_total = round((sum(self.m1.inflow[t] for t in self.m1.T)), 2)
        supply_total = round((pe.value(self.m1.supply) * self.m1.nHrs), 2)
        dout_total = round((sum(pe.value(self.m1.dOut[t]) for t in self.m1.T)), 2)
        sin_total = round((sum(pe.value(self.m1.sIn[t]) for t in self.m1.T)), 2)
        sout_total = round((sum(pe.value(self.m1.sOut[t]) for t in self.m1.T)), 2)
        # eprs_total = round((sum(pe.value(self.m1.ePrs[t]) for t in self.m1.T)), 2)
        esurplus_total = round((sum(pe.value(self.m1.eSurplus[t]) for t in self.m1.T)), 2)
        ebought_total = round((sum(pe.value(self.m1.eBought[t]) for t in self.m1.T)), 2)

        er_si = round((sin_total / inflow_total * 100), 2)
        # ev4 = round((eprs_total / inflow_total * 100), 2)
        er_esi = round((esurplus_total / inflow_total * 100), 2)

        if supply_total != 0:
            er_ds = round((dout_total / supply_total * 100), 2)
            er_ss = round((sout_total / supply_total * 100), 2)
            er_ebs = round((ebought_total / supply_total * 100), 2)
        else:
            print(f'There is no supply.')
            er_ds = 0
            er_ss = 0
            er_ebs = 0

        print(f'Total electricity inflow is {inflow_total} MW')
        print(f'Total supply is {supply_total} MW')
        print(f'Total directly output is {dout_total} MW, {er_ds}% of the total supply.')
        print(f'Total electricity inflow to storage system is {sin_total} MW, '
              f'{er_si}% of the total inflow.')
        print(f'Total electricity outflow from storage system is {sout_total} MW, '
              f'{er_ss}% of the total supply.')
        print(f'Total surplus (loss) is {esurplus_total} MW, '
              f'{er_esi}% of the total inflow, '
              f'costs {overcost} million RMB.')
        print(f'Total electricity purchase is {ebought_total} MW, '
              f'{er_ebs}% of the total supply, '
              f'costs {buycost} million RMB.')

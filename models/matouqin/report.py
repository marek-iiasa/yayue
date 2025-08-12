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
        self.check_df_ec = f'{rep_dir}/check_ec.csv'  # file name of abnormal value of hydrogen tank

        print(f'\nReport ctor: handling results of the Matouqin model.     -------------')

        # set default datastructures
        self.fin_df = pd.DataFrame()
        self.stor_df = pd.DataFrame()
        self.bal_df = pd.DataFrame()
        self.cap_df = pd.DataFrame()
        self.sup_df = pd.DataFrame()
        self.flow_df = pd.DataFrame()
        self.flow_dev_df = pd.DataFrame()
        self.einr_df = pd.DataFrame()
        self.eoutr_df = pd.DataFrame()
        self.xins_df = pd.DataFrame()
        self.flow_s_df = pd.DataFrame()

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
                    if val is not None:
                        f_val = f'{val:.2e}'
                    else:
                        f_val = 'N/A'
                    idx = f'{item[0]}_{ind}'
                    new_row.update({idx: f'{f_val}'})
        self.sol_vars.append(new_row)   # append to the list of rows

    # generate and store df's with info on criteria and the variables requested for report/plots
    def summary(self):
        self.df_vars = pd.DataFrame(self.sol_vars)
        self.df_vars.to_csv(self.f_df_vars, index=True)
        print(f'\nValues of core-model variables requested to be reported are stored in the DataFrame '
              f'"{self.f_df_vars}" file.')

    # generate and store needed results in df's in Excel file for plotting
    def to_plt_df(self, plt_fin=None, plt_stor=None, plt_bal=None, plt_cap=None,
                  plt_sup=None, plt_flow=None, plt_flow_dev=None):
        print(f'\nGet results')

        fin = plt_fin if plt_fin is not None else []
        stor = plt_stor if plt_stor is not None else []
        bal = plt_bal if plt_bal is not None else []
        cap = plt_cap if plt_cap is not None else []
        sup = plt_sup if plt_sup is not None else []
        flow = plt_flow if plt_flow is not None else []
        flow_dev = plt_flow_dev if plt_flow_dev is not None else []

        # finance related results
        if fin:
            self.fin_df = pd.DataFrame(columns=fin)
            for var in fin:
                self.fin_df.loc[0, var] = pe.value(getattr(self.m1, var))

        if stor:
            self.stor_df = pd.DataFrame(
                {var: [pe.value(getattr(self.m1, var)[r]) for r in self.m1.R] for var in stor},
                index=list(self.m1.R)
            )

        if bal:
            self.bal_df = pd.DataFrame(index=self.m1.T)
            spls_val = [pe.value(self.m1.eS[t]) for t in self.m1.T]
            buy_val = [pe.value(self.m1.eB[t]) for t in self.m1.T]
            esprice = pe.value(self.m1.eSprice)
            ebprice = pe.value(self.m1.eBprice)

            self.bal_df['Spls'] = pd.Series(spls_val, index=self.m1.T) * esprice
            self.bal_df['Buy'] = pd.Series(buy_val, index=self.m1.T) * ebprice

        # capacity related results
        if cap:
            self.cap_df = pd.DataFrame(columns=cap)
            cap_res = []

            # report for sms3
            for r, e in self.m1.E_:
                row = {'ESS': r, 'Device': e}

                for var in cap[:2]:
                    val = pe.value(getattr(self.m1, var)[r, e])
                    row[var] = val

                cap_res.append(row)

            for r, s in self.m1.S_:
                row = {'ESS': r, 'Device': s}

                for var in cap[2:4]:
                    val = pe.value(getattr(self.m1, var)[r, s])
                    row[var] = val

                cap_res.append(row)

            for r, x in self.m1.X_:
                row = {'ESS': r, 'Device': x}

                for var in cap[4:]:
                    val = pe.value(getattr(self.m1, var)[r, x])
                    row[var] = val

                cap_res.append(row)

            self.cap_df = pd.DataFrame(cap_res)

        # supply and average inflows
        if sup:
            self.sup_df = pd.DataFrame(columns=sup)
            for var in sup:
                if var == 'avg_inf':
                    avg_inf = sum(self.m1.inflow[t] for t in self.m1.T) / self.m1.nHrs
                    self.sup_df.loc[0, var] = avg_inf
                elif var == 'tot_eOut' or var == 'tot_eInHess' or var == 'tot_eOutHess':
                    var_ = var.split('_', 1)[1]     # corresponding var in the model
                    vol = pe.value(sum(getattr(self.m1, var_)[t] for t in self.m1.T))
                    self.sup_df.loc[0, var] = vol
                else:
                    self.sup_df.loc[0, var] = pe.value(getattr(self.m1, var))

        if flow:
            for t in self.m1.T:
                for var in flow:
                    self.flow_df.loc[t, var] = pe.value(getattr(self.m1, var)[t])

        if flow_dev:
            flow_dev_res = {}
            time_idx = self.m1.T

            for var_name in flow_dev:
                # get the variable object
                var_obj = getattr(self.m1, var_name, None)

                if var_obj is None:
                    print(f'Warning: {var_name} does not exist in the model and was skipped.')
                    continue

                # check if indexed var
                if var_obj.is_indexed():
                    for idx in var_obj.keys():
                        # estimate time index, last
                        new_idx_val = idx[-1] if idx[-1] in time_idx else None
                        oth_idx = idx[:-1] if new_idx_val is not None else idx

                        if new_idx_val is None:
                            print(f'Error: No time index found for {idx}. Skipping this index.')
                            continue

                        # crete col name
                        col_name = f'{var_name}_' + '_'.join(oth_idx) if oth_idx else var_name

                        if new_idx_val not in flow_dev_res:
                            flow_dev_res[new_idx_val] = {}

                        flow_dev_res[new_idx_val][col_name] = pe.value(var_obj[idx])
                        # flow_dev_res.setdefault(new_idx_val, {})[col_name] = pe.value(var_obj[idx])
                else:
                    # store none indexed var val on time index
                    for t in time_idx:
                        flow_dev_res.setdefault(t, {})[var_name] = pe.value(var_obj)

                    # transform to df
                df = pd.DataFrame.from_dict(flow_dev_res, orient='index')
                # df = pd.DataFrame.from_dict(flow_dev_res, orient='index').fillna(0)    # set NAN to 0
                df.index.name = 'T'
                self.flow_dev_df = df

            # get eInr, eOutr, eIns, eOuts
            einr_df = self.flow_dev_df.filter(like='eInr', axis=1)
            eoutr_df = self.flow_dev_df.filter(like='eOutr', axis=1)
            xins_df = self.flow_dev_df.filter(like='xIns', axis=1)
            xouts_df = self.flow_dev_df.filter(like='xOuts', axis=1)
            xvol_df = self.flow_dev_df.filter(like='xVol', axis=1)

            if einr_df.shape[1] == 0:
                raise ValueError(f'There is no "eInr" in flow_dev_df.')
            if eoutr_df.shape[1] == 0:
                raise ValueError(f'There is no "eOutr" in flow_dev_df.')
            if xins_df.shape[1] == 0:
                raise ValueError(f'There is no "xIns" in flow_dev_df.')
            if xouts_df.shape[1] == 0:
                raise ValueError(f'There is no "xOuts" in flow_dev_df.')
            if xvol_df.shape[1] == 0:
                raise ValueError(f'There is no "xVol" in flow_dev_df.')

            col_name_einr = {c: c.split('_')[1] for c in einr_df.columns}
            col_name_eoutr = {c: c.split('_')[1] for c in eoutr_df.columns}

            # rename cols
            einr_df = einr_df.rename(columns=col_name_einr)
            eoutr_df = eoutr_df.rename(columns=col_name_eoutr)

            self.einr_df = einr_df
            self.eoutr_df = eoutr_df
            self.xins_df = xins_df

            # get storage flows
            flow_s = pd.concat([xvol_df, xins_df, xouts_df], axis=1)
            self.flow_s_df = flow_s

        # print(self.fin_df)
        # print(self.stor_df)
        # print(self.bal_df.head(5))
        # print(self.cap_df)
        # print(self.sup_df)
        # print(self.flow_df.head(5))
        # print(self.flow_dev_df.head(5))
        # print(f'eInr: {self.einr_df.head(5)}, eOutr: {self.eoutr_df.head(5)}')
        # print(f'xIns: {self.xins_df.head(5)}')
        # print(f'sFlows: {self.flow_s_df.head(5)}')

    def to_Excel(self):
        with pd.ExcelWriter(f'{self.rep_dir}plot_vars.xlsx', engine='openpyxl') as writer:
            self.fin_df.to_excel(writer, sheet_name='finance')
            self.stor_df.to_excel(writer, sheet_name='cost_Stor', index=True)
            self.bal_df.to_excel(writer, sheet_name='cost_Bal', index=True)
            self.cap_df.to_excel(writer, sheet_name='capacity', index=True)
            self.sup_df.to_excel(writer, sheet_name='supply', index=True)
            self.flow_df.to_excel(writer, sheet_name='flow', index=True)
            self.flow_dev_df.to_excel(writer, sheet_name='flow_dev', index=True)
            self.einr_df.to_excel(writer, sheet_name='eInr', index=True)
            self.eoutr_df.to_excel(writer, sheet_name='eOutr', index=True)
            self.xins_df.to_excel(writer, sheet_name='xIns', index=True)
            self.flow_s_df.to_excel(writer, sheet_name='flow_s', index=True)

        print(f'Variables for plotting are saved to: {self.rep_dir}plot_vars.xlsx')

    def toCsv(self):
        self.fin_df.to_csv(f'{self.rep_dir}finance.csv', index=True)
        self.stor_df.to_csv(f'{self.rep_dir}cost_Stor.csv', index=True)
        self.bal_df.to_csv(f'{self.rep_dir}cost_Bal.csv', index=True)
        self.cap_df.to_csv(f'{self.rep_dir}capacity.csv', index=True)
        self.sup_df.to_csv(f'{self.rep_dir}supply.csv', index=True)
        self.flow_df.to_csv(f'{self.rep_dir}flow.csv', index=True)
        self.flow_dev_df.to_csv(f'{self.rep_dir}flow_dev.csv', index=True)
        self.einr_df.to_csv(f'{self.rep_dir}eInr.csv', index=True)
        self.eoutr_df.to_csv(f'{self.rep_dir}eOutr.csv', index=True)
        self.xins_df.to_csv(f'{self.rep_dir}xIns.csv', index=True)
        self.flow_s_df.to_csv(f'{self.rep_dir}flow_s.csv', index=True)

        print(f'Variables for plotting are saved to csv files')

    def sflow_toCsv(self):
        self.flow_s_df.to_csv(f'{self.rep_dir}flow_s.csv', index=True)

    def check(self):
        print(f'\nResults check')

        # Check inflow and outflow from storage system
        check = []
        for t in self.m1.T:
            einhess = round(pe.value(self.m1.eInHess[t]), 2)
            eouthess = round(pe.value(self.m1.eOutHess[t]), 2)
            value = einhess * eouthess

            if value != 0:
                check.append({'T': t, 'eInHess': einhess, 'eOutHess': eouthess, 'value': value})

        if check:
            check_df = pd.DataFrame(check)
            check_df.to_csv(self.check_df_vars, index=False)
            print(f'HESS store and release at the same time, please check csv file: {self.check_df_vars}')

            # Check inflow and outflow of hydrogen tanks
            check_x = []
            for r, s in self.m1.S_:
                for t in self.m1.T:
                    xins = round(pe.value(self.m1.xIns[r, s, t]), 2)
                    xouts = round(pe.value(self.m1.xOuts[r, s, t]), 2)
                    xvol = round(pe.value(self.m1.xVol[r, s, t]), 2)
                    value = xins * xouts

                    if value != 0:
                        check_x.append({'ESS': r, 'Storage': s, 'T': t,
                                        'xIns': xins, 'xOuts': xouts, 'xVol': xvol, 'value': value})

            if check_x:
                check_x = pd.DataFrame(check_x)
                check_x.to_csv(self.check_df_ec, index=False)
                print(f'Devices store and release energy at the same time, please check csv file: {self.check_df_ec}')
            else:
                print(f'Inflow and outflow of storage devices are correct')

        else:
            print(f'Storage correct')

    def decision_var(self):
        print('Values of decision variables ------------------------------------------------')
        print('1) Supply ------------------------------------------------------------------------')
        supply = round(pe.value(self.m1.supply), 2)
        print(f'Supply = {supply} MW per hour')

        print('2) Storage investment ---------------------------------------------')
        # for r, s in self.m1.P:
        #     num = pe.value(self.m1.sNum[r, s])
        #     if num == 0:
        #         continue
        #     else:
        #         snum = pe.value(self.m1.sNum[r, s])
        #         # scap = round(pe.value(self.m1.sCap[s]), 2)
        #
        #     print(f'Numbers of {r, s} = {snum}')
        #     # print(f'Total capacity of {s} = {scap} MW')

        for r, e in self.m1.E_:
            num = pe.value(self.m1.eNum[r, e])
            if num == 0:
                continue
            else:
                enum = pe.value(self.m1.eNum[r, e])
                # scap = round(pe.value(self.m1.sCap[s]), 2)

            print(f'Numbers of {r, e} = {enum}')
            # print(f'Total capacity of {s} = {scap} MW')

        for r, s in self.m1.S_:
            num = pe.value(self.m1.sNum[r, s])
            if num == 0:
                continue
            else:
                snum = pe.value(self.m1.sNum[r, s])
                # scap = round(pe.value(self.m1.sCap[s]), 2)

            print(f'Numbers of {r, s} = {snum}')

        for r, x in self.m1.X_:
            num = pe.value(self.m1.xNum[r, x])
            if num == 0:
                continue
            else:
                xnum = pe.value(self.m1.xNum[r, x])
                # scap = round(pe.value(self.m1.sCap[s]), 2)

            print(f'Numbers of {r, x} = {xnum}')

    def analyze(self):
        print(f'\n Results analysis')
        print('1) Values of inflow -----------------------------------------------------------------------')
        avg_inflow = round((sum(self.m1.inflow[t] for t in self.m1.T) / self.m1.nHrs), 2)
        print(f'Average inflow = {avg_inflow} MW per hour')

        print('\n2) Values of supply and storage investment ------------------------------------------------')
        print('2.1 Supply ------------------------------------------------------------------------')
        supply = round(pe.value(self.m1.supply), 2)
        r_sa = round((supply / avg_inflow), 2)
        print(f'Supply = {supply} MW per hour, {r_sa} times of average inflow')

        print('\n2.2 Storage investment ---------------------------------------------')
        for r, e in self.m1.E_:
            num = pe.value(self.m1.eNum[r, e])
            if num == 0:
                print(f'There is no investment to {r, e}.')
                continue
            else:
                emxcap = self.m1.emxCap[r, e]

                einv = self.m1.eInv[r, e]

                if einv >= 1000:
                    # unit in [million]
                    einv = einv / 1e3
                    unit = 'million'
                else:
                    # unit in [thousand]
                    einv = einv
                    unit = 'thousand'

                enum = pe.value(self.m1.eNum[r, e])
                ecap = round(pe.value(self.m1.eCap[r, e]), 2)
                inv = round((einv * num), 2)     # yearly investment of the storage type

            print(f'\nInvestment of {r, e}:')
            print(f'Unit capacity of {r, e} is {emxcap} MW')
            print(f'Investment for one {r, e} is {einv} {unit} CNY')
            print(f'Numbers of {r, e} = {enum}')
            print(f'Total capacity = {ecap} MW')
            print(f'Total investment cost of {r, e} = {inv} {unit} CNY')

        for r, s in self.m1.S_:
            num = pe.value(self.m1.sNum[r, s])
            if num == 0:
                print(f'There is no investment to {r, s}.')
                continue
            else:
                smxcap = self.m1.smxCap[r, s]

                sinv = self.m1.sInv[r, s]

                if sinv >= 1000:
                    # unit in [million]
                    sinv = sinv / 1e3
                    unit = 'million'
                else:
                    # unit in [thousand]
                    sinv = sinv
                    unit = 'thousand'

                snum = pe.value(self.m1.sNum[r, s])
                scap = round(pe.value(self.m1.sCap[r, s]), 2)
                inv = round((sinv * num), 2)     # yearly investment of the storage type

            print(f'\nInvestment of {r, s}:')
            print(f'Unit capacity of {r, s} is {smxcap} MW')
            print(f'Investment for one {r, s} is {sinv} {unit} CNY')
            print(f'Numbers of {r, s} = {snum}')
            print(f'Total capacity = {scap} MW')
            print(f'Total investment cost of {r, s} = {inv} {unit} CNY')

        for r, x in self.m1.X_:
            num = pe.value(self.m1.xNum[r, x])
            if num == 0:
                print(f'There is no investment to {r, x}.')
                continue
            else:
                xmxcap = self.m1.xmxCap[r, x]

                xinv = self.m1.xInv[r, x]

                if xinv >= 1000:
                    # unit in [million]
                    xinv = xinv / 1e3
                    unit = 'million'
                else:
                    # unit in [thousand]
                    xinv = xinv
                    unit = 'thousand'

                xnum = pe.value(self.m1.xNum[r, x])
                xcap = round(pe.value(self.m1.xCap[r, x]), 2)
                inv = round((xinv * num), 2)     # yearly investment of the storage type

            print(f'\nInvestment of {r, x}:')
            print(f'Unit capacity of {r, x} is {xmxcap} MW')
            print(f'Investment for one {r, x} is {xinv} {unit} CNY')
            print(f'Numbers of {r, x} = {xnum}')
            print(f'Total capacity = {xcap} MW')
            print(f'Total investment cost of {r, x} = {inv} {unit} CNY')

        # energy storage at last period
        xvol_final = {}
        for r, s in self.m1.S_:
            num = pe.value(self.m1.sNum[r, s])
            if num != 0:
                xvol_final[r, s] = pe.value(self.m1.xVol[r, s, self.m1.nHrs_])
                print(f'\nFinal energy in {r, s}: {xvol_final[r, s]}')

        print('\n3) Overview of outcome variables -------------------------------------------------------------------')
        revenue = pe.value(self.m1.revenue)
        if revenue > 1000:
            # unit in [million yuan]
            unit = 'million'
            revenue = round(pe.value(self.m1.revenue) / 1e3, 2)
            income = round(pe.value(self.m1.income) / 1e3, 2)
            invcost = round(pe.value(self.m1.invCost) / 1e3, 2)
            omc = round(pe.value(self.m1.OMC) / 1e3, 2)
            storcost = round(pe.value(self.m1.storCost) / 1e3, 2)
            splscost = round(pe.value(self.m1.splsCost) / 1e3, 2)
            buycost = round(pe.value(self.m1.buyCost) / 1e3, 2)
            balcost = round(pe.value(self.m1.balCost) / 1e3, 2)
        else:
            unit = 'thousand'
            revenue = round(pe.value(self.m1.revenue), 2)
            income = round(pe.value(self.m1.income), 2)
            invcost = round(pe.value(self.m1.invCost), 2)
            omc = round(pe.value(self.m1.OMC), 2)
            storcost = round(pe.value(self.m1.storCost), 2)
            splscost = round(pe.value(self.m1.splsCost), 2)
            buycost = round(pe.value(self.m1.buyCost), 2)
            balcost = round(pe.value(self.m1.balCost), 2)

        print(f'Total revenue  = {revenue} {unit} CNY')
        print(f'Income  = {income} {unit} CNY')
        print(f'Storage cost  = {storcost} {unit} CNY')
        print(f'Balance cost  = {balcost} {unit} CNY')
        print(f'Investment cost  = {invcost} {unit} CNY')
        print(f'Operation and maintenance cost  = {omc} {unit} CNY')
        print(f'Surplus cost  = {splscost} {unit} CNY')
        print(f'Shortage cost  = {buycost} {unit} CNY')

        cost = round(storcost + balcost, 2)

        if income != 0:
            r_ci = round((cost / income * 100), 2)
        else:
            r_ci = 0

        print(f'\nRevenue and cost analysis:')
        if revenue > 0:
            r_ir = round((income / revenue), 2)
            print(f'Income is {r_ir} times of revenue')
            print(f'Total cost is {cost} {unit} CNY, the cost-income ratio is {r_ci}%')
        else:
            r_ic = round((income / cost), 2)
            r_cr = round((cost / revenue), 2)
            print(f'\nIncome is {r_ic} times of revenue')
            print(f'\nTotal cost is {cost} {unit} CNY, the cost-revenue ratio is {r_cr}%')

        print(f'\nCost structure:')
        if cost != 0:
            r_sc = round((storcost / cost * 100), 2)
            r_invc = round((invcost / cost * 100), 2)
            r_oc = round((omc / cost * 100), 2)
            r_bc = round((balcost / cost * 100), 2)

            print(f'Investment cost accounts for {r_invc}% of total cost')
            print(f'Operation and Maintenance cost accounts for {r_oc}% of total cost')
            print(f'Total storage cost is {r_sc} of total cost, and balance cost accounts for {r_bc}% of total cost')

            r_overc = round((splscost / cost * 100), 2)
            r_buyc = round((buycost / cost * 100), 2)

            if balcost != 0:
                r_ob = round((splscost / balcost * 100), 2)
                r_bb = round((buycost / balcost * 100), 2)
                print(f'Electricity loss accounts for {r_overc}% of total cost, and {r_ob}% of balance cost')
                print(f'Electricity purchase accounts for {r_buyc}% of total cost, and {r_bb}% of balance cost')
            else:
                print(f'Electricity loss accounts for {r_overc}% of total cost.')
                print(f'Electricity purchase accounts for {r_buyc}% of total cost.')

        print(f'\n4) Overview of energy flows ----------------------------------------------------------------')
        inflow_total = round((sum(self.m1.inflow[t] for t in self.m1.T)), 2)
        supply_total = round((pe.value(self.m1.supply) * self.m1.nHrs), 2)
        eout_total = round((sum(pe.value(self.m1.eOut[t]) for t in self.m1.T)), 2)
        einh_total = round((sum(pe.value(self.m1.eInHess[t]) for t in self.m1.T)), 2)
        eouth_total = round((sum(pe.value(self.m1.eOutHess[t]) for t in self.m1.T)), 2)
        esurplus_total = round(pe.value(self.m1.eSurplus), 2)
        ebought_total = round(pe.value(self.m1.eBought), 2)

        er_si = round((einh_total / inflow_total * 100), 2)
        er_esi = round((esurplus_total / inflow_total * 100), 2)

        if supply_total != 0:
            er_ds = round((eout_total / supply_total * 100), 2)
            er_ss = round((eouth_total / supply_total * 100), 2)
            er_ebs = round((ebought_total / supply_total * 100), 2)
        else:
            print(f'There is no supply.')
            er_ds = 0
            er_ss = 0
            er_ebs = 0

        print(f'Total electricity inflow is {inflow_total} MW')
        print(f'Total supply is {supply_total} MW')
        print(f'Total directly output is {eout_total} MW, {er_ds}% of the total supply.')
        print(f'Total electricity inflow to storage system is {einh_total} MW, '
              f'{er_si}% of the total inflow.')
        print(f'Total electricity outflow from storage system is {eouth_total} MW, '
              f'{er_ss}% of the total supply.')
        print(f'Total surplus (loss) is {esurplus_total} MW, '
              f'{er_esi}% of the total inflow, '
              f'costs {splscost} million CNY.')
        print(f'Total electricity purchase is {ebought_total} MW, '
              f'{er_ebs}% of the total supply, '
              f'costs {buycost} million CNY.')

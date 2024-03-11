"""
Manage parameters of the model defined in sms.py
See PyCharm help at https://www.jetbrains.com/help/pycharm/
"""

import pandas as pd
import os


class Params:
    def __init__(self, data_excel):

        self.cf_df = pd.read_excel(data_excel, sheet_name='cf')
        self.gen_df = pd.read_excel(data_excel, sheet_name='generation')
        self.time_df = pd.read_excel(data_excel, sheet_name='time')
        self.price_df = pd.read_excel(data_excel, sheet_name='price')
        self.elec_df = pd.read_excel(data_excel, sheet_name='electrozer')
        self.hytank_df = pd.read_excel(data_excel, sheet_name='tank')
        self.fcell_df = pd.read_excel(data_excel, sheet_name='fuel-cell')

        # define unit conversion factors
        self.cH2 = 0.0899   # conversion factor between hydrogen gas volume and weight, [kg/m3]
        self.cEle = 1000    # conversion factor between MW and kW
        self.hCal = 1.42351e5  # calorific value of hydrogen, [kJ/kg]
        self.eCal = 3.6e3  # calorific value of electricity, [kJ/kWh]

        # print data read from excel file
        print(f'Capacity factor:\n {self.cf_df.head()}')
        print(f'Generation: \n {self.gen_df}')
        print(f'Time related parameters:\n {self.time_df}')
        print(f'Price related parameters:\n {self.price_df}')
        print(f'Electrolyzers:\n {self.elec_df}')
        print(f'Hydrogen tanks:\n {self.hytank_df}')
        print(f'Fuel-cells: \n {self.fcell_df}')

        self.inflow = None
        self.Hrs = self.nHrs = self.ydis = None
        self.penalty = self.ePrice = self.eOver = self.eBprice = None
        self.eh2 = self.eph2 = self.h2Ratio = self.h2Res = self.h2e = None
        self.sInv = None

        self.set_inflow()
        self.set_time()
        self.set_price()
        self.set_elec()
        self.set_hyTank()
        self.set_fcell()

        self.write_to_file()
        self.write_to_excel()

    # data processing
    def set_inflow(self):    # generation
        dv_inflow = pd.DataFrame()
        for index, row in self.gen_df.iterrows():
            name = row['name']
            capacity = row['gCap']
            number = row['gNum']

            # check generation devices name is consistent
            if name in self.cf_df.columns:
                dv_inflow[f'inflow_{name}'] = self.cf_df[name] * capacity * number
            else:
                print(f"Warning: '{name}' not found in {self.cf_df}")

        self.inflow = dv_inflow.sum(axis=1)

        print(f'Inflow:\n {self.inflow.head()}')

    def set_time(self):
        self.Hrs = self.time_df.loc[0, 'Hrs']       # the duration time between each decision period (hour)
        self.nHrs = len(self.cf_df)     # the number of hours in a year
        self.ydis = self.time_df.loc[0, 'ydis']     # the yearly discount factor

        self.time_df['nHrs'] = self.nHrs

        print(f'Time related parameters are added')

    def set_price(self):
        ep = self.price_df.loc[0, 'eP']  # unit contract price, unit in [RMB/kWh]
        oc = self.price_df.loc[0, 'eO']  # unit price of managed electricity surplus, unit in [RMB/kWh]
        self.penalty = self.price_df.loc[0, 'penalty']  # penalty factor, define the price for buying electricity
        self.ePrice = ep / 1e6 * 1e3  # unit contract price, unit in [million RMB/MWh]
        self.eOver = oc / 1e6 * 1e3  # unit price of managed electricity surplus, [million RMB/MWh]

        self.price_df['ePrice'] = self.ePrice
        self.price_df['eOver'] = self.eOver

        print(f'Price related parameters are added')
        print(f'Price information:\n {self.price_df}')

        self.add_price()

    def add_price(self):
        self.eBprice = self.penalty * self.ePrice  # purchase price of buying electricity, unit in [million RMB/MWh]

        self.price_df['eBprice'] = self.eBprice

        print(f'Price related parameters are updated')
        print(f'New price information:\n {self.price_df}')

    def set_elec(self):
        eh2 = 1 / self.elec_df['toHprd'] * self.cEle * self.cH2
        invshare = (((1 + self.ydis) ** self.elec_df['n'] * self.ydis)
                    / ((1 + self.ydis) ** self.elec_df['n'] - 1))
        sinv = invshare * self.elec_df['sInvcost']

        self.elec_df['eh2'] = eh2
        self.elec_df['invshare'] = invshare
        self.elec_df['sInv'] = sinv

        print(f'New parameters of electrolyzers are added')
        print(f'{self.elec_df}')

    def set_hyTank(self):
        eph2 = (1 / self.cEle) * self.hytank_df['toHstr']
        h2res = 1 - self.hytank_df['h2Loss']
        invshare = (((1 + self.ydis) ** self.hytank_df['n'] * self.ydis)
                    / ((1 + self.ydis) ** self.hytank_df['n'] - 1))
        sinv = invshare * self.hytank_df['sInvcost']

        self.hytank_df['eph2'] = eph2
        self.hytank_df['h2Res'] = h2res
        self.hytank_df['invshare'] = invshare
        self.hytank_df['sInv'] = sinv

        print(f'New parameters of hydrogen tanks are added')
        print(f'{self.hytank_df}')

    def set_fcell(self):
        h2ratio = (self.hCal / self.eCal) * (1 / self.cEle)
        h2e = h2ratio * self.fcell_df['e']
        invshare = (((1 + self.ydis) ** self.fcell_df['n'] * self.ydis)
                    / ((1 + self.ydis) ** self.fcell_df['n'] - 1))
        sinv = invshare * self.fcell_df['sInvcost']

        self.fcell_df['h2ratio'] = h2ratio
        self.fcell_df['h2e'] = h2e
        self.fcell_df['invshare'] = invshare
        self.fcell_df['sInv'] = sinv

        print(f'New parameters of fuel-cells are added')
        print(f'{self.fcell_df}')

    def to_ampl(self):
        nhrs_str = '\nparam nHrs :=\n'

        se_str = '\nset Se :=\n'
        sh_str = '\nset Sh :=\n'
        sc_str = '\nset Sc :=\n'

        eprice_str = '\nparam ePrice :=\n'
        ebprice_str = '\nparam eBprice :=\n'
        eover_str = '\nparam eOver :=\n'

        inflow_str = "\nparam inflow :=\n"

        mxcap_str = '\nparam mxCap :=\n'
        hmxin_str = '\nparam hMxIn :=\n'
        hmxout_str = '\nparam hMxOut :=\n'
        hmi_str = '\nparam hmi :=\n'

        eh2_str = '\nparam eh2 :=\n'
        eph2_str = '\nparam eph2 :=\n'
        h2res_str = '\nparam h2Res :=\n'
        h2e_str = '\nparam h2e :=\n'

        sinv_str = '\nparam sInv :=\n'
        somc_str = '\nparam sOmc :=\n'

        # add values
        nhrs_str += f'{self.nHrs} \n'

        eprice_str += f'{self.ePrice} \n'
        ebprice_str += f'{self.eBprice.round(4)} \n'
        eover_str += f'{self.eOver} \n'

        for t, value in self.inflow.items():
            inflow_str += f'{t} {value}\n'

        for index, row in self.elec_df.iterrows():
            se_str += f'{row["name"]} \n'

            mxcap_str += f'{row["name"]} {row["mxCap"]} \n'

            eh2_str += f'{row["name"]} {round(row["eh2"], 2)} \n'

            sinv_str += f'{row["name"]} {round(row["sInv"], 4)} \n'
            somc_str += f'{row["name"]} {round(row["sOmc"], 4)} \n'

        for index, row in self.hytank_df.iterrows():
            sh_str += f'{row["name"]} \n'

            mxcap_str += f'{row["name"]} {row["mxCap"]} \n'
            hmxin_str += f'{row["name"]} {row["hMxIn"]} \n'
            hmxout_str += f'{row["name"]} {row["hMxOut"]} \n'
            hmi_str += f'{row["name"]} {row["hmi"]} \n'

            eph2_str += f'{row["name"]} {round(row["eph2"], 2)} \n'
            h2res_str += f'{row["name"]} {round(row["h2Res"], 4)} \n'

            sinv_str += f'{row["name"]} {round(row["sInv"], 4)} \n'
            somc_str += f'{row["name"]} {round(row["sOmc"], 4)} \n'

        for index, row in self.fcell_df.iterrows():
            sc_str += f'{row["name"]} \n'

            mxcap_str += f'{row["name"]} {row["mxCap"]} \n'

            h2e_str += f'{row["name"]} {round(row["h2e"], 2)} \n'

            sinv_str += f'{row["name"]} {round(row["sInv"], 4)} \n'
            somc_str += f'{row["name"]} {round(row["sOmc"], 4)} \n'

        nhrs_str += ';\n'
        se_str += ';\n'
        sh_str += ';\n'
        sc_str += ';\n'
        eprice_str += ';\n'
        ebprice_str += ';\n'
        eover_str += ';\n'
        inflow_str += ';\n'
        mxcap_str += ';\n'
        hmxin_str += ';\n'
        hmxout_str += ';\n'
        hmi_str += ';\n'
        eh2_str += ';\n'
        eph2_str += ';\n'
        h2res_str += ';\n'
        h2e_str += ';\n'
        sinv_str += ';\n'
        somc_str += ';\n'

        ampl_dat = (nhrs_str + se_str + sh_str + sc_str + eprice_str + ebprice_str + eover_str + inflow_str
                    + mxcap_str + hmxin_str + hmxout_str + hmi_str
                    + eh2_str + eph2_str + h2res_str + h2e_str
                    + sinv_str + somc_str)

        return ampl_dat

    def write_to_file(self):
        ampl_dat = self.to_ampl()
        filename = f'{data_dir}dat1.dat'
        with open(filename, 'w') as file:
            file.write(f'# test data for Matouqin \n')
            file.write(ampl_dat)
        print(f"Data written to {filename}")

    def write_to_excel(self):
        excel_file = f'{data_dir}all_params.xlsx'

        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            self.cf_df.to_excel(writer, sheet_name='cf', index=False)
            self.gen_df.to_excel(writer, sheet_name='generation', index=False)
            self.time_df.to_excel(writer, sheet_name='time', index=False)
            self.price_df.to_excel(writer, sheet_name='price', index=False)
            self.elec_df.to_excel(writer, sheet_name='electrolyzer', index=False)
            self.hytank_df.to_excel(writer, sheet_name='hytank', index=False)
            self.fcell_df.to_excel(writer, sheet_name='fuel-cell', index=False)


path = '.'
data_dir = f'{path}/Data/'
f_data = f'{data_dir}dat1.xlsx'
par = Params(f_data)

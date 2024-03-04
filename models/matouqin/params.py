"""
Manage parameters of the model defined in sms.py
See PyCharm help at https://www.jetbrains.com/help/pycharm/
"""

import pandas as pd
import os

path = '.'
data_dir = f'{path}/Data/'


class Genparams:
    def __init__(self):
        self.dv_gen = {}  # set of renewable power generation devices

    @staticmethod
    def read_gCapf(data_path, col_name, sheet_name='gCapf'):   # read capacity factor data form excel
        df = pd.read_excel(data_path, sheet_name=sheet_name)
        if col_name in df.columns:
            df = df.round({col_name: 2})    # round keep two decimals
            gcapf_dict = pd.Series(df[col_name].values, index=df.iloc[:, 0]).to_dict()  # convert to dict [time: value]
            return gcapf_dict
        else:
            raise ValueError(f"Column '{col_name}' not found in the Excel sheet.")

    def add_device(self, name, gcap, gnum):     # add device one by one
        gcapf_path = f'{data_dir}gCapf.xlsx'
        gcapf = self.read_gCapf(gcapf_path, name)   # read capacity factor data from excel
        inflow = {}
        for t, value in gcapf.items():
            inflow[t] = value * gcap * gnum
        self.dv_gen[name] = {
            'unit capacity': gcap,
            'capacity factor': gcapf,
            'number of generation devices': gnum,
            f'{name} inflow': inflow
        }

    def add_device_from_info(self, info):    # add devices from an info list ['name': , 'gcap': , 'gnum':]
        for device in info:
            self.add_device(device['name'], device['gcap'], device['gnum'])

    def remove_device(self, name):  # delete devices
        if name in self.dv_gen:
            del self.dv_gen[name]

    def to_ampl(self):
        gcap_str = "param gCap :=\n"
        gcapf_str = "param gCapf :=\n"
        gnum_str = "param gNum :=\n"
        inflow_str = "param inflow :=\n"
        # inflow_str = "param inflow :=\n"
        for device, params in self.dv_gen.items():
            gcap_str += f"{device} {params['unit capacity']}\n"
            gnum_str += f"{device} {params['number of generation devices']}\n"
            for key, value in params['capacity factor'].items():
                gcapf_str += f"{device} {key} {value}\n"
            for key, value in params[f'{device} inflow'].items():
                inflow_str += f"{key} {value}\n"
        gcap_str += ";\n"
        gnum_str += ";\n"
        gcapf_str += ";\n"
        inflow_str += ";\n"

        # return gcap_str + gcapf_str + gnum_str + inflow_str
        return inflow_str

    def write_to_file(self, filename):
        ampl_data = self.to_ampl()
        with open(filename, 'w') as file:
            file.write(f'# Add inflow\n')
            file.write(ampl_data)
        print(f"Data written to {filename}")


class StorParam:
    def __init__(self):
        # todo: define the needed data structures, e.g., dict, lists, df (DataFrames)

        self.ver = '0.1'  # version of data

        # define sets
        self.dv_eletr = {}      # electrolyzers
        self.dv_hyTank = {}     # hydrogen tanks
        self.dv_fuCell = {}     # fuel cells
        self.dv_stor = {}

        # set initial values
        self.nHrs = self.Hrs = self.ydis = None
        self.cH2 = self.cEle = self.hCal = self.eCal = None
        self.penalty = self.ePrice = self.eOver = self.eBprice = None
        self.eh2 = self.eph2 = self.h2Ratio = self.h2Res = self.h2e = None
        self.sInv = None

        # define parameter groups 1) time, 2) unit conversion, 3) price parameters
        self.time = {}
        self.con_unit = {}
        self.price = {}

        # self.set_time()         # set initial time parameters
        self.set_con_unit()     # set unit conversion parameters
        # self.set_price()        # set initial electricity price related parameters
        # self.add_price()        # add electricity purchase price

    def set_time(self, nhrs, hrs, ydis):
        self.nHrs = nhrs  # the number of hours in a year
        self.Hrs = hrs  # the duration time between each decision period (hour)
        self.ydis = ydis  # the yearly discount factor

        self.time.update({
            'nHrs': self.nHrs,
            'Hrs': self.Hrs,
            'ydis': self.ydis
        })

        print(f'Time related parameters are added')
        print(f'Time information: {self.time}')

    def set_con_unit(self):
        self.cH2 = 0.0899   # conversion factor between hydrogen gas volume and weight, [kg/m3]
        self.cEle = 1000    # conversion factor between MW and kW
        self.hCal = 1.42351e5  # calorific value of hydrogen, [kJ/kg]
        self.eCal = 3.6e3  # calorific value of electricity, [kJ/kWh]

        self.con_unit.update({
            'cH2': f'{self.cH2:.2e}',
            'cEle': f'{self.cEle:.2e}',
            'hCal': f'{self.hCal:.2e}',
            'eCal': f'{self.eCal:.2e}'
        })

        print(f'Unit conversion related parameters are added')
        print(f'Unit conversion information: {self.con_unit}')

    def set_price(self, eprice, eover, penalty):
        ep = eprice    # unit contract price, unit in [RMB/kWh]
        oc = eover    # unit price of managed electricity surplus, unit in [RMB/kWh]
        self.penalty = penalty  # penalty factor, used to define the price for buying electricity
        self.ePrice = ep / 1e6 * 1e3    # unit contract price, unit in [million RMB/MWh]
        self.eOver = oc / 1e6 * 1e3  # unit price of managed electricity surplus, [million RMB/MWh]

        self.price.update({
            'penalty': f'{self.penalty:.2e}',
            'ePrice': f'{self.ePrice:.2e}',
            'overCost': f'{self.eOver:.2e}'
        })

        print(f'Price related parameters are added')
        print(f'Price information: {self.price}')

        self.add_price()

    def add_price(self):
        self.eBprice = self.penalty * self.ePrice   # purchase price of buying electricity, unit in [million RMB/MWh]

        self.price.update({
            'eBprice': f'{self.eBprice:.2e}'
        })

        print(f'Price related parameters are updated')
        print(f'New price information: {self.price}')

    def set_dv_eletr(self, name, mxcap, n, tohprd, sinvcost, somc):  # add device one by one
        self.dv_eletr[name] = {
            'unit_cap': mxcap,
            'life_time': n,
            'ele_consumption': tohprd,
            'inv_total': sinvcost,
            'OMC': somc
        }

        print(f'Device {name} is added')

    def add_dv_eletr(self, name):
        self.eh2 = 1 / self.dv_eletr[name]['ele_consumption'] * self.cEle * self.cH2
        invshare = (((1 + self.ydis) ** self.dv_eletr[name]['life_time'] * self.ydis)
                    / ((1 + self.ydis) ** self.dv_eletr[name]['life_time'] - 1))
        self.sInv = invshare * self.dv_eletr[name]['inv_total']
        self.dv_eletr[name].update({
            'eh2': f'{self.eh2:.2e}',
            'invShare': f'{invshare:.2e}',
            'sInv': f'{self.sInv:.2e}'
        })

        print(f'New parameters of device {name} are added')
        print(f'{self.dv_eletr}')

    def set_dv_hyTank(self, name, mxcap, hmxin, hmxout, hmis, n, tohstr, h2loss, sinvcost, somc):
        self.dv_hyTank[name] = {
            'unit_cap': mxcap,
            'hyin_max': hmxin,
            'hyout_max': hmxout,
            'hy_min': hmis,
            'life_time': n,
            'elep_consumption': tohstr,
            'hy_loss': h2loss,
            'inv_total': sinvcost,
            'OMC': somc
        }
        print(f'Device {name} is added')

    def add_dv_hyTank(self, name):
        self.eph2 = self.cEle * self.dv_hyTank[name]['elep_consumption']
        self.h2Res = 1 - self.dv_hyTank[name]['hy_loss']
        invshare = (((1 + self.ydis) ** self.dv_hyTank[name]['life_time'] * self.ydis)
                    / ((1 + self.ydis) ** self.dv_hyTank[name]['life_time'] - 1))
        self.sInv = invshare * self.dv_hyTank[name]['inv_total']
        self.dv_hyTank[name].update({
            'eph2': f'{self.eph2:.2e}',
            'h2Res': f'{self.h2Res:.2e}',
            'invShare': f'{invshare:.2e}',
            'sInv': f'{self.sInv:.2e}'
        })

        print(f'New parameters of device {name} are added')

    def set_dv_fuCell(self, name, mxcap, n, e, sinvcost, somc):
        self.dv_fuCell[name] = {
            'unit_cap': mxcap,
            'life_time': n,
            'efficiency': e,
            'inv_total': sinvcost,
            'OMC': somc
        }
        print(f'Device {name} is added')

    def add_dv_fuCell(self, name):
        h2ratio = (self.hCal / self.eCal) * (1 / self.cEle)
        self.h2e = h2ratio * self.dv_fuCell[name]['efficiency']
        invshare = (((1 + self.ydis) ** self.dv_fuCell[name]['life_time'] * self.ydis)
                    / ((1 + self.ydis) ** self.dv_fuCell[name]['life_time'] - 1))
        self.sInv = invshare * self.dv_fuCell[name]['inv_total']
        self.dv_fuCell[name].update({
            'h2Ratio': f'{h2ratio:.2e}',
            'h2e': f'{self.h2e:.2e}',
            'invShare': f'{invshare:.2e}',
            'sInv': f'{self.sInv:.2e}'
        })

        print(f'New parameters of device {name} are added')

    def set_dv_stor(self, ty, info):  # add devices from an info list [type, 'name': xxx, ....], list contain dicts
        if ty == 'electrolyzer':
            for dv in info:
                self.set_dv_eletr(dv['name'], dv['unit_cap'], dv['life_time'], dv['ele_consumption'],
                                  dv['inv_total'], dv['OMC'])
                self.add_dv_eletr(dv['name'])

        elif ty == 'hyTank':
            for dv in info:
                self.set_dv_hyTank(dv['name'], dv['unit_cap'], dv['hyin_max'], dv['hyout_max'], dv['hy_min'],
                                   dv['life_time'], dv['elep_consumption'], dv['hy_loss'],
                                   dv['inv_total'], dv['OMC'])
                self.add_dv_hyTank(dv['name'])

        elif ty == 'fuel-cell':
            for dv in info:
                self.set_dv_fuCell(dv['name'], dv['unit_cap'], dv['life_time'], dv['efficiency'],
                                   dv['inv_total'], dv['OMC'])
                self.add_dv_fuCell(dv['name'])

        self.update_dv_stor()

    def update_dv_stor(self):
        self.dv_stor.clear()    # clear current storage
        self.dv_stor = {**self.dv_eletr, **self.dv_hyTank, **self.dv_fuCell}

    def remove_dv_stor(self, dv_list):  # delete devices, dv_list contains name of devices
        for dv in dv_list:
            delete = False    # use to determine if devices were found and deleted

            if dv in self.dv_eletr:     # delete electrolyzers
                del self.dv_eletr[dv]
                print(f'{dv} is deleted')
                delete = True
            if dv in self.dv_hyTank:    # delete hydrogen tanks
                del self.dv_hyTank[dv]
                print(f'{dv} is deleted')
                delete = True
            if dv in self.dv_fuCell:  # delete fuel-cells
                del self.dv_fuCell[dv]
                print(f'{dv} is deleted')
                delete = True

            if not delete:
                print(f'Device {dv} does not exist.')

        self.update_dv_stor()

    def display_dv_stor(self):
        # check if dv_stor is empty
        if not self.dv_stor:
            print("dv_stor is currently empty.")
            return

        # if not, print
        print(f'Device information:')
        for dv, info in self.dv_stor.items():
            print(f'\t{dv}: {info}')
        print('----------------------------------------------------------------')

    def to_ampl(self):
        se_str = 'set Se :=\n'
        sh_str = '\nset Sh :=\n'
        sc_str = '\nset Sc :=\n'
        nhrs_str = '\nparam nHrs :=\n'
        eprice_str = '\nparam ePrice :=\n'
        ebprice_str = '\nparam eBprice :=\n'
        eover_str = '\nparam eOver :=\n'
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

        for dv, params in self.dv_eletr.items():
            se_str += f'{dv}\n'
            eh2_str += f'{dv} {params["eh2"]}\n'

        for dv, params in self.dv_hyTank.items():
            sh_str += f'{dv}\n'
            hmxin_str += f'{dv} {params["hyin_max"]}\n'
            hmxout_str += f'{dv} {params["hyout_max"]}\n'
            hmi_str += f'{dv} {params["hy_min"]}\n'
            eph2_str += f'{dv} {params["eph2"]}\n'
            h2res_str += f'{dv} {params["h2Res"]}\n'

        for dv, params in self.dv_fuCell.items():
            sc_str += f'{dv}\n'
            h2e_str += f'{dv} {params["h2e"]}\n'

        nhrs_str += f'{self.nHrs}\n'
        eprice_str += f'{self.ePrice}\n'
        ebprice_str += f'{self.eBprice:.2e}\n'
        eover_str += f'{self.eOver}\n'

        for dv, params in self.dv_stor.items():
            mxcap_str += f'{dv} {params["unit_cap"]}\n'
            sinv_str += f'{dv} {params["sInv"]}\n'
            somc_str += f'{dv} {params["OMC"]}\n'

        se_str += ';\n'
        sh_str += ';\n'
        sc_str += ';\n'
        nhrs_str += ';\n'
        eprice_str += ';\n'
        ebprice_str += ';\n'
        eover_str += ';\n'
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

        info_str = (se_str + sh_str + sc_str + nhrs_str + eprice_str + ebprice_str + eover_str
                    + mxcap_str + hmxin_str + hmxout_str + hmi_str + eh2_str + eph2_str + h2res_str + h2e_str
                    + sinv_str + somc_str)
        return info_str

    def write_to_file(self, filename):
        ampl_data = self.to_ampl()
        with open(filename, 'a') as file:
            file.write('\n\n# Add storage\n')
            file.write(ampl_data)
        print(f"Data written to {filename}")


# ----------------------------------------------------------------
generation = Genparams()
# generation.add_device('Wind1', 500, 3)
gen_info = [
    {'name': 'Wind1', 'gcap': 1000, 'gnum': 5},
    {'name': 'Wind2', 'gcap': 1500, 'gnum': 4}]
generation.add_device_from_info(gen_info)   # add power generation devices from a list
generation.remove_device('Wind2')
print(generation.to_ampl())
generation.write_to_file(f'{data_dir}data.dat')

# ----------------------------------------------------------------
storage = StorParam()
storage.set_time(4, 1, 0.05)
storage.set_price(0.8, 8, 5)

eletr_info = [
    {'name': 'Elec1', 'unit_cap': 5, 'life_time': 10, 'ele_consumption': 4.5, 'inv_total': 0.7, 'OMC': 0.005}
    ]
hytank_info = [
    {'name': 'Tank1', 'unit_cap': 1000, 'hyin_max': 300, 'hyout_max': 300, 'hy_min': 5, 'life_time': 20,
     'elep_consumption': 1, 'hy_loss': 0,
     'inv_total': 0.5, 'OMC': 0.005}
    ]
fucell_info = [
    {'name': 'Cell1', 'unit_cap': 300, 'life_time': 20, 'efficiency': 0.7, 'inv_total': 0.3, 'OMC': 0.005}
    ]
storage.set_dv_eletr('Elec1', 5, 10, 4.5, 7, 0.005)
storage.add_dv_eletr('Elec1')

# storage.set_dv_stor('electrolyzer', eletr_info)   # add eletrolyzers
storage.set_dv_stor('hyTank', hytank_info)  # add hydrogen tanks
storage.set_dv_stor('fuel-cell', fucell_info)    # add fuel-cells
# remove_dv_stor({'Elec1', 'Tank1'})   # delete storage devices
storage.display_dv_stor()
print(storage.to_ampl())
storage.write_to_file(f'{data_dir}data.dat')

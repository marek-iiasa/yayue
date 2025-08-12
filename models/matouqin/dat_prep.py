"""
Generate ampl format model parameters defined in sms.py
See PyCharm help at https://www.jetbrains.com/help/pycharm/
"""

import pandas as pd
from pathlib import Path
import re       # use regular expression
import random


class Params:
    def __init__(self, data_dir, data_file, ampl_file):
        self.data_dir = data_dir
        self.data_orig = data_file
        self.ampl_file = ampl_file

        # define initial value
        self.data_type = None   # original datafile type: xlsx, csv, dat
        self.f_data = None      # original data file

        self.cf_df = pd.DataFrame()         # capacity factor
        self.VRE_df = pd.DataFrame()        # VRE generation devices
        self.time_df = pd.DataFrame()       # time
        self.prices_df = pd.DataFrame()      # electricity prices
        self.E2X_df = pd.DataFrame()        # E2X converters, eg: electrolyzers
        self.storage_df = pd.DataFrame()          # Storage devices, eg: hydrogen tanks
        self.X2E_df = pd.DataFrame()        # X2E converters, eg: fuel cells

        # read data from data file
        self.process_f_name()       # extract datafile suffix
        self.read_datafile()        # read and store data in dataframe

        # define default unit conversion factors
        # self.cH2 = 0.0899   # conversion factor between hydrogen gas volume and weight, [kg/m3]
        # self.cEle = 1000    # conversion factor between MW and kW, 1 MW = 1000 KW
        # self.hCal = 33.3    # calorific value of hydrogen, [kWh/kg], (= 120 MJ/kg / 3.6MJ/kWh)
        # self.hCal = 39.4  # calorific value of hydrogen, [kWh/kg], (= 142 MJ/kg / 3.6MJ/kWh)
        # self.hHcv = 1.42351e5  # high calorific value of hydrogen, [kJ/kg]
        # self.hLcv = 1.2e5      # low calorific value of hydrogen, [kJ/kg]
        # self.eCal = 3.6e3  # calorific value of electricity, [kJ/kWh]

        # define default parameters
        self.R = None
        self.inflow = self.pOut = None
        self.nHrs = self.ydis = self.intv = None
        self.idx_sets = []
        # self.ePrice = self.eSprice = self.eBprice = None
        # self.e2x = self.e2s = self.xRes = self.x2e = None

    # read and print original data --------------------------------------------------
    def process_f_name(self):       # define or extract datafile type.
        if isinstance(self.data_orig, list):
            self.data_type = f'.csv'
        elif isinstance(self.data_orig, str):
            # self.data_type = os.path.splitext(self.data_orig)[1]        # [1], extract the suffix
            self.data_type = Path(self.data_orig).suffix.lower()        # get suffix
        else:
            raise TypeError(f'data_orig must be a list or str')

    def read_datafile(self):    # check data files and read data according to different raw data types
        print(f'Read data from {self.data_type} files')

        if self.data_type == '.xlsx':
            # select the original data file
            self.f_data = self.data_dir / 'Raw' / self.data_orig

            # check whether the original data file exists
            if not self.f_data.is_file():
                raise FileNotFoundError(f'Input data file {self.f_data} does not exist')
            else:
                print(f'Selected original data file: {self.f_data}')

            # read original data from Excel file
            self.cf_df = pd.read_excel(self.f_data, sheet_name='cf')      # capacity factor
            self.VRE_df = pd.read_excel(self.f_data, sheet_name='VRE')              # VRE generation devices
            self.time_df = pd.read_excel(self.f_data, sheet_name='time')                # time
            self.prices_df = pd.read_excel(self.f_data, sheet_name='prices')             # prices
            self.E2X_df = pd.read_excel(self.f_data, sheet_name='E2X')              # E2X converters
            self.storage_df = pd.read_excel(self.f_data, sheet_name='storage')            # Storage devices
            self.X2E_df = pd.read_excel(self.f_data, sheet_name='X2E')              # X2E converters

            print(f'Original data has been stored in dataframe')

        elif self.data_type == '.csv':
            # check whether the original data file exists
            f_csv = [f.name for f in (self.data_dir / 'Raw').iterdir() if f.suffix == '.csv']

            f_csv_lost = [f'{name}.csv' for name in self.data_orig if f'{name}.csv' not in f_csv]
            if f_csv_lost:
                raise ValueError(f'Warning: The following .csv files are missing: {f_csv_lost}.')
            else:
                print(f'All required .csv data files are present: {f_csv}.')
                self.f_data = f'7 csv files.'

            # select and read the original data file
            for name in self.data_orig:
                f_path = self.data_dir / 'Raw' / f'{name}{self.data_type}'      # create csv file path
                setattr(self, f'{name}_df', pd.read_csv(f_path))     # read and save in self.{name}_df

            print(f'Original data has been stored in dataframe')

        elif self.data_type == '.dat':
            # select the original data file
            self.f_data = self.data_dir / 'Raw' / self.data_orig

            # check whether the original data file exists
            if not self.f_data.is_file():
                raise FileNotFoundError(f'Input data file {self.f_data} does not exist')
            else:
                print(f'Selected original data file: {self.f_data}')

    # update cf from csv file
    def upd_cf(self, file_new, time):
        cf_new = pd.read_csv(file_new)

        if self.data_type == '.dat':
            raise ValueError(f'Wrong input data file: there is no parameter "cf" in {self.f_data}.\n'
                             f'Please check {self.f_data}, it should be csv name list or .xlsx format file.')

        # update cf by name and time
        print(f'\nUpdating capacity factor for year: {time}')
        upd_t = False       # True if the number of time periods has been updated
        for name in self.cf_df.columns[1:]:
            col = f'{name}_{time}'
            if col in cf_new:
                if not upd_t:
                    n_cf_old = len(self.cf_df)
                    n_cf_new = len(cf_new[col].dropna())

                    # uniform rows
                    if n_cf_old < n_cf_new:
                        self.cf_df = self.cf_df.reindex(range(n_cf_new))        # expend rows
                    else:
                        self.cf_df = self.cf_df.iloc[:n_cf_new].copy()          # drop surplus rows

                    self.cf_df['Time period'] = range(0, n_cf_new)              # generate new period index
                    upd_t = True
                self.cf_df[name] = cf_new[col].astype(float)             # update data and keep original col name
                print(f'"cf" data has been changed to {time}.')
            else:
                print(f'Warning: {col} not found in {cf_new}.')

    def print_df(self):
        # print data read from Excel/Csv files

        if self.data_type == '.dat':
            print(f'Data type is ".dat". Skipping parameter printing.')
            return

        print(f'\nParameter printing start:')
        print(f'Capacity factor:\n {self.cf_df.head()}')
        print(f'VRE generation devices: \n {self.VRE_df}')
        print(f'VRE Inflow:\n {self.inflow.head()}')
        print(f'Time related parameters:\n {self.time_df}')
        print(f'Price related parameters:\n {self.prices_df}')
        print(f'E2X converters:\n {self.E2X_df}')
        print(f'Storage devices:\n {self.storage_df}')
        print(f'X2E converters: \n {self.X2E_df}')
        print(f'Parameter printing completed.')

    def xlsx_to_csv(self):      # transform xlsx file to csv format
        if self.data_type == f'.xlsx':
            print(f'\nConverting Excel to CSV:')
            f_xlsx_dir = self.data_dir / 'Raw' / self.data_orig
            f_xlsx = pd.read_excel(f_xlsx_dir, sheet_name=None)

            n = 0       # count csv files

            for sheet, df in f_xlsx.items():
                csv_name = f'{sheet}.csv'
                df.to_csv(f'{self.data_dir}/Raw/{csv_name}', index=False, encoding='utf-8')
                print(f'Saved {sheet} to {csv_name}')
                n += 1

            if n == 7:
                print(f'Created {n} csv data files.')
            else:
                m = 7 - n
                print(f'{m} sheets missing , please check.')

        else:
            raise ValueError(f'File type error, {self.f_data} should be an Excel file, please check.')

    # data preprocessing ----------------------------------------------------------------
    # 1. Process data
    # 0) precess data, all steps
    def process_data(self):
        # redefine default parameters

        if self.data_type == '.xlsx' or self.data_type == '.csv':
            print(f'\nData preprocessing begin:')

            self.set_inflow()   # set inflow
            self.set_time()     # set time
            self.set_price()    # set prices
            self.set_R()        # set ESSs

            self.set_E2X()      # set E2X converters
            self.set_S()        # set storage devices
            self.set_X2E()      # set X2E converters

            print(f'Data preprocessing end.')

            self.write_to_ampl()  # store in ampl format .dat file

        elif self.data_type == '.dat':
            print(f'Data file is of correct ".dat" type. Skipping process_data.\n'
                  f' Notes:\n'
                  f' Generate data slices for different time periods: self.set_dat(t_new), '
                  f'reset params: nHrs, inflow, ePrice, Invs and OMCs;\n'
                  f' Add outflow pattern "pOut": self.upd_pOut(file_new).')

    # 1) generated inflows
    def set_inflow(self):    # VRE generation
        vre_df = pd.DataFrame()
        for index, row in self.VRE_df.iterrows():
            name = row['name']
            capacity = row['gCap']
            number = row['gNum']

            # check consistence of VRE generation devices
            if name in self.cf_df.columns:
                vre_df[f'inflow_{name}'] = self.cf_df[name] * capacity * number  # unit in MW
            else:
                print(f"Warning: '{name}' is not found in {self.cf_df}")

        if vre_df.empty:
            print('Warning: No VRE inflow calculated. self.inflow will be empty.')
            self.inflow = pd.Series(dtype=float)        # keep type consistent
        else:
            self.inflow = vre_df.sum(axis=1)            # total VRE inflow = sum of all device inflows

        print(f'Inflow complete.')

    # 2) set time related parameters
    def set_time(self):
        self.nHrs = len(self.cf_df)                 # generate number of time periods from cf_df
        self.time_df['nHrs'] = self.nHrs            # the number of time periods
        self.ydis = self.time_df.loc[0, 'ydis']     # the yearly discount factor
        self.intv = self.time_df.loc[0, 'intv']     # h, time interval between every two periods

        print(f'Time related params complete.')

    # 3) set price unit in MW/h
    def set_price(self):
        price_df = self.prices_df
        ep, eb, es = price_df.loc[0, ['eP', 'eB', 'eS']]        # prices in [CNY/kWh]
        # ep = price_df.loc[0, 'eP']     # unit contract price, unit in [CNY/kWh]
        # eb = price_df.loc[0, 'eB']     # unit purchase price, [CNY/kWh]
        # es = price_df.loc[0, 'eS']     # unit price of managing electricity surplus, unit in [CNY/kWh]
        # ep = ep * 1e3 / 1e3            # unit in [thousand CNY/MWh]
        # eb = eb * 1e3 / 1e3            # unit in [thousand CNY/MWh]
        # es = es * 1e3 / 1e3            # unit in [thousand CNY/MWh]

        price_df['ePrice'] = ep * self.nHrs        # annual contract price (constant), unit in [thousand CNY/(MWh*year)]
        price_df['eBprice'] = eb                   # unit purchase price, [thousand CNY/MWh]
        price_df['eSprice'] = es  # unit surplus price, [thousand CNY/MWh]

        print(f'Prices complete.')

    # 4) define set R (ESSs)
    def set_R(self):
        r_e2x = set(self.E2X_df['ESS'].unique())        # select non-repetitive ESSs in E2X_df
        r_s = set(self.storage_df['ESS'].unique())            # select non-repetitive ESSs in S_df
        r_x2e = set(self.X2E_df['ESS'].unique())        # select non-repetitive ESSs in X2E_df
        self.R = sorted(r_e2x | r_s | r_x2e)            # define set R, sorted by A-Z

        print(f'ESSs set "R" completes.')

    # 5) define E2X parameters
    def set_E2X(self):
        e2x_df = self.E2X_df

        # define e2x conversion factor, [xxx/MW]
        e2x = e2x_df['e2e'] * e2x_df['eqx'] * e2x_df['e2xe']
        e2x = e2x * self.intv        # unit in [xxx/MW], per time period
        e2x_df['e2x'] = e2x
        # e2e = e2x_df['e2e']        # rectification efficiency, [0-1], e.g., AC/DC or DC/AC conversion factor.
        # eqx = e2x_df['e2e']        # equivalent calorific value, [XXX (energy form unit)/MWh]
        # e2xe = e2x_df['e2xe']      # E2X conversion efficiency, [0-1], e.g., electrolyzer: 0.6 (60%).
        # e2x = e2e * eqx * e2xe     # E2X conversion factor is defined by the product of the above three factors

        # define annuity factor, used to generate annualized investment cost (pay at the end of year)
        e2x_df['ann'] = (((1 + self.ydis) ** e2x_df['n'] * self.ydis) / ((1 + self.ydis) ** e2x_df['n'] - 1))
        # pay at the beginning of year
        # e2x_df['ann'] = (((1 + self.ydis) ** (e2x_df['n']+1) * self.ydis)
        #             / ((1 + self.ydis) ** e2x_df['n'] - 1))

        # define annual investment cost
        e2x_df['eInv'] = e2x_df['eInv_tot'] * e2x_df['ann']

        print(f'E2X complete.')

    # 6) define Storage parameters
    def set_S(self):
        s_df = self.storage_df

        # define xRes
        xres = 1 - s_df['xLoss']        # self reservation xRes (per hour)
        xres = xres ** self.intv        # self reservation per period
        s_df['xRes'] = xres

        # define e2s per period
        s_df['e2s'] = s_df['e2s'] * self.intv       # e2s per period

        # define annuity factor, used to generate annualized investment cost (pay at the end of year)
        s_df['ann'] = (((1 + self.ydis) ** s_df['n'] * self.ydis) / ((1 + self.ydis) ** s_df['n'] - 1))

        # define annual investment cost
        s_df['sInv'] = s_df['sInv_tot'] * s_df['ann']

        print(f'Storage devices complete.')

    # 7) define X2E parameters
    def set_X2E(self):
        x2e_df = self.X2E_df

        # define X2E conversion factor, [xxx/MW]
        x2e = x2e_df['e2e'] * x2e_df['xqe'] * x2e_df['x2ee']
        x2e = x2e * self.intv        # unit in [xxx/MW], per time period
        x2e_df['x2e'] = x2e

        # define annuity factor, used to generate annualized investment cost (pay at the end of year)
        x2e_df['ann'] = (((1 + self.ydis) ** x2e_df['n'] * self.ydis) / ((1 + self.ydis) ** x2e_df['n'] - 1))

        # define annual investment cost
        x2e_df['xInv'] = x2e_df['xInv_tot'] * x2e_df['ann']

        print(f'X2E complete.')

    # print indexed sets E2X_r, S_r, and X2E_r
    def set_idx_set(self, idx_set, df, name_col):
        if df is None or len(df) == 0:
            return
        for r in self.R:
            sub = df[df['ESS'].astype(str).str.strip() == str(r)].copy()      # pick rows
            if sub.empty:       # no device for this ESS in df, skip
                continue
            text = [f'\nset {idx_set}[{r}] :=\n']
            for name in sub[name_col]:
                text.append(f'{name}\n')
            text.append(';\n')
            self.idx_sets.append(''.join(text))

        print(f'Indexed set(s) {idx_set}_r has been added.')

    # 8) write parameters used in matouqin model to ampl format
    def to_ampl(self):
        blocks = {
            'nhrs': '\nparam nHrs :=\n',
            'intv': '\nparam intv :=\n',
            'r': '\nset R :=\n',

            'ep': '\nparam ePrice :=\n',
            'ebp': '\nparam eBprice :=\n',
            'esp': '\nparam eSprice :=\n',

            'inflow': '\nparam inflow :=\n',

            'emxcap': '\nparam emxCap :=\n',
            'e2x': '\nparam e2x :=\n',
            'einv': '\nparam eInv :=\n',
            'eomc': '\nparam eOMC :=\n',

            'smxcap': '\nparam smxCap :=\n',
            'e2s': '\nparam e2s :=\n',
            'mxsin': '\nparam mxsIn :=\n',
            'mxsout': '\nparam mxsOut :=\n',
            'sini': '\nparam sini :=\n',
            'xch': '\nparam xCh :=\n',
            'xdis': '\nparam xDid :=\n',
            'xres': '\nparam xRes :=\n',
            'sinv': '\nparam sInv :=\n',
            'somc': '\nparam sOMC :=\n',

            'xmxcap': '\nparam xmxCap :=\n',
            'x2e': '\nparam x2e :=\n',
            'xinv': '\nparam xInv :=\n',
            'xomc': '\nparam xOMC :=\n',
        }

        # add values
        blocks['nhrs'] += f'{self.nHrs}\n'
        blocks['intv'] += f'{self.intv}\n'
        blocks['ep'] += f'{self.prices_df["ePrice"].iloc[0]:.3f}\n'
        blocks['ebp'] += f'{self.prices_df["eBprice"].iloc[0]:.3f}\n'
        blocks['esp'] += f'{self.prices_df["eSprice"].iloc[0]:.3f}\n'

        for r in self.R:
            blocks['r'] += f'{r}\n'

        for t, value in self.inflow.items():
            blocks['inflow'] += f'{t} {value:.2f}\n'

        for _, row in self.E2X_df.iterrows():
            ess_e, e2x = row['ESS'], row['E2X']

            blocks['emxcap'] += f'{ess_e} {e2x} {row["emxCap"]}\n'
            blocks['e2x'] += f'{ess_e} {e2x} {round(row["e2x"], 2)}\n'
            blocks['einv'] += f'{ess_e} {e2x} {round(row["eInv"], 2)}\n'
            blocks['eomc'] += f'{ess_e} {e2x} {round(row["eOMC"], 2)}\n'

        for _, row in self.storage_df.iterrows():
            ess_s, s = row['ESS'], row['Storage']

            blocks['smxcap'] += f'{ess_s} {s} {row["smxCap"]}\n'
            blocks['e2s'] += f'{ess_s} {s} {row["e2s"]}\n'
            blocks['mxsin'] += f'{ess_s} {s} {row["mxsIn"]}\n'
            blocks['mxsout'] += f'{ess_s} {s} {row["mxsOut"]}\n'
            blocks['sini'] += f'{ess_s} {s} {row["sini"]}\n'

            blocks['xch'] += f'{ess_s} {s} {round(row["xCh"], 2)}\n'
            blocks['xdis'] += f'{ess_s} {s} {round(row["xDis"], 2)}\n'
            blocks['xres'] += f'{ess_s} {s} {round(row["xRes"], 2)}\n'

            blocks['sinv'] += f'{ess_s} {s} {round(row["sInv"], 2)}\n'
            blocks['somc'] += f'{ess_s} {s} {round(row["sOMC"], 2)}\n'

        for _, row in self.X2E_df.iterrows():
            ess_x, x2e = row['ESS'], row['X2E']

            blocks['xmxcap'] += f'{ess_x} {x2e} {row["xmxCap"]}\n'
            blocks['x2e'] += f'{ess_x} {x2e} {round(row["x2e"], 2)}\n'
            blocks['xinv'] += f'{ess_x} {x2e} {round(row["xInv"], 2)}\n'
            blocks['xomc'] += f'{ess_x} {x2e} {round(row["xOMC"], 2)}\n'

        for k in blocks:
            blocks[k] += f';\n'

        self.set_idx_set("E", self.E2X_df, name_col="E2X")
        self.set_idx_set("S", self.storage_df, name_col="Storage")
        self.set_idx_set("X", self.X2E_df, name_col="X2E")

        order = [
            'nhrs', 'intv', 'r',
            'ep', 'ebp', 'esp',
            'emxcap', 'e2x', 'einv', 'eomc',
            'smxcap', 'e2s', 'mxsin', 'mxsout', 'sini', 'xch', 'xdis', 'xres', 'sinv', 'somc',
            'xmxcap', 'x2e', 'xinv', 'xomc',
            'inflow',
        ]

        base = []
        for key in order:
            base.append(blocks[key] if key in blocks else '')
            if key == 'r':      # add idx_sets after set R
                base.append(''.join(self.idx_sets))

        ampl_dat = ''.join(base)

        return ampl_dat

    # 9) write ample format parameters to ampl file
    def write_to_ampl(self):
        print(f'\nData write to ".dat" file.')
        ampl_dat = self.to_ampl()
        dat_file = self.ampl_file
        with open(dat_file, 'w') as f:
            f.write(f'# Data for Matouqin sms.py\n')
            f.write(ampl_dat)
        print(f'Data write completed. Stored in: {dat_file}.')

    # 2. Process ampl format file
    # modify periods, select a certain amount periods and match the corresponding data
    # 1) deal with price
    @staticmethod
    def handle_ePrice(line, t_old, t_new):  # redefine constant ePrice
        parts = line.split()
        val = float(parts[0])
        val_new = val / t_old * t_new  # cost related to the n_periods
        new_line = f'{val_new:.2}\n'
        return new_line

    # 2) deal with costs, sInv and sOmc
    def handle_cost(self, line, t_old, t_new):  # redefine sInv and sOmc
        parts = line.split()
        item = f'{parts[0]} {parts[1]}'
        val = float(parts[-1])
        val_new = val / t_old * self.intv * t_new  # cost related to the n_periods
        val_new = round(val_new, 2)
        new_line = f'{item} {val_new}\n'
        return new_line

    # 3) rewrite data with corresponding periods
    def set_dat(self, t_new):
        print(f'Generate data slices {t_new} from current data file {self.f_data}.')

        # check file type
        if self.data_type != '.dat':
            raise ValueError(f'Input data file must be .dat, got {self.data_type or "(no suffix)"}.')

        # read the data file
        with (open(self.f_data, 'r') as data_base):
            lines = data_base.readlines()

            for i, line in enumerate(lines):
                if line.strip().startswith('param intv :='):
                    self.intv = float(lines[i + 1].strip().rstrip(';'))
                elif line.strip().startswith('param nHrs :='):
                    self.nHrs = float(lines[i + 1].strip().rstrip(';'))

                if self.intv is not None and self.nHrs is not None:
                    break

            t_old = self.nHrs

            for i, line in enumerate(lines):
                if line.strip().startswith('param nHrs :='):
                    self.nHrs = float(lines[i + 1].strip().rstrip(';'))
                    break

            new_lines = []
            # redefine params
            params = ['nHrs', 'inflow', 'pOut', 'ePrice', 'eInv', 'eOMC', 'sInv', 'sOMC', 'xInv', 'xOMC']
            param_started = False
            param_count = 0  # counting time periods in inflow

            # Determine t_new: (start, end) or the number of periods
            if isinstance(t_new, (tuple, list)):
                if len(t_new) == 2:
                    st_idx, end_idx = int(t_new[0]), int(t_new[1])       # e.g., (720,1440)
                    if end_idx < st_idx or st_idx < 1:
                        raise ValueError(f'Invalid t_new, expected (start>=0, end>=start).')
                    mode = True
                    t_n = end_idx - st_idx + 1
                else:
                    raise ValueError(f'Invalid t_new, expected (start>=0, end>=start).')
            elif isinstance(t_new, int) and t_new > 0:
                mode = False
                t_n = t_new
            else:
                raise ValueError(f'Invalid t_new, expected (start>=0, end>=start) or int.')

            for line in lines:
                if any(f'param {p} :=' in line for p in params):
                    param = line.split()[1].strip(' :=')    # get param name
                    new_lines.append(line)  # add current line to new lines
                    param_started = True    # begin processing parameter
                    param_count = 0         # begin recording data, rows of params
                elif param_started:
                    if line.strip() == ';':
                        if param == 'inflow' and mode:
                            if param_count < st_idx or param_count < end_idx:
                                raise ValueError(f'{t_new} is exceeded the number of time periods ({t_old}) in inflow')
                        elif param == 'pOut' and mode:
                            if param_count < st_idx or param_count < end_idx:
                                raise ValueError(f'{t_new} is exceeded the number of time periods ({t_old}) in inflow')
                        elif param in ('inflow', 'pOut'):
                            if param_count < t_n:
                                raise ValueError(f'{t_new} is exceeded the number of time periods ({t_old}) in inflow')
                        new_lines.append(';\n')  # end recording inflow by hand
                        param_started = False    # end param processing
                    else:
                        processed_line = None
                        if param == 'nHrs':         # redefine nHrs
                            processed_line = f'{t_n}\n'
                        elif param in ('inflow', 'pOut'):     # redefine inflow and pOut
                            param_count += 1
                            if mode:
                                if st_idx <= param_count <= end_idx:
                                    parts = line.strip().split()
                                    val = parts[-1]
                                    new_idx = param_count - st_idx
                                    processed_line = f'{new_idx} {val}\n'
                                else:
                                    continue
                            else:
                                if param_count <= t_n:
                                    processed_line = line
                                else:
                                    continue
                        elif param == 'ePrice':       # redefine ePrice
                            processed_line = self.handle_ePrice(line, t_old, t_n)
                        elif param == 'eInv':         # redefine sInv
                            processed_line = self.handle_cost(line, t_old, t_n)
                        elif param == 'eOMC':       # redefine sOmc
                            processed_line = self.handle_cost(line, t_old, t_n)
                        elif param == 'sInv':         # redefine sInv
                            processed_line = self.handle_cost(line, t_old, t_n)
                        elif param == 'sOMC':       # redefine sOmc
                            processed_line = self.handle_cost(line, t_old, t_n)
                        elif param == 'xInv':         # redefine sInv
                            processed_line = self.handle_cost(line, t_old, t_n)
                        elif param == 'xOMC':       # redefine sOmc
                            processed_line = self.handle_cost(line, t_old, t_n)

                        if processed_line:
                            new_lines.append(processed_line)
                        else:
                            # exceed the specified time periods
                            new_lines.append(';')
                            param_started = False
                else:
                    new_lines.append(line)

        with open(self.ampl_file, 'w', encoding='utf-8') as dat_file:       # write data to new ample formate file
            dat_file.writelines(new_lines)
        print(f'New data version has been stored in {self.ampl_file}.')

    # 3. Store all parameters to Excel file
    def write_to_excel(self):
        temp_dir = self.data_dir / 'Temp'
        f_name = self.ampl_file.stem        # get the file name without suffix
        print(f_name)
        f_xlsx = temp_dir / f'{f_name}_all_params.xlsx'

        with pd.ExcelWriter(f_xlsx, engine='openpyxl') as writer:
            self.cf_df.to_excel(writer, sheet_name='cf', index=False)
            self.VRE_df.to_excel(writer, sheet_name='VRE', index=False)
            self.inflow.to_excel(writer, sheet_name='inflow', index=True)
            self.time_df.to_excel(writer, sheet_name='time', index=False)
            self.prices_df.to_excel(writer, sheet_name='prices', index=False)
            self.E2X_df.to_excel(writer, sheet_name='E2X', index=False)
            self.storage_df.to_excel(writer, sheet_name='S', index=False)
            self.X2E_df.to_excel(writer, sheet_name='X2E', index=False)

        print(f'All parameters are stored in: {f_xlsx}')

    # 4. Add random pOut to ampl format file
    def upd_pOut(self, mode, file_pout=None):
        if self.data_type != '.dat':
            raise ValueError(f'Data file must be .dat, got {self.data_type or "(no suffix)"}.')

        with open(self.f_data, 'r') as f_dat:
            content = f_dat.read()

        # get numbers of time periods
        m = re.search(
            r'(?i)\bparam\s+nHrs\b\s*:=\s*(\d+)\s*;',
            content
        )
        if not m:
            raise ValueError(f'param nHrs not found in {self.f_data}')

        self.nHrs = int(m.group(1))

        # find param pOut := ... ;
        pattern = r'(?i)(param\s+pOut\s*:=\s*.*?;)'
        match = re.search(pattern, content, re.DOTALL)

        # create new pOut
        new_pout = [f'param pOut :=']
        if mode == 'random':
            for i in range(self.nHrs):
                value = round(random.uniform(0.8, 1.2), 2)
                new_pout.append(f'{i} {value}')
            new_pout.append(';')
            new_pout_str = '\n'.join(new_pout)
        elif mode == 'file':
            self.pOut = pd.read_csv(file_pout, index_col=0)
            p = self.pOut['pOut']
            print(self.pOut.head())
            for t, value in p.items():
                new_pout.append(f'{t} {value:.2f}')
            new_pout.append(';')
            new_pout_str = '\n'.join(new_pout)
        else:
            raise ValueError(f'Mode should be "random" or "file".')

        if match:
            # replace old pOut
            content = re.sub(pattern, new_pout_str, content, flags=re.DOTALL)
            print(f'Param pOut has been updated by new a distribution.')
        else:
            # add pOut after inflow
            place = r'(?i)(param\s+inflow\s*:=\s*.*?;)'
            pmatch = re.search(place, content, re.DOTALL)
            if pmatch:
                insert_pos = pmatch.end()
                content = content[:insert_pos] + '\n\n' + new_pout_str + content[insert_pos:]
                print('Parameter pOut has been inserted after param inflow.')
            else:
                content += new_pout_str
                print('Parameter pOut has been added to the end.')

        with open(self.ampl_file, 'w') as f:
            f.write(content)

        print(f'Param pOut has been updated after the inflow in {self.ampl_file}.')


# ------------------------------------------------------------------------------------------------
if __name__ == '__main__':
    path = Path('.')
    dat_dir = path / 'Local' / 'Data'       # Dara dir

    # preparing data in ampl format (.dat), input f_orig should be placed in 'dat_dir/Raw'
    f_orig = f'sms3_c1.xlsx'        # input Excel file
    # f_orig = ['cf', 'VRE', 'time', 'prices', 'E2X', 'storage', 'X2E']     # input csv filenames, 7 files
    # f_orig = f'sms3_c1.dat'  # input .dat file
    # f_orig = f'sms3_pOut.dat'  # input .dat file
    f_new = dat_dir / 'sms3_pOut.dat'   # ampl format file, store generated/updated model parameters
    # f_new = dat_dir / sms3_c1_cut.dat'
    f_cf_new = dat_dir / 'Raw' / 'cf_all.csv'   # new cf file
    f_pout = dat_dir / 'Raw' / 'pout.csv'       # pOut file

    # check if f_new exist, if not, create a new one
    f_new.parent.mkdir(parents=True, exist_ok=True)
    try:
        # mode 'x', create file：if file exist, get FileExistsError, will not overwrite
        with f_new.open('x', encoding='utf-8') as fn:
            fn.write(f'# Empty data file for parameters in Matouqin model sms.py')
        print(f'New AMPL format data file {f_new} has been created.')
    except FileExistsError:
        print(f'New AMPL format data file {f_new} exists, overwrite.')

    # data processing (base data in Excel): select the n`umber of hours the model runs by changing n_periods
    par = Params(dat_dir, f_orig, f_new)        # read data from files
    # par.upd_cf(f_cf_new, 2024)             # update parameter cf, 2020-2024
    par.process_data()                # prepare all parameters used in sms
    par.print_df()                    # print parameters

    # for Excel users
    # par.xlsx_to_csv()               # generate data in csv format
    # par.write_to_excel()            # store all parameters to Excel file, including params not used in sms.py

    # generate data slices
    # par.set_dat(5)                  # generate a cut of t-indexed data and reset others, e.g., first 5 periods
    # par.set_dat((6, 10))            # generate a cut of t-indexed data and reset others, e.g., t=(6,10), 5 periods

    # add/update outflow pattern 'pOut', random or from file.
    # par.upd_pOut('random', file_pout=f_pout)

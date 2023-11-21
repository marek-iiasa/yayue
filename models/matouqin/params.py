"""
Manage parameters of the model defined in model.py
"""


class Params:
    def __init__(self):
        # todo: define the needed data structures, e.g., dict, lists, df (DataFrames)
        self.ver = '0.1'    # version of data
        self.cat = {}   # catalog of data items (might be useful, but you may prefer other solutions)

        self.price = {'ePrice': self.ePrice, 'eBprice': self.eBprice}   # price of something
        self.inDf = None    # DataFrame with data from excel file
        self.eff = {'h2Res': self.h2Res}    # coefficients of several processes, the dict-key would help to used them
        self.cvf = {'eh2': self.eh2, 'eph2': self.eph2, 'h2e': self.h2e}    # conversion factors of several processes.
        self.eltro = {'sCap': self.sCap} # parameters of electrolyzers.
        self.htank ={'sCap': self.sCap, 'hMin': self.hMin, 'mxIn': self.mxIn, 'mxOut': self.mxOut} # parameters of hydrogen tanks.
        self.fuelcell = {}  # parameters of fuel cells.
        # self.df_inp()   # read excel data into data frame
        self.set_eff()  # define efficiencies
        print(f'el2h efficiency: {self.eff.get("el2h")}')

    # todo: add functions to defining the needed params and put them into the above (to be created) elements

    def df_inp(self):   # read data from excel
        assert self.inDf is not None, f'reading excel not implemented yet df_inp = {self.df_inp}.'

    def prices(self):
        self.ePrice = 0.8   # contract price.
        self.penalty = 2    # penalty factor, used to define the price for buying the electricity.
        self.eBprice = self.penalty * self.ePrice

    def unit_conversion(self):  # set unit conversion factor.
        self.cH2 = 0.0899   # the conversion factor between hydrogen gas volume and weight, unit in kg/m3.
        self.cEle = 1000    # the conversion factor between MW and kW.

    def set_h2Ratio(self):  # the ratio of hydrogen and electricity consumed, to produce the same amount of heat, unit in MWh/kg.
        self.hCal = 1.42351e5  # the calorific value of hydrogen, unit in kJ/kg.
        self.eCal = 3.6e3    # the calorific value of electricity, unit in kJ/kWh.
        self.h2Ratio = self.hCal/self.eCal * 1/self.cEle    # unit in MWh/kg

    def set_eff(self):
        self.eff.update({'el2h': 20})
    def set_Invcost(self):
        self.sInvcost =


    def

    # another comment (not in seen in to_do)

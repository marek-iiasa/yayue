"""
Manage parameters of the model defined in model.py
"""


class Params:
    def __init__(self):
        # todo: define the needed data structures, e.g., dict, lists, df (DataFrames)
        self.ver = '0.1'  # version of data
        self.cat = {}     # catalog of data items (might be useful, but you may prefer other solutions)
        self.pPrice = None  # price of something
        self.inDf = None    # DataFrame with data from excel file
        self.eff = {}    # efficiences of several processes, the dict-key would help to used them

        # self.df_inp()   # read excel data into data frame
        self.set_eff()  # define efficiencies
        print(f'el2h efficiency: {self.eff.get("el2h")}')

    # todo: add functions to defining the needed params and put them into the above (to be created) elements

    def df_inp(self):   # read data from excel
        assert self.inDf is not None, f'reading excel not implemented yet df_inp = {self.df_inp}.'

    def prices(self):
        self.pPrice = 20.

    def set_eff(self):
        self.eff.update({'el2h': 20})

    # another comment (not in seen in to_do)

"""
Manage parameters of the model defined in sms.py
"""


class Params:
    def __init__(self):
        # todo: define the needed data structures, e.g., dict, lists, df (DataFrames)
        # todo: check the define of parameter which has index

        self.ver = '0.1'    # version of data

        # parameters used to calculate the parameters of the model defined in sms.py
        # set
        self.G = set()  # set of installed renewable energy generation technologies
        self.Se = set() # set of electrolyzers
        self.Sh = set() # set of hydrogen tanks
        self.Sc = set() # set of fuel cell

        # initial parameters for calculating
        # self.cat = {}  # catalog of data items (might be useful, but you may prefer other solutions)
        self.S = self.Se | self.Sh | self.Sc # a composed set of storage devices
        self.periods = {'nHrs': self.nHrs, 'Hrs': self.Hrs} # numbers of decision periods and the duration time between each decision period.
        self.con = {'cH2':self.cH2, 'cEle':self.cEle}   # conversion factor between different unit of hydrogen and electricity
        self.gCap = {'gCap': self.gCap, 'gNum': self.gNum, 'gCapf': self.gCapf}  # parameter related to renewable energy generation
        # unit capacity of power generating sets, number of sets and capacity factor.
        self.cInv = {'sInvcost': self.sInvCost, 'ydis': self.ydis, 'n': self.n, 'invShare': self.ann} # parameter related to calculate annual investment cost
        self.eConsume = {'toHprd': self.toHprd, 'toHstr': self.toHstr}  # electricity consumption factor during hydrogen production and storage
        self.vCal = {'hCal': self.hCal, 'eCal': self.eCal}  # calorific value of hydrogen and electricity
        self.eff_init = {'ec': self.ec, 'H2Loss': self.h2Loss}  # efficiency of fuel cell and hydrogen
        self.price = {'ePrice': self.ePrice, 'penalty': self.penalty}  # parameters related to electricity price

        # parameters defined in the sms.py
        # self.cat = {}   # catalog of data items (might be useful, but you may prefer other solutions)

        self.inflow =[] # amount of electricity incoming to the site
        self.eltro = [self.sCap, self.eh2] # parameters of electrolyzers
        self.htank = [self.sCap, self.hMxIn, self.hMxOut, self.hmi, self.h2Res, self.eph2]  # parameters of hydrogen tanks
        self.cell = [self.sCap, self.h2e] # parameters of fuel cells
        self.time = {'Hrs': self.Hrs, 'nHrs': self.nHrs, 'ann': self.ann}   # time-related parameters
        self.price = {'ePrice': self.ePrice, 'eBPrice': self.eBprice}   # price
        self.cost = {'overCost': self.overCost, 'sInv': self.sInv, 'sOmc': self.sOmc}   # cost

        # self.inDf = None    # DataFrame with data from excel file
        # self.df_inp()   # read excel data into data frame
        # print(f'cost: {self.cost.get("overCost")}')

    # todo: add functions to defining the needed params and put them into the above (to be created) elements
    # todo: check [inflow,

    #def df_inp(self):   # read data from excel
    #    assert self.inDf is not None, f'reading excel not implemented yet df_inp = {self.df_inp}.'

    # defining the initial parameters
    def periods(self):
        self.nHrs = 8760    # the number of hours in a year
        self.Hrs = 1        # the duration time between each decision period (hour)

    def con(self):
        self.cH2 = 0.0899       # conversion factor between hydrogen gas volume and weight, [kg/m3]
        self.cEle = 1000        # conversion factor between MW and kW

    def gCap(self):
        self.gCap = 100     # unit capacity of the renewable power generating sets
        self.gNum = 10      # number of power generating sets
        self.gCapf = []      # capacity factor of the power generating set

    def cInv(self):
        self.sInvCost = 200     # total investment cost of storage devices, million yuan
        self.ydis = 0.05      # yearly discount factor
        self.n = 20     # lifetime of storage devices


    def eConsume(self):
        self.toHprd = 4.5       # electricity consumption per unit of hydrogen production, [kwh/m3]
        self.toHstr = 1     # electricity consumption to make high-pressure per unit of hydrogen, [kwh/m3]

    def vCal(self):
        self.hCal = 1.42351e5       # calorific value of hydrogen, [kJ/kg]
        self.eCal = 3.6e3       # calorific value of electricity, [kJ/kg]

    def eff_init(self):
        self.ec = 0.7       # efficiency of fuel cell
        self.h2Loss = 0     # self-loss efficiency of hydrogen tank

    def prices(self):
        self.ePrice = 0.8   # contract price.
        self.penalty = 2    # penalty factor, used to define the price for buying the electricity.

    # functions of parameters defined in the sms.py
    def inflow(self):
        self.inflow = []

    def eltro(self):
        self.sCap = 5
        self.eh2 = 1/self.toHprd * self.cEle * self.cH2

    def htank(self):
        self.sCap = 50
        self.hMxIn = 5
        self.hMxOut = 5
        self.hmi = 5
        self.h2Res = 1 - self.h2Loss
        self.eph2 = self.cEle * self.toHstr
    def cell(self):
        self.sCap = 50
        self.h2Ratio = self.hCal/self.eCal * 1/self.cEle
        self.h2e = self.h2Ratio * self.ec

    def time(self):
        self.nHrs = 8760    # the number of hours in a year
        self.Hrs = 1        # the duration time between each decision period (hour)
        self.ann = ((1 + self.ydis) ** self.n * self.ydis) / ((1 + self.ydis) ** self.n - 1)  # annual factor

    def price(self):
        self.ePrice = 0.8       # contract price
        self.eBprice = self.penalty * self.ePrice        # purchase price of buying electricity

    def cost(self):
        self.overCost = 1
        self.sInv = self.ann * self.sInvCost
        self.sOmc = 5
    # def set_eff(self):
    #    self.eff.update({'el2h': 20})

    # another comment (not in seen in to_do)

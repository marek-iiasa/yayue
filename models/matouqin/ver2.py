"""
sms(): returns the Symbolic model specification (SMS), i.e., the Abstract Model of the Matouqin model.
All functions used in the m model are defined before mk_sms() to avoid warnings "m shadows name from outer scope".
Mtq version 2.0 classifies energy  only supports configuration decisions for two ESSs: Battery and Hydrogen.
The two ESSs have their own energy flow paths.
Version 1.0 is a prototype of the Matouqin model versions.
"""

import pyomo.environ as pe      # more robust than using import *


class Storage:
    def __init__(self, model):
        self.m = model

    def set_ess(self):
        if self.m.Ri and self.m.Rm:
            print(f'Storage categories correct.')
        else:
            print(f'Check storage category settings')

        if len(self.m.Ri) and not len(self.m.Rm):
            print(f'Add single energy storage system (ESS).')
            self.RiCstrs()
        elif not len(self.m.Ri) and len(self.m.Rm):
            print(f'Add multi-component energy storage system (ESS).')
            self.RmCstrs()
        elif len(self.m.Ri) and len(self.m.Rm):
            print(f'Add hybrid energy storage system (ESS).')
            self.RCstrs()
        else:
            print(f'Check storage category input.')

    # single component ESS constraints
    def RiCstrs(self):
        @self.m.Constraint(self.m.Ri, self.m.T)              # total electricity to each storage system
        def eInsBalRi(mx, r, t):
            return mx.eIns[r, t] == sum(mx.sInb[r, s, t] for (r, s) in mx.Pb)

        @self.m.Constraint(self.m.Pb, self.m.T)     # the actual amount of electricity will be stored
        def eIneBal(mx, r, s, t):
            return mx.eIne[r, s, t] == mx.e2eIn[r, s] * mx.sInb[r, s, t]

        @self.m.Constraint(self.m.Pb, self.m.T)     # amount of energy in s-th device
        def eVolBal(mx, r, s, t):
            return mx.eVol[r, s, t] == mx.eRes[r, s] * mx.eVol[r, s, (t-1)] + mx.eIne[r, s, t] - mx.eOute[r, s, t]

        @self.m.Constraint(self.m.Pb)             # Amount of electricity at the first period
        def eVolSt(mx, r, s):
            return mx.eVol[r, s, -1] == mx.eInit[r, s]

        @self.m.Constraint(self.m.Pb)              # Amount of electricity at the last period
        def eVolEnd(mx, r, s):
            return mx.eVol[r, s, mx.nHrs_] == mx.eInit[r, s]

        @self.m.Constraint(self.m.Pb, self.m.T)      # Amount of ele in s-th device
        def eVolLow(mx, r, s, t):
            return mx.eVol[r, s, t] >= 0

        @self.m.Constraint(self.m.Pb, self.m.T)      # Amount of ele in s-th device
        def eVolUp(mx, r, s, t):
            return mx.eVol[r, s, t] <= mx.sCap[r, s]

        @self.m.Constraint(self.m.Pb, self.m.T)      # Maximum inflow to s-th device
        def eIneUp(mx, r, s, t):
            return mx.sInb[r, s, t] <= mx.eMxIn[r, s]

        @self.m.Constraint(self.m.Pb, self.m.T)      # Usable outflow from s-th device
        def sOutbBal(mx, r, s, t):
            return mx.sOutb[r, s, t] <= mx.e2eOut[r, s] * mx.eOute[r, s, t]

        @self.m.Constraint(self.m.Pb, self.m.T)      # Maximum usable outflow from s-th device
        def sOutbUp(mx, r, s, t):
            return mx.sOutb[r, s, t] <= mx.eMxOut[r, s]

        @self.m.Constraint(self.m.Ri, self.m.T)               # the sum of outflows from the storage system
        def eOutsBalRi(mx, r, t):
            return mx.eOuts[r, t] == sum(mx.sOutb[r, s, t] for (r, s) in mx.Pb)

        # relations defining auxiliary variables
        @self.m.Constraint(self.m.Pb)  # maximum electricity inflow for s-th bidirectional storage device
        def eMxInC(mx, r, s):
            return mx.eMxIn[r, s] == mx.intv * mx.mxeIn[r, s] * mx.sNum[r, s]

        @self.m.Constraint(self.m.Pb)  # maximum electricity outflow form s-th bidirectional storage device
        def eMxOutC(mx, r, s):
            return mx.eMxOut[r, s] == mx.intv * mx.mxeOut[r, s] * mx.sNum[r, s]

        @self.m.Constraint(self.m.Pb)  # initial electricity in s-th bidirectional storage device
        def eInitC(mx, r, s):
            return mx.eInit[r, s] == mx.eini[r, s] * mx.sCap[r, s]

        print(f'Single component EES constraints added.')

    # multi-components ESS constraints
    def RmCstrs(self):
        @self.m.Constraint(self.m.Rm, self.m.T)      # total electricity to each storage system
        def eInsBalRm(mx, r, t):
            return mx.eIns[r, t] == mx.sInc[r, t] + mx.sIna[r, t]

        @self.m.Constraint(self.m.Rm, self.m.T)      # electricity used to convert ec = sum of inflows to ec converters
        def sIncBal(mx, r, t):
            return mx.sInc[r, t] == sum(mx.eInc[r, s, t] for s in mx.Sp if (r, s) in mx.Pp)

        @self.m.Constraint(self.m.Pp, self.m.T)     # all ec converters inflows <= sum of their capacities
        def eIncUp(mx, r, s, t):
            return mx.eInc[r, s, t] <= mx.intv * mx.sCap[r, s]

        @self.m.Constraint(self.m.Pp, self.m.T)     # ec converted from s-th converter
        def ecOutcBal(mx, r, s, t):
            return mx.ecOutc[r, s, t] == mx.e2ec[r, s] * mx.eInc[r, s, t]

        @self.m.Constraint(self.m.Rm, self.m.T)      # the amount of ec produced by all converters
        def ecInBal1(mx, r, t):
            return mx.ecIn[r, t] == sum(mx.ecOutc[r, s, t] for s in mx.Sp if (r, s) in mx.Pp)

        @self.m.Constraint(self.m.Rm, self.m.T)      # produced ec is split between containers
        def ecInBal2(mx, r, t):
            return mx.ecIn[r, t] == sum(mx.ecIns[r, s, t] for s in mx.Sc if (r, s) in mx.Pc)

        @self.m.Constraint(self.m.Rm, self.m.T)      # additional electricity used for storing ec
        def sInaBal(mx, r, t):
            return mx.sIna[r, t] == sum(mx.eSp[r, s] * mx.ecIns[r, s, t] for s in mx.Sc if (r, s) in mx.Pc)

        @self.m.Constraint(self.m.Pc, self.m.T)        # amount of ec in each container type
        def ecVolBal(mx, r, s, t):
            return (mx.ecVol[r, s, t] == mx.ecRes[r, s] * mx.ecVol[r, s, (t - 1)]
                    + mx.ecIns[r, s, t] - mx.ecOuts[r, s, t])

        @self.m.Constraint(self.m.Pc)  # amount of ec at the first period
        def ecVolSt(mx, r, s):
            return mx.ecVol[r, s, -1] == mx.ecInit[r, s]

        @self.m.Constraint(self.m.Pc)  # amount of ec at the last period
        def ecVolEnd(mx, r, s):
            return mx.ecVol[r, s, mx.nHrs_] == mx.ecInit[r, s]

        # @self.m.Constraint(self.m.Rm, self.m.Sc, self.m.T)  # Amount of ec in each container type
        # def ecVolBal(mx, r, s, t):
        #     if t == 0:
        #         return mx.ecVol[r, s, t] == mx.ecInit[r, s] + mx.ecIns[r, s, t] - mx.ecOuts[r, s, t]
        #     else:
        #         return mx.ecVol[r, s, t] == mx.ecRes[r, s] * mx.ecVol[r, s, (t - 1)]
        #         + mx.ecIns[r, s, t] - mx.ecOuts[r, s, t]

        @self.m.Constraint(self.m.Pc, self.m.T)  # lower constraint of ec in containers of each type
        def ecVolLow(mx, r, s, t):
            return mx.ecVol[r, s, t] >= 0

        @self.m.Constraint(self.m.Pc, self.m.T)  # upper constraint of ec in containers of each type
        def ecVolUp(mx, r, s, t):
            return mx.ecVol[r, s, t] <= mx.sCap[r, s]

        @self.m.Constraint(self.m.Pc, self.m.T)     # maximum inflow to containers of each type
        def ecInsUp(mx, r, s, t):
            return mx.ecIns[r, s, t] <= mx.ecMxIn[r, s]

        @self.m.Constraint(self.m.Pc, self.m.T)        # maximum outflow from containers of each type
        def ecOutsUp(mx, r, s, t):
            return mx.ecOuts[r, s, t] <= mx.ecMxOut[r, s]

        @self.m.Constraint(self.m.Rm, self.m.T)      # total ec flow from all containers
        def ecOutBal1(mx, r, t):
            return mx.ecOut[r, t] == sum(mx.ecOuts[r, s, t] for s in mx.Sc if (r, s) in mx.Pc)

        @self.m.Constraint(self.m.Rm, self.m.T)      # total ec flow is split between electricity converters
        def ecOutBal2(mx, r, t):
            return mx.ecOut[r, t] == sum(mx.ecInc[r, s, t] for s in mx.Se if (r, s) in mx.Pe)

        @self.m.Constraint(self.m.Rm, self.m.T)      # the sum of outflows from the storage systems
        def eOutsBalRm(mx, r, t):
            return mx.eOuts[r, t] == mx.sOutc[r, t] + mx.sOuta[r, t]

        @self.m.Constraint(self.m.Rm, self.m.T)        # electricity from all electricity converters
        def sOutcBal(mx, r, t):
            return mx.sOutc[r, t] == sum(mx.eOutc[r, s, t] for s in mx.Se if (r, s) in mx.Pe)

        @self.m.Constraint(self.m.Rm, self.m.T)        # additional electricity from releasing the ec
        def sOutaBal(mx, r, t):
            return mx.sOuta[r, t] == sum(mx.eRp[r, s] * mx.ecOuts[r, s, t] for s in mx.Sc if (r, s) in mx.Pc)

        @self.m.Constraint(self.m.Pe, self.m.T)      # electricity outflow from converter
        def eOutcBal(mx, r, s, t):
            return mx.eOutc[r, s, t] == mx.ec2e[r, s] * mx.ecInc[r, s, t]

        @self.m.Constraint(self.m.Pe, self.m.T)      # upper constraint of electricity outflow from converter
        def eOutcUp(mx, r, s, t):
            return mx.eOutc[r, s, t] <= mx.intv * mx.sCap[r, s]

        # relations defining auxiliary variables
        @self.m.Constraint(self.m.Pc)  # maximum ec inflow of s-th container
        def ecMxInC(mx, r, s):
            return mx.ecMxIn[r, s] == mx.intv * mx.mxecIn[r, s] * mx.sNum[r, s]

        @self.m.Constraint(self.m.Pc)  # maximum ec outflow from s-th container
        def ecMxOutC(mx, r, s):
            return mx.ecMxOut[r, s] == mx.intv * mx.mxecOut[r, s] * mx.sNum[r, s]

        @self.m.Constraint(self.m.Pc)  # initial energy carrier in s-th container
        def ecInitC(mx, r, s):
            return mx.ecInit[r, s] == mx.ecini[r, s] * mx.sCap[r, s]

        print(f'Multi-components EES constraints added.')

    # Hybrid ESS constraints
    def RCstrs(self):
        self.RiCstrs()
        self.RmCstrs()
        print(f'Hybrid ESS constraints added.')


# ----------------------------------------------------------------
# noinspection PyTypeChecker
def mk_sms():      # p: model parameters prepared in the Params class
    m = pe.AbstractModel(name='Matouqin v. 2.0')   # instance of the concrete model
    # print(f'Generating AbstractModel model for parameters (version: {p.ver}')

    # sets
    # noinspection SpellCheckingInspection
    m.Ri = pe.Set()     # set of individual-component energy storage systems (ESSs)
    m.Rm = pe.Set()     # set of multi-component ESSs

    m.Sb = pe.Set()     # set of bidirectional energy storage device (ESD) types
    m.Sp = pe.Set()     # set of energy carrier converters types
    m.Sc = pe.Set()     # set of energy carrier container types
    m.Se = pe.Set()     # set of electricity converter types

    m.Pb = pe.Set(dimen=2)     # set of pairs Ri and Sb
    m.Pp = pe.Set(dimen=2)     # set of pairs Rm and Sp
    m.Pc = pe.Set(dimen=2)     # set of pairs Rm and Sc
    m.Pe = pe.Set(dimen=2)     # set of pairs Rm and Se

    # noinspection ClassSet. The union function works.
    m.R = pe.Set(initialize=m.Ri | m.Rm)                   # set of storage ESS categories
    m.S = pe.Set(initialize=m.Sb | m.Sp | m.Sc | m.Se)     # set of ESD types
    m.P = pe.Set(initialize=m.Pb | m.Pp | m.Pc | m.Pe)     # set of valid pairs (r, s)

    # noinspection typeInspection
    m.nHrs = pe.Param(domain=pe.PositiveIntegers)       # the number of time periods
    m.nHrs_ = pe.Param(initialize=m.nHrs - 1)     # index of the last time periods
    m.T = pe.RangeSet(0, m.nHrs_)       # set of time periods
    m.Th = pe.RangeSet(-1, m.nHrs_)     # set of time periods (including initial state 't = -1')

    # define variables needed for demonstrating decorators
    # 1) decision variables
    # m.sNum = pe.Var(m.P, within=pe.NonNegativeReals)         # number of units of s-th storage device
    # m.sNum = pe.Var(m.P, within=pe.NonNegativeIntegers)      # number of units of s-th storage device
    m.sNum = pe.Var(m.P, within=pe.NonNegativeIntegers, bounds=(0, 500))   # bounds on int vars required by cplex
    m.supply = pe.Var()       # amount of energy committed to be provided in each time period, [MW]

    # 2) control variables
    # split of inflow:
    m.dOut = pe.Var(m.T, within=pe.NonNegativeReals)    # amount of electricity covering the committed supply, [MWh].
    m.sIn = pe.Var(m.T, within=pe.NonNegativeReals)     # electricity inflow redirected to storage, [MWh].
    m.eS = pe.Var(m.T, within=pe.NonNegativeReals)      # electricity surplus, [MWh].

    # inflow and outflow to/from the ESSs
    m.eIns = pe.Var(m.R, m.T, within=pe.NonNegativeReals)       # amount of electricity to each ESS, [MWh].
    m.eOuts = pe.Var(m.R, m.T, within=pe.NonNegativeReals)      # amount of electricity from each ESS, [MWh].

    # flows through the individual-component storage system
    m.sInb = pe.Var(m.Pb, m.T, within=pe.NonNegativeReals)    # electricity towards charging s-th device, [MWh].
    m.eIne = pe.Var(m.Pb, m.T, within=pe.NonNegativeReals)    # actual electricity stored in s-th device, [MWh].
    m.eVol = pe.Var(m.Pb, m.Th, within=pe.NonNegativeReals)   # electricity amount stored in s-th device, [MWh].
    m.eOute = pe.Var(m.Pb, m.T, within=pe.NonNegativeReals)   # electricity from s-th device, [MWh].
    m.sOutb = pe.Var(m.Pb, m.T, within=pe.NonNegativeReals)   # usable electricity out from s-th device, [MWh].

    # flows through the multi-component storage system
    m.sInc = pe.Var(m.Rm, m.T, within=pe.NonNegativeReals)          # electricity to energy carrier converters, [MWh].
    m.sIna = pe.Var(m.Rm, m.T, within=pe.NonNegativeReals)          # additional ele used when stor ec, [MWh].
    m.eInc = pe.Var(m.Pp, m.T, within=pe.NonNegativeReals)    # ele inflow to energy carrier converter, [MWh].
    m.ecOutc = pe.Var(m.Pp, m.T, within=pe.NonNegativeReals)  # energy carrier outflow from converter, [100 kg].
    m.ecIn = pe.Var(m.Rm, m.T, within=pe.NonNegativeReals)          # amount of produced/split energy carrier, [100 kg].
    m.ecIns = pe.Var(m.Pc, m.T, within=pe.NonNegativeReals)   # energy carrier inflow to container, [100 kg].
    m.ecVol = pe.Var(m.Pc, m.Th, within=pe.NonNegativeReals)  # available ec stored in container, [100 kg].
    m.ecOuts = pe.Var(m.Pc, m.T, within=pe.NonNegativeReals)  # ec outflow from container, [100 kg].
    m.ecOut = pe.Var(m.Rm, m.T, within=pe.NonNegativeReals)         # ec from container to ele converter, [100 kg].
    m.ecInc = pe.Var(m.Pe, m.T, within=pe.NonNegativeReals)   # ec inflow to electricity converter, [100 kg].
    m.eOutc = pe.Var(m.Pe, m.T, within=pe.NonNegativeReals)   # ele outflow from electricity converter, [MWh].
    m.sOutc = pe.Var(m.Rm, m.T, within=pe.NonNegativeReals)         # ele from ele converter to meet supply, [MWh].
    m.sOuta = pe.Var(m.Rm, m.T, within=pe.NonNegativeReals)         # additional ele generated when releasing ec, [MWh].

    # component of the supply
    m.sOut = pe.Var(m.T, within=pe.NonNegativeReals)      # electricity from storage to meet supply, [MWh].
    m.eB = pe.Var(m.T, within=pe.NonNegativeReals)        # electricity purchase on the market, [MWh].

    # Outcome variables
    m.income = pe.Var(within=pe.Reals)      # annual income from providing the committed supply.
    m.storCost = pe.Var(within=pe.Reals)    # annual cost of ESS.
    m.invCost = pe.Var(within=pe.Reals)     # annualized investment cost of ESS.
    m.OMC = pe.Var(within=pe.Reals)         # annual operation and maintenance costs of ESS.
    m.balCost = pe.Var(within=pe.Reals)     # annual management cost of electricity surplus and shortage.
    m.splsCost = pe.Var(within=pe.Reals)    # annual electricity surplus cost.
    m.buyCost = pe.Var(within=pe.Reals)     # annual electricity purchase cost.
    m.revenue = pe.Var(within=pe.Reals)     # annual revenue of the system.

    # Auxiliary variables
    m.sCap = pe.Var(m.P, within=pe.NonNegativeReals)       # total capacity of s-th type of storage devices.
    m.eMxIn = pe.Var(m.Pb, within=pe.NonNegativeReals)    # maximum electricity flow into s-th device, [MWh].
    m.eMxOut = pe.Var(m.Pb, within=pe.NonNegativeReals)   # maximum electricity flow from s-th device, [MWh].
    m.eInit = pe.Var(m.Pb, within=pe.NonNegativeReals)    # total amount of initial energy in s-th device, [MWh].
    m.ecMxIn = pe.Var(m.Pc, within=pe.NonNegativeReals)   # maximum energy carrier flow into device, [100 kg].
    m.ecMxOut = pe.Var(m.Pc, within=pe.NonNegativeReals)  # maximum energy carrier flow from device, [100 kg].
    m.ecInit = pe.Var(m.Pc, within=pe.NonNegativeReals)   # total amount of initial ec in container, [100 kg].
    m.eSurplus = pe.Var(within=pe.NonNegativeReals)                     # total amount of electricity surplus, [MWh].
    m.eBought = pe.Var(within=pe.NonNegativeReals)                      # total amount of electricity purchase, [MWh].

    # parameters
    m.intv = pe.Param(domain=pe.NonNegativeReals)                         # interval between two time periods, [hrs].
    m.inflow = pe.Param(m.T, domain=pe.NonNegativeReals)          # amount of electricity incoming to the site.
    m.mxCap = pe.Param(m.R, m.S, domain=pe.NonNegativeReals)      # unit capacity of each storage device, MW or 100 kg.

    m.mxeIn = pe.Param(m.Pb, domain=pe.NonNegativeReals)    # maximum electricity incoming to the device, [MWh].
    m.mxeOut = pe.Param(m.Pb, domain=pe.NonNegativeReals)   # maximum electricity outflow from the device, [MWh].
    m.eini = pe.Param(m.Pb, domain=pe.NonNegativeReals)     # percentage of initial available energy in device.

    m.mxecIn = pe.Param(m.Pc, domain=pe.NonNegativeReals)   # maximum ec incoming to the container, [100kg].
    m.mxecOut = pe.Param(m.Pc, domain=pe.NonNegativeReals)  # maximum ec outflow from the container, [100kg].
    m.ecini = pe.Param(m.Pc, domain=pe.NonNegativeReals)    # percentage of initial ec in device, [100kg].

    m.e2eIn = pe.Param(m.Pb, domain=pe.NonNegativeReals)    # charging efficiency.
    m.e2eOut = pe.Param(m.Pb, domain=pe.NonNegativeReals)   # discharging efficiency.
    m.eRes = pe.Param(m.Pb, domain=pe.NonNegativeReals)     # retention rate.
    m.e2ec = pe.Param(m.Pp, domain=pe.NonNegativeReals)     # converting electricity to ec, [100kg/MWh].
    m.eSp = pe.Param(m.Pc, domain=pe.NonNegativeReals)      # factor of additional ele consumption, [MWh/100kg].
    m.ecRes = pe.Param(m.Pc, domain=pe.NonNegativeReals)    # ec retention rate.
    m.eRp = pe.Param(m.Pc, domain=pe.NonNegativeReals)      # factor of produced ele when releasing, [MWh/100kg].
    m.ec2e = pe.Param(m.Pe, domain=pe.NonNegativeReals)     # converting ec to electricity [MWh/100kg]

    m.ePrice = pe.Param(domain=pe.NonNegativeReals)             # contract price, [k~CNY/MWh (year)].
    m.eBprice = pe.Param(domain=pe.NonNegativeReals)            # electricity purchase price, [k~CNY/MWh].
    m.eSprice = pe.Param(domain=pe.Reals)                       # electricity surplus price, [k~CNY].
    m.sInv = pe.Param(m.R, m.S, domain=pe.NonNegativeReals)  # per unit investment cost of storage, [k~CNY].
    m.sOmc = pe.Param(m.R, m.S, domain=pe.NonNegativeReals)  # per unit operation cost of storage, [k~CNY].

    # inflow relations
    @m.Constraint(m.T)          # energy inflow is divided into 3 energy flows
    def inflowBal(mx, t):
        return mx.inflow[t] == mx.dOut[t] + mx.sIn[t] + mx.eS[t]

    @m.Constraint(m.T)     # total electricity to the storage system is split between different storage systems
    def sInBal(mx, t):
        return mx.sIn[t] == sum(mx.eIns[r, t] for r in mx.R)

    # supply relations
    @m.Constraint(m.T)      # committed supply is composed of three parts: direct, storage, purchase
    def supplyBal(mx, t):
        return mx.supply == mx.dOut[t] + mx.sOut[t] + mx.eB[t]

    @m.Constraint(m.T)      # total electricity from storage system is defined by the sum of outflows from each ESS
    def sOutBal(mx, t):
        return mx.sOut[t] == sum(mx.eOuts[r, t] for r in mx.R)

    # relations defining outcome variables
    @m.Constraint()     # income from supplying
    def incomeC(mx):
        return mx.income == mx.ePrice * mx.supply

    @m.Constraint()     # annual cost of all storage system
    def storCostC(mx):
        return mx.storCost == mx.invCost + mx.OMC

    @m.Constraint()     # annualized investment cost of all storage system
    def invCostC(mx):
        return mx.invCost == sum(mx.sInv[r, s] * mx.sNum[r, s] for (r, s) in mx.P)

    @m.Constraint()     # operation and maintenance cost of all storage system
    def OMCC(mx):
        return mx.OMC == sum(mx.sOmc[r, s] * mx.sNum[r, s] for (r, s) in mx.P)

    @m.Constraint()     # cost of balancing surplus and purchase
    def balCostC(mx):
        return mx.balCost == mx.splsCost + mx.buyCost

    @m.Constraint()     # cost of handling surplus
    def splsCostC(mx):
        return mx.splsCost == mx.eSprice * mx.eSurplus

    @m.Constraint()     # cost of handling purchase
    def buyCostC(mx):
        return mx.buyCost == mx.eBprice * mx.eBought

    @m.Constraint()     # total revenue of the system
    def revenueC(mx):
        return mx.revenue == mx.income - mx.storCost - mx.balCost

    # relations defining auxiliary variables
    @m.Constraint(m.P)  # total capacity of s-type storage device
    def sCapC(mx, r, s):
        return mx.sCap[r, s] == mx.mxCap[r, s] * mx.sNum[r, s]

    @m.Constraint()             # annual amount of electricity surplus
    def eSurplusBal(mx):
        return mx.eSurplus == sum(mx.eS[t] for t in mx.T)

    @m.Constraint()             # annual amount of electricity purchase
    def eBoughtBal(mx):
        return mx.eBought == sum(mx.eB[t] for t in mx.T)

    # objective/goal-function in single-criterion analysis
    @m.Objective(sense=pe.maximize)
    def obj(mx):
        return mx.revenue

    print('mk_sms(): finished')

    return m
    # m.pprint()    # does not work (needs lengths of sets)

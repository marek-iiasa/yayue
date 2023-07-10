import pyomo.environ as pe       # more robust than using import *
from pwl import PWL


class McMod:
    def __init__(self, mc, m1):
        self.mc = mc    # CtrMca class handling MCMA data and process/analysis status
        self.m1 = m1    # instance of the core model (first block of the aggregate model)

        self.cr_names = []   # names of all criteria
        self.var_names = []  # names of m1 variables defining criteria
        for (i, crit) in enumerate(mc.cr):
            self.cr_names.append(mc.cr[i].name)
            self.var_names.append(mc.cr[i].var_name)

    def mc_itr(self):
        m = pe.ConcreteModel('MC_block')   # instance of the MC-part (second block of the aggregate model)
        act_cr = []     # indices of active criteria
        for (i, crit) in enumerate(self.mc.cr):
            if crit.is_active:
                act_cr.append(i)

        print(f'mc_itr(): stage {self.mc.cur_stage}, {len(act_cr)} active criteria.')

        m1_vars = self.m1.component_map(ctype=pe.Var)  # all variables of the m1 (core model)
        # m.af = pe.Var(domain=pe.Reals, doc='AF')      # pe.Reals gives warning
        m.af = pe.Var(doc='AF')  # Achievement Function (AF), to be maximized  (af = caf_min + caf_reg)

        if self.mc.cur_stage == 1:   # utopia component, selfish optimization
            if len(act_cr) != 1:  # only one criterion active for utopia calculation
                raise Exception(f'mc_itr(): computation of utopia component: {len(act_cr)} active criteria '
                                f'instead of one.')
            # special case, only one m1 variable used and linked with the AF variable
            id_cr = act_cr[0]   # index of the only active criterion
            var_name = self.var_names[id_cr]    # name of m1-variable representing the active criterion
            m1_var = m1_vars[var_name]  # object of core model var. named m1.var_name
            mult = self.mc.cr[id_cr].mult   # multiplier (1 or -1, for max/min criteria, respectively)
            # print(f'{var_name=}, {m1_var=}, {m1_var.name=}, {mult=}')
            # m.afC = pe.Constraint(expr=(m.af == mult * m1_var))  # constraint linking the m1 and m (MC-part) submodels
            # m.goal = pe.Objective(expr=m.af, sense=pe.maximize)

            @m.Constraint()
            def afDef(mx):
                return mx.af == mult * m1_var  # constraint linking the m1 and m (MC-part) submodels

            @m.Objective(sense=pe.maximize)
            def goal(mx):
                return mx.af
            m.goal.activate()  # only mc_block objective active, m1_block obj. deactivated in driver()
            print(f'\nmc_itr(): "{m.name}" for computing utopia of criterion "{self.cr_names[id_cr]}" '
                  f'defined by core_model variable "{var_name}" generated.')
            # m.pprint()
            return m

        # define variables needed for all stages but utopia
        # mc_block with mc_core linking variables
        m.C = pe.RangeSet(0, self.mc.n_crit - 1)   # set of all criteria indices
        m.A = pe.Set(initialize=act_cr)   # set of active criteria indices
        m.x = pe.Var(m.C)    # m.variables linked to the corresponding m1_var
        m.m1_cr_vars = []     # variables (objects) of m1 defining criteria
        for crit in self.mc.cr:
            var_name = crit.var_name
            m1_var = m1_vars[var_name]  # object of core model var. named m1.var_name
            m.m1_cr_vars.append(m1_var)

        @m.Constraint(m.C)
        def xLink(mx, ii):  # link the corresponding m1 and mc_core variables
            return mx.x[ii] == mx.m1_cr_vars[ii]
        # def link_rule(m, i):  # traditional (without decorations) constraint using a rule
        #     return m.x[i] == m.m1_cr_vars[i]
        # m.xLink = pe.Constraint(m.C, rule=link_rule)

        # AF and m1_vars defined above
        m.caf = pe.Var(m.C)    # CAF (value of criterion/component achievement function, i.e., PWL(cr[m1_var])
        m.cafMin = pe.Var()     # min of CAFs
        m.cafReg = pe.Var()     # regularizing term (scaled sum of all CAFs)

        # generate and store params [a, b] of all segments of PWL function y = ax + b, for each criterion
        pwls = []
        for (i, crit) in enumerate(self.mc.cr):
            pwl = PWL(self.mc, i)   # PWL of i-th criterion
            ab = pwl.segments()     # list of [a, b] params defining line y = ax + b
            pwls.append(ab)
            n_seg = len(ab)
            print(f'PWL of {i}-th crit. {crit.name}: {n_seg} segments, each defined by [a, b] of '
                  f'y = ax + b: {ab = }.')
        print(f'\nParams of segments defining each PWL:')
        for (i, ab) in enumerate(pwls):
            print(f'{i = }: {ab = }')

        print(f'\nGenerating constraints defining each of the CAF[i].')

        # generate constraints for each CAF
        @m.Constraint(m.C)
        # todo: the current version processes only the first (middle) segment; other segments, if any, are ignored
        def cafD(mx, ii):
            # i_caf = mx.caf[i]    # CAF of the current criterion
            # i_x = mx.x[i]    # x of the current criterion
            abx = pwls[ii][0]   # [a, b] of 0-th segment of i-th PWL
            # print(f'{ii}-th criterion:')
            print(f'PWL of {ii}-th criterion has {len(pwls[ii])} segments: {pwls[ii] = }')
            # print(f'mid-segment: {abx = }')
            print(f'a = {abx[0]:.2e}, b = {abx[1]:.2e}')
            # print('here')
            return mx.caf[ii] - abx[0] * mx.x[ii] <= abx[1]

        # print('\nMC_block:')
        # m.pprint()
        # print(f'here2')

        '''
        # generate constraints for each CAF
        for (i, crit) in enumerate(self.mc.cr):
            pwl = PWL(self.mc, i)   # PWL of i-th criterion
            ab = pwl.segments()     # list of [a, b] params defining line y = ax + b
            n_seg = len(ab)
            print(f'PWL of {i}-th criterion {crit.name} has {n_seg} segments: {ab}.')
            S = pe.RangeSet(0, n_seg - 1)   # set of segment-indices of the current PWL
            # if i == 0:    # uncomment to run for only second PWL (the second PWL causes error)
            #     continue

            @m.Constraint(S)
            # todo: fix the CAF gen.: the same name of the function aparently connot be reused (e.g., inside a loop)
            def cafD(mx, ss):
                # i_caf = mx.caf[i]    # CAF of the current criterion
                # i_x = mx.x[i]    # x of the current criterion
                # a = ab[ss][0]
                # b = ab[ss][1]
                return mx.caf[i] - ab[ss][0] * mx.x[i] <= ab[ss][1]

            m.pprint()
        '''

        @m.Constraint(m.A)
        # todo: replace m.C by m.A (to be defined as set of active criteria)
        def cafMinD(mx, ii):
            # Todo: exclude inactive criteria
            return mx.cafMin <= mx.caf[ii]

        @m.Constraint()
        def cafRegD(mx):    # to avoid var-shadows warning: use mx instead of m
            return mx.cafReg == sum(mx.caf[ii] for ii in mx.C)

        #  Todo: harmonize epsilon value with the value of CAF(utopia)
        epsilon = 0.001     # epsilon value to be harmonized with CAF(utopia)

        @m.Constraint()
        def afDef(mx):
            return mx.af == mx.cafMin + epsilon / self.mc.n_crit * mx.cafReg

        @m.Objective(sense=pe.maximize)
        def obj(mx):
            return mx.af

        # print('\nMC_block (returned to driver):')
        # m.pprint()

        return m

        # noinspection PyUnreachableCode
        '''
        # self.mc.set_pref()  # set crit attributes (activity, A/R, possibly adjust nadir app.): moved to Mcma class
        if self.mc.cur_stage == 2:  # first stage of nadir approximation
            # todo: set A/R values
            pass
            # raise Exception(f'mc_itr(): handling of stage {self.mc.cur_stage} not implemented yet.')
        elif self.mc.cur_stage == 3:  # second stage of nadir approximation
            raise Exception(f'mc_itr(): handling of stage {self.mc.cur_stage} not implemented yet.')
        elif self.mc.cur_stage == 4:   # Asp/Res based preferences
            raise Exception(f'mc_itr(): handling of stage {self.mc.cur_stage} not implemented yet.')
        elif self.mc.cur_stage > 4:  # should not come here
            raise Exception(f'mc_itr(): handling of stage {self.mc.cur_stage} not implemented yet.')

        # link (through constraints) the corresponding variables of the m1 (core) and m (MC-part) models
        # MC-part variables needed for defining Achievement Function (AF), to be maximized
        # m.af = pe.Var()     # Achievement Function (AF), to be maximized  (af = caf_min + caf_reg) (defined above)

        id_cr = act_cr[0]  # index of the only active criterion
        var_name = self.var_names[id_cr]  # name of m1-variable representing the active criterion
        m1_var = m1_vars[var_name]  # object of core model var. named m1.var_name
        mult = self.mc.cr[id_cr].mult  # multiplier (1 or -1, for max/min criteria, respectively)
        # print(f'{var_name=}, {m1_var=}, {m1_var.name=}, {mult=}')
        m.afC = pe.Constraint(expr=(m.af == mult * m1_var))  # constraint linking the m1 and m (MC-part) submodels
        # m.goal = pe.Objective(expr=m.af, sense=pe.maximize)
        # m.goal.activate()  # objective of m1 block is deactivated
        print(f'\nmc_itr(): concrete model "{m.name}" for computing utopia of criterion "{var_name}" generated.')

        # raise Exception(f'mc_itr(): not implemented yet.')

        # af = caf_min + caf_reg
        # for id_cr in var_names:     # var_names contains list of names of variables representing criteria
        #     m.add_component('caf_' + id_cr, pe.Var()) # CAF: component achievement function of crit. named 'id_cr'
        #     m.add_component('pwl_' + id_cr, pe.Var())  # PWL: of CAF of criterion named 'id' (may not be needed)?
        #
        # if self.mc.cur_stage == 2:  # first stage of nadir approximation
        #     pass
        # return m
        # print('\ncore model display: -----------------------------------------------------------------------------')
        # (populated) variables with bounds, objectives, constraints (with bounds from data but without definitions)
        # m1.display()     # displays only instance (not abstract model)
        # print('end of model display: ------------------------------------------------------------------------\n')
        # m1.inc.display()
        # m1.var_names[0].display() # does not work, maybe a cast could help?
        # xx = var_names[0]
        # print(f'{xx}')
        # m1.xx.display()     # also does not work
    
        # print(f'{m.af.name=}')
        # xx = m.af
        # print(f'{m.af=}')
        # print(f'{xx=}')
        # print(f'{xx.name=}')
        # zz = xx.name
        # print(f'{zz=}')
        # m.var_names[0] = pe.Var()  # does not work
        # var_names.append('x')     # tmp: second variable only needed for testing
    
        # variables defining criteria (to be linked with the corresponding vars of the core model m1)
        # for id in var_names:     # var_names contains list of names of variables to be linked between blocks m and m1
        #     m.add_component(id, pe.Var())
        #     # m.add_component(id, pe.Constraint(expr=(m.id == m1.id)))  # does not work: m.id is str not object
        #     print(f'variable "{id}" defined in the second block.')
        #     # print(f'{m.name=}') # print the block id
        #     # print(f'{m.id=}') # error, Block has no attribute id
        # m.incC = pe.Constraint(expr=(m.inc == 100. * m1.inc))  # linking variables of two blocks
        # print(f'{m.inc.name=}, {m.inc=}')
            '''

    def mc_sol(self, rep_vars=None):   # extract from m1 solution values of all criteria
        # cf regret::report() for extensive processing
        cri_val = {}    # all criteria values in current solution
        m1_vars = self.m1.component_map(ctype=pe.Var)  # all variables of the m1 (core model)
        for (i, var_name) in enumerate(self.var_names):     # loop over m1.vars of all criteria
            m1_var = m1_vars[var_name]
            # val = m1_var.extract_values() # for indexed variables
            val = m1_var.value
            cr_name = self.cr_names[i]
            cri_val.update({cr_name: val})  # add to the dict of crit. values of the current solution
            print(f'Value of variable "{var_name}" defining criterion "{cr_name}" = {val}')
        self.mc.store_sol(cri_val)  # process and store criteria values

        sol_val = {}    # dict with values of variables requested in rep_var
        for var_name in rep_vars:     # loop over m1.vars of all criteria
            m1_var = m1_vars[var_name]
            # todo: indexed variables needs to be detected and handled accrdingly (see regret::report())
            # val = m1_var.extract_values() # for indexed variables
            val = m1_var.value
            sol_val.update({var_name: val})
            # print(f'Value of the report variable {var_name} = {val}')
        print(f'values of selected variables: {sol_val}')
        return sol_val

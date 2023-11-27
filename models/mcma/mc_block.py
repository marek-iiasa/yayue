import pyomo.environ as pe       # more robust than using import *
from pwl import PWL


class McMod:
    """generator of mc-block (abstract model of MC-part) to be integrated with core-model into MMP."""
    def __init__(self, mc, m1):     # ctor only
        self.mc = mc    # CtrMca class handling MCMA data and process/analysis status
        self.m1 = m1    # instance of the core model (first block of the aggregate model)

        self.cr_names = []   # names of all criteria
        self.var_names = []  # names of m1 variables defining criteria
        for (i, crit) in enumerate(mc.cr):
            self.cr_names.append(mc.cr[i].name)
            self.var_names.append(mc.cr[i].var_name)

    def mc_itr(self):
        """sub-model gnerator, called at each itr having preferences defined through criteria attributes."""
        m = pe.ConcreteModel('MC_block')   # instance of the MC-part (second block of the aggregate model)
        act_cr = []     # indices of active criteria
        for (i, cr) in enumerate(self.mc.cr):
            if cr.is_active:
                act_cr.append(i)
        # print(f'mc_itr(): stage {self.mc.cur_stage}, {len(act_cr)} active criteria.')

        m1_vars = self.m1.component_map(ctype=pe.Var)  # all variables of the m1 (core model)
        # m.af = pe.Var(domain=pe.Reals, doc='AF')      # pe.Reals gives warning
        # Achievement Function (AF), maximized; af = caf_min + caf_reg, except of selfish optimizations
        m.af = pe.Var(doc='AF')

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

            @m.Constraint()
            def afDef(mx):  # AF definition; to avoid var-shadows warning: use mx alias of m (also below)
                return mx.af == mult * m1_var  # link the m1-var of core-model with m.af

            @m.Objective(sense=pe.maximize)
            def goal(mx):   # define objective
                return mx.af
            m.goal.activate()  # only mc_block objective active, m1_block obj. deactivated in driver()
            if self.mc.verb > 2:
                print(f'\nmc_itr(): "{m.name}" for computing utopia of criterion "{self.cr_names[id_cr]}" '
                      f'defined by core_model variable "{var_name}" generated.')
            # m.pprint()
            return m

        # define sets and variables needed for all stages but utopia
        m.C = pe.RangeSet(0, self.mc.n_crit - 1)   # set of all criteria indices
        m.A = pe.Set(initialize=act_cr)   # set of active criteria indices (defined above)
        m.x = pe.Var(m.C)    # m.variables linked to the corresponding m1_var
        n_pwls = self.mc.n_crit     # number of CAFs and PWLs
        if self.mc.deg_exp is False:    # fix the vars corresponding the degenerated cube dimension(s)
            for (i, cr) in enumerate(self.mc.cr):
                if cr.is_fixed:
                    n_pwls -= 1
                    assert not cr.is_active, f'Crit. {cr.name} has fixed value; therefore, it must be in_active.'
                    m.x[i].fix(cr.asp)
                    # m.x[i].setlb(cr.asp)
                    # m.x[i].setub(cr.asp)
                    # raise Exception(f'not implemented yet: var[{i}] should be fixed at {cr.asp:.2e}.')
        # m.P = pe.RangeSet(0, n_pwls - 1)   # seq_index of PWLs & m.caf[]
        m.m1_cr_vars = []    # list of variables (objects) of m1 (core model) defining criteria
        for cr in self.mc.cr:     # get m1-vars representing criteria
            var_name = cr.var_name
            m1_var = m1_vars[var_name]  # select from all core-model vars the object named var_name
            m.m1_cr_vars.append(m1_var)

        @m.Constraint(m.C)
        def xLink(mx, ii):  # link the corresponding variables of mc-part and mc_core blocks
            return mx.x[ii] == mx.m1_cr_vars[ii]    # mx: alias of m, ii: index in m.C
        # def link_rule(m, i):  # traditional (without decorations) constraint using a rule
        #     return m.x[i] == m.m1_cr_vars[i]
        # m.xLink = pe.Constraint(m.C, rule=link_rule)

        # remaining variables of mc-block; AF and m1_vars defined above
        m.caf = pe.Var(m.C)    # CAF (value of criterion/component achievement function, i.e., PWL(cr[m_var])
        m.cafMin = pe.Var()     # min of CAFs
        m.cafReg = pe.Var()     # regularizing term (scaled sum of all CAFs)

        # generate and store params [a, b] of all segments of PWL function y = ax + b, for each not-fixed criterion
        pwls = []   # list of PWLs; None is inserted for non-generated PWLs (to provide same indices for CAFs and PWLs)
        segs = []
        var_seq = []    # seq_no of m-var corresponding to the pwl (-1 for undefined PWL)
        for (i, cr) in enumerate(self.mc.cr):
            if not cr.is_fixed:
                pwl = PWL(self.mc, i)   # PWL of i-th criterion
                ab = pwl.segments()     # list of [a, b] params defining line y = ax + b
                pwls.append(ab)
                n_seg = len(ab)     # currently: 1 <= n_seg <= 3
                segs.append(n_seg)  # order of segments: middle (always), optional: above A, below R
                var_seq.append(i)   # indices of vars are the same as of all crit & PWLs
                # print(f'PWL of {i}-th crit. {cr.name}: {n_seg} segments, each defined by [a, b] of '
                #       f'y = ax + b: {ab = }.')
            else:
                pwls.append(None)
                var_seq.append(-1)
                print(f'PWL of crit. {cr.name} CAF not generated (crit. value is fixed)')
        if self.mc.verb > 2:
            print(f'\nParams of s-th segment defining PWL for i-th CAF:')
            for (i, pwl) in enumerate(pwls):
                if pwl is None:
                    print(f'No segments for undefined PWL.')
                else:
                    for (s, ab) in enumerate(pwl):
                        print(f'({i = }, {s = }): a = {ab[0]:.2e}, b = {ab[1]:.2e}')

        # m.S = pe.Set(initialize=segs)   # NOT suitable: 1-dim set stores only unique numbers of segments of each PWL
        # s_pairs = [(0, 1), (1, 1)]  # works for predefined list of pairs: (i, nseq)
        if self.mc.verb > 2:
            print(f'\nGenerating pairs defining two-dimensional set m.S')
        s_pairs = []    # list of pairs: (i, ns), i = index of CAF/PWL, ns = number of segments of the PWL
        for (i, pwl) in enumerate(pwls):
            if pwl is None:
                s_pairs.append((i, -1))  # illegal segment index -1 indicates no segments
                if self.mc.verb > 2:
                    print(f'No segments for undefined PWL.')
            else:
                for (ns, ab) in enumerate(pwl):
                    pair = (i, ns)
                    s_pairs.append(pair)
                    if self.mc.verb > 2:
                        print(f'{pair = }')
        m.S = pe.Set(dimen=2, initialize=s_pairs)   # m.S initialized by list of pairs of indices

        # print(f'\nGenerating constraints for each CAF[i] and segments of its PWL.')
        @m.Constraint(m.S)
        # todo: the below version generates constraints for all segments in all PWLs
        #   more testing is desired
        def cafD(mx, ix, sx):   # is called for each (ix, sx) in m.S; indexes each constraint by (ix, sx)
            if var_seq[ix] >= 0:
                pwlx = pwls[ix]  # pwlx: ix-item from the pwls list of all PWLs
                abx = pwlx[sx]      # params of line defining the sx-th segment:  y = abx[0] * x + abx[1]
                if self.mc.verb > 2:
                    print(f'generating constraint for pair of indices (CAF, segment of its PWL) = ({ix}, {sx}).')
                    print(f'({ix = }, {sx = }): a = {abx[0]:.2e}, b = {abx[1]:.2e}')
                cons_item = mx.caf[ix] <= abx[0] * mx.x[var_seq[ix]] + abx[1]
                return cons_item
            else:   # PWL not generated for fixed criteria; the corresponding caf shall be fixed
                # todo: CAF needs to be defined, but it enters only the reg. term
                return mx.caf[ix] == 0.
                # return pe.Constraint.Skip

        '''
        # the version below also works; it assigns consecutive numbers as the constraint index
        m.cafD = pe.ConstraintList()
        for (ix, sx) in m.S:
            print(f'generating constraint for pair of indices (CAF, segment of its PWL) = ({ix}, {sx}).')
            pwlx = pwls[ix]     # list of PWL segments of ix-th CAF
            abx = pwlx[sx]      # params of line defining the current segment:  y = abx[0] * x + abx[1]
            print(f'({ix = }, {sx = }): a = {abx[0]:.2e}, b = {abx[1]:.2e}')
            m.cafD.add(m.caf[ix] - abx[0] * m.x[ix] <= abx[1])  # caf[i] <= a * x[i] + b
        '''

        # if self.mc.cur_stage == 4:   # neutral solution, PWLs with possibly more than one segment
        #     print('\n---  MC_block:')
        #     m.pprint()
        #     print(f'---  end of specs of the MC_blok.\n')

        @m.Constraint(m.A)
        def cafMinD(mx, ii):    # only active criteria included in the m.cafMin term
            return mx.cafMin <= mx.caf[ii]
            # return pe.Constraint.Skip

        reg_scale = self.mc.epsilon * self.mc.cafAsp / self.mc.n_crit       # scaling coef of regularizing term
        # print(f'----------------------------------------------------- {reg_scale = }')

        @m.Constraint()
        def cafRegD(mx):    # regularizing term
            # todo: correct the summation, if caf[fix_crit] will not be equal to 0.
            return mx.cafReg == reg_scale * sum(mx.caf[ii] for ii in mx.C)

        @m.Constraint()
        def afDef(mx):
            return mx.af == mx.cafMin + mx.cafReg

        @m.Objective(sense=pe.maximize)
        def obj(mx):
            return mx.af

        if self.mc.verb > 2:
            print('\nMC_block (returned to driver):')
            m.pprint()

        return m

        # noinspection PyUnreachableCode
        '''
        # for id_cr in var_names:     # var_names contains list of names of variables representing criteria
        #     m.add_component('caf_' + id_cr, pe.Var()) # CAF: component achievement function of crit. named 'id_cr'
        #     m.add_component('pwl_' + id_cr, pe.Var())  # PWL: of CAF of criterion named 'id' (may not be needed)?
        #
        # variables defining criteria (to be linked with the corresponding vars of the core model m1)
        # for id in var_names:     # var_names contains list of names of variables to be linked between blocks m and m1
        #     m.add_component(id, pe.Var())
        #     # m.add_component(id, pe.Constraint(expr=(m.id == m1.id)))  # does not work: m.id is str not object
        '''

    '''
    # def mc_sol(self, rep_vars=None):
        # cf regret::report() for extensive processing
        moved to Report
        cri_val = {}    # all criteria values in current solution
        m1_vars = self.m1.component_map(ctype=pe.Var)  # all variables of the m1 (core model)
        for (i, var_name) in enumerate(self.var_names):  # extract m1.vars defining criteria
            m1_var = m1_vars[var_name]
            val = m1_var.value
            cr_name = self.cr_names[i]
            cri_val.update({cr_name: val})  # add to the dict of crit. values of the current solution
            # if self.mc.verb > 2:      # printed by Report::add_itr()
            #     print(f'Value of variable "{var_name}" defining criterion "{cr_name}" = {val}')

        # store through updating criteria attributes
        # todo: consider to add to an iter-log criteria values from each iter
        self.mc.store_sol(cri_val)

        # moved to Report
        sol_val = {}    # initialize dict with values of variables requested in rep_var
        # m1_vars = self.m1.component_objects(pe.Var)  # does not work as needed
        m1_vars = self.m1.component_map(ctype=pe.Var)  # all variables of the m1 (core model)
        for var_name in rep_vars:     # loop over m1.vars of all requested var-names
            m1_var = m1_vars[var_name]
            if m1_var is None:
                raise Exception(f'Variable {var_name} is not defined in the core model.')
            # todo: add roundings of values (either here or when df will be created)
            if m1_var.is_indexed():
                val_dict = m1_var.extract_values()  # values returned in dict (indexes as keys)
                sol_val.update({var_name: val_dict})
                # print(f'Values of indexed variable {var_name} = {val_dict}')
            else:
                val = m1_var.value
                sol_val.update({var_name: val})
                # print(f'Value of the report variable {var_name} = {val}')
        
            # the below works but it is rather an ad-hoc fix than a good code
            # xx = pe.value(m1_var)     # gives exception for indexed vars
            # ind = m1_var.index_set().getname()  # works only for indexed vars, raise exception for non-indexed
            ind = None
            # noinspection PyBroadException
            try:
                ind = m1_var.index_set().getname()  # works only for indexed vars, raise exception for non-indexed
            except Exception:
                # e = None
                print(f'{var_name} is not indexed')
            # ind2 = m1_var.get_sets()    # does not work
            # todo: rounding is values should be implemented
            if ind is None:     # not-indexed var
                val = m1_var.value
                sol_val.update({var_name: val})
                print(f'Value of the report variable {var_name} = {val}')
            else:     # indexed var
                val_dict = m1_var.extract_values()  # values returned in dict (indexes as keys)
                sol_val.update({var_name: val_dict})
                print(f'Values of indexed variable {var_name} = {val_dict}')
   '''

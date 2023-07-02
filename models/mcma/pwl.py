"""
Handling of the CAF-PWL
"""


class PWL:  # representation of caf(x) for i-th criterion
    def __init__(self, mc, i):  # cr: specs of a criterion
        self.mc = mc    # CtrMca object
        self.cr = mc.cr[i]
        self.cr_name = self.cr.name
        self.mult = self.cr.mult  # 1 for max-crit, -1 for min.
        self.utopia = self.cr.utopia
        self.asp = self.cr.asp
        self.res = self.cr.res
        self.nadir = self.cr.nadir
        self.vert_x = []    # x-values of vertices
        self.vert_y = []    # y-values of vertices
        print(f"PWL initialized: cr_name = '{self.cr_name}', mult = '{self.mult}', U = '{self.utopia}', "
              "A = '{self.asp}', R = '{self.res}', R = '{self.nadir}'.")

    def pwl_pts(self, i):
        seg_x = []
        seg_y = []
        utopia = self.cr.utopia
        asp = self.cr.asp
        res = self.cr.res
        nadir = self.cr.nadir
        # todo: correct (the ad-hoc set) CAF (y) values for each segment
        # todo: don't generate utopia/nadir points if close to asp/res, respectively
        # Todo: store points in the same sequence for min/max, then reverse the min-lists to them also in inreas. x
        if self.mc.cr[i].mult == 1:  # crit. maximized: x ordered: nadir, res, asp, utopia
            seg_x.append(nadir)
            # seg_x.append(res)
            # seg_x.append(asp)
            # todo: ad-hoc fix to deal with not initiated A/R
            seg_x.append(1.1 * nadir)
            seg_x.append(0.9 * utopia)
            seg_x.append(utopia)
            seg_y.append(-10000.)
            seg_y.append(0.)
            seg_y.append(1000.)
            seg_y.append(1050.)
        if self.mc.cr[i].mult == -1:  # minimized: x ordered: utopia, asp, res, nadir
            seg_x.append(utopia)
            seg_x.append(asp)
            seg_x.append(res)
            seg_x.append(nadir)
            seg_y.append(1050.)
            seg_y.append(1000.)
            seg_y.append(0.)
            seg_y.append(-10000.)
        print(f'PWL points for criterion "{self.mc.cr[i].name}: {utopia=}, {asp=}, {res=}, {nadir=}')
        return seg_x, seg_y

        # noinspection PyUnreachableCode
        '''
                for (i, crit) in enumerate(self.mc.cr):
                    (pwl_x, pwl_y) = self.pwl_pts(i)
                    print(f'{pwl_x = }')
                    print(f'{pwl_y = }')
        
                print(f'\nTesting PWL')
                (pwl_x, pwl_y) = self.pwl_pts(0)
                print(f'{pwl_x = }')
                print(f'{pwl_y = }')
        
                # see the 6.6.1 p.28 for (cryptic) description of parameters of pe.Piecewise()
                # p = pe.Piecewise(...)
        
                import pyomo.core as pcore
                (code, slopes) = pcore.kernel.piecewise_library.util.characterize_function(pwl_x, pwl_y)
                # https://pyomo.readthedocs.io/en/stable/library_reference/kernel/piecewise/util.html
                # codes: 1: affine, 2: convex 3: concave 4: step 5: other
                print(f'\n{code=}, {slopes=}')
        
                import pyomo.kernel as pmo  # more robust than using import *
                # (code, slopes) = pmo.characterize_function(pwl_x, pwl_y)  # does not work
                # (code, slopes) = pmo.piecewise.characterize_function(pwl_x, pwl_y)  # does not work
                # (code, slopes) = pmo.characterize_function(pwl_x, pwl_y)  # neither pmo. nor pe. works
        
                # pmo.piecewise requires pmo vars?
                # x = pmo.Var(bounds=(0., 1000.))
                # x = pmo.Var(bounds=(None, None))
                # m.x = pmo.variable()
                # m.y = pmo.variable()
                m.y = pe.Var()
                m.goal = pe.Objective(expr=m.y, sense=pe.maximize)
                m.goal.activate()  # objective of m1 block is deactivated
                m.p = pmo.piecewise(pwl_x, pwl_y, input=m1_var, output=m.y, repn='cc', bound='eq',
                                    require_bounded_input_variable=False)   # does not work
                print(f'{m.p = }, {type(m.p)}')
                # m.p.display()     # not supported
                # m.p.pprint()     # not supported
                # m.p.validate()    # validation fails: it considers m_var to be unbounded
        
                # id_cr = act_cr[0]  # index of the only active criterion
                # var_name = self.var_names[id_cr]  # name of m1-variable representing the active criterion
                # m1_var = m1_vars[var_name]  # object of core model var. named m1.var_name
                # m.cafMin = pe.Var()     # min of CAFs
                # m.af = pe.Piecewise(pwl_x, pwl_y, pw_repn='CC')
                # m.af = pe.Piecewise(pwl_x, pwl_y, input=m1_var, output=m.cafMin, pw_repn='CC')
                '''

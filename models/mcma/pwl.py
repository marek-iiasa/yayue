"""
Handling of the CAF-PWL
"""


class PWL:  # representation of caf(x)
    def __init__(self, cr):  # cr: specs of a criterion
        self.cr_name = cr.name
        self.mult = cr.mult  # 1 for max-crit, -1 for min.
        self.utopia = cr.utopia
        self.asp = cr.asp
        self.res = cr.res
        self.nadir = cr.nadir
        self.vert_x = []    # x-values of vertices
        self.vert_y = []    # y-values of vertices
        print(f"PWL initialized: cr_name = '{self.cr_name}', mult = '{self.mult}', U = '{self.utopia}', "
              "A = '{self.asp}', R = '{self.res}', R = '{self.nadir}'.")

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

"""
Handling of the CAF-PWL
"""


class PWL:  # representation of caf(x) for i-th criterion
    def __init__(self, mc, i):  # cr: specs of a criterion
        self.mc = mc    # CtrMca object
        self.cr = mc.cr[i]
        self.cr_name = self.cr.name
        self.is_max = self.cr.mult == 1  # 1 for max-crit, -1 for min.
        self.is_asp = self.cr.asp is not None   # Asp. defined?
        self.is_res = self.cr.res is not None   # Res. defined?
        self.is_nadir = self.cr.nadir is not None   # Nadir defined?
        self.vert_x = []    # x-values of vertices
        self.vert_y = []    # y-values of vertices
        print(f"\n----\nPWL initialized: cr_name = '{self.cr_name}', is_max = '{self.is_max}', U = '{self.cr.utopia}', "
              f"A = '{self.cr.asp}', R = '{self.cr.res}', R = '{self.cr.nadir}'.")

        self.set_vert()  # define coordinates of the vertices

    def set_vert(self):  # define coordinates of the vertices
        # todo: move definition of caf_asp to the ctrMc class
        caf_asp = 100.    # temporarily
        assert self.cr.utopia is not None, f'PWL ctor: utopia of criterion "{self.cr_name}" is undefined.'
        assert self.is_res or self.is_nadir, f'Criterion {self.cr_name}: neither reservation nor nadir defined.'
        self.vert_x.append(self.cr.utopia)
        self.vert_y.append(caf_asp)     # the value shall be replaced/ignored, if is_asp == True
        # todo: add skipping "too close" (in terms of x) vertices
        if self.is_asp:
            self.vert_x.append(self.cr.asp)
            self.vert_y.append(caf_asp)
        if self.is_res:
            self.vert_x.append(self.cr.res)
            self.vert_y.append(0)
        if self.is_nadir:
            self.vert_x.append(self.cr.nadir)
            self.vert_y.append(0)   # the value shall be later replaced or ignored
        # print(f'set_vert(): criterion {self.cr_name}: {len(self.vert_x)} vertices defined.')
        print(f'PWL of crit. "{self.cr.name} has {len(self.vert_x)} vertices: x = {self.vert_x}, y = {self.vert_y}')
        # the two assertions below not needed for the above setup
        # assert n_seg > 1, f'PWL of {self.cr_name} has only {len(self.vert_x)} break-point defined.'
        # assert len(self.vert_x) > len(self.vert_y), f'PWL of "{self.cr_name}" criterion has different ' \
        #        f'lenghts of break-points coordinates: x={len(self.vert_x)}, y={len(self.vert_y)}.'

    def segments(self):
        # n_seg = len(self.vert_x) - 1
        ab = []     # list of (a, b) parameters of segments, each defining line: y = ax + b

        # start with the middle segment defined by two points: asp or utopia, and res or nadir
        if self.is_asp:
            x1 = self.vert_x[1]     # utopia not defining mid-segm, if A defined
            y1 = self.vert_y[1]
            x2 = self.vert_x[2]     # second mid-segment point is either R or Nadir (if R not defined)
            y2 = self.vert_y[2]
        else:
            x1 = self.vert_x[0]     # utopia is defines mid-segment, if A iss not defined
            y1 = self.vert_y[0]
            x2 = self.vert_x[1]     # second mid-segment point is either R or Nadir (if R not defined)
            y2 = self.vert_y[1]
        print(f'Middle PWL segment is defined by: ({x1}, {y1}) and ({x2}, {y2}).')
        mid_slope = (x1 - x2) / (y1 - y2)
        b = y1 - mid_slope * x1     # alternatively: b = y2 - slope * x2
        ab.append([mid_slope, b])   # mid-segment is first in the list of segment specs.
        # print(f'ab: {ab}.')
        print(f'parameters of the line y = ax +b: a = {mid_slope:.2e}, {b = :.2e}.')

        # Note: vertices stored in the same way (U, A, R, N) for min/max, this works OK for both types of criteria
        #   because values of both slope and b are invariant in regard of order of points (x1, y1) and (x2, y2)

        assert len(self.vert_x) == 2, f'Processing PWL having {len(self.vert_x)} points not implemented yet.'
        # segments above A (if A defined) and below R (if R defined and not used for mid-segment):
        # defined using: one point and slope; the latter more flat or steep than mid-segment slope, for
        # segments above A and below R, respectively.

        if self.is_asp:  # generate segment above Asp
            # slope: flatter than mid_slop
            # b - defined as above by A point
            pass

        if self.is_res:  # generate segment below Res
            # slope: steeper than mid_slop
            # b - defined as above by R point
            pass

        return ab

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

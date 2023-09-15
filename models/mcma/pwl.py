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
        if 0 < self.mc.verb <= 2:
            print(f"PWL ctor for crit '{self.cr_name}': is_max = {self.is_max}, "
                  f"U = {self.cr.utopia}, A = {self.cr.asp}, R = {self.cr.res}, N = {self.cr.nadir}.")
        elif self.mc.verb > 2:
            print(f"\n----\nPWL ctor for crit '{self.cr_name}': is_max = {self.is_max}, "
                  f"U = {self.cr.utopia}, A = {self.cr.asp}, R = {self.cr.res}, N = {self.cr.nadir}.")
        # todo: cannot format None; either tolerate unformatted or modify to differentiate formatting of elements
        #   f"U = {self.cr.utopia:.2e}, A = {self.cr.asp:.2e}, R = {self.cr.res:.2e}, "
        #   f"N = {self.cr.nadir:.2e}.")
        # at least two points are needed
        # todo: make sure in setting prefence that the below not happen (here any violation causes exception)
        assert self.cr.utopia is not None, f'PWL ctor: utopia of criterion "{self.cr_name}" is undefined.'
        assert self.is_res or self.is_nadir, f'Criterion {self.cr_name}: neither reservation nor nadir defined.'
        # the below relations must hold to conform to the approach assumptions (in particular, concave, increasing CAFs)
        assert self.cr.isBetter(self.cr.utopia, self.cr.asp), f'A {self.cr.asp} must be worse than U {self.cr.utopia}.'
        assert self.cr.isBetter(self.cr.utopia, self.cr.res), f'R {self.cr.res} must be worse than U {self.cr.utopia}.'
        assert self.cr.isBetter(self.cr.utopia, self.cr.nadir), f'N {self.cr.nadir} must be worse than U ' \
            f'{self.cr.utopia}.'
        assert self.cr.isBetter(self.cr.asp, self.cr.res), f'R {self.cr.res} must be worse than A {self.cr.asp}.'
        assert self.cr.isBetter(self.cr.asp, self.cr.nadir), f'N {self.cr.nadir} must be worse than A {self.cr.asp}.'
        assert self.cr.isBetter(self.cr.res, self.cr.nadir), f'N {self.cr.nadir} must be worse than R {self.cr.res}.'
        # the below relations introduced due to both numerical and methodological reasons
        maxVal = max(abs(self.cr.utopia), (abs(self.cr.nadir)))  # value used as basis for min-differences
        minDiff = mc.minDiff * maxVal
        assert self.mc.diffOK(i, self.cr.utopia, self.cr.nadir), f'utopia {self.cr.utopia:.2e} and nadir ' \
            f'{self.cr.nadir:.2e} closer then {minDiff:.1e}. Criterion "{self.cr.name}" unsuitable for MCA.'
        if self.is_asp and not self.mc.diffOK(i, self.cr.utopia, self.cr.asp):
            self.is_asp = False
            print(f'A {self.cr.asp} ignored: it is too close to U {self.cr.utopia}.')
        if self.is_res and self.is_nadir and not self.mc.diffOK(i, self.cr.nadir, self.cr.res):
            self.is_res = False
            print(f'R {self.cr.res} ignored: it is too close to N {self.cr.nadir}.')

        self.set_vert()  # define coordinates of the vertices

    # todo: bug in setting preferences for neutral solution (not all criteria are active)
    def set_vert(self):  # define coordinates of the vertices
        self.vert_x.append(self.cr.utopia)
        self.vert_y.append(self.mc.cafAsp)     # the value shall be replaced/ignored, if is_asp == True
        # points defining "too close" (in terms of x) vertices are removed in the ctor
        if self.is_asp:
            self.vert_x.append(self.cr.asp)
            self.vert_y.append(self.mc.cafAsp)
        if self.is_res:
            self.vert_x.append(self.cr.res)
            self.vert_y.append(0)
        if self.is_nadir:
            self.vert_x.append(self.cr.nadir)
            self.vert_y.append(0)   # the value shall be later replaced or ignored, if is_res == True
        if self.mc.verb > 2:
            print(f"PWL of crit. '{self.cr.name}' has {len(self.vert_x)} vertices: x = {self.vert_x}, "
                  f"y = {self.vert_y}")

    def segments(self):

        # start with the middle segment defined by two points: asp or utopia, and res or nadir
        # Note: vertices stored in the same way (U, A, R, N) for min/max, this works OK for both types of criteria
        #   because values of both slope and b are invariant in regard of order of points (x1, y1) and (x2, y2)
        ab = []     # list of (a, b) parameters of segments, each defining line: y = ax + b
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
        # see: Bronsztejn p. 245
        mid_slope = (y1 - y2) / (x1 - x2)
        b = y1 - mid_slope * x1     # alternatively: b = y2 - slope * x2
        ab.append([mid_slope, b])   # mid-segment is first in the list of segment specs.
        if self.mc.verb > 2:
            print(f'Middle PWL segment is defined by: ({x1:.2e}, {y1:.2e}) and ({x2:.2e}, {y2}:.2e).')
            # print(f'ab: {ab}.')
            print(f'parameters of the mid-segment line y = ax +b: a = {mid_slope:.2e}, b ={b:.2e}.')

        # assert len(self.vert_x) == 2, f'Processing PWL having {len(self.vert_x)} points not implemented yet.'
        # segments above A (if A defined) and below R (if R defined and not used for mid-segment):
        # defined using: one point and slope; the latter more flat or steep than mid-segment slope, for
        # segments above A and below R, respectively.

        if self.is_asp:  # generate segment above Asp
            up_slope = mid_slope / self.mc.slopeR    # flatter than mid_slop
            up_b = y1 - up_slope * x1  # defined as above but by A point
            ab.append([up_slope, up_b])  # up-segment is second in the list of segment specs.
            if self.mc.verb > 2:
                print(f'parameters of the up-segment line y = ax +b: a = {up_slope:.2e}, b ={up_b:.2e}.')

        if self.is_res:  # generate segment below Res
            lo_slope = mid_slope * self.mc.slopeR    # steeper than mid_slop
            lo_b = y2 - lo_slope * x2  # defined as above but by R point
            ab.append([lo_slope, lo_b])  # up-segment is second in the list of segment specs.
            if self.mc.verb > 2:
                print(f'parameters of the lo-segment line y = ax +b: a = {lo_slope:.2e}, b ={lo_b:.2e}.')

        return ab

        # noinspection PyUnreachableCode
        '''
        # alternative/complementary approaches by use of the pe PWL
        # not used but kept for possible future exploration/use
        
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

        '''

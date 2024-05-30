"""
Handling of the CAF-PWL
"""


# noinspection SpellCheckingInspection
# noinspection PySingleQuotedDocstring
class PWL:  # representation of caf(x) for i-th criterion
    def __init__(self, mc, i, verb=-1):
        self.mc = mc    # CtrMca object
        self.cr = mc.cr[i]  # cr: specs of a criterion
        self.cr_name = self.cr.name
        self.is_act = self.cr.is_active
        self.is_fx = self.cr.is_fixed
        self.is_max = self.cr.mult == 1  # 1 for max-crit, -1 for min.
        self.is_asp = self.cr.asp is not None   # Asp. defined?
        self.is_res = self.cr.res is not None   # Res. defined?
        self.is_nadir = self.cr.nadir is not None   # Nadir defined?
        self.verb = verb
        self.asp_val = self.cr.utopia
        self.res_val = self.cr.nadir
        self.up_seg = False   # if True, then generate up-PWL segment
        self.lo_seg = False   # if True, then generate lo-PWL segment
        self.chk_ok = self.chk_param()

    # noinspection PyUnreachableCode
    def chk_param(self):
        if self.verb < 0:
            self.verb = self.mc.verb

        if 0 < self.verb > 1:
            print(f"\n----\nPWL crit '{self.cr_name}': act/fix = {self.is_act}/{self.is_fx}, is_max = {self.is_max}, "
                  f"U = {self.cr.utopia}, A = {self.cr.asp}, R = {self.cr.res}, N = {self.cr.nadir}.")

        # at least two (out of U, A, R, N) are needed
        assert self.cr.utopia is not None, f'PWL ctor: utopia of criterion "{self.cr_name}" is undefined.'
        assert self.is_res or self.is_nadir, f'Criterion {self.cr_name}: neither reservation nor nadir defined.'

        if self.is_nadir:
            maxVal = max(abs(self.cr.utopia), (abs(self.cr.nadir)))  # value used as basis for min-differences
        else:
            maxVal = max(abs(self.cr.utopia), (abs(self.cr.res)))  # value used as basis for min-differences
        minDiff = self.mc.minDiff * maxVal
        # check if U (set in ctor) can be replaced by the provided A
        if self.is_asp:
            if abs(self.cr.utopia - self.cr.asp) > minDiff:
                assert self.cr.pwlBetter(self.cr.utopia, self.cr.asp), f'crit {self.cr_name} (is_max {self.is_max}): '
                f' A {self.cr.asp:.2e} is worse than U {self.cr.utopia:.2e}.'
                self.asp_val = self.cr.asp
                self.up_seg = True
            else:
                if self.verb > 1:
                    print(f'crit {self.cr_name}: ignoring A {self.cr.asp:.2e} as too close to U {self.cr.utopia:.2e}. '
                          f'U used as A.')
                self.is_asp = False     # ignore A, too close to U

        # check if N (set in ctor) can be replaced by the provided R
        if self.is_res and self.is_nadir:
            if abs(self.cr.nadir - self.cr.res) > minDiff:
                assert self.cr.pwlBetter(self.cr.res, self.cr.nadir), f'crit {self.cr_name} (is_max {self.is_max}): '
                f' R {self.cr.res:.2e} is worse than N {self.cr.nadir:.2e}.'
                self.res_val = self.cr.res
                self.lo_seg = True
            else:
                if self.verb > 1:
                    print(f'crit {self.cr_name}: ignoring R {self.cr.res:.2e} as too close to N {self.cr.nadir:.2e}. '
                          f'N used as R.')
                self.is_res = False     # ignore R, too close to N

        # check, if the selected A/R (replaced, if required, by U/N) sufficiently differ
        if abs(self.asp_val - self.res_val) < minDiff:
            print(f'crit {self.cr_name}: the provided A/R pair ({self.asp_val:.2e}, {self.res_val:.2e}) is too close '
                  f'to define a PWL.')
            return False

        return True

    def segments(self):
        # start with the middle segment defined by the pair (self.asp_val, self.res_val) set in chk_param()
        # print(f'mid_slope for crit. "{self.cr_name}": is_asp {self.is_asp}, x1 = {x1:.2e}, x2 = {x2:.2e}')
        ab = []     # list of (a, b, sc) parameters of segments, each defining line: y = ax + b, and core-var scaling
        x1 = self.asp_val   # serves as A
        x2 = self.res_val   # serves as R
        y1 = self.mc.cafAsp  # y(A)
        y2 = 0.  # y(R) = 0.
        y_delta = y1 - y2
        if self.mc.scVar:   # PWL based on scaled core-model var defining the criterion
            var_sc = y_delta / abs(x1 - x2)      # scaling coef. of the core-model var defining the criterion
            x1 *= var_sc
            x2 *= var_sc
            # mid_slope = 1.    # the calculated below should be close to 1,
            # mid_slope = self.cr.mult * y_delta / (var_sc * x_delta)     # negative for min.-criterion
        else:       # PWL based on NOT scaled core-model var
            var_sc = 1.

        x_delta = x1 - x2
        mid_slope = y_delta / x_delta
        min_slope = 1.e-8
        max_slope = 1.e6
        if abs(mid_slope) < min_slope or abs(mid_slope) > max_slope:
            print(f'\nNumerical problem in defining mid_slope for crit. "{self.cr_name}": is_asp {self.is_asp}, '
                  f'is_res {self.is_res},\n\tx1 = {x1:.3e}, x2 = {x2:.3e}, y1 = {y1:.2e}, y2 = {y2:.2e}')
            print(f'slope {mid_slope:.2e}, min_slope {min_slope:.2e}, max_slope {max_slope:.2e}.')
            print('PWL not generated.')
            # mid_slope = 100.    # rather give-up than attempt to redefine the slope
            return None, None

        # see: Bronsztejn p. 245
        b = y1 - mid_slope * x1     # alternatively: b = y2 - slope * x2
        ab.append([mid_slope, b])   # mid-segment is first in the list of segment specs.
        if self.verb > 2:
            print(f'Middle PWL segment is defined by: ({x1:.2e}, {y1:.2e}) and ({x2:.2e}, {y2:.2e}).')
            print(f'params of the mid-segment line y = ax + b: a = {mid_slope:.2e}, b = {b:.2e}, var_sc = {var_sc:2e}.')

        if self.is_asp:  # generate segment above Asp
            up_slope = mid_slope / self.mc.slopeR    # flatter than mid_slop
            up_b = y1 - up_slope * x1  # defined as above but by A point
            ab.append([up_slope, up_b])  # up-segment is second (if generated) in the list of segment specs.
            if self.verb > 2:
                print(f'params of up-segment line y = ax + b: a = {up_slope:.2e}, b = {b:.2e}, var_sc = {var_sc:.2e}.')
        else:
            if self.verb > 2:
                print(f'upper segment of PWL not generated.')

        if self.is_res:  # generate segment below Res
            lo_slope = mid_slope * self.mc.slopeR    # steeper than mid_slop
            lo_b = y2 - lo_slope * x2  # defined as above but by R point
            ab.append([lo_slope, lo_b])  # lo-segment is next (either third or second) in the list of segment specs.
            if self.verb > 2:
                print(f'params of lo-segment line y = ax + b: a = {lo_slope:.2e}, b = {b:.2e}, var_sc = {var_sc:.2e}.')
        else:
            if self.verb > 2:
                print(f'lower segment of PWL not generated.')

        return var_sc, ab

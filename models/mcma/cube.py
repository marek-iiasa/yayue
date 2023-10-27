import math

# todo: add to ParSol:
#   prune marker (to close to another solution) to skip (almost) duplictated solutions during cube generation
#   improve info on CAF (global, in [U, N], vs itr in [A, R]


class ParSol:     # one Pareto solution
    def __init__(self, itr_id, cube_id, vals, a_vals):
        self.itr_id = itr_id    # iter. id: positive indicates cube-seq, negative for Pareto-set corners
        self.cube_id = cube_id	 # id (seq_no) of the parent cube
        self.vals = vals  # list of (not scaled) criteria values of the itr_id solution
        self.a_vals = a_vals  # list of achievement values
        # self.sc_vals = sc_vals  # list of scaled criteria values
        self.closeTo = None     # None replaced by itr_id of a first solution that is close
        self.distMx = None      # None replaced by L-inf distance for close/duplicated solutions
        # print(f'Solution of itr_id {itr_id}: crit. values: {self.vals}, (achievements: {self.a_vals})')
        print(f'Solution of itr_id {itr_id}, a_vals: {self.a_vals}')

    def neigh_inf(self, cube):     # print info on distances to corners of the parent cube
        s1 = cube.s1
        s2 = cube.s2
        for (i, cr) in enumerate(cube.mc.cr):
            res = min(s1.a_vals[i], s2.a_vals[i])
            asp = max(s1.a_vals[i], s2.a_vals[i])
            val = self.a_vals[i]
            is_act = cr.is_active
            # print(f'Crit {cr.name}, s[{s1.itr_id}] {s1.a_vals[i]}, s[{self.itr_id}] {self.a_vals[i]}, '
            #       f's[{s2.itr_id}] {s2.a_vals[i]}')
            if not res <= val <= asp:
                print(f'WARNING: Parsol:neigh_inf():: crit {cr.name} ({is_act=}), {val=} outside [{res=}, {asp=}]')
            # The below occurs when the corresponding criterion is inactive
            # assert res <= val <= asp, f'Parsol:neigh_inf():: crit {cr.name} {val=} outside [{res=}, {asp=}]'

    def is_close(self, s2):     # set self.closeTo and return True, if self is close to solution s2
        self.distMx = 0.
        for (a1, a2) in zip(self.a_vals, s2.a_vals):  # loop over scaled values of criteria
            dist = abs(a1 - a2)
            # todo: define a sensible minDist below
            minDist = 0.5   # was 0.01
            if dist > minDist:   # L-inf (Tchebyshev) norm used for defining close/duplicated solutions
                self.distMx = None
                return False
            self.distMx = max(self.distMx, dist)
        # achievements of all criteria differ less than minDist
        self.closeTo = s2.itr_id
        return True


# todo: add to Cube:
#   skip almost duplictated solution during cube generation
#   store diverse distance metrics (L1, L2, L-Inf)
#   storing in a df info on the progress (using diverse metrics)
#   improve control on printouts
#   consider improving cube generation efficiency (store/update info on neigbours, a new sol is in the current cube)


class Cubes:     # collection of aCubes
    def __init__(self, parRep):
        self.parRep = parRep    # Pareto-set representation object
        self.sols = parRep.sols    # Pareto solutions (without duplicates)
        self.all_cubes = []     # list of all generated cubes

    def add(self, cube):    # add a new cube to the collection
        cube.seq_id = len(self.all_cubes)
        self.all_cubes.append(cube)

    def get(self, seq):    # return the seq_no cube
        assert seq < len(self.all_cubes), f'Cubes::get(): requested {seq}-th cube, only {len(self.all_cubes)} defined.'
        return self.all_cubes[seq]

    def select(self):    # select a cube for generating a new Pareto solution
        best = None
        for c in self.all_cubes:
            if c.used or not c.empty:
                continue
            if best is not None:
                if c.size > best.size:
                    # print(f'Cube ({c.s1.itr_id}, {c.s2.itr_id}), size={c.size:.2e} replaces '
                    #       f'cube ({best.s1.itr_id}, {best.s2.itr_id}), size={best.size:.2e}')
                    best = c
            else:
                best = c
                continue
        if best is None:
            print(f'\nNo cube is available for defining preferences.')
            self.lst_cubes()
            raise Exception(f'Cubes::select(): handling not implemented yet.')
        else:
            # print(f'\nCube selected: ({best.s1.itr_id}, {best.s2.itr_id}), is_degen = {best.is_degen}, '
            #       f'size={best.size:.2e}')
            best.used = True
        return best

    def lst_cubes(self):  # list cubes
        print('\nList of cubes:')
        for (i, c) in enumerate(self.all_cubes):
            c.lst(i)
        print()
        for (i, c) in enumerate(self.all_cubes):
            c.lst_size(i)


class aCube:     # a Cube defined (in achievement values) by the given pair of neighbor solutions
    def __init__(self, mc, s1, s2):
        self.mc = mc    # CtrMca object (provides the needed info on criteria)
        self.s1 = s1    # first solution defining the cube
        self.s2 = s2    # second solution defining the cube
        self.seq_id = None    # seq_nr in the list of all cubes, assigned when the cube is added to Cubes
        self.used = False   # set to True, when the cube was used for generating a solution inside
        self.empty = None   # set to True/False if a solution is/isNot inside
        self.edges = []     # distance components (lengthes of edges for each criterion)
        self.degen = []     # True, if the corresponding edge is too small
        self.is_degen = False   # set to True, if any edge is too small
        self.size = 0.      # cube size = currently L1 distance(s1, s2), for scaled crit values
        self.sizeL1 = 0.    # L1-norm size
        self.sizeL2 = 0.    # L2-norm size
        self.sizeLinf = 0.  # Linf (Tchebyshev)-norm size
        self.aspAch = []   # list of A values in Achievement scale (used to define self.asp/res)
        self.resAch = []   # list of R values in Achievement scale
        # self.sc_asp = []   # list of scaled A values (used in selecting solutions that define the cube)
        # self.sc_res = []   # list of scaled R values
        # self.asp = []   # list of A values in model units (to be used in the MCMA preferences)
        # self.res = []   # list of R values in model units

        # calculate the cube size, and distance components (diffs for each criterion)
        for (a1, a2) in zip(s1.a_vals, s2.a_vals):  # loop over achievements of criteria
            dist = abs(a1 - a2)
            self.sizeL1 += dist  # Manhattan (L1) distance in criteria scaled-values
            self.sizeL2 += dist * dist  # L2 distance
            self.sizeLinf = max(dist, self.sizeLinf)  # Tchebyshev (Linf) distance
            self.edges.append(dist)
            if dist < mc.minDiff:   # difference between achivements too small --> cube dimension degenered
                self.is_degen = True    # the cube degenerated
                self.degen.append(True)  # current dimension degenerated
            else:
                self.degen.append(False)   # current dimension not degenerated
        self.sizeL2 = math.sqrt(self.sizeL2)     # cube size define by L2
        # diverse norms used for the size
        self.size = self.sizeL1     # cube size defined by L1
        # self.size = self.sizeL2     # cube size defined by L2
        # self.size = self.sizeLinf   # cube size defined by Linf

    # define A/R values for spliting the cuboid (i.e., to find a new solution between s1 and s2)
    def setAR(self):
        for (i, cr) in enumerate(self.mc.cr):
            v1 = self.s1.vals[i]
            v2 = self.s2.vals[i]
            if cr.isBetter(v1, v2):  # s1 has better crit. value than s2
                cr.asp = v1
                cr.res = v2
            else:  # s2 has better crit. value than s1
                cr.asp = v2
                cr.res = v1
            if not self.degen[i]:   # not degenerated edge
                cr.is_active = True
                self.aspAch.append(cr.val2ach(cr.asp))
                self.resAch.append(cr.val2ach(cr.res))
            else:   # expand the degenerated edge (used only in the AF regularizing term)
                cr.is_active = False
                # oldA = cr.val
                # oldR = cr.val
                achiv = self.s1.a_vals[i]   # CAF (same/similar for both solutions)
                oldAch = cr.val2ach(achiv)
                expAch = 5.    # A/R expansion-span (in the achivements scale, i.e., [0, 100])
                if achiv < 50.:     # closer to Nadir, move A
                    new_ach = achiv + expAch
                    mark = 'A'
                    cr.asp = cr.ach2val(new_ach)     # get A value corresponding to achievement new_ach
                    self.aspAch.append(new_ach)
                    self.resAch.append(achiv)
                else:           # closer to Utopia, move R
                    new_ach = achiv - expAch
                    mark = 'R'
                    cr.res = cr.ach2val(new_ach)
                    self.aspAch.append(achiv)
                    self.resAch.append(new_ach)
                print(f'Crit. {cr.name} edge {self.edges[i]:.1f} expanded to {expAch:.1f} by moving '
                      f'{mark} from {oldAch} to {new_ach}')
                '''
                print(f'Crit. {cr.name} set to in-active: edge {self.edges[i]:.2e} expanded to {expAch:.2e} by moving:'
                      f'\n\tA from {oldA:.2e} to {cr.asp:.2e},  R from {oldR:.2e} to {cr.res:.2e}.')
                # old version, not good (too much A/R span
                span = 0.5 * abs(cr.utopia - cr.nadir)  # new span of the degenerated edge
                span2 = span / 2.   # A and R by span2, if possible within [U, N]
                distU = abs(cr.utopia - cr.asp)
                distN = abs(cr.nadir - cr.res)
                if distU < distN:  # empty edge closer to utopia
                    if span2 < distU:   # A can be moved towards U by dist2
                        cr.asp = oldA + cr.mult * span2
                        cr.res = oldR - cr.mult * span2
                    else:       # A can be moved to U by only a part of the dist2, thus R is moved more than span2
                        cr.asp = cr.utopia
                        cr.res = oldR - cr.mult * abs(span - distU)
                else:   # empty edge closer to nadir
                    if span2 < distN:   # R can be moved towards N by dist2
                        cr.asp = oldA + cr.mult * span2
                        cr.res = oldR - cr.mult * span2
                    else:       # R can be moved to N by only a part of the dist2, thus A is moved more than span2
                        cr.res = cr.nadir
                        cr.asp = oldA + cr.mult * abs(span - distN)
                '''
            # self.asp.append(cr.asp)
            # self.res.append(cr.res)
            # self.sc_asp.append(cr.sc_var * cr.asp)
            # self.sc_res.append(cr.sc_var * cr.res)
            # print(f'New cube A/R values for criterion {cr.name}: A {cr.asp:.3e}, R {cr.res:.3e}')

    # print: itr_ids of solutions defining the cube, cube size, lengths of cube edges (i.e., components of the size),
    # scaled criteria values defining the diameter-corners, scaled A/R values defining preferences for next iter.
    def lst(self, seq):     # seq: externally defined seq_no of the list of cubes
        val1 = ''
        val2 = ''
        for (v1, v2) in zip(self.s1.vals, self.s2.vals):    # criteria values
            val1 += f'{v1:.2e}, '
            val2 += f'{v2:.2e}, '
        edges = '['
        for dim in self.edges:
            edges += f'{dim:.1f} '
        edges += ']'
        print(f'cube[{seq}] sol [{self.s1.itr_id}, {self.s2.itr_id}], size={self.size:.1f}, '
              f'used {self.used}, empty {self.empty}, degen {self.is_degen}, edges={edges}, '
              f'\n\tcorners: ([{val1}], [{val2}])')

        # the below are for info only; not-scaled A/R values are used for actual preferences
        val1 = ''
        val2 = ''
        # todo: aspAch, resAch for degenerated criteria
        for (v1, v2) in zip(self.aspAch, self.resAch):    # CAF values for A/R
            val1 += f'{v1:.1f} '
            val2 += f'{v2:.1f} '
        print(f'\tNext preferences:  A [{val1}],  R [{val2}]')

    def lst_size(self, seq):  # seq: externally defined seq_no of the list of cubes
        print(f'cube[{seq}], sol [{self.s1.itr_id:3d}, {self.s2.itr_id:3d}], '
              f'sizes: L1={self.sizeL1:.2e}, L2={self.sizeL2:.2e}, Linf={self.sizeLinf:.2e}, degen {self.is_degen}')

    def chk_inside(self, s, s1, s2):    # return True if s is inside cube(s1, s2)
        # it = s.itr_id
        # it1 = s1.itr_id
        # it2 = s2.itr_id
        for (i, cr) in enumerate(self.mc.cr):
            v = s.vals[i]
            v1 = s1.vals[i]
            v2 = s2.vals[i]
            if not min(v1, v2) <= v <= max(v1, v2):
                # print(f'sol {it} is NOT between sols ({it1}, {it2}): crit {cr.name}: {v} is outside ({v1}, {v2}).')
                return False  # v outside the range [v1, v2]
            # else:
            #     print(f'crit {cr.name}: {v} is in the range of ({v1}, {v2}); continue check.')
        # print(f'solution {it} is between solutions ({it1}, {it2}).')
        # raise Exception(f'ParRep::chk_inside() not implemented yet.')
        return True    # all crit-vals of s are between the corresponding values of s1 and s2

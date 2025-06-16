# import datetime
# import pandas as pd
# from numpy.ma.core import append
# import operator
from itertools import combinations  #, permutations
from operator import itemgetter

# from .cube import ParSol, Cubes, aCube
# from .corners import Corners

# noinspection SpellCheckingInspection
class Grid:     # representation of the neighbors
    class aRay:
        def __init__(self, grid, seq, anch0, anch1):
            self.grid = grid
            self.seq = seq          # seq_no of this ray in the set of all rays
            self.is_done = False    # all pairs od neighbor-sols are closer than the gap
            self.anch0 = min(anch0, anch1)      # id of the corresponding solution defining one corner of the ray
            self.anch1 = max(anch0, anch1)      # id of the corresponding solution defining another corner of the ray
            self.idSols = []        # ids of sols belonging to the ray
            self.idSorted = []      # sorted (by the distance to anch0) ids of sols belonging to the ray
            self.sols = grid.sols   # solutions (objects)
            self.gap = grid.gap
            #
            self.idSols.append(anch0)
            self.idSols.append(anch1)
            pass

        def info(self):
            print(f'Ray[{self.seq}]: anch0 = {self.anch0}, anch1 = {self.anch1}, nSols = {len(self.idSols)}')
            print(f'\tidSols: {self.idSols}')
            print(f'\tidSorted: {self.idSorted}')
            pass

        def getSol(self, idSol):  # return the L^inf distance between the sol-pairs
            for s in self.sols:
                if s.itr_id == idSol:
                   return s
            raise Exception(f'Grid::getSol() - solution with id {id} not found.')

        def dist(self, id1, id2):  # return the L^inf distance between the sol-pairs
            p1 = self.getSol(id1)
            p2 = self.getSol(id2)
            val = 0.
            for i in range(self.grid.mc.n_crit):
                val = max(val, abs(p1.a_vals[i] - p2.a_vals[i]))
            # print(f'p1 = {id1}, p2 = {id1}, L^inf dist = {val:.2f}')
            return val

        def mkPairs(self):
            idBase = self.anch0   # base is the anchor with the lowest id
            # if self.anch1 < idBase:   # no longer needed: ids sorted by the ctor
            #     idBase = self.anch1
            assert idBase in self.idSols, f'Grid::mkPairs(): solution with id {idBase} not found'
            dist = []   # distances from the base, used for sorting sols
            for idS in self.idSols:
                d = self.dist(idBase, idS)
                dist.append([idBase, idS, d])
                pass

            dist.sort(key=itemgetter(2), reverse = False)    # sort sols in ascending distance from the anchor
            # store sorted idSols
            self.idSorted = []
            for item in dist:
                self.idSorted.append(item[1])   # item = [idBase, idS, dist]

            # create pairs from neighbor sols, add them to the candidate's dict
            cand = self.grid.cand   # convenience alias of the candidate dict.
            nPairs = len(dist) - 1
            nCand = 0       # number of candidates submitted by the ray
            nSmall = 0
            for i in range(nPairs):
                id0 = dist[i][1]
                id1 = dist[i + 1][1]
                diff = self.dist(id0, id1)
                if diff < self.gap:
                    nSmall += 1
                    continue
                else:
                    nCand += 1
                pair = [id0, id1]
                pair = self.grid.sortPair(pair)
                cand.update({(pair[0], pair[1]): [diff, self.seq]})
            print(f'Grid::mkPairs(): ray[{self.seq}]: {nPairs} pairs defined, {nCand} candidates added, '
                  f'{nSmall} too close pairs ignored')
            if nCand == 0:
                self.is_done = True     # no more cubes to be generated from this ray
                return False
            pass
            return True

    def __init__(self, wflow):      # initialize by the corner, and optionally neutral, solutions
        # references for convenience access
        self.wflow = wflow    # WrkFlow object
        self.mc = wflow.mc    # CtrMca object
        self.parRep = wflow.par_rep         # PF representation object
        self.stage = -1       # -1 ctor, 0 rays0 (built on corners), 1 rays1 (built on rays0)
        self.corners = self.wflow.corner
        self.sols = self.parRep.sols      # Pareto-solutions (ParSol objects), excluding duplicated/close solutions
        self.rays0 = []     # ray-objects built on corners
        self.rays1 = []     # ray-objects built on rays0
        self.rays = None    # reference to rays used at the current stage
        self.cand = {}      # candidate sol-pairs: key - (sorted by val) pair of sol-ids, val - distance, ray-seq_no
        self.accepted = []  # pairs for cube's gener.: idSol1, idSol2, diff, seq_ray
        self.done = {}      # already used sol-pairs: key - (sorted) sol-ids, val - distance
        self.gap = self.parRep.gap
        self.verb = 4   # wflow.verb
        #
        self.lastPair = (None, None)    # ids of the lastly selected solution pair (of most distant neighbors)
        self.lastRay = None  # seq_no of the ray from which the parents were selected
        #
        assert self.mc.n_crit == 3, \
            f'Grid: the problem has {self.mc.n_crit} criteria; only 3 crit. processed by this option.'
        self.wFlow()    # controls work-flows
        pass

    # helpers
    @staticmethod
    # sort ids, input and retun should be a list
    def sortPair(pair):
        if pair[0] > pair[1]:   # sort the pair's indices
            tmp = pair[0]
            pair[0] = pair[1]
            pair[1] = tmp
        return pair

    def chk(self, pair):    # check if the pair of sol-ids was already used
        pair = self.sortPair(pair)      # the done-dict is hashed by ordered sol-ids
        return (pair[0], pair[1]) in self.done.keys()
    # end of helpers

    def wFlow(self):
        if self.stage == -1:    # called from the ctor,  create rays defined by PF corners
            self.stage = 0
            self.rays = self.rays0
            sCorners = self.corners.s_corners
            pair_lst = list(combinations(sCorners, 2))  # pairs of corners
            for seq, (anch0, anch1) in enumerate(pair_lst):   # ctor of rays defined by corners of the PF
                self.rays.append(self.aRay(self, seq, anch0, anch1))
        elif self.stage == 0:    # called from self.addSol()
            pass
        elif self.stage == 1:  # called from self.addSol()
            pass
            # raise Exception(f'Grid::wFlow() - stage {self.stage} not implemented.')
        else:
            raise Exception(f'Grid::wFlow() - stage {self.stage} not implemented.')
        self.explore()
        return

    def mkRays1(self):      # create rays from rays0
        self.stage = 1

        # select a pair of rays0 having the same anchor
        idBase = self.corners.s_corners[0]  # take sol_id of the first corner
        r0 = None
        r1 = None
        for seq, r in enumerate(self.rays0):
            found = None
            if r.anch0 == idBase:
                found = [seq, 0]
            elif r.anch1 == idBase:
                found = [seq, 1]
            if found is not None:
                if r0 is None:
                    r0 = found
                elif r1 is None:
                    r1 = found
                if r1 is not None:
                    break
        pass
        assert r1 is not None, f'Grid::mkRays1(): cannot find two rays0 for {idBase = }'
        # print(f'rays for {idBase = }: {r0 = }, {r1 = }')

        # check which points/sols need to be skipped in order to have pairs of points belonging to each ray
        base0 = self.rays0[r0[0]]
        base1 = self.rays0[r1[0]]
        nSol0 =  len(base0.idSols)
        nSol1 =  len(base1.idSols)
        # todo: add handling different numbers of solutions, as well as different anchors
        assert nSol0 == nSol1, f'Grid::mkRays1(): different number of solutions ({nSol0=}, {nSol1=}) not handled yet.'
        assert r0[1] == r1[1], f'Grid::mkRays1(): different ray anchors ({r0[1]=}, {r1[1]=}) not handled yet.'
        print('The two base-rays')
        base0.info()
        base1.info()
        print(f'{nSol1 = }')

        # generate rays1 for each pair, exclude anchors of rays0
        self.rays = self.rays1
        for i in range(1, nSol0 - 1):    # ignore first and last sol
            an0 = base0.idSorted[i]
            an1 = base1.idSorted[i]
            nRay = self.aRay(self, i - 1, an0, an1)
            print(f'Ray[{i-1}]: {an0 = }, {an1 = }')
            nRay.info()
            self.rays.append(nRay)
            pass
        pass
        print(f'Grid::mkRays1(): {len(self.rays)} rays generated for stage {self.stage}.')

        self.explore()
        # raise Exception(f'Grid::mkRays1() - not implemented yet.')

    def explore(self):      # check, if a pair is available, otherwise generate new set of pairs
        if len(self.cand):
            found = self.selCand()  # select the pair of the most distant neighbors to be used for defining new cube
            if found:
                return  # indices of the pair of most distant neighbors available by self.getPair()
            else:
                print(f'\nGrid::expolore(): no more pair candidates. Generate new set of pairs. ------------------------')

        # empty list of candidate pairs; (re)calculate neighbors of each solution
        # print(f'\n\nAll previously generated cubes used. Generate new set of neighbors. ------------------------------')
        self.mkCand()  # select in each ray sol-pairs candidates for making cubes, store them in self.cand{}
        found = self.selCand()
        if not found:  # no suitable pairs were found, terminate the iterations
            if self.stage == 0:     # mv to stage 1, i.e., create rays1
                self.mkRays1()
            else:
                self.lastPair = (None, None)
                print(f'\nGrid::selCand(): all suitable pairs were provided. Terminate the iterations. ------------------')
        return  # the pair of solution ids (for defining a cube) is available by self.getPair()


    # Entry point: add a new solution and prepare pairs of solutions to be used for a new cube.
    # Called from the ctor to store the corner (and optionally neutral) solutions, as well as for each subsequently
    # found solution; also called for ignored solutions (close to another solution).
    # Returns nothing.
    # Access to pairs through the self.getPair() that returns either a pair of solutions' ids to be used
    # for defining a next cube or (None, None) if there are no more pairs to be used for defining a cube
    def addSol(self, s=None, was_close=False):  # add a Pareto solution
        if was_close:    # the last solution was close (not included in the PF); find a pair from previous solutions
            if self.verb > 2:
                print(f'Grid::addSol(): last solution was close to or dominated by, another solution.')
            pass
        elif s is None:   # nothing to do (sols are processed by aRay objects
            raise Exception(f'Grid::addSol(None) - unexpeted call with the argument "None".')
        else:           # add solution to the corresponding ray
            found = False
            for r in self.rays:
                if r.seq == self.lastRay:
                    found = True
                    r.idSols.append(s.itr_id)
                    break
            if not found:
                raise Exception(f'Grid::addSol() - last solution (id {s.itr_id}) cannot be allocatek to any ray.')
        print(f'Grid::addSol(): there are {len(self.sols)} solutions, {len(self.done)} pairs done.')
        return self.wFlow()

    # return indices of the solution-pair selected for making a next cube
    def getPair(self):
        return self.lastPair

    def mkPairs(self):      # mk pair(s) (for cube generation)
        allDone = True
        arePairs = False
        for r in self.rays:
            if r.is_done:
                continue
            rayPairs = r.mkPairs()      # returns True, if the ray provided pair(s)
            if rayPairs:
                arePairs = True
                allDone = False
        if allDone:
            print(f'Grid::mkPairs(): all pairs were done.')
            # raise Exception(f'Grid::mkPairs(): all pairs were done.')
        assert allDone != arePairs, f'Grid::mkPairs(): inconsistency: {allDone =} != {arePairs =}.'
        return arePairs

    # make the candidate pairs from the neighbors' dict
    def mkCand(self):
        # drop all old lists and dictionaries
        self.cand = {}
        self.accepted = []

        arePairs = self.mkPairs()      # generate pairs of solutions suitable for the cube generation
        assert (arePairs and len(self.cand) > 0) or (not arePairs and len(self.cand) == 0), \
                f'Grid::mkCand(): inconsistency: {arePairs=}, {len(self.cand)=}'

        # scan the pairs and make list of pairs for the cube generation
        for idItem, item in self.cand.items():  # id consists of pt-pair, item of diff and ray's seq_no
            pair = [idItem[0], idItem[1]]   # for self.sort it needs to be a list
            was_used = self.chk(pair)
            if was_used:
                raise Exception(f'Grid::mkCand(): the pair {pair} was used (check, if it indicates PF gap).')
            diff = item[0]      # item[1]: seq_no of the ray
            if diff < self.gap:     # diff: difference of achiev. for the pair of points for i-the criterion
                continue    # skip pt-pair close in i-th dimension (should be distant in other dimension)
                # raise Exception(f'Neigh::mkCand(): the pair ({idItem}, diff  {diff:.2f} should not be in self.neighCube.')
            seq_ray = item[1]
            self.accepted.append([idItem[0], idItem[1], diff, seq_ray])
        pass
        self.accepted.sort(key=itemgetter(2), reverse=True)  # sort in descending order

    # select (from the previously found and sorted by the distance candidates) the pair of the most distant neighbors
    def selCand(self):
        for item in self.accepted:
            id0 = item[0]
            id1 = item[1]
            diff = item[2]
            seq_ray = item[3]
            is_used = self.chk([id0, id1])
            if is_used:     # should not happen, but just in case...
                raise Exception(f'Grid::selCand() - pair of sols ({id0}, {id1}) was already used.')
            self.lastPair = (id0, id1)
            self.lastRay = seq_ray
            self.done.update({self.lastPair: diff})
            self.accepted.pop(0)
            print(f'Solutions ({id0}, {id1}), dist. {diff:.1f} selected for the next cube. {len(self.accepted)} candidates left.')
            return True
        print(f'Grid::selCand(): no more candidates. --------------------------')
        return False
        # raise Exception(f'Neigh::selCand() - not implemented yet.')

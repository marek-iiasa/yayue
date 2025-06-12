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
            self.anch0 = anch0      # id of the corresponding solution defining one corner of the ray
            self.anch1 = anch1      # id of the corresponding solution defining another corner of the ray
            self.idSols = []        # ids of sols belonging to the ray
            self.sols = grid.sols   # solutions (objects)
            self.gap = grid.gap
            #
            self.idSols.append(anch0)
            self.idSols.append(anch1)
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
            if self.anch1 < idBase:
                idBase = self.anch1
            assert idBase in self.idSols, f'Grid::mkPairs(): solution with id {idBase} not found'
            dist = []   # distances from the base, used for sorting sols
            for idS in self.idSols:
                d = self.dist(idBase, idS)
                dist.append([idBase, idS, d])
                pass

            # creating pairs from neighbor sols, add them to the candidate's dict
            dist.sort(key=itemgetter(2), reverse = False)    # sort sols in ascending distance from the anchor
            cand = self.grid.cand   # convenience alias of the candidate dict.
            nPairs = len(dist) - 1
            nSmall = 0
            for i in range(nPairs):
                id0 = dist[i][1]
                id1 = dist[i + 1][1]
                diff = self.dist(id0, id1)
                if diff < self.gap:
                    nSmall += 1
                    continue
                pair = [id0, id1]
                pair = self.grid.sortPair(pair)
                cand.update({(pair[0], pair[1]): [diff, self.seq]})
            print(f'Grid::mkPairs(): ray[{self.seq}]: {nPairs} pairs defined, {nSmall} too close pairs ignored')
            pass

    def __init__(self, wflow):      # initialize by the corner, and optionally neutral, solutions
        # references for convenience access
        self.wflow = wflow    # WrkFlow object
        self.mc = wflow.mc    # CtrMca object
        self.parRep = wflow.par_rep         # PF representation object
        self.corners = self.wflow.corner
        self.sols = self.parRep.sols      # Pareto-solutions (ParSol objects), excluding duplicated/close solutions
        self.rays = []      # list of ray-objects
        self.cand = {}      # candidate sol-pairs: key - (sorted by val) pair of sol-ids, val - distance, ray-seq_no
        self.accepted = []  # pairs for cube's gener.: idSol1, idSol2, diff, seq_ray
        self.done = {}      # already used sol-pairs: key - (sorted) sol-ids, val - distance
        self.gap = self.parRep.gap
        self.verb = 4   # wflow.verb
        #
        self.lastPair = (None, None)    # ids of the lastly selected solution pair (of most distant neighbors)
        self.lastRay = None  # seq_no of the ray from which the parents were selected
        #
        self.init()
        pass

    def init(self):
        # create rays defined by PF corners
        sCorners = self.corners.s_corners
        pair_lst = list(combinations(sCorners, 2))  # pairs of corners
        for seq, (anch0, anch1) in enumerate(pair_lst):   # ctor of rays defined by corners of the PF
            self.rays.append(self.aRay(self, seq, anch0, anch1))

        self.addSol()   # sols processed, make sol-pairs for subsequent getPair() calls
        # raise Exception(f'Grid::init() - not implemented yet.')

    # Entry point: add a new solution and prepare the next pair of solutions to be used for a new cube.
    # Called from the ctor to store the corner (and optionally neutral) solutions, as well as for each subsequently
    # found solution; also called for ignored solutions (close to another solution).
    # The only return point; returns nothing.
    # The self.getPair() returns either a pair of solutions' ids to be used for defining
    # a next cube or (None, None) if there are no more pairs to be used for defining a cube
    def addSol(self, s=None, was_close=False):  # add a Pareto solution
        if was_close:    # the last solution was close (not included in tthe PF); find a pair from previous solutions
            if self.verb > 2:
                print(f'Grid::addSol(): last solution was close to or dominated by, another solution.')
            pass
        elif s is None:   # nothing to do (sols are processed by aRay objects
            pass
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
        if len(self.cand):
            found = self.selCand()  # select the pair of the most distant neighbors to be used for defining new cube
            if found:
                return      # indices of the pair of most distant neighbors available by self.getPair()
            else:
                print(f'\nGrid::addSol(): no more pair candidates. Recalculate neighbors. --------------------------')

        # empty list of candidate pairs; (re)calculate neighbors of each solution
        print(f'\n\nAll previously generated cubes used. Generate new set of neighbors. ------------------------------')
        # self.mkNeigh()     # find neighbors of each solution
        # self.lastPair = (None, None)
        # print(f'\nGrid::selCand(): test termination. ------------------')
        # return
        self.mkCand()      # select from the neighbors' sol-pairs candidates for making cubes, store them in self.cand{}
        found = self.selCand()
        if not found:   # no suitable pairs were found, terminate the iterations
            self.lastPair = (None, None)
            print(f'\nGrid::selCand(): all suitable pairs were provided. Terminate the iterations. ------------------')
        return  # the pair of solution ids (for defining a cube) is available by self.getPair()

    # return indices of the solution-pair selected for making a next cube
    def getPair(self):
        return self.lastPair

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

    def mkPairs(self):      # mk pair(s) (for cube generation)
        allDone = True
        for r in self.rays:
            if r.is_done:
                continue
            r.mkPairs()
            allDone = False
        if allDone:
            print(f'Grid::mkPairs(): all pairs were done.')
            raise Exception(f'Grid::mkPairs(): all pairs were done.')
        return

    # make the candidate pairs from the neighbors' dict
    def mkCand(self):
        # drop all old lists and dictionaries
        self.cand = {}
        self.accepted = []

        self.mkPairs()      # generate pairs of solutions suitable for the cube generation

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

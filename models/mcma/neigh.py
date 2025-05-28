# import datetime
# import pandas as pd
# from numpy.ma.core import append
# import operator
from operator import itemgetter

# from .cube import ParSol, Cubes, aCube
# from .corners import Corners

# noinspection SpellCheckingInspection
class Neigh:     # representation of the neighbors
    def __init__(self, parRep):      # initialize by the corner, and optionally neutral, solutions
        # references for convenience access
        self.wflow = parRep.wflow    # WrkFlow object
        self.mc = parRep.wflow.mc    # CtrMca object
        self.parRep = parRep         # PF representation object
        self.sols = parRep.sols  # Pareto-solutions (ParSol objects), excluding duplicated/close solutions
        #
        self.points = {}         # key - solution id, val - vector of achievements
        self.points2 = []        # self.points converted to a list (to easy sorting)
        self.solSort = []        # self.points2 sorted for each criterion by increasing achievements
        self.neighCube = {}      # neighbors for generating cubes: key - ids of (sol1, sol2, crit), tmp dist in i-th crit
        self.neighDist = {}      # neighbors for calculating the distribution
        self.lastPair = (None, None)    # ids of the lastly selected solution pair (of most distant neighbors)
        self.done = {}      # already used sol-pairs: key - (sorted) sol-ids, val - distance
        self.cand = {}      # candidate sol-pairs: key - (sorted) sol-ids, val - distance
        self.wrkCand = []   # work-list of candidates' pairs (for info only)
        self.wrkPairs = {}  # work-list of candidates' pairs
        #
        self.gap = self.parRep.mc.opt('mxGap', 10)  # the max gap between neighbors
        self.achDiff = 0.1 * self.gap  # tolerance for diffentiating achievements
        self.verbose = 2    # print verbosity level
        #
        self.addSol()       # initialize the neighbors by selfish (and optionally neutral) solutions
        pass

    # Entry point: add a new solution and prepare the next pair of solutions to be used for a new cube.
    # Called from the ctor to store the corner (and optionally neutral) solutions, as well as for each subsequently
    # found solution; also called for ignored solutions (close to another solution).
    # The only return point; returns nothing.
    # The self.getPair() returns either a pair of solutions' ids to be used for defining
    # a next cube or (None, None) if there are no more pairs to be used for defining a cube
    def addSol(self, s=None, was_close=False):  # add a Pareto solution
        if was_close:    # the last solution was close (not included in tthe PF); find a pair from previous solutions
            if self.verbose > 2:
                print(f'Neigh::addSol(): last solution was close to another solution.')
            pass
        elif s is None:   # initial call, use the corner, optionally also neutral, solutions
            print(f'Neigh::addSol(): the ctor initialized with corner (and optionally, neutral) solutions.')
            for s1 in self.sols:
                self.points.update({s1.itr_id: s1.a_vals})
                tmp = s1.a_vals.copy()
                tmp.insert(0, s1.itr_id)    # for convenience, put itr_id in front of each item
                self.points2.append(tmp)
        else:
            self.points.update({s.itr_id: s.a_vals})
            tmp = s.a_vals.copy()
            tmp.insert(0, s.itr_id)    # for convenience, put itr_id in front of each item
            self.points2.append(tmp)
        print(f'Neigh::addsol(): there are {len(self.points)} solutions, {len(self.done)} pairs done.')
        # raise Exception(f'Neigh::addSol() - not implemented yet.')
        if len(self.cand):
            found = self.selCand()  # select the pair of the most distant neighbors to be used for defining new cube
            if found:
                return      # indices of the pair of most distant neighbors available by self.getPair()
            else:
                print(f'\nNeigh::addSol(): no more pair candidates. Recalculate neighbors. --------------------------')

        # empty list of candidate pairs; (re)calculate neighbors of each solution
        print(f'\n\nAll previously generated cubes used. Generate new set of neighbors. ------------------------------')
        self.mkNeigh()     # find neighbors of each solution
        self.mkCand()      # select from the neighbors' sol-pairs candidates for making cubes, store them in self.cand{}
        found = self.selCand()
        if not found:   # no suitable pairs were found, terminate the iterations
            self.lastPair = (None, None)
            print(f'\nNeigh::selCand(): all suitable pairs were provided. Terminate the iterations. ------------------')
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

    def dist(self, pair):   # return the L^inf distance between the sol-pairs
        p1 = self.points[pair[0]]
        p2 = self.points[pair[1]]
        val = 0.
        for i in range(self.mc.n_crit):
            val = max(val, abs(p1[i] - p2[i]))
        print(f'pair {pair}: p1 = {p1}, p2 = {p2}, L^inf dist = {val:.2f}')
        return val

    def chk(self, pair):    # check if the pair of sol-ids was already used
        pair = self.sortPair(pair)      # the done-dict is hashed by ordered sol-ids
        return (pair[0], pair[1]) in self.done.keys()

    # end of helpers

    # mk pair(s) (for cube generation) for k-th sol/pt and i-th crit.; achiev: sorted (for i-th crit) achievements
    def mkPairs(self):
        for i in range(self.mc.n_crit):     # loop over criteria
            achiev = self.solSort[i]        # achievements sorted for i-th criterion in ascending order
            # jLast = 0   # seq of the last-used right point
            for k, p1 in enumerate(achiev):     # k: current seq-no of p1, p1: left pt of the pair with j (to be found)
                if k == len(achiev) - 1:
                    break    # nothing to be done for the last point; process the next criterion
                id1 = p1[0]         # id (solution itr_id) of the left pt in the sought pair
                ach1 = p1[i + 1]    # i-th crit. achievement of the p1
                j = k + 1   # index of the current candidate sol (for a pair with k-th sol), starts with the next to k-th
                phase1 = True   # skip pts with ach. close to k-th (next phase: add points close to first better enough)
                phaseStr = 'phase1'
                achOK = None    # ach of the distant pt
                nFound = 0      # number of pairs found with k-th sol
                nUsed = 0       # number of already used pairs with k-th sol
                while j < len(achiev):
                    # todo: check, if the below condition is indeed useful (next left pt has likely other pattern of remaining crit.)
                    '''
                    if j < jLast:
                        j += 1
                        continue    # current point already used as the right pt in a previous pair; take a next point
                    jLast = j
                    '''
                    p2 = achiev[j]
                    id2 = p2[0]
                    ach2 = p2[i + 1]
                    diff = ach2 - ach1
                    pair = self.sortPair([id1, id2])
                    key = (pair[0], pair[1], i)
                    j += 1
                    # check, if the current point is OK for the pair with k-th pt
                    if phase1:  # looking for the first pt distant enough from k-th pt
                        # isOK = diff > self.gap    # this skips neighbor closer than the gap
                        isOK = diff > self.achDiff
                        if isOK:    # first pair with k-th pt, use it and move to phase2
                            phase1 = False     # start phase2, i.e., looking for pt close to the first distant pt
                            phaseStr = 'phase2'
                            achOK = ach2       # achivement OK for the second phase
                            if self.verbose > 4:
                                print(f'pair {key}, diff {diff:.2f}: move to phase2')
                        else:
                            if self.verbose > 4:
                                print(f'{phaseStr}, pt {id1}, {ach1:.2f}: skipping too close pt {id2}, ach {ach2:.2f}: '
                                      f'checking next pt.')
                            continue    # look for the first pt distant enough from p1
                    else:       # phase2: look for a pt close to the right pt of the first pair with k-th pt
                        if abs(achOK - ach2) < self.achDiff:
                            isOK = True     # current point close enough to the first distant pt
                        else:
                            if self.verbose > 4:
                                print(f'{phaseStr}, skipping pt {id2}, ach {ach2:.2f}: too distant to {achOK:.2f}, '
                                      f'checking next pt.')
                            break   # no (more) suitable pair(s) with k-th point

                    # check, if p1 and p2 are in the same 2-dim plane
                    neighOK = True
                    '''
                    for d in range(self.mc.n_crit):  # check if p1 & p2 are neighbors in more than i-th crit
                        if d == i:
                            continue    # p1 and p2 are obviously neighbors in the i-th criterion
                        ach3 = p1[d + 1]
                        ach4 = p2[d + 1]
                        if self.verbose > 4:
                            print(f'{phaseStr}, {key}, d {d}, ach3 {ach3:.2f}, ach4 {ach4:.2f}')
                        if abs(ach3 - ach4) < self.achDiff:     # neighbor in d-th crit.
                            neighOK = True
                            break  # find pair(s) with the next point
                    '''
                    if self.verbose > 4:
                        print(f'{phaseStr}, {key}, diff {diff:.2f}, isOK {isOK}, neighOK {neighOK}')
                    if not isOK or not neighOK:
                        continue    # find pair(s) with the next point

                    # found pt suitable for the cube-generation pair
                    nFound += 1
                    if not self.chk(pair):
                        self.neighCube.update({key: diff})
                        if self.verbose > 4:
                            print(f'pair {key}, dist {diff:.2f} added for cube generation.')
                    else:
                        nUsed += 1
                        if self.verbose > 4:
                            print(f'skipping pair {key} (used in a previous iteration).')
                    # try next pt to make a pair with k-th sol.
                # end of looking for pairs with k-th sol.
                if self.verbose > 2:
                    print(f'Neigh::mkPairs(): {nFound} pairs found for {k}-th sol, {i}-th crit, incl. {nUsed} already used.')
                pass

    # find closest neighbors (two for each criterion) of each solution, then call self.mkPairs()
    def mkNeigh(self):
        self.wrkCand = []  # drop the old lists and dictionary
        self.solSort = []
        self.wrkPairs = {}
        self.neighCube = {}     # neighbors for each point/solution and criterion
        self.neighDist = {}

        # sort points by increasing achievements for each criterion separately
        for i in range(self.mc.n_crit):
            tmp = sorted(self.points2, key=itemgetter(i + 1), reverse=False)
            self.solSort.append(tmp)

        # find neighbors in each criterion from the corresponding list of sorted (ascending) achievements
        for i in range(self.mc.n_crit):
            achiev = self.solSort[i]
            for k, p1 in enumerate(achiev):
                if k == len(achiev) - 1:
                    break    # nothing to be done for the last point, process data for the next criterion
                id1 = p1[0]
                ach1 = p1[i + 1]
                p2 = achiev[k + 1]
                id2 = p2[0]
                ach2 = p2[i + 1]
                diff = ach2 - ach1
                pair = self.sortPair([id1, id2])
                key = (pair[0], pair[1], i)
                # todo: computation of the neighbor data for distrirbution info needs to be verified
                # print(f'neighbor distribution data item: key {key} dist {diff:.2f}')
                self.neighDist.update({key: diff})      # neighbor data for distribution info

            pass
        pass

        self.mkPairs()  # mk pair(s) for cube generation

    '''
    # find closest neighbors (two for each criterion) of each solution
    def mkNeigh1(self):
        self.wrkCand = []  # drop the old lists and dictionary
        self.solSort = []
        self.wrkPairs = {}
        self.neigh = {}     # neighbors for each point/solution and criterion
        self.neighDeb = {}

        # sort points by increasing achievements for each criterion separately
        for i in range(self.mc.n_crit):
            tmp = sorted(self.points2, key=itemgetter(i + 1), reverse=False)
            self.solSort.append(tmp)

        # find neighbors for each solution: two for each criterion (for worse and better than base) achievements)
        oneNeigh = True    # find for each solution only two neighbors (one with worse achievement and one with better)
        # find adjoint to each base two sols with immediate worse and better achiev. in the i-th criterion
        for seq, base in enumerate(self.solSort[i]):
            neighbors = []      # pair of neighbors for the i-th criterion
            id_base = base[0]
            for i in range(self.mc.n_crit):     # loop over criteria
                # first, the sol with worse achievement
                k = seq - 1         # position (relative to the base) in the solSort[i] (must be before the base)
                id_worse = None     # set for the case no suitable worse sol will be found
                diff_worse = 0.     # achievement difference between base and a worse sol
                achFirst = None
                while k >= 0:
                    worse = self.solSort[i][k]   # closest sol with worse achievement in the i-th criterion
                    ach = worse[i + 1]
                    diff_worse = abs(base[i + 1] - ach)
                    if oneNeigh:
                        id_worse = worse[0]
                        break       # don't look for alternative sols with worse achievement
                    diff_base = diff_worse
                    if achFirst is None:
                        achFirst = ach
                        print(f'base {id_base}, {i}-th crit, closest worse {worse[0]} ach {ach:.1f} diff {diff_base:.1f}')
                    else:
                        diff = abs(ach - achFirst)
                        if diff > self.achDiff:
                            print(f'Neigh::mkNeigh(): next worse sol {worse[0]} differs by {diff:.1f} from the first')
                            break   # the subsequent worse is too much worse than the first found
                    k -= 1  # seq of the possibly next-previous to check
                    if diff_base < self.achDiff:
                        print(f'Neigh::mkNeigh(): next worse sol {worse[0]} too close to the base {diff_base:.1f}')
                        continue  # try next worse
                    pair = self.sortPair([id_base, worse[0]])
                    is_done = self.chk(pair)
                    if is_done:
                        print(f'Neigh::mkNeigh(): pair {pair} was already used. Checking the next worse sol.')
                        continue    # the pair was used, try the next-previous worse sol.
                    id_worse = worse[0]
                    diff_worse = abs(base[i + 1] - worse[i + 1])
                    break   # break the loop: suitable worse sol found
                print(f'sol {id_base}, crit {i}: id_worse {id_worse}, dist_worse {diff_worse:.1f}')

                # second, find the the neighbor sol with better achievement
                k = seq + 1
                id_better = None     # set for the case no suitable worse sol will be found
                diff_better = 0.
                achFirst = None
                while k  < len(self.solSort[i]):
                    better = self.solSort[i][k]   # closest sol with better achievement in the i-th criterion
                    ach = better[i + 1]
                    diff_base = abs(base[i + 1] - ach)
                    if oneNeigh:
                        id_better = better[0]
                        diff_better = diff_base
                        break
                    if achFirst is None:
                        achFirst = ach
                        print(f'base {id_base}, {i}-th crit, closest better {better[0]} ach {ach:.1f} diff {diff_base:.1f}')
                    else:
                        diff = abs(ach - achFirst)
                        if diff > self.achDiff:
                            print(f'Neigh::mkNeigh(): next better sol {better[0]} differs by {diff:.1f} from the first')
                            break   # the subsequent better is too much better than the first found
                    k += 1  # seq of the possibly next to check
                    if diff_base < self.achDiff:
                        print(f'Neigh::mkNeigh(): next better sol {better[0]} too close to the base {diff_base:.1f}')
                        print(f'{k = }')
                        if k > 20:
                            raise Exception(f'Neigh::mkNeigh(): something wrong here.')
                        continue  # try next better
                    pair = self.sortPair([id_base, better[0]])
                    is_done = self.chk(pair)
                    if is_done:
                        print(f'Neigh::mkNeigh(): pair {pair} was already used. Checking the next better sol.')
                        continue    # the pair was used, try the next better sol.
                    id_better = better[0]
                    diff_better = abs(base[i + 1] - better[i + 1])
                    break       # break the loop: suitable better sol found
                print(f'sol {id_base}, crit {i}: id_better {id_better}, dist_better {diff_better:.1f}')

                # if self.verbose > 3:
                #     print(f'Sol {id_base} crit_id {i}, pair worse: ({id_base}, {id_worse}), dist. {dist_worse:.1f}')
                #     print(f'Sol {id_base} crit_id {i}, pair better: ({id_base}, {id_better}), dist. {dist_better:.1f}')
                # end processing a sol on the i-th criterion
                #
                # store the info in self.neigh{}
                # item1 = [id_worse, dist_worse]
                # item2 = [id_better, dist_better]
                # self.neighDeb.update({id_base: [i, [item1, item2]]})   # debugging info

                if oneNeigh:
                    item = [i, id_worse, id_better]
                    neighbors.append(item)
                else:
                    # store pairs of (base, neighbor), where neighbors are (worse and better) sol relative to each base
                    if id_worse is not None:
                        pair = self.sortPair([id_base, id_worse])
                        is_done = self.chk(pair)
                        if not is_done:
                            key = (pair[0], pair[1])
                            self.neigh.update({key: 0.})   # dist will be added after processing all sols
                        else:
                            raise Exception(f'Neigh::mkNeigh(): the worse pair {pair} was already used.')
                    if id_better is not None:
                        pair = self.sortPair([id_base, id_better])
                        is_done = self.chk(pair)
                        if not is_done:
                            key = (pair[0], pair[1])
                            self.neigh.update({key: 0.})   # dist will be added after processing all sols
                        else:
                            raise Exception(f'Neigh::mkNeigh(): the better pair {pair} was already used.')
                pass
                # end of the loop on criteria for the selected base
                if oneNeigh:
                    self.neigh.update({id_base: neighbors})
            pass
        # end of the loop on solution
        pass

        if not oneNeigh:
            # set distances between neighbors
            for pair, dist in self.neigh.items():
                dist = self.dist(pair)
                self.neigh.update({pair: dist})
            pass
    '''

    # make the candidate pairs from the neighbors' dict
    def mkCand(self):
        self.cand = {}  # drop the old list (although it should be anyway empty)
        for idItem, diff in self.neighCube.items():  # id consists of pt-pair and crit id
            pair = [idItem[0], idItem[1]]   # for self.sort it needs to be a list
            was_used = self.chk(pair)
            if diff < self.gap:     # diff: difference of achiev. for the pair of points for i-the criterion
                continue    # skip pt-pair close in a dimension (should be distant in other didmension
                # raise Exception(f'Neigh::mkCand(): the pair ({idItem}, diff  {diff:.2f} should not be in self.neighCube.')
            if was_used:
                raise Exception(f'Neigh::mkCand(): the pair {pair} was used (check, if it indicates PF gap).')
            pair = (pair[0], pair[1])   # for use as a key the pair needs to be tuple
            if pair in self.cand:
                oldDiff = self.cand.get(pair)   # the max of differences for previous criteria
                diff = max(diff, oldDiff)
            self.cand.update({pair: diff})  # diff here corresponds to the L^inf norm dist. between the pair of sols.
        pass

    # select (from the previously found candidates) the pair of the most distant neighbors
    def selCand(self):
        # if len(self.cand) == 0:
        #     raise Exception(f'Neigh::selCand() called for empty candidate list.')
        d =  sorted(self.cand.items(), key= itemgetter(1), reverse=True)   # default False: ascending
        for pair, val in d:
            is_used = self.chk(pair)
            if is_used:     # should not happen, but just in case...
                raise Exception(f'Neigh::selCand() - pair {pair} was already used.')
            self.lastPair = pair
            self.done.update({self.lastPair: val})
            self.cand.pop(pair)
            print(f'Solutions {pair} dist. {val:.1f} selected for the next cube. {len(self.cand)} candidates left.')
            return True
        print(f'Neigh::selCand(): no more candidates. --------------------------')
        return False
        # raise Exception(f'Neigh::selCand() - not implemented yet.')

    # find and store the pair of the most distant neighbors to be used for defining new cube
    def explore(self):
        self.wrkCand = []  # drop the old lists and dictionary
        self.solSort = []
        self.wrkPairs = {}

        for i in range(self.mc.n_crit):  # sort points by achievements for each criterion separately
            tmp = sorted(self.points2, key=itemgetter(i + 1), reverse=False)
            '''
            # rm from points2 thee first of the adjoint items representing already used pairs
            toPrune = []    # positions of the items to be removed from the list
            for seq, item1 in enumerate(tmp):
                if seq == len(tmp) - 1:
                    break   # the last item has no next to check
                item2 = tmp[seq + 1]
                id1 = item1[0]
                id2 = item2[0]
                pass
                if self.chk([id1, id2]):
                    toPrune.insert(0, seq)   # remove the first item from the list (removing from the end)
                pass
            for seq in toPrune:
                tmp.pop(seq)
            '''
            self.solSort.append(tmp)

        n_sol = len(self.sols)
        self.wrkCand = []  # refresh the list before each exploration
        # for seq in range(0, n_sol, 2):  # select every 2nd sol as the base to compare with the previous and the next
        for seq in range(n_sol):  # select every sol as the base to compare with the previous and the next
            base = self.points2[seq]  # base point/solution
            self.mkCand1(base)  # make candidate solution pairs with the currently selected base sol.
        pass
        # select from the wrkCand pairs to be stored in cand{} (to be used for making cubes)
        '''
        for item in self.wrkCand:   # item: [crit_id, pair (either low or upp), diff
            diff = item[2]
            if diff > self.gap:
                pair = item[1]
                pair = self.sortPair(pair)
                self.cand.update({pair: diff})
                pass
            pass
        '''
        for pair, val in self.wrkPairs.items():
            val = self.dist(pair)  # L^inf distance between the sol-pair
            self.wrkPairs.update({pair: val})
            if val > self.gap:
                is_used = self.chk(pair)
                if not is_used:
                    self.cand.update({pair: val})
                else:
                    # print(f'Neigh::explore(): skipping already used pair {pair}.')
                    pass
                pass
            else:  # mark the close-pair as done
                self.done.update({pair: val})
                pass
            pass
        pass
        # raise Exception(f'Neigh::explore() - not implemented yet.')

        '''
            low = self.solSort[0][seq - 1]      # point with smaller achievement
            id_low = low[0]
            id_base = base[0]
            if seq < n_sol - 1:
                upp = self.solSort[0][seq + 1]      # the sol with achievement > the base achievement
                id_upp = upp[0]
            else:
                upp = None
                id_upp = None
                # raise Exception(f'Neigh::find() - the case not implemented yet.')
            pass

            # select either (base, low) or (base, upp) based on the achievement diff in 0-th criterion
            pairLow = [id_base, id_low]
            done = self.chk(pairLow)
            if done:
                diffLow = 0.
            else:
                diffLow = base[1] - low[1]
            if upp is not None:
                pairUpp = [id_base, id_upp]
                done = self.chk(pairUpp)
                if done:
                    diffUpp = 0.
                else:
                    diffUpp = upp[1] - base[1]
                pass
            else:
                diffUpp = 0.
                pairUpp = [None, None]
            if diffLow > diffUpp:
                diff = diffLow
                pair = pairLow
            else:
                diff = diffUpp
                pair = pairUpp
            pass
            print(f'Pair: ({pair[0]}, {pair[1]}), distance {diff:.1f}, crit_id = 0.')
            if dist <  diff:    # distance between neighbors based on the 0-th criterion
                dist = diff
                bestPair = pair
                print(f'Current best pair: ({bestPair[0]}, {bestPair[1]}), distance {dist:.1f}, crit_id = 0.')

            # check achievements of the better neighbors' pair (base, upp) or (base, low) in the remaining criteria
            for i in range(1, self.mc.n_crit):
                found = False
                for seq2 in range(n_sol):   # find the base in the list sorted by i-th criterion
                    cand = self.solSort[i][seq2]
                    if cand[0] == id_base:
                        found = True    # found the base in the list sorted by i-th criterion
                        if seq2 > 0:
                            low = self.solSort[i][seq2 - 1]
                        else:
                            low = None  # the base is the very first in the sorted list
                            # raise Exception(f'Neigh::find() - the case not implemented yet.')
                        pass
                        if seq2 < n_sol - 1:
                            upp = self.solSort[i][seq2 + 1]
                        else:
                            upp = None      # the base is the very last in the sorted list
                            # raise Exception(f'Neigh::find() - the case not implemented yet.')
                        break
                if not found:
                    raise Exception(f'Neigh::find() - the case not implemented yet.')
                pass
                if low is not None:
                    pairLow = [id_base, low[0]]
                    done = self.chk(pairLow)
                    if done:
                        diffLow = 0.
                        pairLow = [None, None]
                    else:
                        diffLow = base[i + 1] - low[i + 1]
                    pass
                else:       # no worse solution (in the sorted list)
                    diffLow = 0.
                    pairLow = [None, None]
                if upp is not None:
                    pairUpp = [id_base, upp[0]]
                    done = self.chk(pairUpp)
                    if done:
                        diffUpp = 0.
                        pairUpp = [None, None]
                    else:
                        diffUpp = upp[i + 1] - base[i + 1]
                    pass
                else:       # no better solution (in the sorted list)
                    diffUpp = 0.
                    pairUpp = [None, None]
                if diffLow > diffUpp:
                    diff = diffLow
                    pair = pairLow
                else:
                    diff = diffUpp
                    pair = pairUpp
                pass
                print(f'Crit_id {i}, pair: ({pair[0]}, {pair[1]}), distance {diff:.1f}, crit_id = {i}.')
                if dist < diff:  # distance between neighbors based on the i-th and previous criteria
                    dist = diff
                    bestPair = pair
                    print(f'Current best pair: ({bestPair[0]}, {bestPair[1]}), distance {dist:.1f}, crit_id = {i}.')

                # end of checking the best pair for i-th (and previoudly checked) criterion
                pass
            pass
            '''

        '''
        # most distant neighbors found
        bestPair = self.sortPair(bestPair)
        print(f'Most distant neighbors found, sols_id: ({bestPair[0]}, {bestPair[1]}), distance {dist:.1f}.')
        self.lastPair = (bestPair[0], bestPair[1])
        self.done.update({self.lastPair: dist})
        # raise Exception(f'Neigh::find() - cube creation not implemented yet.')
        '''

    # select a set of neighbors to make pairs with the selected base (a given solution)
    def mkCand1(self, base):
        id_base = base[0]
        for i in range(self.mc.n_crit):
            if self.verbose > 3:
                print(f'------------------------ candidate pairs for base {id_base} and criterion {i}')
            seq2 = 0     # just to avoid the compiler warning
            found = False
            for seq2 in range(len(self.solSort[i])):  # find the base in the list sorted by i-th criterion
                cand = self.solSort[i][seq2]
                if cand[0] == id_base:
                    found = True  # found the base in the list sorted by i-th criterion
                    break
            if not found:
                print(f'------ Neigh::mkCand(): skipping base {id_base} (not in the {i}-th sorted list).')
                # continue      # relevant if solSort are shortened by removing a sol from the already used adjoint pair
                raise Exception(f'Neigh::mkCand() - solution with id {id_base} not found in the sorted list.')
            pass
            lows = []       # alternative low achievements for the base
            k = seq2 - 1    # index of points having worse (than the base) achievements
            is_first = True
            achFirst = None
            while k >= 0:
                low = self.solSort[i][k]
                ach = low[i + 1]
                if is_first:
                    is_first = False
                    achFirst = ach
                else:
                    diff = abs(achFirst - ach)
                    if diff > self.achDiff:     # alternative low achievements with similar achievements
                        break   # don't check points with worse achievements than that found
                lows.append(low)
                k -= 1
                pass
            pass

            upps = []       # alternative better-achievement pairs for the base
            k = seq2 + 1    # index of points having better (than the base) achievements
            is_first = True
            achFirst = None
            while k < len(self.solSort[i]):
                upp = self.solSort[i][k]
                ach = upp[i + 1]
                if is_first:
                    is_first = False
                    achFirst = ach
                else:
                    diff = abs(achFirst - ach)
                    if diff > self.achDiff:     # alternative upp-achievements with similar achievements
                        break   # don't check points with better achievements than that found
                upps.append(upp)
                k += 1
                pass
            pass

            # store pairs composed of the base and either worse or better achievements
            for low in lows:
                pairLow = [id_base, low[0]]
                done = self.chk(pairLow)
                if done:
                    continue
                diffLow = base[i + 1] - low[i + 1]
                self.wrkCand.append([i, pairLow, diffLow])
                pair = self.sortPair(pairLow)
                self.wrkPairs.update({(pair[0], pair[1]): diffLow})   # to overwrite the pair duplicate
                if self.verbose > 3:
                    print(f'Crit_id {i}, base_id {id_base}, pairLow: ({pairLow[0]}, {pairLow[1]}), dist. {diffLow:.1f}')
                pass
            for upp in upps:
                pairUpp = [id_base, upp[0]]
                done = self.chk(pairUpp)
                if done:
                    continue
                diffUpp = upp[i + 1] - base[i + 1]
                self.wrkCand.append([i, pairUpp, diffUpp])
                pair = self.sortPair(pairUpp)
                self.wrkPairs.update({(pair[0], pair[1]): diffUpp})   # to overwrite the pair duplicate
                if self.verbose > 3:
                    print(f'Crit_id {i}, base_id {id_base}, pairUpp: ({pairUpp[0]}, {pairUpp[1]}), dist. {diffUpp:.1f}')
                pass
            pass
            # end of computing achievement diffs for the i-th criterion between the base and
            # the immediately worse and better sols (low and upp, respectively)
        pass

        '''
            if diffLow > diffUpp:
                diff = diffLow
                pair = pairLow
            else:
                diff = diffUpp
                pair = pairUpp
            pass
            print(f'Crit_id {i}, pair: ({pair[0]}, {pair[1]}), distance {diff:.1f}, crit_id = {i}.')
            if dist < diff:  # distance between neighbors based on the i-th and previous criteria
                dist = diff
                bestPair = pair
                print(f'Current best pair: ({bestPair[0]}, {bestPair[1]}), distance {dist:.1f}, crit_id = {i}.')

            # end of checking the best pair for i-th (and previoudly checked) criterion
            pass
        pass
        '''

"""
Geometry of the ray-structured expansion (cfg: expandMode: rays); three criteria, i.e. a 2-D diagonal projection.

The ray-structured expansion uses the diagonal probes of the expansion only to discover the outline of the
Pareto front outside the region covered by the previous stages; the regions found in this way (pockets) are
then filled by rays of cuboids, as in the grid option of the SPFR:

* pocket   : a region between the convex hull H0 of the projected PFR at the start of the expansion and the
             hull H1 after the discovery; it is bounded by two chains with common end points: the new chain
             (vertices of H1 outside H0; any number of them) and the old chain (vertices of H0);
* chain ray: the segment between two consecutive vertices of a chain; filled by cuboids defined by pairs of
             consecutive solutions on the ray (as the envelope of the grid option);
* sweep ray: the segment between a solution of one (filled) chain and the solution of the other chain at the
             same relative arc length (as the internal rays of the grid option; the pairing by the arc length
             handles chains with different numbers of solutions).
"""
import numpy as np
from scipy.spatial import ConvexHull


def hull_ccw(W, ids):
    """Ids of the vertices of the convex hull of the 2-D points W (rows correspond to ids), counterclockwise.
    Degenerate (collinear) point sets: the two extreme points."""
    W = np.asarray(W, float)
    ids = list(ids)
    if len(W) < 3:
        return ids
    try:
        h = ConvexHull(W)
        return [ids[i] for i in h.vertices]     # counterclockwise for 2-D hulls
    except Exception:
        c = W - W.mean(axis=0)
        d = np.linalg.svd(c)[2][0]              # main direction of the (collinear) points
        t = c @ d
        return [ids[int(np.argmin(t))], ids[int(np.argmax(t))]]


def seg_param(p, a, b):
    d = b - a
    return float((p - a) @ d / max(d @ d, 1e-18))


def seg_dist(p, a, b):
    t = min(max(seg_param(p, a, b), 0.0), 1.0)
    return float(np.linalg.norm(p - (a + t * (b - a))))


def outward_normal(a, b):
    """Outward unit normal of the edge a -> b of a counterclockwise polygon."""
    d = b - a
    n = np.array([d[1], -d[0]])
    return n / max(np.linalg.norm(n), 1e-18)


def simplify_closed(P, ids, tol):
    """Remove vertices of a closed polygon that are closer than tol to the chord of their neighbours."""
    P = [np.asarray(p, float) for p in P]
    ids = list(ids)
    while len(ids) > 3:
        n = len(ids)
        d = [seg_dist(P[i], P[i - 1], P[(i + 1) % n]) for i in range(n)]
        i = int(np.argmin(d))
        if d[i] >= tol:
            break
        del P[i]
        del ids[i]
    return P, ids


def arc_length(P):
    """Normalized cumulative arc length of the polyline P."""
    P = np.asarray(P, float)
    if len(P) < 2:
        return np.zeros(len(P))
    s = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    return s / max(s[-1], 1e-18)


def cyclic_runs(flags):
    """Maximal runs of True in a cyclic list; each run as a list of indices (in cyclic order)."""
    n = len(flags)
    if n == 0 or all(flags) or not any(flags):
        return [] if not all(flags) or n == 0 else [list(range(n))]
    start = next(i for i in range(n) if not flags[i])     # start the scan at a False element
    runs, cur = [], []
    for j in range(1, n + 1):
        i = (start + j) % n
        if flags[i]:
            cur.append(i)
        elif cur:
            runs.append(cur)
            cur = []
    if cur:
        runs.append(cur)
    return runs

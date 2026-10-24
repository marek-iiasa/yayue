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
             nearest relative length along the chain (as the internal rays of the grid option; the pairing by the
             length handles chains with different numbers of solutions).

Distances compared with rho are Chebyshev (L-inf) distances in the achievement space.  Distances between
solutions (gaps, lengths along the chains: arc_length_inf) are the L-inf distances of the points; questions about
the outline seen along the diagonal (is a solution on a segment of the outline, how far outside it is) use the
L-inf distance between the diagonal lines through the points (qdist, seg_dist_q), i.e. the L-inf distance modulo
the diagonal: min_s ||p - q - s 1||_inf = (max_i d_i - min_i d_i) / 2, d = p - q.  The height along the diagonal
is ignored there, as in the projection (the PF boundary between two vertices of the outline need not be straight
in the achievement space).  No Euclidean distance is used; the 2-D projection only gives the convex hull, the side
of a segment (outward_normal: a direction) and the order of points along a segment (seg_param).
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


def seg_dist_inf(p, a, b):
    """Chebyshev (L-inf) distance of the point p from the segment [a, b] (achievement space, any dimension).
    f(t) = max_i |p_i - a_i - t d_i| is convex and piecewise linear; its minimum over [0, 1] is attained at an
    end point, at a zero of one term or where two terms are equal."""
    p, a, b = (np.asarray(x, float) for x in (p, a, b))
    e, d = p - a, b - a
    cand = [0.0, 1.0]
    k = len(e)
    for i in range(k):
        if abs(d[i]) > 1e-15:
            cand.append(e[i] / d[i])
        for j in range(i + 1, k):
            for s in (1.0, -1.0):           # e_i - t d_i = s (e_j - t d_j)
                den = d[i] - s * d[j]
                if abs(den) > 1e-15:
                    cand.append((e[i] - s * e[j]) / den)
    return float(min(np.max(np.abs(e - t * d)) for t in cand if 0.0 <= t <= 1.0))


def qnorm(d):
    """L-inf norm modulo the diagonal: min_s ||d - s 1||_inf = (max_i d_i - min_i d_i) / 2."""
    d = np.asarray(d, float)
    return float(0.5 * (np.max(d) - np.min(d)))


def qdist(p, q):
    """L-inf distance between the diagonal lines through the points p and q (achievement space)."""
    return qnorm(np.asarray(p, float) - np.asarray(q, float))


def qdual(g):
    """Dual of qnorm for a direction g with sum(g) = 0 (g = Q^T nrm): sup g.d / qnorm(d) = ||g||_1.  A point at the
    Euclidean (projection) distance s from a hyperplane with the unit normal nrm is at the L-inf distance modulo the
    diagonal s / qdual(Q^T nrm) from it."""
    return float(max(np.sum(np.abs(np.asarray(g, float))), 1e-12))


def seg_dist_q(p, a, b):
    """L-inf distance modulo the diagonal of the point p from the segment [a, b]: the L-inf distance between the
    diagonal line through p and the strip {a + t (b - a) + s 1, t in [0, 1]}.  g(t) = qnorm(p - a - t (b - a)) is
    convex and piecewise linear; its minimum over [0, 1] is attained at an end point or where two components of
    p - a - t (b - a) are equal."""
    p, a, b = (np.asarray(x, float) for x in (p, a, b))
    e, d = p - a, b - a
    cand = [0.0, 1.0]
    k = len(e)
    for i in range(k):
        for j in range(i + 1, k):
            den = d[i] - d[j]
            if abs(den) > 1e-15:
                cand.append((e[i] - e[j]) / den)
    return float(min(qnorm(e - t * d) for t in cand if 0.0 <= t <= 1.0))


def arc_length_inf(Y):
    """Normalized cumulative length of the polyline Y measured by the Chebyshev (L-inf) distances of
    consecutive points (achievement space)."""
    Y = np.asarray(Y, float)
    if len(Y) < 2:
        return np.zeros(len(Y))
    s = np.r_[0.0, np.cumsum(np.max(np.abs(np.diff(Y, axis=0)), axis=1))]
    return s / max(s[-1], 1e-18)


def outward_normal(a, b):
    """Outward normal of the edge a -> b of a counterclockwise polygon (a direction; its length is irrelevant)."""
    d = b - a
    n = np.array([d[1], -d[0]])
    return n / max(np.linalg.norm(n), 1e-18)


def simplify_closed(P, ids, tol, dist=None):
    """Remove vertices of a closed polygon that are closer than tol to the chord of their neighbours.
    dist(p, a, b): distance of p from the segment [a, b] (default: seg_dist_q, the L-inf distance modulo the
    diagonal; the points P are achievement vectors)."""
    P = [np.asarray(p, float) for p in P]
    ids = list(ids)
    dist = seg_dist_q if dist is None else dist
    while len(ids) > 3:
        n = len(ids)
        d = [dist(P[i], P[i - 1], P[(i + 1) % n]) for i in range(n)]
        i = int(np.argmin(d))
        if d[i] >= tol:
            break
        del P[i]
        del ids[i]
    return P, ids


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

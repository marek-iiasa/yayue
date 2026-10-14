"""
Geometry of the expansion stage (no Pyomo dependency; NumPy/SciPy only).

All functions work in the achievement space of the current Utopia/Nadir (0 at Nadir, 100 at
Utopia, every criterion maximized):

* diagonal projection: w = Q y (Q: orthonormal basis of the plane 1^T y = 0), height h = mean(y),
  y = Q^T w + h 1;
* the Pareto front is the graph of a concave function h(w) over the projected efficient domain;
* certificate of a simplex S of the projected PFR: for every point w of S
      dist(front point at w, E) <= dist(F(w), E) + (U(w) - flat(w)) = beta(w),
  where F(w) is the flat (interpolated) point and U an upper envelope of h:
  the minimum of the supporting hyperplanes given by dual values (variant with duals) or of the
  secant planes of the known points (variant without duals), and the Utopia box y <= 100.
"""
from itertools import combinations
from collections import defaultdict
import numpy as np
from scipy.spatial import cKDTree, Delaunay, ConvexHull


# ----------------------------------------------------------------------------- basics
def basis(k):
    """Orthonormal basis Q ((k-1) x k) of the plane 1^T y = 0."""
    M = np.eye(k) - np.ones((k, k)) / k
    _, _, Vt = np.linalg.svd(M)
    return Vt[:k - 1]


def bary_grid(dim, m):
    """Barycentric coordinates of a regular grid on a dim-simplex with m subdivisions."""
    pts = []
    for c in combinations(range(m + dim), dim):
        prev, lam = -1, []
        for ci in c:
            lam.append(ci - prev - 1)
            prev = ci
        lam.append(m + dim - 1 - prev)
        pts.append(np.array(lam) / m)
    return np.array(pts)


def to_ach(Z, u, n):
    """maximization-oriented criterion values z -> achievements (100 at u, 0 at n)."""
    return 100.0 * (np.asarray(Z, float) - n) / (u - n)


def from_ach(Y, u, n):
    return n + np.asarray(Y, float) * (u - n) / 100.0


def linf(a, b):
    return float(np.max(np.abs(np.asarray(a) - np.asarray(b))))


# ----------------------------------------------------------------------------- hull / triangulation
def hull_facets(W):
    """Facets of the convex hull of the projected points W (n x d).
    Returns a list of (vertex indices, outward unit normal, offset) with normal.w + offset = 0 on
    the facet and > 0 outside.  d = 1 (two criteria) is handled explicitly."""
    W = np.asarray(W, float)
    if W.shape[1] == 1:
        i0, i1 = int(np.argmin(W[:, 0])), int(np.argmax(W[:, 0]))
        return [((i0,), np.array([-1.0]), float(W[i0, 0])),
                ((i1,), np.array([1.0]), -float(W[i1, 0]))]
    try:
        hull = ConvexHull(W)
    except Exception:                       # degenerate (e.g. collinear) point sets
        hull = ConvexHull(W, qhull_options='QJ')
    return [(tuple(int(v) for v in s), eq[:-1].copy(), float(eq[-1]))
            for s, eq in zip(hull.simplices, hull.equations)]


def triangulate(W):
    """Simplices (index tuples) of a triangulation of the projected points.  For d = 1 the
    consecutive points (sorted by w) form the intervals."""
    W = np.asarray(W, float)
    if W.shape[1] == 1:
        order = np.argsort(W[:, 0])
        return np.array([[order[i], order[i + 1]] for i in range(len(order) - 1)
                         if W[order[i + 1], 0] - W[order[i], 0] > 1e-9], dtype=int)
    try:
        return Delaunay(W).simplices
    except Exception:
        return Delaunay(W, qhull_options='QJ').simplices


def max_edge(Ys):
    return max(linf(Ys[a], Ys[b]) for a, b in combinations(range(len(Ys)), 2))


# ----------------------------------------------------------------------------- upper envelopes
def box_bound(P):
    """Utopia box y <= 100 gives h <= 100 - max_i (Q^T w)_i; P = Q^T w (rows)."""
    return 100.0 - P.max(axis=1)


def tangent_envelope(P, TL, TB):
    """Upper bound on the height from the tangents lam.y <= b (rows of TL, TB): with y = P + h 1,
    h <= (b - lam.P) / sum(lam).  P = Q^T w (rows).  Includes the Utopia box."""
    U = box_bound(P)
    if len(TB):
        U = np.minimum(U, ((TB[None, :] - P @ TL.T) / TL.sum(axis=1)[None, :]).min(axis=1))
    return U


class SecantEnvelope:
    """Upper envelope of h from the known front points K only (variant without dual values).

    Concavity of h: for a simplex T of the triangulation of K and a vertex q of T, the secant
    (hyper)plane of T bounds h from above in the cone opposite to T at q, i.e. at locations w with
    w - w_q = sum_j a_j (w_q - w_j), a_j >= 0 (j: the other vertices of T)."""

    def __init__(self, YK, Q):
        self.Y = np.asarray(YK, float)
        self.Q = Q
        self.W = self.Y @ Q.T
        self.H = self.Y.mean(axis=1)
        self.simplices = triangulate(self.W)
        self.fan = defaultdict(list)
        planes = []
        for t, simp in enumerate(self.simplices):
            A = np.hstack([self.W[simp], np.ones((len(simp), 1))])
            planes.append(np.linalg.lstsq(A, self.H[simp], rcond=None)[0])   # h ~ c.w + c0
            for v in simp:
                self.fan[int(v)].append(t)
        self.planes = np.array(planes) if planes else np.zeros((0, self.W.shape[1] + 1))

    def envelope(self, Wg, verts):
        """U(w) at the locations Wg (n x d) inside the simplex with K-vertex indices verts."""
        U = box_bound(Wg @ self.Q)
        for q in verts:
            wq = self.W[q]
            dirs = wq - Wg
            for t in self.fan[int(q)]:
                others = [v for v in self.simplices[t] if v != q]
                M = (self.W[others] - wq).T
                try:
                    a = np.linalg.solve(M, dirs.T).T
                except np.linalg.LinAlgError:
                    continue
                ok = np.all(a >= -1e-9, axis=1)
                if ok.any():
                    pl = self.planes[t]
                    U[ok] = np.minimum(U[ok], Wg[ok] @ pl[:-1] + pl[-1])
        return U


# ----------------------------------------------------------------------------- certificates
def simplex_bound(Ys, G, tree, Q, TL=None, TB=None, secant=None, verts=None):
    """Pointwise bound beta = dist(F, E) + max(U - flat, 0) on the barycentric grid G of the
    simplex with vertices Ys (achievements), plus the sampling correction 2 * edge / m.
    U from the tangents (TL, TB) or, if `secant` is given, from the secant envelope.
    Returns (bound, distance part, band part, barycentric coordinates of the worst point)."""
    F = G @ Ys
    d = tree.query(F, p=np.inf)[0]
    hF = F.mean(axis=1)
    P = F - hF[:, None]
    if secant is None:
        U = tangent_envelope(P, TL if TL is not None else np.zeros((0, Ys.shape[1])),
                             TB if TB is not None else np.zeros(0))
    else:
        U = secant.envelope(F @ Q.T, verts)
    g = np.maximum(U - hF, 0.0)
    m = max(int(round(1.0 / max(G[G > 0].min(), 1e-12))), 1) if (G > 0).any() else 1
    tot = d + g
    i = int(np.argmax(tot))
    return float(tot[i] + 2.0 * max_edge(Ys) / m), float(d[i]), float(g[i]), G[i]


def nn_distances(Y):
    """L-inf distance of every point to its nearest neighbour."""
    if len(Y) < 2:
        return np.zeros(len(Y)), np.zeros(len(Y), dtype=int)
    d, j = cKDTree(Y).query(Y, k=2, p=np.inf)
    return d[:, 1], j[:, 1]

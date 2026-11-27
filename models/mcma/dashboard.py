"""
Interactive HTML dashboard of a pyMCMA analysis: 2D projections and a 3D plot of the Pareto-front
representation (criteria achievements, as in mcma plots) linked with a scrollable table of parFront.csv.

Self-contained module: depends only on pandas, plotly and yaml (already required by mcma) and does not import
anything else from mcma, so it can also be used without running an analysis (analizy/manage.py --dashboard).
The page is a single static HTML file; plotly.js is loaded from a shared local file (if given and present) and
otherwise from the plotly CDN (the version matching the installed plotly package).

Used by mcma (report.py) at the end of an analysis, when the analysis config has:
    dashboard: True                     # write <resDir>dashboard.html
    dashboardJs: ../plotly.min.js       # (default) shared plotly.js, path relative to the analysis folder;
                                        # written if missing or of another version; False: CDN only

Usage outside of mcma (from the models/ directory):
    from mcma.dashboard import Dashboard, prepare_plotlyjs
    js = prepare_plotlyjs('mcma/analizy/plotly.min.js')     # None (CDN) if the file cannot be written
    Dashboard.from_dir('mcma/analizy/pipa10er').write(plotlyjs=js)
"""
import errno
import html
import json
import math
import os
import re
from pathlib import Path

import pandas as pd
import plotly
import plotly.graph_objects as go
import yaml

__all__ = ['Dashboard', 'write_plotlyjs', 'prepare_plotlyjs', 'plotlyjs_version', 'subtitle', 'DASHBOARD',
           'PLOTLYJS_DEFAULT']

DASHBOARD = 'dashboard.html'
PLOTLYJS = 'plotly.min.js'
PLOTLYJS_DEFAULT = f'../{PLOTLYJS}'     # default of the option dashboardJs (shared by analyses in one folder)
CDN = 'https://cdn.plot.ly/plotly-{ver}.min.js'

# origin of a solution (column 'origin' of parFront.csv) -> marker colour; order = legend order
ORIGIN_COLORS = {
    'corner': '#222222', 'neutral': '#9467bd', 'cube': '#1f77b4', 'other': '#7f7f7f',
    'discover': '#ff7f0e', 'ray': '#2ca02c', 'promoted': '#17becf', 'boundary': '#a65628',
    'interior': '#8c564b', 'coverage': '#e377c2', 'gap': '#bcbd22'}
EXTRA_COLORS = ['#393b79', '#637939', '#8c6d31', '#843c39', '#7b4173', '#3182bd', '#e6550d', '#31a354']
NO_ORIGIN = 'solution'      # group name when parFront.csv has neither 'origin' nor 'parents' column
# no 'origin' column: a solution with two parents ('[itr_id, itr_id]') comes from a cube, without them ('[none]')
# it is taken as a corner (approximation: also a neutral solution has no parents)
ORIGIN_FROM_PARENTS = {True: 'cube', False: 'corner'}

# cuboid view: solutions generated from the cuboid H(r, a) spanned by their two parents (column 'parents')
CUBOID_ORIGINS = ('cube', 'gap')    # 'gap' with parents = probe in the cuboid of a pair (rays mode); else [none]
MAX_SPLIT_DIM = 4                   # the 2^k sub-cuboids are drawn only for k <= MAX_SPLIT_DIM criteria
BOX_TOL = 0.01                      # tolerance of 'point in a box' (achievements in parFront.csv have 2 decimals)


# ------------------------------------------------------------------------------------------- plotly.js file
def plotlyjs_version():
    """Version of plotly.js bundled with the installed plotly package (used also for the CDN URL)."""
    return plotly.offline.get_plotlyjs_version()


def write_plotlyjs(path):
    """Write the plotly.js bundle to path, unless the file already holds the same version.
    Returns True if the file was (re)written. The file is replaced atomically (analyses run in parallel may
    write the same shared file)."""
    path = Path(path)
    ver = plotlyjs_version()
    if path.is_file():
        with open(path, encoding='utf-8', errors='replace') as f:
            head = f.read(300)
        if f'plotly.js v{ver}' in head:
            return False
    tmp = path.with_name(f'.{path.name}.{os.getpid()}.tmp')
    try:
        tmp.write_text(plotly.offline.get_plotlyjs(), encoding='utf-8')
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()
    return True


def prepare_plotlyjs(path):
    """Shared plotly.js for dashboards: path (written if missing or of another version), or None (CDN) if path
    is empty or the file cannot be written."""
    if not path:
        return None
    try:
        write_plotlyjs(path)
    except OSError as e:
        print(f'Dashboard: cannot write plotly.js to "{path}" ({e}); the CDN will be used.')
        return None
    return Path(path)


# ------------------------------------------------------------------------------------------- analysis files
def _read_yaml(path):
    with open(path, encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


def analysis_cfg(ana_dir):
    """Options of an analysis merged as by mcma: defaults (or ../Sys/cfg_sys.yml), then cfg.yml (or the file
    named in cfg.txt). Paths in the options are relative to ana_dir."""
    ana_dir = Path(ana_dir)
    sys_cfg = ana_dir / '..' / 'Sys' / 'cfg_sys.yml'
    data = _read_yaml(sys_cfg) if sys_cfg.is_file() else \
        {'resDir': 'Results/', 'mxIter': 1000, 'showPlot': True, 'neutral': True, 'verb': 0}
    usr = ana_dir / 'cfg.yml'
    loc = ana_dir / 'cfg.txt'
    if loc.is_file():
        words = loc.read_text().split()
        if len(words) == 1:
            usr = ana_dir / words[0]
    if not usr.is_file():
        raise FileNotFoundError(f'no analysis config {usr}')
    data.update(_read_yaml(usr))
    return data


def subtitle(cfg):
    """Short description of the analysis options shown next to the title (cfg: dict-like with get())."""
    sub = []
    if cfg.get('mxGap') is not None:
        sub.append(f'mxGap {cfg.get("mxGap")}')
    if cfg.get('grid'):
        sub.append('grid')
    if cfg.get('expand'):
        sub.append(f'expand ({cfg.get("expandMode") or "cert"})')
    return ', '.join(sub)


def results_dir(ana_dir, cfg=None):
    """Directory with results of the analysis (resDir[/run_id], relative to ana_dir)."""
    cfg = analysis_cfg(ana_dir) if cfg is None else cfg
    res = Path(ana_dir) / str(cfg.get('resDir') or 'Results/')
    if cfg.get('run_id') is not None:
        res = res / str(cfg['run_id'])
    return res


def read_payoff(path):
    """payoff.txt -> {criterion: (utopia, nadir)}; {} if the file is missing."""
    out = {}
    path = Path(path)
    if not path.is_file():
        return out
    for line in path.read_text().splitlines():
        m = re.match(r'^\s*(\S+)\s+U\s+(\S+)\s+N\s+(\S+)', line)
        if m:
            try:
                out[m.group(1)] = (float(m.group(2)), float(m.group(3)))
            except ValueError:
                pass
    return out


# ------------------------------------------------------------------------------------------- formatting
def _num(v, as_int=False):
    """Number for JSON (None for NaN/inf/missing); as_int: integer columns (e.g. itr_id)."""
    if v is None:
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(f):
        return None
    return int(f) if as_int and f.is_integer() else f


def _fmt(v, as_int=False):
    """Number formatting used both in hover labels and (in the page script) in the table."""
    f = _num(v, as_int)
    if f is None:
        return ''
    if isinstance(f, int):
        return str(f)
    if f == 0:
        return '0'
    return f'{f:.2f}' if 1e-2 <= abs(f) < 1e4 else f'{f:.4e}'


# ------------------------------------------------------------------------------------------- dashboard
class Dashboard:
    """Dashboard of one analysis.

    df:    solutions, one row per solution, with columns: itr_id, <criterion name> (values) and
           a_<criterion name> (achievements, 0-100); optional: origin, parents, domin and any others (shown
           in the table).
    crit:  list of criteria, each a dict: {'name': str, 'sense': 'min'|'max', 'utopia': float, 'nadir': float}
           (utopia and nadir optional; shown in the header).
    """

    def __init__(self, df, crit, title='pyMCMA analysis', subtitle='', out_dir=None):
        self.df = df.reset_index(drop=True).copy()
        self.df = self.df.loc[:, [c for c in self.df.columns if not str(c).startswith('Unnamed')]]
        self.crit = [dict(c) for c in crit]
        self.names = [c['name'] for c in self.crit]
        self.title = title
        self.subtitle = subtitle
        self.out_dir = Path(out_dir) if out_dir is not None else None   # default location of write()
        missing = [c for n in self.names for c in (n, f'a_{n}') if c not in self.df.columns]
        if 'itr_id' not in self.df.columns:
            missing.insert(0, 'itr_id')
        if missing:
            raise ValueError(f'columns missing in the solutions data: {missing}')
        if len(self.names) < 2:
            raise ValueError('at least two criteria are needed')
        if 'origin' not in self.df.columns:     # older mcma (master without expand_rays): derived from parents
            if 'parents' in self.df.columns:
                self.df['origin'] = [ORIGIN_FROM_PARENTS[len(re.findall(r'-?\d+', str(p))) == 2]
                                     for p in self.df['parents']]
            else:
                self.df['origin'] = NO_ORIGIN
        self.df['origin'] = self.df['origin'].fillna('other').astype(str)
        present = list(dict.fromkeys(self.df['origin']))
        self.groups = [g for g in ORIGIN_COLORS if g in present] + sorted(g for g in present if g not in ORIGIN_COLORS)
        extra = iter(EXTRA_COLORS * 10)
        self.colors = {g: ORIGIN_COLORS.get(g) or next(extra) for g in self.groups}
        self.parents = self._parents()
        # number of sub-cuboids drawn by the cuboid view (0: view not available)
        self.n_boxes = 2 ** len(self.names) if len(self.names) <= MAX_SPLIT_DIM and any(self.parents) else 0

    def _parents(self):
        """Per row: row indices [i, j] of the two parents of a solution generated from their cuboid (origin in
        CUBOID_ORIGINS and column 'parents' = '[itr_id, itr_id]' with both parents present), else None."""
        if 'parents' not in self.df.columns:
            return [None] * len(self.df)
        pos = {}
        for k, v in enumerate(self.df['itr_id']):
            f = _num(v, True)
            if f is not None:
                pos.setdefault(int(f), k)
        out = []
        for k, (org, par) in enumerate(zip(self.df['origin'], self.df['parents'])):
            res = None
            if org in CUBOID_ORIGINS:
                ids = re.findall(r'-?\d+', str(par))
                if len(ids) == 2:
                    rows = [pos.get(int(x)) for x in ids]
                    if None not in rows and k not in rows and rows[0] != rows[1]:
                        res = rows
            out.append(res)
        return out

    # ----------------------------------------------------------------------------------- construction
    @classmethod
    def from_dir(cls, ana_dir, title=None):
        """Read the analysis in ana_dir: cfg.yml (crit_def, resDir, run_id, payoff), parFront.csv, payoff.txt."""
        ana_dir = Path(ana_dir)
        cfg = analysis_cfg(ana_dir)
        res = results_dir(ana_dir, cfg)
        f_pf = res / 'parFront.csv'
        if not f_pf.is_file():
            raise FileNotFoundError(errno.ENOENT, 'no results file (parFront.csv)', str(f_pf))
        crit_def = cfg.get('crit_def')
        if not crit_def:
            raise ValueError(f'{ana_dir}: crit_def missing in the config')
        payoff = read_payoff(ana_dir / str(cfg.get('payoff', 'payoff.txt')))
        crit = []
        for cd in crit_def:
            name, sense = str(cd[0]), str(cd[1]).lower()
            u, n = payoff.get(name, (None, None))
            crit.append({'name': name, 'sense': sense, 'utopia': u, 'nadir': n})
        df = pd.read_csv(f_pf)
        return cls(df, crit, title=title or ana_dir.resolve().name, subtitle=subtitle(cfg), out_dir=res)

    # ----------------------------------------------------------------------------------- figures
    def _hover(self):
        out = []
        for _, r in self.df.iterrows():
            lines = [f'<b>itr {_fmt(r["itr_id"], True)}</b> ({html.escape(r["origin"])})']
            for c in self.crit:
                n = c['name']
                lines.append(f'{html.escape(n)}: {_fmt(r[n])}  (a = {_fmt(r[f"a_{n}"])})')
            out.append('<br>'.join(lines))
        return out

    def _range(self, i):
        a = pd.to_numeric(self.df[f'a_{self.names[i]}'], errors='coerce')
        lo = min(0.0, float(a.min())) if a.notna().any() else 0.0
        hi = max(100.0, float(a.max())) if a.notna().any() else 100.0
        pad = 0.04 * (hi - lo)
        return [lo - pad, hi + pad]

    def _label(self, i):
        c = self.crit[i]
        return f"{c['name']} ({c['sense']})"

    def _traces(self, axes, three_d, legend):
        hover = self._hover()
        coords = [pd.to_numeric(self.df[f'a_{self.names[i]}'], errors='coerce') for i in axes]
        traces = []
        for g in self.groups:
            idx = [int(k) for k in self.df.index[self.df['origin'] == g]]
            corner = g == 'corner'
            marker = dict(color=self.colors[g], size=(7 if corner else 4) if three_d else (10 if corner else 7),
                          symbol='diamond' if corner else 'circle', opacity=0.9,
                          line=dict(width=0.5 if not three_d else 0, color='white'))
            kw = dict(x=[_num(coords[0][k]) for k in idx], y=[_num(coords[1][k]) for k in idx],
                      mode='markers', name=g, legendgroup=g, showlegend=legend, marker=marker,
                      customdata=idx, text=[hover[k] for k in idx], hovertemplate='%{text}<extra></extra>')
            if three_d:
                kw['z'] = [_num(coords[2][k]) for k in idx]
                traces.append(go.Scatter3d(**kw))
            else:
                traces.append(go.Scattergl(**kw))
        # overlay traces (filled by the page script, found there by name): the lasso selection, the cuboid view
        # (outline of the parent cuboid, outlines of its sub-cuboids, points in the sub-cuboids, the two parents)
        # and the current solution (drawn last, on top)
        def add(name, mode, marker=None, line=None, hover=False):
            kw = dict(x=[], y=[], mode=mode, name=name, showlegend=False, customdata=[])
            if marker is not None:
                kw['marker'] = marker
            if line is not None:
                kw['line'] = line
            if hover:
                kw.update(text=[], hovertemplate='%{text}<extra></extra>')
            else:
                kw['hoverinfo'] = 'skip'
            traces.append(go.Scatter3d(z=[], **kw) if three_d else go.Scattergl(**kw))

        add('selection', 'markers', marker=dict(size=9 if three_d else 12, symbol='circle-open', color='#111111',
                                                line=dict(width=2, color='#111111')))
        if self.n_boxes:
            add('cuboid', 'lines', line=dict(color='#000000', width=6 if three_d else 2.2))
            for b in range(self.n_boxes):
                add(f'box{b}', 'lines', line=dict(color='#888888', width=3 if three_d else 1.4))
            add('subpts', 'markers', hover=True,
                marker=dict(size=6 if three_d else 9, color=[], opacity=1.0,
                            line=dict(width=0.5 if not three_d else 0, color='white')))
            add('parents', 'markers', hover=True,
                marker=dict(size=9 if three_d else 13, symbol='square-open', color='#000000',
                            line=dict(width=2, color='#000000')))
        add('current', 'markers', marker=dict(size=14 if three_d else 20, symbol='circle-open', color='#e41a1c',
                                              line=dict(width=4, color='#e41a1c')))
        return traces

    def figures(self):
        """[(axes, figure), ...] for the 2D projections, and (axes, figure) of the 3D plot (None if n_crit != 3)."""
        n = len(self.names)
        three = n == 3
        figs2d = []
        pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
        for k, (i, j) in enumerate(pairs):
            fig = go.Figure(self._traces((i, j), False, legend=not three and k == 0))
            fig.update_layout(
                template='plotly_white', margin=dict(l=55, r=10, t=10, b=45), dragmode='lasso',
                xaxis=dict(title=dict(text=self._label(i)), range=self._range(i), zeroline=False),
                yaxis=dict(title=dict(text=self._label(j)), range=self._range(j), zeroline=False),
                legend=dict(orientation='h', x=0, y=1.0, yanchor='bottom'), uirevision='keep',
                hoverlabel=dict(align='left'), clickmode='event')
            figs2d.append(((i, j), fig))
        fig3d = None
        if three:
            fig = go.Figure(self._traces((0, 1, 2), True, legend=True))

            def ax(i):
                return dict(title=dict(text=self._label(i)), range=self._range(i), backgroundcolor='white',
                            gridcolor='#dddddd', showbackground=True)
            fig.update_layout(
                template='plotly_white', margin=dict(l=0, r=0, t=0, b=0), uirevision='keep',
                scene=dict(xaxis=ax(0), yaxis=ax(1), zaxis=ax(2), aspectmode='cube'),
                legend=dict(orientation='h', x=0, y=1.0, yanchor='top', itemsizing='constant'),
                hoverlabel=dict(align='left'))
            fig3d = ((0, 1, 2), fig)
        return figs2d, fig3d

    # ----------------------------------------------------------------------------------- table data
    def _table(self):
        first = ['itr_id', 'origin']
        crit_cols = self.names + [f'a_{n}' for n in self.names]
        rest = [c for c in self.df.columns if c not in first + crit_cols]
        cols = first + crit_cols + rest
        kinds, labels, tips = [], [], []
        sense = {c['name']: c['sense'] for c in self.crit}
        for c in cols:
            if pd.api.types.is_integer_dtype(self.df[c]) or pd.api.types.is_bool_dtype(self.df[c]):
                kinds.append('int')
            elif pd.api.types.is_numeric_dtype(self.df[c]):
                kinds.append('num')
            else:
                kinds.append('str')
            labels.append(str(c))
            if c in sense:
                tips.append(f'{c}: criterion value ({sense[c]})')
            elif str(c).startswith('a_') and str(c)[2:] in sense:
                tips.append(f'{str(c)[2:]}: achievement (0 = Nadir, 100 = Utopia)')
            else:
                tips.append(str(c))
        rows = []
        for _, r in self.df.iterrows():
            rows.append([_num(r[c], k == 'int') if k != 'str' else ('' if pd.isna(r[c]) else str(r[c]))
                         for c, k in zip(cols, kinds)])
        coords = [[_num(v) for v in pd.to_numeric(self.df[f'a_{n}'], errors='coerce')] for n in self.names]
        return {'cols': labels, 'kinds': kinds, 'tips': tips, 'rows': rows,
                'origin': list(self.df['origin']), 'coords': [list(t) for t in zip(*coords)],
                'origin_col': cols.index('origin')}

    # ----------------------------------------------------------------------------------- page
    def html(self, plotlyjs=None, out_dir=None):
        """HTML of the dashboard. plotlyjs: path of a shared plotly.min.js (relative link computed from out_dir,
        the directory of the page); the CDN is used when it is None or the file cannot be loaded."""
        figs2d, fig3d = self.figures()
        plots = [{'id': f'p2d{k}', 'axes': list(axes), 'is3d': False, 'fig': json.loads(fig.to_json())}
                 for k, (axes, fig) in enumerate(figs2d)]
        if fig3d is not None:
            plots.append({'id': 'p3d', 'axes': list(fig3d[0]), 'is3d': True, 'fig': json.loads(fig3d[1].to_json())})
        data = {'groups': self.groups, 'colors': self.colors, 'plots': plots, 'table': self._table(),
                'cube': {'nb': self.n_boxes, 'tol': BOX_TOL, 'parents': self.parents,
                         'hover': self._hover() if self.n_boxes else [],
                         'max_dim': MAX_SPLIT_DIM, 'origins': list(CUBOID_ORIGINS)}}
        js_data = json.dumps(data, separators=(',', ':'), allow_nan=False).replace('</', '<\\/')

        local = ''
        if plotlyjs is not None:
            base = Path(out_dir) if out_dir is not None else Path('.')
            try:
                local = os.path.relpath(Path(plotlyjs).resolve(), base.resolve()).replace(os.sep, '/')
            except ValueError:      # e.g. another drive on Windows
                local = Path(plotlyjs).resolve().as_uri()
        cdn = CDN.format(ver=plotlyjs_version())

        n = len(self.names)
        layout_cls = 'n3 no2d' if n == 3 else ('n2' if n == 2 else 'many')   # n3: 2D plots hidden by default
        divs2d = '\n'.join(f'<div class="dplot" id="{p["id"]}"></div>' for p in plots if not p['is3d'])
        div3d = '<div class="dplot" id="p3d"></div>' if fig3d is not None else ''
        toggle = ('<label class="sw-lab" title="Show/hide the 2D projections (hidden: the 3D plot takes their '
                  'space)"><input type="checkbox" class="switch" id="tog2d" autocomplete="off"> 2D plots</label>'
                  if fig3d is not None else '')

        counts = self.df['origin'].value_counts()
        info = f'{len(self.df)} solutions: ' + ', '.join(
            f'<span class="dot" style="background:{self.colors[g]}"></span>{html.escape(g)} {counts[g]}'
            for g in self.groups)
        un = []
        for c in self.crit:
            u, nd = c.get('utopia'), c.get('nadir')
            if u is not None and nd is not None:
                un.append(f'<b>{html.escape(c["name"])}</b> ({c["sense"]}): U {u:.4g}, N {nd:.4g}')
        un_html = ' &nbsp;·&nbsp; '.join(un)
        sub = f' <span class="sub">{html.escape(self.subtitle)}</span>' if self.subtitle else ''

        return (PAGE.replace('{{TITLE}}', html.escape(self.title))
                .replace('{{SUB}}', sub)
                .replace('{{INFO}}', info)
                .replace('{{UN}}', un_html)
                .replace('{{LAYOUT}}', layout_cls)
                .replace('{{DIVS2D}}', divs2d)
                .replace('{{DIV3D}}', div3d)
                .replace('{{TOGGLE2D}}', toggle)
                .replace('{{LOCAL}}', json.dumps(local))
                .replace('{{CDN}}', json.dumps(cdn))
                .replace('{{DATA}}', js_data))

    def write(self, path=None, plotlyjs=None):
        """Write the dashboard; default path: <results dir>/dashboard.html (set by from_dir) or ./dashboard.html."""
        if path is None:
            path = (self.out_dir if self.out_dir is not None else Path('.')) / DASHBOARD
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.html(plotlyjs=plotlyjs, out_dir=path.parent), encoding='utf-8')
        return path


# ------------------------------------------------------------------------------------------- page template
PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{TITLE}} - pyMCMA dashboard</title>
<style>
  :root { --line: #d9d9d9; --muted: #666; --hl: #fde2e2; --head: #f4f4f4; }
  * { box-sizing: border-box; }
  html, body { margin: 0; height: 100%; background: #fff; color: #222;
               font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; font-size: 14px; }
  body { display: flex; flex-direction: column; }
  header { padding: 8px 14px 6px; border-bottom: 1px solid var(--line); }
  h1 { font-size: 18px; margin: 0 0 3px; } h1 .sub { font-weight: normal; color: var(--muted); font-size: 14px; }
  .meta { color: var(--muted); font-size: 12.5px; line-height: 1.6; }
  .dot { display: inline-block; width: 9px; height: 9px; border-radius: 50%; margin: 0 3px 0 6px; }
  main { flex: 1; min-height: 0; display: grid; grid-template-columns: minmax(0, 1fr) minmax(340px, 33%); }
  #plots { min-height: 0; padding: 6px; display: grid; gap: 6px; }
  #plots.n3 { grid-template-rows: minmax(150px, 1fr) minmax(0, 3fr); }   /* 2D row: 1/4 of the height */
  #plots.n3.no2d { grid-template-rows: minmax(0, 1fr); }
  #plots.no2d .row2d { display: none; }
  #plots.n2 { grid-template-rows: minmax(0, 1fr); }
  #plots.many { overflow: auto; grid-auto-rows: 330px; }
  .row2d { display: grid; gap: 6px; grid-template-columns: repeat(3, minmax(0, 1fr)); min-height: 0; }
  #plots.n2 .row2d { grid-template-columns: minmax(0, 1fr); }
  #plots.many .row2d { display: contents; }
  #plots.many { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .dplot { border: 1px solid var(--line); border-radius: 4px; min-height: 0; min-width: 0; height: 100%; }
  aside { min-height: 0; display: flex; flex-direction: column; border-left: 1px solid var(--line); }
  .bar { padding: 6px 10px; display: flex; gap: 8px; align-items: center; flex-wrap: wrap;
         border-bottom: 1px solid var(--line); font-size: 12.5px; }
  .bar .cur { font-weight: 600; } .bar .grow { flex: 1; }
  button { font: inherit; font-size: 12.5px; padding: 2px 8px; border: 1px solid #bbb; border-radius: 4px;
           background: #fafafa; cursor: pointer; } button:disabled { opacity: .45; cursor: default; }
  .hint { color: var(--muted); font-size: 11.5px; padding: 3px 10px 5px; border-bottom: 1px solid var(--line); }
  .wrap { flex: 1; min-height: 0; overflow: auto; position: relative; }
  table { border-collapse: collapse; width: 100%; font-variant-numeric: tabular-nums; font-size: 12.5px; }
  th, td { padding: 3px 7px; border-bottom: 1px solid #eee; white-space: nowrap; text-align: right; }
  td.s, th.s { text-align: left; }
  th { position: sticky; top: 0; background: var(--head); border-bottom: 1px solid var(--line); cursor: pointer;
       user-select: none; z-index: 1; }
  th .arr { color: var(--muted); font-size: 10px; }
  tbody tr { cursor: pointer; } tbody tr:hover { background: #f5f8ff; }
  tbody tr.cur { background: var(--hl); } tbody tr.cur td { font-weight: 600; }
  select { font: inherit; font-size: 12.5px; padding: 1px 4px; max-width: 100%; }
  label.sw-lab { display: inline-flex; align-items: center; gap: 5px; cursor: pointer; }
  input.switch { appearance: none; -webkit-appearance: none; position: relative; flex: none; margin: 0;
                 width: 30px; height: 17px; border-radius: 9px; background: #c4c4c4; cursor: pointer;
                 transition: background .15s; }
  input.switch::before { content: ''; position: absolute; top: 2px; left: 2px; width: 13px; height: 13px;
                         border-radius: 50%; background: #fff; box-shadow: 0 1px 2px rgba(0,0,0,.3);
                         transition: transform .15s; }
  input.switch:checked { background: #1f77b4; }
  input.switch:checked::before { transform: translateX(13px); }
  input.switch:focus-visible { outline: 2px solid #1f77b4; outline-offset: 2px; }
  input.switch:disabled { cursor: default; }
  .cubeinfo { display: none; padding: 4px 10px 6px; border-bottom: 1px solid var(--line); font-size: 12px;
              line-height: 1.55; max-height: 30vh; overflow: auto; }
  .cubeinfo .warn { color: #b03a00; }
  .cubeinfo .it { display: inline-flex; align-items: center; gap: 4px; margin-right: 10px; white-space: nowrap;
                  cursor: pointer; }
  .cubeinfo .it.off { opacity: .35; }
  .cubeinfo .sw { display: inline-block; width: 11px; height: 11px; border-radius: 2px; }
  #err { display: none; margin: 30px; padding: 14px; border: 1px solid #e0a0a0; background: #fff4f4; }
  @media (max-width: 900px) {
    main { display: block; overflow: auto; }
    #plots.n3 { grid-template-rows: auto 420px; }
    #plots.n3.no2d { grid-template-rows: 420px; }
    .row2d, #plots.many { grid-template-columns: minmax(0, 1fr); }
    .row2d .dplot, #plots.many .dplot { height: 320px; }
    #plots.n2 .dplot { height: 420px; }
    aside { border-left: 0; border-top: 1px solid var(--line); height: 75vh; }
  }
</style>
<script>
const DASH = {{DATA}};
</script>
</head>
<body>
<header>
  <h1>{{TITLE}}{{SUB}}</h1>
  <div class="meta">{{INFO}}</div>
  <div class="meta">{{UN}}</div>
</header>
<div id="err"></div>
<main>
  <section id="plots" class="{{LAYOUT}}">
    <div class="row2d">
{{DIVS2D}}
    </div>
    {{DIV3D}}
  </section>
  <aside>
    <div class="bar">
      <span class="cur" id="cur">no solution selected</span><span class="grow"></span>
      <span id="count"></span>
      <button id="clear" disabled>clear selection</button>
    </div>
    <div class="bar" id="cubebar">
      {{TOGGLE2D}}
      <label class="sw-lab" id="cubeLab" title="For a solution generated from a cuboid (origin cube or gap with parents): outline
the cuboid H(r, a) spanned by its parents pj1, pj2 (black), outline its sub-cuboids H(p, v), v = vertices of H(r, a),
and colour the solutions lying in them"><input type="checkbox" class="switch" id="cubeOn" autocomplete="off"> cuboid view</label>
      <select id="subSel" disabled title="Sub-cuboids to show: all, or one pair of opposite sub-cuboids"></select>
    </div>
    <div class="cubeinfo" id="cubeInfo"></div>
    <div class="hint">Click a point or a row to highlight a solution; lasso on a 2D plot filters the table
      (double-click the plot or "clear selection" to reset); legend toggles origins; click a header to sort.</div>
    <div class="wrap" id="wrap"><table><thead><tr id="thead"></tr></thead><tbody id="tbody"></tbody></table></div>
  </aside>
</main>
<script>
(function () {
  'use strict';
  const T = DASH.table, G = DASH.groups, nG = G.length;
  const plots = [];          // {div, axes, is3d}
  const trs = [];            // row index -> <tr>
  const hidden = new Set();  // hidden origin groups
  let current = null;        // row index of the highlighted solution
  let selection = null;      // Set of row indices selected by lasso (null = no filter)
  let sortCol = null, sortDir = 1;

  function fmt(v, kind) {
    if (v === null || v === undefined) return '';
    if (kind !== 'num') return String(v);
    if (v === 0) return '0';
    const a = Math.abs(v);
    return (a >= 1e-2 && a < 1e4) ? v.toFixed(2) : v.toExponential(4).replace(/e([+-])(\d)$/, 'e$10$2');
  }

  // ------------------------------------------------------------------ table
  function buildTable() {
    const head = document.getElementById('thead'), body = document.getElementById('tbody');
    T.cols.forEach((c, j) => {
      const th = document.createElement('th');
      th.className = T.kinds[j] === 'str' ? 's' : '';
      th.title = T.tips[j] + ' (click to sort)';
      th.innerHTML = '';
      th.appendChild(document.createTextNode(c + ' '));
      const arr = document.createElement('span'); arr.className = 'arr'; th.appendChild(arr);
      th.addEventListener('click', () => sortBy(j));
      head.appendChild(th);
    });
    T.rows.forEach((r, i) => {
      const tr = document.createElement('tr');
      r.forEach((v, j) => {
        const td = document.createElement('td');
        if (T.kinds[j] === 'str') td.className = 's';
        if (j === T.origin_col) {
          const d = document.createElement('span'); d.className = 'dot'; d.style.margin = '0 5px 0 0';
          d.style.background = DASH.colors[v] || '#999'; td.appendChild(d);
        }
        td.appendChild(document.createTextNode(fmt(v, T.kinds[j])));
        tr.appendChild(td);
      });
      tr.addEventListener('click', () => setCurrent(i, false));
      trs.push(tr); body.appendChild(tr);
    });
  }

  function sortBy(j) {
    sortDir = (sortCol === j) ? -sortDir : 1; sortCol = j;
    const num = T.kinds[j] !== 'str';
    const idx = T.rows.map((_, i) => i);
    idx.sort((a, b) => {
      let x = T.rows[a][j], y = T.rows[b][j];
      if (x === null || x === '') return 1; if (y === null || y === '') return -1;
      const c = num ? x - y : String(x).localeCompare(String(y), undefined, {numeric: true});
      return (c || a - b) * sortDir;
    });
    const body = document.getElementById('tbody');
    idx.forEach(i => body.appendChild(trs[i]));
    document.querySelectorAll('#thead .arr').forEach((s, k) => { s.textContent = k === j ? (sortDir > 0 ? '▲' : '▼') : ''; });
  }

  function visible(i) { return !hidden.has(T.origin[i]); }

  function filterTable() {
    let n = 0;
    trs.forEach((tr, i) => {
      const show = visible(i) && (!selection || selection.has(i));
      tr.style.display = show ? '' : 'none'; if (show) n++;
    });
    document.getElementById('count').textContent = `${n} of ${trs.length} shown`;
    document.getElementById('clear').disabled = !selection;
  }

  // ------------------------------------------------------------------ cuboid view
  // A solution p generated from the cuboid H(r, a) of its parents pj1, pj2 (r = min, a = max) splits it by the
  // planes y_i = p_i into 2^k sub-cuboids H(p, v), v = vertices of H(r, a).  A vertex is a bit mask: bit d set =
  // coordinate d of v is a_d.  Opposite sub-cuboids (v, complement of v) form a pair; pj1, pj2 are one such pair,
  // a, r another one (unattainable, dominated: no solutions expected there).
  const CB = DASH.cube, NB = CB.nb, K = T.cols.length && T.coords.length ? T.coords[0].length : 0;
  const PAIR_COLORS = [['#1f5fbf', '#7fb0ea'], ['#c62828', '#f4928a'], ['#2e7d32', '#8fd19e'],
    ['#6a3d9a', '#c2a5cf'], ['#8c510a', '#dfc27d'], ['#01665e', '#80cdc1'], ['#b8860b', '#f0d58c']];
  const AR_COLORS = ['#4d4d4d', '#b5b5b5'];
  let cubeOn = false, subChoice = 'par', cube = null, tinted = [], greyed = false;
  const GREY = '#d4d4d4';      // all other solutions while a cuboid is shown (the coloured ones stand out)

  function cubeOf(i) {
    if (!NB || i === null || !CB.parents[i]) return null;
    const [ia, ib] = CB.parents[i], P = T.coords[i], A = T.coords[ia], B = T.coords[ib], tol = CB.tol;
    if ([P, A, B].some(v => v.some(x => x === null))) return null;
    const full = (1 << K) - 1, bits = m => [...Array(K).keys()].map(d => (m >> d) & 1);
    const lo = A.map((x, d) => Math.min(x, B[d])), hi = A.map((x, d) => Math.max(x, B[d]));
    const pc = P.map((x, d) => Math.min(Math.max(x, lo[d]), hi[d]));
    const outside = P.some((x, d) => x < lo[d] - tol || x > hi[d] + tol);
    const m1 = A.reduce((m, x, d) => m | ((x > B[d] ? 1 : 0) << d), 0), m2 = full ^ m1;
    const vert = m => bits(m).map((b, d) => b ? hi[d] : lo[d]);
    const name = m => '(' + bits(m).map(b => b ? 'a' : 'r').join(',') + ')';
    // pairs: pj1/pj2 first, then the other uncharted pairs, a/r last
    const reps = [];
    for (let m = 0; m <= full; m++) if (m < (full ^ m) && m !== Math.min(m1, m2) && m !== 0) reps.push(m);
    const pairs = [{key: 'par', boxes: [m1, m2], cols: PAIR_COLORS[0],
                    label: 'H(p, pj1) + H(p, pj2)'}];
    reps.forEach((m, k) => {
      const a = (m & 1) ? m : full ^ m;      // dark colour: the box whose vertex has criterion 1 at a
      pairs.push({key: 'o' + k, boxes: [a, full ^ a], cols: PAIR_COLORS[(k + 1) % PAIR_COLORS.length],
                  label: `v = ${name(a)} + ${name(full ^ a)}`});
    });
    pairs.push({key: 'ar', boxes: [full, 0], cols: AR_COLORS, label: 'v = a + r (unattainable, dominated)'});
    const box = {};
    pairs.forEach(pr => pr.boxes.forEach((m, k) => {
      const v = vert(m);
      let role = 'uncharted';
      if (m === full) role = 'a, unattainable'; else if (m === 0) role = 'r, dominated';
      else if (m === m1) role = `pj1 = itr ${T.rows[ia][0]}`; else if (m === m2) role = `pj2 = itr ${T.rows[ib][0]}`;
      box[m] = {m: m, color: pr.cols[k], pair: pr.key, lo: pc.map((x, d) => Math.min(x, v[d])),
                hi: pc.map((x, d) => Math.max(x, v[d])), label: `H(p, v), v = ${name(m)}`, role: role, rows: []};
    }));
    // solutions in the parent cuboid -> sub-cuboid (side of each splitting plane)
    T.coords.forEach((y, j) => {
      if (j === i || j === ia || j === ib || y.some(x => x === null)) return;
      if (y.some((x, d) => x < lo[d] - tol || x > hi[d] + tol)) return;
      let m = 0;
      y.forEach((x, d) => {
        const b = hi[d] - lo[d] <= tol ? ((m1 >> d) & 1) : (x > pc[d] ? 1 : 0);
        m |= b << d;
      });
      box[m].rows.push(j);
    });
    const delta = Math.max(...hi.map((x, d) => x - lo[d]));
    return {i: i, ia: ia, ib: ib, lo: lo, hi: hi, outside: outside, pairs: pairs, box: box, delta: delta};
  }

  function shownBoxes(c) {
    if (!c || subChoice === 'none') return [];
    const prs = subChoice === 'all' ? c.pairs : c.pairs.filter(pr => pr.key === subChoice);
    return [].concat(...prs.map(pr => pr.boxes)).map(m => c.box[m]);
  }

  // outline of the box [lo, hi] projected on the axes of a plot: x, y (, z) arrays with null between edges
  function outline(lo, hi, axes) {
    const out = axes.map(() => []);
    const corner = (bs) => axes.map((a, d) => bs[d] ? hi[a] : lo[a]);
    const n = axes.length, nc = 1 << n;
    for (let c = 0; c < nc; c++) for (let d = 0; d < n; d++) {
      if ((c >> d) & 1) continue;
      const p0 = corner([...Array(n).keys()].map(e => (c >> e) & 1));
      const p1 = corner([...Array(n).keys()].map(e => ((c | (1 << d)) >> e) & 1));
      axes.forEach((_, k) => out[k].push(p0[k], p1[k], null));
    }
    return out;
  }

  function cubeInfo() {
    const el = document.getElementById('cubeInfo'), sel = document.getElementById('subSel');
    if (!cubeOn) { el.style.display = 'none'; sel.disabled = true; return; }
    el.style.display = 'block';
    el.textContent = '';
    if (current === null) { el.textContent = 'Select a solution generated from a cuboid (origin ' +
                                             CB.origins.join(' or ') + ').'; sel.disabled = true; return; }
    if (!cube) {
      el.textContent = `itr ${T.rows[current][0]} (${T.origin[current]}) was not generated from a cuboid ` +
                       '(no pair of parents in parFront.csv).';
      sel.disabled = true; return;
    }
    sel.disabled = false;
    const c = cube, it = r => T.rows[r][0];
    const head = document.createElement('div');
    head.innerHTML = `<b>H(r, a)</b> of pj1 = itr ${it(c.ia)}, pj2 = itr ${it(c.ib)} &nbsp; ` +
      `δ = ‖a − r‖<sub>∞</sub> = ${c.delta.toFixed(2)}`;
    el.appendChild(head);
    if (c.outside) {
      const w = document.createElement('div'); w.className = 'warn';
      w.textContent = 'p lies outside H(r, a); it is clipped to the cuboid for the split.';
      el.appendChild(w);
    }
    const g = document.createElement('div'); g.style.color = 'var(--muted)';
    g.textContent = 'Other solutions are greyed; black squares: pj1, pj2. Click an item to show its pair only.';
    el.appendChild(g);
    const shown = new Set(shownBoxes(c).map(b => b.m));
    c.pairs.forEach(pr => {
      const line = document.createElement('div');
      pr.boxes.forEach(m => {
        const b = c.box[m], s = document.createElement('span');
        s.className = 'it' + (shown.has(m) ? '' : ' off');
        s.title = `${b.label} (${b.role}): ${b.rows.length} solution(s); click to show this pair only`;
        s.innerHTML = `<span class="sw" style="background:${b.color}"></span>${name3(b)} ` +
                      `<span style="color:var(--muted)">${b.role}</span> <b>${b.rows.length}</b>`;
        s.addEventListener('click', () => { subChoice = pr.key; fillSelect(); overlay(); });
        line.appendChild(s);
      });
      el.appendChild(line);
    });
  }
  function name3(b) { return b.label.replace('H(p, v), v = ', 'v = '); }

  function fillSelect() {
    const sel = document.getElementById('subSel');
    const opts = [['all', 'all sub-cuboids'], ['none', 'parent cuboid only']];
    if (cube) cube.pairs.forEach(pr => opts.splice(opts.length - 1, 0, [pr.key, pr.label]));
    else opts.splice(1, 0, ['par', 'H(p, pj1) + H(p, pj2)']);
    if (!opts.some(o => o[0] === subChoice)) subChoice = 'all';
    sel.textContent = '';
    opts.forEach(([v, t]) => { const o = document.createElement('option'); o.value = v; o.textContent = t;
                               sel.appendChild(o); });
    sel.value = subChoice;
  }

  function tintTable(c, boxes) {
    tinted.forEach(r => { trs[r].style.boxShadow = ''; });
    tinted = [];
    if (!c) return;
    boxes.forEach(b => b.rows.forEach(r => { trs[r].style.boxShadow = `inset 6px 0 0 ${b.color}`; tinted.push(r); }));
    [c.ia, c.ib].forEach(r => { trs[r].style.boxShadow = 'inset 6px 0 0 #000'; tinted.push(r); });
  }

  // ------------------------------------------------------------------ plots
  function overlay() {
    const sel = selection ? [...selection].filter(visible) : [];
    const cur = (current !== null && visible(current)) ? [current] : [];
    cube = cubeOn ? cubeOf(current) : null;
    if (NB && cube && !cube.pairs.some(pr => pr.key === subChoice) && !['all', 'none'].includes(subChoice))
      subChoice = 'all';
    const boxes = shownBoxes(cube);
    const pts = [], cols = [], tips = [];
    boxes.forEach(b => b.rows.filter(visible).forEach(r => {
      pts.push(r); cols.push(b.color); tips.push(CB.hover[r] + `<br><i>in ${b.label} (${b.role})</i>`);
    }));
    const par = cube ? [cube.ia, cube.ib] : [];
    const parTips = cube ? [cube.ia, cube.ib].map((r, k) => CB.hover[r] + `<br><i>parent pj${k + 1}</i>`) : [];
    if (NB) fillSelect();
    cubeInfo(); tintTable(cube, boxes);
    const grey = !!cube, regrey = grey !== greyed;
    greyed = grey;
    return Promise.all(plots.map(p => {
      const dims = ['x', 'y', 'z'].slice(0, p.axes.length);
      const coordsOf = rows => dims.map((_, d) => rows.map(r => T.coords[r][p.axes[d]]));
      // markers: selection, current (+ points in the sub-cuboids, parents)
      const mk = [[sel, 'selection'], [cur, 'current']];
      if (NB) mk.push([pts, 'subpts'], [par, 'parents']);
      const u = {customdata: mk.map(m => m[0])};
      dims.forEach(k => { u[k] = []; });
      mk.forEach(([rows]) => coordsOf(rows).forEach((v, d) => u[dims[d]].push(v)));
      let job = Plotly.restyle(p.div, u, mk.map(m => p.idx[m[1]]));
      if (regrey)
        job = job.then(() => Plotly.restyle(p.div, {'marker.color': G.map(g => grey ? GREY : DASH.colors[g])},
                                            G.map((_, k) => k)));
      if (NB) {
        const v = {text: [tips, parTips], 'marker.color': [cols, '#000000']};
        job = job.then(() => Plotly.restyle(p.div, v, [p.idx.subpts, p.idx.parents]));
        // lines: the parent cuboid and the sub-cuboids (unused box traces emptied)
        const lines = [cube ? outline(cube.lo, cube.hi, p.axes) : dims.map(() => [])];
        const lcol = ['#000000'];
        for (let k = 0; k < NB; k++) {
          const b = boxes[k];
          lines.push(b ? outline(b.lo, b.hi, p.axes) : dims.map(() => []));
          lcol.push(b ? b.color : '#888888');
        }
        const w = {'line.color': lcol};
        dims.forEach((k, d) => { w[k] = lines.map(l => l[d]); });
        const tr = [p.idx.cuboid].concat([...Array(NB).keys()].map(k => p.idx['box' + k]));
        job = job.then(() => Plotly.restyle(p.div, w, tr));
      }
      return job;
    }));
  }

  // A restyle of a 3D (WebGL) plot made inside its plotly_click handler makes plotly emit the click again, which
  // restyles again, ... (endless recursion, the page hangs).  Clicks are therefore handled outside the event
  // (setTimeout), one at a time, and a click on the solution that is already current is ignored.
  let clickBusy = false;
  function plotClick(ev) {
    const pt = ev && ev.points && ev.points[0];
    if (clickBusy || !pt || pt.customdata === undefined || pt.customdata === null || isNaN(+pt.customdata)) return;
    const i = +pt.customdata;
    if (i === current) return;
    clickBusy = true;
    setTimeout(() => {
      Promise.resolve(setCurrent(i, true)).catch(() => {}).then(() => setTimeout(() => { clickBusy = false; }, 100));
    }, 0);
  }

  function setCurrent(i, scroll) {
    if (current !== null) trs[current].classList.remove('cur');
    current = i;
    trs[i].classList.add('cur');
    const r = T.rows[i];
    document.getElementById('cur').textContent = `itr ${r[0]} (${T.origin[i]})`;
    if (scroll) {
      const wrap = document.getElementById('wrap'), tr = trs[i];
      if (tr.style.display !== 'none')
        wrap.scrollTop = tr.offsetTop - wrap.clientHeight / 2 + tr.offsetHeight / 2;
    }
    return overlay();
  }

  function setSelection(rows) {
    selection = rows ? new Set(rows) : null;
    filterTable(); overlay();
  }

  function clearSelection() {
    plots.forEach(p => {       // drop plotly's own selection (dimmed points, selection outline) in the 2D plots
      if (p.is3d) return;
      const tr = G.map((_, k) => k);
      Plotly.update(p.div, {selectedpoints: tr.map(() => null)}, {selections: []}, tr);
    });
    setSelection(null);
  }

  function applyVisibility() {
    const vis = G.map(g => hidden.has(g) ? 'legendonly' : true);
    plots.forEach(p => Plotly.restyle(p.div, {visible: vis}, G.map((_, k) => k)));
    filterTable(); overlay();
  }

  function legendClick(ev) {
    if (ev.curveNumber >= nG) return false;
    const g = G[ev.curveNumber];
    if (hidden.has(g)) hidden.delete(g); else hidden.add(g);
    if (hidden.size === nG) hidden.delete(g);   // keep at least one group visible
    applyVisibility(); return false;
  }

  function legendDoubleClick(ev) {
    if (ev.curveNumber >= nG) return false;
    const g = G[ev.curveNumber];
    const isolated = hidden.size === nG - 1 && !hidden.has(g);
    hidden.clear();
    if (!isolated) G.forEach(h => { if (h !== g) hidden.add(h); });
    applyVisibility(); return false;
  }

  function init() {
    buildTable(); filterTable();
    const cfg = {responsive: true, displaylogo: false, scrollZoom: false};
    const jobs = DASH.plots.map(p => {
      const div = document.getElementById(p.id);
      const rec = {div: div, axes: p.axes, is3d: p.is3d, idx: {}};
      p.fig.data.forEach((t, k) => { if (k >= nG) rec.idx[t.name] = k; });
      plots.push(rec);
      return Plotly.newPlot(div, p.fig.data, p.fig.layout, cfg).then(() => {
        div.on('plotly_click', plotClick);
        div.on('plotly_legendclick', legendClick);
        div.on('plotly_legenddoubleclick', legendDoubleClick);
        if (!p.is3d) {
          div.on('plotly_selected', ev => {
            if (!ev || !ev.points) return;
            setSelection(ev.points.filter(q => q.curveNumber < nG).map(q => +q.customdata));
          });
          div.on('plotly_deselect', clearSelection);
        }
      });
    });
    document.getElementById('clear').addEventListener('click', clearSelection);
    const tog = document.getElementById('tog2d');
    // the browser may restore the state of the switches after a reload: set them to the initial page state
    if (tog) tog.checked = !document.getElementById('plots').classList.contains('no2d');
    document.getElementById('cubeOn').checked = cubeOn;
    if (tog) tog.addEventListener('change', () => {   // show/hide the 2D row; plots resized to the new layout
      const off = !tog.checked;
      document.getElementById('plots').classList.toggle('no2d', off);
      requestAnimationFrame(() => plots.forEach(p => { if (p.is3d || !off) Plotly.Plots.resize(p.div); }));
    });
    if (!NB) {
      const bar = document.getElementById('cubeLab');     // only the cuboid view is disabled, not the 2D switch
      document.getElementById('cubeOn').disabled = true;
      bar.title = K > CB.max_dim ? `cuboid view: only for up to ${CB.max_dim} criteria`
                                  : 'cuboid view: no solutions with parents (column parents) in parFront.csv';
      bar.style.opacity = '.5';
    }
    fillSelect();
    document.getElementById('cubeOn').addEventListener('change', ev => { cubeOn = ev.target.checked; overlay(); });
    document.getElementById('subSel').addEventListener('change', ev => { subChoice = ev.target.value; overlay(); });
    return Promise.all(jobs);
  }

  // ------------------------------------------------------------------ plotly.js: shared local file, else CDN
  const LOCAL = {{LOCAL}}, CDN = {{CDN}};
  function fail() {
    const e = document.getElementById('err');
    e.style.display = 'block';
    e.textContent = 'Cannot load plotly.js' + (LOCAL ? ` from "${LOCAL}" nor` : '') + ` from ${CDN} ` +
      '(no local file and no internet access?). The table is shown without plots.';
    buildTable(); filterTable();
  }
  function loadScript(src, ok, bad) {
    const s = document.createElement('script');
    s.src = src; s.charset = 'utf-8';
    s.onload = () => (window.Plotly ? ok() : bad());
    s.onerror = bad;
    document.head.appendChild(s);
  }
  // DASH_READY resolves with the plotly.js source used: 'local', 'cdn' or 'none'
  window.DASH_READY = new Promise(res => {
    window.addEventListener('DOMContentLoaded', () => {
      let src = 'none';
      const done = () => init().then(() => res(src));
      const tryCdn = () => { src = 'cdn'; loadScript(CDN, done, () => { fail(); res('none'); }); };
      if (LOCAL) { src = 'local'; loadScript(LOCAL, done, tryCdn); } else tryCdn();
    });
  });
})();
</script>
</body>
</html>
"""

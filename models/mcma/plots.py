from itertools import combinations

import numpy as np
import pandas as pd
from scipy.special import comb  # for computing number of combinations
from matplotlib import mlab
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib import patches
import matplotlib as mpl
from matplotlib.colors import ListedColormap
# from matplotlib.ticker import LinearLocator
import seaborn as sns
from .plots2 import InteractiveParallel

# import mplcursors     # for interactive plots, currently not used
sns.set()  # settings for seaborn plotting style


# todo: Horizontal size of all plots should not be larger than the A4 paper width minus 20mm
# noinspection SpellCheckingInspection
class Plots:
    def __init__(self, wflow, df_vars):  # driver for plots
        self.wflow = wflow
        self.cfg = wflow.cfg
        self.mc = wflow.mc
        self.df = wflow.par_rep.df_sol  # df with distinct solutions
        self.df_vars = df_vars  # df with values of core-model variable (might be None)
        self.cr_defs = wflow.mc.cr  # criteria specs
        self.dir_name = self.cfg.get('resDir')  # result-dir: all plots shall be stored there
        self.show_plot = self.cfg.get('showPlot')
        self.hire_plot = self.cfg.get('hiPlot') is True  # True, if hi-res plots are requested
        self.n_crit = len(self.cr_defs)
        self.cols = self.df.columns  # columns of the df defined in the report() using the criteria names
        self.cr_name = []  # criteria names
        self.cr_col = []  # col-names containing criteria achievements values
        self.n_sol = len(self.df.index)  # number of solutions defined in the df
        self.seq = self.df[self.cols[0]]
        self.def_colors = ['blue', 'orange', 'lime', 'red', 'fuchsia',
                           'brown', 'pink', 'green', 'cyan', 'yellow']
        self.def_markers = ['o', 'v', '^', 's', 'h', 'D']
        self.sol_colors = None
        self.medoids = None
        self.figures = {}  # placeholder for all plots, the keys might be names of the corresponding functions
        self.df[self.cr_name] = self.df[self.cr_name].astype('float')
        self.int_parallel = None
        self.dpi = 200

        if self.show_plot is None:  # just in case the option is missed in cfg
            self.show_plot = False

        for cr in self.cr_defs:
            self.cr_name.append(cr.name)
            self.cr_col.append(f'a_{cr.name}')

        if self.wflow.cluster is None:
            self.sol_colors = [self.def_colors[0]]
        else:
            self.sol_colors = [self.def_colors[i % len(self.def_colors)]
                               for i in self.wflow.cluster.sol2cl]
            self.medoids = self.wflow.cluster.medoids

        SMALL_SIZE = 8
        MEDIUM_SIZE = SMALL_SIZE + 2

        plt.rc('font', size=SMALL_SIZE)  # controls default text sizes
        plt.rc('axes', titlesize=SMALL_SIZE)  # fontsize of the axes title
        plt.rc('axes', labelsize=SMALL_SIZE)  # fontsize of the x and y labels
        plt.rc('axes', titlesize=MEDIUM_SIZE)  # fontsize of the ax title
        plt.rc('xtick', labelsize=SMALL_SIZE)  # fontsize of the tick labels
        plt.rc('ytick', labelsize=SMALL_SIZE)  # fontsize of the tick labels
        plt.rc('legend', fontsize=SMALL_SIZE)  # legend fontsize

    def show_figures(self):
        plt.show()

    def save_figures(self):
        dpi = 300
        for name, fig in self.figures.items():
            filename = f'{self.dir_name}{name}.png'
            fig.savefig(filename, dpi=dpi)
            print(f'Plot "{name}" is saved to "{filename}".')

    def plot2D(self):
        n_plots = comb(self.n_crit, 2, exact=True)  # number of pairs for n_crit
        ncols = 3
        nrows = n_plots // ncols
        if nrows * ncols < n_plots:
            nrows += 1
        fig_heig = 2 * nrows
        print(f'\nFigure with 2D-plots of {n_plots} pairs of criteria.')

        fig1 = plt.figure(figsize=(7, fig_heig), dpi=self.dpi)  # y was 10 (for one chart)
        fig1.canvas.manager.set_window_title(
            f'Criteria achievements for {self.n_sol} solutions.')  # window title

        ticks = np.linspace(0, 100, 6).astype('int')
        cr_ticklabels = []
        for i in range(self.n_crit):
            ticklabels = np.linspace(self.cr_defs[i].nadir, self.cr_defs[i].utopia, 6)
            cr_ticklabels.append([f'{label:0.2e}' for label in ticklabels])

        i_plot = 0  # current plot number (subplots numbers from 1)
        ax = []
        m_size = 5  # marker size  (was 30)
        for i_first in range(self.n_crit):
            name1 = self.cr_name[i_first]
            for i_second in range(i_first + 1, self.n_crit):
                name2 = self.cr_name[i_second]
                print(f'Subplot {i_plot}, criteria: ({name1}, {name2})')
                ax.append(fig1.add_subplot(nrows, ncols, i_plot + 1))  # subplots numbered from 1

                ax[i_plot].set_xlabel(name1, va='center')
                ax[i_plot].set_ylabel(name2, va='center')
                ax[i_plot].set_xticks(ticks, labels=ticks, fontsize=6, va='bottom')
                ax[i_plot].set_yticks(ticks, labels=ticks, fontsize=6, ha='center')

                ax[i_plot].set_xlim(-5, 105)
                ax[i_plot].set_ylim(-5, 105)
                ax[i_plot].set_axisbelow(True)

                ax_y = ax[i_plot].twinx()
                ax_y.tick_params(bottom=False, top=False, left=False, right=False)
                ax_y.set_ylim(-5, 105)
                ax_y.set_yticks(ticks, labels=cr_ticklabels[i_second], ha='left', fontsize=6)
                ax_y.grid(False)

                ax_x = ax[i_plot].twiny()
                ax_x.tick_params(bottom=False, top=False, left=False, right=False)
                ax_x.set_xlim(-5, 105)
                ax_x.set_xticks(ticks, labels=cr_ticklabels[i_first],
                                rotation=30, ha='left', va='center', fontsize=6)
                ax_x.grid(False)

                if self.wflow.cluster:
                    data_to_draw = self.df.groupby(by=self.wflow.cluster.sol2cl)
                else:
                    data_to_draw = [[0, self.df]]
                for clst, data in data_to_draw:
                    ax[i_plot].scatter(x=data[self.cr_col[i_first]], y=data[self.cr_col[i_second]],
                                       c=self.def_colors[clst % len(self.def_colors)],
                                       s=m_size,
                                       marker=self.def_markers[clst % len(self.def_markers)])

                if self.medoids is not None:
                    for clst, medoid in enumerate(self.medoids):
                        ax[i_plot].scatter(x=medoid[i_first], y=medoid[i_second],
                                           c=self.def_colors[clst % len(self.def_colors)],
                                           s=60, edgecolor='black', linewidths=1,
                                           marker=self.def_markers[clst % len(self.def_markers)])

                ax[i_plot].set_xlim(-5, 105)
                ax[i_plot].set_ylim(-5, 105)
                ax[i_plot].tick_params(bottom=False, top=False, left=False, right=False)

                '''
                # labels of points used only for debugging purposes
                for (i, seq) in enumerate(self.seq):
                    ax[i_plot].text(self.df[self.cr_col[i_first]][i] + 2, self.df[self.cr_col[i_second]][i] + 2,
                                    f'{seq}')
                    if i > 20:
                        break
                '''
                '''
                # mplcursors don't work with subplots
                crs.append(mplcursors.cursor(ax[i_plot], hover=True))  # mplcursors for interactive labels
                crs[i_plot].connect("add", lambda sel: self.set_tooltip(sel, i_plot))
                lambda sel: sel.annotation.set_text(  # 1st value taken from the df, others from the axes
                f"{self.df[self.cols[0]] [sel.index]}: ({sel.target[0]:.2e}, {sel.target[1]:.2e})"))
                '''
                i_plot += 1

        plt.tight_layout()
        self.figures['plot2D'] = fig1

    # def set_tooltip(self, sel, i):
    #     sel.annotation.set_text(f'Label: {self.df[self.cols[0]][sel.target.index]} (Subplot {i})'
    #                             f'\nCoordinates: ({sel.target[0]:.2f}, {sel.target[1]:.2f})')

    # plot the value of requested core-model variable along costs
    def vars(self, var_name):
        if self.df_vars is None:
            print('No core-model variables requested to plot.')
            return
        print(f'Plotting requested core model variable "{var_name}" not implemented yet.')
        # df_vars constains values labeled as varName_index, where index is e.g., the technology ID (BTL, OTL, PTL)
        fig, ax = plt.subplots(figsize=(7, 5), dpi=self.dpi)

        # TODO Marek: Please check what variables should be used as X and Y and change it to fit general case
        x_var = 'cost'  # Variable used for X axis
        y_vars = [c for c in self.df_vars.columns if 'act' in c]  # Variables which data will be stacked on Y axis

        df_vars = self.df_vars.astype('float').sort_values(by=x_var)

        x_var_data = df_vars[x_var].to_numpy()  # Should be (N,)
        y_vars_data = df_vars[y_vars].to_numpy().T  # Should be (M, N)

        ax.stackplot(x_var_data, y_vars_data, labels=y_vars, linewidth=0)

        ax.set_xticks(np.linspace(x_var_data[0], x_var_data[-1], 7))
        ax.set_yticks(np.linspace(np.min(y_vars_data), np.max(y_vars_data), 7))

        ax.set_xlabel(x_var)
        ax.set_ylabel('Criteria values')
        ax.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc='upper left', ncols=len(y_vars), mode='expand')

        plt.tight_layout()
        self.figures['vars'] = fig

    def vars_alternative(self):
        colors = mpl.rcParams['axes.prop_cycle'].by_key()['color']

        fig, ax = plt.subplots(figsize=(7, 5), dpi=self.dpi)
        # TODO Marek: Please check what variables should be used as X and Y and change it to fit general case
        x_var = 'cost'  # Variable used for X axis
        y_vars = [c for c in self.df_vars.columns if 'act' in c]

        df_vars = self.df_vars.astype('float').sort_values(by=[x_var, *y_vars])
        bar_width = (df_vars[x_var].iloc[-1] - df_vars[x_var].iloc[0]) / df_vars[x_var].unique().shape[0]

        for x_val, x_val_df in df_vars.groupby(by=x_var):
            y_vars_data = x_val_df[y_vars].to_numpy()
            if y_vars_data.shape[0] == 1:
                bottom = 0
                for i, y_val in enumerate(y_vars_data[0]):
                    ax.bar(x_val, y_val, bar_width,
                           color=colors[i % len(y_vars)], bottom=bottom, linewidth=0)
                    bottom += y_val
            else:
                new_bar_width = bar_width / y_vars_data.shape[0]
                x_values = np.linspace(x_val - bar_width / 2 + new_bar_width / 2,
                                       x_val + bar_width / 2 - new_bar_width / 2,
                                       y_vars_data.shape[0])
                bottom = np.zeros_like(y_vars_data.T[0])
                for i, y_val in enumerate(y_vars_data.T):
                    ax.bar(x_values, y_val, new_bar_width,
                           color=colors[i % len(y_vars)], bottom=bottom, linewidth=0)
                    bottom += y_val

        ax.set_xlabel(x_var)
        ax.set_ylabel('Criteria values')

        legend_patches = [patches.Patch(color=c, label=l) for c, l in zip(colors, y_vars)]
        ax.legend(handles=legend_patches, bbox_to_anchor=(0., 1.02, 1., .102), loc='upper left', ncols=len(y_vars),
                  mode='expand')

        plt.tight_layout()
        self.figures['vars_alternative'] = fig

    def parallel(self):
        # todo: the app freezes when a criterion choice button is clicked
        fig3 = plt.figure(figsize=(7, 3.2), dpi=self.dpi)
        fig3.canvas.manager.set_window_title(
            f'Criteria achievements for {self.n_sol} solutions.')

        self.int_parallel = InteractiveParallel(self.df,
                                                self.cr_name,
                                                self.cr_col,
                                                self.cr_defs,
                                                fig3)

        self.figures['parallel'] = fig3

    def sol_stages(self):  # two subplots: 1. iters + solutions, 2. stage-max cube-size + actual max-size
        summary_df = self.wflow.par_rep.progr.df_stages
        if summary_df is None:
            print('\nPlots::sol_stage(): no data for solution stages yet.')
            return
        fig = plt.figure(figsize=(6, 2.5), dpi=self.dpi)
        fig.canvas.manager.set_window_title(f'Summary of {len(self.wflow.par_rep.progr.cubes2proc)} computation stages')
        plot_kw = dict(marker='o', markersize=5, linestyle='--', linewidth=2)
        ax = fig.add_subplot(1, 2, 1)
        ax.plot(summary_df['step'], summary_df['itr'],
                color='tab:blue',
                label='Iterations',
                **plot_kw)

        ax.plot(summary_df['step'], summary_df['n_sol'],
                color='tab:orange',
                label='Distinct solutions',
                **plot_kw)

        ax.set_xticks(summary_df['step'])
        ax.set_ylabel('Iterations/solutions')
        ax.set_xlabel('Computation stage')
        ax.legend(loc='upper left')

        ax = fig.add_subplot(1, 2, 2)
        ax.plot(summary_df['step'], summary_df['upBnd'],
                color='tab:red',
                label='Cuboid size bound',
                **plot_kw)

        ax.plot(summary_df['step'], summary_df['mx_cube'],
                color='tab:green',
                label='Actual max cuboid-size',
                **plot_kw)

        ax.set_xticks(summary_df['step'])
        ax.set_ylabel('Cuboid size')
        ax.set_xlabel('Computation stage')
        ax.legend(loc='upper right')

        plt.tight_layout()
        self.figures['stageProg'] = fig

    def kde_stages(self):  # for each stage: histogram + KDE
        # todo: AS: pls improve vertical size (number of cols changed to 2); appears to be wrong for even
        #   number of plots
        n_plots = len(self.wflow.par_rep.progr.cubes2proc)
        if n_plots < 2:
            print('\nPlots::kde_stages(): no data for KDE stages yet.')
            return
        mx_hight = 9.0
        ncols = 3
        if len(self.wflow.par_rep.progr.cubes2proc[self.wflow.par_rep.progr.cur_step - 1][-1]) == 0:
            n_plots -= 1  # plot for last stage not generated
        nrows = n_plots // ncols
        if nrows * ncols < n_plots:
            nrows += 1
        fig = plt.figure(figsize=(7, min(mx_hight, 2 * nrows)), dpi=self.dpi, tight_layout=True)
        fig.canvas.manager.set_window_title(f'Distribution of distance between neighbour solutions.')

        for step in self.wflow.par_rep.progr.cubes2proc:
            if len(self.wflow.par_rep.progr.cubes2proc[step][-1]) == 0:
                print(f'Empty cube list for computation stage {step}.')
                continue
            ax = fig.add_subplot(nrows, ncols, step + 1)
            neighbour_cube_sizes = []
            if self.cfg.get('verb') > 3:
                print(f'{step = }')
                print(f'neigh {self.wflow.par_rep.progr.cubes2proc[step]}')
            for cube_id, cube_size in self.wflow.par_rep.progr.cubes2proc[step][-1]:
                if self.cfg.get('verb') > 3:
                    print(f'{cube_id = }, {cube_size = }')
                neighbour_cube_sizes.append(cube_size)

            ax.hist(neighbour_cube_sizes,
                    bins=25,
                    range=(0, 50),  # was 100
                    density=True,
                    linewidth=0.5)

            # Check if list has at least two different values, so we can calculate KDE
            if neighbour_cube_sizes[0] != neighbour_cube_sizes[-1]:
                kde = mlab.GaussianKDE(neighbour_cube_sizes)
                x = np.linspace(0, 50, 200)
                y = kde(x)
                ax.plot(x, y, color='k', linewidth=2)

            ax.set_xticks(range(0, 60, 10))
            ax.set_xlabel('Dist. between neighbors')
            if step % ncols == 0:
                ax.set_ylabel('Prob. Density')
            ax.set_title(f'Stage {step}', va='center')

        plt.tight_layout()
        self.figures['stageKDE'] = fig

    def plot3D(self, only_centres=False):
        if self.n_crit < 3:  # just return for bi-criteria problem
            return

        n_plots = comb(self.n_crit, k=3, exact=True)
        n_cols = n_rows = int(np.ceil(np.sqrt(n_plots)))

        fig2 = plt.figure(figsize=(3.5 * n_cols, 2.5 * n_rows), dpi=self.dpi)
        fig2.set_facecolor('#EAEAF2')
        fig2.canvas.manager.set_window_title(
            f'Criteria achievements for {self.n_sol} solutions.')  # window title
        gs = GridSpec(n_rows, n_cols, fig2, hspace=0.05, wspace=0.05,
                      left=0.05, right=0.95, bottom=0.05, top=0.95)

        for ax_idx, (i, j, k) in enumerate(combinations(range(self.n_crit), r=3)):
            # ax = fig2.add_subplot(n_rows, n_cols, ax_idx, projection='3d')
            ax = fig2.add_subplot(gs[ax_idx], projection='3d', computed_zorder=False)
            ax.set_xlabel(self.cr_name[i])
            ax.set_ylabel(self.cr_name[j])
            ax.set_zlabel(self.cr_name[k])
            # noinspection PyArgumentList
            # warning suppressed here (complains on unfilled params x and y)
            if not only_centres:
                if self.wflow.cluster:
                    data_to_draw = self.df.groupby(by=self.wflow.cluster.sol2cl)
                else:
                    data_to_draw = [[0, self.df]]
                for clst, data in data_to_draw:
                    ax.scatter(xs=data[self.cr_col[i]],
                               ys=data[self.cr_col[j]],
                               zs=data[self.cr_col[k]],
                               c=self.def_colors[clst % len(self.def_colors)],
                               s=10,
                               marker=self.def_markers[clst % len(self.def_markers)],
                               zorder=4)

            if self.medoids is not None:
                for clst, medoid in enumerate(self.medoids):
                    ax.scatter(xs=medoid[i],
                               ys=medoid[j],
                               zs=medoid[k],
                               c=self.def_colors[clst % len(self.def_colors)],
                               s=60, edgecolor='black', linewidths=1.5, zorder=5,
                               marker=self.def_markers[clst % len(self.def_markers)])

            # ax.view_init(elev=15, azim=45, roll=0)     # front origin: (100, 100)
            ax.view_init(elev=15, azim=225, roll=0)     # front origin: (0, 0)
            mxLabelPlot = self.wflow.mc.opt('mxLabelPlot', 0)
            for (idx, seq) in enumerate(self.seq):
                # noinspection PyTypeChecker
                if idx >= mxLabelPlot:
                    break
                ax.text(x=self.df[self.cr_col[i]][idx] + 2,
                        y=self.df[self.cr_col[j]][idx] + 2,
                        z=self.df[self.cr_col[k]][idx] + 2,
                        s=str(seq), fontdict=None)

            # Cubes drawing
            cubes = self.wflow.par_rep.cubes.all_cubes  # aspiracja i rezewacja w CAF: aspAch, resAch
            if only_centres:
                mxCubePlot = 0
            else:
                mxCubePlot = self.mc.opt('mxCubePlot', 0)

            for idx, cube in cubes.items():
                if idx >= mxCubePlot:
                    break
                p1 = [cube.s1.a_vals[v] for v in [i, j, k]]
                p2 = [cube.s2.a_vals[v] for v in [i, j, k]]
                c = 'k' if cube.used else 'r'
                if p1 and p2:
                    bottom = [(p1[0], p1[1], p1[2]), (p1[0], p2[1], p1[2]), (p2[0], p2[1], p1[2]), (p2[0], p1[1], p1[2]),
                              (p1[0], p1[1], p1[2])]
                    ax.plot(*zip(*bottom), c=c, lw=0.5)

                    top = [(p1[0], p1[1], p2[2]), (p1[0], p2[1], p2[2]), (p2[0], p2[1], p2[2]), (p2[0], p1[1], p2[2]),
                           (p1[0], p1[1], p2[2])]
                    ax.plot(*zip(*top), c=c, lw=0.5)

                    for b, t in zip(bottom, top):
                        ax.plot(*zip(*[b, t]), c=c, lw=0.5)

        if only_centres:
            self.figures['centres3D'] = fig2
        else:
            self.figures['plot3D'] = fig2

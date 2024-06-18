import numpy as np
import pandas as pd
from scipy.special import comb  # for computing number of combinations
from matplotlib import mlab
import matplotlib.pyplot as plt
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
        self.cmap = ListedColormap(['brown', 'red', 'orange', 'blue', 'green'])  # takes every item...
        # self.cmap = ListedColormap(['black', 'green', 'blue', 'red', 'brown'])  # takes every item...
        self.cmap1 = ListedColormap(['blue', 'blue', 'blue', 'blue', 'blue', 'blue'])  # mono-color ALL crit-plots
        self.cat_num = pd.Series(index=range(self.n_sol), dtype='Int64')  # seq_id of category
        self.figures = {}  # placeholder for all plots, the keys might be names of the corresponding functions
        self.df[self.cr_name] = self.df[self.cr_name].astype('float')
        self.int_parallel = None
        self.dpi = 200

        if self.show_plot is None:  # just in case the option is missed in cfg
            self.show_plot = False

        for cr in self.cr_defs:
            self.cr_name.append(cr.name)
            self.cr_col.append(f'a_{cr.name}')

        n_cat = 4  # number of categories (including the virtual corner-solutions)
        n_members = int((self.n_sol - self.n_crit) / (n_cat - 1))  # number of non-corner items in each category
        i_memb = 0  # current number of members already assigned to a category
        i_cat = 1  # id of the current category (excluding corner-solutions, which are in 0-th category)
        for (i, sol) in enumerate(self.df[self.cols[0]]):
            if i < self.n_crit:  # corner solution
                self.cat_num[i] = 0
            else:
                self.cat_num[i] = i_cat
                i_memb += 1
                if i_memb == n_members:
                    i_cat += 1
                    i_memb = 0

        SMALL_SIZE = 8
        MEDIUM_SIZE = SMALL_SIZE + 2

        plt.rc('font', size=SMALL_SIZE)  # controls default text sizes
        plt.rc('axes', titlesize=SMALL_SIZE)  # fontsize of the axes title
        plt.rc('axes', labelsize=MEDIUM_SIZE)  # fontsize of the x and y labels
        plt.rc('axes', titlesize=MEDIUM_SIZE)  # fontsize of the ax title
        plt.rc('xtick', labelsize=SMALL_SIZE)  # fontsize of the tick labels
        plt.rc('ytick', labelsize=SMALL_SIZE)  # fontsize of the tick labels
        plt.rc('legend', fontsize=SMALL_SIZE)  # legend fontsize

    def show_figures(self):
        plt.show()

    def save_figures(self):
        dpi = 300 if self.hire_plot else 100
        for name, fig in self.figures.items():
            filename = f'{self.dir_name}{name}.png'
            fig.savefig(filename, dpi=dpi, bbox_inches='tight')
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

                ax[i_plot].scatter(x=self.df[self.cr_col[i_first]], y=self.df[self.cr_col[i_second]], c=self.cat_num,
                                   cmap=self.cmap1, s=m_size)

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
                                                self.cmap,
                                                fig3)

        self.figures['parallel'] = fig3

    def sol_stages(self):  # two subplots: 1. iters + solutions, 2. stage-max cube-size + actual max-size
        summary_df = self.wflow.par_rep.progr.df_stages
        if summary_df is None:
            print('\nPlots::sol_stage(): no data for solution stages yet.')
            return
        fig = plt.figure(figsize=(6, 2.5), dpi=self.dpi)
        fig.canvas.manager.set_window_title(f'Summary of {len(self.wflow.par_rep.progr.neigh)} computation stages')
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
        n_plots = len(self.wflow.par_rep.progr.neigh)
        if n_plots < 2:
            print('\nPlots::kde_stages(): no data for KDE stages yet.')
            return
        mx_hight = 9.0
        ncols = 3
        if len(self.wflow.par_rep.progr.neigh[self.wflow.par_rep.progr.cur_step - 1][-1]) == 0:
            n_plots -= 1  # plot for last stage not generated
        nrows = n_plots // ncols
        if nrows * ncols < n_plots:
            nrows += 1
        fig = plt.figure(figsize=(7, min(mx_hight, 2 * nrows)), dpi=self.dpi, tight_layout=True)
        fig.canvas.manager.set_window_title(f'Distribution of distance between neighbour solutions.')

        for step in self.wflow.par_rep.progr.neigh:
            if len(self.wflow.par_rep.progr.neigh[step][-1]) == 0:
                print(f'Empty cube list for computation stage {step}.')
                continue
            ax = fig.add_subplot(nrows, ncols, step + 1)
            neighbour_cube_sizes = []
            if self.cfg.get('verb') > 3:
                print(f'{step = }')
                print(f'neigh {self.wflow.par_rep.progr.neigh[step]}')
            for cube_id, cube_size in self.wflow.par_rep.progr.neigh[step][-1]:
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

    def plot3D(self):
        if self.n_crit < 3:  # just return for bi-criteria problem
            return
        if self.n_crit > 3:
            # todo: implement 3D subplots for more than 3 criteria
            print(f'Plots.plot3D(): not implemented for {self.n_crit} criteria yet.')
            return
        # assert self.n_crit == 3, f'Plots.plot3D(): not implemented for {self.n_crit} criteria yet.'
        fig2 = plt.figure(figsize=(7, 7), dpi=self.dpi)
        fig2.canvas.manager.set_window_title(
            f'Criteria achievements for {self.n_sol} solutions.')  # window title
        ax = fig2.add_subplot(projection='3d')
        ax.set_xlabel(self.cr_name[0])
        ax.set_ylabel(self.cr_name[1])
        ax.set_zlabel(self.cr_name[2])
        # noinspection PyArgumentList
        # warning suppressed here (complains on unfilled params x and y)
        ax.scatter(xs=self.df[self.cr_col[0]], ys=self.df[self.cr_col[1]], zs=self.df[self.cr_col[2]],
                   label='Criteria Achievements', c=self.cat_num, cmap=self.cmap, s=50)

        # Cubes drawing
        cubes = self.wflow.par_rep.cubes.all_cubes  # aspiracja i rezewacja w CAF: aspAch, resAch
        mxCubePlot = self.mc.opt('mxCubePlot', 0)
        for i, cube in cubes.items():
            # p1 = cube.aspAch
            # p2 = cube.resAch
            if i >= mxCubePlot:
                break
            p1 = cube.s1.a_vals
            p2 = cube.s2.a_vals
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

        # font = {'family': 'serif', 'color': 'darkred', 'weight': 'normal', 'size': 16,}
        # ax.view_init(elev=3, azim=-135, roll=0)
        ax.view_init(elev=15, azim=45, roll=0)
        mxLabelPlot = self.wflow.mc.opt('mxLabelPlot', 0)
        for (i, seq) in enumerate(self.seq):
            # noinspection PyTypeChecker
            if i > mxLabelPlot:
                break
            ax.text(self.df[self.cr_col[0]][i] + 2, self.df[self.cr_col[1]][i] + 2, self.df[self.cr_col[2]][i] + 2,
                    f'{seq}', fontdict=None)

        self.figures['plot3D'] = fig2

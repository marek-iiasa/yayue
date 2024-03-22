import numpy as np
import pandas as pd
from scipy.special import comb    # for computing number of combinations
from matplotlib import mlab
import matplotlib.pyplot as plt
from matplotlib.widgets import RangeSlider
from matplotlib.colors import ListedColormap, Normalize
import matplotlib.cm as cm
from mpl_toolkits.axes_grid1 import make_axes_locatable
import seaborn as sns
# import mplcursors     # for interactive plots, currently not used
sns.set()   # settings for seaborn plotting style


# todo: Plots should preferably be prepared (as self.xxxx figs), then saved in one function, and shown in another func.
# noinspection SpellCheckingInspection
class Plots:
    def __init__(self, mc, df_vars):   # driver for plots
        self.cfg = mc.cfg
        self.mc = mc
        self.df = mc.par_rep.df_sol     # df with distinct solutions
        self.df_vars = df_vars     # df with values of core-model variable (might be None)
        self.cr_defs = mc.cr    # criteria specs
        self.dir_name = self.cfg.get('resDir')  # result-dir: all plots shall be stored there
        self.show_plot = self.cfg.get('showPlot')
        self.hire_plot = self.cfg.get('hiPlot') is True     # True, if hi-res plots are requested
        self.n_crit = len(self.cr_defs)
        self.cols = self.df.columns  # columns of the df defined in the report() using the criteria names
        self.cr_name = []   # criteria names
        self.cr_col = []   # col-names containing criteria achievements values
        self.n_sol = len(self.df.index)  # number of solutions defined in the df
        self.seq = self.df[self.cols[0]]
        self.cmap = ListedColormap(['brown', 'red', 'orange', 'blue', 'green'])  # takes every item...
        # self.cmap = ListedColormap(['black', 'green', 'blue', 'red', 'brown'])  # takes every item...
        self.cmap1 = ListedColormap(['blue', 'blue', 'blue', 'blue', 'blue', 'blue'])  # mono-color ALL crit-plots
        self.cat_num = pd.Series(index=range(self.n_sol), dtype='Int64')    # seq_id of category
        self.plots = {}  # placeholder for all plots, the keys might be names of the corresponding functions

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

        # criterion considered as "main" for the parallel coordinates plot
        self.main_crit_idx = 0
        self.main_crit = self.df[self.cr_col[self.main_crit_idx]]

    def plot2D(self):
        n_plots = comb(self.n_crit, 2, exact=True)  # number of pairs for n_crit
        n_perrow = 3
        n_percol = int(float(n_plots) / float(n_perrow))
        if n_percol * n_perrow < n_plots:
            n_percol += 1
        fig_heig = 4. * n_percol
        print(f'\nFigure with 2D-plots of {n_plots} pairs of criteria.')

        fig1 = plt.figure(figsize=(15, fig_heig))  # y was 10 (for one chart)
        fig1.canvas.manager.set_window_title(
            f'Criteria achievements for {self.n_sol} solutions.')  # window title
        fig1.subplots_adjust(wspace=0.3, hspace=0.3)

        i_plot = 0  # current plot number (subplots numbers from 1)
        ax = []
        m_size = 20  # marker size  (was 30)
        for i_first in range(self.n_crit):
            name1 = self.cr_name[i_first]
            for i_second in range(i_first + 1, self.n_crit):
                name2 = self.cr_name[i_second]
                print(f'Subplot {i_plot}, criteria: ({name1}, {name2})')
                ax.append(fig1.add_subplot(n_percol, n_perrow, i_plot + 1))  # subplots numbered from 1
                ax[i_plot].set_xlabel(name1)
                ax[i_plot].set_ylabel(name2)
                ax[i_plot].set_title(name1 + ' vs ' + name2)
                ax[i_plot].scatter(x=self.df[self.cr_col[i_first]], y=self.df[self.cr_col[i_second]], c=self.cat_num,
                                   cmap=self.cmap1, s=m_size)
                # ax[i_plot].scatter(x=self.df[name1], y=self.df[name2], c=self.cat_num, cmap=self.cmap, s=m_size)
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

        f_name = f'{self.dir_name}p2D.png'
        plt.tight_layout()
        fig1.savefig(f_name)
        # plt.show()
        print(f'2D plot of Pareto solutions stored in file: {f_name}')

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

    def hiPlots(self):  # generate high-resolution plots
        # todo: maybe high-res plots should be done in each plot-function?
        #   then to either generate either high-res plot only or pair of plots
        if self.hire_plot is False:
            print('\n----------------------------------------------------hiPlot not requested.')
            return
        print('\n---------------------------------------------------hi-resolution plots not implemented yet.')

    def parallel(self):
        fig3, ax = plt.subplots(figsize=(self.n_crit * 5, 7))
        fig3.canvas.manager.set_window_title(
            f'Criteria achievements for {self.n_sol} solutions.')

        ax.set_xlabel('Criteria names')
        ax.set_ylabel('Criterion Achievement Function')

        # Colors configuration
        cmap = self.cmap
        scaler = Normalize(vmin=0, vmax=100)
        colors = cmap(scaler(self.main_crit))

        # Draw vertical parallel lines
        for i in range(self.n_crit):
            ax.axvline(i, color='k', linewidth=2)
        ax.set_xticks(range(self.n_crit), labels=self.cr_name)

        # Draw all solutions
        lines = []
        for i, row in self.df[self.cr_col].iterrows():
            line, = ax.plot(row, linewidth=2, marker='o', markersize=10, color=colors[i])
            lines.append(line)

        # Add color-bar
        divider = make_axes_locatable(ax)
        cax = divider.append_axes('left', size='5%', pad=0.5)
        plt.colorbar(cm.ScalarMappable(norm=Normalize(0, 100), cmap=cmap), cax=cax)
        cax.yaxis.set_ticks_position('left')

        # Save fig before adding the slider
        f_name = f'{self.dir_name}parallel.png'
        fig3.savefig(f_name)

        # Add RangeSlider
        slider_cax = divider.append_axes('left', size='5%', pad=0.5)
        slider = RangeSlider(slider_cax, label="Range of values", valmin=0, valmax=100,
                             orientation='vertical', valinit=(0, 100), valstep=0.1,
                             valfmt='%0.1f', handle_style={'size': 15})

        def update_slider(val):
            min_val, max_val = val

            for aline in lines:
                if min_val <= aline.get_ydata()[self.main_crit_idx] <= max_val:
                    aline.set_alpha(1)
                else:
                    aline.set_alpha(0.1)

        slider.on_changed(update_slider)

        if self.show_plot:
            plt.show()
        else:
            print(f'Plots not displayed (this would pause the execution until plot-windows are closed).')

    def sol_stages(self):   # two subplots: 1. iters + solutions, 2. stage-max cube-size + actual max-size
        summary_df = self.mc.par_rep.progr.df_stages
        fig = plt.figure(figsize=(10, 5))
        fig.canvas.manager.set_window_title(f'Summary data of {len(self.mc.par_rep.progr.neigh)} computation stages')

        plot_kw = dict(marker='o', markersize=10, linestyle='--', linewidth=3)
        ax = fig.add_subplot(1, 2, 1)
        ax.plot(summary_df['step'], summary_df['itr'],
                color='tab:blue',
                label='Number of iterations',
                **plot_kw)

        ax.plot(summary_df['step'], summary_df['n_sol'],
                color='tab:orange',
                label='Number of distinct solutions',
                **plot_kw)

        ax.set_xticks(summary_df['step'])
        ax.set_ylabel('Number of iterations/solutions')
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

    def kde_stages(self):   # for each stage: histogram + KDE
        mx_hight = 9.0
        ncols = 2
        n_plots = len(self.mc.par_rep.progr.neigh)
        if len(self.mc.par_rep.progr.neigh[self.mc.par_rep.progr.cur_step - 1][-1]) == 0:
            n_plots -= 1    # plot for last stage not generated
        nrows = n_plots // 2 + n_plots % 2
        # print(f'{nrows = } {n_plots = } rest {n_plots % 2}--------------------------')
        fig = plt.figure(figsize=(5 * ncols, min(mx_hight, 2.8 * nrows)))
        fig.canvas.manager.set_window_title(f'Distribution of distance between neighbour solutions.')
        fig.subplots_adjust(wspace=0.3, hspace=0.85)

        for step in self.mc.par_rep.progr.neigh:
            if len(self.mc.par_rep.progr.neigh[step][-1]) == 0:
                print(f'Empty cube list for computation stage {step}.')
                return
            ax = fig.add_subplot(nrows, ncols, step + 1)
            neighbour_cube_sizes = []
            if self.cfg.get('verb') > 3:
                print(f'{step = }')
                print(f'neigh {self.mc.par_rep.progr.neigh[step]}')
            for cube_id, cube_size in self.mc.par_rep.progr.neigh[step][-1]:
                if self.cfg.get('verb') > 3:
                    print(f'{cube_id = }, {cube_size = }')
                neighbour_cube_sizes.append(cube_size)

            ax.hist(neighbour_cube_sizes,
                    bins=50,
                    range=(0, 50),  # was 100
                    density=True)

            # Check if list has at least two different values, so we can calculate KDE
            if neighbour_cube_sizes[0] != neighbour_cube_sizes[-1]:
                kde = mlab.GaussianKDE(neighbour_cube_sizes)
                x = np.linspace(0, 50, 200)
                y = kde(x)
                ax.plot(x, y, color='k', linewidth=4)

            ax.set_xticks(range(0, 60, 10))
            ax.set_xlabel('Distance between neighbor solutions')
            ax.set_ylabel('Probability Density')
            ax.set_title(f'Stage {step}')

        plt.tight_layout()

    def plot3D(self):
        if self.n_crit < 6:     # ad-hoc suppress 3D
            return
        if self.n_crit > 3:
            # todo: implement 3D subplots for more than 3 criteria
            print(f'Plots.plot3D(): not implemented for {self.n_crit} criteria yet.')
            return
        # assert self.n_crit == 3, f'Plots.plot3D(): not implemented for {self.n_crit} criteria yet.'
        fig2 = plt.figure(figsize=(12, 9))
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
        # font = {'family': 'serif', 'color': 'darkred', 'weight': 'normal', 'size': 16,}
        # ax.view_init(elev=3, azim=-135, roll=0)
        ax.view_init(elev=15, azim=45, roll=0)
        for (i, seq) in enumerate(self.seq):
            # noinspection PyTypeChecker
            ax.text(self.df[self.cr_col[0]][i] + 2, self.df[self.cr_col[1]][i] + 2, self.df[self.cr_col[2]][i] + 2,
                    f'{seq}', fontdict=None)
            if i > 20:
                break
        # Show the plot
        f_name = f'{self.dir_name}p3D.png'
        # f_name = f'{self.cfg.get("resDir")}p3D.png'
        fig2.savefig(f_name)
        print(f'3D plot of Pareto solutions stored in file: {f_name}')
        # if self.show_plot:
        #     plt.show()
        # else:
        #     print(f'Plots not displayed (this would pause the execution until plot-windows are closed).')

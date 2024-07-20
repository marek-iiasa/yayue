import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import RangeSlider, RadioButtons
from matplotlib.colors import ListedColormap, Normalize
from matplotlib.gridspec import GridSpec
import matplotlib.patheffects as path_effects
import matplotlib.cm as cm


class InteractiveParallel:
    def __init__(self, df, cr_name, cr_col, cr_defs, fig):
        self.df = df
        self.cr_name = cr_name
        self.cr_col = cr_col
        self.cr_defs = cr_defs
        self.n_crit = len(cr_col)
        self.cmap = ListedColormap(['brown', 'red', 'orange', 'blue', 'green'])

        self.main_crit_idx = 0
        self.slider = None
        self.lines = None
        self.radio = None
        self.colors = None
        self.axes_text = []

        self.fig = fig
        self.axes = None
        self.init_axes()

        self.init_plot()

    def init_plot(self):
        ax = self.axes['plot']
        ax.set_xlabel('Criteria names', va='center')
        ax.set_xticks(range(self.n_crit), labels=self.cr_name)

        # Color configuration
        self.generate_colors()

        # Draw vertical parallel lines
        for i in range(self.n_crit):
            ax.axvline(i, color='k', linewidth=2)
        self.init_parallel_axes()

        # Draw all solutions
        self.lines = []
        for i, row in self.df[self.cr_col].iterrows():
            line, = ax.plot(row, linewidth=1, marker='o', markersize=5, color=self.colors[i])
            self.lines.append(line)

        # Add colorbar
        plt.colorbar(cm.ScalarMappable(norm=Normalize(0, 100), cmap=self.cmap),
                     cax=self.axes['colorbar'])
        self.axes['colorbar'].set_ylabel('CAF/Real values', labelpad=-45)
        self.axes['colorbar'].yaxis.set_ticks_position('left')
        self.axes['colorbar'].set_ylim(-5, 105)
        self.axes['colorbar'].tick_params(bottom=False, top=False, left=False, right=False)
        self.axes['plot'].yaxis.set_tick_params(labelleft=False)

        # Add slider
        self.slider = RangeSlider(self.axes['slider'], label='Range',
                                  valmin=0, valmax=100, orientation='vertical',
                                  valinit=(0, 100), valstep=0.1,
                                  valfmt='%0.1f', handle_style={'size': 10})
        self.slider.on_changed(self.update_slider)

        # Add radio buttons
        # self.radio = RadioButtons(self.axes['radio'], labels=self.cr_name,
        #                           radio_props={'s': 40, 'c': 'tab:blue'},
        #                           label_props={'fontsize': [6]*len(self.cr_name)})
        # self.radio.on_clicked(self.update_radio)

    def init_parallel_axes(self, n=6):
        ax = self.axes['plot']

        ax_effects = [path_effects.Stroke(linewidth=1.5, foreground='black'),
                      path_effects.Normal()]
        text_effects = [path_effects.Stroke(linewidth=1.5, foreground='white'),
                        path_effects.Normal()]

        ticks = np.linspace(0, 100, n)
        for i in range(self.n_crit):
            labels = np.linspace(self.cr_defs[i].nadir, self.cr_defs[i].utopia, n)

            ax.plot([i] * n, ticks, c='k', marker='_', zorder=10, linewidth=2,
                    markersize=10, path_effects=ax_effects)

            one_axes_text = []
            for t, l in zip(ticks, labels):
                one_axes_text.append(ax.text(i + 0.01, t + 1, f'{l:0.2e}',
                                             ha='left', va='bottom',
                                             fontsize=6,
                                             fontweight='bold',
                                             path_effects=text_effects))
            self.axes_text.append(one_axes_text)

    def update_parallel_axes(self):
        perm = list(range(self.n_crit))
        perm.remove(self.main_crit_idx)
        perm = [self.main_crit_idx, *perm]
        n = len(self.axes_text[0])

        for i, cr_idx in enumerate(perm):
            labels = np.linspace(self.cr_defs[cr_idx].nadir, self.cr_defs[cr_idx].utopia, n)

            for j, l in enumerate(labels):
                self.axes_text[i][j].set_text(f'{l:0.2e}')

    def init_axes(self):
        gs_right = GridSpec(1, 2,
                            width_ratios=(0.5, 4 * self.n_crit),
                            wspace=0.0,
                            left=0.3,
                            figure=self.fig)
        gs_left = GridSpec(2, 1,
                           height_ratios=(1, 3),
                           hspace=0.2,
                           right=0.2,
                           figure=self.fig)
        self.axes = {'plot': self.fig.add_subplot(gs_right[0, 1])}
        self.axes = self.axes | {
            'colorbar': self.fig.add_subplot(gs_right[0, 0], sharey=self.axes['plot']),
            # 'radio': self.fig.add_subplot(gs_left[0, 0]),
            'slider': self.fig.add_subplot(gs_left[:, 0])
        }

    def generate_colors(self):
        scaler = Normalize(vmin=0, vmax=100)
        self.colors = self.cmap(scaler(self.df[self.cr_col[self.main_crit_idx]]))

    def update_slider(self, val):
        min_val, max_val = val

        for aline in self.lines:
            if min_val <= aline.get_ydata()[0] <= max_val:
                aline.set_alpha(1)
            else:
                aline.set_alpha(0.1)

    def update_radio(self, label):
        self.main_crit_idx = self.cr_name.index(label)

        # Reorder column names and labels
        cols = self.cr_col.copy()
        first = cols.pop(self.main_crit_idx)
        cols = [first, *cols]

        names = self.cr_name.copy()
        first = names.pop(self.main_crit_idx)
        names = [first, *names]

        # Regenerate color list
        self.generate_colors()

        # Update colors and data (order)
        for (i, row), c, line in zip(self.df[cols].iterrows(), self.colors, self.lines):
            line.set_color(c)
            line.set_ydata(row.to_numpy())

        # Update xticklabels
        self.axes['plot'].set_xticklabels(names)

        # Manually run update slider to update alpha
        self.update_slider(self.slider.val)

        # Update parallel axes text
        self.update_parallel_axes()

        # Force matplotlib to redraw the figure
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

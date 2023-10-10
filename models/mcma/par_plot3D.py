# import sys      # needed from stdout
# import os
# import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import seaborn as sns
import mplcursors
# from crit import Crit
sns.set()   # settings for seaborn plotting style


# noinspection PySingleQuotedDocstring
def plot3D(df, cr_defs, dir_name):
    """df: solutions to be plotted, dir_name: dir for saving the plot"""

    # todo: indexing needs to be modified (does not work for more than 2 criteria)
    """
    n_crit = len(cr_defs)
    cols = df.columns  # columns of the df defined in the report() using the criteria names
    n_sol = len(df.index)  # number of solutions defined in the df
    seq = df[cols[0]]
    norm = plt.Normalize(seq.min(), seq.max())

    heat_map = False     # if True then use the heat map; alternative: use discrete colors, e.g., from a ListedColormap
    if heat_map:
        norm = plt.Normalize(seq.min(), seq.max())
        cmap = plt.get_cmap('viridis')
        cat_num = None
    else:       # define categories of the iterations
        # cmap = sns.color_palette('Set1', 4)   # works with sns plots, not with plt
        # cmap = ListedColormap(['#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00'])
        # cmap = ListedColormap(['green', 'blue', 'red', 'magenta'])  # ignores! blue or green, if it is on second pos.
        # cmap = ListedColormap(['blue', 'green', 'red', 'gray', 'magenta'])    # ignores green
        cmap = ListedColormap(['green', 'blue', 'red'])  # takes every item, if no more specified
        # cmap = plt.get_cmap('viridis')  # ok
        # cmap = plt.get_cmap('Set1')  # ok
        # cmap = plt.get_cmap('Set3')  # ok
        # cmap = plt.get_cmap('Dark2')  # ok
        # cat = pd.Series(index=range(n_sol), dtype='string')  # category id for selecting colors from discrete colormap
        # cut_num contains (for each data item) data category id, to be used as the color index in the cmap
        cat_num = pd.Series(index=range(n_sol), dtype='Int64')
        # cat = pd.Series(data='?', index=range(n_sol), dtype=None)   # works ok
        n_cat = 3   # number of categories (including the virtual corner-solutions)
        n_members = int((n_sol - n_crit)/(n_cat - 1))  # number of non-corner items in each category
        i_memb = 0  # current number of members already assigned to a category
        i_cat = 1   # id of the current category (excluding corner-solutions, which are in 0-th category)
        for (i, sol) in enumerate(df[cols[0]]):
            if i < n_crit:  # corner solution
                cat_num[i] = 0
            else:
                cat_num[i] = i_cat
                i_memb += 1
                if i_memb == n_members:
                    i_cat += 1
                    i_memb = 0

    # Create two scatter plots using Matplotlib
    # fig, ax = plt.subplots()  # not good, when subplots are used
    fig = plt.figure(figsize=(16, 8))  # (width, height)
    fig.canvas.manager.set_window_title(f'Scatter plots of criteria attributes for {n_sol} solutions.')  # window title
    # fig.canvas.set_window_title(f'Scatter plots of criteria attributes for {n_sol} solutions.')  # the window title
    fig.subplots_adjust(wspace=0.3, hspace=0.5)
    m_size = 70     # marker size

    # define the first subplot
    ax1 = fig.add_subplot(131)  # per-col, per_row, subplot number (starts from 1)
    ax1.set_title(f'Criteria values')  # title of the subplot
    # ax1.scatter(df[cols[1]], df[cols[2]], label=f'Pareto solutions\n{cols[0]}: ({cols[1]}, {cols[2]})')
    if heat_map:
        scat1 = ax1.scatter(df[cols[1]], df[cols[2]], c=seq, cmap=cmap, norm=norm, marker='o', s=m_size,
                            label=f'Pareto solutions\n{cols[0]}: ({cols[1]}, {cols[2]})')
        # cbar = fig.colorbar(scat1, ax=ax1, label='itr_id')    # cbar not used here
        fig.colorbar(scat1, ax=ax1, label='itr_id')
    else:
        # scat1 = ax1.scatter(df[cols[1]], df[cols[2]], c=cat_num, cmap=cmap, marker='o', s=m_size,
        ax1.scatter(df[cols[1]], df[cols[2]], c=cat_num, cmap=cmap, marker='o', s=m_size,
                    label=f'Pareto solutions\n{cols[0]}: ({cols[1]}, {cols[2]})')
        # todo: add legend of the marker-colors
        # fig.colorbar(scat1, ax=ax1, label='itr_id')   # does not work
        # todo: sns.scatterplot does not work yet.
        '''
        scat1 = sns.scatterplot(data=df, x=cols[1], y=cols[2], legend='full') # , c=cat_num, cmap=cmap, marker='o',
                            s=m_size,
                            # legend=f'Pareto solutions\n{cols[0]}: ({cols[1]}, {cols[2]})')
        '''
    """
    """
    ax1.legend()  # legend within the subplot (defined by the label param of scatter)
    ax1.set_xlabel(cols[1])  # labels of the axis
    ax1.set_ylabel(cols[2])
    crs1 = mplcursors.cursor(ax1, hover=True)  # mplcursors for interactive labels
    crs1.connect("add", lambda sel: sel.annotation.set_text(  # 1st value taken from the df, others from the axes
        f"{df[cols[0]][sel.index]}: ({sel.target[0]:.2e}, {sel.target[1]:.2e})"))

    # define the second subplot
    ax2 = fig.add_subplot(132)  # per-col, per_row, subplot number (starts from 1)
    # ax2.scatter(df[cols[3]], df[cols[4]], label=f'Pareto solutions\n{cols[0]}: ({cols[3]}, {cols[4]})')
    if heat_map:
        scat1 = ax2.scatter(df[cols[3]], df[cols[4]], c=seq, cmap=cmap, norm=norm, marker='o', s=m_size,
                            label=f'Pareto solutions\n{cols[0]}: ({cols[3]}, {cols[4]})')
        # cbar = fig.colorbar(scat1, ax=ax2, label='itr_id')    # cbar not used here
        fig.colorbar(scat1, ax=ax2, label='itr_id')
    else:
        # scat1 = ax2.scatter(df[cols[3]], df[cols[4]], c=cat_num, cmap=cmap, marker='o', s=m_size,
        ax2.scatter(df[cols[3]], df[cols[4]], c=cat_num, cmap=cmap, marker='o', s=m_size,
                    label=f'Pareto solutions\n{cols[0]}: ({cols[3]}, {cols[4]})')
    ax2.legend()
    ax2.set_xlabel(cols[1])
    ax2.set_ylabel(cols[2])
    ax2.set_title(f'Criteria achievements')
    crs2 = mplcursors.cursor(ax2, hover=True)
    crs2.connect("add", lambda sel: sel.annotation.set_text(
        f"{df[cols[0]][sel.index]}: ({sel.target[0]:.1f}, {sel.target[1]:.1f})"))
# ------------
    ax3 = fig.add_subplot(133)  # per-col, per_row, subplot number (starts from 1)
    # ax2.scatter(df[cols[3]], df[cols[4]], label=f'Pareto solutions\n{cols[0]}: ({cols[3]}, {cols[4]})')
    """
    """
    if heat_map:
        scat1 = ax2.scatter(df[cols[3]], df[cols[4]], c=seq, cmap=cmap, norm=norm, marker='o', s=m_size,
                            label=f'Pareto solutions\n{cols[0]}: ({cols[3]}, {cols[4]})')
        # cbar = fig.colorbar(scat1, ax=ax2, label='itr_id')    # cbar not used here
        fig.colorbar(scat1, ax=ax2, label='itr_id')
    else:
        # scat1 = ax2.scatter(df[cols[3]], df[cols[4]], c=cat_num, cmap=cmap, marker='o', s=m_size,
        ax3.scatter(df[cols[3]], df[cols[4]], c=cat_num, cmap=cmap, marker='o', s=m_size,
                    label=f'Pareto solutions\n{cols[0]}: ({cols[3]}, {cols[4]})')
    ax3.legend()
    ax3.set_xlabel(cols[1])
    ax3.set_ylabel(cols[2])
    ax3.set_title(f'Criteria achievements')
    crs3 = mplcursors.cursor(ax3, hover=True)
    crs3.connect("add", lambda sel: sel.annotation.set_text(
        f"{df[cols[0]][sel.index]}: ({sel.target[0]:.1f}, {sel.target[1]:.1f})"))
    """
    fig = plt.figure(figsize=(16, 8))  # (width, height)
    ax = plt.axes(projection='3d')
    ax.legend()
    ax.set_xlabel('q1')
    ax.set_ylabel('q2')
    ax.set_zlabel('q3')
    ax.view_init(30, 45)
    ax.set_title(f'Criteria values 3D plot')
    #crs2 = mplcursors.cursor(ax, hover=True)
    #crs2.connect("add", lambda sel: sel.annotation.set_text(df['itr_id'][sel.target.index]))

    #ax3.plot3D(df['q1'], df['q2'], df['q3'])
    ax.scatter(df['q1'], df['q2'], df['q3'])
    # add labels to all points
    lab = 1
    for (i, j, k) in zip(df['q1'], df['q2'], df['q3']):
        if lab > (len(df.index) - 4):
        #label = '(%d, %d, %d)' % (i, j, k)
            label = '%d' %lab
            ax.text(i, j, k, label)
        lab = lab + 1
    plt.show()
   #for iter in df['itr_id']:
    #    label = 'a'
    #   plt.text(df['q1'][iter], df['q2'][iter], df['q3'][iter], label, va='bottom', ha='center')
# ------------
    # Show the plot in a pop-up window and store it
    # plt.legend()
    f_name = dir_name + '/par_sol3D_'+str(len(df.index))+'.png'
    fig.savefig(f_name)
    plt.show()
    print(f'Plot 3D of Pareto solutions stored in file: {f_name}')



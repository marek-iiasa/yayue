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
def plot2D(df, cr_defs, dir_name):
    """df: solutions to be plotted, dir_name: dir for saving the plot"""

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
        '''
        for (i, item) in enumerate(cat_num):
            cat_num[i] = i_cat
            # cat[i] = str(i_cat)
            i_memb += 1
            if i_memb == n_members:
                i_cat += 1
                i_memb = 0
            # cat_map.update({i: cat[i]})
        # cat_num = cat.map(cat_map)
        '''

    # Create two scatter plots using Matplotlib
    # fig, ax = plt.subplots()  # not good, when subplots are used
    fig = plt.figure(figsize=(16, 8))  # (width, height)
    fig.canvas.set_window_title(f'Scatter plots of criteria attributes for {n_sol} solutions.')  # the window title
    fig.subplots_adjust(wspace=0.3, hspace=0.5)
    m_size = 70     # marker size

    # define the first subplot
    ax1 = fig.add_subplot(121)  # per-col, per_row, subplot number (starts from 1)
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
    ax1.legend()  # legend within the subplot (defined by the label param of scatter)
    ax1.set_xlabel(cols[1])  # labels of the axis
    ax1.set_ylabel(cols[2])
    crs1 = mplcursors.cursor(ax1, hover=True)  # mplcursors for interactive labels
    crs1.connect("add", lambda sel: sel.annotation.set_text(  # 1st value taken from the df, others from the axes
        f"{df[cols[0]][sel.index]}: ({sel.target[0]:.2e}, {sel.target[1]:.2e})"))

    # define the second subplot
    ax2 = fig.add_subplot(122)  # per-col, per_row, subplot number (starts from 1)
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

    # Show the plot in a pop-up window and store it
    # plt.legend()
    f_name = dir_name + '/par_sol.png'
    fig.savefig(f_name)
    plt.show()
    print(f'Plot of Pareto solutions stored in file: {f_name}')

    '''
    # examples/temples below
    def plot2D_ex(self):
        import pandas as pd
        import matplotlib.pyplot as plt
        import mplcursors

        # Create a sample DataFrame with data
        data = {'x': [1, 2, 3, 4, 5],
                'y': [2, 4, 6, 8, 10],
                'label': ['A', 'B', 'C', 'D', 'E']}  # Additional label column
        df = pd.DataFrame(data)

        # Create a scatter plot using Matplotlib
        fig, ax = plt.subplots()
        # scatter = ax.scatter(df['x'], df['y'], label='Data Points')
        ax.scatter(df['x'], df['y'], label='Data Points')

        # Add labels and title
        ax.set_xlabel('X-axis')
        ax.set_ylabel('Y-axis')
        ax.set_title('Interactive Scatter Plot')

        # Use mplcursors for interactive labels
        cursor = mplcursors.cursor(hover=True)
        cursor.connect("add", lambda sel: sel.annotation.set_text(
            f"Label: {df['label'][sel.index]}\nCoordinates: ({sel.target[0]:.2f}, {sel.target[1]:.2f})"))
        # cursor.connect("add", lambda sel: sel.annotation.set_text(
        #     f"Label: {df['label'][sel.target.index]}\nCoordinates: ({sel.target[0]:.2f}, {sel.target[1]:.2f})"))

        plt.legend()

        # Show the plot in a pop-up window
        plt.show()

    def plot2Db(self):  # displays in the browser
        import pandas as pd
        import plotly.graph_objects as go

        # Create a sample DataFrame with data
        data = {'x': [1, 2, 3, 4, 5],
                'y': [2, 4, 6, 8, 10],
                'label': ['A', 'B', 'C', 'D', 'E']}  # Additional label column
        df = pd.DataFrame(data)

        # Create a scatter plot using Plotly Graph Objects
        fig = go.Figure()

        # Add scatter trace with customized hover information
        # scatter = fig.add_trace(go.Scatter(   # scatter object not needed here (but "scatter = " might be useful...)
        fig.add_trace(go.Scatter(
            x=df['x'],
            y=df['y'],
            mode='markers',
            text=df['label'],  # The text to display in hover tooltip
            hoverinfo='text+x+y',  # Display 'text', 'x', and 'y' in tooltip
            marker=dict(size=10)
        ))

        # Update layout for better formatting
        fig.update_layout(
            title='Interactive Scatter Plot',
            xaxis_title='X-axis',
            yaxis_title='Y-axis'
        )

        # Show the plot
        fig.show()
    '''

    '''
    # version without hints extended by the content of another df column
    # plt displays in a pop-up window, 
    def plot2Da(self):
        import pandas as pd
        import matplotlib.pyplot as plt
        import mplcursors

        # Create a sample DataFrame
        data = {'x': [1, 2, 3, 4, 5],
                'y': [2, 4, 6, 8, 10]}
        df = pd.DataFrame(data)

        # Create a scatter plot
        plt.scatter(df['x'], df['y'], label='Data Points')

        # Add labels and title
        plt.xlabel('X-axis')
        plt.ylabel('Y-axis')
        plt.title('Interactive Scatter Plot')

        # Use mplcursors for interactive labels
        cursor = mplcursors.cursor(hover=True)
        cursor.connect("add", lambda sel: sel.annotation.set_text(f"({sel.target[0]:.2f}, {sel.target[1]:.2f})"))

        plt.legend()
        plt.show()
    '''


'''
# just templates/examples, to be adapted (also WebGL problem [see the TODO above] has to be fixed)
    def plot3(self):
        import pandas as pd
        import matplotlib.pyplot as plt
        import mplcursors

        # Create a sample DataFrame with 3D data
        data = {'x': [1, 2, 3, 4, 5],
                'y': [2, 4, 6, 8, 10],
                'z': [10, 8, 6, 4, 2]}
        df = pd.DataFrame(data)

        # Create a 3D scatter plot
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        scatter = ax.scatter(df['x'], df['y'], df['z'], label='Data Points')

        # Add labels and title
        ax.set_xlabel('X-axis')
        ax.set_ylabel('Y-axis')
        ax.set_zlabel('Z-axis')
        ax.set_title('3D Scatter Plot')

        # Use mplcursors for interactive labels
        cursor = mplcursors.cursor(hover=True)
        cursor.connect("add", lambda sel: sel.annotation.set_text(
            f"({sel.target[0]:.2f}, {sel.target[1]:.2f}, {sel.target[2]:.2f})"))

        plt.legend()
        plt.show()

    def plot3a(self):
        # Create a sample DataFrame with 3D data
        import pandas as pd
        import plotly.express as px

        # Create a sample DataFrame with 3D data
        data = {'x': [1, 2, 3, 4, 5],
                'y': [2, 4, 6, 8, 10],
                'z': [10, 8, 6, 4, 2]}
        df = pd.DataFrame(data)

        # Create an interactive 3D scatter plot using Plotly
        fig = px.scatter_3d(df, x='x', y='y', z='z', title='3D Scatter Plot',
                            labels={'x': 'X-axis', 'y': 'Y-axis', 'z': 'Z-axis'})

        # Show the plot
        fig.show()
'''

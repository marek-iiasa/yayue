# import sys      # needed from stdout
# import os
# import numpy as np
# import pandas as pd
import matplotlib.pyplot as plt
import mplcursors


# noinspection PySingleQuotedDocstring
def plot2D(df, dir_name):
    '''
    # Create a sample DataFrame with data
    data = {'x': [1, 2, 3, 4, 5],
            'y': [2, 4, 6, 8, 10],
            'label': ['A', 'B', 'C', 'D', 'E']}  # Additional label column
    df = pd.DataFrame(data)
    '''

    cols = df.columns
    n_sol = len(df.index)

    # Create a scatter plot using Matplotlib
    fig, ax = plt.subplots()
    # scatter = ax.scatter(df['x'], df['y'], label='Data Points')   # scatter not used but useful for debug
    # scatter = ax.scatter(df[cols[1]], df[cols[2]], label='Pareto solutions')
    ax.scatter(df[cols[1]], df[cols[2]], label=f'Pareto solutions\n{cols[0]}: ({cols[1]}, {cols[2]})')

    # Add labels and title
    ax.set_xlabel(cols[1])
    ax.set_ylabel(cols[2])
    ax.set_title(f'Plot of {n_sol} Pareto solutions')

    # Use mplcursors for interactive labels
    cursor = mplcursors.cursor(hover=True)
    cursor.connect("add", lambda sel: sel.annotation.set_text(
        f"{df[cols[0]][sel.index]}: ({sel.target[0]:.2e}, {sel.target[1]:.2e})"))
    # f"{cols[0]}: {df[cols[0]][sel.index]}\nCrit-vals: ({sel.target[0]:.2e}, {sel.target[1]:.2e})"))

    plt.legend()

    # Show the plot in a pop-up window
    f_name = dir_name + '/par_sol.png'
    fig.savefig(f_name)
    print(f'Solution plot stored in file: {f_name}')
    plt.show()

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

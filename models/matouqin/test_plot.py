import pandas as pd
import matplotlib.pyplot as plt
import re
import os


def plot_dv_flow(org_df, var_names, dv_names=None, periods=None, pl_type=None, iteration=None):
    # check if var_names and dv_names are lists, pl_type is str
    if isinstance(var_names, str):
        var_names = [var_names]
    if isinstance(dv_names, str):
        dv_names = [dv_names]
    if pl_type is not None:
        if isinstance(pl_type, str):
            print('Pl_type right')
        else:
            print('Pl_type wrong, check')
            return

    # select needed results from csv file
    # construct regular expressions and display
    regex_patterns = fr"(\w+)_\('(\w+)',\s*(\d+)\)"  # select 3 parts, remember add () to each selection type
    print("Constructed Regex Pattern:", regex_patterns)

    # test the regex_pattern
    '''
    test_string = "hVol_('Tank1', 0)"
    match = re.search(regex_patterns, test_string)
    if match:
        # check str
        if match.group(0):
            print("Extracted str:", match.group(0))

        # check var_name
        if match.group(1):
            print("Extracted var name:", match.group(1))

        # check device name
        if match.group(2):
            print("Extracted device name:", match.group(2))

        # check time period
        if match.group(3):
            print("Extracted time period:", match.group(3))
    else:
        print("No match found")
    '''
    # select and store needed results
    dv_df = org_df.filter(regex=regex_patterns)
    print(dv_df)

    # check the selections
    if dv_df.empty:
        print('Wrong variable selection. Please reselect the variables')
        return
    else:
        print('Selection finished')

    # get the number of variables for plotting
    var_n = len(var_names)
    print(f'var_name:{var_names}')
    print(f'var_num:{var_n}')

    # check/find device names in each variable
    if dv_names is None:
        dv_names = set((match.group(2)) for col in dv_df.columns
                       for match in [re.search(regex_patterns, col)] if match)
        print(f'dv_names: {dv_names}')
        dv_n = len(dv_names)
        print('dv_num:', dv_n)
    else:
        dv_n = len(dv_names)
        print('dv_num:', dv_n)

    # check/find time periods
    if periods is None:
        periods = set(int(match.group(3)) for col in dv_df.columns
                      for match in [re.search(regex_patterns, col)] if match)
        print('periods:', periods)
        periods = range(max(periods) + 1)
        print('range periods:', periods)

    # identify plotting types
    if pl_type is None:
        if var_n == 1 and dv_n > 1:
            pl_type = 'var'
        elif var_n > 1 and dv_n == 1:
            pl_type = 'dv'
        else:
            pl_type = 'both'

    iteration = len(org_df)

    # define plotting
    def plot_flow_chart(plot_type):
        # todo: modify colors
        color_map = plt.get_cmap('tab10')

        # check plotting type, var: energy flow of different devices; dv: energy flows of the same device; both: both
        if plot_type == 'var':
            print('plotting start')
            for i in range(iteration):
                # print(f'irritation = {i}')
                for var_name in var_names:
                    print(f'var_name = {var_name}')
                    plt.figure(figsize=(10, 8))
                    # choose data for plotting
                    plt_df = dv_df.filter(col for col in dv_df.columns if col.startswith(f'{var_name}_'))
                    print(f'columns = {plt_df}')
                    plt_dv_names = set((match.group(2)) for col in plt_df.columns
                                       for match in [re.search(regex_patterns, col)] if match)
                    # print(f'plt_dv_names = {plt_dv_names}')
                    plt_dv_n = len(plt_dv_names)    # numbers of devices, for setting the bar position
                    plt_dv_t = set(int(match.group(3)) for col in plt_df.columns
                                       for match in [re.search(regex_patterns, col)] if match)  # match the time periods
                    plt_df_n = len(plt_df.columns)  # numbers of the columns of data
                    # print(f'plt_df_n = {plt_df_n}')
                    for index, plt_dv_name in enumerate(plt_dv_names):
                        for t in plt_dv_t:
                            bar_width = 0.8 / plt_dv_n
                            col_name = f"{var_name}_('{plt_dv_name}', {t})"
                            if col_name in dv_df.columns:
                                value = dv_df.at[i, col_name]
                                # print(col_name, value)
                                label = plt_dv_name if t == max(plt_dv_t) else None
                                bar_position = t + (index - (plt_dv_n - 1) / 2) * bar_width
                                plt.bar(bar_position, value, width=bar_width, color=color_map(index),
                                        label=label, edgecolor='black', linewidth=0.8)
                                plt.text(bar_position, value, f'{value:.2f}', ha='center', va='bottom')
                                plt.axhline(0, color='gray', linewidth=0.8, linestyle='--')
                    plt_title = f'{var_name} flow chart'
                    plt.title(plt_title)
                    plt.xlabel('Time Period')
                    plt.ylabel(f'{var_name} flow (MW)')
                    plt.xticks([t for t in plt_dv_t], [str(t) for t in plt_dv_t])
                    plt.legend(title='Devices', bbox_to_anchor=(1.05, 1), loc='upper left',
                               borderaxespad=0., edgecolor='black')
                    plt.tight_layout()
                    # plt.show()
                    plt.savefig(f'{fig_dir}{i}_{var_name}_bar.png')

        elif plot_type == 'dv':
            print('plotting start')
            for i in range(iteration):
                # print(f'irritation = {i}')
                for dv_name in dv_names:
                    print(f'dv_name = {dv_name}')
                    plt.figure(figsize=(10, 8))
                    # choose data for plotting
                    plt_df = dv_df.filter(regex=r"(\w+)_\('(" + dv_name + r")',\s*(\d+)\)")
                    print(f'columns = {plt_df}')
                    plt_df_n = len(plt_df.columns)  # numbers of the columns of data
                    plt_var_names = set((match.group(1)) for col in plt_df.columns
                                       for match in [re.search(regex_patterns, col)] if match)
                    # print(f'plt_var_names = {plt_var_names}')
                    plt_dv_t = set(int(match.group(3)) for col in plt_df.columns
                                   for match in [re.search(regex_patterns, col)] if match)  # match the time periods
                    plt_var_n = len(plt_var_names)  # numbers of devices, for setting the bar position
                    for index, plt_var_name in enumerate(plt_var_names):
                        for t in plt_dv_t:
                            bar_width = 0.8 / plt_var_n
                            col_name = f"{plt_var_name}_('{dv_name}', {t})"
                            if col_name in dv_df.columns:
                                value = dv_df.at[i, col_name]
                                # print(col_name, value)
                                label = plt_var_name if t == max(plt_dv_t) else None
                                bar_position = t + (index - (plt_var_n - 1) / 2) * bar_width
                                plt.bar(bar_position, value, width=bar_width, color=color_map(index),
                                        label=label, edgecolor='black', linewidth=0.8)
                                plt.text(bar_position, value, f'{value:.2f}', ha='center', va='bottom')
                                plt.axhline(0, color='gray', linewidth=0.8, linestyle='--')
                    plt_title = f'{dv_name} flow chart'
                    plt.title(plt_title)
                    plt.xlabel('Time Period')
                    plt.ylabel(f'{dv_name} flow (MW)')
                    plt.xticks([t for t in plt_dv_t], [str(t) for t in plt_dv_t])
                    plt.legend(title='Devices', bbox_to_anchor=(1.05, 1), loc='upper left',
                               borderaxespad=0., edgecolor='black')
                    plt.tight_layout()
                    # plt.show()
                    plt.savefig(f'{fig_dir}{i}_{dv_name}_bar.png')

    # choose plotting function
    if pl_type == 'var':
        plot_flow_chart('var')
        print('Energy flow plotting finished')
    elif pl_type == 'dv':
        plot_flow_chart('dv')
        print('Energy flow plotting finished')
    elif pl_type == 'both':
        plot_flow_chart('var')
        plot_flow_chart('dv')
        print('Energy flow plotting finished')

    iteration = len(org_df)


def plot_flow(org_df, var_names):
    # check if var_names and dv_names are lists, pl_type is str
    if isinstance(var_names, str):
        var_names = [var_names]

    # select needed results from csv file
    # construct regular expressions and display
    regex_patterns = fr"(\w+)_(\w+)"  # select 2 parts, remember add () to each selection type
    print("Constructed Regex Pattern:", regex_patterns)

    # select and store needed results
    dv_df = org_df.filter(regex=regex_patterns)
    print(dv_df)

    if dv_df.empty:
        print('Wrong variable selection. Please reselect the variables')
        return
    else:
        print('Selection finished')

    iteration = len(org_df)

    for i in range(iteration):
        # print(f'irritation = {i}')
        print(f'plotting start')
        for var_name in var_names:
            print(f'var_name = {var_name}')
            plt.figure(figsize=(10, 8))
            columns = [col for col in dv_df.columns if col.startswith(var_name)]
            print(f'{var_name} column: {columns}')
            x_labels = [re.search(r'_(\w+)$', col).group(1) for col in columns]
            print(f'{var_name} x_labels = {x_labels}')
            for index, (col, label) in enumerate(zip(dv_df.columns, x_labels)):
                plt.bar(label, dv_df[col].values[i])
                plt.text(label, dv_df[col].values[i], f'{dv_df[col].values[i]:.2f}', ha='center', va='bottom')
            plt.axhline(0, color='gray', linewidth=0.8, linestyle='--')
            plt.title(f'{var_name} flow chart')
            plt.xlabel(f'Time periods')
            plt.ylabel(f'{var_name} flow (MW)')
            plt.xticks(x_labels)
            # plt.legend(dbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0., edgecolor='black')
            # plt.tight_layout()
            # plt.show()
            plt.savefig(f'{fig_dir}{i}_{var_name}_bar.png')
        print(f'plotting finished')


def plot_capacity(org_df, var_names):
    # check if var_names and dv_names are lists, pl_type is str
    if isinstance(var_names, str):
        var_names = [var_names]

    # select needed results from csv file
    # construct regular expressions and display
    regex_patterns = fr"(\w+)_(\w+)"  # select 2 parts, remember add () to each selection type
    print("Constructed Regex Pattern:", regex_patterns)

    # select and store needed results
    dv_df = org_df.filter(regex=regex_patterns)
    print(dv_df)

    if dv_df.empty:
        print('Wrong variable selection. Please reselect the variables')
        return
    else:
        print('Selection finished')

    iteration = len(org_df)

    for i in range(iteration):
        # print(f'irritation = {i}')
        print(f'plotting start')
        for var_name in var_names:
            print(f'var_name = {var_name}')
            plt.figure(figsize=(10, 8))
            columns = [col for col in dv_df.columns if col.startswith(var_name)]
            print(f'{var_name} column: {columns}')
            x_labels = [re.search(r'_(\w+)$', col).group(1) for col in columns]
            print(f'{var_name} x_labels = {x_labels}')
            for index, (col, label) in enumerate(zip(dv_df.columns, x_labels)):
                plt.bar(label, dv_df[col].values[i], label=f'{label}')
                plt.text(label, dv_df[col].values[i], f'{dv_df[col].values[i]:.2f}', ha='center', va='bottom')
            plt.axhline(0, color='gray', linewidth=0.8, linestyle='--')
            plt.title(f'Capacity of storage devices')
            plt.xlabel(f'Storage devices')
            plt.ylabel(f'Capacity (MW)')
            plt.xticks(x_labels)
            plt.legend(title='Devices', bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0., edgecolor='black')
            plt.tight_layout()
            # plt.show()
            plt.savefig(f'{fig_dir}{i}_{var_name}_bar.png')
        print(f'plotting finished')


# example
path = '.'
res_dir = f'{path}/Results/'
fig_dir = f'{path}/Figures/'

if not os.path.exists(res_dir):
    os.makedirs(res_dir)
if not os.path.exists(fig_dir):
    os.makedirs(fig_dir)

df = pd.read_csv(f'{res_dir}df_vars.csv')

var = ['eIn', 'hIn', 'hOut', 'hVol', 'hInc', 'cOut']
var1 = ['dOut', 'sIn', 'ePrs', 'sOut', 'eSurplus', 'eBought']
var2 = ['sNum']
dv = ['Tank1']
plot_dv_flow(df, var, iteration=0)
# plot_flow(df, var1)
# plot_capacity(df, 'sNum')

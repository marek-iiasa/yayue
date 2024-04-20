import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.gridspec as gridspec
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
import plotly.graph_objects as pgo
import plotly.io as pio
from plotly.subplots import make_subplots
import pandas as pd
import pyomo.environ as pe
import numpy as np


def set_plt_format():
    plt.rcParams.update({
        'font.family': 'Times New Roman',
        'axes.titlesize': '15',  # title size
        'axes.titlepad': 12,  # space between title and figure
        'axes.labelsize': '13',  # axis title size
        'axes.labelpad': 5,  # space between label and figure
        'xtick.labelsize': '10',  # axis scale size
        'ytick.labelsize': '10',  # axis scale size
        'legend.fontsize': '10',  # legend font size
        'legend.title_fontsize': '13',  # legend title font size
        'font.size': '10',  # font size
        })


def set_pgo_format():
    pgo_templ1 = pgo.layout.Template(
        layout=pgo.Layout(
            width=1000, height=800,
            font=dict(family="Times New Roman", size=13, color="black"),
            titlefont=dict(size=15),
            xaxis=dict(showline=True, linecolor='black',
                       linewidth=1, mirror=True,
                       showgrid=False, showticklabels=True,
                       tickfont=dict(size=13),
                       title_standoff=12,
                       ),
            yaxis=dict(showline=True, linecolor='black',
                       linewidth=1, mirror=True,
                       showgrid=False, showticklabels=True,
                       tickfont=dict(size=13),
                       title_standoff=12,
                       ),
            # legend=dict(x=0.325, y=0.98, traceorder="normal",
            #             font=dict(size=12),
            #             bgcolor="white",
            #             bordercolor="Black", borderwidth=1,
            #             xanchor='center', yanchor='top', orientation="h",
            #             )
        )
    )

    # set new template as default
    pio.templates["pgo_templ1"] = pgo_templ1
    pio.templates.default = "pgo_templ1"


def set_color(numbers):
    n = numbers
    colors = []
    if n == 2:
        # light pink and purple
        # colors = ['#ffbeb4', '#b3c2ff']

        # bule and pink
        colors = ['#0c7bb3', '#f2bae8']

        # orange and yellow
        # colors = ['#f9957f', '#f2f5d0']

        # yellow and blue
        # colors = ['#eae5c9', '#6cc6cb']

        # purple and yellow
        # colors = ['#9fa5d5', '#e8f5c8']
    elif n == 3:
        # gray, blue and orange
        colors = ['#a5a5a5', '#599bd5', '#f7d8b5']

    elif n == 4:
        # white, gray, green and blue
        colors = ['#f4f3f3', '#dfdfdf', '#bfd8d5', '#b1bed5']

        # pink, blue, and silver
        # colors = ['#f9ecec', '#f0d9da', '#c8d9e8', '#ecf2f9']

        # blue, purple, azure and light green
        # colors = ['#69779b', '9692af', '#acdbdf', 'd7eaea']

        # white and green
        # colors = ['#ffffff', '#f0f5f2', '#adc2b5', '#829d93']

        # pink white and blue
        # colors = ['#e3a6ae', '#eecece', '#f7f7f7', '#87c8c8']

        # orange and brown
        # colors = ['#ebc1a7', '#e8dac7', '#f5f2f0', '#cbc088']

        # grey and brown
        # colors = ['#89c5c5', '#e7e5e4', '#d4cfca', '#aea79c']
    elif n == 5:
        # blue to orange
        colors = ['#001b2e', '#294c60', '#adb6c4', '#ffefd3', '#ffc49b']

        # purple to orange
        # colors = ['#885a89', '#8aa8a1', '#cbcbd4', '#d1b490', '#ee7b30']
    elif 5 < n <= 8:
        # blue
        # colors = ['#092b58', '#2f5e8a', '#466a84', '#7ba3d6', '#d5d6da',
        #           '#9e9ea0', '#7f714c', '#4d5848', '#903e28']

        # green
        colors = ['#b7c7ac', '#8aa58b', '#8bb6b8', '#7dc1ea', '#578498',
                  '#334a75', '#e3a98c', '#3b5e57']
    elif 8 < n <= 10:
        # brown
        colors = ['#56442c', '#61523d', '#796d57', '#89785c', '#a59a7d',
                  '#d7d5c6', '#c4cec6', '#8ea2a9', '#698286', '#727b76']
    elif n > 10:
        # blue and yellow as main colors
        colors = ['#235f93', '#3b5e57', '#ee7d2f', '#a5a6a3', '#febf0e',
                  '#70ae4a', '#599cd3', '#1f4575', '#9f4a25', '#636562',
                  '#98742c']

    return colors


def add_labels(bars, values, axs, precision, offset):
    for bar, value in zip(bars, values):
        offset = offset
        pre = precision
        ax = axs
        if value != 0:
            if value > 0:
                # y_position = value + offset
                y_position = bar.get_height() + offset
                va_position = 'bottom'
            else:
                # y_position = value - offset
                y_position = bar.get_height() - offset
                va_position = 'top'
            ax.text(bar.get_x() + bar.get_width() / 2, y_position, f'{bar.get_height():{pre}}',
                    ha='center', va=va_position, fontsize=10)


class Plot:
    def __init__(self, rep_dir, figs_dir):
        self.res_dir = rep_dir
        self.fig_dir = figs_dir
        pl_excel = f'{self.res_dir}plot_vars.xlsx'

        # read data from excel
        self.finance_df = pd.read_excel(pl_excel, sheet_name='finance', index_col=0)
        self.cap_df = pd.read_excel(pl_excel, sheet_name='capacity', index_col=0)
        self.supply_df = pd.read_excel(pl_excel, sheet_name='supply', index_col=0)
        self.flow_df = pd.read_excel(pl_excel, sheet_name='flow', index_col=0)
        self.dvflow_df = pd.read_excel(pl_excel, sheet_name='dvflow', index_col=0)

        # print(f'Finance results:\n {self.finance_df} \n')
        # print(f'Capacity results:\n {self.cap_df} \n')
        # print(f'Supply results:\n {self.supply_df} \n')
        # print(f'Flow results:\n {self.flow_df.head(10)} \n')
        # print(f'Dv_flow results:\n {self.dvflow_df} \n')

        # Color setting
        # self.color_1 = set_color(2)
        # print(f'Color settings:\n {self.color_1}')

        # set format
        set_plt_format()
        set_pgo_format()

        # self.plot_finance()
        # self.plot_capacity()
        # self.plot_dv_flow()
        # self.plot_flow()

    def plot_overview(self):
        print('Overview plotting start')

        # get values
        variables = self.finance_df.columns.tolist()
        values = self.finance_df.iloc[0].values
        cap = self.cap_df

        # plotting
        fig = plt.figure(figsize=(10, 8))

        gs = gridspec.GridSpec(2, 2, fig)

        ax1 = fig.add_subplot(gs[0, :])
        ax2 = fig.add_subplot(gs[1, 0])
        ax3 = fig.add_subplot(gs[1, 1])

        color = set_color(3)

        # 1) finance
        bars = ax1.bar(variables, values,
                       color=set_color(7),
                       width=0.5,
                       edgecolor='black',
                       linewidth=0.8, label=variables)
        add_labels(bars, values, ax1, '.2f', 0.01)

        ax1.axhline(0, color='gray', linewidth=0.8, linestyle='--')
        # plt.ylim(-100, 160)    # Set the value range of the y-axis
        # ax1.set_xlabel('Categories')
        ax1.set_ylabel('Million Yuan')
        ax1.set_title('a) Financial Overview', y=-0.2)
        ax1.legend(title='Finance', bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0., edgecolor='black')

        # 2) capacity
        ax22 = ax2.twinx()

        non_tank_dv = cap[~cap.index.str.contains('Tank')]
        tank_dv = cap[cap.index.str.contains('Tank')]

        bars1 = ax2.bar(non_tank_dv.index, non_tank_dv['sCap'], edgecolor='black',
                        color=color, label='Non-Tank (MW)')
        add_labels(bars1, non_tank_dv['sCap'], ax2, '.0f', offset=0)
        ax2.set_title('b) Capacity of the storage system', y=-0.2)
        # ax2.set_xlabel('Storage devices')
        ax2.set_ylabel('Capacity (MW)')
        bars2 = ax22.bar(tank_dv.index, tank_dv['sCap'], edgecolor='black', color=color[2], label='Tank (kg)')
        ax22.set_ylabel('Capacity (kg)')
        add_labels(bars2, tank_dv['sCap'], ax22, '.0f', offset=0)
        # ax2.tick_params(axis='x', rotation=45)

        # 3) number of storage devices
        ax3.bar(non_tank_dv.index, non_tank_dv['sNum'], color=color, edgecolor='black',
                label=non_tank_dv.index)
        ax3.bar(tank_dv.index, tank_dv['sNum'], color=color[2], edgecolor='black',
                label=tank_dv.index)
        ax3.set_title('c) Numbers of storage device', y=-0.2)
        # ax3.set_xlabel('Storage devices')
        ax3.set_ylabel('Numbers')
        # ax3.tick_params(axis='x', rotation=45)

        for idx, val in enumerate(non_tank_dv['sNum']):
            if val != 0:
                ax3.text(idx, val, f'{val}', ha='center', va='bottom')
        for idx, val in enumerate(tank_dv['sNum']):
            if val != 0:
                ax3.text((idx + len(non_tank_dv)), val, f'{val}', ha='center', va='bottom')

        ax3.legend(title='Devices', bbox_to_anchor=(1.05, 1), loc='upper left',
                   borderaxespad=0., edgecolor='black')

        plt.subplots_adjust(top=0.99,
                            bottom=0.08,
                            left=0.069,
                            right=0.87,
                            hspace=0.25,
                            wspace=0.40)

        # fig.tight_layout()
        plt.savefig(f'{self.fig_dir}Finance_overview.png')
        # plt.show()
        # plt.close()

        print('Overview plotting finished \n'
              '--------------------------------')

    def plot_finance(self):
        print('Finance plotting start')

        variables = self.finance_df.columns.tolist()
        values = self.finance_df.iloc[0].values

        plt.figure(figsize=(10, 8))
        bars = plt.bar(variables, values, color=set_color(7), edgecolor='black',
                       linewidth=0.8, label=variables)
        add_labels(bars, values, plt, '.2f', 0.01)

        plt.axhline(0, color='gray', linewidth=0.8, linestyle='--')
        # plt.ylim(-100, 160)    # Set the value range of the y-axis
        plt.xlabel('Categories')
        plt.ylabel('Million Yuan')
        plt.title('Financial Overview')
        plt.legend(title='Finance', bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0., edgecolor='black')
        plt.tight_layout()
        plt.savefig(f'{self.fig_dir}Finance_bar.png')
        # plt.show()
        # plt.close()
        print('Finance plotting finished \n'
              '--------------------------------')

    def plot_capacity(self):
        print('Capacity plotting start')

        # get values
        cap = self.cap_df

        # 1) sCap
        # plotting
        fig, axs = plt.subplots(1, 2, figsize=(12, 5))
        color = set_color(3)

        ax2 = axs[0].twinx()

        non_tank_dv = cap[~cap.index.str.contains('Tank')]
        tank_dv = cap[cap.index.str.contains('Tank')]

        bars1 = axs[0].bar(non_tank_dv.index, non_tank_dv['sCap'], edgecolor='black',
                           color=color, label='Non-Tank (MW)')
        add_labels(bars1, non_tank_dv['sCap'], axs[0], '.0f', offset=0)
        axs[0].set_title('Capacity of the storage system')
        axs[0].set_xlabel('Storage devices')
        axs[0].set_ylabel('Capacity (MW)')
        bars2 = ax2.bar(tank_dv.index, tank_dv['sCap'], edgecolor='black', color=color[2], label='Tank (kg)')
        ax2.set_ylabel('Capacity (kg)')
        for bar in bars2:
            if bar.get_height() != 0:
                ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f'{bar.get_height()}',
                         ha='center', va='bottom')

        # axs[2].tick_params(axis='x', rotation=45)

        # 2) sNum
        axs[1].bar(non_tank_dv.index, non_tank_dv['sNum'], color=color, edgecolor='black',
                   label=non_tank_dv.index)
        axs[1].bar(tank_dv.index, tank_dv['sNum'], color=color[2], edgecolor='black',
                   label=tank_dv.index)
        axs[1].set_title('Numbers of storage device')
        axs[1].set_xlabel('Storage devices')
        axs[1].set_ylabel('Numbers')
        # axs[2].tick_params(axis='x', rotation=45)

        for idx, val in enumerate(non_tank_dv['sNum']):
            if val != 0:
                axs[1].text(idx, val, f'{val}', ha='center', va='bottom', fontsize=12)
        for idx, val in enumerate(tank_dv['sNum']):
            if val != 0:
                axs[1].text((idx+len(non_tank_dv)), val, f'{val}', ha='center', va='bottom', fontsize=12)

        axs[1].legend(title='Devices', bbox_to_anchor=(1.05, 1), loc='upper left',
                      borderaxespad=0., edgecolor='black')

        plt.subplots_adjust(left=0.1,
                            right=0.95,
                            bottom=0.1,
                            top=0.9,
                            hspace=0.4,
                            wspace=0.55)

        fig.tight_layout()
        plt.savefig(f'{self.fig_dir}Cap_bar.png')
        # plt.show()

        print('Capacity plotting finished \n'
              '--------------------------------')

    def plot_flow(self, step='hourly'):
        print(f'Flow plotting start')

        supply_h = self.supply_df['supply'].iloc[0]
        avg_h = self.supply_df['avg_inflow'].iloc[0]
        flow = self.flow_df.copy()

        # print(self.flow_df.head(10))
        # print(flow.head(10))

        # fig = pgo.Figure()
        fig = make_subplots(rows=2, cols=1)

        # set date index
        time_deltas = pd.to_timedelta(flow.index, unit='h')
        start_date = pd.Timestamp('2019-01-01 00:00')
        date_times = start_date + time_deltas
        flow.index = date_times

        if step == 'hourly':
            agg_df = flow
            avg_inflow = avg_h
            supply = supply_h
        elif step == 'daily':
            agg_df = flow.resample('D').sum()
            avg_inflow = flow['inflow'].sum() / 365
            supply = supply_h * 24
        elif step == 'weekly':
            agg_df = flow.resample('W').sum()
            avg_inflow = flow['inflow'].sum() / 52
            supply = supply_h * 168
        elif step == 'monthly':
            agg_df = flow.resample('M').sum()
            avg_inflow = flow['inflow'].sum() / 12
            supply = supply_h * 30
        else:
            raise ValueError(f'Invalid step')

        # print(f'{agg_df.head(10)}')

        # plot inflow at bottom
        fig.add_trace(pgo.Bar(x=agg_df.index, y=agg_df['inflow'], name='inflow',
                              textposition='auto',
                              marker=dict(color=set_color(11)[-1]
                                          # line=dict(color='black', width=1)
                                          ),
                              ),
                      row=2, col=1,
                      )

        fig.update_xaxes(title_text='Time', row=2, col=1)
        fig.update_yaxes(title_text=f'{step.capitalize()} Inflow (MW) ', row=2, col=1)

        fig.add_shape(type="line",
                      x0=(agg_df.index[0]), y0=avg_inflow,
                      x1=(agg_df.index[-1]), y1=avg_inflow,
                      # xref="paper",
                      # yref="y",
                      line=dict(color="grey", width=2, dash="dot"),
                      row=2, col=1,
                      )

        fig.add_annotation(x=(agg_df.index[0]), y=(1.3 * avg_inflow),
                           text=f'Avg_inflow = {round(avg_inflow, 2)} MW',
                           font=dict(size=18),
                           bgcolor='#f5f5f5',
                           showarrow=False,
                           xanchor='left',  # starting from the left side of the x coordinate
                           row=2, col=1,
                           )

        # plot other flows
        for i, variable in enumerate(agg_df.columns[1:]):
            fig.add_trace(pgo.Bar(x=agg_df.index, y=agg_df[variable], name=variable,
                                  textposition='auto',
                                  marker=dict(color=set_color(11)[i],
                                              # line=dict(color='black', width=1)
                                              ),
                                  ),
                          row=1, col=1,
                          )

        fig.update_xaxes(title_text='Time', row=1, col=1)
        fig.update_yaxes(title_text=f'{step.capitalize()} Flows (MW)',
                         # range=[-30, 16],
                         row=1, col=1)

        fig.add_shape(type="line",
                      x0=(agg_df.index[0]), y0=0,
                      x1=(agg_df.index[-1]), y1=0,
                      # xref="paper",
                      # yref="y",
                      line=dict(color="gray", width=2, dash="dot"),
                      showlegend=False,
                      row=1, col=1,
                      )

        fig.add_shape(type="line",
                      x0=(agg_df.index[0]), y0=supply,
                      x1=(agg_df.index[-1]), y1=supply,
                      # xref="paper",
                      # yref="y",
                      line=dict(color="grey", width=2, dash="dot"),
                      row=1, col=1,
                      )

        fig.add_annotation(
            x=(agg_df.index[0]), y=(1.3 * supply),
            text=f'Supply = {round(supply, 2)} MW',
            font=dict(size=18),
            bgcolor='#f5f5f5',
            showarrow=False,
            xanchor='left',  # starting from the left side of the x coordinate
            row=1, col=1,
        )

        fig.update_layout(
            # barmode='stack',
            barmode='relative',     # positive and negative values are displayed relative to 0
            # bargap=0,   # set the spacing between the bars
            title='Flow overview',
            legend_title='Variables',
            plot_bgcolor='white',   # background color
            width=1400, height=800,
        )

        fig.write_image(f'{self.fig_dir}Flow_overview.png')    # save as png file (static)
        fig.write_html(f'{self.fig_dir}Flow_overview.html')    # save as html file (interactive)
        fig.show()
        print('Flow overview plotting finished \n'
              '--------------------------------')

    def plot_dv_flow(self, n, unit='day'):
        # print hourly flows in specific day or week
        print(f'Plotting energy flows in the {unit} {n} start')

        # get values
        dv_ele_df = self.dvflow_df.filter(like='Elec')
        dv_hy_df = self.dvflow_df.filter(like='Tank')
        dv_fc_df = self.dvflow_df.filter(like='Cell')

        flow_h_df = self.flow_df
        supply_h = self.supply_df['supply'].iloc[0]

        # plotting
        fig, axs = plt.subplots(4, 1, figsize=(10, 10))

        # data processing, day, week
        if unit == 'day':
            dv_ele = dv_ele_df.iloc[((n - 1) * 24):(n * 24 - 1)]
            dv_hy = dv_hy_df.iloc[((n - 1) * 24):(n * 24 - 1)]
            dv_fc = dv_fc_df.iloc[((n - 1) * 24):(n * 24 - 1)]
            flow = flow_h_df.iloc[((n - 1) * 24):(n * 24 - 1)]

            for ax in axs:
                ax.xaxis.set_major_locator(ticker.MultipleLocator(4))

        elif unit == 'week':
            dv_ele = dv_ele_df.iloc[((n - 1) * 168):(n * 168 - 1)]
            dv_hy = dv_hy_df.iloc[((n - 1) * 168):(n * 168 - 1)]
            dv_fc = dv_fc_df.iloc[((n - 1) * 168):(n * 168 - 1)]
            flow = flow_h_df.iloc[((n - 1) * 168):(n * 168 - 1)]

            for ax in axs:
                ax.xaxis.set_major_locator(ticker.MultipleLocator(24))

        else:
            raise ValueError(f'Invalid unit')

        # 1) flows overview
        if flow.empty:
            print(f'There is no energy flows in the model, please check')
        else:
            flow.plot(ax=axs[0], color=set_color(11))
            axs[0].axhline(y=supply_h, color='grey', linestyle='--')
            axs[0].axhline(y=0, color='black', linestyle=':')
            axs[0].text(flow.index[0], supply_h, f'Supply = {round(supply_h, 2)}',
                        verticalalignment='bottom', horizontalalignment='left')

        axs[0].legend(bbox_to_anchor=(1.15, 1.02), loc='upper center', ncol=1)
        axs[0].set_xlabel('Time')
        axs[0].set_ylabel('Electricity flow (MW)')
        axs[0].tick_params(axis='x', rotation=0)

        # 1) electrolyzer flows
        if dv_ele.empty:
            print(f'There is no energy flows through the electrolyzer')
        else:
            # dv_ele_p = dv_ele.loc[:, (dv_ele != 0).any(axis=0)]     # remove 0 columns
            # dv_ele_p.plot(ax=axs[0],
            dv_ele.plot(ax=axs[1],
                        # kind='bar', width=0.8,
                        # edgecolor='black',
                        )

            max_val = dv_ele.max().max()
            min_val = dv_ele.min().min()

            max_t = dv_ele.idxmax().loc[dv_ele.max().idxmax()]
            min_t = dv_ele.idxmin().loc[dv_ele.min().idxmin()]

            axs[1].annotate(f'{max_val:.2f}', xy=(max_t, max_val), xytext=(max_t, 1.01 * max_val))
            # arrowprops=dict(facecolor='black', shrink=0.05)
            axs[1].annotate(f'{min_val:.2f}', xy=(min_t, min_val), xytext=(min_t, 1.01 * (min_val-0.1)))
            # arrowprops=dict(facecolor='black', shrink=0.05))

            axs[1].set_ylim([(min_val - 2), (max_val + 2)])
            axs[1].legend(bbox_to_anchor=(1.15, 1.02), loc='upper center', ncol=1)
            axs[1].set_title('a) Electricity flow in storage devices', y=-0.5)
            axs[1].set_xlabel('Time')
            axs[1].set_ylabel('Electricity flow (MW)')
            axs[1].tick_params(axis='x', rotation=0)

        # 2) hydrogen flows
        if dv_hy.empty:
            print(f'There is no energy flows through the hydrogen tank')
        else:
            # dv_hy_p = dv_hy.loc[:, (dv_hy != 0).any(axis=0)]  # remove 0 columns
            # dv_hy_p.plot(ax=axs[1],

            dv_hy_in = dv_hy.filter(like='hIn')
            dv_hy_out = dv_hy.filter(like='hOut')

            mmax = dv_hy_in.max().max()
            mmin = dv_hy_out.min().min()

            # max_idx = dv_hy_in.idxmax()
            # min_idx = dv_hy_out.idxmin()
            #
            # axs[1].annotate(f'Max: {max_hInc}',
            #             xy=(max_idx, mmax),
            #             xytext=(max_idx, mmax * 1.05),
            #             arrowprops=dict(facecolor='black', arrowstyle="->"),
            #             ha='center')

            dv_hy.plot(ax=axs[2],
                       # kind='bar', width=0.8,
                       # edgecolor='black',
                       )
            # for container in axs[1].containers:
            #     axs[1].bar_label(container)

            axins = inset_axes(axs[2], width='70%', height='55%', loc='lower right',
                               bbox_to_anchor=(0.4, 0.2, 0.6, 0.6),
                               bbox_transform=axs[2].transAxes)
            dv_hy.plot(ax=axins, legend=False)
            axins.set_ylim(1.1 * (mmin-10), 1.1 * (mmax+15))

            # hide axes or labels
            # axins.set_xlabel('Time (zoomed in)')
            # axins.set_ylabel('Flow (zoomed in)')
            # axins.tick_params(labelleft=False, labelbottom=False)

            axs[2].legend(bbox_to_anchor=(1.15, 1.02), loc='upper center', ncol=1)
            axs[2].set_title('b) Hydrogen flow in storage devices', y=-0.5)
            axs[2].set_xlabel('Time')
            axs[2].set_ylabel('Hydrogen flow (kg)')
            axs[2].tick_params(axis='x', rotation=0)

        # 3) Fuel-cell flows
        if dv_fc.empty:
            print(f'There is no energy flows through the fuel cell')
        else:
            # dv_fc_p = dv_fc.loc[:, (dv_fc != 0).any(axis=0)]      # remove 0 columns
            # fc_h = dv_fc_p.filter(like='hInc')
            # fc_e = dv_fc_p.filter(like='cOut')
            fc_h = dv_fc.filter(like='hInc')
            fc_e = dv_fc.filter(like='cOut')

            max_h = fc_h.max().max()
            min_h = fc_h.min().min()
            max_e = fc_e.max().max()
            min_e = fc_e.min().min()

            max_ht = fc_h.idxmax().loc[fc_h.max().idxmax()]
            min_ht = fc_h.idxmin().loc[fc_h.min().idxmin()]
            max_et = fc_e.idxmax().loc[fc_e.max().idxmax()]
            min_et = fc_e.idxmin().loc[fc_e.min().idxmin()]

            fc_e.plot(ax=axs[3], xlabel='Time', ylabel='Electricity flow (MW)', legend=False)
            # kind='bar', width=0.8, edgecolor='black',
            axs[3].annotate(f'{max_e:.2f}', xy=(max_et, max_e), xytext=(max_et, max_e + 0.1))
            axs[3].annotate(f'{min_e:.2f}', xy=(min_et, min_e), xytext=(min_et, min_e + 0.1))

            ax3 = axs[3].twinx()
            fc_h.plot(ax=ax3, ylabel='Hydrogen (kg)', color='pink', legend=False)
            # kind='bar', width=0.8, # edgecolor='black',
            ax3.annotate(f'{max_h:.2f}', xy=(max_ht, max_h), xytext=(max_ht, max_h + 5))
            ax3.annotate(f'{min_h:.2f}', xy=(min_ht, max_h), xytext=(min_ht, min_h + 5))

            # for container in axs[2].containers:
            #     axs[2].bar_label(container)

            # ax2.legend(bbox_to_anchor=(1.11, 1.02), loc='upper left', ncol=1)
            # axs[2].legend(bbox_to_anchor=(1.2, 0.85), loc='upper left', ncol=1)
            axs[3].set_ylim([(min_e - 2), (max_e + 2)])
            lines, labels = axs[3].get_legend_handles_labels()
            lines2, labels2 = ax3.get_legend_handles_labels()
            axs[3].legend(lines + lines2, labels + labels2, bbox_to_anchor=(1.1, 1.02), loc='upper left', ncol=1)

            axs[3].tick_params(axis='x', rotation=0)

            axs[3].set_title('c) Energy flows in fuel cells', y=-0.5)

            # set x coordinate interval
            # for ax in axs:
            #     ax.xaxis.set_major_locator(ticker.MultipleLocator(24))

            plt.subplots_adjust(top=0.981,
                                bottom=0.108,
                                left=0.083,
                                right=0.809,
                                hspace=0.6,
                                wspace=0.2)

        # plt.tight_layout()
        print('Dv flows plotting finished \n'
              '--------------------------------')

        plt.savefig(f'{self.fig_dir}Dvflows.png')

# path = '.'
# res_dir = f'{path}/Results/'    # repository of results
# fig_dir = f'{path}/Figures/'    # repository of figures
# Fig = Plot(res_dir, fig_dir)
#
# Fig.plot_overview()     # Finance and storage overview
# Fig.plot_flow('hourly')         # Flow overview, 'hourly', 'daily', 'weekly', 'monthly' flows
# # Fig.plot_flow('weekly')
# # Fig.plot_dv_flow(20, 'day')     # unit: 'day', 'week'
# plt.show()
#
# Fig.plot_finance()
# Fig.plot_capacity()

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import plotly.graph_objects as pgo
import plotly.io as pio
from plotly.subplots import make_subplots
import pandas as pd
import pyomo.environ as pe
import numpy as np


def set_plt_format():
    plt.rcParams.update({
        'font.family': 'Times New Roman',
        'axes.titlesize': '18',  # title size
        'axes.titlepad': 15,  # space between title and figure
        'axes.labelsize': '15',  # axis title size
        'axes.labelpad': 10,  # space between label and figure
        'xtick.labelsize': '13',  # axis scale size
        'ytick.labelsize': '13',  # axis scale size
        'legend.fontsize': '12',  # legend font size
        'legend.title_fontsize': '13',  # legend title font size
        'font.size': '12',  # font size
        })


def set_pgo_format():
    pgo_templ1 = pgo.layout.Template(
        layout=pgo.Layout(
            width=1000, height=800,
            font=dict(family="Times New Roman", size=13, color="black"),
            titlefont=dict(size=18),
            xaxis=dict(showline=True, linecolor='black',
                       linewidth=1, mirror=True,
                       showgrid=False, showticklabels=True,
                       tickfont=dict(size=15),
                       ),
            yaxis=dict(showline=True, linecolor='black',
                       linewidth=1, mirror=True,
                       showgrid=False, showticklabels=True,
                       tickfont=dict(size=15),
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


def add_labels(bars, values, precision, offset):
    for bar, value in zip(bars, values):
        offset = offset
        pre = precision
        if value != 0:
            if value > 0:
                # y_position = value + offset
                y_position = bar.get_height() + offset
                va_position = 'bottom'
            else:
                # y_position = value - offset
                y_position = bar.get_height() - offset
                va_position = 'top'
            plt.text(bar.get_x() + bar.get_width() / 2, y_position, f'{bar.get_height():{pre}}',
                     ha='center', va=va_position, fontsize=12)


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
        # print(f'Flow results:\n {self.flow_df} \n')
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

    def plot_finance(self):
        print('Finance plotting start')

        variables = self.finance_df.columns.tolist()
        values = self.finance_df.iloc[0].values

        plt.figure(figsize=(10, 8))
        bars = plt.bar(variables, values, color=set_color(7), edgecolor='black',
                       linewidth=0.8, label=variables)
        add_labels(bars, values, '.2f', 0.01)

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

        # plotting
        fig, axs = plt.subplots(1, 2, figsize=(14, 6))
        color = set_color(3)

        # 1) sCap
        ax2 = axs[0].twinx()

        non_tank_dv = cap[~cap.index.str.contains('Tank')]
        tank_dv = cap[cap.index.str.contains('Tank')]

        bars1 = axs[0].bar(non_tank_dv.index, non_tank_dv['sCap'], edgecolor='black',
                           color=color, label='Non-Tank (MW)')
        axs[0].set_title('Capacity of the storage system')
        axs[0].set_xlabel('Storage devices')
        axs[0].set_ylabel('Capacity (MW)')
        bars2 = ax2.bar(tank_dv.index, tank_dv['sCap'], edgecolor='black', color=color[2], label='Tank (kg)')
        ax2.set_ylabel('Capacity (kg)')
        for bar in bars1:
            if bar.get_height() != 0:
                axs[0].text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f'{bar.get_height()}',
                            ha='center', va='bottom')
        add_labels(bars2, tank_dv['sCap'], '.0f', offset=0)
        # axs[0].tick_params(axis='x', rotation=45)

        # 2) sNum
        axs[1].bar(non_tank_dv.index, non_tank_dv['sNum'], color=color, edgecolor='black')
        axs[1].bar(tank_dv.index, tank_dv['sNum'], color=color[2], edgecolor='black')
        axs[1].set_title('Numbers of storage device')
        axs[1].set_xlabel('Storage devices')
        axs[1].set_ylabel('Numbers')
        # axs[1].tick_params(axis='x', rotation=45)

        for idx, val in enumerate(non_tank_dv['sNum']):
            if val != 0:
                axs[1].text(idx, val, f'{val}', ha='center', va='bottom', fontsize=12)
        for idx, val in enumerate(tank_dv['sNum']):
            if val != 0:
                axs[1].text((idx+len(non_tank_dv)), val, f'{val}', ha='center', va='bottom', fontsize=12)

        plt.subplots_adjust(left=0.1,
                            right=0.95,
                            bottom=0.1,
                            top=0.9,
                            hspace=0.2,
                            wspace=0.5)

        # fig.tight_layout()
        plt.savefig(f'{self.fig_dir}Cap_bar.png')
        # plt.show()

        print('Capacity plotting finished \n'
              '--------------------------------')

    def plot_flow(self):
        print(f'Flow plotting start')

        supply = self.supply_df['supply'].iloc[0]
        avg_inflow = self.supply_df['avg_inflow'].iloc[0]
        flow = self.flow_df
        # print('flow')

        # fig = pgo.Figure()
        fig = make_subplots(rows=1, cols=2)
        fig.add_trace(pgo.Bar(x=flow.index, y=flow['inflow'], name='inflow',
                              # text=flow['inflow'],
                              textposition='auto',
                              marker=dict(color=set_color(11)[-1]
                                          # line=dict(color='black', width=1)
                                          ),
                              ),
                      row=1, col=1,
                      )

        fig.update_xaxes(title_text='Time', row=1, col=1)
        fig.update_yaxes(title_text='Inflow (MW)', row=1, col=1)

        for i, variable in enumerate(flow.columns[1:]):
            fig.add_trace(pgo.Bar(x=flow.index, y=flow[variable], name=variable,
                                  # text=flow[variable],
                                  textposition='auto',
                                  marker=dict(color=set_color(11)[i],
                                              # line=dict(color='black', width=1)
                                              ),
                                  ),
                          row=1, col=2,
                          )

        fig.update_xaxes(title_text='Time', row=1, col=2)
        fig.update_yaxes(title_text='Flows (MW)', row=1, col=2)

        fig.add_shape(type="line",
                      x0=(flow.index[0]), y0=0,
                      x1=(flow.index[-1]+0.5), y1=0,
                      # xref="paper",
                      # yref="y",
                      line=dict(color="gray", width=2, dash="dot"),
                      showlegend=False,
                      row=1, col=2,
                      )

        fig.add_shape(type="line",
                      x0=(flow.index[0]-0.2), y0=supply,
                      x1=(flow.index[-1]+0.5), y1=supply,
                      # xref="paper",
                      # yref="y",
                      line=dict(color="grey", width=2, dash="dot"),
                      row=1, col=2,
                      )

        fig.add_annotation(
            x=20, y=(1.1 * supply),
            text=f'Supply = {round(supply, 2)} MW',
            font=dict(size=18),
            showarrow=False,
            row=1, col=2,
        )

        fig.add_shape(type="line",
                      x0=(flow.index[0] - 0.2), y0=avg_inflow,
                      x1=(flow.index[-1] + 0.5), y1=avg_inflow,
                      # xref="paper",
                      # yref="y",
                      line=dict(color="grey", width=2, dash="dot"),
                      row=1, col=1,
                      )

        fig.add_annotation(
            x=20, y=(1.1 * avg_inflow),
            text=f'Avg_inflow = {round(avg_inflow, 2)} MW',
            font=dict(size=18),
            showarrow=False,
            row=1, col=1,
        )

        fig.update_layout(
            # barmode='stack',
            barmode='relative',
            title='Flow overview',
            # xaxis_title='Time',
            # yaxis_title='Electricity flow (Mw)',
            # xaxis=dict(title='Time'),
            # yaxis=dict(title='Values'),
            legend_title='Variables',
            plot_bgcolor='white',   # background color
            width=1400, height=800,
            )

        fig.show()
        # fig.write_image(f'{self.fig_dir}Flow_overview.png')    # save as png file (static)
        # fig.write_html(f'{self.fig_dir}Flow_overview.html')    # save as html file (interactive)
        print('Flow overview plotting finished \n'
              '--------------------------------')

    def plot_dv_flow(self):
        print('Dv flows plotting start')

        # get values
        dv_ele = self.dvflow_df.filter(like='Elec')
        dv_hy = self.dvflow_df.filter(like='Tank')
        dv_fc = self.dvflow_df.filter(like='Cell')

        # print(dv_ele)
        # print(dv_hy)
        # print(dv_fc)

        # plotting
        fig, axs = plt.subplots(3, 1, figsize=(10, 8))

        # 1) electrolyzer flows
        dv_ele_p = dv_ele.loc[:, (dv_ele != 0).any(axis=0)]
        dv_ele_p.plot(ax=axs[0],
                      # kind='bar', width=0.8,
                      # edgecolor='black',
                      )
        # for container in axs[0].containers:
        #     axs[0].bar_label(container)

        axs[0].legend(bbox_to_anchor=(1.15, 1.02), loc='upper center', ncol=1)
        axs[0].set_title('Electricity flow in storage devices')
        axs[0].set_xlabel('Time')
        axs[0].set_ylabel('Electricity flow (MW)')
        axs[0].tick_params(axis='x', rotation=0)

        # 2) hydrogen flows
        dv_hy_p = dv_hy.loc[:, (dv_hy != 0).any(axis=0)]
        dv_hy_p.plot(ax=axs[1],
                     # kind='bar', width=0.8,
                     # edgecolor='black',
                     )
        # for container in axs[1].containers:
        #     axs[1].bar_label(container)

        axs[1].legend(bbox_to_anchor=(1.15, 1.02), loc='upper center', ncol=1)
        axs[1].set_title('Hydrogen flow in storage devices')
        axs[1].set_xlabel('Time')
        axs[1].set_ylabel('Hydrogen flow (kg)')
        axs[1].tick_params(axis='x', rotation=0)

        # 3) Fuel-cell flows
        # dv_fc_p = dv_fc.loc[:, (dv_fc != 0).any(axis=0)]
        # fc_h = dv_fc_p.filter(like='hInc')
        fc_e = dv_fc.filter(like='cOut')
        fc_e.plot(ax=axs[2],
                  title='Energy flows in fuel cells',
                  xlabel='Time',
                  ylabel='Electricity flow (MW)',
                  # kind='bar', width=0.8,
                  # edgecolor='black',
                  )

        # ax2 = axs[2].twinx()
        # fc_h.plot(ax=ax2,
        #           ylabel='Hydrogen (kg)',
        #           color='green',
        #           # kind='bar', width=0.8,
        #           # edgecolor='black',
        #           )

        # for container in axs[2].containers:
        #     axs[2].bar_label(container)

        axs[2].legend(bbox_to_anchor=(1.15, 1.02), loc='upper center', ncol=1)
        # ax2.legend(bbox_to_anchor=(1.15, 0.85), loc='upper left', ncol=1)
        axs[2].tick_params(axis='x', rotation=0)

        for ax in axs:
            ax.xaxis.set_major_locator(ticker.MultipleLocator(25))

        plt.subplots_adjust(left=0.1,
                            right=0.95,
                            bottom=0.1,
                            top=0.9,
                            hspace=0.5,
                            wspace=0.2)

        plt.tight_layout()
        print('Dv flows plotting finished \n'
              '--------------------------------')

        plt.savefig(f'{self.fig_dir}Dvflows_bar.png')
        plt.show()


# path = '.'
# res_dir = f'{path}/Results/'    # repository of results
# fig_dir = f'{path}/Figures/'    # repository of figures
# Fig = Plot(res_dir, fig_dir)
# Fig.plot_flow()
# Fig.plot_finance()
# Fig.plot_capacity()
# Fig.plot_dv_flow()

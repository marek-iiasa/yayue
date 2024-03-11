import matplotlib.pyplot as plt
import plotly.graph_objects as pgo
import plotly.io as pio
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
        'legend.title_fontsize': '13'  # legend title font size
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


class Plot:
    def __init__(self, model, fig_dir):
        self.fig_dir = fig_dir
        self.m = model

        # Color setting
        self.color_1 = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2']

        # set format
        set_plt_format()
        set_pgo_format()

        # todo sepreate get.value and store
        # todo input html fig for dv flow

        self.plot_finance()
        self.plot_capacity()
        self.plot_flow()
        self.plot_dv_flow()

    def plot_finance(self):
        print('Finance plotting start')

        # get values
        revenue = pe.value(self.m.revenue)
        income = pe.value(self.m.income)
        inv = pe.value(self.m.invCost)
        omc = pe.value(self.m.OMC)
        over = pe.value(self.m.overCost)
        buy = pe.value(self.m.buyCost)
        bal = pe.value(self.m.balCost)

        finance_df = pd.DataFrame({
            'Variable': ['Revenue', 'Income', 'InvCost', 'OMC', 'OverCost', 'BuyCost', 'BalCost'],
            'Value': [revenue, income, inv, omc, over, buy, bal]
        })

        print(finance_df)

        plt.figure(figsize=(8, 6))
        bars = plt.bar(finance_df['Variable'], finance_df['Value'], color=self.color_1, edgecolor='black',
                       linewidth=0.8, label=finance_df['Variable'])
        for bar, value in zip(bars, finance_df['Value']):
            offset = 0.01
            if value >= 0:
                y_position = value + offset
                va_position = 'bottom'
            else:
                y_position = value - offset
                va_position = 'top'
            plt.text(bar.get_x() + bar.get_width() / 2, y_position, f'{value:.2f}', ha='center', va=va_position)

        plt.axhline(0, color='gray', linewidth=0.8, linestyle='--')
        plt.xlabel('Categories')
        plt.ylabel('Million Yuan')
        plt.title('Financial Overview')
        plt.legend(title='Finance', bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0., edgecolor='black')
        plt.tight_layout()
        # plt.show()
        plt.savefig(f'{self.fig_dir}_Finance_bar.png')
        print('Finance plotting finished \n'
              '--------------------------------')

    def plot_capacity(self):
        print('Capacity plotting start')

        # get values
        cap = pd.DataFrame(index=self.m.S)
        for s in self.m.sNum:
            cap.loc[s, 'sNum'] = pe.value(self.m.sNum[s])
        for s in self.m.sCap:
            cap.loc[s, 'sCap'] = pe.value(self.m.sCap[s])

        print(cap)

        # plotting
        fig, axs = plt.subplots(1, 2, figsize=(14, 6))
        # 1) sCap
        ax2 = axs[0].twinx()
        non_tank_dv = cap[~cap.index.str.contains('Tank')]
        tank_dv = cap[cap.index.str.contains('Tank')]

        axs[0].bar(non_tank_dv.index, non_tank_dv['sCap'], edgecolor='black', color='g', label='Non-Tank (MW)')
        axs[0].set_title('Capacity of the storage system')
        axs[0].set_xlabel('Storage devices')
        axs[0].set_ylabel('Capacity (MW)')
        ax2.bar(tank_dv.index, tank_dv['sCap'], edgecolor='black', color='b', label='Tank (kg)')
        ax2.set_ylabel('Capacity (kg)')
        # axs[0].tick_params(axis='x', rotation=45)
        for idx, val in enumerate(cap['sCap']):
            axs[1].text(idx, val, f"{val}", ha='center', va='bottom', fontsize=12)

        # 2) sNum
        axs[1].bar(cap.index, cap['sNum'], edgecolor='black')
        axs[1].set_title('Numbers of storage device')
        axs[1].set_xlabel('Storage devices')
        axs[1].set_ylabel('Numbers')
        # axs[1].tick_params(axis='x', rotation=45)

        for idx, val in enumerate(cap['sNum']):
            axs[1].text(idx, val, f'{val}', ha='center', va='bottom', fontsize=12)

        plt.subplots_adjust(left=0.1,
                            right=0.95,
                            bottom=0.1,
                            top=0.9,
                            hspace=0.2,
                            wspace=0.5)

        # fig.tight_layout()
        plt.savefig(f'{self.fig_dir}_Cap_bar.png')
        # plt.show()

        print('Capacity plotting finished \n'
              '--------------------------------')

    def plot_flow(self):
        # todo: figure out 整体图
        print(f'Flow plotting start')

        # get values
        flow = pd.DataFrame({
            'Time': [],
            'dOut': [],
            'sIn': [],
            'sOut': [],
            'ePrs': [],
            'eSurplus': [],
            'eBought': []
        })

        supply = pe.value(self.m.supply)

        flow['Time'] = [t for t in self.m.T]
        # flow['inflow'] = [round(pe.value(self.m.inflow[t]), 2) for t in self.m.T]
        flow['dOut'] = [round(pe.value(self.m.dOut[t]), 2) for t in self.m.T]
        flow['sIn'] = [round(pe.value(self.m.sIn[t]), 2) for t in self.m.T]
        flow['sOut'] = [round(pe.value(self.m.sOut[t]), 2) for t in self.m.T]
        flow['ePrs'] = [round(pe.value(self.m.ePrs[t]), 2) for t in self.m.T]
        flow['eSurplus'] = [round(pe.value(self.m.eSurplus[t]), 2) for t in self.m.T]
        flow['eBought'] = [round(pe.value(self.m.eBought[t]), 2) for t in self.m.T]

        print(flow)

        fig = pgo.Figure()
        for i, variable in enumerate(flow.columns[1:]):
            fig.add_trace(pgo.Bar(x=flow['Time'], y=flow[variable], name=variable,
                                  text=flow[variable], textposition='auto',
                                  marker=dict(color=self.color_1[i],
                                              line=dict(color='black', width=1)
                                              ),
                                  )
                          )

        fig.add_shape(type="line",
                      x0=(flow['Time'].iloc[0]-0.5), y0=0,
                      x1=(flow['Time'].iloc[-1]+0.5), y1=0,
                      # xref="paper",
                      # yref="y",
                      line=dict(color="gray", width=2, dash="dot"),
                      showlegend=False,
                      )

        fig.add_shape(type="line",
                      x0=(flow['Time'].iloc[0]-0.5), y0=supply,
                      x1=(flow['Time'].iloc[-1]+0.5), y1=supply,
                      # xref="paper",
                      # yref="y",
                      line=dict(color="grey", width=2, dash="dot"),
                      )

        fig.add_annotation(
            x=0.1, y=(supply + 40),
            text=f'Supply = {round(supply, 2)}',
            font=dict(size=18),
            showarrow=False,
        )

        fig.update_layout(
            barmode='stack',
            title='Flow overview',
            xaxis_title='Time',
            yaxis_title='Electricity flow (Mw)',
            xaxis=dict(title='Time'),
            yaxis=dict(title='Values'),
            legend_title='Variables',
            plot_bgcolor='white',   # background color
            )

        fig.show()

    def plot_dv_flow(self):
        print('Finance plotting start')

        # get values
        dv_ele = pd.DataFrame()
        dv_hy = pd.DataFrame()
        dv_ele.index = [t for t in self.m.T]
        dv_hy.index = [t for t in self.m.T]

        for dv in self.m.Se:
            ein = [pe.value(self.m.eIn[dv, t]) for t in self.m.T]
            dv_ele[f'eIn_{dv}'] = ein

        for dv in self.m.Sh:
            hin = [pe.value(self.m.hIn[dv, t]) for t in self.m.T]
            hout = [-pe.value(self.m.hOut[dv, t]) for t in self.m.T]
            hvol = [pe.value(self.m.hVol[dv, t]) for t in self.m.T]
            dv_hy[f'hIn_{dv}'] = hin
            dv_hy[f'hOut_{dv}'] = hout
            dv_hy[f'hvol_{dv}'] = hvol

        for dv in self.m.Sc:
            hinc = [-pe.value(self.m.hInc[dv, t]) for t in self.m.T]
            dv_hy[f'hInc_{dv}'] = hinc

            cout = [-pe.value(self.m.cOut[dv, t]) for t in self.m.T]
            dv_ele[f'cOut_{dv}'] = cout

        print(dv_ele)
        print(dv_hy)

        # plotting
        fig, axs = plt.subplots(2, 1, figsize=(10, 10))
        # 1) electrolyzer flows
        dv_ele.plot(kind='bar', ax=axs[0], width=0.8,  edgecolor='black')
        for container in axs[0].containers:
            axs[0].bar_label(container)

        axs[0].legend(bbox_to_anchor=(1.15, 1.02), loc='upper center', ncol=1)
        axs[0].set_title('Electricity flow in storage devices')
        axs[0].set_xlabel('Time')
        axs[0].set_ylabel('Electricity flow (MW)')
        axs[0].tick_params(axis='x', rotation=0)

        # 2) hydrogen flows
        dv_hy.plot(kind='bar', ax=axs[1], width=0.8, edgecolor='black')
        for container in axs[1].containers:
            axs[1].bar_label(container)

        axs[1].legend(bbox_to_anchor=(1.15, 1.02), loc='upper center', ncol=1)
        axs[1].set_title('Hydrogen flow in storage devices')
        axs[1].set_xlabel('Time')
        axs[1].set_ylabel('Hydrogen flow (kg)')
        axs[1].tick_params(axis='x', rotation=0)

        plt.subplots_adjust(left=0.1,
                            right=0.95,
                            bottom=0.1,
                            top=0.9,
                            hspace=0.45,
                            wspace=0.2)

        plt.tight_layout()
        plt.savefig(f'{self.fig_dir}dvflow_bar.png')
        print('Dv flows plotting finished \n'
              '--------------------------------')
        plt.show()

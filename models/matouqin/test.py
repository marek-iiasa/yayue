import matplotlib.pyplot as plt
import pandas as pd
import pyomo.environ as pe


class Plot:
    def __init__(self, model, fig_dir):
        self.fig_dir = fig_dir
        self.m = model

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

        # Color setting
        self.color_1 = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2']

        self.plot_finance()

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
        plt.show()
        plt.savefig(f'{self.fig_dir}_Finance_bar.png')
        print('Finance plotting finished \n'
              '--------------------------------')

    def plot_flow(self):
        # todo: figure out 整体图
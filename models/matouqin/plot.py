import pandas as pd
import matplotlib.pyplot as plt

path = '.'
res_dir = f'{path}/Results/'
df = pd.read_csv(f'{res_dir}df_vars.csv')

# Font size and type for all figures
plt.rcParams.update({
    'font.family': 'Times New Roman',
    'axes.titlesize': '18',     # title size
    'axes.titlepad': 15,        # space between title and figure
    'axes.labelsize': '15',     # axis title size
    'axes.labelpad': 10,        # space between label and figure
    'xtick.labelsize': '13',    # axis scale size
    'ytick.labelsize': '13',    # axis scale size
})

# Color setting
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2']

# Plotting
# Cost
finance = df[['revenue', 'income', 'invCost', 'OMC', 'overCost', 'buyCost', 'balCost']]
finance_long = finance.melt(value_vars=['revenue', 'income', 'invCost', 'OMC', 'overCost', 'buyCost', 'balCost'])
plt.figure(figsize=(8, 6))
plt.tick_params(direction='in')
plt.bar(finance_long['variable'], finance_long['value'], color=colors, edgecolor='black', linewidth=0.8)
plt.axhline(0, color='gray', linewidth=0.8, linestyle='--')
plt.title('Financial Overview')
plt.xlabel('Categories',)
plt.ylabel('Thousands Yuan')
# plt.show()

# Energy flow
# Hydrogen tank

n = 1
hy_long_df = pd.DataFrame()
for i in range(0, n + 1):
    tank_df = df.filter(like=f'Tank{i}').rename(lambda x: x.split('_')[-1], axis='columns')
    tank_df = tank_df.melt(var_name='Index', value_name=f'Tank{i}_Flow', ignore_index=False)
    hy_long_df = pd.concat([hy_long_df, tank_df], axis=1)

# 重置索引（如果需要）
hy_long_df.reset_index(inplace=True)

# 绘图
plt.figure(figsize=(10, 6))
for i in range(0, n + 1):
    plt.plot(hy_long_df['Index'], hy_long_df[f'Tank{i}_Flow'], label=f'Tank{i}')

plt.title('Tank Flows')
plt.xlabel('Index')
plt.ylabel('Flow (MW)')
plt.legend()
plt.show()

'''
# for all flows
def flow(df, vars, device, n, t):
    select = df[[col for col in df.columns if vars in col and any(f'{device}{i}' in col for i in range(0, n + 1))]]
    df_long = pd.DataFrame()
    for i in range(0, n + 1):
        flow_df = df.filter(like=f'Tank{i}').rename(lambda x: x.split('_')[-1], axis='columns')
        flow_df = flow_df.melt(var_name='Index', value_name=f'{device}{i}_Flow', ignore_index=False)
        df_long = pd.concat([df_long, flow_df], axis=1)

    df_long.reset_index(inplace=True)

    plt.figure(figsize=(10, 6))
    for i in range(1, n + 1):
        plt.plot(df_long['Index'], df_long[f'{device}{i}_Flow'], label=f'{device}{i}')

    plt.title(f'{device} Flows')
    plt.xlabel('Index')
    plt.ylabel('Flow (MW)')
    plt.legend()

    plt.show()

a = flow(df, 'hVol', 'tank',1,4)
'''
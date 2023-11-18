""" Clustering of 121 alternatives of technology learning, developed by Marek Makowski, IIASA"""
# The alter121.csv was developed in 2019 by Tieju Ma, Hongtao Ren and Binqqing Ding, ECUST Shanghai;
# The data represents criteria values of 121 alternatives obtained by analysis of a dedicated model
# of technology learning.
# Most of these alternatives are dominated by another alternatives, i.e., are Pareto inefficient.
# Pareto-alternatives, stored in pareto.csv, are the subset of all alternatives stored in alter121.csv
# More information about the code and data development can be found in the Readme.txt file.

# Note: the sklearn package was installed as scikit-learn
# import sys
import os
import numpy as np  # used in tutorial https://www.youtube.com/watch?v=ikt0sny_ImY
import pandas as pd
import collections   # for Counter()
from scipy.special import comb    # for computing number of combinations
import matplotlib
import matplotlib.pyplot as plt
# from mpl_toolkits import Axes3D   error: cannot import name 'Axes3D' from 'mpl_toolkits' (unknown location)
# from mpl_toolkits.mplot3d import Axes3D   # this works OK
import seaborn as sns
# import csv
# import sklearn    # this import is not needed; sklearn was installed as scikit-learn, and recognized by pyCharm
from sklearn.cluster import KMeans
# from sklearn.preprocessing import scale
# from sklearn.preprocessing import normalize
# from sklearn.preprocessing import MinMaxScaler
sns.set()  # plot styling

# Only a subset of alternatives in alter121.csv is Pareto efficient; these are stored in the pareto.csv file
# Clustering is done for all alternatives
# Each alt. attributes: alt_id, rate2, rate3, cost, emission risk, foster, risk1, risk2, risk3
# Any combinations of the criteria (cost, emission risk, foster, risk1, risk2, risk3) can be selected for analysis,
# see examples below.
file = 'alter121.csv'   # all 121 alternatives (19techn problem)

# 3 original criteria
# crit_cols = ['cost', 'emission', 'risk']
# fig_pref = 'Figs/cer/'   # dir for Figures of clusters of the four criteria selected above

# 4 criteria: 3 original + foster
crit_cols = ['cost', 'emission', 'risk', 'foster']
fig_pref = 'Figs/cerf/'   # dir for Figures of clusters of the four criteria selected above

# 4 risk criteria
# crit_cols = ['risk','risk1','risk2','risk3']
# Figs/4risks'   # cost, emission, risk, foster

# SA (Saudi Arabia water/energy/environment study done and published with Simon Parkinson)
# file = 'sa_itr/482.csv' # Saudi Arabia, 127 itr, ele_def, wat_def, co2, wat, cost
# file = 'sa_itr/541.csv' # SA, 28 itr
# crit_cols = ['cost', 'wat', 'co2']
# fig_pref = 'sa_itr/541_3c_'
# crit_cols = ['cost', 'wat', 'co2', 'ele_def', 'wat_def']
# fig_pref = 'sa_itr/541_5c_'

if not os.path.exists(fig_pref):    # create dir for Figures, if it does not exist
    os.makedirs(fig_pref, mode=0o755)
    print(f'Directory {fig_pref} created for storing figures.')

df = pd.read_csv(file)
print(df.head())
# print(df)
# df.describe()
# print(df.shape)

# sample for clutering: composed of normalized columns corresponding to the subset of criteria selected for clustering
sample = df[crit_cols].copy()
sample = sample.apply(lambda x: (x.max() - x)/(x.max() - x.min()))    # normalized [0, 1] criteria values
# sample = sample.apply(lambda x: (x - x.min())/abs((x.max() - x.min())))  # achievements (all crit. minimized)
# print(sample.head())
# print(sample)
print(f'Statistics of the normalized criteria values:\n{sample.describe()}')
#
# sample[0:10,]  # does not work
# kmeans = sklearn.cluster.KMeans(n_clusters=3, random_state = 0).fit(sample)
# cl_centers = kmeans.cluster_centers_
# cl_centers   # cl_centers is 3*2 numpy.ndarray, it has no attribute plot
# result = cluster.predict(sample)   # ???

# check acceptability of data
n_clust = 7     # arbitrary choice of the number of clusters
n_crit = len(crit_cols)
assert n_crit > 1, f'Too few criteria: {n_crit}'
assert n_crit == len(sample.columns), f'Number of data columns: {len(sample.columns)} '
f'inconsistent with the criteria number: {n_crit}.'
assert n_clust > 1, f'Too few requested clusters:  {n_clust}.'
n_rows = len(sample.index)
assert n_rows > 2 * n_clust, f'Too few data points: {n_rows} for exloring {n_clust} clusters'

print('\nProblem config:', n_crit, 'criteria/colums,', n_clust, 'clusters,', n_rows, 'samples/rows.')

X = sample   # bad clustering without scaling the sample, here not needed because the sample is normalized
# X = scale(sample)   # better clustering but centers scaled (i.e., can't be plotted in original scales)
# X.head()   #'numpy.ndarray' object has no attribute 'head'
# X[0:10,]
kmeans = KMeans(n_clusters=n_clust, random_state=5, n_init='auto')
kmeans.fit(X)
y_kmeans = kmeans.predict(X)

print('\nCluster id/seq_no for each alternative:\n', kmeans.labels_)   # cluster id/number containing each alternative
cnt = collections.Counter(kmeans.labels_)
print('\nNumbers of points/alternatives in each cluster:', cnt)     # dict, keys: cluster seq_no
centers = kmeans.cluster_centers_  # list of lists: outer list of clusters, inner of criteria values
# print('\nCenters of clusters:\n', centers)    # this info is now integreted to a printout below

cl_memb = []    # number of members in each cluster
cl_radius = []  # radius of each cluster, i.e., max distance of each element from the corresponding cluster-center
for i in range(n_clust):
    cent = centers[i]
    max_dist = 0.
    n_memb = 0
    for i_row in range(n_rows):
        if kmeans.labels_[i_row] != i:
            # print('row', i_row, 'does not belong to cluster', i)
            continue
        n_memb += 1
        # print('compute distance here')  dist = i_row
        # print('cent', cent)
        # sample.iloc[i_row]
        # print('row:', sample.iloc[i_row])
        dist = np.sqrt(np.sum([(a-b)**2 for a, b in zip(cent, sample.iloc[i_row])]))
        # print('cent', cent, 'i_row', i_row, 'row', sample.iloc[i_row], 'dist =', dist)
        if dist > max_dist:
            max_dist = dist
    # print('Cluster', i, ', members', n_memb, ', radius =', max_dist)
    cl_memb.append(n_memb)
    cl_radius.append(round(max_dist, 2))
print(f'\nSummary of {n_clust} clusters for {n_crit} criteria: {crit_cols}:')
for i in range(n_clust):
    c_coor = ''  # format coordinates of cluster centers
    for j in range(n_crit):
        c_coor += f'{centers[i, j]:.3f} '
    print(f'Cluster {i}, members: {cl_memb[i]:2d}, radius: {cl_radius[i]:.2f}, center: [{c_coor}].')

# color preparation
cent_cmap = []   # color-levels (normalized to [0, 1]) for each center
for i in range(n_clust):
    cent_cmap.append(float(i)/(float(n_clust) - 1.))
# print('color levels of centers (normalized to [0,1]): ', cent_cmap)
clust_int = kmeans.labels_  # cluster numbers/ids for each point (int by default)
clust_float = clust_int.astype(np.float32)
# print('colors (positions in cmap) of points before normalizing to [0,1]:\n', clust_float)
clust_float = np.multiply(clust_float, 1./max(clust_float))  # after [0,1] normalization

# col_theme no longer used
# col_theme = np.array(['darkgray', 'lightsalmon', 'powderblue', 'darkgreen', 'darkblue'])
# col_theme = np.array(['darkorange', 'magenta', 'darkgreen', 'darkblue', 'red', 'darkgray'])

# cmap selection
# see https://matplotlib.org/3.1.0/tutorials/colors/colormaps.html
# a selection of popular colormaps: viridis, PiYG, PRGn, RdYlGn, winter, Spectral;
# good for clusters: brg, Dark2, tab10
# NOT good: Paired
# see https://matplotlib.org/3.1.0/tutorials/colors/colormaps.html
# cmap = matplotlib.cm.get_cmap('brg')  # deprecated; updated code below
cmap = matplotlib.colormaps['brg']

# 2D plots (for criteria pairs) first
# configure number and locations of plots
# n_plots = int((n_crit * (n_crit - 1)) / 2)   # number of pairs for n_crit 
n_plots = comb(n_crit, 2, exact=True)   # number of pairs for n_crit (calculated by comb() function)
n_plots += 1    # additional subplot with comments
n_perrow = 3
# n_percol_ = float(n_plots) / flot(n_perrow)
n_percol = int(float(n_plots) / float(n_perrow))
if n_percol * n_perrow < n_plots:
    n_percol += 1
fig_heig = 3.5 * n_percol
print(f'\nFigure with 2D-plots of {n_plots - 1} pairs of criteria.')    # additional plot contains the legend

fig1 = plt.figure(figsize=(12, fig_heig))   # y was 10 (for one chart)
fig1.subplots_adjust(wspace=0.3, hspace=0.4)

i_plot = 0  # current plot number (subplots numbers start from 1)
ax = []
for i_first in range(n_crit):
    name1 = crit_cols[i_first]
    for i_second in range(i_first + 1, n_crit):
        name2 = crit_cols[i_second]
        # print('Plot', i_plot + 1, 'pair (', name1, ',', name2, ')')
        print(f'Plot {i_plot}: pair ({name1}, {name2})')
        ax.append(fig1.add_subplot(n_percol, n_perrow, i_plot + 1))  # subplots numbered from 1
        ax[i_plot].set_xlabel(name1)
        ax[i_plot].set_ylabel(name2)
        ax[i_plot].set_title(name1 + ' vs ' + name2)
        ax[i_plot].scatter(x=sample[name1], y=sample[name2], c=cmap(clust_float), s=50)
        for i in range(len(centers)):
            ax[i_plot].scatter(x=centers[i, i_first], y=centers[i, i_second],
                               # color = cmap(cent_cmap[i]), s = 250)
                               marker='h', edgecolor=cmap(cent_cmap[i]), facecolor="None", s=250)
        i_plot += 1

ax.append(fig1.add_subplot(n_percol, n_perrow, i_plot + 1))  # last subplot with text/comments
ax[i_plot].axis('off')
ax[i_plot].set_title('Information about clusters')
ax[i_plot].invert_yaxis()
txt = []
for i in range(n_clust):
    txt.append(f'Cluster {str(i)}:  members {cl_memb[i]:2d}, radius = {cl_radius[i]:.2f}')
    # print(txt[i])
    ax[i_plot].text(0.01, 0.1 + 0.1 * i, txt[i], color=cmap(cent_cmap[i]), fontsize=12)

fig1_file = f'{fig_pref}{str(n_clust)}_2D.png'
plt.savefig(fig1_file, bbox_inches='tight')
print('Scatter 2D-plots saved to: ', fig1_file)
# plt.show()   # if commented then plot is shown together with Fig. 2

# 3D plots follow 2D plots
# NOTE: interactive 3D plots don't work with subplots

# configure number and locations of plots
n_plots = comb(n_crit, 3, exact=True)   # number of triples for n_crit
# n_plots += 1    # subplot with comments (available with 2D-plots) not generated with 3d-plots
n_perrow = 2
n_percol = int(float(n_plots) / float(n_perrow))
if n_percol * n_perrow < n_plots:
    n_percol += 1
fig_heig = 10 * n_percol
print(f'\nFigure with 3D-of plots of {n_plots} triplets of criteria.')

# fig = plt.figure(figsize = (12,fig_heig))   # y was 10
# fig.subplots_adjust(wspace=0.3, hspace=0.4)
fig = plt.figure(figsize=(12, 10))

i_plot = 0  # current plot number (subplots numbers from 1)
ax = []
for i_first in range(n_crit):
    name1 = crit_cols[i_first]
    for i_second in range(i_first + 1, n_crit):
        name2 = crit_cols[i_second]
        for i_third in range(i_second + 1, n_crit):
            name3 = crit_cols[i_third]
            print(f'Plot {i_plot}: criteria ({name1}, {name2}, {name3})')
            ax.append(fig.add_subplot(n_percol, n_perrow, i_plot + 1, projection='3d'))  # subplots numbered from 1
            ax[i_plot].set_xlabel(name1)
            ax[i_plot].set_ylabel(name2)
            ax[i_plot].set_zlabel(name3)
            sub_title = name1 + ' vs ' + name2 + ' vs ' + name3
            # Placement 0, 0 would be the bottom left, 1, 1 would be the top right.
            ax[i_plot].text2D(0.05, 0.95, sub_title, transform=ax[i_plot].transAxes)
            # the above places title at the controlled place, the below at the center too close to chart
            # ax[i_plot].set_title(name1 +' vs ' + name2 + ' vs ' + name3)
            
            # ax.set_zlim(1e+6, 3e+6)   # replaced by the min/max normalization to [0,1]
            # ax.view_init(60, -50)  # 70 above x-y plane, 50 rotate 50 degr, counter-clockwise about z-xis
            ax[i_plot].scatter(xs=sample[name1], ys=sample[name2], zs=sample[name3],
                               # c = col_theme[kmeans.labels_], s = 50)    # cmap='viridis' colors according values
                               c=cmap(clust_float), s=50)
            # ax[i_plot].scatter(x = sample[name1], y = sample[name2], c = cmap(clust_float), s = 50)
            for i in range(len(centers)):
                ax[i_plot].scatter(xs=centers[i, i_first], ys=centers[i, i_second], zs=centers[i, i_third],
                                   marker='h', facecolor=(0, 0, 0, 0),  # cmap(cent_cmap[i]),
                                   edgecolor=cmap(cent_cmap[i]), s=250)
                # the below does not work in 3D, facecolor not accepted
                # marker='h', edgecolor=cmap(cent_cmap[i]), facecolor="None", s = 250)
            i_plot += 1

# subplot with comments not generated with the 3D-plots
# ax.append(fig.add_subplot(n_percol, n_perrow, i_plot + 1))  # last 3D-subplot with text/comments
# ax[i_plot].axis('off')
# ax[i_plot].set_title('Information about clusters')
# ax[i_plot].invert_yaxis()
# txt = []
# for i in range(n_clust):
#    txt.append('Cluster ' + str(i) +', members ' + str(cl_memb[i]) + ', radius = ' +str(cl_radius[i]))
#    print(txt[i])
#    ax[i_plot].text(0.01, 0.1 + 0.1 * i, txt[i], color = cmap(cent_cmap[i]), fontsize=12)

fig_file = f'{fig_pref}{str(n_clust)}_3D.png'
plt.savefig(fig_file, bbox_inches='tight')   # saved plots are not interactive
print('Scatter 3D-plots saved to: ', fig_file)
plt.show()

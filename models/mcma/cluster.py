""" Clustering pymcma solutions, Marek Makowski, IIASA"""
import numpy
import pandas as pd
import numpy as np  # used in tutorial https://www.youtube.com/watch?v=ikt0sny_ImY
from sklearn.cluster import KMeans
from sklearn_extra.cluster import KMedoids      # doesn't install through conda; pip install needed
from scipy.special import comb    # for computing number of combinations
# from scipy.cluster.vq import vq     # get centroids at the corresponding closest solution
import matplotlib
import matplotlib.pyplot as plt
# uncommenting the two lines below appears to have no effect
# import seaborn as sns
# sns.set()  # plot styling

'''
# import sys
import os
import collections   # for Counter()
# from mpl_toolkits import Axes3D   error: cannot import name 'Axes3D' from 'mpl_toolkits' (unknown location)
# from mpl_toolkits.mplot3d import Axes3D   # this works OK
# import csv
# import sklearn    # this import is not needed; sklearn was installed as scikit-learn, and recognized by pyCharm
# from sklearn.preprocessing import scale
# from sklearn.preprocessing import normalize
# from sklearn.preprocessing import MinMaxScaler
'''


class Cluster:
    def __init__(self, rep):
        self.rep = rep      # Report object, contains: config,  dfs with solutions
        self.crit = rep.wflow.mc.cr      # criteria specs
        self.cr_names = rep.cr_names
        self.df_sol = rep.wflow.par_rep.df_sol      # df with all Pareto sols
        self.sols = pd.DataFrame()      # df with CAFs of sols to be clustered (col names == cr_names)
        for cr in self.cr_names:
            name = f'a_{cr}'
            self.sols[cr] = self.df_sol[name]
        self.n_sols = len(self.sols)
        self.sol2cl = None  # list of cluster id for each solution: y_means returned by kmeans.predict()
        self.centers = None     # centers of clusters
        self.medoids = None     # medoids of clusters (solutions closest to the corresponding cluster-center)
        self.cl_memb = []  # number of members in each cluster
        self.cl_rad = []  # radius of each cluster

    def mk_clust(self, n_clust):
        print(f'\nClustering {self.n_sols} Pareto solutions into {n_clust} clusters.')
        print(f'Statistics of the criteria achievements:\n{self.sols.describe()}')
        kmeans = KMeans(n_clusters=n_clust, random_state=5, n_init='auto')
        # kmeans.fit(self.sols)     # fitting a df works but matrix of solutions is expected
        points = self.sols.to_numpy()    # matrix of solutions
        kmeans.fit(points)
        # self.sol2cl = kmeans.predict(self.sols)
        self.sol2cl = kmeans.predict(points)
        self.centers = kmeans.cluster_centers_
        print(f'Centers:\n{self.centers}')

        # medoids
        kmedoids = KMedoids(n_clusters=n_clust, random_state=5).fit(points)
        self.medoids = kmedoids.cluster_centers_
        print(f'Medoids:\n{self.medoids}')
        # self.centers.sort(axis=0)     # sorting centers requires the corresponding modifications of sol2cl
        # print(f'Sorted (by 0-th crit) centers: \n{self.centers}')

        # todo: discuss whether to use centers or medoids, or maybe both, or provide selection through cfg.yml
        # number of sols and radius
        for i_clus, center in enumerate(self.centers):  # loop on clusters
            n_memb = 0      # number of members in the cluster
            max_dist = 0.   # max distance of cluster-members from the center
            for i_sol in range(self.n_sols):
                if kmeans.labels_[i_sol] != i_clus:
                    continue    # i_sol does not belong to the current cluster
                n_memb += 1
                # distance between center and the current member-sol
                dist = np.sqrt(np.sum([(a-b)**2 for a, b in zip(center, self.sols.iloc[i_sol])]))
                if dist > max_dist:
                    max_dist = dist
            self.cl_memb.append(n_memb)
            self.cl_rad.append(round(max_dist, 2))
            cent_coord = ''   # string with rounded center coordinates
            sep = ''
            for i, coord in enumerate(center):
                coor_int = int(coord + 0.5)
                # cent_coord = f'{cent_coord}{sep}{self.cr_names[i]}={coor_int}'
                cent_coord += f'{sep}{self.cr_names[i]}={coor_int}'
                sep = ', '
            print(f'Cluster {i_clus}: members = {n_memb:2d}, radius = {max_dist:.1f}, center = [{cent_coord}]')

        # pass
        # raise Exception('Cluster::mk_lust() - not implemented yet.')

        # medoids used above instead of the alternative vq approach described at:
        # https://stackoverflow.com/questions/21660937/get-nearest-point-to-centroid-scikit-learn
        # todo: discuss whether to use sklearn-extra or implement vq instead
        pass

    def plots(self):
        # raise Exception('Cluster::plots() - not implemented yet.')
        # color preparation
        cent_cmap = []  # color-levels (normalized to [0, 1]) for each center
        n_crit = len(self.cr_names)
        n_clust = len(self.centers)
        for i in range(n_clust):
            cent_cmap.append(float(i) / (float(n_clust) - 1.))
        # print('color levels of centers (normalized to [0,1]): ', cent_cmap)
        # clust_int = kmeans.labels_  # cluster numbers/ids for each point (int by default)
        clust_int = self.sol2cl  # cluster numbers/ids for each point (int by default)
        clust_float = clust_int.astype(np.float32)
        # print('colors (positions in cmap) of points before normalizing to [0,1]:\n', clust_float)
        clust_float = np.multiply(clust_float, 1. / max(clust_float))  # after [0,1] normalization

        # cmap selection
        # see https://matplotlib.org/3.1.0/tutorials/colors/colormaps.html
        # a selection of popular colormaps: viridis, PiYG, PRGn, RdYlGn, winter, Spectral;
        # good for clusters: brg, Dark2, tab10
        # NOT good: Paired
        # see https://matplotlib.org/3.1.0/tutorials/colors/colormaps.html
        # cmap = matplotlib.cm.get_cmap('brg')  # deprecated; updated code below
        cmap = matplotlib.colormaps['brg']

        # 2D plots first
        # rcParams['figure.figsize'] = 6, 8  # error: name 'rcParams' is not defined
        # configure number and locations of plots
        # n_plots = int((n_crit * (n_crit - 1)) / 2)   # number of pairs for n_crit
        n_plots = comb(n_crit, 2, exact=True)  # number of pairs for n_crit
        n_plots += 1  # additional subplot with comments
        n_perrow = 3
        n_percol = int(float(n_plots) / float(n_perrow))
        if n_percol * n_perrow < n_plots:
            n_percol += 1
        fig_heig = 3.5 * n_percol
        print(f'\nFigure with 2D-plots of {n_plots - 1} pairs of criteria.')

        fig1 = plt.figure(figsize=(12, fig_heig))  # y was 10 (for one chart)
        fig1.subplots_adjust(wspace=0.3, hspace=0.4)

        i_plot = 0  # current plot number (subplots numbers from 1)
        ax = []
        for i_first, name1 in enumerate(self.cr_names):
            for i_second in range(i_first + 1, n_crit):
                name2 = self.cr_names[i_second]
                # print('Plot', i_plot + 1, 'pair (', name1, ',', name2, ')')
                print(f'Plot {i_plot}: pair ({name1}, {name2})')
                ax.append(fig1.add_subplot(n_percol, n_perrow, i_plot + 1))  # subplots numbered from 1
                ax[i_plot].set_xlabel(name1)
                ax[i_plot].set_ylabel(name2)
                ax[i_plot].set_title(name1 + ' vs ' + name2)
                ax[i_plot].scatter(x=self.sols[name1], y=self.sols[name2], c=cmap(clust_float), s=20)
                for i in range(n_clust):
                    ax[i_plot].scatter(x=self.centers[i, i_first], y=self.centers[i, i_second],
                                       # color = cmap(cent_cmap[i]), s = 250)
                                       marker='h', linewidths=5, edgecolor=cmap(cent_cmap[i]),
                                       facecolor="None", s=250)
                i_plot += 1

        ax.append(fig1.add_subplot(n_percol, n_perrow, i_plot + 1))  # last subplot with text/comments
        ax[i_plot].axis('off')
        ax[i_plot].set_title('Information about clusters')
        ax[i_plot].invert_yaxis()
        txt = []
        for i in range(n_clust):
            txt.append(f'Cluster {str(i)}:  members {self.cl_memb[i]:2d}, radius = {self.cl_rad[i]:.2f}')
            # print(txt[i])
            ax[i_plot].text(0.01, 0.1 + 0.1 * i, txt[i], color=cmap(cent_cmap[i]), fontsize=12)

        # fig1_file = f'{}fig_pref + str(n_clust) + '_2D.png'
        # fig1_file = f'{fig_pref}{str(n_clust)}_2D.png'
        # plt.savefig(fig1_file, bbox_inches='tight')
        # print('Scatter 2D-plots saved to: ', fig1_file)
        # plt.show()   # if commented then plot is shown together with Fig. 2

        # 3D charts follow 2D charts
        # NOTE: interactive 3D plots don't work with subplots

        # confusions, if redefined here?
        # %matplotlib notebook
        # %matplotlib

        # configure number and locations of plots
        n_plots = comb(n_crit, 3, exact=True)  # number of triples for n_crit
        # n_plots += 1    # subplot with comments
        n_perrow = 2
        n_percol = int(float(n_plots) / float(n_perrow))
        if n_percol * n_perrow < n_plots:
            n_percol += 1
        # fig_heig = 10 * n_percol
        # print('number of plots:', n_plots, ', n_rows', n_percol, ', n_cols', n_perrow)
        print(f'\nFigure with 3D-of plots of {n_plots} triplets of criteria.')

        # fig = plt.figure(figsize = (12,fig_heig))   # y was 10
        # fig.subplots_adjust(wspace=0.3, hspace=0.4)
        fig = plt.figure(figsize=(12, 10))

        i_plot = 0  # current plot number (subplots numbers from 1)
        ax = []
        for i_first, name1 in enumerate(self.cr_names):
            for i_second in range(i_first + 1, n_crit):
                name2 = self.cr_names[i_second]
                for i_third in range(i_second + 1, n_crit):
                    name3 = self.cr_names[i_third]
                    # print('Plot', i_plot + 1, 'triplet (', name1, ',', name2, ',', name3, ')')
                    print(f'Plot {i_plot}: criteria ({name1}, {name2}, {name3})')
                    ax.append(
                        fig.add_subplot(n_percol, n_perrow, i_plot + 1, projection='3d'))  # subplots numbered from 1
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
                    ax[i_plot].scatter(xs=self.sols[name1], ys=self.sols[name2], zs=self.sols[name3],
                                       # c = col_theme[kmeans.labels_], s = 50) # cmap='viridis' colors according values
                                       c=cmap(clust_float), s=20)
                    # ax[i_plot].scatter(x = sample[name1], y = sample[name2], c = cmap(clust_float), s = 50)
                    for i in range(n_clust):
                        ax[i_plot].scatter(xs=self.centers[i, i_first], ys=self.centers[i, i_second],
                                           zs=self.centers[i, i_third],
                                           marker='h', facecolor=(0, 0, 0, 0),  # cmap(cent_cmap[i]),
                                           linewidths=5, edgecolor=cmap(cent_cmap[i]), s=250)
                        # the below does not work in 3D, facecolor not accepted
                        # marker='h', edgecolor=cmap(cent_cmap[i]), facecolor="None", s = 250)
                    i_plot += 1

        # ax.append(fig.add_subplot(n_percol, n_perrow, i_plot + 1))  # last subplot 2D with text/comments
        # ax[i_plot].axis('off')
        # ax[i_plot].set_title('Information about clusters')
        # ax[i_plot].invert_yaxis()
        # txt = []
        # for i in range(n_clust):
        #    txt.append('Cluster ' + str(i) +', members ' + str(cl_memb[i]) + ', radius = ' +str(cl_radius[i]))
        #    print(txt[i])
        #    ax[i_plot].text(0.01, 0.1 + 0.1 * i, txt[i], color = cmap(cent_cmap[i]), fontsize=12)

        # fig_file = fig_pref + str(n_clust) + '_3D.png'
        # fig_file = f'{fig_pref}{str(n_clust)}_3D.png'
        # plt.savefig(fig_file, bbox_inches='tight')  # saved plots are not interactive
        # print('Scatter 3D-plots saved to: ', fig_file)
        # show is applied to all Figs in another place
        # plt.show()
        # pass

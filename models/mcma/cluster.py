""" Clustering pymcma solutions, Marek Makowski, IIASA"""
# import math
import sys
import pandas as pd
import numpy as np
# from sklearn.cluster import KMeans
from matplotlib.gridspec import GridSpec
from scipy.special import comb    # for computing number of combinations
# from scipy.cluster.vq import vq     # get centroids at the corresponding closest solution
import matplotlib
import matplotlib.pyplot as plt
# uncommenting the two lines below appears to have no effect
# import seaborn as sns
# sns.set()  # plot styling

try:
    from sklearn_extra.cluster import KMedoids      # on macOS: doesn't install through conda; pip install needed
except ModuleNotFoundError:
    print("""Your installation of pyMCMA is not completed!
In order to finish your installation please install scikit-learn-extra package.
It can be installed either by conda:

conda install scikit-learn-extra

or by pip (on macos-arm64 systems):

pip install --no-deps scikit-learn-extra

For the detailed instructions refer to the online documentation:
https://pymcma.readthedocs.io/readme.html""")
    sys.exit(1)

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


# noinspection SpellCheckingInspection
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
        self.n_clust = None  # number of clusters (to be defined in ::mk_clust()
        # noinspection SpellCheckingInspection
        self.cl_memb = []  # number of members in each cluster
        self.cl_rad = []  # radius of each cluster

    def mk_clust(self, n_clust):
        self.n_clust = n_clust
        print(f'\nClustering {self.n_sols} Pareto solutions into {n_clust} clusters.')
        print(f'Statistics of the criteria achievements:\n{self.sols.describe()}')
        points = self.sols.to_numpy()    # matrix of solutions

        # KMeans ready to use but currently not used
        # kmeans = KMeans(n_clusters=n_clust, random_state=5, n_init='auto')
        # # kmeans.fit(self.sols)     # fitting a df works but matrix of solutions is expected
        # kmeans.fit(points)
        # self.sol2cl = kmeans.predict(self.sols)
        # self.sol2cl = kmeans.predict(points)
        # self.centers = kmeans.cluster_centers_
        # print(f'Centers:\n{self.centers}')
        #
        # self.centers.sort(axis=0)     # sorting centers requires the corresponding modifications of sol2cl
        # print(f'Sorted (by 0-th crit) centers: \n{self.centers}')
        # centers = self.centers

        # medoids
        kmedoids = KMedoids(n_clusters=n_clust, random_state=5).fit(points)
        self.sol2cl = kmedoids.predict(points)
        self.medoids = kmedoids.cluster_centers_
        sol_labels = kmedoids.labels_
        centers = self.medoids
        print(f'Medoids:\n{self.medoids}')

        # number of sols and radius
        for i_clus, center in enumerate(centers):  # loop on clusters
            # noinspection SpellCheckingInspection
            n_memb = 0      # number of members in the cluster
            max_dist = 0.   # max distance of cluster-members from the center
            for i_sol in range(self.n_sols):
                if sol_labels[i_sol] != i_clus:
                    continue    # i_sol does not belong to the current cluster
                n_memb += 1
                # distance between center/medoid and the current member-sol
                # tmp = self.sols.iloc[i_sol]
                # distx = np.sqrt(np.sum([(a-b)**2 for a, b in zip(center, self.sols.iloc[i_sol])]))
                dist = np.sqrt(np.sum((center - self.sols.iloc[i_sol])**2))
                # print(f'Dist: {dist}, {distx = }')
                if dist > max_dist:
                    max_dist = dist
                    # # print(f'i_clus {i_clus}, i_sol {i_sol} ({tmp}) {center = }, new max distance: {max_dist}')
                    # if i_clus == 4 and i_sol == 1:
                    #     xx = 0
                    #     for a, b in zip(center, tmp):
                    #         xx += (a - b)**2
                    #         print(f'{a = }, {b = }, {xx = }')
                    #     xxx = np.sqrt(xx)
                    #     print(f'{xxx = }')

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

        # find ranges of criteria values in solutions belonging to each cluster
        # infty = float(math.inf)
        # infty2 = np.inf
        # x1 = min(15, infty)
        # x2 = max(15, infty)
        vMin = pd.DataFrame(columns=self.cr_names, index=range(self.n_clust))    # crit. min-values (index = cluster)
        # vMin.fillna(infty, inplace=True)  # not necessary (empty df are with NaN, min/max replaces them with new val)
        vMax = pd.DataFrame(columns=self.cr_names, index=range(self.n_clust))    # crit. max-values (index = cluster)
        # vMax.fillna(-infty, inplace=True)     # fillna() deprecated, hence better refrain from using it.
        for i_clus, sol in zip(sol_labels, points):  # loop on cluster-labels and solutions
            for i_cr, cr_val in enumerate(sol):     # criteria values in the current solution
                oldMin = vMin.iat[i_clus, i_cr]     # access by indices of: row, col
                newMin = min(cr_val, oldMin)
                vMin.iat[i_clus, i_cr] = newMin
                oldMax = vMax.iat[i_clus, i_cr]
                newMax = max(cr_val, oldMax)
                vMax.iat[i_clus, i_cr] = newMax

        print(f'\nCriteria min-achievements (by clusters):\n{vMin}')
        print(f'Criteria max-achievements (by clusters):\n{vMax}')

        # convert achievements to crit-values
        for i_cr, cr in enumerate(self.crit):  # loop on criteria
            for i_clust in range(self.n_clust):     # loop on clusters
                aval = vMin.iat[i_clust, i_cr]
                cr_val = cr.ach2val(aval)
                vMin.iat[i_clust, i_cr] = cr_val
                aval = vMax.iat[i_clust, i_cr]
                cr_val = cr.ach2val(aval)
                vMax.iat[i_clust, i_cr] = cr_val
                pass

        print(f'\nCriteria min-values (by clusters):\n{vMin}')
        print(f'Criteria max-values (by clusters):\n{vMax}')
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
        n_clust = self.n_clust
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
        # n_plots += 1  # additional subplot with comments
        n_perrow = 3
        n_percol = int(float(n_plots) / float(n_perrow))
        if n_percol * n_perrow < n_plots:
            n_percol += 1
        fig_heig = 2 * n_percol
        print(f'\nFigure with 2D-plots of {n_plots - 1} pairs of criteria.')

        fig1 = plt.figure(figsize=(7, fig_heig), dpi=self.rep.plots.dpi)  # y was 10 (for one chart)

        cent = self.medoids     # use medoids as centers in the plots
        # cent = self.centers     # use Kmeans.centers as centers in the plots

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
                    ax[i_plot].scatter(x=cent[i, i_first], y=cent[i, i_second],
                                       # color = cmap(cent_cmap[i]), s = 250)
                                       marker='h', linewidths=2, edgecolor='black',
                                       facecolor=cmap(cent_cmap[i]), s=150)
                i_plot += 1

        # ax.append(fig1.add_subplot(n_percol, n_perrow, i_plot + 1))  # last subplot with text/comments
        # ax[i_plot].axis('off')
        # ax[i_plot].set_title('Information about clusters')
        # ax[i_plot].invert_yaxis()
        # ax[i_plot].view_init(elev=15, azim=45, roll=0)
        # txt = []
        # for i in range(n_clust):
        #     txt.append(f'Cluster {str(i)}:  members {self.cl_memb[i]:2d}, radius = {self.cl_rad[i]:.2f}')
        #     # print(txt[i])
        #     ax[i_plot].text(0.01, 0.1 + 0.1 * i, txt[i], color=cmap(cent_cmap[i]), fontsize=8)

        plt.tight_layout()
        self.rep.plots.figures['cluster2D'] = fig1

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
        if n_plots == 1:
            n_percol = n_perrow = 1
        else:
            n_perrow = 2
            n_percol = n_plots // n_perrow
            if n_percol * n_perrow < n_plots:
                n_percol += 1
        # fig_heig = 10 * n_percol
        # print('number of plots:', n_plots, ', n_rows', n_percol, ', n_cols', n_perrow)
        print(f'\nFigure with 3D-of plots of {n_plots} triplets of criteria.')

        # Fig with solutions and either Kmeans.centers or medoids
        dpi = self.rep.plots.dpi
        fig = plt.figure(figsize=(3.5 * n_perrow, 2.5 * n_percol), dpi=dpi)
        fig.set_facecolor('#EAEAF2')
        gridspec_params = dict(hspace=0.15, wspace=0.05, left=0.05, right=0.95, bottom=0.1, top=0.9)
        gs = GridSpec(n_percol, n_perrow, fig, **gridspec_params)

        fig2 = plt.figure(figsize=(3.5 * n_perrow, 2.5 * n_percol), dpi=dpi)     # separate Fig with medoids
        fig2.set_facecolor('#EAEAF2')
        gs2 = GridSpec(n_percol, n_perrow, fig2, **gridspec_params)

        i_plot = 0  # current plot number (subplots numbers from 1)
        ax = []
        ax2 = []
        for i_first, name1 in enumerate(self.cr_names):
            for i_second in range(i_first + 1, n_crit):
                name2 = self.cr_names[i_second]
                for i_third in range(i_second + 1, n_crit):
                    name3 = self.cr_names[i_third]
                    # print('Plot', i_plot + 1, 'triplet (', name1, ',', name2, ',', name3, ')')
                    print(f'Plot {i_plot}: criteria ({name1}, {name2}, {name3})')
                    ax.append(
                        fig.add_subplot(gs[i_plot], projection='3d', computed_zorder=False))
                    ax[i_plot].set_xlabel(name1)
                    ax[i_plot].set_ylabel(name2)
                    ax[i_plot].set_zlabel(name3)
                    ax[i_plot].view_init(elev=15, azim=45, roll=0)
                    ax2.append(
                        fig2.add_subplot(gs2[i_plot], projection='3d', computed_zorder=False))
                    ax2[i_plot].set_xlabel(name1)
                    ax2[i_plot].set_ylabel(name2)
                    ax2[i_plot].set_zlabel(name3)
                    ax2[i_plot].view_init(elev=15, azim=45, roll=0)
                    sub_title = name1 + ' vs ' + name2 + ' vs ' + name3
                    # Placement 0, 0 would be the bottom left, 1, 1 would be the top right.
                    ax[i_plot].text2D(0.05, 0.95, sub_title, transform=ax[i_plot].transAxes)
                    ax2[i_plot].text2D(0.05, 0.95, sub_title, transform=ax2[i_plot].transAxes)
                    # the above places title at the controlled place, the below at the center too close to chart
                    # ax[i_plot].set_title(name1 +' vs ' + name2 + ' vs ' + name3)

                    # ax.set_zlim(1e+6, 3e+6)   # replaced by the min/max normalization to [0,1]
                    # ax.view_init(60, -50)  # 70 above x-y plane, 50 rotate 50 degr, counter-clockwise about z-xis
                    ax[i_plot].scatter(xs=self.sols[name1], ys=self.sols[name2], zs=self.sols[name3],
                                       # c = col_theme[kmeans.labels_], s = 50) # cmap='viridis' colors according values
                                       c=cmap(clust_float), s=20, alpha=0.5, zorder=4)
                    # ax[i_plot].scatter(x = sample[name1], y = sample[name2], c = cmap(clust_float), s = 50)
                    for i in range(n_clust):
                        ax[i_plot].scatter(xs=cent[i, i_first], ys=cent[i, i_second],
                                           zs=cent[i, i_third],
                                           marker='h', facecolor=cmap(cent_cmap[i]),  # cmap(cent_cmap[i]),
                                           linewidths=2, edgecolor='black', s=100, zorder=5)
                        ax2[i_plot].scatter(xs=cent[i, i_first], ys=cent[i, i_second],
                                            zs=cent[i, i_third],
                                            marker='h', facecolor=cmap(cent_cmap[i]),  # cmap(cent_cmap[i]),
                                            linewidths=2, edgecolor='black', s=100)
                        # the below does not work in 3D, facecolor not accepted
                        # marker='h', edgecolor=cmap(cent_cmap[i]), facecolor="None", s = 250)
                    i_plot += 1

        self.rep.plots.figures['cluster3D'] = fig
        self.rep.plots.figures['centres3D'] = fig2

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

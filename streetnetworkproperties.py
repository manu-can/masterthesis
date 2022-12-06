import os
import time
import multiprocessing as mp

from utils.utils import *
from utils.graph_indices import *


def network_properties(routeid, city, extent, path, routes):
    print(routeid)
    id = routeid

    t1 = time.time()
    path_sub = os.path.join(path, '02_Subgraphs', city)
    path_res = os.path.join(path, '03_StreetNetworkProperties', extent)

    # read clipped graph of selected area extent
    graph = NetworkGraph(os.path.join(path_sub, extent, '{:s}_nx_graph_{:02d}.p'.format(city[3:].lower(), routeid)))

    # read convex hull polygon shape
    polygon = nx.read_gpickle(os.path.join(path_sub, extent, '{:s}_polygon_{:02d}.p'.format(city[3:].lower(), routeid)))

    # feature/property computation for defined area
    features = indices(routeid, graph, polygon, routes[routeid])

    # store features as csv
    features.to_csv(os.path.join(path_res, '{:s}_properties_{:02d}.csv'.format(city[3:].lower(), routeid)), index=False)
    print(id, '{:.2f} min'.format((time.time() - t1) / 60))


if __name__ == '__main__':
    '''
    - script to extract street network properties
    
    -> select city
    -> select area extent
    '''

    #####################################################
    path_data = os.path.join(os.path.normpath(os.getcwd() + os.sep + os.pardir), '01_Data')

    # ARGUMENTS TO SET
    # ------------------------------------------------------------------------------------#
    city = '01_Vienna'  # 01_Vienna, 02_Mexico, 03_Djibouti
    size = 'big'  # big, medium, small
    # ------------------------------------------------------------------------------------#

    path_orig = os.path.join(path_data, '01_Original', city)
    path_graph = os.path.join(path_orig, [f for f in os.listdir(path_orig) if 'nx_graph_with_ec_with_bearing' in f][0])
    path_routes = os.path.join(path_orig, [f for f in os.listdir(path_orig) if 'random_routes' in f][0])
    files = [f for f in os.listdir(path_orig) if 'our_approach' in f]

    # routes, graph and ids
    routes = nx.read_gpickle(path_routes)
    graph = NetworkGraph(path_graph)
    routeIDs = list(range(100))

    # compute street network properties
    pool = mp.Pool(int(mp.cpu_count() - 2))
    pool.starmap_async(network_properties, [(r, city, size, path_data, routes) for r in routeIDs]).get()
    pool.close()
    pool.join()

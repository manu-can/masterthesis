import multiprocessing as mp

from utils.processing import *


if __name__ == '__main__':
    '''
    - script for preprocessing
    - can be used to clip a graph (set function to 'clipping', select size)
    - can be used to compute local centalities (set function to 'centralities')
     
    -> select city
    -> select clipping of subgraphs or local centrality computation
    '''

    #####################################################
    path_data = os.path.join(os.path.normpath(os.getcwd() + os.sep + os.pardir), '01_Data')

    # ARGUMENTS TO SET
    # ------------------------------------------------------------------------------------#
    city = '03_Djibouti'    # 01_Vienna, 02_Mexico, 03_Djibouti
    function = 'clipping'  # clipping, centralities
    size = 'small'         # None, boundingbox, subgraphs, big, medium, small
    # ------------------------------------------------------------------------------------#

    path_orig = os.path.join(path_data, '01_Original', city)
    path_sub = os.path.join(path_data, '02_Subgraphs', city)
    path_graph = os.path.join(path_orig, [f for f in os.listdir(path_orig) if 'nx_graph_with_ec_with_bearing' in f][0])
    path_routes = os.path.join(path_orig, [f for f in os.listdir(path_orig) if 'random_routes' in f][0])

    # routes, graph and ids
    routes = nx.read_gpickle(path_routes)
    graph = NetworkGraph(path_graph)
    ids = list(range(100))

    # radius for local centrality computation
    radius = 800

    # multiprocessing: one route per node
    pool = mp.Pool(int(mp.cpu_count() - 1))

    if function == 'clipping':
        pool.starmap_async(graph_clipping, [(id, city, graph, routes, path_sub, size) for id in ids]).get()
    elif function == 'centralities':
        pool.starmap_async(local_centrality_computation, [(id, city, path_sub, radius) for id in ids]).get()
    else:
        print('Please set the variable function to a valid input (clipping or centralities).')
import os
import time
import multiprocessing as mp

from utils.utils import *


def process(file, data, routeid, graph, routes, path):
    print(file, routeid)
    t0 = time.time()

    # shortest path
    sp = routes[routeid]
    sp_nodes = graph.get_nodes_of_route(sp)
    sp_length = sum([graph.get_edge_attribute('length_utm_m', edge=i) for i in sp])

    # use pre-computed csv with node length (for node ratio)
    nodeset = pd.read_csv(os.path.join(path, 'node_ratios', 'route_{:02d}.csv'.format(routeid)))
    nodeset['l'] = nodeset['l'] / sp_length

    nodeset_tot = pd.DataFrame(columns=['id', 'x', 'y', 'l'])

    for a in range(3000):
        suc = data.data.success[(data.data.route_id == routeid) & (data.data.agent_id == a)].iloc[0]
        dat = data.get_filtered_data(agent=a, route=routeid)

        edges = dat.path_taken_edges.apply(eval)
        nodes = graph.get_nodes_of_route(edges[0])

        nodelist = pd.DataFrame.from_dict(nodes)
        nodelist['agent_id'] = a
        nodelist['route_id'] = routeid
        nodelist['success'] = suc
        nodelist = pd.merge(nodelist, nodeset[['id', 'l']], on=['id'])

        nodeset_tot = pd.concat([nodeset_tot, nodelist], ignore_index=True)

    name = file[-30:-4]
    if 'perc' in name:
        folder = 'dji_prc' if 'dji' in name else 'mex_prc' if 'mex' in name else 'vie_prc'
    else:
        folder = 'dji_fch' if 'dji' in name else 'mex_fch' if 'mex' in name else 'vie_fch'

    isExist = os.path.exists(os.path.join(path, 'boundingbox', 'alltakennodes', folder))
    if not isExist:
        os.makedirs(os.path.join(path, 'boundingbox', 'alltakennodes', folder))

    save_path = os.path.join(path, 'boundingbox', 'alltakennodes', folder, 'route_{:02d}_taken.csv'.format(routeid))
    nodeset_tot.to_csv(save_path)

    print('Route ID: {:02d}, Time: {:.2f}'.format(routeid, time.time() - t0))

if __name__ == '__main__':
    '''
    - script to compute and store node ratios of all taken nodes of Vienna's 6 simulation datasets 
    - needed for data driven reduction of the node ratio threshold
    '''

    #####################################################
    path_data = os.path.join(os.path.normpath(os.getcwd() + os.sep + os.pardir), '01_Data')

    city = '01_Vienna'

    path_orig = os.path.join(path_data, '01_Original', city)
    path_sub = os.path.join(path_data, '02_Subgraphs', city)
    path_graph = os.path.join(path_orig, [f for f in os.listdir(path_orig) if 'nx_graph_with_ec_with_bearing' in f][0])
    path_routes = os.path.join(path_orig, [f for f in os.listdir(path_orig) if 'random_routes' in f][0])
    files = [f for f in os.listdir(path_orig) if 'our_approach' in f]

    # routes, graph and ids
    routes = nx.read_gpickle(path_routes)
    graph = NetworkGraph(path_graph)

    routeIDs = list(range(100))

    data = []
    for f in files:
        data.append(AgentData(os.path.join(path_orig, f)))

    pool = mp.Pool(mp.cpu_count() - 1)
    pool.starmap_async(process, [(files[i], data[i], r, graph, routes, path_sub)
                                 for i in range(len(files)) for r in routeIDs]).get()
    pool.close()
    pool.join()

import momepy as mm
import time, os

from utils.utils import *
from utils.area_definitions import *

def local_centrality_computation(routeid, city, path, radius):
    t1 = time.time()

    # read subgraph
    g_sub = NetworkGraph(os.path.join(path, 'subgraphs', '{:s}_nx_graph_{:02d}.p'.format(city[3:].lower(), routeid)))

    # CENTRALITY COMPUTATIONS
    # local closeness centralities
    g_sub.graph = mm.closeness_centrality(g_sub.graph, radius=radius, distance='length_utm_m',
                                              weight='length_utm_m', name='cc'+str(radius))

    # local betweenness centralities
    c_g_sub = nx.MultiGraph(g_sub.keep_only_shortest_edge())  # chosen shortest edge of parallel edges
    c_g_sub = mm.betweenness_centrality(c_g_sub, radius=radius, distance='length_utm_m',
                                            weight='length_utm_m', name='cb'+str(radius))
    for n in g_sub.nodes:
        try:
            g_sub.graph.nodes[n]['cb'+str(radius)] = c_g_sub.nodes[n]['cb'+str(radius)]
        except KeyError:
            g_sub.graph.nodes[n]['cb'+str(radius)] = float('NaN')

    # local straightness centralities
    g_sub.graph = mm.straightness_centrality(g_sub.graph, radius=radius, distance='length_utm_m',
                                                 weight='length_utm_m', name='cs'+str(radius), normalized=False)

    # store modified subgraph
    path_out = os.path.join(path, 'subgraphs_with_centralities', '{:s}_nx_graph_{:02d}.p'.format(city[3:].lower(), routeid))
    nx.write_gpickle(g_sub.graph, path_out)

    print(routeid, '{:.2f} min'.format((time.time() - t1) / 60))


def graph_clipping(routeid, city, graph, routes, path, size):
    t1 = time.time()

    # shortest path, nodes and length
    sp = routes[routeid]
    sp_nodes = graph.get_nodes_of_route(sp)
    sp_length = sum([graph.get_edge_attribute('length_utm_m', edge=i) for i in sp])

    buffer = 1

    # clipping of graph to selected size
    if size == 'boundingbox':
        # boundingbox around shortest path plus buffer of half the shortest path length
        buffer = sp_length / 2
        n_minmax = area_min_max(graph, sp_nodes, buffer)
        g_sub = NetworkGraph('', graph=graph.graph, nodelist=n_minmax['id'])

    elif size == 'subgraphs':
        # subgraphs based on node ratio threshold 1.5, no local centrality attributes present yet
        thresh = 1.5

        # use pre-computed csv with node length (for node ratio)
        node_ratios = pd.read_csv(os.path.join(path, 'boundingbox', 'node_ratios', 'route_{:02d}.csv'.format(routeid)))
        g_clipped = NetworkGraph('', graph=graph.graph, nodelist=node_ratios.id)
        _, n_spnode = area_node_ratios(g_clipped, node_ratios, sp_length, thresh, buffer)
        g_sub = NetworkGraph('', graph=graph.graph, nodelist=n_spnode['id'])

    elif size == 'big' or size == 'medium' or size == 'small':
        # subgraphs based on node ratios (BIG, MEDIUM, SMALL AREAS), local centrality attributes have to be added first!
        thresh = 1.5 if size == 'big' else 1.346 if size == 'medium' else 1.203 if size == 'small' else 0

        # use pre-computed csv with node length (for node ratio)
        node_ratios = pd.read_csv(os.path.join(path, 'boundingbox', 'node_ratios', 'route_{:02d}.csv'.format(routeid)))
        g = NetworkGraph(os.path.join(
            path, 'subgraphs_with_centralities', '{:s}_nx_graph_{:02d}.p'.format(city[3:].lower(), routeid)))
        _, n_spnode = area_node_ratios(g, node_ratios, sp_length, thresh, buffer)
        g_sub = NetworkGraph('', graph=g.graph, nodelist=n_spnode['id'])

    else:
        print('Set the variable size to a valid input (boundingbox, subgraphs, big, medium, small).')
        return


    # store clipped subgraph
    path_out = os.path.join(path, size, '{:s}_nx_graph_{:02d}.p'.format(city[3:].lower(), routeid))
    nx.write_gpickle(g_sub.graph, path_out)


    # compute and store node length of all nodes in boundingbox (easier access for later computations)
    if size == 'boundingbox':
        # l = shortest path(start - n) + shortest path(n - end)
        nodeset = pd.DataFrame(g_sub.nodes, columns=['id'])
        temp = np.zeros((len(nodeset), 3))
        for n in range(len(nodeset)):
            try:
                sp1 = nx.shortest_path_length(g_sub.graph, sp_nodes['id'][0], nodeset.id.iloc[n], weight='length_utm_m')
                sp2 = nx.shortest_path_length(g_sub.graph, nodeset.id.iloc[n], sp_nodes['id'][-1],
                                              weight='length_utm_m')
                l = sp1 + sp2
            except:
                l = 0
            pt = g_sub.nodes[nodeset.id.iloc[n]]['geom_utm']
            temp[i, :] = np.array([pt.x, pt.y, l])
        nodeset = pd.concat([nodeset, pd.DataFrame(temp, columns=['x', 'y', 'l'])], axis=1)

        save_path = os.path.join(path, size, 'node_ratios', 'route_{:02d}.csv'.format(routeid))
        nodeset.to_csv(save_path, index=False)

    print(routeid, '{:.2f} min'.format((time.time() - t1) / 60))
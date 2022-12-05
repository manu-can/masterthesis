import pandas as pd
import numpy as np
import networkx as nx
import osmnx as ox
import copy
from shapely.geometry import Point


def indices(id, graph, polygon, route):

    # shortest path, nodes and length
    sp_nodes = graph.get_nodes_of_route(route)
    start, end = sp_nodes['id'][0], sp_nodes['id'][-1]
    sp_length = sum([graph.get_edge_attribute('length_utm_m', edge=i) for i in route])

    # allowed detour length (50% of the shortest path length)
    detour = sp_length * 0.5

    # minimum node bearing difference to destination (added as attribute to nodes of graph)
    node_bearing_to_dest_attribute(graph, end)
    nd_dest = [graph.nodes[n]['min_bearing_to_dest'] for n in graph.nodes]

    # dictionaries with local centralities (key is node id)
    cc800 = {n: graph.nodes[n]['cc800'] for n in graph.nodes}
    cb800 = {n: graph.nodes[n]['cb800'] for n in graph.nodes}
    cs800 = {n: graph.nodes[n]['cs800'] for n in graph.nodes}

    columns = ['route_id', 'segments', 'intersections', 'area', 'length', 'intersection_density_a',
               'street_density', 'graph_density', 'mean_node_degree', 'mean_segment_length',
               'deadend_perc', 'mean_deadend_length',
               'detour_to_mean_segment_ratio', 'detour_to_mean_deadend_ratio',
               'perc_3_way', 'perc_4_way', 'perc_3_4_way', 'perc_reg_3_way', 'perc_reg_4_way', 'perc_reg_int',
               'straightness_perc', 'area_circularity', 'orientation_order', 'mean_bearing_to_dest',
               'mean_cc800', 'mean_cb800', 'mean_cs800',
               'edge_connectivity', 'node_connectivity',
               'deadend_start', 'deadend_end',
               'cc800_start', 'cc800_end',
               'cb800_start', 'cb800_end',
               'cs800_start', 'cs800_end']

    # STREET NETWORK PROPERTIES
    route_id = id
    segments = graph.graph.size()                                           # number of segments []
    intersections = graph.graph.order()                                     # number of intersections []
    area = polygon.area / 1e6                                               # area [km²]
    length = graph.graph.size(weight='length_utm_m') / 1e3                  # total street leng[km]
    intersection_density_a = intersections / area                           # intersection density [# / km²]
    street_density = length / area                                          # street density [km / km²]
    graph_density = ((2 * segments) / (intersections * intersections-1))    # graph density []
    mean_node_degree = average_node_degree(graph)                           # mean node degree [# edges / # node]
    mean_segment_length = length * 1e3 / segments                           # mean segment length [m]
    deadend_perc = deadend_percentage(graph)                                # dead end percentage[%]
    mean_deadend_length = deadend_mean_length(graph)                        # mean dead end segment length [m]
    detour_to_segment_ratio = detour / mean_segment_length                  # detour to mean segment length ratio [m/m]
    detour_to_deadend_ratio = detour / mean_deadend_length if not np.isnan(mean_deadend_length) else float('NaN')  # detour to mean dead end segment length ratio[m/m]
    p3, p4, p_3_4_way, p_reg_3, p_reg_4, p_reg_int = intersection_properties(graph)   # intersection percentages [%]
    straightness_perc = straightness_percentage(graph)                      # straightness percentage [%]
    area_circ = area_circularity(polygon)                                   # area circularity []
    orientation_ord = orientation_order(graph)                              # orientation order []
    mean_node_bearing_to_dest = np.nanmean(nd_dest)                         # mean node bearing to destination []
    meanCC800 = np.nanmean(list(cc800.values()))                            # mean local closeness centrality []
    meanCB800 = np.nanmean(list(cb800.values()))                            # mean local betweenness centrality []
    meanCS800 = np.nanmean(list(cs800.values()))                            # mean local straightness centrality []

    # START / END NODE PROPERTIES
    edge_conn = nx.edge_connectivity(graph.graph, start, end)               # edge connectivity, start to end node []
    node_conn = nx.node_connectivity(graph.graph, start, end)               # node connectivity, start to end node []
    deadend_start = 1 if graph.nodes[start]['num_ways'] == 1 else 0         # dead end - start node [y/n]
    deadend_end = 1 if graph.nodes[end]['num_ways'] == 1 else 0             # dead end - end node [y/n]
    cc800_start = cc800[start]                                              # local closeness centrality start node, d=800 []
    cc800_end = cc800[end]                                                  # local closeness centrality, end node, d=800 []
    cb800_start = cb800[start]                                              # local betweenness centrality, start node, d=800 []
    cb800_end = cb800[end]                                                  # local betweenness centrality, end node, d=800 []
    cs800_start = cs800[start]                                              # local straightness centrality, start node, d=800 []
    cs800_end = cs800[end]                                                  # local straightness centrality, end node, d=800 []

    data = [route_id, segments, intersections, area, length, intersection_density_a,
            street_density, graph_density, mean_node_degree, mean_segment_length,
            deadend_perc, mean_deadend_length,
            detour_to_segment_ratio, detour_to_deadend_ratio,
            p3, p4, p_3_4_way, p_reg_3, p_reg_4, p_reg_int,
            straightness_perc, area_circ, orientation_ord, mean_node_bearing_to_dest,
            meanCC800, meanCB800, meanCS800,
            edge_conn, node_conn,
            deadend_start, deadend_end,
            cc800_start, cc800_end,
            cb800_start, cb800_end,
            cs800_start, cs800_end]

    df = pd.DataFrame([data], columns=columns)

    return df


def average_node_degree(graph):
    """
    sum of all incident edges divided by the number of nodes in the graph
    :param graph: NetworkGraph
    :return: mean node degree
    """
    edges = sum([graph.graph.nodes[n]['num_ways'] for n in graph.graph.nodes])
    mean_degree = edges / graph.graph.order()
    return mean_degree


def straightness_percentage(graph):
    """
    percentage of straight street segments of all network edges (same length to mm)
    :param graph: NetworkGraph
    :return: percentage
    """
    count = 0
    for u, v, data in graph.edges(data=True):
        if u != v:
            first, last = graph.graph.nodes[u]['geom_utm'], graph.graph.nodes[v]['geom_utm']
            straightline = first.distance(last)
            if straightline != 0.0:
                if np.abs(straightline - data['length_utm_m']) < 1e-3:
                    count += 1

    percentage = count / graph.graph.size() * 100
    return percentage


def deadend_percentage(graph):
    """
    percentage of dead end nodes (num_ways = 1) of all nodes in graph
    :param graph: NetworkGraph
    :return: percentage
    """
    count = 0
    for n in graph.graph.nodes:
        if graph.graph.nodes[n]['num_ways'] == 1:
            count += 1

    percentage = count / graph.graph.order() * 100
    return percentage


def intersection_properties(graph):
    """
    percentage of 3- and 4-way intersections of all nodes (minus deadends)
    percentage of regular intersections of all 3- and 4-way intersections (see Fogliaroni et al. 2018)
    :param graph: NetworkGraph
    :return: 3-way, 4-way, 3+4-way intersection percentage, regular 3-way, 4-way, 3+4-way intersection percentage
    """
    count1way = 0
    count3way, count3reg = 0, 0
    count4way, count4reg = 0, 0
    for n in graph.graph.nodes:
        if graph.graph.nodes[n]['num_ways'] == 1:
            count1way += 1
        if graph.graph.nodes[n]['num_ways'] == 3:
            count3way += 1
            if graph.graph.nodes[n]['delta_t'] <= 18:
                count3reg += 1
        elif graph.graph.nodes[n]['num_ways'] == 4:
            count4way += 1
            if graph.graph.nodes[n]['delta'] <= 36:
                count4reg += 1

    percentage_3_way = (count3way) / (len(graph.nodes)-count1way) * 100
    percentage_4_way = (count4way) / (len(graph.nodes)-count1way) * 100
    percentage_3_4_way = (count3way + count4way) / (len(graph.nodes) - count1way) * 100

    percentage_regular_3_ways = count3reg / count3way * 100
    percentage_regular_4_ways = count4reg / count4way * 100
    percentage_regular_3_4_way = (count3reg + count4reg) / (count3way + count4way) * 100

    return percentage_3_way, percentage_4_way, percentage_3_4_way, \
           percentage_regular_3_ways, percentage_regular_4_ways, percentage_regular_3_4_way


def area_circularity(polygon):
    """
    deviation of area shape from perfect circle (see https://gis.stackexchange.com/a/10925)
    :param polygon: convex hull around graph nodes
    :return: area circularity
    """
    r = polygon.length/np.sqrt(polygon.area) / (2*np.sqrt(np.pi))
    return r


def orientation_order(graph):
    """
    (see Boeing, G. 2018)
    :param graph: NetworkGraph.graph (with edge attribute "bearing")
    :return: phi (orientation order)
    """
    g = copy.deepcopy(graph)
    g.graph.graph['crs'] = 4326
    for u, v, data in g.edges(data=True):
        data["length"] = data.pop("length_utm_m")
    H0 = ox.orientation_entropy(g.graph)
    Hmax = 3.584
    Hgrid = 1.386
    phi = 1 - ((H0 - Hgrid) / (Hmax - Hgrid)) ** 2
    return phi


def node_bearing_to_dest_attribute(graph, destination):
    """
    function to add node attribute "min_bearing_to_dest" to all nodes within graph
    :param graph: NetworkGraph
    :param destination: node id of route destination
    :return:
    """
    dest = graph.nodes[destination]['geom_utm']

    for n in graph.nodes:
        node = graph.nodes[n]['geom_utm']
        bearing_dest = (90 - np.rad2deg(np.arctan2(dest.y - node.y, dest.x - node.x))) % 360
        diffs = []
        for e in graph.edges(n):
            node_adj = graph.nodes[e[1]]['geom_utm']
            dist_straight = node.distance(node_adj)
            if dist_straight == 0.0:
                pass
            elif np.abs(dist_straight - graph.graph[n][e[1]][0]['length_utm_m']) < 1e-3:
                bearing_node_adj = (90 - np.rad2deg(np.arctan2(node_adj.y - node.y, node_adj.x - node.x))) % 360
                diffs.append(
                    min(np.abs(bearing_dest - bearing_node_adj), 360 - np.abs(bearing_dest - bearing_node_adj)))
            else:
                line_nodes = []
                try:
                    l_multiline = len(graph.graph[n][e[1]][0]['geom_utm'].geoms)
                    for l in graph.graph[n][e[1]][0]['geom_utm'].geoms:
                        line_nodes.extend(l.coords)
                except:
                    line_nodes.extend(graph.graph[n][e[1]][0]['geom_utm'].coords)

                dists, points = [], []
                for coords in line_nodes:
                    dist = node.distance(Point(coords))
                    if dist != 0:
                        dists.append(dist)
                        points.append(coords)
                closest_node = Point(points[np.argmin(dists)])
                bearing_node_adj = (90 - np.rad2deg(np.arctan2(closest_node.y - node.y, closest_node.x - node.x))) % 360
                diffs.append(
                    min(np.abs(bearing_dest - bearing_node_adj), 360 - np.abs(bearing_dest - bearing_node_adj)))

        graph.nodes[n]['min_bearing_to_dest'] = min(diffs) if len(diffs) != 0 else float('NaN')


def deadend_mean_length(graph):
    """
    function to compute mean segment length of all dead end segments
    :param graph: NetworkGraph
    :return: mean dead end segment length
    """
    deadend_count = 0
    deadend_total_l = 0
    for n in graph.nodes:
        if graph.nodes[n]['num_ways'] == 1:
            try:
                u, v = list(graph.edges([n]))[0][0], list(graph.edges([n]))[0][1]
                deadend_total_l += graph.graph[u][v][0]['length_utm_m']
                deadend_count += 1
            except:
                pass
    if deadend_count != 0:
        deadend_length = deadend_total_l / deadend_count
    else:
        deadend_length = float('NaN')
    return deadend_length

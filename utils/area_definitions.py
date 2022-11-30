from shapely.geometry import Point, LineString, MultiPoint

def area_min_max(g, sp, buffer):
    """
    :param g: NetworkGraph
    :param sp: shortest path, dict(id, x, y)
    :param buffer: additional buffer [m], int or float
    :return: nodes inside the area, dict(id, x, y)
    """
    xmin = min(sp['x'][:]) - buffer
    xmax = max(sp['x'][:]) + buffer
    ymin = min(sp['y'][:]) - buffer
    ymax = max(sp['y'][:]) + buffer

    nodes_inside = dict(id=[], x=[], y=[])
    for n in g.graph:
        pt = g.graph.nodes[n]['geom_utm']
        if xmin <= pt.x <= xmax and ymin <= pt.y <= ymax:
            nodes_inside['id'].append(n)
            nodes_inside['x'].append(pt.x)
            nodes_inside['y'].append(pt.y)
    return nodes_inside


def area_beeline(g, sp, buffer):
    """
    :param g: NetworkGraph
    :param sp: shortest path, dict(id, x, y)
    :param buffer: additional buffer [m], int or float
    :return: surrounding polygon, nodes inside the area, dict(id, x, y)
    """
    st = Point(sp['x'][0], sp['y'][0])
    ed = Point(sp['x'][-1], sp['y'][-1])
    beeline = LineString([st, ed])
    if buffer == 'l/2':
        buffer = beeline.length / 2
    elif buffer == 'l/4':
        buffer = beeline.length / 4
    elif buffer is type(int) or buffer is type(float):
        buffer = buffer
    else:
        print('Please specify a suitable buffer: int, float or string ("l/2", "l/3").')
    polygon = beeline.buffer(buffer)
    nodes_inside = g.get_nodes_in_polygon(polygon)
    return polygon, nodes_inside


def area_shortest_path(g, sp, buffer):
    """
    :param g: NetworkGraph
    :param sp: shortest path, dict(id, x, y)
    :param buffer: additional buffer [m], int or float
    :return: surrounding polygon, nodes inside the area, dict(id, x, y)
    """
    line = LineString([Point(sp['x'][i], sp['y'][i]) for i in range(len(sp['id']))])
    polygon = line.buffer(buffer)
    nodes_inside = g.get_nodes_in_polygon(polygon)
    return polygon, nodes_inside


def area_shortest_path_adj(g, sp, buffer):
    """
    :param g: NetworkGraph
    :param sp: shortest path, dict(id, x, y)
    :param buffer: additional buffer [m], int or float
    :return: surrounding polygon, nodes inside the area, dict(id, x, y)
    """
    sp_nodes_adj = []
    for sp_n in sp['id']:
        for first_n in g.graph.neighbors(sp_n):
            for second_n in g.graph.neighbors(first_n):
                for third_n in g.graph.neighbors(second_n):
                    for fourth_n in g.graph.neighbors(third_n):
                        sp_nodes_adj.append(fourth_n)

    nodeset = g.get_coords_nodelist(set(sp_nodes_adj))
    pointset = MultiPoint([(nodeset['x'][i], nodeset['y'][i])
                           for i in range(len(nodeset['x']))])
    ch = pointset.convex_hull
    polygon = ch.buffer(buffer)
    nodes_inside = g.get_nodes_in_polygon(polygon)
    return polygon, nodes_inside


def area_taken_nodes(g, data, buffer):
    """
    :param g: NetworkGraph
    :param data: filtered results (ID)
    :param buffer: additional buffer [m], int or float
    :return: surrounding polygon, nodes inside the area, dict(id, x, y), list with all routes
    """
    edges = data.path_taken_edges.apply(eval)
    all_taken = []
    nodelist = []
    for i in range(3000):
        nodes = g.get_nodes_of_route(edges[i])
        all_taken.extend(nodes['id'])
        nodelist.append(nodes['id'])

    nodeset = g.get_coords_nodelist(set(all_taken))
    pointset = MultiPoint([(nodeset['x'][i], nodeset['y'][i])
                           for i in range(len(nodeset['x']))])
    ch = pointset.convex_hull
    polygon = ch.buffer(buffer)
    nodes_inside = g.get_nodes_in_polygon(polygon)
    return polygon, nodes_inside, nodelist


def area_node_ratios(g, area, sp_length, ratio, buffer):
    """
    :param g: NetworkGraph
    :param area: DataFrame containing data of current route
    :param sp_length: shortest path length [m], float
    :param ratio: maximum value of nodelength / sp_length, [1.0 - 1.5]
    :param buffer: additional buffer [m], int or float
    :return: surrounding polygon, nodes inside the area, dict(id, x, y)
    """
    nodeset = area[(area.l / sp_length <= ratio) & (area.l / sp_length != 0.)]
    pointset = MultiPoint([(nodeset.x.iloc[i], nodeset.y.iloc[i])
                           for i in range(len(nodeset))])
    ch = pointset.convex_hull
    polygon = ch.buffer(buffer)
    nodes_inside = g.get_nodes_in_polygon(polygon)
    return polygon, nodes_inside

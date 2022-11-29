import numpy as np
from shapely.geometry import Point


def compute_bearing_attributes(g):
    """
    function to compute and add edge attribute "bearing" to existing graph
    :param g: NetworkGraph without edge attribute "bearing"
    :return: g: NetworkGraph with edge attribute "bearing"
    """

    # counters
    count_straight, count_non_straight = 0, 0
    count_loops, count_none = 0, 0

    # list of differences for node bearings (1/2 are first/last node of edge segment)
    diffs_1, diffs_2 = [], []

    # loop all edges in graph
    for u, v, data in g.edges(data=True):
        if u != v:
            first, last = g.graph.nodes[u]['geom_utm'], g.graph.nodes[v]['geom_utm']
            straight_line = first.distance(last)

            # junction is None
            if straight_line == 0.0:
                # bearing is set to NaN
                count_none += 1
                data['bearing'] = float('NaN')

            # straight street segment (difference < 1mm)
            elif np.abs(straight_line - data['length_utm_m']) < 1e-3:
                # bearing is compass heading (first to last node)
                bearing = (90 - np.rad2deg(np.arctan2(last.y - first.y, last.x - first.x))) % 360
                data['bearing'] = bearing
                count_straight += 1

            # curved street segment (difference >= 1mm)
            else:
                # bearing is compass heading (first to last node)
                bearing = (90 - np.rad2deg(np.arctan2(last.y - first.y, last.x - first.x))) % 360
                data['bearing'] = bearing
                count_non_straight += 1

                # check differences in simplified compass heading and more complex node bearing

                # get closest adjacent point, line-of-sight from first and last node respectively
                first_adj = closest_curve_point(g.graph, u, v, first)
                last_adj = closest_curve_point(g.graph, u, v, last)

                # compute node bearing (1/2 are first/last node of edge segment)
                bearing1 = (90 - np.rad2deg(np.arctan2(first_adj.y - first.y, first_adj.x - first.x))) % 360
                bearing2 = (90 - np.rad2deg(np.arctan2(last_adj.y - last.y, last_adj.x - last.x))) % 360

                # compute simplified straight
                bearing_simplified_1 = bearing
                bearing_simplified_2 = (bearing_simplified_1 + 180) % 360

                # compute differences (consider all cases)
                if bearing_simplified_1 > 270 and bearing1 < 90:
                    diff1 = ((360 - bearing_simplified_1) + bearing1)
                elif bearing1 > 270 and bearing_simplified_1 < 90:
                    diff1 = ((360 - bearing1) + bearing_simplified_1)
                else:
                    diff1 = (np.abs(bearing1 - bearing_simplified_1))
                if bearing_simplified_2 > 270 and bearing2 < 90:
                    diff2 = ((360 - bearing_simplified_2) + bearing2)
                elif bearing2 > 270 and bearing_simplified_2 < 90:
                    diff2 = ((360 - bearing2) + bearing_simplified_2)
                else:
                    diff2 = (np.abs(bearing2 - bearing_simplified_2))
                diffs_1.append(diff1)
                diffs_2.append(diff2)
        else:
            count_loops += 1

    nr_edges = len(g.edges)
    print('Number of edges: {:6d}'.format(nr_edges))
    print('Junction None:   {:6d}, {:5.2f}%'.format(count_none, count_none/nr_edges*100))
    print('Self-loops:      {:6d}, {:5.2f}%'.format(count_loops, count_loops/nr_edges*100))
    print('Straight:        {:6d}, {:5.2f}%'.format(count_straight, count_straight/nr_edges*100))
    print('Non-straight:    {:6d}, {:5.2f}%'.format(count_non_straight, count_non_straight/nr_edges*100))
    print('Median bearing difference (node bearing - simplified): {:.2f}°'.format(np.median(diffs_1 + diffs_2)))

    return g


def closest_curve_point(g, u, v, init_node):
    """
    function to find closest adjacent point within linestring to initial node
    :param g: NetworkGraph.graph
    :param u: node ID corresponding to first node of edge
    :param v: node ID corresponding to second node of edge
    :param init_node: geometry of initial node
    :return: geometry of point closest to initial node
    """

    # edge under consideration
    edge = g[u][v]

    # check if edge is multilinestring and handle accordingly
    try:
        len(edge[0]['geom_utm'].geoms)
        points = []
        # add all points within multilinestring to point list
        for line in edge[0]['geom_utm'].geoms:
            points += line.coords
    except:
        # add all points within linestring to point list
        points = list(edge[0]['geom_utm'].coords)

    distances, pointlist = [], []
    for point in points:
        # compute distance to initial node
        dist = init_node.distance(Point(point))
        if dist != 0:
            distances.append(dist)
            pointlist.append(point)

    # find point with minimum distance to init_node
    pt_min = Point(pointlist[np.argmin(distances)])
    return pt_min


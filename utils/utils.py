import networkx as nx
import pandas as pd
import numpy as np
from shapely.geometry import Point

class NetworkGraph():
    def __init__(self, path, graph=None, nodelist=None):
        if graph and nodelist is None:
            self.graph = graph
        elif graph and nodelist is not None:
            self.graph = graph.subgraph(nodelist).copy()
        else:
            self.graph = nx.read_gpickle(path)
        self.nodes = self.graph.nodes
        self.edges = self.graph.edges

    def get_node_attributes(self):
        pass

    def get_edge_attribute(self, attribute, edge=None, node1=None, node2=None):
        if edge is None:
            u = node1
            v = node2
            if self.graph.is_multigraph():
                shortest = []
                for e in range(len(self.graph[u][v])):
                    shortest.append(self.graph[u][v][e].get('length_utm_m'))
                i = np.where(shortest == np.min(shortest))[0][0]
                attr = self.graph[u][v][i].get(str(attribute))
            else:
                attr = self.graph[u][v].get(str(attribute))
        else:
            u = edge[0]
            v = edge[1]
            i = edge[2]
            attr = self.graph[u][v][i].get(str(attribute))

        return attr

    def get_nodes_of_route(self, edgelist):
        nodes, x, y = [], [], []
        for e in edgelist:
            n = [e[0]]

            if e == edgelist[-1]:
                n.append(e[1])

            nodes.extend(n)
            x.extend([self.graph.nodes[m]['geom_utm'].x for m in n])
            y.extend([self.graph.nodes[m]['geom_utm'].y for m in n])
        return dict(id=nodes, x=x, y=y)

    def get_edges_of_route(self, nodelist):
        edges = []
        for n in range(len(nodelist) - 1):
            u = nodelist[n]
            v = nodelist[n+1]
            if self.graph.is_multigraph():
                shortest = []
                for e in range(len(self.graph[u][v])):
                    shortest.append(self.graph[u][v][e].get('length_utm_m'))
                i = np.where(shortest == np.min(shortest))[0][0]
                edges.append(tuple([u, v, i]))
            else:
                edges.append(tuple([u, v]))
        return edges

    def get_coords_nodelist(self, nodelist):
        nodes, x, y = [], [], []
        for n in nodelist:
            nodes.append(n)
            x.append(self.graph.nodes[n]['geom_utm'].x)
            y.append(self.graph.nodes[n]['geom_utm'].y)
        return dict(id=nodes, x=x, y=y)

    def get_nodes_in_polygon(self, polygon):
        nodes_inside = dict(id=[], x=[], y=[])
        for n in self.graph:
            pt = self.nodes[n]['geom_utm']
            if polygon.contains(Point(pt.x, pt.y)):
                nodes_inside['id'].append(n)
                nodes_inside['x'].append(pt.x)
                nodes_inside['y'].append(pt.y)
        return nodes_inside

    def plot(self):
        # unfreeze graph  returns a MultiGraph, but without selfloops (JUST FOR PLOTTING)
        g_plot = nx.MultiGraph(self.graph)
        # removing selfloops only possible from unfrozen graph
        g_plot.remove_edges_from(nx.selfloop_edges(g_plot))
        return g_plot

    def keep_only_shortest_edge(self):
        # transforms graph from multigraph to graph, keep shortest edge (length_utm_m)
        g_single = nx.Graph()
        for u, v, data in self.graph.edges(data=True):
            shortest = []
            for e in range(len(self.graph[u][v])):
                shortest.append(self.graph[u][v][e].get('length_utm_m'))
            i = np.where(shortest == np.min(shortest))[0][0]
            g_single.add_edge(u, v, **self.graph[u][v][i])
        return g_single

class AgentData():
    def __init__(self, path, fields=None):
        if fields is None:
            fields = ['agent_id', 'route_id', 'path_taken_edges',
                      'shortest_path_length', 'path_taken_length', 'goal_reached']
        self.data = pd.read_csv(path, usecols=fields)
        self.data['taken_shortest'] = self.data['path_taken_length'] / self.data['shortest_path_length']
        conditions = [(self.data['goal_reached'] == 1) & (self.data['taken_shortest'] <= 1.50),
                      (self.data['goal_reached'] == 0), (self.data['taken_shortest'] > 1.50)]
        self.data['success'] = np.select(conditions, [True, False, False])

    def success_per_route(self, id=None):
        if id is not None:
            success = self.data[(self.data['success'] == 1) & (self.data['route_id'] == id)]\
                .groupby(self.data['route_id']).size().reset_index(name='count')
        else:
            success = self.data[self.data['success'] == 1]\
                .groupby(self.data['route_id']).size().reset_index(name='count')
        success['percentage'] = success['count'] / 3000 * 100
        return success

    def get_filtered_data(self, agent=None, route=None):
        if agent is None and route is None:
            return None
        if agent is None:
            return self.data[(self.data.route_id == route)].reset_index(drop=True)
        if route is None:
            return self.data[(self.data.agent_id == agent)].reset_index(drop=True)
        return self.data[(self.data.route_id == route) & (self.data.agent_id == agent)].reset_index(drop=True)
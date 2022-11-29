import os

from utils.utils import *
from utils.bearing import *


if __name__ == '__main__':
    '''
    - script to add edge attribute "bearing" to the edges of the graphs
    - for Vienna, Mexico City and Djibouti City, respectively
    '''

    #####################################################
    path_data = os.path.join(os.path.normpath(os.getcwd() + os.sep + os.pardir), '01_Data')

    cities = ['01_Vienna', '02_Mexico', '03_Djibouti']

    for city in cities:
        path_orig = os.path.join(path_data, '01_Original', city)
        path_graph = os.path.join(path_orig, [f for f in os.listdir(path_orig) if 'nx_graph' in f][0])

        # read graph as NetworkGraph
        graph = NetworkGraph(path_graph)

        # add additional edge bearing attributes to graph
        graph = compute_bearing_attributes(graph)

        # store graph with bearing attributes
        path_out = os.path.join(path_orig, '{:s}_nx_graph_with_ec_with_bearing.p'.format(city[3:].lower()))
        nx.write_gpickle(graph.graph, path_out)

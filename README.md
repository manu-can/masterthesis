
add_edge_bearing.py
- script to add edge attribute "bearing" to the edges of the graphs
- for Vienna, Mexico City and Djibouti City, respectively

preprocessing.py
- script for preprocessing
- can be used to clip a graph (set function to 'clipping', select size)
- can be used to compute local centalities (set function to 'centralities')
- used in the following order:
. clipping, boundingbox
. clipping, subgraphs
. centralities
. clipping, big
. clipping, medium
. clipping, small

taken_nodes.py
- script to compute and store node ratios of all taken nodes of Vienna's 6 simulation datasets 
- needed for data driven reduction of the node ratio threshold

taken_nodes_analysis.py
- script to analyse the taken node ratios of all taken nodes of Vienna's 6 simulation datasets 
- computation of the node ratio threshold

streetnetworkproperties.py
- script to extract street network properties
- used for 3 cities (Vienna, Mexico City, Djibouti City) and 3 area extents (big, medium, small)

regression.py
- script to compute regression models
- used for 3 cities (Vienna, Mexico City, Djibouti City) and combined dataset and 3 area extents (big, medium, small)


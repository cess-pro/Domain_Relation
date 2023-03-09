# from the graphs, output the drawing js of global graph.
# INPUT:
#   folder_analysis (global variable, folder for analysis)
#   folder_analysis/graph_set_global.bin (output of 2_build_dependency.py)
# OUTPUT:
#   folder_analysis/global_graph_(type).js
# Python 3

import sys
import os
import time
import networkx as nx
import matplotlib.pyplot as plt
import pickle

###### GLOBAL CONFIG ######
# folder_analysis = "top100k"
# os.chdir(folder_analysis)
output_filename = "global_graph/global_graph_"       # global_graph_(type).js
degree_limit = 2     # the entire graph is tooooo big. only draw nodes that have over this indegree.

# global graphs. Global_graph_set = {"general": G, "explicit", "critical", "essential"}
Global_graph_set = pickle.load(open("graph_set_global.bin", "rb"))

###### MAIN ######
for mode in ["general", "explicit", "critical", "essential"]:
    # result_dict = {"links": [{"source": "6099", "target": "6371", "value": 1}, ...],
    #                "nodes": [{"name": "example.com", "id": "6099", "value": 1}, ...]}
    result_dict = {}
    result_dict["nodes"] = []
    result_dict["links"] = []

    # domain_id_mapping[domain] = id
    domain_id_mapping = {}

    ### add node to result_dict.
    id = 0
    for node in Global_graph_set[mode].nodes():
        node_name = node
        # only add nodes that have many indegree.
        if Global_graph_set[mode].in_degree(node) > degree_limit or Global_graph_set[mode].out_degree(node) > degree_limit:
            node_dict = {}
            node_dict["name"] = node_name
            node_dict["id"] = str(id)
            node_dict["value"] = 1
            result_dict["nodes"].append(node_dict)
            domain_id_mapping[node_name] = node_dict["id"]
            id += 1

    ### add edge to result_dict.
    for edge in Global_graph_set[mode].edges():
        source = edge[0]
        target = edge[1]
        node_dict = {}
        try:
            node_dict["source"] = domain_id_mapping[source]
            node_dict["target"] = domain_id_mapping[target]
            node_dict["value"] = 1
            result_dict["links"].append(node_dict)
        except:
            continue

    outputf = open(output_filename + mode + ".js", "w")
    outputf.write("webkitDep=")
    outputf.write(str(result_dict).replace("\'", "\""))



















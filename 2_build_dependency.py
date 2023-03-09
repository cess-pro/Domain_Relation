# from the NS results, build and analyze the dependency graph of each domain.
# INPUT:
#   folder_analysis (global variable, folder for analysis)
# OUTPUT:
#   folder_analysis/Graph/ (optional, controlled by SAVE_GRAPH_AS_FILE)
#   folder_analysis/graph_set_per_domain.bin
#   folder_analysis/graph_set_global.bin
# Python 3

import sys
import os
import time
import networkx as nx
import matplotlib.pyplot as plt
import pickle

###### GLOBAL CONFIG ######
folder_analysis = "res"

DEBUG = True
domain_file = "topdomain10k.txt"
ns_file = "domain_ns_info.txt"
null_ns = "~NO~NS~"

SAVE_GRAPH_AS_FILE = True
graph_output_dir = "graph/"

# all graphs. Graph_set[domain] = {"G_general": {"graph": G, "extrasize": 5, "avgextradepth", "maxextradepth"},
#                                  "G_explicit", "G_critical", "G_essential"}
# saved as folder_analysis/graph_set.bin
Graph_set = {}
# global graphs. Global_graph_set = {"general": G, "explicit", "critical", "essential"}
Global_graph_set = {}
for mode in ["essential", "general", "explicit", "critical"]:
    Global_graph_set[mode] = nx.DiGraph()

###### INIT ######
# if DEBUG:
#     folder_analysis = "topdomain10k.txt"
# else:
#     folder_analysis = sys.argv[1]

# os.chdir(folder_analysis)

# read and store domain list from domain_file.
domain_list = []
inputf = open(domain_file)
for line in inputf:
    domain_list.append(line.strip().lower().split("\t")[0])
inputf.close()
print("[++] Domains in list:", len(domain_list))

# read and store (domain, ns) mappings from ns_file. domain_ns[domain] = {ns1, ns2, ...}
domain_ns = {}
inputf = open(ns_file)
for line in inputf:
    line = line.strip()
    try:
        domain, ns = line.split("\t")
    except:
        print(line)
        continue
    ns = ns.rstrip(".")
    # if this is some true ns and not dead end, add to dict.
    if ns != null_ns:
        if domain not in domain_ns:
            domain_ns[domain] = []
        if ns not in domain_ns[domain]:
            domain_ns[domain].append(ns)
print("[++] Zones in NS dict:", len(domain_ns))

###### FUNC ######
# DFS of the dependency graph of each domain. 1. from NS record; 2. from the direct parent domain.
# mode is one of the following: "general", "explicit", "critical", "essential"
# build global graphs WHILE building individual ones.
def build_graph(domain, G, mode):
    # 1. find the next node from NS records.
    try:
        for ns in domain_ns[domain]:
            ns_parent = ns[ns.find(".") + 1:]    # only take the parent of each NS.
            if mode == "general":
                # [General] add everything.
                # if ns is already in the graph (i.e., visited), then just add the edge.
                if ns_parent not in G.nodes:
                    G.add_node(ns_parent)
                    G.add_edge(domain, ns_parent)
                    # add the node and edge to GLOBAL graph.
                    if ns_parent not in Global_graph_set[mode].nodes:
                        Global_graph_set[mode].add_node(ns_parent)
                    if not Global_graph_set[mode].has_edge(domain, ns_parent):
                        Global_graph_set[mode].add_edge(domain, ns_parent)
                    build_graph(ns_parent, G, mode)
                else:
                    G.add_edge(domain, ns_parent)
                    # add the edge to GLOBAL graph.
                    if not Global_graph_set[mode].has_edge(domain, ns_parent):
                        Global_graph_set[mode].add_edge(domain, ns_parent)
            elif mode == "explicit" and not has_glue(domain, ns):
                # [Explicit] only add nodes without glue.
                if ns_parent not in G.nodes:
                    G.add_node(ns_parent)
                    G.add_edge(domain, ns_parent)
                    # add the node and edge to GLOBAL graph.
                    if ns_parent not in Global_graph_set[mode].nodes:
                        Global_graph_set[mode].add_node(ns_parent)
                    if not Global_graph_set[mode].has_edge(domain, ns_parent):
                        Global_graph_set[mode].add_edge(domain, ns_parent)
                    build_graph(ns_parent, G, mode)
                else:
                    G.add_edge(domain, ns_parent)
                    # add the edge to GLOBAL graph.
                    if not Global_graph_set[mode].has_edge(domain, ns_parent):
                        Global_graph_set[mode].add_edge(domain, ns_parent)
            elif mode == "critical":
                # [Critical] only add nodes if EVERY NS is without glue.
                glue_flag = False
                for ns in domain_ns[domain]:
                    if has_glue(domain, ns):
                        glue_flag = True
                        break
                if not glue_flag:
                    if ns_parent not in G.nodes:
                        G.add_node(ns_parent)
                        G.add_edge(domain, ns_parent)
                        # add the node and edge to GLOBAL graph.
                        if ns_parent not in Global_graph_set[mode].nodes:
                            Global_graph_set[mode].add_node(ns_parent)
                        if not Global_graph_set[mode].has_edge(domain, ns_parent):
                            Global_graph_set[mode].add_edge(domain, ns_parent)
                        build_graph(ns_parent, G, mode)
                    else:
                        G.add_edge(domain, ns_parent)
                        # add the edge to GLOBAL graph.
                        if not Global_graph_set[mode].has_edge(domain, ns_parent):
                            Global_graph_set[mode].add_edge(domain, ns_parent)
            # [Essential] do nothing.
    except Exception as e:
        print("[ns error]", domain, e)

    # 2. find the next node from the direct parent.
    # the parent node applies to all modes.
    if domain.find(".") >= 0:
        parent = domain[domain.find(".") + 1:]
    else:
        parent = "."
    if parent not in G.nodes:
        G.add_node(parent)
        G.add_edge(domain, parent)
        # add the node and edge to GLOBAL graph.
        if parent not in Global_graph_set[mode].nodes:
            Global_graph_set[mode].add_node(parent)
        if not Global_graph_set[mode].has_edge(domain, parent):
            Global_graph_set[mode].add_edge(domain, parent)
        # root does not need searching.
        if parent != ".":
            build_graph(parent, G, mode)
    else:
        G.add_edge(domain, parent)
        # add the edge to GLOBAL graph.
        if not Global_graph_set[mode].has_edge(domain, parent):
            Global_graph_set[mode].add_edge(domain, parent)


# record: dom1 NS dom2.
# determining if there is a glue of dom2 in the parent of dom1.
def has_glue(dom1, dom2):
    # dom1: example.com; dom2: ns2.example.net
    # get parent of dom2 and dom1.
    parent_of_dom2 = dom2[dom2.find(".") + 1:]  # example.net
    if dom1.find(".") < 0:
        # the parent of dom1 is root. return true because everything is under root.
        return True
    parent_of_dom1 = dom1[dom1.find(".") + 1:]  # com

    # if parent of dom2 is not under parent of dom1, then it is out-of-bailiwick (no glue).
    if not parent_of_dom2.endswith("." + parent_of_dom1):
        return False
    else:
        return True

###### MAIN ######
# begin query ns of these domains.
counter = 1
for domain in domain_list:
    # one graph for each domain.
    G_set = {}
    # build graph for essential first, as the metrics of all graphs depend on it.
    for mode in ["essential", "general", "explicit", "critical"]:
        # build graph first.
        G_set[mode] = {}
        G_set[mode]["graph"] = nx.DiGraph()
        G_set[mode]["graph"].add_node(domain)
        print("[+++++] domain no.", counter, domain, mode)
        build_graph(domain, G_set[mode]["graph"], mode)

        # show and save graphs.
        if SAVE_GRAPH_AS_FILE or domain == "tsinghua.edu.cn":
            nx.draw_spring(G_set[mode]["graph"], with_labels=True)
            plt.savefig(graph_output_dir + domain + "." + mode + ".png")
            plt.clf()

        # calc metrics.
        if mode != "essential":
            # Zn = V(G) - V(G_essential)
            Zn = G_set[mode]["graph"].nodes - G_set["essential"]["graph"].nodes
            # 1. ExtraSize(G) = |Zn|
            G_set[mode]["extrasize"] = len(Zn)

            # 2. AvgExtraDepth & MaxExtraDepth
            AvgExtraDepth = 0
            MaxExtraDepth = 0
            # the value does not make sense when Zn is empty.
            if len(Zn) == 0:
                G_set[mode]["avgextradepth"] = AvgExtraDepth
                G_set[mode]["maxextradepth"] = MaxExtraDepth
                continue
            for zi in Zn:
                # get the distance between domain and zi (i.e., each node in Zn).
                depth = nx.shortest_path_length(G_set[mode]["graph"], source=domain, target=zi)
                AvgExtraDepth += depth
                if depth > MaxExtraDepth:
                    MaxExtraDepth = depth
            AvgExtraDepth /= float(len(Zn))
            G_set[mode]["avgextradepth"] = AvgExtraDepth
            G_set[mode]["maxextradepth"] = MaxExtraDepth

    Graph_set[domain] = G_set

    counter += 1
    if DEBUG and counter > 200:
        break

pickle.dump(Graph_set, open("graph_set_per_domain.bin", "wb"))
pickle.dump(Global_graph_set, open("graph_set_global.bin", "wb"))
# nx.draw_spring(Global_graph_set["essential"], with_labels=True)
# n = 1


# merge the global graph after individual ones. it is TOO SLOW. pls build global graph WHILE building individual ones.
'''
print("\n")
# Global_graph_set = {"general": G, "explicit", "critical", "essential"}
Global_graph_set = {}
for mode in ["general", "explicit", "critical", "essential"]:
    Global_graph_set[mode] = nx.DiGraph()
    domain_counter = 1
    for domain in Graph_set:
        Global_graph_set[mode] = nx.compose(Global_graph_set[mode], Graph_set[domain][mode]["graph"])
        # nx.draw_spring(Global_graph_set[mode], with_labels=True)
        # plt.clf()
        domain_counter += 1
        if domain_counter % 100 == 0:
            print("[++++++] Global: building", mode, "domain no.", domain_counter)

pickle.dump(Global_graph_set, open("graph_set_global.bin", "wb"))
'''
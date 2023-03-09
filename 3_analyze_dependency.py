# from the graphs, output metrics of dependency analysis.
# INPUT:
#   folder_analysis (global variable, folder for analysis)
#   folder_analysis/graph_set_per_domain.bin (output of 2_build_dependency.py)
#   folder_analysis/graph_set_global.bin (output of 2_build_dependency.py)
#   folder_analysis/domain_list.txt (used to determine the ranking of top domains)
# OUTPUT:
#
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
domain_file = "topdomain10k.txt"

###### INIT ######
# all graphs. Graph_set[domain] = {"G_general": {"graph": G, "extrasize": 5, "avgextradepth", "maxextradepth"},
#                                  "G_explicit", "G_critical", "G_essential"}
# read from folder_analysis/graph_set.bin
Graph_set = pickle.load(open("graph_set_per_domain.bin", "rb"))
print("[+]", len(Graph_set), "domains in the Graph set.\n")
# global graphs. Global_graph_set = {"general": G, "explicit", "critical", "essential"}
Global_graph_set = pickle.load(open("graph_set_global.bin", "rb"))

###### MAIN ######
### Global graph analysis.
# 1. relative density = |E(Global_graph)| / |E(Global_essential)|
Global_essential_edge_count = Global_graph_set["essential"].number_of_edges()
print("[+] Count of edges in Global graph of essential:", Global_essential_edge_count)
for mode in ["general", "explicit", "critical"]:
    edge_count = Global_graph_set[mode].number_of_edges()
    RelativeDensity = edge_count / Global_essential_edge_count
    print("[+] RelativeDensity of", mode, "is", RelativeDensity)

# 2. the indegree of each node (the most depended domains).
# TODO: the distribution of global indegree.
top = 50    # print the top 20 domains.
print("\n[+] The indegree of top", top, "nodes (excluding TLDs):")
# first find the closure of G_critical.
G = nx.transitive_closure(Global_graph_set["critical"])
node_indegree = {}
for node in G.nodes():
    node_indegree[node] = G.in_degree(node)
# sort the nodes in G by their indegree.
temp = sorted(node_indegree.items(), key=lambda x: x[1], reverse=True)
counter = 0
for item in temp:
    if "." in item[0]:
        print("\t", item)
        counter += 1
    if counter > top:
        break

### Individual graph analysis.
# 1. distribution of ExtraSize, MaxExtraDepth, AvgExtraDepth.
has_zn = {}     # count of domains that has non-essential dependency (non-empty Zn); has_zn = {"general": count_of_domain, "explicit", "critical"}
avg_zn = {}     # the avg length of non-empty Zn; avg_zn = {"general", "explicit", "critical"}
max_extra_depth_under_4 = {}
for domain in Graph_set:
    for mode in ["general", "explicit", "critical"]:
        if mode not in has_zn:
            has_zn[mode] = 0
            avg_zn[mode] = 0
            max_extra_depth_under_4[mode] = 0
        if Graph_set[domain][mode]["extrasize"] > 0:
            has_zn[mode] += 1
            avg_zn[mode] += Graph_set[domain][mode]["extrasize"]
        if Graph_set[domain][mode]["maxextradepth"] < 4:
            max_extra_depth_under_4[mode] += 1
# calc average.
for mode in ["general", "explicit", "critical"]:
    avg_zn[mode] /= has_zn[mode]
print("\n[+] domains with non-essential dependency: ")
for mode in ["general", "explicit", "critical"]:
    print(mode, "count:", has_zn[mode], "pct:", has_zn[mode] / len(Graph_set), "avg:", avg_zn[mode])
print("\n[+] domains with max-extra-depth < 3: ")
for mode in ["general", "explicit", "critical"]:
    print(mode, "count:", max_extra_depth_under_4[mode], "pct:", max_extra_depth_under_4[mode] / len(Graph_set))

# 2. relationship between domain rank & |Zn|
# read domain rankings.
domain_list = []
inputf = open(domain_file)
for line in inputf:
    domain_list.append(line.split("\t")[0])
inputf.close()
# concentrate magnitude domains in one dot.
magnitude = 10000
# extract and draw |Zn| in order.
x = []
y_general = []
y_explicit = []
y_critical = []
for i in range(0, len(domain_list), magnitude):
    x.append(i)
    avg_g = 0
    avg_e = 0
    avg_c = 0
    for j in range(i, i + magnitude):
        avg_g += Graph_set[domain_list[j]]["general"]["extrasize"]
        avg_e += Graph_set[domain_list[j]]["explicit"]["extrasize"]
        avg_c += Graph_set[domain_list[j]]["critical"]["extrasize"]
    y_general.append(avg_g / float(magnitude))
    y_explicit.append(avg_e / float(magnitude))
    y_critical.append(avg_c / float(magnitude))
plt.plot(x, y_general, 'o-', color='g', label="G_general")
plt.plot(x, y_explicit, 'o-', color='b', label="G_explicit")
plt.plot(x, y_critical, 'o-', color='r', label="G_critical")
plt.xlabel("Domain ranking")
plt.ylabel("Avg # extra dependency")
plt.legend(loc = "best")
plt.show()

# 3. relationship between |Zn| and TLD.
# avg_zn[mode] = {com: (sum_value, domain_count), net: (sum_value, domain_count), ...}
avg_zn = {}
non_empty_zn = {}
for mode in ["general", "explicit", "critical"]:
    avg_zn[mode] = {}
    non_empty_zn[mode] = {}
    for domain in Graph_set:
        # split domains according to TLDs.
        tld = domain[domain.rfind(".") + 1:]
        if tld not in avg_zn[mode]:
            avg_zn[mode][tld] = [0, 0]      # [sum_value, domain_count]
            non_empty_zn[mode][tld] = [0, 0]
        avg_zn[mode][tld][0] += Graph_set[domain][mode]["extrasize"]
        avg_zn[mode][tld][1] += 1
        # check |Zn| of this domain.
        if Graph_set[domain][mode]["extrasize"] > 0:
            # Zn is non-empty.
            non_empty_zn[mode][tld][0] += 1
        non_empty_zn[mode][tld][1] += 1

# draw the results. first the avg |Zn| graph per TLD.
plt.clf()
x = []
y_general = []
y_explicit = []
y_critical = []
# tld_list = ["com", "net", "org", "ru", "de", "uk", "jp", "br", "info", "pl", "cn", "fr", "it", "nl", "au", "in", "es", "eu", "cz", "ca"]
tld_list = ["com", "net", "org", "xyz", "info", "top", "cc", "co", "io", "me", "cn", "tv", "ru", "de", "uk", "jp", "br", "pl", "fr", "eu"]

for tld in tld_list: # avg_zn["general"]:
    x.append(tld)
    y_general.append(avg_zn["general"][tld][0] / float(avg_zn["general"][tld][1]))
    y_explicit.append(avg_zn["explicit"][tld][0] / float(avg_zn["explicit"][tld][1]))
    y_critical.append(avg_zn["critical"][tld][0] / float(avg_zn["critical"][tld][1]))
plt.plot(x, y_general, 'o-', color='g', label="G_general")
plt.plot(x, y_explicit, 'o-', color='b', label="G_explicit")
plt.plot(x, y_critical, 'o-', color='r', label="G_critical")
plt.xlabel("TLD")
plt.ylabel("Avg # extra dependency")
plt.legend(loc = "best")
plt.show()

# draw the results. the ratio of domains with non-empty |Zn| graph per TLD.
plt.clf()
x = []
y_general = []
y_explicit = []
y_critical = []
tld_list = ["com", "net", "org", "xyz", "info", "top", "cc", "co", "io", "me", "cn", "tv", "ru", "de", "uk", "jp", "br", "pl", "fr", "eu"]
for tld in tld_list: # avg_zn["general"]:
    x.append(tld)
    y_general.append(non_empty_zn["general"][tld][0] / float(non_empty_zn["general"][tld][1]))
    y_explicit.append(non_empty_zn["explicit"][tld][0] / float(non_empty_zn["explicit"][tld][1]))
    y_critical.append(non_empty_zn["critical"][tld][0] / float(non_empty_zn["critical"][tld][1]))
plt.plot(x, y_general, 'o-', color='g', label="G_general")
plt.plot(x, y_explicit, 'o-', color='b', label="G_explicit")
plt.plot(x, y_critical, 'o-', color='r', label="G_critical")
plt.xlabel("TLD")
plt.ylabel("% Domains with non-empty extra dependencies")
plt.legend(loc = "best")
plt.show()

# find the NS and dependencies of Top sites. (iteratively)
# INPUT: sys.argv[1] (file of domains to be queried)
# OUTPUT: ./domain_ns_info.txt

import sys
from dns.resolver import *
import dns.rdatatype
import time
from tqdm import tqdm

###### GLOBAL CONFIG ######
DEBUG = True
output_file = "domain_ns_info.txt"
resolver_in_use = ["9.9.9.9"]

###### INIT ######
if DEBUG:
    domain_file = "topdomain10k.txt"
else:
    domain_file = sys.argv[1]

# store (domain, ns) mappings. domain_ns[domain] = {ns1, ns2, ...}
domain_ns = {}
# output file.
outputf = open(output_file, "w")

# use specified resolvers for this task.
new_resolver = Resolver()
new_resolver.nameservers = resolver_in_use


###### FUNC ######
# query, write and return the NS of a zone.
def query_ns(zone):
    # this zone has been logged. stop.
    if zone in domain_ns:
        # print(zone, "logged.")
        return []
    print("Deal with ", zone)
    try:
        ns = new_resolver.resolve(zone, rdtype=dns.rdatatype.RdataType.NS).rrset.items
        time.sleep(0.25)
        ns_str_list = []
        # log this zone and write to file.
        domain_ns[zone] = {}
        for item in ns:
            ns_str_list.append(str(item).rstrip("."))
            domain_ns[zone][str(item)] = 0
            outputf.write(zone + "\t" + str(item) + '\n')
        # print(zone, ns_str_list)
        return ns_str_list
    except Exception as e:
        # print(zone, e)
        domain_ns[zone] = {}
        outputf.write(zone + "\t" + "~NO~NS~" + '\n')
        return []

# query the ns of one domain, as well as all domains in the ns record, iteratively (DFS).
def iterate_query_ns(domain_list):
    domain_list_expanded = []
    # add all parent domains into the list.
    for domain in domain_list:
        domain_tmp = domain + "."
        while domain_tmp.find(".") >= 0:
            if domain_tmp not in domain_list_expanded:
                domain_list_expanded.append(domain_tmp.rstrip("."))
            domain_tmp = domain_tmp[domain_tmp.find(".") + 1:]

    # iteratively query.
    for domain in domain_list_expanded:
        ns_str_list = query_ns(domain)
        iterate_query_ns(ns_str_list)

###### MAIN ######
inputf = open(domain_file)
domain_list = []
# read the top domain list.
for line in inputf:
    line = line.strip()
    domain = line.split("\t")[0]
    domain_list.append(domain.lower())

# begin query ns of these domains.
counter = 0
for domain in tqdm(domain_list):
    print("\n\n[+++++++++++++++++++++++] now domain no.", counter, domain)
    iterate_query_ns([domain])
    counter += 1

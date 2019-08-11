from heapq import heappop, heappush
import networkx as nx

def dijsktra(G, source_node):
    routes = {}
    unvisited = [(0, source_node, source_node)]
    visited = set()

    while unvisited:
        (cost, dst, nh) = heappop(unvisited)
        if dst not in visited or cost == routes[dst][0][1]:
            visited.add(dst)
            if nh == source_node: 
                nh = dst

            if dst in routes:
                routes[dst].append((nh, cost))
            else:
                routes[dst] = [(nh, cost)]

            for n in G.neighbors(dst):
                heappush(unvisited, (cost+G[dst][n]['cost'], n, nh))

    return routes



def mk_topo(pods, bw):
    num_hosts         = (pods ** 3)/4
    num_agg_switches  = pods * pods
    num_core_switches = (pods * pods)/4

    hosts = [('h' + str(i), {'type':'host'})
             for i in range (1, num_hosts + 1)]

    core_switches = [('s' + str(i), {'type':'switch','id':i})
                       for i in range(1,num_core_switches + 1)]

    agg_switches = [('s' + str(i), {'type':'switch','id':i})
                    for i in range(num_core_switches + 1,num_core_switches + num_agg_switches+ 1)]

    g = nx.DiGraph()
    g.add_nodes_from(hosts)
    g.add_nodes_from(core_switches)
    g.add_nodes_from(agg_switches)

    host_offset = 0
    for pod in range(pods):
        core_offset = 0
        for sw in range(pods/2):
            switch = agg_switches[(pod*pods) + sw][0]
            # Connect to core switches
            for port in range(pods/2):
                core_switch = core_switches[core_offset][0]
                g.add_edge(switch,core_switch,
                           {'src_port':port,'dst_port':pod,'capacity':bw,'cost':1})
                g.add_edge(core_switch,switch,
                           {'src_port':pod,'dst_port':port,'capacity':bw,'cost':1})
                core_offset += 1

            # Connect to aggregate switches in same pod
            for port in range(pods/2,pods):
                lower_switch = agg_switches[(pod*pods) + port][0]
                g.add_edge(switch,lower_switch,
                           {'src_port':port,'dst_port':sw,'capacity':bw,'cost':1})
                g.add_edge(lower_switch,switch,
                           {'src_port':sw,'dst_port':port,'capacity':bw,'cost':1})

        for sw in range(pods/2,pods):
            switch = agg_switches[(pod*pods) + sw][0]
            # Connect to hosts
            for port in range(pods/2,pods): # First k/2 pods connect to upper layer
                host = hosts[host_offset][0]
                # All hosts connect on port 0
                g.add_edge(switch,host,
                           {'src_port':port,'dst_port':0,'capacity':bw,'cost':1})
                g.add_edge(host,switch,
                           {'src_port':0,'dst_port':port,'capacity':bw,'cost':1})
                host_offset += 1

    return g




if __name__ == "__main__":
    
    G = mk_topo(4,1)
    # edges = [
    #     ("A","B", {'cost':7}),
    #     ("A","D", {'cost':5}),
    #     ("B","C", {'cost':8}),
    #     ("B","D", {'cost':9}),
    #     #("B","E", {'cost':7}),
    #     ("C","E", {'cost':5}),
    #     ("D","E", {'cost':15}),
    #     ("D","F", {'cost':6}),
    #     ("E","F", {'cost':8}),
    #     ("E","G", {'cost':9}),
    #     ("F","G", {'cost':11})
    # ]

    # edges = [
    #       ("A", "C", {'cost': 1}),
    #       ("A", "G", {'cost': 1}),
    #       ("A", "E", {'cost': 1}),
    #       ("B", "D", {'cost': 1}),
    #       ("B", "H", {'cost': 1}),
    #       ("B", "F", {'cost': 1}),
    #       ("D", "C", {'cost': 1}),
    #       ("H", "G", {'cost': 1}),
    #       ("F", "E", {'cost': 1}),
    #       ("F", "C", {'cost': 1}),
    #       ("D", "G", {'cost': 1}),
    #       ("H", "E", {'cost': 1}),  
    # ]

    # G.add_edges_from(edges)
    # print edges

    for x in G:
        for y in G.neighbors(x):
            print x,y, G[x][y]['cost']

    print "DIJSKTRA---------"

    r = dijsktra(G, "h1")

    print r


























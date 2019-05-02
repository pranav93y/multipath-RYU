import networkx as nx
import copy


def dijskrtas(G, source_node):
    #initailize distances
    distance = {}
    nodes = G.nodes()
    for x in nodes:
        #distance to all other nodes is infinity
        distance[x] = {'node_name': x, 'distance': float("inf"), 'next_hop': None}

    #distance to source node is 0
    distance[source_node] = {'node_name': source_node,'distance': 0,'next_hop': source_node};

    visited_nodes = {}
    unvisited_nodes = copy.copy(distance)

    while(len(unvisited_nodes) > 0):
        min_dist = float('inf') 
        min_node = None 

        #get node with minimum distance
        for x in unvisited_nodes.values():
            if(x['distance'] == float('inf')):
                continue
            if x['distance'] <= min_dist:
                min_dist = x['distance']
                min_node = x['node_name']
                next_hop = x['next_hop']

        if (min_node not in visited_nodes):
            visited_nodes[min_node] = [next_hop]
            for x in G.neighbors(min_node):
                if(x in visited_nodes):
                    continue
                if(min_dist + G[min_node][x]['weight'] < unvisited_nodes[x]['distance']):
                    unvisited_nodes[x]['distance'] = min_dist + G[min_node][x]['weight']
                    unvisited_nodes[x]['node_name'] = x
                    unvisited_nodes[x]['next_hop'] = x if min_node == source_node else next_hop 

        distance[min_node] = unvisited_nodes[min_node]
        del unvisited_nodes[min_node]
    return distance
 





if __name__ == '__main__':

    G = nx.Graph()
    G.add_nodes_from([1,2,3,4,5,6])
    G.add_edges_from([(1,2,{'weight':3}),(1,3,{'weight':5}),(2,3,{'weight':1}),(2,4,{'weight':4}),(2,6,{'weight':5}),(3,4,{'weight':3}),(3,5,{'weight':7}),(4,5,{'weight':2}),(4,6,{'weight':8})])
    d = dijskrtas(G, 1)
    print(str(d))

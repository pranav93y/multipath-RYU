
"""
A simple minimal topology script for Mininet.

Based in part on examples in the [Introduction to Mininet] page on the Mininet's
project wiki.

[Introduction to Mininet]: https://github.com/mininet/mininet/wiki/Introduction-to-Mininet#apilevels

"""

from mininet.topo import Topo
from mininet.util import irange

class FatTreeTopo( Topo ):

    def build( self ):
        # Create hosts.
        k = 0
        i = 0
        n = 0
        hosts = []
        for i in range(1,17):
            h = self.addHost('h%s' % str(i))
            hosts.append(h)

        # Create root root switches
        k = 0
        i = 0
        n = 0
        root_switches = []
        for i in range(1,5):
            sw = self.addSwitch( 's%s' % str(i), dpid = str(i) )
            root_switches.append(sw)

        # Create aggregate switches
        agg_switches = []
        k = 0
        i = 0
        n = 0
        for k in range (0,4):
            for i in range(0,2):
                sw = self.addSwitch( 's%s' % str((n+i) + int('10', 16)), dpid = str((n+i) + 16) )
                agg_switches.append(sw)
            n += i+1

        # Create edge switches
        edge_switches = []
        k = 0
        i = 0
        n = 0
        for k in range (0,4):
            for i in range(0,2):
                sw = self.addSwitch( 's%s' % str((n+i) + int('20', 16)), dpid = str((n+i) + 32) )
                edge_switches.append(sw)
            n += i+1


        # Add links between root and aggregate
        k = 0
        i = 0
        n = 0
        for k in range(0,8):
            if k%2 == 0:
                self.addLink(agg_switches[k], root_switches[0])
                self.addLink(agg_switches[k], root_switches[1])
            else:
                self.addLink(agg_switches[k], root_switches[2])
                self.addLink(agg_switches[k], root_switches[3])

        # Add Links between agg and edge_switches
        k = 0
        i = 0
        n = 0
        for i in range(0,8):
            if i%2 == 0:
                self.addLink(edge_switches[i], agg_switches[i])
                self.addLink(edge_switches[i], agg_switches[i+1])
            else:
                self.addLink(edge_switches[i], agg_switches[i])
                self.addLink(edge_switches[i], agg_switches[i-1])

        # Add links between the edge switch and each host
        k = 0
        i = 0
        n = 0
        for i in range(0,8):
            for k in range(0,2):
                self.addLink(hosts[n], edge_switches[i])
                n +=1

# Allows the file to be imported using `mn --custom <filename> --topo minimal`
topos = {
    'ft': FatTreeTopo
}


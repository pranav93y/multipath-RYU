''' Testing out simple topologies'''

from mininet.topo import Topo
from mininet.util import irange

class simpleTopo( Topo ):
    def build( self ):
        #create switches
        switches = []
        for i in range(0,4):
            sw = self.addSwitch( 's%s' % str(i), dpid = str(i) )
            switches.append(sw)

        #create hosts
        hosts = []
        for k in range(0,4):
            h = self.addHost('h%s' % str(k))
            hosts.append(h)

        #add links
        self.addLink(hosts[0], switches[2])
        self.addLink(hosts[1], switches[2])

        self.addLink(hosts[2], switches[3])
        self.addLink(hosts[3], switches[3])

        self.addLink(switches[0], switches[2])
        self.addLink(switches[1], switches[2])

        self.addLink(switches[0], switches[3])
        self.addLink(switches[1], switches[3])

topos = {
    'sim': simpleTopo
}
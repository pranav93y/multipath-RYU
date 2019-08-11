from mininet.topo import Topo
 
class MinimalTopo( Topo ):
    "Minimal topology with a single switch and two hosts"
 
    def build( self ):
        # h1 = self.addHost( 'h1' )
        # h2 = self.addHost( 'h2' )

        # s1 = self.addSwitch( 's1' )
        # s2 = self.addSwitch( 's2' )
        # s3 = self.addSwitch( 's3' )

        # self.addLink( s1, h1 )
        # self.addLink( s2, h2 )

        # self.addLink( s3, s1 )
        # self.addLink( s3, s2 )


        # Create two hosts.
        h1 = self.addHost( 'h1' )
        h2 = self.addHost( 'h2' )
        h3 = self.addHost( 'h3' )
        h4 = self.addHost( 'h4' )
 
        # Create a switch
        s1 = self.addSwitch( 's1', dpid='1' )
        s2 = self.addSwitch( 's2', dpid='2' )
        s3 = self.addSwitch( 's3', dpid='3' )
        s4 = self.addSwitch( 's4', dpid='4' )
 
        # Add links between the switch and each host
        self.addLink( s3, h1 )
        self.addLink( s3, h2 )
        self.addLink( s4, h3 )
        self.addLink( s4, h4 )

        #Add links between switches
        self.addLink( s3, s1 )
        self.addLink( s3, s2 )

        self.addLink( s4, s1 )
        self.addLink( s4, s2 )
 
# Allows the file to be imported using `mn --custom <filename> --topo minimal`
topos = {
    'minimal': MinimalTopo
}
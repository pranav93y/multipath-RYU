# Copyright (C) 2011 Nippon Telegraph and Telephone Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
An OpenFlow 1.0 L2 learning switch implementation.
"""

from heapq import heappop, heappush

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.mac import haddr_to_bin
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.lib.packet import mpls
from ryu.topology.api import get_switch, get_link
from ryu.topology import event

import networkx as nx 


HIGH = 0x9000
MID = 0x8000
LOW = 0x7000

BCAST_ADDR = "ff:ff:ff:ff:ff:ff"
MASK = "01:00:00:00:00:00"

class SimpleSwitch(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch, self).__init__(*args, **kwargs)
        self.switch_to_port = {}
        self.label = 20
        self.switch_to_label = {}
        self.dst_to_label = {}
        self.host_to_switch = {}
        self.net = nx.DiGraph()

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # install table-miss flow entry
        #
        # We specify NO BUFFER to max_len of the output action due to
        # OVS bug. At this moment, if we specify a lesser number, e.g.,
        # 128, OVS will send Packet-In with invalid buffer_id and
        # truncated packet data. In that case, we cannot output packets
        # correctly.  The bug has been fixed in OVS v2.1.0.
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        priority = 0
        self.add_flow(datapath, match, actions, priority)

    def add_flow(self, datapath, match, actions, priority, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        if buffer_id == None:
            buffer_id = ofproto.OFP_NO_BUFFER

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]

        mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst, buffer_id=buffer_id)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)

        if eth.ethertype == ether_types.ETH_TYPE_LLDP or eth.ethertype == ether_types.ETH_TYPE_IPV6:
            # ignore lldp packet
            return
        dst = eth.dst
        src = eth.src

        dpid = datapath.id
        ethtype = eth.ethertype

        # self.dst_to_label.setdefault(dpid, {})
        # self.switch_to_port.setdefault(dpid, {})
        # in_port = msg.match['in_port']
        # ethtype = eth.ethertype

        # #self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)

        # root_port = None
        # # Learn source switch if host
        # if src not in self.host_to_switch:
        #     self.host_to_switch[src] = {'switch': dpid, 'port': in_port}

        #     # Add FTE when current src is dst
        #     match = parser.OFPMatch(eth_dst = src)
        #     actions = [parser.OFPActionOutput(in_port)]
        #     priority = HIGH
        #     self.add_flow(datapath, match, actions, priority, None)
        #     root_port = in_port

        # if self.host_to_switch[src]['switch'] != dpid: #and self.host_to_switch[src]['switch'] not in self.switch_to_port[dpid]:
        #     #Add FTE to account current src as dst 
        #     #root_port denotes the port on current dpid that leads 
        #     #to next hop along the shortest path to source switch connected to src. 
        #     path = nx.shortest_path(self.net, dpid, self.host_to_switch[src]['switch'])
        #     next_hop = path[path.index(dpid)+1]
        #     root_port = self.net[dpid][next_hop]['port']
        #     self.switch_to_port[dpid][self.host_to_switch[src]['switch']] = root_port

        # if root_port ==  None:
        #     self.logger.info("Root Port is None...\n Quitting...")
        #     return

        # #Add flow for unknown unicast, drop duplicate flooded packets
        # match = parser.OFPMatch(eth_src=src)
        # actions = []
        # priority = LOW
        # self.add_flow(datapath, match, actions, priority, None)

        # #Add flow to accept traffic through root port
        # match = parser.OFPMatch(eth_src=src, in_port = root_port)
        # actions = [parser.OFPActionOutput(ofproto.OFPP_FLOOD)]
        # priority = MID
        # self.add_flow(datapath, match, actions, priority, None)

        # #Add flow for broadcast/multicast
        # match = parser.OFPMatch(eth_src=src, eth_dst=(BCAST_ADDR, MASK), in_port=root_port)
        # actions = [parser.OFPActionOutput(ofproto.OFPP_FLOOD)]
        # priority = HIGH
        # self.add_flow(datapath, match, actions, priority, None)

        # if dst in self.host_to_switch:
        #     match = parser.OFPMatch(eth_dst = dst)
        #     if self.host_to_switch[dst]['switch'] in self.switch_to_port[dpid]:
        #         out_port = self.switch_to_port[dpid][self.host_to_switch[dst]['switch']]
        #     else:
        #         #Set root port
        #         path = nx.shortest_path(self.net, dpid, self.host_to_switch[dst]['switch'])
        #         next_hop = path[path.index(dpid)+1]
        #         root_port = self.net[dpid][next_hop]['port']
        #         self.switch_to_port[dpid][self.host_to_switch[dst]['switch']] = root_port
        #         out_port = root_port
        #     actions = [parser.OFPActionOutput(out_port)]
        #     priority = HIGH
        #     self.add_flow(datapath, match, actions, priority, msg.buffer_id)

        # data = None
        # if msg.buffer_id == ofproto.OFP_NO_BUFFER:
        #     data = msg.data

        # out = datapath.ofproto_parser.OFPPacketOut(
        #     datapath=datapath, buffer_id=msg.buffer_id, in_port=in_port,
        #     actions=actions, data=data)
        # datapath.send_msg(out)

        # If ARP
        if ethtype == 2054:
            self.arpHandler(msg)
        # If IPV4
        elif ethtype == 2048:
            self.ipv4Handler(msg)
        #If MPLS unicast
        elif ethtype == 34887:
            self.mplsHandler(msg)

    def arpHandler(self, msg):
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)

        in_port = msg.match['in_port']
        ethtype = eth.ethertype
        dst = eth.dst
        src = eth.src
        dpid = datapath.id

        self.logger.info("Launching ARP handler for dpid: %s, src: %s, dst: %s", datapath.id, src, dst)

        # out_port = ofproto.OFPP_FLOOD
        # actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]
        # if dst in self.mac_to_port[datapath.id]:
        #     out_port = self.mac_to_port[datapath.id][dst]
        #     priority = HIGH
        #     match = datapath.ofproto_parser.OFPMatch(in_port=in_port, eth_src=eth.src, eth_dst=dst)
        #     actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]
        #     self.add_flow(datapath, match, actions, priority, msg.buffer_id)

        self.switch_to_label.setdefault(dpid, {})
        self.switch_to_port.setdefault(dpid, {})
        

        root_port = None
        # Learn source switch if host
        if src not in self.host_to_switch:
            self.host_to_switch[src] = {'switch': dpid, 'port': in_port}

            # Add FTE when current src is dst
            match = parser.OFPMatch(eth_dst = src, eth_type=ethtype)
            actions = [parser.OFPActionOutput(in_port)]
            priority = HIGH
            #self.add_flow(datapath, match, actions, priority, None)
            root_port = in_port

        if self.host_to_switch[src]['switch'] != dpid: #and self.host_to_switch[src]['switch'] not in self.switch_to_port[dpid]:
            #Add FTE to account current src as dst 
            #root_port denotes the port on current dpid that leads 
            #to next hop along the shortest path to source switch connected to src. 
            # path = nx.shortest_path(self.net, dpid, self.host_to_switch[src]['switch'])
            # next_hop = path[path.index(dpid)+1]
            # root_port = self.net[dpid][next_hop]['port']
            # self.switch_to_port[dpid][self.host_to_switch[src]['switch']] = root_port
            root_port = self.switch_to_port[dpid][self.host_to_switch[src]['switch']]

        if root_port ==  None:
            self.logger.info("Root Port is None...\n Quitting...")
            # self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)
            return

        #Add flow for unknown unicast, drop duplicate flooded packets
        match = parser.OFPMatch(eth_src=src, eth_type=ethtype)
        actions = []
        priority = LOW
        self.add_flow(datapath, match, actions, priority, None)

        #Add flow to accept traffic through root port
        match = parser.OFPMatch(eth_src=src, in_port = root_port, eth_type=ethtype)
        actions = [parser.OFPActionOutput(ofproto.OFPP_FLOOD)]
        priority = MID
        self.add_flow(datapath, match, actions, priority, None)

        #Add flow for broadcast/multicast
        match = parser.OFPMatch(eth_src=src, eth_dst=(BCAST_ADDR, MASK), in_port=root_port, eth_type=ethtype)
        actions = [parser.OFPActionOutput(ofproto.OFPP_FLOOD)]
        priority = HIGH
        self.add_flow(datapath, match, actions, priority, None)

        if dst in self.host_to_switch:
            match = parser.OFPMatch(eth_dst = dst, eth_src = src, eth_type=ethtype)
            # if self.host_to_switch[dst]['switch'] in self.switch_to_port[dpid]:
            #     out_port = self.switch_to_port[dpid][self.host_to_switch[dst]['switch']]
            # else:
            #     #Set root port
            #     path = nx.shortest_path(self.net, dpid, self.host_to_switch[dst]['switch'])
            #     next_hop = path[path.index(dpid)+1]
            #     root_port = self.net[dpid][next_hop]['port']
            #     self.switch_to_port[dpid][self.host_to_switch[dst]['switch']] = root_port
            #     out_port = root_port
            if self.host_to_switch[dst]['switch'] == dpid:
                out_port = self.host_to_switch[dst]['port']
            else:
                out_port = self.switch_to_port[dpid][self.host_to_switch[dst]['switch']]
            actions = [parser.OFPActionOutput(out_port)]
            priority = HIGH
            self.add_flow(datapath, match, actions, priority, msg.buffer_id)

        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = datapath.ofproto_parser.OFPPacketOut(
            datapath=datapath, buffer_id=msg.buffer_id, in_port=in_port,
            actions=actions, data=data)
        datapath.send_msg(out)

    def ipv4Handler(self, msg):
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)

        dst = eth.dst
        in_port = msg.match['in_port']
        dpid = datapath.id
        self.logger.info("Launching IPV4 handler for datatpath%s", datapath.id)

        # If the packet is IPV4, it means that the datapath is a LER
        # IPV4 packets that come trough in_port with this destination
        match = parser.OFPMatch(eth_src = eth.src, in_port=in_port, eth_dst=dst, eth_type=eth.ethertype)

        # self.label = self.label + 1
        # self.switch_to_label[datapath.id][eth.dst] = self.label

        label = None
        if self.host_to_switch[dst]['switch'] == dpid:
            out_port = self.host_to_switch[dst]['port']
            actions = [parser.OFPActionOutput(out_port)]
        else:
            # out_port = self.switch_to_port[dpid][self.host_to_switch[dst]['switch']]
            # choose label
            
            paths_labels = self.switch_to_label[dpid][self.host_to_switch[dst]['switch']].keys()
            label = paths_labels[0]
            next_hop = self.switch_to_label[dpid][self.host_to_switch[dst]['switch']][label]['next_hop']
            out_port = self.net[dpid][next_hop]['port']
            # Set the action to be performed by the datapath
            actions = [parser.OFPActionPushMpls(ethertype=34887,type_=None, len_=None),
                parser.OFPActionSetField(mpls_label=label),
                parser.OFPActionOutput(out_port)]

        
        # self.logger.info("Flow match: in_port=%s, dst=%s, type=IP",in_port, dst)
        # self.logger.info("Flow actions: pushMPLS=%s, out_port=%s",label, out_port)

        priority = HIGH

        # Install a flow# verify if we have a valid buffer_id, if yes avoid to send both
        # flow_mod & packet_out
        self.add_flow(datapath, match, actions, priority, msg.buffer_id)

        data = None 
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)

    def mplsHandler(self, msg):
        datapath = msg.datapath
        ofproto = datapath.ofproto
        in_port = msg.match['in_port']
        dpid = datapath.id
        parser = datapath.ofproto_parser

        self.logger.info("Launching MPLS Handler for datatpath%s", dpid)

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)

        mpls_proto = pkt.get_protocol(mpls.mpls)
        dst = eth.dst
        ethtype = eth.ethertype

        # The switch can be a LSR or a LER, but the match is the same
        match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_type=ethtype,mpls_label=mpls_proto.label)

        # self.logger.info("Flow match: in_port=%s, dst=%s, type=IP, label=%s",in_port, dst, mpls_proto.label)

        # Set the out_port using the relation learnt with the ARP packet
        #out_port = self.switch_to_port[dpid][self.host_to_switch[dst]['switch']]
        # self.logger.info("Source Swith Dst: " + str(self.host_to_switch[dst]['switch']))
        # self.logger.info("dpid: " + str(dpid))

        if self.host_to_switch[dst]['switch'] != dpid:
            # out_port = self.switch_to_port[dpid][self.host_to_switch[dst]['switch']]
            #Choose label
            paths_labels = self.switch_to_label[dpid][self.host_to_switch[dst]['switch']].keys()
            label = paths_labels[0]
            next_hop = self.switch_to_label[dpid][self.host_to_switch[dst]['switch']][label]['next_hop']
            out_port = self.net[dpid][next_hop]['port']

            #The switch is LSR
            #Create New Label
            # self.label = self.label + 1
            actions = [parser.OFPActionPopMpls(),
                        parser.OFPActionPushMpls(),
                        parser.OFPActionSetField(mpls_label=label),
                        parser.OFPActionOutput(out_port)]
            # self.logger.info("Flow actions: switchMPLS=%s, out_port=%s",label, out_port)
        else:
            # self.logger.info("Edge Router>>>>>>>>")
            out_port = self.host_to_switch[dst]['port']
            #The switc is LER
            #Pop Label
            actions = [parser.OFPActionPopMpls(),
            parser.OFPActionOutput(out_port)]
            # self.logger.info("Flow actions: popMPLS, out_port=%s", out_port)
        priority = HIGH
        # Install a flow
        self.add_flow(datapath, match, actions, priority, msg.buffer_id)

        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)

    @set_ev_cls(ofp_event.EventOFPPortStatus, MAIN_DISPATCHER)
    def _port_status_handler(self, ev):
        msg = ev.msg
        reason = msg.reason
        port_no = msg.desc.port_no

        ofproto = msg.datapath.ofproto
        if reason == ofproto.OFPPR_ADD:
            self.logger.info("port added %s", port_no)
        elif reason == ofproto.OFPPR_DELETE:
            self.logger.info("port deleted %s", port_no)
        elif reason == ofproto.OFPPR_MODIFY:
            self.logger.info("port modified %s", port_no)
        else:
            self.logger.info("Illeagal port state %s %s", port_no, reason)

    @set_ev_cls(event.EventSwitchEnter)
    def handler_switch_enter(self, ev):
        self.net.clear()
        self.switch_to_label.clear()
        # The Function get_switch(self, None) outputs the list of switches.
        topo_raw_switches = get_switch(self, None)
        # The Function get_link(self, None) outputs the list of links.
        topo_raw_links = get_link(self, None)

        links = [(link.src.dpid, link.dst.dpid, {'port': link.src.port_no, 'cost': 1}) for link in topo_raw_links]
        switches = [i.dp.id for i in topo_raw_switches]

        self.logger.info("Switches: %d --------------------------", len(switches))
        self.logger.info(str(switches))
        self.logger.info("---------------------------------------")
        self.logger.info("Links: %d -----------------------------", len(links))
        self.logger.info(str(links))
        self.logger.info("---------------------------------------")

        self.net.add_nodes_from(switches)
        self.net.add_edges_from(links)

        self.set_root_ports(switches)
        self.logger.info("Root Ports: >>>>>>>>>>>>>>>>>>>>>>")
        self.logger.info(str(self.switch_to_port))

        del topo_raw_links
        del topo_raw_switches

        r = self.dijsktra(self.net, switches[0])
        self.logger.info("SW: %s =============================================>", str(switches[0]))
        self.logger.info(str(r))

        self.compute_labels(switches)
        

    def set_root_ports(self, switches):
        for sw in switches:
            self.switch_to_port.setdefault(sw, {})
            for i in switches:
                if i == sw:
                    continue
                #Set root port
                path = nx.shortest_path(self.net, sw, i)
                next_hop = path[path.index(sw)+1]
                root_port = self.net[sw][next_hop]['port']
                self.switch_to_port[sw][i] = root_port

    def compute_labels(self, switches):
        for src in switches:
            label = 21
            r = self.dijsktra(self.net, src)
            self.switch_to_label.setdefault(src, {})
            for dst in r.keys():
                if dst == src:
                    continue
                self.switch_to_label[src].setdefault(dst, {})
                for path in r[dst]:
                    self.switch_to_label[src][dst][label] = {'next_hop': path[0], 'cost': path[1]}
                    label += 1
        self.logger.info("LABELS COMPUTED &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
        self.logger.info(str(self.switch_to_label))
        self.logger.info("LABELS COMPUTED &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")

    def dijsktra(self, G, source_node):
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



    



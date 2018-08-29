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

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.lib import mac
from ryu.lib.mac import haddr_to_bin
from ryu.controller import mac_to_port

import networkx as nx

from ryu.topology import event, switches
from ryu.topology.api import get_switch, get_link
from ryu.app.wsgi import ControllerBase

#import matplotlib.pyplot as plt

class SimpleSwitch13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch13, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.net = nx.DiGraph()
        self.count = 0

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
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)

    def is_broadcast_mac(mac):
        if mac == "ff:ff:ff:ff:ff:ff":
            return True 
        else:
            return False

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        # If you hit this you might want to increase
        # the "miss_send_length" of your switch
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                              ev.msg.msg_len, ev.msg.total_len)
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        if eth.ethertype == ether_types.ETH_TYPE_LLDP or eth.ethertype == ether_types.ETH_TYPE_IPV6:
            # ignore lldp packet
            return
        dst = eth.dst
        src = eth.src

        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})

        self.logger.info(">>>>>>> packet in %s %s %s %s", dpid, src, dst, in_port)


        # # learn a mac address to avoid FLOOD next time.
        # self.mac_to_port[dpid][src] = in_port

        # Check to see if src is already in mac_to_port
        # If not, add src to mac_to_port
        if src not in self.mac_to_port[dpid]:
            self.mac_to_port[dpid][src] = in_port

            self.logger.info("src NOT-in mac to port====================================")
            self.logger.info(self.mac_to_port)
        else:
            # This means that there is already a src entry in mac_to_port
            # If in_port of packet is something different from the first (original)
            # in_port, we can conclude that this packet was flooded, and can be dropped

            self.logger.info("src IN mac to port========================================")
            self.logger.info(self.mac_to_port)
            if self.mac_to_port[dpid][src] != in_port and str(dst) == "ff:ff:ff:ff:ff:ff":
                # add flow to drop packet on this in_port
                prio = 2
                actions = []
                match = parser.OFPMatch(eth_src=src,in_port = in_port)
                inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,actions)]
                if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                    mod = parser.OFPFlowMod(datapath=datapath, buffer_id=msg.buffer_id,
                                            priority=prio, match=match,
                                            instructions=inst)

                else:
                    mod = parser.OFPFlowMod(datapath=datapath, priority=prio,
                                            match=match, instructions=inst)

                datapath.send_msg(mod)
                self.logger.info("IN PORT WRONG: %s, DROPPING PKT", in_port)
                return


        if src not in self.net:
            self.net.add_node(src)
            self.net.add_edge(dpid, src, {'port':in_port})
            self.net.add_edge(src, dpid)


        if dst in self.net:
            path = nx.shortest_path(self.net, src, dst)
            next = path[path.index(dpid)+1]
            out_port = self.net[dpid][next]['port']
            self.logger.info("dst found, outputing pkt to port %s", out_port)
            self.logger.info("path is : %s", str(path))
        else:
            out_port = ofproto.OFPP_FLOOD

        # if dst in self.mac_to_port[dpid]:
        #     out_port = self.mac_to_rt[dpopid][dst]
        #     self.logger.info("dst found, outputing pkt to port %s", out_port)
        # else:
        #     out_port = ofproto.OFPP_FLOOD
        #     self.logger.info("dst NOT found, flooding...")

        actions = [parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src)
            # verify if we have a valid buffer_id, if yes avoid to send both
            # flow_mod & packet_out
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 1, match, actions, msg.buffer_id)
                #return
            else:
                self.add_flow(datapath, 1, match, actions)
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)


    @set_ev_cls(event.EventSwitchEnter)
    def get_topology_data(self, ev):
        switch_list = get_switch(self, None)
        switches = [i.dp.id for i in switch_list]
        # print "Switches:---------------------"
        # print switches
        # print "------------------------------"
        link_list = get_link(self, None)
        links = [(link.src.dpid, link.dst.dpid, {'port':link.src.port_no}) for link in link_list]
        print "Links:--------------------------------------------------------"
        print links
        print "size: ", str(len(links))
        print "-----------------------------------------------------------------"
        self.net.add_nodes_from(switches)
        self.net.add_edges_from(links)
        if len(switches) >= 20:
            #nx.draw(self.net)
            #plt.savefig("path.png")
            print "++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
            return

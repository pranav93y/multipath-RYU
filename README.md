# Source Based Flood
#### This is step 1. The idea is to simply flood all traffic over source based trees. The root port is established in every switch for each host as the port in which traffic is first seen from that host. Any traffic that is not through a root port for a given host is dropped. This is a simple extention to the ```simple_switch_13.py``` Ryu controller example [here](https://github.com/osrg/ryu/blob/master/ryu/app/simple_switch_13.py).

# Usage

#### This project uses [Mininet](http://mininet.org/) to simmulate SDN topologies. 

- Note : The Controller application and the Mininet CLI must be running on separate terminals.

#### Controller

- The controller can be started by simply executing the `run-controller.sh` bash script: 
```
     bash run-controller.sh 
```
- By default, the controller will run `controller.py` located within the `controllers` directory. 

- The `run-controller.sh` script will accept three flags:
	- `-f` or `--file` to specify a path to a custom controller file. 
	- `-o` to **disable** the `--observe-links` flag to Ryu.
	- `-r` to **disable** the Ryu REST API.  


#### Mininet Topology

- The Mininet Topology can be built by running the `build-topo.sh` bash script. 
- By default, this script will build a Fat Tree topology with `k = 4`. The python script for building this topology the `topologies/mn_ft.py` file. 

- The `build-topo.sh` script will accept these flags as parameters:
	- `-f` or `--file` to specify the path to a custom topology.
	- `-t` or `--topo` to spcify the corresponding mininet topology.





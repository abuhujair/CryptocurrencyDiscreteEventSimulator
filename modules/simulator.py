import random
import numpy as np
import heapq
import copy
import graphviz as graph
import networkx as nx
import matplotlib.pyplot as plt
import os

import settings
from utils.logger import get_logger
from modules.network import Node
from modules.event_handler import Event, EventHandler
from modules.blockchain import Block, Transaction


class Simulator:
    """Discrete event simulator for etherum blockchain. 
    """
    def __init__(self, num_nodes:int , slow_nodes:float, low_hash:float, inter_arrival_time:float,
                    inter_arrival_time_block:float , simulation_time:float, MAX_BLOCK_LENGTH: int, 
                    attack_type:int=0, adv_hash:float=0.0, adv_connected:float=0.0):
        """Initialize node, network and simulator parameters

        Args:
            num_nodes (int): Number of nodes in the network
            slow_nodes (float): Percentage of slow nodes
            low_hash (float): Percentage of low hashing power nodes
            inter_arrival_time (float): Inter-arrival time between transactions
            inter_arrival_time_block (float): Inter-arrival time between blocks
            simulation_time (float): Simulation time 
            MAX_BLOCK_LENGTH (int): Max number of transactions in a block
            attack_type (int): Default 0. 1 for Selfish Mining, 2 for Stubborn Mining
            adv_hash (float): Default 0. Hashing power of attacker.
            adv_connected (float): Default 0, Percentage of node adversary is connected to.
        """
        self.num_nodes = num_nodes
        self.num_slow_nodes = int(num_nodes*slow_nodes)
        self.num_low_hash = int(num_nodes*low_hash)
        self.iat = inter_arrival_time
        self.iat_block = inter_arrival_time_block
        self.simulation_time = simulation_time
        self.MAX_BLOCK_LENGTH = MAX_BLOCK_LENGTH
        self.attack_type = attack_type
        self.adv_hash = adv_hash
        self.adv_connected = adv_connected

        self.logger = get_logger("EVENT")

        self.gen_exp = np.random.default_rng()  # Exponential distribution generator
        self.save_parameters()
 
        # Create peer network
        self.nodes = self.create_nodes()    # Dictionary [id: Node]
        self.create_network()   # Create edges between peers

        self.networkVisualizer()    # Visulaize the peer network
        
        self.event_queue = list()   # Priority queue of event queue [Event]
        self.event_handler = EventHandler(self.event_queue, self.nodes, self.iat, self.iat_block, self.logger)
    
        # Initialize first transaction events
        for node in self.nodes.values():
            new_event = Event(
                event_time = round(self.gen_exp.exponential(self.iat),4),
                event_type = 1, # Create transaction
                event_node = node
            )
            self.event_handler.add_event(new_event)

        # Initialize first mining events
        for node in self.nodes.values():
            new_event = Event(
                event_time = round(self.gen_exp.exponential(self.iat_block)/2,4),
                event_type = 3, # Create transaction
                event_node = node
            )
            self.event_handler.add_event(new_event)

        # Run the simulation
        self.run_simulation(simulation_time=self.simulation_time)

        # Save the results
        for node in list(self.nodes.values()):
            with open(f"{settings.NODES_DIR}/{node.id}_blockchain.txt", "w") as file:
                file.write(str(node.blockchain))

        # Save blockchain visualizations
        self.blockchainVisualizer()

    # ==========================================================================================
    # Peer network
    def create_nodes(self):
        """Create all peer nodes in the blockchain

        Returns:
            dict: Dictionary [id: Node] of all the newly generated nodes
        """
        transactions = list()
        account_balance = dict()

        # Generate genesis block transactions
        for i in range(self.num_nodes):
            coins = random.uniform(50, 500)
            new_transaction = Transaction(
                payer=-1,
                payee=i,
                value=coins,
                timestamp=0,
            )
            transactions.append(new_transaction)
            account_balance[i] = coins

        # Genereate the genesis block
        genesis_block = Block(
            parent_block_id=None,
            block_position=0,
            timestamp=0,
            transactions=transactions,
            block_creator=-1,
            account_balance=account_balance
        )

        nodes = {}
        hash_power = (1 - self.adv_hash)/(10*(self.num_nodes-1) - 9*self.num_low_hash)

        self.slow_nodes = random.sample(range(1 if self.attack_type!=0 else 0 , self.num_nodes), self.num_slow_nodes)     # Slow nodes
        self.low_hash_p = random.sample(range(1 if self.attack_type!=0 else 0 , self.num_nodes), self.num_low_hash)   # Low hashing power nodes
        if self.attack_type!=0:
            nodes[0] = Node(node_id=0,
                            node_type=1,
                            genesis_block=copy.deepcopy(genesis_block),
                            hash=self.adv_hash,
                            MAX_BLOCK_LENGTH=self.MAX_BLOCK_LENGTH,
                            node_label=self.attack_type
                            )
            nodes[0].num_peers = int(self.adv_connected*self.num_nodes)

        for i in range(1 if self.attack_type!=0 else 0, self.num_nodes):
            if (i in self.slow_nodes) and (i in self.low_hash_p):
                nodes[i] = Node(node_id=i,
                                node_type=0,
                                genesis_block=copy.deepcopy(genesis_block),
                                hash=hash_power,
                                MAX_BLOCK_LENGTH=self.MAX_BLOCK_LENGTH,
                                )
            
            elif i in self.slow_nodes:
                nodes[i] = Node(node_id=i,
                                node_type=0,
                                genesis_block=copy.deepcopy(genesis_block),
                                hash=hash_power*10,
                                MAX_BLOCK_LENGTH=self.MAX_BLOCK_LENGTH,
                                )

            elif i in self.low_hash_p:
                nodes[i] = Node(node_id=i,
                                node_type=1,
                                genesis_block=copy.deepcopy(genesis_block),
                                hash=hash_power,
                                MAX_BLOCK_LENGTH=self.MAX_BLOCK_LENGTH,
                                )
            
            else:
                nodes[i] = Node(node_id=i,
                                node_type=1,
                                genesis_block=copy.deepcopy(genesis_block),
                                hash=hash_power*10,
                                MAX_BLOCK_LENGTH=self.MAX_BLOCK_LENGTH,
                                )
        self.logger.info("Peer nodes created successfully")
        return nodes

    def create_network(self):
        """Create interconnections between peer nodes in the network. 
        """            
        while True:                        
            for node in self.nodes.values():
                for rand_peer in random.sample(list(self.nodes.values()), self.num_nodes):
                    if len(node.peers) == node.num_peers:   # Max peers attached
                        break
                    if node != rand_peer and (rand_peer.id not in node.peers) and len(node.peers)<node.num_peers and len(rand_peer.peers)<rand_peer.num_peers:
                        propagation_delay = round(random.uniform(0.01, 0.5), 4)
                        node.add_peer(rand_peer.id, propagation_delay)
                        rand_peer.add_peer(node.id, propagation_delay)
            
            if self.check_connectivity():   # If entire network is formed with specified properties
                break
            
            for node in self.nodes.values():    # Reset the network
                node.delete_peers()

        self.logger.info("Connected P2P Network Created.")

    def check_connectivity(self):
        """Check if the peer network is formed with the specified properties

        Returns:
            bool: True if valid, else False
        """
        root_node = self.nodes[0]
        visited = [root_node.id]
        planned = [peer_id for peer_id in root_node.peers]

        while len(planned):
            node_id = planned.pop()
            if node_id in visited:
                continue

            visited.append(node_id)
            for peer in self.nodes[node_id].peers:
                if peer not in visited:
                    planned.append(peer)

        if self.num_nodes == len(visited):
            return True

        self.logger.info("The Network is not connected. Retrying ...")
        return False
    
    # ==========================================================================================
    # Report and Visualization Functions
    def networkVisualizer(self):
        """Generate graph for peer nodes network of the simulator. 
        Different colors represent different types of nodes and edges.
        """
        network_graph_nodes = []
        network_graph_edges = []
        colormap_nodes = []
        colormap_edges = []
        for node in list(self.nodes.values()):
            network_graph_nodes.append(node.id)
            for i in node.peers:
                network_graph_edges.append((i, node.id))
                if node.id in self.slow_nodes or i in self.slow_nodes:
                    colormap_edges.append('#7F7F7F')                    #Slow conection
                else:
                    colormap_edges.append('#7F0000')                    #Fast Connection 
        
        G = nx.DiGraph()
        G.add_nodes_from(network_graph_nodes)
        G.add_edges_from(network_graph_edges)

        if self.attack_type!= 0:
            colormap_nodes.append("#FF0000")                            #Attacker Node
        for i in range(0 if self.attack_type == 0 else 1, self.num_nodes):
            if(i in self.low_hash_p):
                colormap_nodes.append('#0000FF')
            else:
                colormap_nodes.append('#00FF00')

        pos = nx.spring_layout(G)
        nx.draw(G, pos, node_color=colormap_nodes, edge_color=colormap_edges, with_labels=True)
        if self.attack_type!=0:
            plt.legend(["NODES: Blue:- Low Hash Power, Green:- High Hash Power, & Red:- Attacker", "EDGE: Red:- Fast connection & Gray:- Slow Connection"], loc='best')
        else:
            plt.legend(["NODES: Blue:- Low Hash Power & Green:- High Hash Power", "EDGE: Red:- Fast connection & Gray:- Slow Connection"], loc='best')
        plt.savefig(f"{settings.REPORT_DIR}/peer_network.png")
        self.logger.info("Peer network visualization saved")

    def blockchainVisualizer(self):
        """Visualize the final generated blockchain
        """
        blockchain_graph_nodes = []
        blockchain_graph_edges = []

        blocks = {}
        blocks['Curr'] = 'Longest\nChain'
            
        block_count = 0
        for node in self.nodes.values(): 
            for block in list(node.blockchain.blocks.values()):
                blockchain_graph_nodes.append(block.id)
                if block.id not in blocks:
                    blocks[block.id] = 'ID- '+str(block_count)+',\nN- '+str(block.coinbase_transaction.payee)+',\nTS- '+str(block.timestamp)
                    block_count+=1
                if block.parent_block_id == None:    # Genesis block
                    continue
                blockchain_graph_edges.append((block.id, block.parent_block_id))

            blockchain_graph_nodes.sort()
            
            blockchain_graph_nodes.append('Curr')
            blockchain_graph_edges.append(('Curr',node.blockchain.current_block.id))

            G = graph.Digraph(f"{node.id}")
            G.attr(rankdir='LR',splines='line')
            
            for block in blockchain_graph_nodes:
                G.node(str(blocks[block]))
            
            for edge in blockchain_graph_edges:
                G.edge(str(blocks[list(edge)[0]]),str(blocks[list(edge)[1]]))   
            
            G.render(f"{settings.NODES_DIR}/{node.id}_blockchain")  # Save blockchain images
            G.clear()
            os.remove(f"{settings.NODES_DIR}/{node.id}_blockchain") # Remove metadata
            blockchain_graph_edges.clear()
            blockchain_graph_nodes.clear()

    def save_parameters(self):
        output = ""
        output += 'num_nodes = '+str(self.num_nodes)+',\n'
        output += 'Slow_nodes = '+str(self.num_slow_nodes)+',\n'
        output += 'low_hash = '+str(self.num_low_hash)+',\n'
        output += 'inter_arrival_time = '+str(self.iat)+',\n'
        output += 'inter_arrival_time_block = '+str(self.iat_block)+',\n'
        output += 'simulation_time = '+str(self.simulation_time)+',\n'
        output += 'MAX_BLOCK_LENGTH = '+str(self.MAX_BLOCK_LENGTH)+',\n'
        output += 'attack_type = '+str(self.attack_type)+',\n'
        output += 'adv_hash = '+str(self.adv_hash)+',\n'
        output += 'adv_connected = '+str(self.adv_connected)+',\n'
        with open(f"{settings.REPORT_DIR}/input_parameters.txt", "w") as file:
            file.write(output)        


    # ==========================================================================================
    # Simulator functions

    def run_simulation(self, simulation_time:float):
        """Run simulation of ethereum

        Args:
            simulation_time (float): Simulation time
        """
        print("Simulation started.")
        current_time = 0
        period = int(simulation_time/20) if simulation_time>20 else 1
        for period in range(period, int(simulation_time)+1, period):                
            while current_time < period and self.event_queue != []:
                event = heapq.heappop(self.event_queue)
                current_time = event.time
                self.event_handler.handle_event(event)
            print("Simulation completed for: "+str(current_time)+"s")
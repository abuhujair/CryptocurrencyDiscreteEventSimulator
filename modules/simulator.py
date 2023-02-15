import random
import numpy as np
import heapq
from typing import List
import copy
import graphviz as graph
import networkx as nx
import matplotlib.pyplot as plt

from modules.network import Node
from modules.event_handler import Event, EventHandler
from modules.blockchain import Block, Transaction


class Simulator:
    """Simulator instance
    """
    def __init__(self, num_nodes:int , slow_nodes:float, low_hash:float, inter_arrival_time:float,
                    inter_arrival_time_block:float , simulation_time:float, MAX_BLOCK_LENGTH: int):
        self.num_nodes = num_nodes
        self.num_slow_nodes = int(num_nodes*slow_nodes)
        self.num_low_hash = int(num_nodes*low_hash)
        self.iat = inter_arrival_time
        self.iat_block = inter_arrival_time_block
        self.MAX_BLOCK_LENGTH = MAX_BLOCK_LENGTH

        self.gen_exp = np.random.default_rng()  # Exponential distribution generator
        # Create peer network
        self.nodes = self.create_nodes()    # Dictionary [id: Node]
        self.create_network()
        
        self.event_queue = list()
        self.event_handler = EventHandler(self.event_queue, self.nodes, self.iat, self.iat_block)
    
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

        self.run_simulation(simulation_time=simulation_time)

        for node in list(self.nodes.values()):
            print(node.blockchain)

    # ==========================================================================================
    # Peer network
    def create_nodes(self):
        """Create all nodes in the blockchain

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

        genesis_block = Block(
            parent_block_id=None,
            block_position=0,
            timestamp=0,
            transactions=transactions,
            block_creator=-1,
            account_balance=account_balance
        )

        nodes = {}

        hash_power = 1/(10*self.num_nodes - 9*self.num_low_hash)

        self.slow_nodes = random.sample(range(self.num_nodes), self.num_slow_nodes)
        self.low_hash_p = random.sample(range(self.num_nodes), self.num_low_hash)

        for i in range(self.num_nodes):
            if (i in self.slow_nodes) and (i in self.low_hash_p):
                nodes[i] = Node(node_id=i,
                                node_type=0,
                                genesis_block=copy.deepcopy(genesis_block),
                                hash=hash_power,
                                MAX_BLOCK_LENGTH=self.MAX_BLOCK_LENGTH)
            
            elif i in self.slow_nodes:
                nodes[i] = Node(node_id=i,
                                node_type=0,
                                genesis_block=copy.deepcopy(genesis_block),
                                hash=hash_power*10,
                                MAX_BLOCK_LENGTH=self.MAX_BLOCK_LENGTH)

            elif i in self.low_hash_p:
                nodes[i] = Node(node_id=i,
                                node_type=1,
                                genesis_block=copy.deepcopy(genesis_block),
                                hash=hash_power,
                                MAX_BLOCK_LENGTH=self.MAX_BLOCK_LENGTH)
            
            else:
                nodes[i] = Node(node_id=i,
                                node_type=1,
                                genesis_block=copy.deepcopy(genesis_block),
                                hash=hash_power*10,
                                MAX_BLOCK_LENGTH=self.MAX_BLOCK_LENGTH)

        return nodes

    def create_network(self):
        """Create interconnections between nodes
        """
        while True:
            for node in self.nodes.values():
                for rand_peer in random.sample(list(self.nodes.values()), self.num_nodes):
                    if len(node.peers) == node.num_peers:
                        break
                    if node != rand_peer and (rand_peer.id not in node.peers) and len(node.peers)<node.num_peers and len(rand_peer.peers)<rand_peer.num_peers:
                        propagation_delay = round(random.uniform(0.01, 0.5), 4)
                        node.add_peer(rand_peer.id, propagation_delay)
                        rand_peer.add_peer(node.id, propagation_delay)
            
            network_graph_nodes = []
            network_graph_edges = []
            colormap_nodes = []
            colormap_edges = []
            for node in list(self.nodes.values()):
                network_graph_nodes.append(node.id)
                for i in node.peers:
                    network_graph_edges.append((i, node.id))
                    if node.id in self.slow_nodes or i in self.slow_nodes:
                        colormap_edges.append('#53565A')                    #Slow conection
                    else:
                        colormap_edges.append('#A1000E')                    #Fast Connection 
            
            G = nx.DiGraph()
            G.add_nodes_from(network_graph_nodes)
            G.add_edges_from(network_graph_edges)

            for i in network_graph_nodes:
                if(i in self.low_hash_p):
                    colormap_nodes.append('#00AEEF')
                else:
                    colormap_nodes.append('#26D07C')

            # for i in network_graph_edges:
            #     G.add_edge(str(list(i)[0]),str(list(i)[1]))   
            pos = nx.spring_layout(G)
            nx.draw(G, pos, node_color=colormap_nodes, edge_color=colormap_edges, with_labels=True)
            plt.legend(["NODES: Blue:- Low Hash Power & Green:- High Hash Power", "EDGE: Red:- Fast connection & Gray:- Slow Connection"], loc='best')
            # plt.show()
            plt.savefig(f"results/Node_Network.png")


            # G = graph.Digraph('parent', engine='neato')
            # # G.edge_attr.update(arrowsize='2')
            # # G.attr(rankdir='LR',splines='line')
            # for i in network_graph_nodes:
            #     G.node(str(i))
            # for i in network_graph_edges:
            #     G.edge(str(list(i)[0]),str(list(i)[1]))   
            # G.view()

            if self.check_connectivity():
                break
            
            for node in self.nodes.values():
                node.delete_peers()

        print("Connected P2P Network Created.")

    def check_connectivity(self):
        """Check if the blockchain is valid

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

        print("The Network is not connected.")
        return False

    def visualizer(self):
        blockchain_graph_nodes = []
        blockchain_graph_edges = []
        for user in self.nodes.values(): 
            for node in list(user.blockchain.blocks.values()):
                blockchain_graph_nodes.append(node.id)
                if node.parent_block_id == None:    # Genesis block
                    continue
                blockchain_graph_edges.append((node.id, node.parent_block_id))
            nodes = {}
            for i in range(len(blockchain_graph_nodes)):
                nodes[blockchain_graph_nodes[i]]=i
            G = graph.Digraph(f"{user.id}")
            G.attr(rankdir='LR',splines='line')
            for i in blockchain_graph_nodes:
                G.node(str(nodes[i]))
            for i in blockchain_graph_edges:
                G.edge(str(nodes[list(i)[0]]),str(nodes[list(i)[1]]))   
            # G.view()
            G.render(f"results/node_{user.id}s_blockchain")
            G.clear()
            blockchain_graph_edges.clear()
            blockchain_graph_nodes.clear()
            # del(G)
            # del(blockchain_graph_edges)
            # del(blockchain_graph_edges)
        # print(blockchain_graph_nodes)
        # print(blockchain_graph_edges)
        # G = nx.DiGraph()
        # G.add_nodes_from(blockchain_graph_nodes)
        # G.add_edges_from(blockchain_graph_edges)

        # # Draw the graph using a spring layout
        # pos = nx.nx_agraph.graphviz_layout(G, prog='neato')
        # nx.draw(G, pos, with_labels=False)
        
        # plt.show()
    # ==========================================================================================
    # Simulator functions
    def run_simulation(self, simulation_time:float):
        current_time = 0
        while current_time < simulation_time and self.event_queue != []:
            event = heapq.heappop(self.event_queue)
            current_time = event.time
            self.event_handler.handle_event(event)
        self.visualizer()
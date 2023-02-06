import random
import numpy as np
import heapq
from typing import List
import copy

from modules.network import Node
from modules.event_handler import Event, EventHandler
from modules.blockchain import Block, Transaction, Utxo


class Simulator:
    """Simulator instance
    """
    def __init__(self, num_nodes:int , slow_nodes:float, inter_arrival_time:float, inter_arrival_time_block:float , simulation_time:float):
        self.num_nodes = num_nodes
        self.num_slow_nodes = int(num_nodes*slow_nodes)
        self.iat = inter_arrival_time
        self.iat_block = inter_arrival_time_block

        self.gen_exp = np.random.default_rng()  # Exponential distribution generator
        # Create peer network
        self.nodes = self.create_nodes()    # Dictionary [id: Node]
        self.create_network()
        
        self.event_queue = list()
        self.event_handler = EventHandler(self.event_queue, self.nodes, self.iat, self.iat_block)
    
        # Initialize first transaction events
        for node in self.nodes.values():
            new_event = Event(
                event_time = float("{:.2f}".format(self.gen_exp.exponential(self.iat))),
                event_type = 1, # Create transaction
                event_node = node
            )
            self.event_handler.add_event(new_event)

        # Initialize first mining events
        for node in self.nodes.values():
            new_event = Event(
                event_time = float("{:.2f}".format(self.gen_exp.exponential(self.iat*30))),
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
        utxo_set = dict()
        transactions = list()

        # Generate genesis block transactions
        for i in range(self.num_nodes):
            coins = random.uniform(50, 500)
            new_transaction = Transaction(
                payer=-1,
                payee=i,
                value=coins,
                timestamp=0,
            )
        
            new_utxo = Utxo(
                new_transaction.id,
                owner=i,
                value=coins
            )
            new_transaction.add_utxos(input_utxos=None, output_utxos=[new_utxo])

            transactions.append(new_transaction)
            utxo_set[new_utxo.id] = new_utxo

        genesis_block = Block(
            parent_block_id=None,
            block_position=0,
            timestamp=0,
            transactions=transactions,
            block_creator=-1
        )

        nodes = {}
        random_index = random.sample(range(self.num_nodes),self.num_nodes)

        hash = list(self.gen_exp.uniform(0.0,1.0,self.num_nodes))
        hash = [i/sum(hash) for i in hash]

        for i in random_index[0:self.num_slow_nodes]:   # SLOW nodes
            nodes[i] = Node(node_id=i, node_type=0, genesis_block=copy.deepcopy(genesis_block), utxo_set=copy.deepcopy(utxo_set),hash = hash[i])
        
        for i in random_index[self.num_slow_nodes:self.num_nodes]:  # FAST nodes
            nodes[i] = Node(node_id=i, node_type=1, genesis_block=copy.deepcopy(genesis_block), utxo_set=copy.deepcopy(utxo_set),hash = hash[i])
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

    # ==========================================================================================
    # Simulator functions
    def run_simulation(self, simulation_time:float):
        current_time = 0
        while current_time < simulation_time and self.event_queue != []:
            event = heapq.heappop(self.event_queue)
            current_time = event.time
            self.event_handler.handle_event(event) 

        
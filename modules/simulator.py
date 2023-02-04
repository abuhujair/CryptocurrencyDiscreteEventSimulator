import random
import numpy as np
import heapq

from modules.node import Node
from modules.event import Event

class Simulator:
    """Simulator instance
    """
    def __init__(self, num_nodes:int , slow_nodes:float, inter_arrival_time:float):
        self.num_nodes = num_nodes
        self.num_slow_nodes = int(num_nodes*slow_nodes)
        self.iat = inter_arrival_time
        
        self.nodes = self.create_nodes()    # Dictionary [id: Node]
        self.create_network()
        
        self.event_queue = []   # priority queue of Event objects
        self.gen_exp = np.random.default_rng()

        self.initialize_simulator()

    def create_nodes(self):
        """Create all nodes in the blockchain

        Returns:
            dict: Dictionary [id: Node] of all the newly generated nodes
        """
        nodes = {}
        random_index = random.sample(range(self.num_nodes),self.num_nodes)

        for i in random_index[0:self.num_slow_nodes]:   # SLOW nodes
            nodes[i] = Node(node_id = i,node_type = 0)
        
        for i in random_index[self.num_slow_nodes:self.num_nodes]:  # FAST nodes
            nodes[i] = Node(node_id = i,node_type = 1)
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
                        node.add_peer(rand_peer.id)
                        rand_peer.add_peer(node.id)
            
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

    def initialize_simulator(self):
        """Initial event creation to first transaction event for all nodes.
        """
        
        #TODO
        # Provide initial utxo

        for node in self.nodes.values():
            heapq.heappush(
                self.event_queue,
                Event(
                    event_time = self.gen_exp.exponential(self.iat),
                    event_type = 1, 
                    event_node = node
                )
            )
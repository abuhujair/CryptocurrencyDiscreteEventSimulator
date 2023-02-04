import random


class Node:
    """Node object for the blockchain
    """
    def __init__(self, node_id: int, node_type: int):
        """Node object

        Args:
            node_id (int): Unique id for the node
            node_type (int): 0 - Slow, 1 - Fast 
        """
        self.id = node_id
        self.type = node_type

        self.num_peers = random.randint(4,8)    # Fixed number of peers
        self.peers = [] # list of node ids

    def add_peer(self, node_id: int):
        if len(self.peers) < self.num_peers:
            self.peers.append(node_id)

    def delete_peers(self):
        self.peers.clear()
        self.num_peers = random.randint(4,8)    # reset number of peers

    # ========================================================================================
    # Peer functions

    def generate_txn():
        raise NotImplementedError

    # ========================================================================================
    # Miner functions
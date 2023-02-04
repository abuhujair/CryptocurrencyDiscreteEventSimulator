import random
from typing import Dict
import hashlib

from modules.blockchain import Blockchain, Block, Utxo

class Node:
    """Node object for the blockchain
    """
    def __init__(self, node_id: int, node_type: int, genesis_block:Block, utxo_set:Dict[hashlib._hashlib.HASH, Utxo]):
        """Node object

        Args:
            node_id (int): Unique id for the node
            node_type (int): 0 - Slow, 1 - Fast 
        """
        self.id = node_id
        self.type = node_type

        self.num_peers = random.randint(4,8)    # Fixed number of peers
        self.peers = [] # list of node ids

        self.blockchain = Blockchain(genesis_block)
        self.utxo_set = utxo_set  # Dict[hashlib._hashlib.HASH, Utxo]

    def add_peer(self, node_id: int):
        """Add new peer to the node

        Args:
            node_id (int): Unique id of the node
        """
        if len(self.peers) < self.num_peers:
            self.peers.append(node_id)

    def delete_peers(self):
        """Remove all peers of the node
        """
        self.peers.clear()
        self.num_peers = random.randint(4,8)    # reset number of peers

    # ========================================================================================
    # Peer functions

    def generate_txn(self):
        raise NotImplementedError
    
    def add_utxo(self):
        raise NotImplementedError

    # ========================================================================================
    # Miner functions
from __future__ import annotations
import random
from typing import Dict
import hashlib
import numpy as np

from modules.blockchain import Blockchain, Block, Utxo, Transaction

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
        
        self.own_utxo = list()  # Nodes own money
        for utxo in list(utxo_set.values()):
            if utxo.owner == self.id:
                self.own_utxo.append(utxo)

        self.propagation_delays = {}
        self.transactions = dict()  # [transaction_id, Transaction]
        self.gen_exp = np.random.default_rng()

    def add_peer(self, node_id: int, propagation_delay:float):
        """Add new peer to the node

        Args:
            node_id (int): Unique id of the node
        """
        if len(self.peers) < self.num_peers:
            self.peers.append(node_id)
            self.propagation_delays[node_id] = propagation_delay

    def delete_peers(self):
        """Remove all peers of the node
        """
        self.peers.clear()
        self.num_peers = random.randint(4,8)    # reset number of peers

    # ========================================================================================
    # Peer functions
    def generate_txn(self, payee:int, timestamp:float):
        """Creates a new transaction

        Args:
            payee (int): Unique id of the payee
            timestamp (float): Simulation timestamp

        Returns:
            Transaction: Transaction object
        """
        total_money = 0
        for utxo in self.own_utxo:
            total_money += utxo.value

        value = random.uniform(0.0001, total_money)
        new_transaction = Transaction(
            payer=self.id,
            payee=payee,
            value=value,
            timestamp=timestamp
        )

        input_utxos = list()
        current_value = 0
        for utxo in self.own_utxo:
            current_value += utxo.value
            input_utxos.append(utxo)
            if current_value >= value:
                break

        money_back = current_value - value
        output_utxos = list()
        output_utxos.append(Utxo(   # Money back Utxo
            new_transaction.id,
            owner=self.id,
            value=money_back
        ))

        output_utxos.append(Utxo(   # paid utxo
            transaction_id=new_transaction.id,
            owner=payee,
            value=value
        ))
        new_transaction.add_utxos(input_utxos, output_utxos)
        return new_transaction

    def receive_txn(self, transaction: Transaction):
        """Receive new transaction from a peer

        Args:
            transaction (Transaction): New transaction

        Returns:
            bool: True if already present, False if added now
        """
        if transaction.id in self.transactions.keys():  # Check in pending transactions
            return False
        
        for txn in self.blockchain.current_block.transactions:  # Check in the latest block
            if transaction.id == txn.id:
                return False
            
        self.transactions[transaction.id] = transaction
        return True
            
    def get_latency(self, peer: Node, message_size: float):
        """Get transaction transmission latency

        Args:
            peer (Node): Peer node
            message_size (float): Size of message in Mb

        Returns:
            float: Latency of transmission
        """
        p = self.propagation_delays[peer.id]
        c = 5 if self.type == 0 or peer.type == 0 else 100
        m = message_size
        d = round(self.gen_exp.exponential(0.096/c), 4)
        latency = p + m/c + d
        return latency
    
    # ========================================================================================
    # Miner functions
    def add_utxo(self):
        raise NotImplementedError

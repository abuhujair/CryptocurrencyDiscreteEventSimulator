from __future__ import annotations
import random
from typing import Dict
import hashlib
import numpy as np

from modules.blockchain import Blockchain, Block, Utxo, Transaction

class Node:
    """Node object for the blockchain
    """
    def __init__(self, node_id: int, node_type: int, genesis_block:Block, utxo_set:Dict[hashlib._hashlib.HASH, Utxo], hash):
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
        self.hash = hash

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
    
    def mine_block(self, block:Block):
        """Operations performed after mining has completed

        Args:
            block (Block): New block to be added to the blockchain
        """
        self.blockchain.add_block(
            parent_block_id=self.blockchain.current_block.id,
            child_block=block,
        )
        for txn in block.transactions:
            del self.transactions[txn.id]
            self.execute_transaction(txn)

        self.utxo_set[block.miner_utxo.id] = block.miner_utxo   # Coin base transaction        

    def create_block(self):
        """Create block for mining

        Returns:
            Block: Newly formed block
        """
        counter = 0
        transactions = []
        for txn_id in list(transactions.keys()):
            if self.verify_transaction(self.transactions[txn_id]):
                transactions.append(self.transactions[txn_id])
            else:
                del self.transactions[txn_id]
            counter += 1
            if counter == 999:
                break
        
        block = Block(
            parent_block_id = -1,
            block_position = self.blockchain.current_block.block_position + 1,
            timestamp = -1,
            transactions = transactions,
            block_creator = self.id
        )
        return block 

    def verify_transaction(self, transaction:Transaction):
        """Verify total incoming and outgoing utxo of the transaction

        Args:
            transaction (Transaction): Transaction object

        Returns:
            bool: True for success, False for failure
        """
        total_incoming = 0
        total_outgoing = 0

        # Check if all the utxo are valid by comparing them from the miner utxo set
        for utxo in transaction.input_utxos:
            if not utxo.id in list(self.utxo_set.keys()):
                return False
            
        for utxo in transaction.input_utxos:
            total_incoming += utxo.value

        for utxo in transaction.output_utxos:
            total_outgoing += utxo.value

        if total_incoming != total_outgoing + transaction.value or total_incoming < 0:  # Total incoming = Total outgoing
            return False
        
        return True
    
    def execute_transaction(self, transaction: Transaction):
        """Execute transaction by modifying the utxo

        Args:
            transaction (Transaction): Transaction object
        """
        for utxo in transaction.input_utxos:
            del self.utxo_set[utxo.id]
        
        for utxo in transaction.output_utxos:
            self.utxo_set[utxo.id] = utxo

    def verify_block(self, block:Block):
        """Verify if block can be added to the blockchain

        Args:
            block (Block): Block to be added

        Returns:
            bool: True if verified, else False
        """
        for transaction in self.transactions:
            if self.verify_transaction(transaction):
                return False

        return True
    
    def create_fork(self, block:Block):
        """Create fork for the newly added block

        Args:
            block (Block): New block to be added

        Returns:
            bool: True if the block is added, else False
        """
        if block.id not in self.blockchain.blocks.keys():    # If block already not exists
            if self.blockchain.add_block(
                parent_block_id = block.parent_block_id,
                child_block = block
            ):
                for txn in block.transactions:
                    del self.transactions[txn.id]
                    self.execute_transaction(txn)

                self.utxo_set[block.miner_utxo.id] = block.miner_utxo   # Coin base transaction   
                return True
        return False 
        
    def remove_block(self, block:Block):
        pass



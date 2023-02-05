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
    def mine_block(self, block:Block):
        """Operations performed after mining has completed

        Args:
            block (Block): New block to be added to the blockchain
        """
        self.blockchain.add_block(
            parent_block_id=block.parent_block_id,
            child_block=block,
        )
        self.execute_block_utxo(block)

    def create_block(self):
        """Create block for mining

        Returns:
            Block: Newly formed block
        """
        counter = 0
        txns = []
        for txn_id in list(self.transactions.keys()):
            if self.verify_transaction(self.transactions[txn_id]):
                txns.append(self.transactions[txn_id])
            else:
                del self.transactions[txn_id]
            counter += 1
            if counter == 999:
                break
        
        block = Block(
            parent_block_id = self.blockchain.current_block.id,
            block_position = self.blockchain.current_block.block_position + 1,
            timestamp = -1,
            transactions = txns,
            block_creator = self.id
        )
        return block 

    def verify_transaction(self, transaction:Transaction, utxo_set: Dict[hashlib._hashlib.HASH, Utxo] = None):
        """Verify total incoming and outgoing utxo of the transaction

        Args:
            transaction (Transaction): Transaction object

        Returns:
            bool: True for success, False for failure
        """
        
        if utxo_set == None:
            utxo_set = self.utxo_set
        total_incoming = 0
        total_outgoing = 0

        # Check if all the utxo are valid by comparing them from the miner utxo set
        for utxo in transaction.input_utxos:
            if not utxo.id in list(utxo_set.keys()):
                return False
            
        for utxo in transaction.input_utxos:
            total_incoming += utxo.value

        for utxo in transaction.output_utxos:
            total_outgoing += utxo.value

        if total_incoming != total_outgoing + transaction.value or total_incoming < 0:  # Total incoming = Total outgoing
            return False
        
        return True
    
    def execute_transaction(self, transaction: Transaction, utxo_set: Dict[hashlib._hashlib.HASH, Utxo]):
        """Execute transaction by modifying the utxo

        Args:
            transaction (Transaction): Transaction object
            utxo_set (Dict[hashlib._hashlib.HASH, Utxo], optional): utxo_set to be modified. Defaults to None.
        """
        if utxo_set == None:   
            utxo_set = self.utxo_set

        for utxo in transaction.input_utxos:
            del self.utxo_set[utxo.id]
        
        for utxo in transaction.output_utxos:
            self.utxo_set[utxo.id] = utxo

    def remove_transaction( self, transaction:Transaction, utxo_set: Dict[hashlib._hashlib.HASH, Utxo]):
        """remove transaction by modifying the utxo_set

        Args:
            transaction (Transaction): Transaction object
            utxo_set (Dict[hashlib._hashlib.HASH, Utxo], optional): utxo_set to be modified. Defaults to None.
        """
        if utxo_set == None:   
            utxo_set = self.utxo_set

        for utxo in transaction.output_utxos:
            del self.utxo_set[utxo.id]
        
        for utxo in transaction.input_utxos:
            self.utxo_set[utxo.id] = utxo

    def verify_block(self, block:Block, utxo_set: Dict[hashlib._hashlib.HASH, Utxo] = None):
        """Verify if block can be added to the blockchain, for block received or created by it.

        Args:
            block (Block): Block to be added

        Returns:
            bool: True if verified, else False
        """
        if utxo_set == None: #if primary chain is being verified
            utxo_set = self.utxo_set
        
        for transaction in block.transactions:
            if not self.verify_transaction(transaction):
                return False
        return True
    
    def execute_block_utxo(self, block: Block, utxo_set: Dict[hashlib._hashlib.HASH, Utxo] = None,
                            transactions: Dict[hashlib._hashlib.HASH,Transaction] = None):
        """Added new utxo by the block, and update the pending transaction pool

        Args:
            block (Block): Block Object
            utxo_set (Dict[hashlib._hashlib.HASH, Utxo], optional): utxo_set. Defaults to None.
            transactions (Dict[hashlib._hashlib.HASH,Transaction], optional): transactions. Defaults to None.
        """
        if utxo_set == None:
            utxo_set = self.utxo_set
        if transactions == None:
            transactions = self.transactions

        for txn in block.transactions:
            del transactions[txn.id] #TODO How to handle this when we are only making copy of utxo
            self.execute_transaction(txn,utxo_set)
        self.utxo_set[block.miner_utxo.id] = block.miner_utxo   # Coin base transaction        

    def remove_block_utxo(self, block: Block, utxo_set: Dict[hashlib._hashlib.HASH, Utxo] = None,
                            transactions: Dict[hashlib._hashlib.HASH,Transaction] = None):
        """Removes all the utxo created by block, and add utxo removed by the block when added to blockchain 
        Args:
            block (Block): Block Object
            utxo_set (Dict[hashlib._hashlib.HASH, Utxo], optional): utxo_set. Defaults to None.
            transactions (Dict[hashlib._hashlib.HASH,Transaction], optional): transactions. Defaults to None.
        """
        if utxo_set == None:
            utxo_set = self.utxo_set
        if transactions == None:
            transactions = self.transactions

        for transaction in block.transactions:
            self.remove_transaction(transaction=transaction,utxo_set=utxo_set)
            transactions[transaction.id] = transaction
        del utxo_set[block.miner_utxo.id]

    def receive_block(self, block:Block):
        if block.id in self.blockchain.blocks.keys() or block.parent_block_id not in self.blockchain.blocks.keys():
            return False

        latest_block_position = self.blockchain.current_block.block_position
        #TODO fork block verification will fail due to invalid utxo
        if block.parent_block_id != self.blockchain.current_block.id: # This will lead to fork, or extension of forked chain.
            #Since checkpointing is not implemented, fork and fork extension will be possible at any blocklength.
            
            utxo_set,transactions = self.create_new_utxo_set(block) #create new utxo_set for the forked chain
            if self.verify_block(block,utxo_set):
                self.blockchain.add_block(
                    parent_block_id = block.parent_block_id,
                    child_block = block)
                if(block.block_position > latest_block_position): #If the chain is being switched, utxo_set need to be updated    
                    self.utxo_set = utxo_set
                    self.transactions = transactions
                    self.execute_block_utxo(block)
                return True
            else:
                return False

        elif block.block_position > latest_block_position:    # verify block, and add chain to the block.
            if self.verify_block(block):
                self.blockchain.add_block(
                    parent_block_id=block.parent_block_id,
                    child_block=block
                )
                self.execute_block_utxo(block)
                return True
            else:
                return False
        return False

    def create_new_utxo_set(self, block:Block):
        """Creates a copy of utxo_set and pending transaction pool for the forked chain

        Args:
            block (Block): Block Object

        Returns:
            utxo_set: Dict[utxo_id, utxo]
            txn_set: Dict[transactions_id, transaction]
        """
        utxo_set = self.utxo_set.copy()
        txn_set = self.transactions.copy()

        block_oc = self.blockchain.current_block #original_block_chain
        length_oc = block_oc.block_position 
        while length_oc >= block.block_position: #Removed all the utxo until the length of chain became equal.
            self.remove_block_utxo(block_oc,utxo_set,txn_set)
        
            block_oc = self.blockchain.blocks[block_oc.parent_block_id]
            length_oc = block_oc.block_position

        block_nc = self.blockchain.blocks[block.parent_block_id] #new_block_chain
        block_to_be_added = []
        while block_oc != block_nc: #Remove utxo until fork point
            self.remove_block_utxo(block_oc,utxo_set,txn_set)
            
            block_to_be_added.append(block_nc.id)
            block_oc = self.blockchain.blocks[block_oc.parent_block_id]
            length_oc = block_oc.block_position
            block_nc = self.blockchain.blocks[block_nc.parent_block_id]

        while block_to_be_added != []: #add utxo until chain is new chain is created
            block_add = self.blockchain.blocks[block_to_be_added.pop()]
            self.execute_block_utxo(block_add,utxo_set,txn_set)
        
        return utxo_set,txn_set
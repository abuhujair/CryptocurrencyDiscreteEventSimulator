from __future__ import annotations
import random
from typing import Dict
import numpy as np
import copy

import settings
from modules.blockchain import Blockchain, Block, Transaction

class Node:
    """Peer node of the network
    """
    def __init__(self, node_id: int, node_type: int, genesis_block:Block, hash:float, MAX_BLOCK_LENGTH:int, node_label:int=0):
        """Initialize peer node with miner properties.

        Args:
            node_id (int): Unique id for the node
            node_type (int): 0 - Slow, 1 - Fast 
            genesis_block (Block): Genesis block of the blockchain
            hash (float): Hashing power
            MAX_BLOCK_LENGTH (int): Maximum number of transactions in a block
        """
        self.id = node_id
        self.node_label = node_label # 0: Honest Miner, 1: Selfish Miner, 2: Stubborn Miner
        if self.node_label == 1 or self.node_label== 2:
            self.block_queue = list() # List[Block] of block pending to be transmitted by attacker

        self.type = node_type
        self.MAX_BLOCK_LENGTH = MAX_BLOCK_LENGTH

        self.num_peers = random.randint(4,8)    # Fixed number of peers
        self.peers = [] # list of node ids
        self.propagation_delays = {}
        self.hash = hash

        self.blockchain = Blockchain(genesis_block)

        self.pending_transactions = dict()  # [transaction_id, Transaction]
        self.transactions = dict()  # [transaction_id, Transaction]
        self.gen_exp = np.random.default_rng()
        #TODO how to maintain current account balance across all operations
        self.current_balance = self.blockchain.current_block.account_balance[self.id]

    # ========================================================================================
    # Peer functions
    def add_peer(self, node_id: int, propagation_delay:float):
        """Add new peer to current peer

        Args:
            node_id (int): Unique id of the node
        """
        if len(self.peers) < self.num_peers:
            self.peers.append(node_id)
            self.propagation_delays[node_id] = propagation_delay

    def delete_peers(self):
        """Remove all peers of the node
        """
        self.peers = []
        self.propagation_delays = {}
        self.num_peers = random.randint(4,8)    # reset number of peers

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
        latency = round(p + m/c + d,4)
        return latency

    # ========================================================================================
    # Transaction functions
    def generate_txn(self, payee:int, timestamp:float):
        """Creates a new transaction

        Args:
            payee (int): Unique id of the payee
            timestamp (float): Simulation timestamp

        Returns:
            Transaction: Transaction object
        """
        total_money = self.blockchain.current_block.account_balance[self.id]

        value = random.uniform(0.0001, total_money)
        new_transaction = Transaction(
            payer=self.id,
            payee=payee,
            value=value,
            timestamp=timestamp
        )
        self.pending_transactions[new_transaction.id] = new_transaction
        return new_transaction

    def receive_txn(self, transaction: Transaction):
        """Receive new transaction from a peer

        Args:
            transaction (Transaction): New transaction

        Returns:
            bool: False if already present, True if added now
        """
        if transaction.id not in self.transactions:  # Check in pending transactions                
            self.transactions[transaction.id] = transaction
            self.pending_transactions[transaction.id] = transaction
            return True
        return False
            
    # ========================================================================================
    # Miner functions    
    def mine_block(self, block:Block, timestamp: float):
        """Operation to be performed when mining is successful
        Args:
            block (Block): Block Object
            timestamp (float): Timestamp

        Returns:
            bool: True, if block is verfied and added to blockchain, else False
        """
        block.timestamp = timestamp
        if self.verify_block(block):
            self.blockchain.add_block(child_block=block)
            self.execute_block(block)
            return True
        return False

    def create_block(self):
        """Create block for mining

        Returns:
            Block: Newly formed block
        """
        account_balance = copy.deepcopy(self.blockchain.current_block.account_balance)
        counter = 0
        txns = []
        #TODO Some transaction may not be added to transaction pool ever? How to prioritize.
        for txn in list(self.pending_transactions.values()):
            if account_balance[txn.payer] >= txn.value:
                txns.append(copy.deepcopy(txn))
                account_balance[txn.payer] -= txn.value
                account_balance[txn.payee] += txn.value
                counter += 1
            if counter == self.MAX_BLOCK_LENGTH-1:
                break

        account_balance[self.id] +=50
        block = Block(
            parent_block_id=self.blockchain.current_block.id,
            block_position=self.blockchain.current_block.block_position + 1,
            timestamp=-1,
            transactions=txns,
            block_creator=self.id,
            account_balance=account_balance
        )
        return block 

    def verify_block(self, block:Block, pending_transactions:Dict[str,Transaction] = None, current_block:Block = None):
        """Verify a block to be added to blockchain

        Args:
            block (Block): Block Object
            pending_transactions (Dict[str,Transaction], optional): Pool of pending transactions. Defaults to None.
            current_block (Block, optional): Pointer to the last block of blockchain. Defaults to None.

        Returns:
            bool: True if block is verfied successfully, else False
        """
        if pending_transactions == None: #if primary chain is being verified
            pending_transactions = self.pending_transactions
        if current_block == None: #if primary chain is being verified
            current_block = self.blockchain.current_block

        current_account_balance = copy.deepcopy(current_block.account_balance)
        sum_outgoing = [0]*len(current_account_balance)
        txns = dict() #Dict[str,Transaction]
        for transaction in block.transactions:
            if transaction not in txns and (transaction.id in pending_transactions 
                or transaction.id not in self.transactions):
                txns[transaction.id] = transaction
                sum_outgoing[transaction.payer] -= transaction.value
                sum_outgoing[transaction.payee] += transaction.value
            else:
                return False
        
        #Coinbase Transaction
        sum_outgoing[block.coinbase_transaction.payee] += block.coinbase_transaction.value

        for node in range(len(current_account_balance)):
            if (current_account_balance[node]+sum_outgoing[node] < 0  
                or round(current_account_balance[node]+sum_outgoing[node], 5) != round(block.account_balance[node],5)):
                return False
        return True
    
    def execute_block(self, block:Block, pending_transactions:Dict[str,Transaction] = None):
        """Updated the pending transaction pool
        Args:
            block (Block): Block Object
            pending_transactions (Dict[str,Transaction], optional): pending transaction pool. Defaults to None.
            current_block (Block, optional): last block of blockchain. Defaults to None.
        """
        if pending_transactions == None: #if primary chain is being verified
            pending_transactions = self.pending_transactions
        # if current_block == None: #if primary chain is being verified
        #     current_block = self.blockchain.current_block

        for txn in block.transactions:
            if txn.id in pending_transactions:
                del pending_transactions[txn.id]
            else:
                self.transactions[txn.id] = txn

        if block.coinbase_transaction.id not in self.transactions:
            self.transactions[block.coinbase_transaction.id] = copy.deepcopy(block.coinbase_transaction)
        
    def remove_block(self, block:Block, pending_transactions:Dict[str,Transaction] = None):
        """Add all transaction of block back to pending_transaction pool

        Args:
            block (Block): Block Object
            pending_transactions (Dict[str,Transaction], optional): Pending transaction pool. Defaults to None.
            current_block (Block, optional): last block of blockchain. Defaults to None.
        """
        if pending_transactions == None: #if primary chain is being verified
            pending_transactions = self.pending_transactions
        # if current_block == None: #if primary chain is being verified
        #     current_block = self.blockchain.current_block

        for txn in block.transactions:
            pending_transactions[txn.id] = txn
        
    def receive_block(self, block:Block):
        """Operation to be done when a block is received.

        Args:
            block (Block): Block Object

        Returns:
            bool: True if block is to be propogated. otherwise False.
        """
        if block.id in self.blockchain.blocks.keys():
            return False

        if block.parent_block_id not in self.blockchain.blocks.keys():
            if block.parent_block_id not in self.blockchain.cached_blocks:
                self.blockchain.cached_blocks[block.parent_block_id] = block
            return False
        
        if block.parent_block_id in self.blockchain.cached_blocks:
            del self.blockchain.cached_blocks[block.parent_block_id]

        latest_block_position = self.blockchain.current_block.block_position
        if block.parent_block_id != self.blockchain.current_block.id: # This will lead to fork, or extension of forked chain.
            #Since checkpointing is not implemented, fork and fork extension will be possible at any blocklength.
            pending_transactions = self.create_new_pool(block) #create new pending transaction pool
            if self.verify_block(block,pending_transactions,self.blockchain.blocks[block.parent_block_id]):
                self.blockchain.add_block(child_block = block)
                if(block.block_position == latest_block_position+1): #If the chain is being switched, pending transaction pool need to be updated    
                    self.pending_transactions = pending_transactions
                    self.execute_block(block)
            else:
                return False

        elif block.block_position == latest_block_position+1:    # verify block, and add chain to the block.
            if self.verify_block(block):
                self.blockchain.add_block(child_block=block)
                self.execute_block(block)
            else:
                return False
        #Return true if the block is added to the chain (not necessarily main chain)
        return True

    def create_new_pool(self, block:Block):
        """Creates a copy of pending transaction pool for the forked chain

        Args:
            block (Block): block object

        Returns:
            pending_transactions Dict[str, Transaction]: pool of pending transactions for the forked chain
        """
        pending_transactions = copy.deepcopy(self.pending_transactions)

        block_oc = self.blockchain.current_block #original_block_chain
        length_oc = block_oc.block_position 
        while length_oc >= block.block_position: #Add all transaction in pending transactions until the length of chain becomes equal
            self.remove_block(block_oc,pending_transactions)
        
            block_oc = self.blockchain.blocks[block_oc.parent_block_id]
            length_oc = block_oc.block_position

        block_nc = self.blockchain.blocks[block.parent_block_id] #new_block_chain
        block_to_be_added = []
        while block_oc.id != block_nc.id: #Add all transaction in pending transactions until fork point
            self.remove_block(block_oc,pending_transactions)
            
            block_to_be_added.append(block_nc.id)
            block_oc = self.blockchain.blocks[block_oc.parent_block_id]
            length_oc = block_oc.block_position
            block_nc = self.blockchain.blocks[block_nc.parent_block_id]

        while block_to_be_added != []: #add utxo until chain is new chain is created
            block_add = self.blockchain.blocks[block_to_be_added.pop()]
            self.execute_block(block_add,pending_transactions)
        
        return pending_transactions
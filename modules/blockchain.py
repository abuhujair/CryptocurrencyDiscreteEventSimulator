from __future__ import annotations
import hashlib
from typing import List, Dict
import networkx as nx
import matplotlib.pyplot as plt        
import graphviz as graph

class Transaction:
    """Transaction instance
    """
    def __init__(self, payer:int, payee:int, value:float, timestamp:float):
        """Creates transaction object

        Args:
            payer (int): Unique id of the payer of the transaction
            payee (int): Unique id of the payee of the transactoin
            value (float): Total value of the transaction
            timestamp (float): Simulation timestamp of the transaction
        """
        self.id = hashlib.sha256(f"{payer}-{payee}-{value}-{timestamp}".encode()).hexdigest()
        self.payer = payer
        self.payee = payee
        self.value = value
        self.timestamp = timestamp

    def __str__(self) -> str:
        output = f"\tTRANSACTION {self.id} Payer : {self.payer} Payee : {self.payee} Value : {self.value} Timestamp : {self.timestamp}\n"
        return output

class Block:
    """Transaction block instance
    """
    def __init__(self, parent_block_id:str, block_position:int, timestamp:float, transactions:List[Transaction], block_creator:int, account_balance:Dict[int,float]) -> None:
        """Creates a block of the blockchain with the transactions

        Args:
            parent_block_id (str): Unique id of the parent block, -1 if block has not been added in the blockchain yet
            block_position (int): Position of the block in the block chain, -1 if block has not been added in the blockchain yet
            timestamp (float): Simulation timestamp
            transactions (List[Transaction]): List of transactions contained in the block
            block_creator (int): Unique id of the creator of the block
            account_balance (Dict[int, float]): Account balance of all the peers
        """
        transaction_str = ""
        for transaction in transactions:
            transaction_str += str(transaction.id) + " "

        self.id = hashlib.sha256(f"{timestamp}-{transaction_str}".encode()).hexdigest()
        self.timestamp = timestamp
        self.transactions = transactions

        self.parent_block_id = parent_block_id
        self.block_position = block_position
        self.coinbase_transaction = Transaction(payer=-1,payee=block_creator,value=50,timestamp=timestamp)
        self.account_balance = account_balance #Dict [int, float]
        
    def __str__(self) -> str:
        if self.parent_block_id is None:
            output = f"GENESIS BLOCK {self.id} Parent block id : None Timestamp : {self.timestamp} Block position : {self.block_position}\n"
        else:
            output = f"BLOCK {self.id} Parent block id : {self.parent_block_id} Timestamp : {self.timestamp} Block position : {self.block_position}\n"
        output += f"\tTransactions:\n"
        for txn in self.transactions:
            output += f"\t{txn}"
        output += f"\tCoinbase Transaction:\n \t{self.coinbase_transaction}"
        output += f"\tSum of Account Balance: {sum(self.account_balance.values())}"
        return output

class Blockchain:
    """Blockchain instance
    """
    def __init__(self, genesis_block:Block) -> None:
        """Blockchain object that stores a tree structure chain

        Args:
            genesis_block (Block): Genesis block of the blockchain
        """
        self.root = genesis_block
        self.current_block = genesis_block
        self.blocks = dict()    # Dict[str, Block]
        self.blocks[genesis_block.id] = genesis_block
        self.cached_blocks = dict() #Dict[parent_block_id, Block]


    def add_block(self, child_block:Block):
        """Add new block to the blockchain

        Args:
            parent_block_id (str): Unique id of the parent block
            child_block (Block): New block to be added

        Returns:
            bool: True if block added to the main chain, else False
        """
        self.blocks[child_block.id] = child_block
        if ( self.current_block.id == child_block.parent_block_id #A new block is added to existing chain
            or child_block.block_position == self.current_block.block_position +1 ): #a new block is added to forked chain
            self.current_block = child_block
    
    def __str__(self) -> str:
        output = f"Blockchain\n"
        for block in list(self.blocks.values()):
            output += f"\t{block}\n"
        return output
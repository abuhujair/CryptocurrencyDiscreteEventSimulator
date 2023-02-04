from __future__ import annotations
import hashlib
from typing import List, Dict


class Utxo:
    """Unspent transaction output instance
    """
    def __init__(self, transaction_id:hashlib._hashlib.HASH, owner:int, value:float):
        """Creates a new Utxo from the provided transaction details

        Args:
            transaction_id (hashlib._hashlib.HASH): Unique transaction id
            owner (int): Unique node id which owns the utxo
            value (float): Total value of the utxo
        """
        self.id = hashlib.sha256(f"{owner}-{value}-{transaction_id.hexdigest()}".encode())
        self.transaction_id = transaction_id
        self.owner = owner
        self.value = value
        

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
        self.id = hashlib.sha256(f"{payer}-{payee}-{value}-{timestamp}".encode())
        self.payer = payer
        self.payee = payee
        self.value = value
        self.timestamp = timestamp

    def add_utxos(self, input_utxos:List[Utxo], output_utxos:List[Utxo]):
        """Add utxos to the transaction

        Args:
            input_utxos (List[Utxo]): List of input Utxo 
            output_utxos (List[Utxo]): List of output Utxo 
        """
        self.input_utxos = input_utxos
        self.output_utxos = output_utxos

class Block:
    """Transaction block instance
    """
    def __init__(self, parent_block_id:hashlib._hashlib.HASH, block_position:int, timestamp:float, transactions:List[Transaction], block_creator:int) -> None:
        """Creates a block of the blockchain with the transactions

        Args:
            parent_block_id (hashlib._hashlib.HASH): Unique id of the parent block, -1 if block has not been added in the blockchain yet
            block_position (hashlib._hashlib.HASH): Position of the block in the block chain, -1 if block has not been added in the blockchain yet
            timestamp (float): Simulation timestamp
            transactions (List[Transaction]): List of transactions contained in the block
            block_creator (int): Unique id of the creator of the block
        """
        transaction_str = ""
        for transaction in transactions:
            transaction_str += str(transaction.id.hexdigest()) + " "

        self.id = hashlib.sha256(f"{timestamp}-{transaction_str}".encode())
        self.timestamp = timestamp
        self.transactions = transactions

        self.parent_block_id = parent_block_id
        self.block_position = block_position
        self.miner_utxo = Utxo(transaction_id=self.id, owner=block_creator, value=50)

    def add_child_block(self, block:Block):
        """Add child block to the current block

        Args:
            block (Block): Child block to be added
        """
        if block not in self.child_blocks:
            self.child_blocks.append(block)
    

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
        self.blocks = dict()    # Dict[hashlib._hashlib.HASH, Block]
        self.blocks[genesis_block.id] = genesis_block

    def add_block(self, parent_block_id: hashlib._hashlib.HASH, child_block:Block):
        """Add new block to the blockchain

        Args:
            parent_block_id (hashlib._hashlib.HASH): Unique id of the parent block
            child_block (Block): New block to be added

        Returns:
            bool: True if block added successfully, else False
        """
        if parent_block_id not in list(self.blocks.keys()): # Parent block does not exist
            return False

        self.blocks[child_block.id] = child_block
        child_block.parent_block_id = parent_block_id
        self.current_block = child_block
        return True

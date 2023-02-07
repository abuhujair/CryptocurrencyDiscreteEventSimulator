from __future__ import annotations
import hashlib
from typing import List, Dict
# import networkx as nx
# import matplotlib.pyplot as plt


class Utxo:
    """Unspent transaction output instance
    """
    def __init__(self, transaction_id:str, owner:int, value:float):
        """Creates a new Utxo from the provided transaction details

        Args:
            transaction_id (str): Unique transaction id
            owner (int): Unique node id which owns the utxo
            value (float): Total value of the utxo
        """
        self.id = hashlib.sha256(f"{owner}-{value}-{transaction_id}".encode()).hexdigest()
        self.transaction_id = transaction_id
        self.owner = owner
        self.value = value

    def __str__(self) -> str:
        return f"\t\tUTXO {self.id}\n\t\tTransaction ID : {self.transaction_id}\n\t\tOwner : {self.owner}\n\t\tValue : {self.value}"
        

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

    def add_utxos(self, input_utxos:List[Utxo], output_utxos:List[Utxo]):
        """Add utxos to the transaction

        Args:
            input_utxos (List[Utxo]): List of input Utxo 
            output_utxos (List[Utxo]): List of output Utxo 
        """
        self.input_utxos = input_utxos
        self.output_utxos = output_utxos

    def __str__(self) -> str:
        output = f"\tTRANSACTION {self.id}\n\tPayer : {self.payer}\n\tPayee : {self.payee}\n\tValue : {self.value}\n\tTimestamp : {self.timestamp}\n"
        if self.input_utxos is not None:
            output += "\tPayer UTXO\n"
            for utxo in self.input_utxos:
                output += f"\t\t{utxo}\n"
        output += "\tGenerated UTXO\n"
        for utxo in self.output_utxos:
            output += f"\t\t{utxo}\n"
        return output

class Block:
    """Transaction block instance
    """
    def __init__(self, parent_block_id:str, block_position:int, timestamp:float, transactions:List[Transaction], block_creator:int) -> None:
        """Creates a block of the blockchain with the transactions

        Args:
            parent_block_id (str): Unique id of the parent block, -1 if block has not been added in the blockchain yet
            block_position (int): Position of the block in the block chain, -1 if block has not been added in the blockchain yet
            timestamp (float): Simulation timestamp
            transactions (List[Transaction]): List of transactions contained in the block
            block_creator (int): Unique id of the creator of the block
        """
        transaction_str = ""
        for transaction in transactions:
            transaction_str += str(transaction.id) + " "

        self.id = hashlib.sha256(f"{timestamp}-{transaction_str}".encode()).hexdigest()
        self.timestamp = timestamp
        self.transactions = transactions

        self.parent_block_id = parent_block_id
        self.block_position = block_position
        self.miner_utxo = Utxo(transaction_id=self.id, owner=block_creator, value=50)

    def __str__(self) -> str:
        if self.parent_block_id is None:
            output = f"BLOCK {self.id}\nParent block id : None\nTimestamp : {self.timestamp}\nBlock position : {self.block_position}\n"
        else:
            output = f"BLOCK {self.id}\nParent block id : {self.parent_block_id}\nTimestamp : {self.timestamp}\nBlock position : {self.block_position}\n"
        output += "Transactions\n"
        for txn in self.transactions:
            output += f"\t{txn}\n"
        output += f"Miner UTXO : {self.miner_utxo}\n"
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

    def add_block(self, parent_block_id: str, child_block:Block):
        """Add new block to the blockchain

        Args:
            parent_block_id (str): Unique id of the parent block
            child_block (Block): New block to be added

        Returns:
            bool: True if block added successfully, else False
        """
        if parent_block_id not in list(self.blocks.keys()): # Parent block does not exist
            return False
        
        self.blocks[child_block.id] = child_block
        if ( self.current_block.id == child_block.parent_block_id #A new block is added to existing chain
            or child_block.block_position > self.current_block.block_position +1 ): #a new block is added to forked chain
            self.current_block = child_block
        return True
    
    def __str__(self) -> str:
        nodes = {}
        id_mapping = {}
        counter  = 0
        for node in list(self.blocks.values()):
            id_mapping[node.id] = counter
            counter += 1

        for node in list(self.blocks.values()):
            try:
                if id_mapping[node.parent_block_id] in nodes.keys():
                    nodes[id_mapping[node.parent_block_id]].append((id_mapping[node.id],node.block_position))
                else:
                    nodes[id_mapping[node.parent_block_id]] = [(id_mapping[node.id],node.block_position)]
            except:
                pass

        return f"{nodes}"

    # def __str__(self) -> str:
    #     blockchain_graph_nodes = []
    #     blockchain_graph_edges = []
    #     for node in list(self.blocks.values()):
    #         blockchain_graph_nodes.append(node.id.hexdigest())
    #         if node.parent_block_id == None:    # Genesis block
    #             continue
    #         blockchain_graph_edges.append((node.id.hexdigest(), node.parent_block_id.hexdigest()))

    #     print(blockchain_graph_nodes)
    #     print(blockchain_graph_edges)
    #     G = nx.DiGraph()
    #     G.add_nodes_from(blockchain_graph_nodes)
    #     G.add_edges_from(blockchain_graph_edges)
    #     nx.draw_networkx(G)
    #     plt.title("Blockchain")
    #     plt.savefig("test.png")
    #     return "Printed"
    
    # def __str__(self) -> str:
    #     output = f"Blockchain\n"
    #     for block in list(self.blocks.values()):
    #         output += f"{block}\n"
    
    #     return output
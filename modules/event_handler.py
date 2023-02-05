import heapq
from typing import List, Dict
import random
import numpy as np

from modules.network import Node
from utils.logger import get_logger
from modules.blockchain import Block


class Event:
    def __init__(self, event_time:float, event_type:int, event_node: Node, **kwargs):
        """Event object

        Args:
            event_time (float): simulation time
            event_type (int): 0: Not defined, 1: create txn, 2: recieve txn, 3: start_mining (to be called only once), 4: end_mining, 5: receive_block
            event_node (Node): Node object that creates the event
        """
        self.time = event_time
        self.type = event_type 
        self.node = event_node
        self.extra_parameters = kwargs

    def __lt__(self,other:"Event")->bool:
        return self.time < other.time
    
    def __str__(self):
        return f"EVENT : {self.time}s-Type:{self.type}-NodeId:{self.node.id}-{self.extra_parameters.values()}"
    

class EventHandler:
    """Event handler instance of the simulator
    """
    def __init__(self, event_queue:List[Event], nodes:Dict[int, Node], iat:float, iat_b:float) -> None:
        self.event_queue = event_queue   # Priority list for events
        self.nodes = nodes
        self.gen_exp = np.random.default_rng()
        self.logger = get_logger("EVENT")
        self.iat = iat
        self.iat_b = iat_b
    
    def add_event(self, event:Event):
        """Push new event in the event queue

        Args:
            event (Event): Event object
        """
        heapq.heappush(self.event_queue, event)

    def handle_event(self, event:Event):
        self.logger.info(event)

        if event.type == 1: # Create transaction
            while True:
                payee = random.randint(0,len(self.nodes)-1)
                if event.node.id != payee:
                    break
            new_transaction = event.node.generate_txn(payee=payee, timestamp=event.time)
            
            # Propogate new transaction
            for peer_id in event.node.peers:
                latency = event.node.get_latency(self.nodes[peer_id], 0.008)  # 0.008 Mb = 1KB
                
                self.add_event(Event(
                    event_time=round(event.time + latency,4),
                    event_type=2,
                    event_node=self.nodes[peer_id],
                    transaction = new_transaction,
                    event_creator = event.node
                )) 

            # Generate new transaction
            self.add_event(Event(
                event_time=round(self.gen_exp.exponential(self.iat)) + event.time,
                event_type=1,
                event_node=event.node,
            ))
        
        elif event.type == 2:   # Receive transaction
            transaction = event.extra_parameters['transaction']
            event_creator_node = event.extra_parameters['event_creator']
            if event.node.receive_txn(transaction):
                for peer_id in event.node.peers:
                    if peer_id == event_creator_node:   # Circular dependency
                        continue

                    latency = event.node.get_latency(self.nodes[peer_id], 0.008)  # 0.008 Mb = 1KB
                    
                    self.add_event(Event(
                        event_time=round(event.time + latency,4),
                        event_type=2,
                        event_node=self.nodes[peer_id],
                        transaction = transaction,
                        event_creator = event.node
                    )) 

        elif event.type == 3:   # Mining Start
            new_block = event.node.create_block()
            self.add_event(Event(
                event_time=round(event.time+self.gen_exp.exponential(self.iat_b/event.node.hash),4),
                event_type=4,
                event_node=event.node,
                block=new_block
            ))

        elif event.type == 4:   # Mining end
            latest_block_number = event.node.blockchain.current_block.block_position
            block = event.extra_parameters['block']
            if block.block_position >= latest_block_number:
                event.node.mine_block()
                # Propagate the block
                for peer_id in event.node.peers:
                    message_length = (len(block.transactions) + 1)*0.008
                    latency = event.node.get_latency(self.nodes[peer_id], message_length)
                    
                    self.add_event(Event(
                        event_time=round(event.time + latency, 4),
                        event_type=5,
                        event_node=self.nodes[peer_id],
                        block = block,
                        event_creator = event.node
                    )) 
            
            new_block = event.node.create_block()
            self.add_event(Event(
                event_time=round(event.time+self.gen_exp.exponential(self.iat_b/event.node.hash),4),
                event_type=4,
                event_node=event.node,
                block=new_block
            ))

        elif event.type == 5:   # Receive block
            latest_block_number = event.node.blockchain.current_block.block_position
            block = event.extra_parameters['block']
            #TODO fork block verification will fail due to invalid utxo
            if block.block_position == latest_block_number and event.node.verify_block(block): # Create fork
                event.node.create_fork()

            elif block.block_position > latest_block_number:    # Change longest chain
                # Case 1 : No fork

                # Case 2 : fork
                #TODO Reverting of the transaction
                fork_start_id = event.node.blockchain.current_block.parent_block_id
                parent_id = block.parent_block_id
                for blk in event.node.blockchain.blocks.keys():
                    if blk.id != parent_id and blk.parent_block_id == fork_start_id:
                        event.node.remove_block(blk)
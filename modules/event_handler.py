import heapq
from typing import List, Dict
import random
import numpy as np
import copy

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
        if self.type == 1:
            return f"EVENT : {self.time}s-Type:{self.type}-NodeId:{self.node.id}"
        if self.type == 2:
            return f"EVENT : {self.time}s-Type:{self.type}-NodeId:{self.node.id}-Transaction:{self.extra_parameters['transaction'].id}-EventCreator:{self.extra_parameters['event_creator'].id}"
        if self.type == 3:
            return f"EVENT : {self.time}s-Type:{self.type}-NodeId:{self.node.id}"
        if self.type == 4:
            return f"EVENT : {self.time}s-Type:{self.type}-NodeId:{self.node.id}-Block:{self.extra_parameters['block'].id}"
        if self.type == 5:
            return f"EVENT : {self.time}s-Type:{self.type}-NodeId:{self.node.id}-Block:{self.extra_parameters['block'].id}-EventCreator:{self.extra_parameters['event_creator'].id}"
    

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
                    transaction = copy.deepcopy(new_transaction),
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
                        transaction = copy.deepcopy(transaction),
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
            print(event)
            latest_block_number = event.node.blockchain.current_block.block_position
            block = event.extra_parameters['block']
            if block.block_position == latest_block_number+1 and event.node.mine_block(block,event.time):
                # Propagate the block
                for peer_id in event.node.peers:
                    message_length = (len(block.transactions) + 1)*0.008
                    latency = event.node.get_latency(self.nodes[peer_id], message_length)
                    
                    self.add_event(Event(
                        event_time=round(event.time + latency, 4),
                        event_type=5,
                        event_node=self.nodes[peer_id],
                        block = copy.deepcopy(block),
                        event_creator = event.node
                    )) 
            
                new_block = event.node.create_block()
                self.add_event(Event(
                    event_time=round(event.time+self.gen_exp.exponential(self.iat_b/event.node.hash),4),
                    event_type=4,
                    event_node=event.node,
                    block=new_block
                ))
            # for node in list(self.nodes.values()):
            #     print(node.id,node.blockchain)

        elif event.type == 5:   # Receive block
            print(event)
            block = event.extra_parameters['block']
            event_creator_node = event.extra_parameters['event_creator']
            if event.node.receive_block(block):
                # Propagate the block
                for peer_id in event.node.peers:
                    if peer_id == event_creator_node:   # Circular dependency
                        continue

                    message_length = (len(block.transactions) + 1)*0.008
                    latency = event.node.get_latency(self.nodes[peer_id], message_length)
                    # self.logger.critical(f"{round(event.time + latency, 4)}\t\t{latency}\t\t{event.time}")
                    
                    self.add_event(Event(
                        event_time=round(event.time + latency, 4),
                        event_type=5,
                        event_node=self.nodes[peer_id],
                        block = copy.deepcopy(block),
                        event_creator = event.node
                    )) 

                new_block = event.node.create_block()
                self.add_event(Event(
                    event_time=round(event.time+self.gen_exp.exponential(self.iat_b/event.node.hash),4),
                    event_type=4,
                    event_node=event.node,
                    block=new_block
                ))
            # for node in list(self.nodes.values()):
            #     print(node.blockchain)



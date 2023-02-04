import heapq
from typing import List, Dict
import random
import numpy as np

from modules.network import Node
from utils.logger import get_logger


class Event:
    def __init__(self, event_time:float, event_type:int, event_node: Node, **kwargs):
        """Event object

        Args:
            event_time (float): simulation time
            event_type (int): 0: Not defined, 1: create txn, 2: recieve txn
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
    def __init__(self, event_queue:List[Event], nodes:Dict[int, Node], iat:float) -> None:
        self.event_queue = event_queue   # Priority list for events
        self.nodes = nodes
        self.gen_exp = np.random.default_rng()
        self.logger = get_logger("EVENT")
        self.iat = iat
    
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

        elif event.type == 3:   # reset mining
            pass

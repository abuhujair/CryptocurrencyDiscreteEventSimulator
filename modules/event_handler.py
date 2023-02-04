import heapq

from modules.network import Node


class Event:
    def __init__(self, event_time:float, event_type:int, event_node: Node):
        """Event object

        Args:
            event_time (float): simulation time
            event_type (int): 0: Not defined, 1: create txn, 2: recieve txn
            event_node (Node): Node object that creates the event
        """
        self.time = event_time
        self.type = event_type 
        self.node = event_node

    def __lt__(self,other:"Event")->bool:
        return self.time < other.time
    

class EventHandler:
    """Event handler instance of the simulator
    """
    def __init__(self) -> None:
        self.event_queue = []   # Priority list for events
    
    def add_event(self, event:Event):
        """Push new event in the event queue

        Args:
            event (Event): Event object
        """
        heapq.heappush(self.event_queue, event)
import Pyro4
import threading
import time
import random
import sys
from utils import get_node_instance, hashing

@Pyro4.expose
class ChordNode:
    def __init__(self, id, m):
        self._id = id
        self.m = m
        self.MAXPROC = pow(2, m)
                
    @property
    def id(self):
        return self._id
    
    @property
    def successor(self):
        return get_node_instance(self._ft_node[1])

    @successor.setter
    def successor(self, new_id):
        self._ft_node[1] = new_id
        self._successors_list = []

    @property
    def predecessor(self):
        return get_node_instance(self._ft_node[0])
    
    @predecessor.setter
    def predecessor(self, new_id):
        self._ft_node[0] = new_id
        self._predecessor_keys = self.predecessor.keys
    
    @property
    def ft_node(self):
        return self._ft_node

    @property
    def finger_table(self):
        return [(self._ft_start[i], self._ft_node[i]) for i in range(1, self.m + 1)]

    @property
    def keys(self):
        return self._keys

    @property
    def predecessor_keys(self):
        return self._predecessor_keys
   
    @predecessor_keys.setter
    def predecessor_keys(self, new_keys):
        self._predecessor_keys = new_keys
    
    def inrange(self, key, lwb, upb): 
        '''
        Return True if key is between lwb and upb in the 
        ring of nodes, False in other case
        '''                                        
        lwb = lwb % self.MAXPROC
        upb = upb % self.MAXPROC

        if lwb == upb:
            return True
        elif lwb < upb:                                                          
            return lwb <= key and key < upb                                     
        else:                                                                      
            return (lwb <= key and key < upb + self.MAXPROC) or (lwb <= key + self.MAXPROC and key < upb)   

    def find_successor(self, id):
        '''
        Find id's node successor
        '''
        node = self.find_predecessor(id)
        if node is None:
            return None
        return node.successor

    def find_predecessor(self, id):
        '''
        Find id's node predecessor
        '''
        node = self
        temp = self
        while not self.inrange(id, node.id + 1, node.ft_node[1] + 1):
            node = node.closest_preceding_finger(id)
            if node is None or node.id == temp.id:
                break
            temp = node
        return node

    def closest_preceding_finger(self, id):
        '''
        Return the closest node finger preceding id
        '''
        for i in range(self.m, 0, -1):
            if self.inrange(self._ft_node[i], self.id + 1, id):
                node_id = self._ft_node[i]
                return get_node_instance(node_id)
        return self

    def join(self, nodeid = None):
        '''
        Return True if the node was successfully joined to 
        the system, False in other case
        '''
        self._keys = {}
        self._predecessor_keys = {}
        self._successors_list = []

        self._ft_start = [None] * (self.m + 1)
        for i in range(1, self.m + 1):
            self._ft_start[i] = (self.id + pow(2, i-1)) % self.MAXPROC

        self._ft_node = [None] * (self.m + 1)
        # Is the first node in the ring
        if nodeid is None:
            for i in range(0, self.m + 1):
                self._ft_node[i] = self.id
            print(f'\nJoin of first node {self.id}')
        # Is not the first node in the ring
        else:    
            node = get_node_instance(nodeid)
            try:
                self.init_finger_table(node)
                self.update_others()
                print(f'\nJoin node {self.id} with {nodeid}')
            except:
                print(f'\nError: Could not join node {self.id} with {nodeid}')
                return False
        
        print_node_info(self)
        return True

    def init_finger_table(self, node):
        '''
        Initialize finger table of local node, starting
        from an arbitrary node already in the network
        '''
        self.successor = node.find_successor(self._ft_start[1]).id
        self.predecessor = self.successor.ft_node[0]

        succ_keys = self.successor.keys.keys()
        for key in succ_keys:
            if self.inrange(key, self.ft_node[0] + 1, self.id + 1):
                self.keys[key] = self.successor.pop_key(key)  
        self.successor.successor.predecessor_keys = self.successor.keys
        
        self._predecessor_keys = self.predecessor.keys

        self.successor.predecessor = self.id

        for i in range(1, self.m):
            if self.inrange(self._ft_start[i+1], self.id, self._ft_node[i]):
                self._ft_node[i+1] = self._ft_node[i]
            else:
                self._ft_node[i+1] = node.find_successor(self._ft_start[i+1]).id 
                
    def update_others(self):
        '''
        Update all nodes whose finger tables should refer to local node
        '''
        for i in range(1, self.m + 1):
            p = self.find_predecessor((self.id - pow(2, i-1)) % self.MAXPROC)
            if p is not None and p.id != self.id: 
                p.update_finger_table(self.id, i)

    def update_finger_table(self, s, i):
        '''
        If s is ith finger of local node, update local node's finger table with s
        '''
        if self.inrange(s, self.id, self._ft_node[i]):
            self._ft_node[i] = s
            p = self.predecessor
            if p is not None and p.id != s:
                p.update_finger_table(s, i)

    def stabilize(self):
        '''
        Periodically verify local node’s immediate successor,
        and tell the successor about local node
        '''
        while self.successor is None:
            if not self._successors_list:
                self.successor = self.id
                return 
            self.successor = self._successors_list.pop(0)  

        x = self.successor.predecessor
        if x is not None and self.inrange(x.id, self.id + 1, self._ft_node[1]) and ((self.id + 1) % self.MAXPROC) != self._ft_node[1]:
            self.successor = x.id
        if self.successor is not None: 
            self.successor.notify(self)

    def notify(self, node):
        '''
        Local node thinks node might be our predecesor
        '''
        if self.predecessor is None:
            for key in self._predecessor_keys.keys():
                self._keys[key] = self._predecessor_keys[key]
                if self.successor is not None:
                    self.successor.update_predecessor_key(key, self._keys[key])
    
        if self.predecessor is None or self.inrange(node.id, self._ft_node[0] + 1, self.id):
            self.predecessor = node.id

    def fix_fingers(self):
        '''
        Periodically refresh finger table entries
        '''
        i = random.randint(2, self.m)
        node = self.find_successor(self._ft_start[i])
        if node is not None:
            self._ft_node[i] = node.id

    def update_succesors_list(self):
        while True:
            new_succ = None
            if not self._successors_list:
                new_succ = self.successor
            elif len(self._successors_list) <= self.m:
                new_succ = self._successors_list[-1]
                new_succ = get_node_instance(new_succ)
            
            if new_succ is not None:
                self._successors_list.append(new_succ.id)

            time.sleep(1)

    def lookup(self, key):
        '''
        Return the node responsible for storing the key 
        '''
        while True:
            if self.inrange(key, self._ft_node[0] + 1, self.id + 1):
                return self
            else:
                for k in range(1, self.m):
                    if self.inrange(key, self._ft_start[k], self._ft_start[k + 1]): 
                        node = get_node_instance(self._ft_node[k])
                        if node is not None:       
                            return node.lookup(key)
                else:
                    node = get_node_instance(self._ft_node[self.m])
                    if node is not None:
                        return node.lookup(key)

    def update_key(self, key, value):
        '''
        Update the value of a key in local node 
        '''
        self._keys[key] = value

    def pop_key(self, key):
        '''
        Delete a key in local node and returns its value
        '''
        if key in self._keys.keys():
            value = self._keys.pop(key) 
            print(f'Key {key} was deleted in node {self.id}')
            return value
        
        print(f'Error: Could not delete key {key} in node {self.id}')
        return None 
    
    def update_predecessor_key(self, key, value):
        '''
        Update the value of a key in predecessor_keys dictionary 
        in local node
        '''
        self._predecessor_keys[key] = value
    
    def save_key(self, key, value):
        '''
        Save a key and its value in the system and return 
        True if the operation was successfully and False in
        other case
        '''
        node = self.lookup(key)
        if node is not None:
            node.update_key(key, value)
            node.successor.update_predecessor_key(key, value)
            print(f'Key {key} was saved in node {node.id}')
            return True
        
        print(f'Error: Could not save key {key} in the system')
        return False

    def get_value(self, key):
        '''
        Return the value of a key stored in the system
        '''
        node = self.lookup(key)
        if node is not None and key in node.keys.keys():
            return node.keys[key]
        
        return None        


def stabilize_function(node):
    while True:
        try:
            node.stabilize()
            node.fix_fingers()
            time.sleep(1)
        except:
            pass


def print_node_info(node):
    if node is not None:
        print(f'\nNode {node.id}')
        print(f'Predecessor: {node.ft_node[0]}')
        print(f'Successor: {node.ft_node[1]}')
        for i in node.finger_table:
            print(f'Start: {i[0]}   Node: {i[1]}')
        print(f'Keys: {list(node.keys.keys())}')
        print(f'Predecesor keys: {list(node.predecessor_keys.keys())}')


def print_node_function(node) :
    while True:
        print_node_info(node)
        time.sleep(30)  


def main(address, bits, node_address = None):
    id = hashing(bits, address)
    node = ChordNode(id, bits)
    
    host_ip, host_port = address.split(':')
    daemon = Pyro4.Daemon(host=host_ip, port=int(host_port))
    uri = daemon.register(node)
    ns = Pyro4.locateNS()
    ns.register(f'CHORD{id}', uri)

    request_thread = threading.Thread(target=daemon.requestLoop)
    request_thread.start()

    if node_address is None:
        node.join()
    else:
        node_id = hashing(bits, node_address)
        node.join(node_id)

    stabilize_thread = threading.Thread(target=stabilize_function, args=[node])
    stabilize_thread.start()

    print_tables_thread = threading.Thread(target=print_node_function, args=[node])
    print_tables_thread.start()

    print_tables_thread = threading.Thread(target=node.update_succesors_list, args=[])
    print_tables_thread.start()


if __name__ == '__main__':
    if len(sys.argv) == 3:
        main(address=sys.argv[1], bits=int(sys.argv[2]))
    elif len(sys.argv) == 4:
        main(address=sys.argv[1], bits=int(sys.argv[3]), node_address=sys.argv[2])
    else:
        print('Error: Missing arguments')
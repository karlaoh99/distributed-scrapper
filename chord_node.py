import Pyro4
import Pyro4.errors
import threading
import time
import random


@Pyro4.expose
class Node:
    def __init__(self, id, m):
        self._id = id
        self.m = m
        self.MAXPROC = pow(2, m)
        
    @property
    def id(self):
        return self._id
    
    @property
    def successor(self):
        return get_node_instance(self.ft_node[1])

    @successor.setter
    def successor(self, new_id):
        self.ft_node[1] = new_id
        self.successor_list = []

    @property
    def predecessor(self):
        return get_node_instance(self.ft_node[0])
    
    @predecessor.setter
    def predecessor(self, new_id):
        self.ft_node[0] = new_id
        self._predecessor_keys = self.predecessor.keys
    
    @property
    def finger_table(self):
        return [(self.ft_start[i], self.ft_node[i]) for i in range(1, self.m + 1)]

    @property
    def fingers(self):
        return self.ft_node

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
        lwb = lwb % self.MAXPROC
        upb = upb % self.MAXPROC
        if(key is None):
            print(self.ft_node)
            print(self.id)
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
        while not self.inrange(id, node.id + 1, node.fingers[1] + 1):
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
            if self.inrange(self.ft_node[i], self.id + 1, id):
                node_id = self.ft_node[i]
                return get_node_instance(node_id)
        return self

    def join(self, nodeid):
        '''
        Return true if the node was succesfully joined to 
        the system, false in other case
        '''
        print(nodeid)
        self._keys = {}
        self._predecessor_keys = {}
        self.successor_list = []

        self.ft_start = [None] * (self.m + 1)
        for i in range(1, self.m + 1):
            self.ft_start[i] = (self.id + pow(2, i-1)) % self.MAXPROC

        self.ft_node = [None] * (self.m + 1)
        if nodeid is None:  # first node in the system
            for i in range(0, self.m + 1):
                self.ft_node[i] = self.id
            print(f'\nJoin of first node {self.id}')
        else:  # is not the first node in the system  
            node = get_node_instance(nodeid)
            # try:
            self.init_finger_table(node)
            self.update_others()
            print(f'\nJoin node {self.id} with {nodeid}')
            # except:
            #     return False
        
        print_finger_table(self)
        return True

    def init_finger_table(self, node):
        '''
        Initialize finger table of local node, starting
        from an arbitrary node already in the network
        '''
        self.successor = node.find_successor(self.ft_start[1]).id
        self.predecessor = self.successor.fingers[0]

        keys_ = self.successor.keys.keys()
        for key in keys_:
            if self.inrange(key, self.fingers[0] + 1, self.id + 1):
                self.keys[key] = self.successor.pop_key(key)  
        self.successor.successor.predecessor_keys = self.successor.keys
        
        self._predecessor_keys = self.predecessor.keys

        self.successor.predecessor = self.id

        for i in range(1, self.m):
            if self.inrange(self.ft_start[i+1], self.id, self.ft_node[i]):
                self.ft_node[i+1] = self.ft_node[i]
            else:
                self.ft_node[i+1] = node.find_successor(self.ft_start[i+1]).id 
                
    def update_others(self):
        '''
        Update all nodes whose finger tables should refer to self
        '''
        for i in range(1, self.m + 1):
            p = self.find_predecessor((self.id - pow(2, i-1)) % self.MAXPROC)
            if p is not None and p.id != self.id: 
                p.update_finger_table(self.id, i)

    def update_finger_table(self, s, i):
        '''
        If s is ith finger of n, update self's finger table with s
        '''
        if self.inrange(s, self.id, self.ft_node[i]):
            self.ft_node[i] = s
            p = self.predecessor
            if p is not None and p.id != s:
                p.update_finger_table(s, i)

    def stabilize(self):
        '''
        Periodically verify n’s immediate successor,
        and tell the successor about n
        '''
        while self.successor is None:
            if not self.successor_list:
                self.successor = self.id
                return 
            self.successor = self.successor_list.pop(0)  

        x = self.successor.predecessor
        if x is not None and self.inrange(x.id, self.id + 1, self.ft_node[1]) and ((self.id + 1) % self.MAXPROC) != self.ft_node[1]:
            self.successor = x.id
        if self.successor is not None: 
            self.successor.notify(self)

    def notify(self, node):
        '''
        Self thinks node might be our predecesor
        '''
        if self.predecessor is None or self.inrange(node.id, self.ft_node[0] + 1, self.id):
            if self.predecessor is None:
                for key in self._predecessor_keys.keys():
                    self._keys[key] = self._predecessor_keys[key]
                    if self.successor is not None:
                        self.successor.update_key_in_succe(key, self._keys[key])
            self.predecessor = node.id

    def fix_fingers(self):
        '''
        Periodically refresh finger table entries
        '''
        i = random.randint(2, self.m)
        succ = self.find_successor(self.ft_start[i])
        if succ is not None:
            self.ft_node[i] = succ.id

    def update_succesor_list(self):
        new_succ = None
        if not self.successor_list:
            new_succ = self.successor
        elif len(self.successor_list) <= self.m:
            new_succ = self.successor_list[-1]
            new_succ = get_node_instance(new_succ)
        
        if new_succ is not None:
            self.successor_list.append(new_succ.id)

    def lookup(self, key):
        while True:
            if self.inrange(key, self.ft_node[0] + 1, self.id + 1):
                return self
            else:
                for k in range(1, self.m):
                    if self.inrange(key, self.ft_start[k], self.ft_start[k + 1]): 
                        node = get_node_instance(self.ft_node[k])
                        if node is not None:       
                            return node.lookup(key)
                else:
                    node = get_node_instance(self.ft_node[self.m])
                    if node is not None:
                        return node.lookup(key)

    def update_key(self, key, content):
        self._keys[key] = content

    def pop_key(self, key):
        return self._keys.pop(key)
    
    def update_key_in_succe(self, key, content):
        self._predecessor_keys[key] = content
    
    def save_key(self, key, value):
        '''
        Save a key and a value in the system 
        '''
        node = self.lookup(key)
        if node is not None:
            node.update_key(key, value)
            node.successor.update_key_in_succe(key, value)
            print(node.id)

    def get_value(self, key):
        '''
        Return the value of a key
        '''
        node = self.lookup(key)
        if node is not None and key in node.keys.keys():
            return node.keys[key]
        return None        


def get_node_instance(id):
    with Pyro4.Proxy(f'PYRONAME:{str(id)}') as p:
        try:
            p._pyroBind()
            return p
        except Pyro4.errors.CommunicationError:
            return None


def stabilize_function(node):
    while True:
        try:
            node.stabilize()
            node.fix_fingers()
            time.sleep(1)
        except:
            pass


def print_finger_table(node):
    if node is not None:
        print(f'Node {node.id}')
        print(f'Predecessor: {node.fingers[0]}')
        print(f'Successor: {node.fingers[1]}')
        for i in node.finger_table:
            print(f'Start: {i[0]}   Node: {i[1]}')
        print(node.keys)
        print(node.predecessor_keys)


def print_nodes(server_nodes) :
    while True:
        nodes_id = server_nodes.get_members()
        print(nodes_id)
        print('\nFinger Tables')
        for id in nodes_id:
            node = get_node_instance(id)
            print_finger_table(node)
        time.sleep(30)  


def main():
    server_nodes = get_node_instance('SERVERNODES')
    init_node_id = server_nodes.get_random_node()
    new_id = server_nodes.get_disponible_id()

    node = Node(new_id, server_nodes.m)
    daemon = Pyro4.Daemon()
    uri = daemon.register(node)
    ns = Pyro4.locateNS()
    ns.register(str(new_id), uri)

    request_thread = threading.Thread(target=daemon.requestLoop)
    request_thread.start()

    node.join(init_node_id)

    stabilize_thread = threading.Thread(target=stabilize_function, args=[node])
    stabilize_thread.start()

    print_tables_thread = threading.Thread(target=print_nodes, args=[server_nodes])
    print_tables_thread.start()


if __name__ == '__main__':
    main()
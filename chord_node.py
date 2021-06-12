import Pyro4
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
        
        if lwb == upb:
            return True
        elif lwb < upb:                                                          
            return lwb <= key and key < upb                                     
        else:                                                                      
            return (lwb <= key and key < upb + self.MAXPROC) or (lwb <= key + self.MAXPROC and key < upb)   

    # ask node n to find id's node successor
    def find_successor(self, id):
        node = self.find_predecessor(id)
        return node.successor

    # ask node n to find id's node predecessor
    def find_predecessor(self, id):
        node = self
        temp = self
        while not self.inrange(id, node.id + 1, node.successor.id + 1):
            node = node.closest_preceding_finger(id)
            if node.id == temp.id:
                break
            else: 
                temp = node
        return node

    # return the closest node finger preceding id
    def closest_preceding_finger(self, id):
        for i in range(self.m, 0, -1):
            if self.inrange(self.ft_node[i], self.id + 1, id):
                node_id = self.ft_node[i]
                return get_node_instance(node_id)
        return self

    def join(self, nodeid):
        self._keys = {}
        self._predecessor_keys = {}

        self.ft_start = [None] * (self.m + 1)
        for i in range(1, self.m + 1):
            self.ft_start[i] = (self.id + pow(2, i-1)) % self.MAXPROC

        self.ft_node = [None] * (self.m + 1)
        if nodeid is None:
            for i in range(1, self.m + 1):
                self.ft_node[i] = self.id
            self.predecessor = self.id
            print(f'\nJoin of first node {self.id}')
        else:
            node = get_node_instance(nodeid)
            self.init_finger_table(node)
            self.update_others()
            print(f'\nJoin node {self.id} with {nodeid}')
        
        print_finger_table(self)

    # periodically verify n’s immediate successor,
    # and tell the successor about n.
    def stabilize(self):
        x = self.successor.predecessor
        if self.inrange(x.id, self.id + 1, self.successor.id) and ((self.id + 1) % self.MAXPROC) != self.successor.id:
            self.successor = x.id
        self.successor.notify(self)

    # n' thinks it might be our predecesor
    def notify(self, node):
        if self.predecessor is None or self.inrange(node.id, self.predecessor.id + 1, self.id):
            self.predecessor = node.id

    # periodically refresh finger table entries.
    def fix_fingers(self):
        i = random.randint(2, self.m)
        self.ft_node[i] = self.find_successor(self.ft_start[i]).id

    # initialize finger table of local node, starting
    # from an arbitrary node already in the network
    def init_finger_table(self, node):
        self.successor = node.find_successor(self.ft_start[1]).id
        self.predecessor = self.successor.predecessor.id

        keys_ = self.successor.keys.keys()
        print(keys_)
        for key in keys_:
            if self.inrange(key,self.predecessor.id + 1,self.id + 1):
                self.keys[key] = self.successor.pop_key(key)  
        print("keys successor")             
        print(self.successor.keys)
        self.successor.successor.predecessor_keys = self.successor.keys

        self.successor.predecessor = self.id

        for i in range(1, self.m):
            if self.inrange(self.ft_start[i+1], self.id, self.ft_node[i]):
                self.ft_node[i+1] = self.ft_node[i]
            else:
                self.ft_node[i+1] = node.find_successor(self.ft_start[i+1]).id 
                
    # update all nodes whose finger tables should refer to n
    def update_others(self):
        for i in range(1, self.m + 1):
            p = self.find_predecessor((self.id - pow(2, i-1)) % self.MAXPROC)
            if p.id != self.id: ####
                p.update_finger_table(self.id, i)

    # if s is ith finger of n, update n's finger table with s
    def update_finger_table(self, s, i):
        if self.inrange(s, self.id, self.ft_node[i]):
            self.ft_node[i] = s
            p = self.predecessor
            if p.id != s: ####
                p.update_finger_table(s, i)

    def lookup(self, key):
        if self.inrange(key, self.predecessor.id + 1 , self.id + 1):
            return self
        else:
            for k in range(1, self.m):
                if self.inrange(key, self.ft_start[k], self.ft_start[k + 1]): 
                    node = get_node_instance(self.ft_node[k])       
                    return node.lookup(key)
            else:
                node = get_node_instance(self.ft_node[self.m])
                return node.lookup(key)

    def update_key(self, key, content):
        self._keys[key] = content

    def pop_key(self, key):
        return self._keys.pop(key)
    
    def update_key_in_succe(self, key, content):
        self._predecessor_keys[key] = content
    
    def save_key(self, key, content):
        node = self.lookup(key)
        node.update_key(key, content)
        node.successor.update_key_in_succe(key, content)

    def get_content(self, key):
        node = self.lookup(key)
        if key in node.keys.keys:
            return node.keys[key]
        return None        


def get_node_instance(id):
    return Pyro4.Proxy(f'PYRONAME:{str(id)}')


def stabilize_function(node):
    while True:
        node.stabilize()
        node.fix_fingers()
        time.sleep(1)


def print_finger_table(node):
    print(f'Node {node.id}')
    print(f'Predecessor: {node.predecessor.id}')
    print(f'Successor: {node.successor.id}')
    for i in node.finger_table:
        print(f'Start: {i[0]}   Node: {i[1]}')
    print(node.keys)
    print(node.predecessor_keys)

def print_nodes(server_nodes) :
    while True:
        nodes_id = server_nodes.get_members()
        print('\nFinger Tables')
        for id in nodes_id:
            node = get_node_instance(id)
            print_finger_table(node)
        time.sleep(80)  


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
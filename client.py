from server_nodes import *
import Pyro4 
from chord_node import get_node_instance


if __name__ == '__main__':
    keys = {4,6,7}
    search ={ 1,6,7,0}
    server_nodes = get_node_instance('SERVERNODES')
    id_ = server_nodes.get_random_node()
    print(id_)
    node = get_node_instance(id_)
    print(node.id)
    for k in keys:
        node.save_key(k,"lala")
    print("hhhhh")
    for k in search:
        n = node.lookup(k)
        print(f'Id : {n.id}')




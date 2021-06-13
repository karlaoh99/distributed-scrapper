import Pyro4
import random
import sys

@Pyro4.expose
class NodesList:
    def __init__(self, m):
        self._m = m
        self.MAXPROC = pow(2, m)
        self.members = []

    @property
    def m(self):
        return self._m

    def get_disponible_id(self):
        #new_id = random.choice(list(set([i for i in range(self.MAXPROC)]) - set(self.members)))
        if 2 not in self.members:
            new_id = 2
        elif 6 not in self.members:
            new_id = 6
        elif 3 not in self.members:
            new_id = 3
        elif 5 not in self.members:
            new_id = 5
        self.members.append(new_id)
        print(self.members)  
        return new_id

    def get_random_node(self):
        if len(self.members) == 0:
            return None
        # return random.choice(self.members)
        return 2

    def get_members(self):
        return self.members


def main():
    if len(sys.argv) == 2:
        m =  sys.argv[1]
        nodes_list = NodesList(int(m))
        daemon = Pyro4.Daemon()
        uri = daemon.register(nodes_list)    
        ns = Pyro4.locateNS()
        ns.register('SERVERNODES', uri)
        daemon.requestLoop()


if __name__ == '__main__':
    main()
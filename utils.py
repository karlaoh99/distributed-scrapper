import Pyro4
import Pyro4.errors
import hashlib

def get_node_instance(id):
    return get_proxy(f'CHORD{id}')


def get_scrapper_instance(id):
    return get_proxy(f'SCRAPPER{id}')


def get_proxy(id):
    Pyro4.Proxy(f'PYRONAME:{id}')
    with Pyro4.Proxy(f'PYRONAME:{id}') as p:
        try:
            p._pyroBind()
            return p
        except Pyro4.errors.CommunicationError:
            return None


def hashing(bits, string):
    hash = hashlib.sha256(string.encode()).hexdigest()
    hash = int(hash, 16) % pow(2, bits)
    return hash
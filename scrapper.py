import sys
import Pyro4
import threading
import time
import requests
from bs4 import BeautifulSoup
from random import randint
from utils import get_node_instance, get_scrapper_instance, hashing


@Pyro4.expose
class ScrapperNode:
    def __init__(self,address, chord_address, m):
        self.address = address
        self.chord_id = hashing(m, chord_address)
        self.chord_successors_list = []
        self.m = m
 
    @property
    def scrappers_list(self):
        return self._scrappers_list 
    
    def change_chord_node(self):
        for id in self.chord_successors_list:
            node = get_node_instance(id)
            if node is not None:
                self.chord_id = id
                return node
        return None             

    def add_scrapper(self, address):
        if address not in self._scrappers_list:
            self._scrappers_list.append(address)

    def join(self, scrapper_address):
        self._scrappers_list = [self.address]
        if scrapper_address is not None:
            node = get_scrapper_instance(scrapper_address)
            if node is not None:
                try:
                    list = node.scrappers_list
                    for addr in list:
                        if addr == self.address:
                            continue
                        self._scrappers_list.append(addr)
                        node = get_scrapper_instance(addr)
                        if node is not None:
                            node.add_scrapper(self.address)
                except:
                    return False
            else:
                return False
        
        return True

    def choose_scrapper_node(self):
        i = randint(0, len(self._scrappers_list) - 1)
        return self._scrappers_list[i]
     
    def get_html(self, url, d):
        htmls = []
        
        while True:
            chord_node = get_node_instance(self.chord_id)
            if chord_node is None:
                chord_node = self.change_chord_node()
            
            try:
                hash = hashing(self.m, url)
                if hash is None:
                    print(f'Error: Could not load the html of {url}, verify that it is correct and you have internet connection')
                    return htmls
                
                html = chord_node.get_value(hash, url)
                if html is None:
                    html = self.load_html(url)
                    if html is not None:
                        chord_node.save_key(hash, (url, html))
                    else:
                        print(f'Error: Could not load the html of {url}, verify that it is correct and you have internet connection')
                        return htmls
                
                htmls.append(html) 
                d -= 1               
                
                if d < 0:
                    return htmls

                html_urls = self.parse_html(html)
                for url in html_urls:
                    scrapper_addr = self.choose_scrapper_node()
                    if scrapper_addr != self.address:  
                        node = get_scrapper_instance(scrapper_addr)
                        try:
                            htmls.extend(node.get_html(url, d))
                        except:
                            htmls.extend(self.get_html(url, d))
                    else:
                        htmls.extend(self.get_html(url, d))
                
                return htmls

            except:
                if not self.chord_successors_list:
                    print(f'Error: Could not connect with chord node {self.chord_id}')
                    break
            
        return  htmls

    def load_html(self, url):
        try:
            response = requests.get(url)
            if response: 
                return response.text
        except:
            pass
        return None
    
    def parse_html(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        urls = []
        for link in soup.find_all('a'):
            url = link.get('href')
            if url is not None and url[0] != '#' and url[0] != '/':
                urls.append(url)
        return urls

    def update_chord_successors_list(self):
        while True:
            node = get_node_instance(self.chord_id)
            if node is not None:
                try:
                    self.chord_successors_list = node.successors_list
                except:
                    pass
            time.sleep(1)  

    def update_scrappers_list(self):
        while True:
            list = self._scrappers_list
            for addr in list:
                node = get_scrapper_instance(addr)
                if node is None:
                    self._scrappers_list.remove(addr)
            time.sleep(1) 

    def print_node_info(self):
        while True:
            print(f'\nAddress: {self.address}')
            print(f'Chord node: {self.chord_id}')
            print(f'Chord node successors list: {self.chord_successors_list}')
            print(f'Scrappers list: {self.scrappers_list}')
            time.sleep(10)   


def main(address, scrapper_address, chord_address, bits):
    host_ip, host_port = address.split(':')
    try:
        daemon = Pyro4.Daemon(host=host_ip, port=int(host_port))
    except:
        print('Error: There is another node in the system with that address, please try another')
        return
    
    node = ScrapperNode(address, chord_address, bits)
    uri = daemon.register(node)
    ns = Pyro4.locateNS()
    ns.register(f'SCRAPPER{address}', uri)
    
    if node.join(scrapper_address):
        request_thread = threading.Thread(target=daemon.requestLoop)
        request_thread.start()
        
        chord_sucessor_list_thread = threading.Thread(target=node.update_chord_successors_list)
        chord_sucessor_list_thread.start()
        
        scrappers_list_thread = threading.Thread(target=node.update_scrappers_list)
        scrappers_list_thread.start()
        
        print_thread = threading.Thread(target = node.print_node_info)
        print_thread.start()
    
    else:
        print(f'Error: Could not connect to the network, no scrapper with address: {scrapper_address}')


if __name__ == '__main__':
    if len(sys.argv) == 4:
        main(sys.argv[1], None, sys.argv[2], int(sys.argv[3]))
    elif len(sys.argv) == 5:
        main(sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])) 
    else:
        print('Error: Missing arguments')
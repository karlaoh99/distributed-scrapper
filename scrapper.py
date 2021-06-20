from hashlib import new
from platform import node
import time
import sys
import Pyro4
import threading
import requests
from bs4 import BeautifulSoup
from random import randint, random
from utils import get_node_instance, get_scrapper_instance,hashing


@Pyro4.expose
class ScrapperNode:
    def __init__(self,address, chord_address,scrapper_address, m):
        self.id = address
        self.scrapper_address = scrapper_address
        self.chord_id = hashing(m, chord_address)
        self.m = m
        self.chord_succlist = []
        self._scrapperslist = []
        
    
 
    @property
    def scrappers_list(self):
        return self._scrapperslist 
        
    @scrappers_list.setter
    def scrappers_list(self,list):
        self._scrapperslist  = list    

    def get_chord_successor_list(self):
        while True:
            node = get_node_instance(self.chord_id)
            if node is not None:
                try:
                    list_ = node.successors_list
                    self.chord_succlist = list_ 
                except:
                    pass
            time.sleep(1)    
    
    def change_chord_node(self):
        for  id_ in self.chord_succlist:
            node = get_node_instance(id_)
            if node is not None:
                self.chord_id = node.id
        return node            

    def get_scrappers_list(self):
        if self.scrapper_address is None:
            node = self
            self._scrapperslist.append(self.id)
            return True
        else:
            node = get_scrapper_instance(self.scrapper_address)
            try:
                print(node)
                self._scrapperslist = node.scrappers_list
                self._scrapperslist.append(self.id)
                list = self._scrapperslist
                for item in list:
                    if item != self.id:
                        node = get_scrapper_instance(item)
                        try:
                            node.scrappers_list = self.scrappers_list
                        except:
                            self._scrapperslist.remove(item)
                return True
            except:
                return False 

    def update_scrappers_list(self):
        while True:
            list = self._scrapperslist
            for add in list:
                if add != self.id:
                    node = get_scrapper_instance(add)
                    if node is None:
                        self._scrapperslist.remove(add)
            time.sleep(1)        

    def choose_scrapper_node(self):
        i = randint(0,len(self._scrapperslist)-1)
        return self._scrapperslist[i]
     
    def get_html(self, url, d):
        htmls = []
        hash = hashing(self.m, url) 
        bool_ = True
        while bool_ and d >= 0:
            try:
                chord_node = get_node_instance(self.chord_id)
                if chord_node is None:
                    chord_node = self.change_chord_node()
                html = chord_node.get_value(hash,url)
                if html is None:
                    html = self.load_html(url)
                    if html is not None:
                        chord_node.save_key(hash,(url, html))
                    else:
                        print(f'Error: Could not load the html of {url}')
                        break 
                html_urls = self.parse_html(html)
                htmls.append(html)
                d-=1
                if d < 0:
                    break
                else :
                    for u in html_urls:
                        d_= d
                        node_scrapper_id = self.choose_scrapper_node()
                        if node_scrapper_id != self.id:  
                            node_scrapper=  get_scrapper_instance(node_scrapper_id)
                            try:
                                aux  = node_scrapper.get_html(u,d_)
                                htmls.extend(aux)
                            except:
                                aux = self.get_html(u,d_)
                                htmls.extend(aux) 
                        else:
                            aux = self.get_html(u,d_)
                            htmls.extend(aux)
                    d-=1     
                    
            except:
                if not self.chord_succlist:
                    bool_ = False                          
                    print(f'Error: Could not connect with chord node {self.chord_id}')
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
            if url is not None and url != '#':
                urls.append(url)
        return urls

    def print_node_info(self):
        print("entro")
        print(f'\nNode {self.id}')
        print(f'\nChord node {self.chord_id}')
        print(f'\nChord nodes list {self.chord_succlist}')
        print(f'\nscrapper nodes list {self._scrapperslist}')
            

    def print_node_function(self) :
        while True:
            self.print_node_info()
            time.sleep(30)  



def main(address, chord_address, bits, scrapper_address = None):
    node = ScrapperNode(address ,chord_address, scrapper_address,bits)

    host_ip, host_port = address.split(':')
   
    daemon = Pyro4.Daemon(host=host_ip, port=int(host_port))
    uri = daemon.register(node)
    ns = Pyro4.locateNS()
    ns.register(f'SCRAPPER{address}', uri)
    request_thread = threading.Thread(target=daemon.requestLoop)
    request_thread.start()
    
    if node.get_scrappers_list():
        chord_sucessor_list_thread = threading.Thread(target=node.get_chord_successor_list)
        chord_sucessor_list_thread.start()
       
        scrappers_list_thread = threading.Thread(target=node.update_scrappers_list)
        scrappers_list_thread.start()
        
        print_thread = threading.Thread(target = node.print_node_function )
        print_thread.start()
    else:
        print(f'Error : It was not possible to connect to the network because the node with ip and port {scrapper_address} does not exist')

if __name__ == '__main__':
    if len(sys.argv) == 5:
        main(sys.argv[1], sys.argv[3], int(sys.argv[4]),sys.argv[2]) 
    elif len(sys.argv)== 4:
        main(sys.argv[1], sys.argv[2], int(sys.argv[3]))
    elif len(sys.argv) < 4:
        print('Error: Missing arguments, you must enter the scrapper node address, the chord node address and the number of bits')
    else:
        print('Error: Too many arguments, you must enter only the scrapper node address, the chord node address and the number of bits')
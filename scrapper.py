import sys
import Pyro4
import threading
import time
import requests
from bs4 import BeautifulSoup
from utils import get_node_instance, hashing


@Pyro4.expose
class ScrapperNode:
    def __init__(self, chord_address, m):
        self.m = m
        self.chord_id = hashing(m, chord_address)
        self.chord_successors_list = []
    
    def get_chord_successor_list(self):
        while True:
            node = get_node_instance(self.chord_id)
            if node is not None:
                try:
                    self.chord_successors_list = node.successors_list
                except:
                    pass
            time.sleep(1)

    def change_chord_node(self):
        for id in self.chord_successors_list:
            node = get_node_instance(id)
            if node is not None:
                self.chord_id = node.id
                return node
        return None            

    def get_html(self, url, d):
        chord_node = get_node_instance(self.chord_id)
        if chord_node is None:
            chord_node = self.change_chord_node()
            
        if chord_node is not None:
            htmls = []
            urls = [url]
            while d >= 0 and urls:
                temp_urls = []
                count = 0
                while count < len(urls):
                    url = urls[count]
                    hash = hashing(self.m, url)
                    try:
                        html = chord_node.get_value(hash, url)
                        if html is None:
                            html = self.load_html(url)
                            if html is not None:
                                chord_node.save_key(hash, (url, html))
                            else:
                                print(f'Error: Could not load the html of {url}')
                                count += 1
                                continue     
                        html_urls = self.parse_html(html)
                        htmls.append(html)
                        temp_urls.extend(html_urls)
                        count += 1
                    except:
                        chord_node = self.change_chord_node() 
                        if chord_node is None:
                            break

                d -= 1
                urls = temp_urls
            return htmls
            
        else:
            print(f'Error: Could not connect with chord node {self.chord_id}')
            return None

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


def main(address, chord_address, bits):
    node = ScrapperNode(chord_address, bits)

    host_ip, host_port = address.split(':')
    daemon = Pyro4.Daemon(host=host_ip, port=int(host_port))
    uri = daemon.register(node)
    ns = Pyro4.locateNS()
    ns.register(f'SCRAPPER{address}', uri)

    request_thread = threading.Thread(target=daemon.requestLoop)
    request_thread.start()
    chord_sucessor_list_thread = threading.Thread(target=node.get_chord_successor_list)
    chord_sucessor_list_thread.start()


if __name__ == '__main__':
    if len(sys.argv) == 4:
        main(sys.argv[1], sys.argv[2], int(sys.argv[3]))
    elif len(sys.argv) < 4:
        print('Error: Missing arguments, you must enter the scrapper node address, the chord node address and the number of bits')
    else:
        print('Error: Too many arguments, you must enter only the scrapper node address, the chord node address and the number of bits')
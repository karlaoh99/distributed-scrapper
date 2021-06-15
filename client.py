import sys
import os
from shutil import rmtree
from utils import get_scrapper_instance


def main(address, depth):
    scrapper = get_scrapper_instance(address)
    
    path = 'urls/urls.txt'
    fd = open(path,'r')
    initial_urls = fd.readlines()
    count_url = 0
    for url in initial_urls:
        url = url.rstrip()
        htmls = scrapper.get_html(url, depth)
        if htmls:
            count = 0
            if os.path.exists(f'url{count_url}'):
                rmtree(f'url{count_url}')
            os.makedirs(os.path.abspath(f'url{count_url}'))
            for html in htmls:
                f = open(f'url{count_url}/url{count}.html', 'w+')
                f.write(html)
                f.close()
                count += 1
        count_url += 1        
    fd.close()


if __name__ == '__main__':
    if len(sys.argv) == 3:
        main(sys.argv[1], int(sys.argv[2]))
    else:
        print('Error: Missing arguments')
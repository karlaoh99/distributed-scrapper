import sys
import os
from shutil import rmtree
from utils import get_scrapper_instance


def main(scrapper_address):
    path = 'urls/urls.txt'
    if not os.path.exists(path):
        print(f'Error: No such file or directory: {path}')
        return
        
    scrapper = get_scrapper_instance(scrapper_address)
    if not scrapper:
        print(f'Error: Could not connect to scrapper with address: {scrapper_address}')
        return

    fd = open(path, 'r')
    urls = fd.readlines()
    fd.close()
    count_url = 0

    for url in urls:
        url, depth = url.split(' ')
        try:
            count = 0
            htmls = scrapper.get_html(url, depth)
            
            if os.path.exists(f'url{count_url}'):
                rmtree(f'url{count_url}')
            os.makedirs(os.path.abspath(f'url{count_url}'))
            
            for html in htmls:
                fd = open(f'url{count_url}/url{count}.html', 'w+')
                fd.write(html)
                fd.close()
                count += 1
        except:
            print(f'Error: There was an error getting the html of the url {url}')

        count_url += 1     


if __name__ == '__main__':
    if len(sys.argv) == 2:
        main(sys.argv[1])
    elif len(sys.argv) < 2:
        print('Error: Missing arguments, you must enter the scrapper node address')
    else:
        print('Error: Too many arguments, you must enter only the scrapper node address')
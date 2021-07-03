import sys
import os
from shutil import rmtree
from utils import get_scrapper_instance


def main(scrapper_address):
    count_url = 0
    while True:    
        url = input('\nType the url and its depth, both separated by space and press enter:\n')
        
        scrapper = get_scrapper_instance(scrapper_address)
        if not scrapper:
            print(f'Error: Could not connect to scrapper with address: {scrapper_address}')
            return

        while os.path.exists(f'url{count_url}'):
            count_url += 1
        os.makedirs(os.path.abspath(f'url{count_url}'))
        
        try:
            url, depth = url.split(' ')
            depth = int(depth)
        except:
            print('Error: You entered the url and depth wrong')
            continue

        try:
            count = 0
            htmls = scrapper.get_html(url, depth)

            if len(htmls) == 0:
                print(f'Error: There was an error getting the htmls of the url {url}')
                continue

            for html in htmls:
                fd = open(f'url{count_url}/url{count}.html', 'w+')
                fd.write(html)
                fd.close()
                count += 1
        except:
            print(f'Error: There was an error getting the htmls of the url {url}')

        count_url += 1     


if __name__ == '__main__':
    if len(sys.argv) == 2:
        main(sys.argv[1])
    elif len(sys.argv) < 2:
        print('Error: Missing arguments, you must enter the scrapper node address')
    else:
        print('Error: Too many arguments, you must enter only the scrapper node address')
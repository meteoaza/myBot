from bs4 import BeautifulSoup
import requests


URL = 'http://anekdotov.net/anekdot/'
url = requests.get(URL)
html = (url.text)


def main():
    soap = BeautifulSoup(html, 'lxml')

    div = soap.find('table', class_= 'maintbl')
    a = div.find_all('a')
    print(a)




if __name__ == '__main__':
    main()
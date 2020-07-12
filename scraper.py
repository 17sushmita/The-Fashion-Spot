import requests 
from bs4 import BeautifulSoup 
  
URL = "https://www.myntra.com/women-shirts-tops-tees?f=Categories%3ATops"
r = requests.get(URL) 
print(r.content)  
'''
soup = BeautifulSoup(r.content, 'html5lib') 
print(soup.prettify())
'''
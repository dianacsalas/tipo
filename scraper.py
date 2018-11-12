#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

page = requests.get("http://books.toscrape.com/index.html")
soup = BeautifulSoup(page.content, 'html.parser')

url_l=[]
text_l=[]
for link in soup.find_all('a'):
    href=link.get('href')
    text=link.get_text()
    url_l.append(href)
    text_l.append(text)

M = range(0,len(text_l))

for m in M:
    text_l[m] = re.sub('\n|\r','', text_l[m])
    text_l[m] = re.sub('\s\s+','', text_l[m])
list(text_l)

catalog = pd.DataFrame({'category': text_l,'url': url_l})
catalog['classif'] = catalog.url.apply(lambda x: x[:24])
catalog = catalog[catalog.classif == 'catalogue/category/books']
catalog = catalog[catalog.category != 'Books']
catalog = catalog.drop('classif', 1)
catalog.index -=3

P = range(0,len(catalog.category))
url_prev = 'http://books.toscrape.com/'

n_elements = []
for p in P:
    page = requests.get(url_prev+catalog.url[p])
    soup = BeautifulSoup(page.content, 'html.parser')
    n_elements.append(soup.find('form',class_='form-horizontal').select("strong")[0].text)

catalog['n_elements'] = n_elements

url_prev = 'http://books.toscrape.com/'
C = range(0,len(catalog.category))
prices_catalog = pd.DataFrame(columns=['book','price','category'])

for c in C:
    category_act = catalog.category[c]
    text_url = url_prev+catalog.url[c]

    page = requests.get(text_url)
    soup = BeautifulSoup(page.content, 'html.parser')
    np = soup.find_all('li',class_='current')
    
    if not np:
        num_of_pages = 1
    else:
        num_of_pages = int(re.sub('\s\s+','',np[0].get_text())[-1:])

    book_list_final = pd.DataFrame(columns=['book','price'])
    F = range(1,num_of_pages+1)

    for f in F:
        if num_of_pages > 1:
            text_url_aux = re.sub('index','page-'+str(f),text_url)
        else:
            text_url_aux = text_url
            
        page_aux = requests.get(text_url_aux)
        soup_aux = BeautifulSoup(page_aux.content, 'html.parser')
    
        books_l=[]

        for link in soup_aux.find_all('article', {'class': 'product_pod'}):
            for link2 in link.find_all('a'):
                title = link2.get('title')
                if title:
                    books_l.append(title)
        
        book_list = pd.DataFrame({'book': books_l})
    
        G = range(0,len(catalog.category))
        for g in G:
            book_list = book_list[book_list.book != catalog.category[g]]
     
        prices_l = []
        prices_l = [sd.get_text() for sd in soup_aux.find_all('p',class_='price_color')]
        book_list['price']=prices_l
        book_list['price'].replace(regex=True,inplace=True,to_replace=r'£',value=r'')
    
        if f == 1:
            book_list_final = book_list
        else:
            book_list_final = pd.DataFrame.append(book_list_final,book_list)

    book_list_final['category'] = category_act
    
    if c == 0:
        prices_catalog = book_list_final
    else:
        prices_catalog = pd.DataFrame.append(prices_catalog,book_list_final)
        
prices_catalog.price = prices_catalog.price.astype(float).fillna(0.0)
grouped_df = prices_catalog['price'].groupby(prices_catalog['category'])

prices_catalog_min = pd.DataFrame(grouped_df.min().reset_index(name = 'min_price'))
prices_catalog_max = pd.DataFrame(grouped_df.max().reset_index(name = 'max_price'))
prices_catalog_mean = pd.DataFrame(grouped_df.mean().reset_index(name = 'mean_price'))

catalog = pd.merge(catalog, prices_catalog_min, how='left', on=['category'])
catalog = pd.merge(catalog, prices_catalog_max, how='left', on=['category'])
catalog = pd.merge(catalog, prices_catalog_mean, how='left', on=['category'])

catalog.to_csv('catalogData.csv', index=False, header=True)
prices_catalog.to_csv('catalogPrices.csv', index=False, header=True)


import pandas as pd
import numpy as np
import sqlite3
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
def content_based_filtering(product_id):
    con = sqlite3.connect("shop/test.db")
    subcategory=con.execute("SELECT subcategory_id from addproduct WHERE id="+str(product_id)+" LIMIT 1").fetchone()[0]
    category=con.execute("SELECT category_id from addproduct WHERE id="+str(product_id)+" LIMIT 1").fetchone()[0]
    '''
    if subcategory:
        products=pd.read_sql_query("SELECT * from addproduct WHERE subcategory_id="+str(subcategory), con)
    else:
        products=pd.read_sql_query("SELECT * from addproduct WHERE category_id="+str(category), con)
    print(products['id'])
    '''
    specs=pd.read_sql_query("SELECT product_id,spec_id from specsvalues where category_id="+str(category),con)
    sp=specs.groupby('product_id')['spec_id'].apply(list).to_frame()
    for i in specs['spec_id'].unique():
        sp[i]=0
    for i in sp.index:
        for j in sp.loc[i,'spec_id']:
            sp.loc[i,j]=1
    sp=sp.drop('spec_id',axis='columns')
    scores=pd.Series(index=sp.index)
    for i in sp.index:
        scores.loc[i]=sp.loc[product_id].dot(sp.loc[i])
    con.close()
    return scores.sort_values(ascending=False)[scores>1]

def Hot_Sellers():
    con = sqlite3.connect("shop/test.db")

    events=pd.read_sql_query("SELECT * from events",con)
    events=events[events['event']=='transaction'].head(500)
    con.close()
    return events['product_id'].value_counts().index


def Top_Categories():
    con = sqlite3.connect("shop/test.db")

    events=pd.read_sql_query("SELECT events.timestamp, events.customer_id, events.event, events.product_id, events.transaction_id, addproduct.category_id, addproduct.subcategory_id from events INNER JOIN addproduct where events.product_id=addproduct.id",con)
    events=events[events['event']=='transaction'].head(500)
    con.close()
    return events['subcategory_id'].value_counts().index


def Top_Brands():
    con = sqlite3.connect("shop/test.db")

    events=pd.read_sql_query("SELECT events.timestamp, events.customer_id, events.event, events.product_id, events.transaction_id, addproduct.brand_id from events INNER JOIN addproduct where events.product_id=addproduct.id",con)
    events=events[events['event']=='transaction'].head(500)
    con.close()
    return events['brand_id'].value_counts().index


def most_viewed(user_id):
    con = sqlite3.connect("shop/test.db")
    events=pd.read_sql_query("SELECT events.timestamp, events.customer_id, events.event, events.product_id, events.transaction_id, addproduct.category_id, addproduct.subcategory_id from events INNER JOIN addproduct where events.product_id=addproduct.id and events.customer_id="+str(user_id)+" ORDER BY timestamp DESC LIMIT 20",con)
    items=events['product_id'].value_counts()
    most_viewed_items=items[items>3].index
    most_viewed_subcategory=events['subcategory_id'].value_counts().index
    if len(most_viewed_subcategory)>5:
        most_viewed_subcategories=most_viewed_subcategory[:5]
    most_viewed_category=events['category_id'].value_counts().index[0]
    #print(most_viewed_items,most_viewed_subcategory,most_viewed_category)
    return most_viewed_items,most_viewed_subcategory,most_viewed_category



def recommended_items_by_itemviewed(items):
    rec_list=set()
    for item in items:
        rec_list.update(content_based_filtering(item).index)
    return rec_list


def search_query(query,thresh=0.1):
    con = sqlite3.connect("shop/test.db")

    specifications=pd.read_sql_query("SELECT specsvalues.product_id AS id, specs.name AS specifications from specsvalues INNER JOIN specs ON specsvalues.spec_id=specs.id",con)
    spec_list=specifications.groupby('id')['specifications'].apply(lambda x: "%s" % ' '.join(x)).to_frame().reset_index()
    products=pd.read_sql_query("SELECT addproduct.id,addproduct.name, addproduct.price, addproduct.colors, addproduct.desc, category.name AS category, subcategories.name AS subcategory FROM addproduct LEFT JOIN category ON addproduct.category_id=category.id LEFT JOIN subcategories ON addproduct.subcategory_id=subcategories.id",con)
    products=pd.merge(products,spec_list,on="id")
    x = products.loc[:, products.columns != 'id'].to_string(header=False,index=False,index_names=False).lower().split('\n')
    df=pd.DataFrame({'id':products['id'],'product':x})
    print(df)
    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(df['product'])
    query_vec = vectorizer.transform([query.lower()])
    results = cosine_similarity(X,query_vec).reshape((-1,))
    idx, = np.where(results > thresh)
    sorted_idx= idx[np.argsort(results[idx])][::-1]
    print(sorted_idx)
    con.close()
    product_list=[]
    for i in sorted_idx:
        product_list.append(df.loc[i,'id'])
    print(product_list)

    return product_list
    
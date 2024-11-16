import pandas as pd
from pymongo import MongoClient

#Read file
file_path = 'amz_ca_total_products_data_processed.csv' 
product_data = pd.read_csv(file_path)

#Connect to database
client = MongoClient('mongodb://localhost:27017/')
db = client['amazon_catalog']
collection = db['products']

#Insert data
def insert_data(dataframe):
    records = dataframe.to_dict(orient='records')
    collection.insert_many(records)
    print("Data inserted successfully!")

insert_data(product_data)
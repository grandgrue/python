# -*- coding: utf-8 -*-
"""
Created on Thu Jun 25 19:08:30 2020

@author: sszgrm
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
# import matplotlib.pyplot as plt

# execution mode
# 1 = default charting mode
# 2 = debug mode with additional information 
mode = 1
db_path = '..\..\Python\DailyBudgetBackup2.sqlite'
excel_out = '..\..\Python\DailyBudget.xlsx'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

# List all available tables

if mode==2:

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    list_tables = cursor.fetchall()
    
    for i in list_tables:
        print("Details for: " + i[0])
    
        cursor.execute("SELECT sql FROM sqlite_master WHERE name = '" + i[0] + "';")
        print(cursor.fetchall())
        
        cursor.execute("SELECT * FROM " + i[0] + " LIMIT 10;")
        print(cursor.fetchall())
        
        cursor.execute("SELECT count(*) FROM " + i[0] + ";")
        print(cursor.fetchall())
        
        print("---")



# Interesting tables for my reporting
# ZBOOKING - Actual budget bookings
# ZCATEGORY - Categories to choose from 


df_book = pd.read_sql_query("SELECT ZCATEGORY, ZDATE, ZAMOUNT, ZNOTE FROM ZBOOKING", conn)

# Daily Budget stores dates as float: seconds after 2001-01-01
def convert_epoch(dateinseconds):
    utc_time = datetime(2001,1,1) + timedelta(seconds=dateinseconds)
    return utc_time
df_book['dateISO'] = df_book.apply(lambda x: convert_epoch(x['ZDATE']),axis=1)

# Prepare Categories for join with Bookings
df_cat = pd.read_sql_query("SELECT Z_PK AS ZCATEGORY, ZDESC AS CatName FROM ZCATEGORY", conn)

# Join Category to Bookings
df_rep = pd.merge(df_book, df_cat, on='ZCATEGORY', how='left')

# Convert spendings to positive values for charts by multiplying with -1
df_rep["amount"] = df_rep["ZAMOUNT"]*-1

# remove unused columns
del df_rep['ZDATE']
del df_rep['ZAMOUNT']

print(df_cat)

# Used Categories
# The Primary Key changes from Backup to Backup!
print(df_rep.groupby("CatName")["amount"].sum())
# 12 = Groceries
#  4 = Household
# 11 = Restaurant
# 10 = Pet
# 20 = Cigarettes
# 15 = Transportation
# 17 = Entertainment

df_main = df_rep.copy()
main_cat = ['Groceries','Household','Restaurant','Pet', 'Cigarettes', 'Transportation', 'Entertainment']
df_main['category'] = (df_main.CatName.str.findall('|'.join(main_cat)).str[0])
cat_is_empty = (pd.isnull(df_main.category))
df_main.loc[cat_is_empty, 'category']='Other'

print(df_main.groupby("category")["amount"].sum())

df_main["strdate"] = df_main["dateISO"].dt.strftime("%Y-%m-%d").str.slice(start=0, stop=7)
print(df_main.head())

print(df_main.groupby("strdate")["amount"].sum())

print(df_cat)
#df_subcat = df_rep[df_rep["ZCATEGORY"]==10]

piv_cat = df_main.pivot_table(values="amount", index="category", columns="strdate", aggfunc=sum)
print(piv_cat)

# write-mode to create a new excel sheet 
with pd.ExcelWriter(excel_out, engine="openpyxl", mode='w') as writer:
    piv_cat.to_excel(writer, sheet_name='Categories')

# rot = rotate labels by 45 degrees
#df_all.plot(x="dateISO", y="amount", kind="bar")
#plt.show()


# only groceries and household
df_grohou = df_rep[df_rep.CatName.isin(["Groceries", "Household"])].copy()
print(df_grohou.groupby("ZNOTE")["amount"].sum())
df_grohou["strdate"] = df_grohou["dateISO"].dt.strftime("%Y-%m-%d").str.slice(start=0, stop=7)

# create a new variable with the most common stores
store_name = ['Migros','Coop','Otto','Lidl', 'Aldi']
df_grohou['store'] = (df_grohou.ZNOTE.str
                             .findall('|'.join(store_name))
                             .str[0])
store_is_empty = (pd.isnull(df_grohou.store))
df_grohou.loc[store_is_empty, 'store']='Other'
print(df_grohou.groupby(["store", "ZNOTE"])["amount"].sum())

print(df_grohou.groupby(["store"])["amount"].sum())

piv_store = df_grohou.pivot_table(values="amount", index="store", columns="strdate", aggfunc=sum)
print(piv_store)

# append mode to add a sheet to the above created excel file
with pd.ExcelWriter(excel_out, engine="openpyxl", mode='a') as writer:
    piv_store.to_excel(writer, sheet_name='Store')

conn.close()
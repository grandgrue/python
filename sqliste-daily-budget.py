# -*- coding: utf-8 -*-
"""
Created on Thu Jun 25 19:08:30 2020

@author: sszgrm
"""

import sqlite3

db_path = '..\..\Python\DailyBudgetBackup2.sqlite'

conn = sqlite3.connect(db_path)

cursor = conn.cursor()
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

conn.close()

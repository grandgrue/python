# -*- coding: utf-8 -*-
"""
Created on Sat Jun 27 14:23:10 2020

@author: sszgrm
"""

import sys
import pandas as pd
import urllib.request
import json 

# api settings
ckanurl = "https://data.stadt-zuerich.ch"
resource_url1 = ckanurl + "/dataset/80d5c8af-b389-41d2-b6d8-d0deb1639f00/resource/b2abdef7-3e3f-4883-8033-6787a1561987/download/bev390od3903.csv"
showapi = ckanurl + "/api/3/action/package_show?id=" 
queryapi = ckanurl + "/api/3/action/resource_search?query=name:"

# Version 1: Access the data directly
# the csv is accessible with this url:
# https://data.stadt-zuerich.ch/dataset/80d5c8af-b389-41d2-b6d8-d0deb1639f00/resource/b2abdef7-3e3f-4883-8033-6787a1561987/download/bev390od3903.csv
# ressource_url = ckanurl + "/dataset/80d5c8af-b389-41d2-b6d8-d0deb1639f00/resource/b2abdef7-3e3f-4883-8033-6787a1561987/download/bev390od3903.csv"
dataset1 = pd.read_csv(resource_url1)
print(dataset1.head())


# Version 2: Use the dataset_id and access the first ressource
# see https://data.stadt-zuerich.ch/dataset/bev_bestand_jahr_quartier_alter_herkunft_geschlecht_od3903
dataset_id = "vehrkehrsaufkommen-in-zurich" # thats a showcase without resources
dataset_id = "bev_bestand_jahr_quartier_alter_herkunft_geschlecht_od3903"

with urllib.request.urlopen(showapi + dataset_id) as url:
    data2 = json.loads(url.read().decode())
    if data2["success"]==True:
        if len(data2["result"]["resources"]) > 0:
            resource_url2 = data2["result"]["resources"][0]["url"]
            dataset2 = pd.read_csv(resource_url2)
        else:
          sys.exit("CKAN package show API returned no resources.")  
    else:
        sys.exit("CKAN package show API call was not successfull.")
print(dataset2.head())
 

# Version 3: Use the ressource_name to query ckan and access the first with this name
# see https://data.stadt-zuerich.ch/dataset/bev_bestand_jahr_quartier_alter_herkunft_geschlecht_od3903/resource/b2abdef7-3e3f-4883-8033-6787a1561987
resource_name = "BEV390OD3903.csv"

with urllib.request.urlopen(queryapi + resource_name) as url:
    data3 = json.loads(url.read().decode())
    if data3["success"]==True:
        if data3["result"]["count"]>0:
            resource_url3 = data3["result"]["results"][0]["url"]
            dataset3 = pd.read_csv(resource_url3)
        else:
            sys.exit("No resource with the name " + resource_name + " found.")
    else:
        sys.exit("CKAN resource query was not successfull.")
print(dataset3.head())
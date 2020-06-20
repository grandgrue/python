# -*- coding: utf-8 -*-
"""
Created on Fri Jun 19 20:18:36 2020

@author: grandgrue
"""

import pandas as pd
import numpy as np
import urllib.request, json 

ckanurl = "https://data.stadt-zuerich.ch"
listapi = ckanurl + "/api/3/action/package_list"
showapi = ckanurl + "/api/3/action/package_show?id=" 
orgcsv = "organizations.csv"
orgmapcsv = "org-mapping.csv"
err_miss_map = "error_missing-mapping.csv"

# read a list of all packages (containing datasets, showcases, harvesters, etc.) from ckan api
listdata = pd.read_json(listapi) 

# prepare empty list
list_pkg = []

# loop trough all the packages and send a request to the ckan api for each of them
# as we expect several hundrets of packages, this will take a while
for index, row in listdata.iterrows():
    
    # read package details from ckan api
    with urllib.request.urlopen(showapi + row["result"]) as url:
        data = json.loads(url.read().decode())
  
        # we are only interested in active datasets (no harvesters or showcases)      
        if (data["result"]["type"]=="dataset") & (data["result"]["state"]=="active"):
            pkg_name = data["result"]["name"]
            pkg_author = data["result"]["author"]
            
            # add relevant attributes to a list
            element_list_pkg = [pkg_name, pkg_author]
            list_pkg.append(element_list_pkg)
        
    # for testing purposes we terminate the loop after 10 lines
    if index == 20:
        break   

# Convert list_pkg to dataframe for further processing (merging with mapping)
data_list = pd.DataFrame(list_pkg, columns = ['name' , 'author']) 

# Load the definition of all valid organizational entities */
data_org = pd.read_csv(orgcsv)
data_org["orgentity"] = data_org["DA"] + ", " + data_org["Dept"]

# Primary Mapping
data_list["orgentity"] = data_list.author.str.split(', ').str[-2] + ", " + data_list.author.str.split(', ').str[-1] 
# Left join organizational entities where the spelling is identical
data_list_org1 = pd.merge(data_list, data_org, on='orgentity', how='left')

# Secondary Mapping
data_org_map = pd.read_csv(orgmapcsv)
# Left join organizational entities with mapping list
data_list_org2 = pd.merge(data_list_org1, data_org_map, on='author', how='left')
# This results in two mapping fields: Nr and key

# Merge Nr and key - leading is the input of the manual org mapping
def org_nr(nr1, nr2):
    if pd.isnull(nr2):
        return nr1
    else:
        return nr2
data_list_org2['nrkey'] = data_list_org2.apply(lambda x: org_nr(x['Nr'],x['key']),axis=1)

# Missing Mappings
data_err_miss = data_list_org2[data_list_org2["nrkey"].isnull()]

data_err_miss.to_csv(err_miss_map)

if data_err_miss.shape[0]>0:
    print("ERROR: " + str(data_err_miss.shape[0]) + " missing mapping(s). See " + err_miss_map)
else:
    print("NOTE: Successfully mapped all authors")
 
    
# Prepare Data for Reporting
    
# Add department-key (first letter of nrkey) and counter to simplify further summary statistics
data_list_org2["deptkey"] = data_list_org2.nrkey.str.slice(stop=1)
data_list_org2["count"] = 1

# Aggregate results and rename and remove pivot-index for later join with pixel-positions
data_report_dept = pd.pivot_table(data_list_org2,index=["deptkey"],values=["count"],aggfunc=np.sum)
data_report_dept.index.names = ['Nr']
data_report_dept["type"] = "department"
data_report_dept =  data_report_dept.rename_axis(None, axis=1).reset_index() 

data_report_da = pd.pivot_table(data_list_org2,index=["nrkey"],values=["count"],aggfunc=np.sum)
data_report_da.index.names = ['Nr']
data_report_da =  data_report_da.rename_axis(None, axis=1).reset_index() 

data_pixel = data_org[["Nr", "xPixel", "yPixel"]]

data_pixel_dept = pd.merge(data_pixel, data_report_dept, on='Nr', how='left')
data_pixel_dept.rename(columns={'count': 'countDept'}, inplace=True)

data_pixel_report = pd.merge(data_pixel_dept, data_report_da, on='Nr', how='left')
data_pixel_report.rename(columns={'count': 'countDA'}, inplace=True)


# Create report by overlaying text on an existing org-chart image

image_in = "stzh-org.png"
image_out = "stzh-org-mod.png"
box_width = 160
padding_top_dept = -50
padding_right_dept = 5
padding_top_da = 13
padding_right_da = 3
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
import datetime
 
img = Image.open(image_in)
draw = ImageDraw.Draw(img)
font_dept = ImageFont.truetype("arial.ttf", 28, encoding="unic")
font_da = ImageFont.truetype("arial.ttf", 24, encoding="unic")
font_state = ImageFont.truetype("arial.ttf", 10, encoding="unic")

today = datetime.date.today()
draw.text((1500, 870), "Stand: " + today.strftime("%d.%m.%Y"), (0, 0, 0), font=font_state)

#font = ImageFont.load_default()
#font = ImageFont.truetype('Pillow/Tests/fonts/FreeMono.ttf', 20)

for index, row in data_pixel_report.iterrows():
    if row["type"]=="department":
        if pd.isnull(row["countDept"]):
            text = "0"
        else:
            text = str(int(row["countDept"]))
        text_width, text_height = draw.textsize(text, font_dept)
        xCoord = row["xPixel"]+box_width-text_width-padding_right_dept
        yCoord = row["yPixel"]+padding_top_dept
        draw.text((xCoord, yCoord), text, (0, 0, 0), font=font_dept)        
    else:
        if pd.isnull(row["countDA"]):
            text = "0"
        else:
            text = str(int(row["countDA"]))
        text_width, text_height = draw.textsize(text, font_da)
        xCoord = row["xPixel"]+box_width-text_width-padding_right_da
        yCoord = row["yPixel"]+padding_top_da
        draw.text((xCoord, yCoord), text, (0, 0, 0), font=font_da)
img.save(image_out)


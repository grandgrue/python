# -*- coding: utf-8 -*-
"""
Created on Mon Jun 29 17:10:41 2020

@author: sszgrm
"""

# TODOS
# - Verbesserung anstatt "Path too long" das File kopieren und lokal entzippen
# --- Beispiel in: J:/Datenmanagement/4_DWH/2_Qualitätssicherung/1_BVS6/ 

import zipfile
import re
import os
import pandas as pd
import numpy as np
import datetime
import json

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

# unzip one file from a zip archive to a given directory
def proj_unzip(zip_path, extract_filename, extract_path):
    if len(zip_path)>255:
        # ZipFile does not support long paths
        print("ERROR: Path too long: " + zip_path)
        return
    else:
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extract(extract_filename, path=extract_path)
                return extract_path + "/" + extract_filename
        except Exception: 
            print('ERROR: Not unzippable: ' + zip_path) 
            return

# read project.xml as a textfile an find infomap codeblocks

# libname _egimle sasioime
# 	 mappath="/InformationMaps/Bevoelkerung/BVS Wegzug int."
# 	 aggregate=yes
# 	 metacredentials=no
# 	 PRESERVE_MAP_NAMES=YES
# 	 %SetDisplayOrder;
# /* NOTE: when using this LIBNAME statement in a batch environment,  */
# /* you might need to add metadata host and credentials information. */
#
# data WORK.WEG (label='Ausgewählte Daten von BVS Wegzug int.');
# 	sysecho "Extrahieren von Daten aus der Information Map";
# 	length 
# 		FilterJahr 8
# 		...
# 		;
# 	label 
# 		FilterJahr="Jahresfilter"  /* Jahresfilter */
# 		...
# 		;
# 	
# 	set _egimle."BVS Wegzug int."n 
# 		(keep=
# 			FilterJahr
# 			StichtagDatJahr
# 			AnzWezuWir
# 			HerkunftSort
# 			ExportVersionCd 
# 		 /* default EXPCOLUMNLEN is 32 */ 
# 		 filter=((FilterJahr &gt;= 1) AND NOT (ExportVersionCd = "A")) 
# 		 
# 		 );
# 	
# run;
#
# /* clear the libname when complete */
# libname _egimle clear;

# the function extracts the variable names in two ways:
# 1. whats inside a "length" statement
# 2. whats inside a "keep" statement
# The length list has added information about the datatype
# But when users manipulate the code, the keep-list is more reliable

def extract_infomap_code(code_file, file_encoding):

    infomap_list_code = []
    keep_list = []
    is_im_block = False
    is_keep_block = False
    i=0
    
    with open(code_file, encoding=file_encoding) as f:
        content = f.readlines()
        for x in content:
            line = x.strip()
            i = i + 1
            
            if line == "libname _egimle sasioime": 
                # code block with libname starting
                im_list = {}
                keep_list = []
                is_im_block = True
            if line == "libname _egimle clear;": 
                if not "variables_keep" in im_list:
                     # No variables could be extracted, that is not good
                     im_list["variables_keep"] = ["ERROR no variables found"]
                infomap_list_code.append(im_list)
                is_keep_block = False
                is_im_block = False
            
            if is_im_block == True:
                mappath_search = re.search('mappath="(.*)"', line, re.IGNORECASE)
                if mappath_search:
                    # extract infomap name as the text behind the last slash
                    im_list["infomap_name"] = mappath_search.group(1).rsplit('/', 1)[-1]
                        
                if is_keep_block == True:
                    if line[-2:] == ");" or line[0:8] == "filter=(":
                        # end of code block with keep variable definitions
                        im_list["variables_keep"] = keep_list
                        is_keep_block = False
                    else:
                        # check if the line is a comment 
                        if line and line[0:2] != "/*" and line[0:2] != "*/" and line[0:1] != "%":
                            # add this variable definition to the list
                            keep_list.append(line)
                    
                if line[0:6] == "(keep=":
                     # code block with keep variable definition starting
                    keep_list = []
                    is_keep_block = True               
         
    return infomap_list_code

# Read configuration
with open('config.json', 'r') as f:
    config = json.load(f)
temp_path = config['temp_path']
path_ignore = config['path_ignore']
path_list = config['path_list'] 
write_to_excel = config['write_to_excel']  


# write_to_excel = True
# temp_path = "H:/Daten/Project/Desktop-2020/SampleSEG"

temp_unzip_path = temp_path + "/tempunzip"
proj_filename = "project.xml"

# path_ignore = ["/archiv/", "/_archiv/", "/Archiv/", "/_Archiv/", "/archive/",
#                "/Archive", "/alt/", "/Alt/", "/Archiv_nicht-löschen/",
#                "/00_Archiv/", "/0_Archiv/", "/9_Archiv/", "/X_Archiv/",
#                "/99_Alte_Anfrage_vor_InfoDesk/"]


# path_list = ["P:/Hotellerie"]

#edit the data
# config = {}
# config['temp_path'] = temp_path
# config['path_ignore'] = path_ignore
# config['path_list'] = path_list
# config['write_to_excel'] = write_to_excel

#write it back to the file
# with open('config.json', 'w') as f:
#     json.dump(config, f, sort_keys=True, indent=4)

excel_out = temp_path + "/report.xlsx"

csv_out = temp_path + "/infomap-var-list.csv"

now = datetime.datetime.now()
print ("Start walking directories: " + now.strftime("%Y-%m-%d %H:%M:%S"))

list_seg = []
list_sas = []

for scan_path in path_list: 
    print("Scanning: " + scan_path)
    
    # traverse root directory, and list directories as dirs and files as files
    for root, dirs, files in os.walk(scan_path):
        for file in files:
            if file.endswith(".egp"):
                seg_path = os.path.join(root, file).replace('\\', '/')
                
                # check if path contains patterns like "archived" or "old" and ignore them
                to_ignore = any(x in seg_path for x in path_ignore) 
                if to_ignore==False:
                    list_seg.append(seg_path)
    
            if file.endswith(".sas"):
                sas_path = os.path.join(root, file).replace('\\', '/')
                
                # check if path contains patterns like "archived" or "old" and ignore them
                to_ignore = any(x in sas_path for x in path_ignore) 
                if to_ignore==False:
                    list_sas.append(sas_path)

df_list_seg = pd.DataFrame(list_seg, columns = ['seg_path'])

df_list_sas = pd.DataFrame(list_sas, columns = ['sas_path'])

if write_to_excel:
    with pd.ExcelWriter(excel_out, engine="openpyxl", mode='w') as writer:
        df_list_seg.to_excel(writer, sheet_name='SEG-Projects')
        
    with pd.ExcelWriter(excel_out, engine="openpyxl", mode='a') as writer:
        df_list_sas.to_excel(writer, sheet_name='SAS-Code-Files')


now = datetime.datetime.now()
print ("Start extracting informationmaps: " + now.strftime("%Y-%m-%d %H:%M:%S"))

df_im_code = pd.DataFrame()

# loop through all the SAS Enterprise Guide files
for index, row in df_list_seg.iterrows():
    # unzip the project.xml file from the egp-file (which is a zip-file)
    proj_fullpath = proj_unzip(row["seg_path"], proj_filename, temp_unzip_path)

    if proj_fullpath:
        # find alle informationmaps in the code element of project.xml
        im_list_code = extract_infomap_code(proj_fullpath, "utf16")
        if im_list_code:
            # add the filename and store in a dataframe
            df_list_code = pd.DataFrame(im_list_code)
            df_list_code['filename']=row["seg_path"].replace('/', '\\')
            df_im_code = df_im_code.append(df_list_code, ignore_index = True)

# loop through all the SAS code files
for index, row in df_list_sas.iterrows():
   # find alle informationmaps in the code element of project.xml
    im_list_code = extract_infomap_code(row["sas_path"], "latin-1")
    if im_list_code:
        # add the filename and store in a dataframe
        df_list_code = pd.DataFrame(im_list_code)
        df_list_code['filename']=row["sas_path"].replace('/', '\\')
        df_im_code = df_im_code.append(df_list_code, ignore_index = True)

if df_im_code.empty==False:
    # transpose the variables column containing a list of variables to a new row variables
    lst_col = 'variables_keep'
    df_im_transv = pd.DataFrame({
          col:np.repeat(df_im_code[col].values, df_im_code[lst_col].str.len())
          for col in df_im_code.columns.drop(lst_col)}
        ).assign(**{lst_col:np.concatenate(df_im_code[lst_col].values)})[df_im_code.columns]
 
    df_im_transv = df_im_transv.drop_duplicates()
    
    if write_to_excel:
        # append-mode to create a new sheet in the existing excel file
        with pd.ExcelWriter(excel_out, engine="openpyxl", mode='a') as writer:
            df_im_transv.to_excel(writer, sheet_name='Code')
        
    df_im_transv.to_csv (csv_out, index = False, header=True)
 
now = datetime.datetime.now()
print ("Stop: " + now.strftime("%Y-%m-%d %H:%M:%S"))
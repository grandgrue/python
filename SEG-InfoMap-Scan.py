# -*- coding: utf-8 -*-
"""
Created on Mon Jun 29 17:10:41 2020

@author: sszgrm
"""

# TODOS
# - Verarbeiten von mehreren Verzeichnissen
# - Skalierbare Version mit Ablage in Datenbank
# - Error-Handling z.B. "BadZipFile: File is not a zip file"
# - Handling von %include-statements
# --- Sie sollten in einen Backlog aufgenommen werden und separat verwendet werden
# --- Includes zu suchen bringt nichts, da sie oft mit macro-variablen verborgen werden.
# --- Anstelle sollen alle .sas Dateien auch indexiert werden
# - Beim Code-Parsing nicht length, sondern keep nehmen - ist zuverlässiger
# --- Kommentare berücksichtigen

import zipfile
import re
import os
import pandas as pd
import numpy as np
import datetime

pd.set_option('display.max_columns', None)
#pd.set_option('display.max_rows', None)

# unzip one file from a zip archive to a given directory
def proj_unzip(zip_path, extract_filename, extract_path):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extract(extract_filename, path=extract_path)
        return extract_path + "/" + extract_filename


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
                is_im_block = True
            if line == "libname _egimle clear;": 
                infomap_list_code.append(im_list)
                is_keep_block = False
                is_im_block = False
            
            if is_im_block == True:
                mappath_search = re.search('mappath="(.*)"', line, re.IGNORECASE)
                if mappath_search:
                    # extract infomap name as the text behind the last slash
                    im_list["infomap_name"] = mappath_search.group(1).rsplit('/', 1)[-1]
                        
                if is_keep_block == True:
                    if line == ");" or line[0:8] == "filter=(":
                        # end of code block with keep variable definitions
                        im_list["variables_keep"] = keep_list
                        is_keep_block = False
                    else:
                        # check if the line is a comment 
                        if line[0:2] != "/*":
                            # add this variable definition to the list
                            keep_list.append(line)
                    
                if line == "(keep=":
                     # code block with keep variable definition starting
                    keep_list = []
                    is_keep_block = True               
         
    return infomap_list_code

temp_path = "H:/Daten/Project/Desktop-2020/SampleSEG"
temp_unzip_path = temp_path + "/tempunzip"
proj_filename = "project.xml"

path_ignore = ["/archiv/", "/_archiv/", "/Archiv/", "/_Archiv/", "/archive/",
               "/Archive", "/alt/", "/Alt/", "/Archiv_nicht-löschen/"]

root_path = "H:/Daten/Project/Desktop-2020/SampleSEG"
root_path = "O:/Auswertungen/Hotellerie"
root_path = "O:/Auswertungen/Mobilitaet-Verkehr"
root_path = "O:/Auswertungen"
root_path = "O:/Auswertungen/Bevoelkerung"
root_path = "P:/SAS/Siedlungsbericht/PROD"

excel_out = temp_path + "/report.xlsx"


now = datetime.datetime.now()
print ("Start walking directories: " + now.strftime("%Y-%m-%d %H:%M:%S"))

list_seg = []
list_sas = []
# traverse root directory, and list directories as dirs and files as files
for root, dirs, files in os.walk(root_path):
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

   # find alle informationmaps in the code element of project.xml
    im_list_code = extract_infomap_code(proj_fullpath, "utf16")
    if im_list_code:
        # add the filename and store in a dataframe
        df_list_code = pd.DataFrame(im_list_code)
        df_list_code['filename']=row["seg_path"]
        df_im_code = df_im_code.append(df_list_code, ignore_index = True)

# loop through all the SAS code files
for index, row in df_list_sas.iterrows():
   # find alle informationmaps in the code element of project.xml
    im_list_code = extract_infomap_code(row["sas_path"], "latin-1")
    if im_list_code:
        # add the filename and store in a dataframe
        df_list_code = pd.DataFrame(im_list_code)
        df_list_code['filename']=row["sas_path"]
        df_im_code = df_im_code.append(df_list_code, ignore_index = True)

if df_im_code.empty==False:
    # transpose the variables column containing a list of variables to a new row variables
    lst_col = 'variables_keep'
    df_im_transv = pd.DataFrame({
          col:np.repeat(df_im_code[col].values, df_im_code[lst_col].str.len())
          for col in df_im_code.columns.drop(lst_col)}
        ).assign(**{lst_col:np.concatenate(df_im_code[lst_col].values)})[df_im_code.columns]
 
    df_im_transv = df_im_transv.drop_duplicates()
    
    # append-mode to create a new sheet in the existing excel file
    with pd.ExcelWriter(excel_out, engine="openpyxl", mode='a') as writer:
        df_im_transv.to_excel(writer, sheet_name='Code')
 
now = datetime.datetime.now()
print ("Stop: " + now.strftime("%Y-%m-%d %H:%M:%S"))
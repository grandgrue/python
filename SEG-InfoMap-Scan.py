# -*- coding: utf-8 -*-
"""
Created on Mon Jun 29 17:10:41 2020

@author: sszgrm
"""

# TODOS
# - Tabelle mit InformationMaps
# - Tabelle mit Feldnamen (impact analyse)
# - Handling von %include-statements
# --- Sie sollten in einen Backlog aufgenommen werden und separat verwendet werden
# - "archiv" im Namen des Pfades 
# gefundene Beispiel: "\Archiv\", "\alt\", "\Archiv_nicht-löschen\", "\_Archiv\"

import zipfile
import re
import os
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np

# unzip one file from a zip archive to a given directory
def proj_unzip(zip_path, extract_filename, extract_path):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extract(extract_filename, path=extract_path)
        return extract_path + "/" + extract_filename



# read project.xml as xml an find clicked InformationMap elements

    # <InformationMap_List>
    #     <InformationMap>
    #         <Element>
    #             <Label>BVS Zuzug int.</Label>
    #             <Type>INFORMATIONMAP</Type>
    #             <ModifiedOn>636123019566140409</ModifiedOn>
    #             <ModifiedBy>Möhr Philipp (SSZ)</ModifiedBy>

def extract_infomap_meta(project_file):
    infomap_list_meta = []
    root = ET.parse(project_file).getroot()
    
    for type_tag in root.findall('InformationMap_List/InformationMap/Element'):
        im_list = {}
        for child in type_tag:   
            if child.tag=="Label": im_list["infomap_name"] = child.text
            if child.tag=="ModifiedOn": im_list["modified_at"] = child.text
            if child.tag=="ModifiedBy": im_list["modified_by"] = child.text
        infomap_list_meta.append(im_list)
    return infomap_list_meta



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
# 		StichtagDatJahr 8
# 		AnzWezuWir 8
# 		HerkunftSort 8
# 		ExportVersionCd $ 200
# 		;
# 	label 
# 		FilterJahr="Jahresfilter"  /* Jahresfilter */
# 		StichtagDatJahr="Daten gültig per Jahr"  /* Daten gültig per Jahr */
# 		AnzWezuWir="Anzahl Wegzüge wirtschaftlich"  /* Anzahl Wegzüge wirtschaftlich */
# 		HerkunftSort="Herkunft (Sort)"  /* Herkunft (Sort) */
# 		ExportVersionCd="Exportversion (Code)"  /* Exportversion (Code) */
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


def extract_infomap_code(project_file):
    infomap_list_code = []
    len_list = []
    is_im_block = False
    is_len_block = False
    i=0
    
    with open(project_file, encoding="utf16") as f:
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
                is_len_block = False
                is_im_block = False
            
            if is_im_block == True:
                mappath_search = re.search('mappath="(.*)"', line, re.IGNORECASE)
                if mappath_search:
                    # extract infomap name as the text behind the last slash
                    im_list["infomap_name"] = mappath_search.group(1).rsplit('/', 1)[-1]
    
                if is_len_block == True:
                    if line == ";":
                        # end of code block with length variable definitions
                        im_list["variables"] = len_list
                        is_len_block = False
                    else:
                        # add this variable definition to the list
                        len_list.append(line)
                    
                if line == "length":
                    # code block with length variable definition starting
                    len_list = []
                    is_len_block = True
    return infomap_list_code


temp_unzip_path = "H:/Daten/Project/Desktop-2020/SampleSEG/tempunzip"
proj_filename = "project.xml"

root_path = "O:/Auswertungen/Mobilitaet-Verkehr"
root_path = "H:/Daten/Project/Desktop-2020/SampleSEG"
root_path = "O:/Auswertungen/Hotellerie"

excel_out = "H:/Daten/Project/Desktop-2020/SampleSEG/report.xlsx"

df_im_meta = pd.DataFrame()
df_im_code = pd.DataFrame()

# traverse root directory, and list directories as dirs and files as files
for root, dirs, files in os.walk(root_path):
    for file in files:
        if file.endswith(".egp"):
            seg_path = os.path.join(root, file).replace('\\', '/')
            # print(seg_path)

            # unzip the project.xml file from the egp-file (which is a zip-file)
            proj_fullpath = proj_unzip(seg_path, proj_filename, temp_unzip_path)
            
            # find all informationmaps in xml tags
            im_list_meta = extract_infomap_meta(proj_fullpath)
            # print(im_list_meta)
            
            im_list_code = extract_infomap_code(proj_fullpath)
            # print(im_list_code)

            df_list_meta = pd.DataFrame(im_list_meta)
            df_list_meta['seg_path']=seg_path
            df_im_meta = df_im_meta.append(df_list_meta, ignore_index = True)

            df_list_code = pd.DataFrame(im_list_code)
            df_list_code['seg_path']=seg_path
            df_im_code = df_im_code.append(df_list_code, ignore_index = True)


df_im_meta = df_im_meta.sort_values(by='modified_at', ascending=False)
df_im_meta = df_im_meta.drop_duplicates(subset='infomap_name', keep='first')
print(df_im_meta)

# write-mode to create a new excel sheet 
with pd.ExcelWriter(excel_out, engine="openpyxl", mode='w') as writer:
    df_im_meta.to_excel(writer, sheet_name='Meta')

# transpose the variables column containing a list of variables to a new row variables
lst_col = 'variables'
df_im_transv = pd.DataFrame({
      col:np.repeat(df_im_code[col].values, df_im_code[lst_col].str.len())
      for col in df_im_code.columns.drop(lst_col)}
    ).assign(**{lst_col:np.concatenate(df_im_code[lst_col].values)})[df_im_code.columns]

df_im_transv = df_im_transv.drop_duplicates()

print(df_im_transv)

# append-mode to create a new sheet in the existing excel file
with pd.ExcelWriter(excel_out, engine="openpyxl", mode='a') as writer:
    df_im_transv.to_excel(writer, sheet_name='Code')
    
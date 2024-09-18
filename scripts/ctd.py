# -*- coding: utf-8 -*-
"""
Created on Wed Mar 13 10:49:45 2024

@author: dosullivan1
"""
import os
import pandas as pd
import chevron
from typing import Dict, List

# Import bespoke functions
import scripts.calculations as calculations

class CTD_Data:
    def __init__(self, 
                 rawFileDirectory, 
                 cnvFileDirectory, 
                 bottleFileDirectory, 
                 psaDirectory):
        """
        Parameters:
            rawFileDirectory: str
            
            cnvFileDirectory: str
            
            bottleFileDirectory: str
            
            psaDirectory: str
            
        Returns:
            CTD_Data Class
        """
        # get list of all files in directories
        files = os.listdir(rawFileDirectory) + os.listdir(bottleFileDirectory) 
        filetypes = ['.xmlcon','.bl','.hex','.hdr','.cnv','.btl']
        
        self.psaDirectory = psaDirectory 
        self.instrumentPath =""
        self.BottleDirectory = bottleFileDirectory
        self.CreateFile = 0
        self.inputDirectory = rawFileDirectory
        self.OutputDirectory = rawFileDirectory
        self.cnvDirectory = cnvFileDirectory
        
        fileTypeCount= []
        xmlCon = ""
        i=0
        
        self.df = pd.DataFrame()    
        allFilesInDirectory = []
        allFileTypesInDirectory=[]
        self.arrayItemsIndex=[]
        self.arrayItemsValue=[]
        self.blarrayItemsIndex=[]
        self.blarrayItemsValue=[]
        
        self.MergeHeaderFile: int | None = None
        self.numberArrayItems: int | None = None
        self.arrayItems: List | Dict | None = None

        # Loop directory and get the file names and types 
        
        for filetype in filetypes:
            names = []
            for name in files:
                if filetype == '.bl' and name.lower().endswith(filetype):
                    with open(os.path.join(rawFileDirectory,name), 'r') as f:
                        line_num = len(f.readlines()) # not most efficient
                    if line_num > 2:
                        #print('greater than 2: ' + name)    
                        names.append(name)
                        allFilesInDirectory.append(name.lower())
                        allFileTypesInDirectory.append(filetype)
                if filetype != '.bl' and name.lower().endswith(filetype): 
                    names.append(name)
                    allFilesInDirectory.append(name.lower())
                    allFileTypesInDirectory.append(filetype)
                if filetype == '.hex' and name.lower().endswith(filetype):
                    self.arrayItemsIndex.append(i)
                    self.arrayItemsValue.append(name)
                    i+=1

            fileTypeCount.append(len(names))
            if filetype=='.xmlcon':
                xmlCon = names[0]
                      
            
        self.fileNameAndType = dict(zip(allFilesInDirectory,allFileTypesInDirectory))
        self.df_preprocessing = pd.DataFrame(allFilesInDirectory) 
        self.df = self.df_preprocessing
        self.df[['cast','file_type']] = self.df[0].str.split(".",expand=True)

        self.df['present'] = 1
        self.df = self.df.pivot(index='cast', columns='file_type', values='present')
        self.df = self.df.fillna(0)
        
        for item in ['hdr','bl','hex','XMLCON','cnv','btl']:
            if item.lower() not in self.df.columns:
                self.df[item]=0
           
        self.arrayItems = dict(zip(self.arrayItemsIndex,self.arrayItemsValue)) 
        self.instrumentPath=os.path.join(rawFileDirectory,xmlCon)
     
        # Logic to create different PSA files        
        self.df['headerANDblMissing']=((self.df['hdr'] == 0) & (self.df['bl'] == 0) & (self.df['hex'] == 1) & (self.df['xmlcon'] == 1))
        self.df['blMissing']=((self.df['hdr'] == 1) & (self.df['bl'] == 0) & (self.df["hex"] == 1) & (self.df['xmlcon'] == 1))
        self.df['headerMissing']=((self.df['hdr'] == 0) & (self.df['bl'] == 1) & (self.df['hex'] == 1) & (self.df['xmlcon'] == 1))
        self.df['headerANDblPresent']=((self.df['hdr'] == 1) & (self.df['bl'] == 1) & (self.df['hex'] == 1) & (self.df['xmlcon'] == 1))
        self.df['blPresent']= self.df['bl'] == 1
        self.df['btlPresent']= self.df['btl'] == 1
        self.df['cnvPresent']= self.df['cnv'] == 1
        
        # Don't generate PSA if these are not included - display a warning 
        self.df['hexMissing']=((self.df['hex'] == 0) & (self.df['xmlcon'] == 1))
        self.df['xmlconMissing']=((self.df['hex'] == 1) & (self.df['xmlcon']))
               
        self.headerANDblPresent = self.df[self.df['headerANDblPresent']==True].index.tolist()
        self.headerANDblMissing = self.df[self.df['headerANDblMissing']==True].index.tolist()      
        self.headerMissing = self.df[self.df['headerMissing']==True].index.tolist()     
        self.blMissing = self.df[self.df['blMissing']==True].index.tolist()
        self.blPresent = self.df[self.df['blPresent']==True].index.tolist()
        self.btlPresent = self.df[self.df['btlPresent']==True].index.tolist()
        self.cnvPresent = self.df[self.df['cnvPresent']==True].index.tolist()

        # Do not generate PSA file - display warnings
        self.hexMissing = self.df[self.df['hexMissing']==True].index.tolist()
        self.xmlconMissing = self.df[self.df['xmlconMissing']==True].index.tolist()

#%%
def generateXml(psaTemplate, data, name):
    """
    Generate XML file for each PSA file
    
    Parameters:
        psaTemplate: str
        
        data:
        
        name:
    Returns:
        
    """
    with open(psaTemplate, 'r+', encoding="utf-8") as f:
        outputXML = chevron.render(f, {'data': data})
        #print(outputXML)
   
    with open(os.path.join(data.psaDirectory,name), 'w+', encoding="utf-8") as createXML:
        createXML.write(outputXML)
        print(name + " file created in cruise PSA folder")
    
            
#%%
def generate_psa_files(sensor_counts,
                       PSA_template_folder,
                       raw,
                       screen_2Hz,
                       bottle,
                       psa,
                       proc_mode):     
    """
    Parameters:
        sensor_counts: dict
            Contains type of sensors and number of them attached to the rig
        PSA_template_folder: str
            Name of directory with PSA templates
        raw: str
            Name of directory containing the raw CTD files
        screen_2Hz: str
            Name of directory with CNV files
        bottle: str
            Name of directory containing the .btl files
        psa: str
            Name of the directory containing the .psa files
        proc_mode: int
            Processing mode - should all files be processed or just those that
            have not been processed yet
        
    Returns:
        CTD_Data object
    """
    # Location of psa xml templates
    if sensor_counts['OxygenSensor']==0:
        psaTemplate = os.path.join(PSA_template_folder,'MI_datcnvTemplate_noO2.psa')
        botTemplate = os.path.join(PSA_template_folder,'MI_botsumTemplate_noO2.psa')
    elif sensor_counts['OxygenSensor']==1:
        psaTemplate = os.path.join(PSA_template_folder,'MI_datcnvTemplate_oneO2.psa')
        botTemplate = os.path.join(PSA_template_folder,'MI_botsumTemplate_oneO2.psa')
    elif sensor_counts['OxygenSensor']==2:
        psaTemplate = os.path.join(PSA_template_folder,'MI_datcnvTemplate_secO2.psa')
        botTemplate = os.path.join(PSA_template_folder,'MI_botsumTemplate_secO2.psa')
    
    wildeditTemplate = os.path.join(PSA_template_folder,'MI_wildeditTemplate.psa')
    filterTemplate = os.path.join(PSA_template_folder,'MI_filterTemplate.psa')
    celltmTemplate = os.path.join(PSA_template_folder,'MI_celltmTemplate.psa')
    binavg2HzTemplate = os.path.join(PSA_template_folder,'MI_binavg_2HzTemplate.psa')
    
    # Create dataset object to pass to template
    data = CTD_Data(raw, screen_2Hz, bottle, psa)
    # Repeating element of key value pairs to populate array items in psa file
    
    # Logic to generate different PSA files
    if proc_mode == 0:
        input_arg = data.headerANDblPresent
    elif proc_mode == 1:
        input_arg = [x for x in data.headerANDblPresent if x not in data.cnvPresent]
    if len(input_arg) > 0:
        data.MergeHeaderFile = 1
        data.CreateFile = 2
        data.numberArrayItems = len(input_arg)
        data.arrayItems = calculations.splitList(input_arg)
        name='datcnv_headerANDblPresent.psa'
        generateXml(psaTemplate, data, name)
        name='wildedit_headerANDblPresent.psa'
        generateXml(wildeditTemplate, data, name)
        name='filter_headerANDblPresent.psa'
        generateXml(filterTemplate, data, name)
        name='cellTM_headerANDblPresent.psa'
        generateXml(celltmTemplate, data, name)
        name='binavg2Hz_headerANDblPresent.psa'
        generateXml(binavg2HzTemplate, data, name)
        
    if proc_mode == 0:
        input_arg = data.headerANDblMissing
    elif proc_mode == 1:
        input_arg = [x for x in data.headerANDblMissing if x not in data.cnvPresent]     
    if len(input_arg) > 0:
        data.MergeHeaderFile = 0
        data.CreateFile = 0
        data.numberArrayItems = len(input_arg)
        data.arrayItems = calculations.splitList(input_arg)
        name='datcnv_headerANDblMissing.psa'
        generateXml(psaTemplate, data, name)
        name='wildedit_headerANDblMissing.psa'
        generateXml(wildeditTemplate, data, name)
        name='filter_headerANDblMissing.psa'
        generateXml(filterTemplate, data, name)
        name='cellTM_headerANDblMissing.psa'
        generateXml(celltmTemplate, data, name)
        name='binavg2Hz_headerANDblMissing.psa'
        generateXml(binavg2HzTemplate, data, name)
        
    if proc_mode == 0:
        input_arg = data.headerMissing
    elif proc_mode == 1:
        input_arg = [x for x in data.headerMissing if x not in data.cnvPresent] 
    if len(input_arg) > 0:
        data.MergeHeaderFile = 0 # type: ignore
        data.CreateFile = 2
        #data.arrayItems = dict2array(data.headerMissing)
        data.numberArrayItems = len(input_arg)
        data.arrayItems = calculations.splitList(input_arg)
        name='datcnv_headerMissing.psa'
        generateXml(psaTemplate, data, name)
        name='wildedit_headerMissing.psa'
        generateXml(wildeditTemplate, data, name)
        name='filter_headerMissing.psa'
        generateXml(filterTemplate, data, name)
        name='cellTM_headerMissing.psa'
        generateXml(celltmTemplate, data, name)
        name='binavg2Hz_headerMissing.psa'
        generateXml(binavg2HzTemplate, data, name)
        
    if proc_mode == 0:
        input_arg = data.blMissing
    elif proc_mode == 1:
        input_arg = [x for x in data.blMissing if x not in data.cnvPresent] 
    if len(input_arg) > 0:
        data.MergeHeaderFile = 1
        data.CreateFile = 0
        data.numberArrayItems = len(input_arg)
        data.arrayItems = calculations.splitList(input_arg)
        name='datcnv_blMissing.psa'
        generateXml(psaTemplate, data, name)
        name='wildedit_blMissing.psa'
        generateXml(wildeditTemplate, data, name)
        name='filter_blMissing.psa'
        generateXml(filterTemplate, data, name)
        name='cellTM_blMissing.psa'
        generateXml(celltmTemplate, data, name)
        name='binavg2Hz_blMissing.psa'
        generateXml(binavg2HzTemplate, data, name)
        
    ### Modified 06/07/21 to account for cruises without Btl files ###
    btl_files = data.blPresent
    for file in data.hexMissing:
        if file in btl_files:
            btl_files.remove(file)
    for file in data.blMissing:
        if file in btl_files:
            btl_files.remove(file)
    for file in data.headerANDblMissing:
        if file in btl_files:
            btl_files.remove(file)
    
    if proc_mode == 0:
        input_arg = data.blPresent
    elif proc_mode == 1:
        input_arg = [x for x in data.blPresent if x not in data.btlPresent] 
    if len(input_arg) > 0:
        data.numberArrayItems = len(input_arg) # type: ignore
        #print(data.numberArrayItems)
        data.arrayItems = calculations.splitList(input_arg) # type: ignore
        name='MI_botsum.psa'
        generateXml(botTemplate, data, name)    
           
    if len(data.hexMissing) > 0:
        print("Warning: hex files are missing")
    
    if len(data.xmlconMissing) > 0:
        print("Warning: xmlcon files are missing") 
     
    return data    

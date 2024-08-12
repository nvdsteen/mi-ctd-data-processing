# -*- coding: utf-8 -*-
"""
Created on Tue Mar 26 09:39:46 2024

@author: dosullivan1
"""
import os
import pandas as pd
from datetime import datetime as dt
import seawater

import scripts.sensor_configuration as sensor_configuration

#%%    
def sbe_btl2df(directory, raw_folder):
    """
    This function extracts information from a series of bottle files and 
    returns it as a single Dataframe.
    
    Parameters:
        directory: str
            Name of directory where .btl files are stored for the cruise 
        
    Returns: 
        pandas.DataFrame
            Data from .btl files combined into one dataframe
    """
    # Find all .btl files in the directory
    file_list = list(filter(lambda y: ('.btl' in y), os.listdir(directory)))
    # Initiate dataframe to store data in
    data_all = pd.DataFrame()
    
    # Loop through all files and read the relevant data from them
    for f in file_list:
        file = os.path.join(directory,f)
        with open(file,'r') as prof:
            # Determine column names and descriptions and file header length
            try:
                count = 0
                col_name = []
                data = []
                while True:
                    line = next(prof)
                    count += 1
                    if line[0]=='#':
                        continue
                    elif line[0]=='*':
                        continue
                    elif line[0] ==' ':
                        col_name.append(line)
                        col_name.append(next(prof))
                        while True:
                            data.append(next(prof))
                        break
            except StopIteration:
                data_avg = []
                data_std = [] 
                data_min = [] 
                data_max = []
                time = []
                for item in data:
                    item = item.replace('  ',',')
                    item = item.replace(' ','')
                    item = item.replace(',,,',',')
                    item = item.replace(',,',',')
                    item = item.replace(',,',',')
                    item = item.replace('(',',')
                    item = item.replace(')\n','')
                    item = item.split(',')
                    if item[-1] == 'avg':
                        data_avg.append(item[1:-1])
                    if item[-1] == 'std':
                        data_std.append(item[0:-1])
                    if item[-1] == 'min':
                        data_min.append(item[0:-1])
                    if item[-1] == 'max':
                        data_max.append(item[0:-1])
                    if item[-1] == 'sdev':
                        time.append(item[1])
                
                header = []        
                for item in col_name:
                    item = item.replace(' ',',')
                    item = item.replace(' ','')
                    item = item.replace(',,,',',')
                    item = item.replace(',,,,',',')
                    item = item.replace(',,,',',')
                    item = item.replace(',,,',',')
                    item = item.replace(',,',',')
                    item = item.replace(',,,',',')
                    item = item.replace(',,',',')
                    item = item.replace('\n','')
                    item = item.replace('WetStarTurbWETntu0','WetStar,TurbWETntu0')
                    item = item.split(',')
                    
                    header.append(item[1:])
                
                # Read data from file into a DataFrame using arguments from above
                data = pd.DataFrame(data_avg)
                data.columns = header[0]
                data.insert(0, 'CTD number', f.replace('.btl','').upper())
                data['Time'] = time
                
                # Rename voltage channels to sensor type
                sensor_dict = sensor_configuration.file_sensor_config(raw_folder, f)
                data_all.rename(columns=sensor_dict, inplace=True)
                if 'NotInUse' in data.columns:
                    data = data.drop(columns=['NotInUse'])

                data_all = pd.concat([data_all, data], sort=False)
        data_all = data_all.reset_index(drop=True)
    # Ensure date is in the expected formated
    data_all['Date'] = data_all['Date'].str[3:5]+' '+data_all['Date'].str[0:3]+' '+data_all['Date'].str[5:]
    # Ensure bottle is type float
    data_all['Bottle'] = data_all['Bottle'].astype(float)
    # Re-format Bottle Firing Time
    data_all['Bottle Firing Time'] = data_all.apply(lambda x: dt.strptime(x['Date'] + ' ' + x['Time'], '%d %b %Y %H:%M:%S'), axis=1)
    data_all.drop('Time', axis=1, inplace=True)

    data_all = data_all.loc[:,~data_all.columns.duplicated()]
    
    return data_all
    
#%%  
def sbe352df(directory):
    """
    This function extracts the temperature at bottle firing from the SBE35 
    output files.
        
    Parameters:
        directory: str
            Name of directory that contains SBE35 output files
        
    Returns:
        pandas.DataFrame
        Containing Cruise, CTD number, Bottle number and temperature value from SBE35 sensor
    """
    # Initiate dataframe to store data
    data_all = pd.DataFrame()
    # Get all file names in the directory
    file_list = os.listdir(directory)
    # Loop through files and read the relevant data from them
    for f in file_list:
        file = os.path.join(directory,f)
        with open(file,'r') as prof:
            # Determine file header length
            count = 0
            while True:
                line = next(prof)
                count += 1
                if line[0:2] =='dd':
                    break
        data = pd.read_csv(file, sep=r'\s+', header=None, skiprows=count)
        data['Cruise'] = os.path.splitext(file.replace(directory+'\\',''))[0].split('_')[0]
        data['CTD number'] = os.path.splitext(file.replace(directory+'\\',''))[0]
        data_all = pd.concat([data_all, data], sort=False)
    
    data_all = data_all.rename(columns = {7: 'Bottle', 16: 'SBE35_t090C'})
    # Subset columns to output required data to join to other datasets
    data_all = data_all[['Cruise','CTD number','Bottle','SBE35_t090C']]
    data_all = data_all.reset_index(drop=True)

    return data_all

#%%
def create_bottle_summary(bottle_directory, cruiseID,
                          logs,
                          ctd_events,
                          sbe35_raw,
                          raw_folder):
    # TODO: Should not have a function that doesn't return something
    # Should really return the data frame and then save it to a csv file within the notebook
    """
    Create a file with a summary of the bottle data collected
    
    Parameters:
        bottle_directory: str
            Name of directory with .btl files outputted from the CTD
        cruiseID: str
            Cruise ID
        logs: str
            Name of directory where the logsheets are stored
        ctd_events: pandas.DataFrame
            Data collected from the CTD over the entire duration of the research cruise
        sbe35_raw: str
            Name of directory with raw output files from the SBE35 sensor
        raw_folder: str
            Name of directory where raw data files are stored.
    Returns:
        Saves CSV files with the bottle summary
    """
    ## Load event, bottle logsheet metadata, .btl firing metadata and SBE35 file temperatures
    print("\nMerging bottle firing data with metadata from logsheets")
    # Run through btl file outputs and reformat to a csv for the cruise using function sbe_btl2df()
    if len(os.listdir(bottle_directory))>0:
        
        ####################################################################################################################################
        ## Reformat the .btl files into a single csv
        ####################################################################################################################################
        
        btl_output = sbe_btl2df(bottle_directory, raw_folder)

                        ### ED removing second o2 sensor variables from end of following list 21/06/2021
        btl_output = btl_output.rename(columns={'PrDM': 'prDM', 'DepSM': 'depSM', 'T090C': 't090C', 'T190C': 't190C', 'C0S/m': 'c0S/m', 'C1S/m': 'c1S/m', 
                                                'Sal00': 'sal00', 'Sal11': 'sal11', 'Sbeox0V': 'sbeox0V', 'Sbeox0Mm/L': 'sbeox0Mm/L', 'Sbeox1V': 'sbeox1V', 'Sbeox1Mm/L': 'sbeox1Mm/L'})
        btl_output['Bottle']=btl_output['Bottle'].astype(int)

        print("\tNumber of bottles in .btl files: %s" % len(btl_output))

        # Check for duplicate bottle firings in the file
        print("\nACTION *** Check for duplicates of the following bottle firing events ***")
        display(btl_output[btl_output[['CTD number','Bottle']].duplicated()])
        
        ####################################################################################################################################
        # Load bottle metadata from logsheets & merge with bottle firing data
        ####################################################################################################################################
        
        logsheets = os.path.join(logs,'%s_Log.xls' % cruiseID)

        # Load details of Bedford numbers assigned to sample bottles
        try:
            ####################################################################################################################################
            ## Load bottle metadata from logsheet
            ####################################################################################################################################
            bedfords = pd.read_excel(logsheets,
                                     sheet_name='CTD Casts - Bottles',
                                     usecols = "A,B,C,D,E,F,G,H")
            bedfords = bedfords.dropna(axis=0, how='all')
            bedfords.columns = ['CTD Cast number','Standard Station Name','CTD number','Bottle','Bedford Number','Nominal depth [m]','Status','Comment']
            bedfords['Standard Station Name'] = bedfords['Standard Station Name'].astype(str)
            bedfords['Comment'] = bedfords['Comment'].astype(str)
            bedfords['Comment']=bedfords['Comment'].str.replace(',',';')
            bedfords['Bottle']=bedfords['Bottle'].astype(int)
            for item in ['CTD Cast number','Standard Station Name','CTD number']:
                bedfords[item] = bedfords[item].str.upper()

            print("\tNumber of bottle logsheet rows with Bedford Numbers: %s" % len(bedfords[bedfords['Bedford Number'].notnull()]))
            print("\tNumber of bottle logsheet rows: %s" % len(bedfords))
           
            # Check for duplicate bottle firings in the file
            if len(bedfords[bedfords['Bedford Number'].notnull()])>0:
                df_x = bedfords[bedfords['Bedford Number'].notnull()]
                bedford_duplicated = df_x[df_x['Bedford Number'].duplicated()]['Bedford Number'].tolist()
                if len(bedford_duplicated)>0:
                    print("\nACTION *** Check for duplicated Bedford Numbers ***")
                    display(bedfords[bedfords['Bedford Number'].isin(bedford_duplicated)].sort_values(['Bedford Number', 'CTD number','Bottle'], ascending=[True, True, True]))
                    
            # Check bottle firing flags are valid
            file_flags = bedfords['Status'].unique().tolist()

            c = list(set(file_flags) - set(['G','L','M','DNF','B']))
            if len(c)>0:
                print("ACTION *** Unknown bottle status flags included in bottle log: ***")
                print(c)
                print("ACTION *** Please correct in the bottle log ***")

            ####################################################################################################################################
            # Combine metadata with bottle logsheet metadata
            ####################################################################################################################################
            btl_meta = pd.merge(ctd_events, bedfords, how = 'outer', on = ['CTD number'])
            print("Combined CTD event metadata with bottle logsheet metadata")

            print("\tNumber of bottle logsheet rows with Bedford Numbers: %s" % len(bedfords[bedfords['Bedford Number'].notnull()]))
            print("\tNumber of bottle logsheet rows: %s" % len(bedfords))
        
        except:
            print('CTD Casts - Bottles sheet does not exist in the log files.')
            btl_meta = ctd_events

        # Combine SBE bottle firing sensor values with metadata
        try:
            btl_meta = pd.merge(btl_output, btl_meta, how = 'inner', on = ['CTD number', 'Bottle'])
            print("Combined logsheet metadata and bottle firing data")
            print("\tNumber of rows with Bedford Numbers after logsheets and .btl file merge: %s" % len(btl_meta[btl_meta['Bedford Number'].notnull()]))
        except:
            btl_meta = pd.merge(btl_output, btl_meta, how = 'inner', on = ['CTD number'])
            print("No Bedford numbers available for pre/post merge comparison")

        print("\tNumber of rows of bottles after logsheets and .btl file merge: %s" % len(btl_meta))


        # Load and reformat the SBE35 output for the cruise using function sbe352df()
        if len(os.listdir(sbe35_raw))>0:
            sbe35_output = sbe352df(sbe35_raw)
            sbe35_output['SBE35temp_QC'] = '0'

            print("Number of bottles with SBE35 temperature data: %s" % len(sbe35_output))

            # Combine metadata with SBE35 output
            btl_meta = pd.merge(btl_meta, sbe35_output, how = 'left', on = ['Cruise','CTD number','Bottle'])

            try:
                print("Number of rows with Bedford Numbers after SBE35 merge: %s" % len(btl_meta[btl_meta['Bedford Number'].notnull()]))
            except:
                print("No Bedford numbers available for pre/port merge comparison")

            print("Number of rows after SBE35 merge = %s" % len(btl_meta))

        else:
            print("No SBE35 files for this cruise in the archive.")
            btl_meta['SBE35_t090C'] = None
            btl_meta['SBE35temp_QC'] = '9'

        # Set linear time from first to last cast of the cruise
        btl_meta['linear_time'] = (btl_meta['CTD_start'] - btl_meta['CTD_start'].min()) / (btl_meta['CTD_start'].max() - btl_meta['CTD_start'].min())    
        btl_meta['pot090C'] = btl_meta.apply(lambda x: seawater.ptmp(float(x.sal00), float(x.t090C), float(x.prDM)), axis=1)

        ### ED removing second o2 sensor variables from end of following list 21/06/2021
        # Data collation template
        cols_master = ['CTD Cast number','Cruise','Standard Station Name','CTD number','linear_time','CTD_start','Latitude [degrees_north]', 'Longitude [degrees_east]','Bot. depth [m]',
                       'Bottle','Nominal depth [m]', 'Bedford Number','Status','Comment','prDM','depSM','t090C','t190C','c0S/m','c1S/m','sal00','sal11','pot090C','sbeox0V','sbeox0Mm/L',
                       'sbeox1V','sbeox1Mm/L','SBE35_t090C','SBE35temp_QC','Bottle Firing Time']
        cols_out = []
        for item in cols_master:
            if item in btl_meta.columns.tolist():
                cols_out.append(item)
        print(cols_out)
        data_template = btl_meta[cols_out].sort_values(by=['CTD_start','Bottle'], ascending=True)

        template_csv = os.path.join(bottle_directory, f'{cruiseID}_bottle_summary.csv')
        data_template.to_csv(template_csv, index=False)

        # print(data_template.columns)
        print("\nBottle metadata and data merged. File saved to: %s" % template_csv)

    else:
        print("No bottle files to be processed for this cruise")


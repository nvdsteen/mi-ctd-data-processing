# -*- coding: utf-8 -*-
"""
Created on Tue Mar 26 09:29:19 2024

@author: dosullivan1
"""
import os
import pandas as pd
import gc
import re
import math 
import numpy as np

# Import bespoke functions
import scripts.calculations as calculations
import scripts.sensor_configuration as sensor_configuration

#%% 
def process_cnv(raw_directory):
    
    """
    Parameters:
        raw_directory: str
            Name of directory with raw output files from the CTD
    Returns:
        dict        
        Contains names of CNV files, latitude, longitude and timestamp of the 
        start of each cast contained in the CNV files
    """
    # Get list of files in the raw data directory
    filelist = os.listdir(raw_directory)
    # Initiate lists to store data in
    cnvfilelist = []
    latlist = []
    longlist = []    
    timelist = []
    systimelist = []
    
    # Extract cnv file names
    for item in filelist:
        if item.endswith(".cnv"):
            item = item.split('.')
            cnvfilelist.append(item[0].upper())
    
    # Extract lat, long and timestamp from cnv file and create list to add to dataframe        
    for item in cnvfilelist:
        with open(raw_directory+"\\"+item+'.cnv') as f:
            for line in f:
                line = line.rstrip()
                if line.startswith("* NMEA Latitude"):
                    latlist.append(line)
                if line.startswith("* NMEA Longitude"):
                    longlist.append(line)
                if line.startswith("* System UpLoad Time"):
                    timelist.append(line)
                if line.startswith("* System UTC"):
                    systimelist.append(line)
                
    return {'cnvfilelist': cnvfilelist,
            'latlist': latlist,
            'longlist': longlist,
            'timelist': timelist,
            'systimelist': systimelist}

def get_NMEA_from_header(directory, fileformat):
    '''
    Parameters: 
        directory: str
        fileformat: str
    Output:
        pd.DataFrame
    '''
    
    # Get CNV filenames
    filelist = os.listdir(directory)
    infofilelist = []
    
    for item in filelist:
        if item.endswith(".%s" % fileformat.lower()):
            item = item.split('.')
            infofilelist.append(item[0].upper())
    
    # Set dataframe for population
    df_NMEA = pd.DataFrame(columns = ['CTD number', 'Lat','Long','Upload Time','UTC Time'])
    
    # Extract lat, long and timestamps from cnv file        
    for item in infofilelist:
        with open(os.path.join(directory,item+".%s" % fileformat.lower())) as f:
            latdec = np.nan 
            londec = np.nan
            upload_time = ''
            utc_time = ''
        
            for line in f:
                line = line.rstrip()
                if line.startswith("* NMEA Latitude"):
                    x = line.split( )
                    latdec = float(x[5])/60
                    latdec = latdec + float(x[4])
                    if x[6]=='S':
                        latdec = latdec * -1

                if line.startswith("* NMEA Longitude"):
                    x = line.split( )
                    londec = float(x[5])/60
                    londec = londec + float(x[4])
                    if x[6]=='W':
                        londec = londec * -1
                    
                if line.startswith("* System UpLoad Time"):
                    upload_time = line
                    
                if line.startswith("* System UTC"):
                    utc_time = line

        # Save metadata to dataframe for file
        df_NMEA = pd.concat([df_NMEA, 
                             pd.DataFrame([[item,latdec,londec,upload_time,utc_time]], 
                                          columns = ['CTD number', 'Lat','Long','Upload Time','UTC Time'])
                             ]
                            )
    df_NMEA['Upload Time'] = pd.to_datetime(df_NMEA['Upload Time'].str.split('= ',expand=True)[1], format= '%b %d %Y %H:%M:%S')
    df_NMEA['UTC Time'] = pd.to_datetime(df_NMEA['UTC Time'].str.split('= ',expand=True)[1], format= '%b %d %Y %H:%M:%S')
    
    return df_NMEA

#%%
def load_logsheet(logsheets,
                  cruiseID,
                  cnvfilelist):
    """
    Load logsheet if it exists, rename and reformat columns accordingly 
    
    Parameters:
        logsheets: str
            Name of file containing the logsheet
        cruiseID: str
            Cruise Code
        cnvfilelist: list
            list of CNV files to be processed
            
    Returns:
        pandas.DataFrame
    """
    ctd_log = pd.DataFrame()
    if os.path.exists(logsheets):
        # Load CTD event metadata from logsheets
        print('Logsheet file saved in archive. Loading metadata from the logsheet file.')
        ctd_log = pd.read_excel(logsheets, 
                                sheet_name='CTD logs',
                                usecols = "C,D,E,F,H,O,P,R")
        ctd_log.columns = ['Cruise', 'Event number', 'CTD Cast number',
                           'Standard Station Name', 'CTD number',
                           'Latitude [degrees_north]', 'Longitude [degrees_east]',
                           'Bot. depth [m]']
        ctd_log['Event number'] = ctd_log['Event number'].astype(int)
        ctd_log['CTD number']  = ctd_log['CTD number'].str.upper()

        print("Number of CTD events in logsheet: %s" % len(ctd_log))

        # Check cruise matches ID provided for processing and is unique within the logsheet
        log_cruise_values = ctd_log['Cruise'].unique().tolist()
        if len(log_cruise_values)!=1:
            print("\nACTION *** Multiple cruises in the logsheet. Please check for typos or split logsheet by cruises")
            print("\tCruises listed in logsheet: %s" % log_cruise_values)
        else:
            if log_cruise_values[0] != cruiseID:
                print("\nACTION *** Cruise recorded in the logsheet does not match the cruise ID provided for processing. Please correct the logsheet.")
                print("\tCruise listed in logsheet: %s" % log_cruise_values[0])
        
        # Check CNV filenames against filenames in logsheet
        a = list(set(cnvfilelist) - set(ctd_log['CTD number'].unique().tolist()))
        b = list(set(ctd_log['CTD number'].unique().tolist()) - set(cnvfilelist))
        
        if len(a) !=0 or len(b) != 0:
            print('\nACTION *** Discrepancy in available CTD metadata between the Log and the header files. ***')
            print("\tFilenames not in the CTD logsheet \t\t\t\t%s" % a)
            print("\tCTD logsheet filenames without files in the raw data folder \t%s" % b)

    else:
        print('Logsheet file not provided.')
        # ctd_log = None
    
    return ctd_log

#%% 
def create_ctd_events(cruiseID,
                      raw_directory,
                      logs,
                      pumpdf):
    """
    Parameters:
        cruiseID: str
        
        raw_directory: str
            Name of directory with the raw output files from the CTD
        logs: str
            Name of the directory where the logsheet is stored
        pumpdf: pandas.DataFrame
    Returns:
        pandas.DataFrame
        
    """
    
    cnv_data = process_cnv(raw_directory)

    print("\nExtracting cast metadata from the header information for each cast for reference.")
    df_NMEA = get_NMEA_from_header(raw_directory, 'cnv')
    # Check if NMEA stream position and time saved to CTD header in CNV files
    # Check all fields populated
    print('\tNumber of HDR files available in cruise folder: %s' % (len(df_NMEA)))
    df_missingNMEA = df_NMEA.isnull().sum()
    for item in ['Lat','Long','Upload Time','UTC Time']:
        if df_missingNMEA[item]!=0:
            counts = df_missingNMEA[item]
            print("ACTION *** %s missing in %s HDR files *** Ensure %s entered into logsheet from paper logs for:" % (item, counts, item))
            print(df_NMEA[df_NMEA[item].isnull()]['CTD number'].tolist())
        else:
            print("\t%s present in all HDR files" % (item))

    systimelist = cnv_data['systimelist']
    latdec = calculations.convert_latitude_to_decimal(cnv_data['latlist'])
    longdec = calculations.convert_longitude_to_decimal(cnv_data['longlist'])
    logsheets = os.path.join(logs,'%s_Log.xls' % cruiseID)
    ctd_log = load_logsheet(logsheets, cruiseID, cnvfilelist=cnv_data['cnvfilelist'])
    
    # Merge profiles with metadata
    ## Use the NMEA time and position (lat and long) as prefered source for these fields
    if df_missingNMEA.sum() == 0:
        
        # Continue to build ctd_events dataframe from metadata in header
        ctd_events = pd.DataFrame() 
        ctd_events['Deck_checks'] = df_NMEA['UTC Time']
        ctd_events['Cruise'] = cruiseID
        ctd_events['CTD number']  = df_NMEA['CTD number']
        ctd_events['Latitude [degrees_north]'] = df_NMEA['Lat']
        ctd_events['Longitude [degrees_east]'] = df_NMEA['Long']

        #join output from pumpdf based on CTD number
        ctd_events = ctd_events.merge(pumpdf, on='CTD number')
        ctd_events['CTD_start'] = ctd_events['Deck_checks'] + ctd_events['Start']
        ctd_events['CTD_start'] = ctd_events['CTD_start'].dt.round('s')
        del ctd_events['Start']
        
        ## Join additional metadata fields if logsheet exists
        if ctd_log is not None:   ### if there is NMEA and logsheet then merge 
            # Merge logsheet metadata (less position data) in data frame ctd_log with date-times from header
            print("Merging NMEA lat, long and time with logsheet populated during the cruise")
            subset_columns = ctd_log.columns.to_list()
            subset_columns.remove('Latitude [degrees_north]')
            subset_columns.remove('Longitude [degrees_east]')
            ctd_log['CTD number'] = ctd_log['CTD number'].str.upper()
            ctd_events = ctd_events.merge(ctd_log[subset_columns], on=['CTD number', 'Cruise'])
            print("\tNumber of CTD events in merged logsheet: %s" % len(ctd_log))
            print("\tNumber of CTD events after merging metadata from CTD header files with logsheets: %s" % len(ctd_events))          
           
        else:
            print("No logsheet to merge additional cast metadata.")
        
        ctd_events_nopos = None
        
    ## In the absence of the NMEA fields then use the logsheet metadata
    elif os.path.exists(logsheets) and (df_missingNMEA['Lat'] != 0 or df_missingNMEA['Long'] != 0):
        
        # Merge logsheet metadata in data frame ctd_log with date-times from header
        ctd_events = pd.DataFrame()
        if df_missingNMEA['UTC Time'] == 0: 
            ctd_events['Deck_checks'] = df_NMEA['UTC Time']
        else:
            ctd_events['Deck_checks'] = df_NMEA['Upload Time']
        ctd_events['Cruise'] = cruiseID
        ctd_events['CTD number']  = df_missingNMEA['CTD number']
        ctd_events = ctd_events.merge(ctd_log, on=['Cruise','CTD number'])
        print("Number of CTD events in merged logsheet: %s" % len(ctd_log))

        #join output from pumpdf based on CTD number
        ctd_events = ctd_events.merge(pumpdf, on='CTD number')
        ctd_events['CTD_start'] = ctd_events['Deck_checks'] + ctd_events['Start']
        ctd_events['CTD_start'] = ctd_events['CTD_start'].dt.round('s')
        del ctd_events['Start']

        ctd_events_nopos = None
        
    ## In the absence of both NMEA and logsheets then take the system upload time (have to assume this is correctly synchronised with the ship's time) and get lat/long positions from the underway dataset
    else:
        print("ACTION *** No logsheet file or NMEA data in the HDR files. Lat/lon will need to be extracted from underway data streams for CTD date-times. ***")
            
        # Collate a list of the system time and add on time elapsed until the surface soak to approximate start of downcast for underway postion extraction of lat/lon 
        ctd_events_nopos = pd.DataFrame()
        if len(systimelist)!=0:
            ctd_events_nopos['Deck_checks']  = df_NMEA['Upload Time']
        else:
            ctd_events_nopos['Deck_checks'] = ''
        ctd_events_nopos['Cruise'] = cruiseID
        ctd_events_nopos['CTD number']  = df_NMEA['CTD number']

        #join output from pumpdf based on CTD number
        if len(systimelist)!=0:
            ctd_events_nopos = ctd_events_nopos.merge(pumpdf, on='CTD number')
            ctd_events_nopos['CTD_start'] = ctd_events_nopos['Deck_checks'] + pd.Timedelta(ctd_events_nopos['Start'], unit='S') # type: ignore 
            ctd_events_nopos['CTD_start'] = ctd_events_nopos['CTD_start'].dt.round('S')
            del ctd_events_nopos['Start']
        else:
            ctd_events_nopos['CTD_start'] = ''

        db_metadata = os.path.join(logs,'Metadata_'+cruiseID+'.csv')

        if not os.path.exists(db_metadata):                                         ### if no metadata file present make one without Lat Lon
            # Save metadata to file for underway postion extraction of lat/lon
            ctd_events_nopos.to_csv(os.path.join(logs,'Metadata_'+cruiseID+'_nopos.csv'), index= False)
            print('Metadata_'+cruiseID+'_nopos.csv saved to logsheets folder. Populate lat/lon positions from underway database before proceeding.')
        else:                                                                       ### if user has populated metadata file with Lat Lons
            print("File present with latitude and longitude from database underway SCS processing.")
            ctd_events = pd.read_csv(db_metadata, parse_dates = ['Deck_checks',
                                                                'CTD_start'
                                                                ])
        
    return ctd_events

#%%
def create_output_csv_for_fisheries(df, output_directory):
    """
    Outputs data to meet requirement of the fisheries team. 
    Extracts data at the iso-surface, 5m, 20m, 50m and bottom depth
    
    Parameters:
        df: pandas.DataFrame
            Profile data from the CTD for the entire cruise
        output_directory: str
            Name of folder to save csv files
    """
    # Iso-surface outputs for fisheries team    
    output_params = ['Longitude [degrees_east]','Latitude [degrees_north]','t090C','sal00']
    
    # Create dataframe for data at 5m depth
    df_surface = df[df['depSM'].between(4,6)].groupby('CTD number').mean(numeric_only=True)
    df_surface['depSM'] = 5.0
    df_surface = df_surface[output_params]
    df_surface.to_csv(os.path.join(output_directory,'ts5.csv'), index=True, header=False)
    
    # Create dataframe for data at 20m depth
    df_20 = df[df['depSM'].between(19,21)].groupby('CTD number').mean(numeric_only=True)
    df_20['depSM'] = 20.0
    df_20 = df_20[output_params]
    df_20.to_csv(os.path.join(output_directory,'ts20.csv'), index=True, header=False)
    
    # Create dataframe for data at 50m
    df_50 = df[df['depSM'].between(49,51)].groupby('CTD number').mean(numeric_only=True)
    df_50['depSM'] = 50.0
    df_50 = df_50[output_params]
    df_50.to_csv(os.path.join(output_directory,'ts50.csv'), index=True, header=False)
    
    # Create dataframe for data at the bottom of the water column
    df_bottom = pd.DataFrame()
    for cast in df['CTD number'].unique().tolist():
        df_bottom = pd.concat([df_bottom,df[(df['CTD number']==cast) & (df['depSM'].between(df[df['CTD number']==cast]['depSM'].max()-2,df[df['CTD number']==cast]['depSM'].max()))].groupby('CTD number').mean(numeric_only=True)])
    df_bottom = df_bottom[output_params]
    df_bottom.to_csv(os.path.join(output_directory,'tsbottom.csv'), index=True, header=False)
    
    # Delete dataframes to clear up space as they have been save to csvs
    del(df)
    del(df_surface)
    del(df_20)
    del(df_50)
    del(df_bottom)
    gc.collect()
    
    return print("Depth surfaces saved to %s." % output_directory)

#%%
def merge_data_with_metadata(cruiseID,
                             output_directory,
                             ctd_events,
                             logs):
    """
    Combine data collected from the CTD with it's corresponding metadata and saves
    it as a CSV file
    
    Parameters:
        cruiseID: str
            Cruise ID
        output_directory: str
            Name of directory to save CSV file to
        ctd_events: pandas.DataFrame
            Data collected from the CTD over the period of the entire cruise
        logs: str
            Name of directory to save metadata csv file to
            
    Returns:
        pandas.DataFrame
    """
    # Merge metadata with cast data
    # Load binned CTD data
    uncal_file = os.path.join(output_directory,'cruise_data_uncal_1mbinned.csv') 
    df = pd.read_csv(uncal_file)
    # Add column with filename as lowercase for later matching
    df['CTD number lower'] = df['CTD number'].str.lower()
    print("Number of rows in profile dataframe prior to metadata merge: %s" % len(df))

    # Add linear time to metadata for calibrations
    ctd_events['linear_time'] = (ctd_events['CTD_start']-ctd_events['CTD_start'].min())/(ctd_events['CTD_start'].max()-ctd_events['CTD_start'].min())
    # Add column with filename all lowercase for matching
    ctd_events['CTD number lower'] = ctd_events['CTD number'].str.lower()
    # Merge dataframes based on lowercase filename
    df = pd.merge(ctd_events, df, how = 'inner', on = ['CTD number lower'])
    # Drop surplus columns
    df = df.drop(['CTD number lower','CTD number_y'], axis = 1)
    # Rename column
    df.rename(columns = {'CTD number_x':'CTD number'}, inplace = True)
    print("Number of rows in profile dataframe after to metadata merge: %s" % len(df))

    # Save profiles ready for screening
    df.to_csv(os.path.join(output_directory,'%s_CTDprofiles_uncal_1mbinned_meta.csv' % cruiseID), index=False)
    print("Data file saved and ready for QC to output folder.")
    
    # Save metadata
    ctd_events.to_csv(os.path.join(logs,'Metadata_'+cruiseID+'.csv'), index= False)
    print('Metadata_'+cruiseID+'.csv saved to logsheets folder.')
    
    return df
    

#%%                              
def cnv2df(cruiseID, file_list, params=[], raw_folder = '', directory = '', 
           txt_strip = '', ud_id = True, z_cord = 'prDM'):
    """
    This function loads a list of SBE CTD profile CNV format files into a 
    pandas DataFrame. Using arguments the profiles can be provisionally QC'd, 
    down-up cast identified (for Hz data) and profile names generated from the file name.
    
    Parameters:   
        cruiseID: str
            Cruise ID, function assumes cruiseID is used as part of the filenaming convention.
        file_list: list
            A list of file paths for the CNV files. To run for a single file, provide a list with one item;
        params: list
            If only a subset of the parameters are required, provide a list 
            using the SBE CNV column name (e.g. 'prDM' for Pressure);
        raw_folder: str
            Name of directory with raw files
        directory: str
            Name of folder containing CNV files
        txt_strip: str
            Regular expression to isolate the profile name from the file name
        ud_id: bool
            If the file contains the full cast (e.g. 2Hz data) the routine will 
            add a column ('cast') to the DataFrame indicating if the measurement
            is part of the down or upcast of each profile
        z_cord: str
            Provide the z variable for determining the down/up cast split
    
    Returns:
        pandas.DataFrame
        Data from all CNV files is combined together into a pandas DataFrame
    """
    
    # Checks function inputs are of the correct type
    def type_check(file_list=file_list, params=params, txt_strip=txt_strip, ud_id=ud_id, z_cord=z_cord):
        if not isinstance(file_list, list):
            raise TypeError("Error: 'file_list' should be a list.")

        if not isinstance(params, list) or not isinstance(txt_strip, str) or \
           not isinstance(ud_id, bool) or not isinstance(z_cord, str):
            raise TypeError(
                "Error: 'params' should be a list, 'txt_strip' should be a string, "
                "'ud_id' should be a boolean, and 'z_cord' should be a string."
            )
        
    type_check(file_list=file_list, params=params, txt_strip=txt_strip, ud_id=ud_id, z_cord=z_cord)

    # Set DataFrame container for function
    data_all = pd.DataFrame()
    
    # Iterate through files provided in the file_list argument
    for file in file_list:
        #print(file)       # for debugging
        f = os.path.join(directory,file)
        with open(f,'r') as prof:
            # Determine column names and descriptions and file header length
            count = 0
            col_id = []
            col_name = []
            col_description = []
            while True:
                line = next(prof)
                count += 1
                if line =='*END*\n':
                    break
                elif '# name ' in line:
                    col_id.append(re.findall(r'[0-9]+',line)[0])
                    col_name.append(line.split(': ')[0].split(' = ')[1])
                    col_description.append(line.split(': ')[1][0:-1])

        # Read data from file into a DataFrame using arguments from above
        data = pd.read_csv(f, sep=r'\s+', header=None, index_col=0, names=col_name, skiprows=count, low_memory=False)
        
        # Set any columns that are read as string to float
        colsf = data.select_dtypes(exclude=['float']).columns
        data[colsf] = data[colsf].apply(pd.to_numeric, errors='coerce')
        # Drop SBE CNV file flag column
        data = data.drop(columns=['flag'])
        
        # Rename voltage channels to sensor type
        sensor_dict = sensor_configuration.file_sensor_config(raw_folder, file)
        data.rename(columns=sensor_dict, inplace=True)
        # Drop any voltage channels that were not in use
        if 'NotInUse' in data.columns:
            data = data.drop(columns=['NotInUse'])
            
        # Return data as DataFrame and reset the Index as unique for each cycle.
        data = data.reset_index()
                
        # Checks the z-cordinate parameter provided exists in the data.
        if ud_id == True and z_cord not in col_name:
            raise IOError("Please provide the name of a valid z-co-ordinate within file: %s." % file)
            
        # If the cast is to be split into down and up cast cycles use the z-cord provided.
        if ud_id ==True:
            data['cast'] = 'D'
            data.loc[int(data[z_cord].idxmax())+1:,['cast']] = 'U'
        
        # Add profile name to the DataFrame as taken from the filename using txt_strip argument.
        data.insert(0, 'profile', file.replace(txt_strip,'').upper())
        
        # Add file data to function DataFrame
        data_all = pd.concat([data_all, data],sort=False)
            
    # Reset function DataFrame index to unique row number for all cycles in the data set     
    data_all = data_all.reset_index(drop=True)

    # Reduce to a subset of the parameters provided as an function argument
    if len(params) != 0:
        file_params = ['profile']
        if ud_id==True:
            file_params.append('cast')
        for item in params:
            file_params.append(item)
        data_all = data_all[file_params]

    return data_all

#%%
def start_dcast(df, profile_id, zcoord):
    """
    Parameters:
        df: pandas.DataFrame
            2Hz data frame returned from cnv2df function. Contains all data
            from the CNV files
        profile_id: str
            Name of column containing the profile name
        zcoord: str
            Provide the z variable for determining the down/up cast split
    Returns:
        pandas.DataFrame
    """
    # Get a list of profiles from the dataframe
    profile_list = df[profile_id].unique().tolist()
    # Instantiate an empty list to collate results
    pumpIndexList = []
    
    # Iterate through each profile in the dataframe
    for item in profile_list:
        # Subset the dataframe to give a dataframe per profile
        cruisedf = df[(df[profile_id] == item)]
        # Check if the profile only contains up cast data. 
        # Can happen when data acquisition fails during a cast.
        if cruisedf['cast'].unique == 'U':
            # Where upcast data only present return warning message.
            print("File %s contains only up-cast data. Check if file should be merged with downcast." % item)
        else:
            # Where downcast data present
            # print(item)             ## for debugging
            dcst_cycles = len(cruisedf[(cruisedf.cast=='D')])
            # Find number of downcast cycles where pump is off
            dcst_pump_off_cycles = len(cruisedf[(cruisedf.pumps==0) & (cruisedf.cast=='D')])
            # Find number of downcast cycles where pump is on
            dcst_pump_on_cycles = len(cruisedf[(cruisedf.pumps==1) & (cruisedf.cast=='D')])
            print("\tDown cast cycles: %s\tPump off cycles: %s\t Pump on cycles: %s" % (dcst_cycles, dcst_pump_off_cycles, dcst_pump_on_cycles))
            # Check if the pump is switched on for the entire downcast
            if dcst_pump_on_cycles==dcst_cycles:
                print('\tPump on throughout downcast')
                # For profiles where the pump is on for the full downcast,
                # get the first pressure/depth in the file
                mindep = cruisedf[cruisedf['cast']=='D'][zcoord].min()
                print("\tMinimum depth after pump switches on: %s" % mindep)
                # Return index of the first data cycle for the profile
                mindepIndex = cruisedf[(cruisedf.pumps==1) & (cruisedf.cast=='D') & 
                                       (cruisedf[zcoord]==mindep)].index[0]
                print(mindepIndex)
            # Check if the pump is switched off for the entire downcast
            elif dcst_pump_off_cycles==dcst_cycles:
                print('\tPump off throughout downcast')
                mindep = cruisedf[cruisedf['cast']=='D'][zcoord].min()
                print("\tMinimum depth for down-cast: %s ***Manual selection for start of cast required***" % mindep)
                # Return index of the first data cycle for the profile
                mindepIndex = cruisedf[(cruisedf.pumps==0) & (cruisedf.cast=='D') & (cruisedf[zcoord]==mindep)].index[0]
            # Where pump switches on during downcast    
            else:
                print('\tPump switches on during downcast')
                # return the index of the maximum depth/pressure before the pump switches on
                maxdepoff = cruisedf[(cruisedf.pumps==0) & (cruisedf.cast=='D')][zcoord].max()
                #print(maxdepoff)
                maxdepoffIndex = cruisedf[(cruisedf.pumps==0) & (cruisedf.cast=='D') & (cruisedf[zcoord]==maxdepoff)].index[0]
                #print(maxdepoffIndex)
                mindep = cruisedf[(cruisedf.pumps==1) & (cruisedf.cast=='D') & (cruisedf['prDM']<maxdepoff) & (cruisedf.index>maxdepoffIndex)][zcoord].min()
                #print(mindep)
                if math.isnan(mindep):
                    print('\tCheck if surface soak took place.')
                    mindep = cruisedf[(cruisedf.pumps==1) & (cruisedf.cast=='D')].prDM.min()
                    # Return the index of the shallowest depth of the downcast after the pump turns on during the downcast
                    mindepIndex = cruisedf[(cruisedf.pumps==1) & (cruisedf.cast=='D') & (cruisedf[zcoord]==mindep)].index[0]
                else:
                    # Return the index of the shallowest depth of the downcast after the pump turns on during the downcast
                    mindepIndex = cruisedf[(cruisedf.pumps==1) & (cruisedf.cast=='D') & (cruisedf[zcoord]==mindep) & (cruisedf.index>maxdepoffIndex)].index[0]
                print("\tMinimum depth after pump switches on: %s" % mindep)
            
            # Collate a list of indices for the shallowest cycle of the downcast to be taken forward    
            pumpIndexList.append(mindepIndex)
            #print(pumpIndexList)
    # Use the list of indices for each profile to subset the profile dataframe 
    # to provide the index to be used as the downcast start for each profile
    pumpdf = df.loc[pumpIndexList]
    pumpdf = pumpdf[[profile_id,'timeS',zcoord]]
    pumpdf[['timeS',zcoord]] = pumpdf[['timeS',zcoord]].apply(pd.to_numeric)
    
    return pumpdf

#%% 
def combine_files2cast_old(dfin, combined):
    """
    Merge multiple files from a cast where data logging interupted, 
    resulting in multiple files for the cast.

    Parameters:
        dfin: pandas.DataFrame
        
        combined: dict
            Containing the initial cast CNV filename and the CNV file names to 
            be merged and their cast status (ie. if it was an downcast or upcast)
            Cast status should be one of 'D', 'U' or 'D/U'
            'D' - downcast
            'U' - upcast
            'D/U' - downcast or upcast
            Should be in the form of:
            combined = {'initial cast CNV filename' : 
                        [{'CNV file to be merged':'cast status'},
                         {'CNV file to be merged':'cast status'}, ]}
            eg. combined = {'CE21003_CTD002.CNV': [{'CE21003_CTD002B.CNV': 'D/U'},
                                                   {'CE21003_CTD002C.CNV': 'U'}]
                            }            
    
    Returns:
        pandas.DataFame
    
    """
    if combined!=None:
        for item in list(combined.keys()):
            print(item)
            for prfile in combined[item]:
                # print(prfile)    # for debugging
                files = list(prfile.keys())
                # print(files)     # for debugging
                for ind in files:
                    print(ind)
                    cst = prfile[ind]
                    print(cst)
                    if cst =='U':
                        dfin.loc[dfin['profile']==ind,'cast'] = 'U'
                        print("Data from file %s updated cast status to 'U' (down-cast='D', up-cast='U')." % (ind))
                    else:
                        print("Data from file %s retained cast status (down-cast='D', up-cast='U')." % (ind))
                    dfin['profile'] = dfin['profile'].str.replace(ind,item,regex=True)
                    print("Data from file %s relabeled profile name to %s." % (ind,item))
    else:
        print("No files indicated for merging.")     
            
    return dfin

#%% 
def combine_files2cast(dfin, combined, cell_id):
    """
    Merge multiple files from a cast where data logging interupted, 
    resulting in multiple files for the cast.

    Parameters:
        dfin: pandas.DataFrame
        
        combined: dict
            Containing the initial cast CNV filename and the CNV file names to 
            be merged and their cast status (ie. if it was an downcast or upcast)
            Cast status should be one of 'D', 'U' or 'D/U'
            'D' - downcast
            'U' - upcast
            'D/U' - downcast or upcast
            Should be in the form of:
            combined = {'initial cast CNV filename' : 
                        [{'CNV file to be merged':'cast status'},
                         {'CNV file to be merged':'cast status'}, ]}
            eg. combined = {'CE21003_CTD002.CNV': [{'CE21003_CTD002B.CNV': 'D/U'},
                                                   {'CE21003_CTD002C.CNV': 'U'}]
                            }
        cell_id: int
    
    Returns:
        pandas.DataFame
    """
    
    if combined!=None:
        for item in list(combined.keys()):
            if item in dfin['profile'].unique().tolist():
                # print(item)    # for debugging
                for prfile in combined[item].keys():
                    #print(prfile)    # for debugging
                    cst = combined[item][prfile]
                    #print(cst)     # for debugging
                    if cst =='U':
                        dfin.loc[dfin['profile']==prfile,'cast'] = 'U'
                        print("Data from file %s updated cast status to 'U' (down-cast='D', up-cast='U')." % (prfile))
                    else:
                        print("Data from file %s retained cast status (down-cast='D', up-cast='U')." % (prfile))
                    dfin['profile'] = dfin['profile'].str.replace(prfile,item,regex=True)
                    print("Data from file %s relabeled profile name to %s." % (prfile,item))
            else:
                raise IOError("Cast for merging not present in file. Please checked combined variable defined in cell %s" % cell_id)
    else:
            print("No files indicated for merging.")
               
    return dfin
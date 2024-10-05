# -*- coding: utf-8 -*-
"""
Created on Tue Mar 26 09:29:53 2024

@author: dosullivan1
"""
import os
from pathlib import Path
import xml.etree.ElementTree as elementTree
import pandas as pd 
from IPython.display import display

#%% 
def get_sensor_coefficients(master_sensor_coeffs,
                            df_cast_sensors,
                            raw_data_directory,
                            output_directory):
    """
    Uses the XMLCON file and master sensor coefficient dictionary to execute
    file_widget_v3.coeff_config and identify all sensors that were on the rig 
    throughout the cruise to save a csv file for each sensor with the coefficients 
    for each cast. Saves a second csv file that has a summary highlighting on 
    what cast a sensor was swapped out.
    
    Parameters
    -----------------
    master_sensor_coeffs: dict
    
    df_cast_sensors: pandas.DataFrame
        Contains the sensor and it's serial number on each voltage channel for each cast
        
    raw_data_dictionary: str
        Name of folder containing raw XMLCON files
    
    output_directory: str
        Name of directory to output csv files to
    
    Returns
    -----------------
    int
        Count of number of sensors
    """
    # Identify coefficients for ancillary sensors that have been deployed on the rig during the cruise
    sensor_counts = {}
    for sensor in list(master_sensor_coeffs.keys()):
        count=0
        for i in range(0,len(df_cast_sensors.columns)):
            if sensor in df_cast_sensors.drop_duplicates().iloc[0,i]:
                count = count + 1
        sensor_counts[sensor] = count
        # Determine whether
        if count==0:
            print("No %s on the rig." % sensor)
        if count>0:
            for i in range(0,count):
                coefficient_config = coeff_config(raw_data_directory, {sensor: master_sensor_coeffs[sensor]}, i)
                s = coefficient_config['sensors_df']
                t = coefficient_config['sensors_df_summary']
                display(t)
                s.to_csv(os.path.join(output_directory,'sensor_coeffs_fulltable_%s%s.csv' % (sensor,i)))
                t.to_csv(os.path.join(output_directory,'sensor_coeffs_summarytable_%s%s.csv' % (sensor,i)))
                
    return sensor_counts

#%% 
def file_sensor_config(directory, file):            
    """
    Creates a dictionary of sensors attached to each voltage channel based 
    on the XMLCON file  
    
    Parameters
    ----------
    directory: str
        directory of where sensor configuration files are stored
        
    file: str
        Name of an XMLCON or CNV file to search for sensor information
    
    Returns
    -------
    dict
        Voltage channels on the CTD rig with the sensors and serial numbers 
        attached to each voltage channel
    """
    
    file_extension = Path(file).suffix.upper().replace('.CNV','.XMLCON').replace('.BTL','.XMLCON')
    
    config_xml_file = None
    for fi in Path(directory).iterdir():
        if fi.is_file() and fi.name.lower() == Path(file).with_suffix(file_extension).name.lower():
            config_xml_file = fi
    config_xml = elementTree.parse(os.path.join(directory, config_xml_file))
    config = config_xml.getroot()
    
    # Initialise dictionary to use to store sensor information
    sensor_dict = {}
    # Search XMLCON to find Sensor Array and the number of sensors within the file
    sensor_count = int(config.find('./Instrument/SensorArray').attrib['Size']) # type: ignore
    
    # Loop through the number of sensors present and find it's name, serial number and voltage channel
    for item in range(0,sensor_count):
        voltage_channel = 'v'+str(item-5)
        sensor_type = list(config.find('./Instrument/SensorArray/Sensor[@index="%s"]' % item))[0].tag # type: ignore
        # Find Serial Number
        sensor_sn = config.find('./Instrument/SensorArray/Sensor[@index="%s"]/%s/SerialNumber' % (item, sensor_type)).text # type: ignore
        # Update sensor dictionary
        if type(sensor_sn)==str:
            sensor_dict.update({voltage_channel : sensor_type+'_sn'+sensor_sn})
        else:
            # TODO: Why are we not including the serial number of it is not a string?
            # If it is not a string does not mean it doesn't exists, it is a weird format or is it a number?
            sensor_dict.update({voltage_channel : sensor_type})
    
    return sensor_dict


#%%  
def sensor_config(directory, cruiseID):  
    """
    Parameters
    ------------
        directory: str
            Name of directory where raw files are stored
        
        cruiseID: str
            Cruise ID
        
    Returns
    -------
        dict
            Containing sensor for each cast and highlighting where sensors were swapped out
    """
    files = os.listdir(directory)
    
    df_cast_sensors = pd.DataFrame()
    
    # for file in files:
        # if '.XMLCON' in file.upper():
            # sensor_dict = file_sensor_config(directory, file)
            # df_sensor = pd.DataFrame(sensor_dict, index=[file.lower().replace('.xmlcon','')])
            # df_cast_sensors = pd.concat([df_cast_sensors,df_sensor])
    sensor_conf_extension = "XMLCON"
    xmlcon_files = [str(file) for file in Path(directory).rglob(f"*") if file.suffix.lower() == f'.{sensor_conf_extension.lower()}']
    for fi in xmlcon_files:
        fi_name = Path(fi).name
        sensor_dict = file_sensor_config(directory, fi_name)
        df_sensor = pd.DataFrame(sensor_dict, index=[fi_name.lower().replace('.xmlcon','')])
        df_cast_sensors = pd.concat([df_cast_sensors,df_sensor])

    
    # Find where the sensors were swapped
    label0 = df_cast_sensors.drop_duplicates(keep='first').T.columns.tolist()
    label1 = df_cast_sensors.drop_duplicates(keep='last').T.columns.tolist()
    
    master_labels = {}
    for i in range(0,len(label0)):
        first = label0[i]
        last = label1[i]
        if first != last:
            master_labels[first] = '%s - %s' % (first.replace(cruiseID.lower()+'_',''),last.replace(cruiseID.lower()+'_',''))
        else:
            master_labels[first] = '%s' % (first.replace(cruiseID.lower()+'_',''))
    
    return {'cast_sensors': df_cast_sensors, 
            'cast_labels': df_cast_sensors.drop_duplicates(keep='first').T.rename(columns=(master_labels))
            }
     

#%%
def coeff_config(directory, sensor_coeffs, sensor_no):
    """
    Function returns a dataframe of distinct coefficient combinations from a 
    folder including SBE XMLCON files.
    Aim is to highlight where coefficients are not consistent across a cruise 
    and/or sensors have been swapped out.
    
    Parameters
    -------------
        directory: str
            Name of directory where raw XMLCON files are stored
        
        sensor_coeffs: dict
            A dictionary of of sensor name with their SBE coefficient labels  
            e.g. sensor_coeffs = {'FluoroWetlabWetstarSensor': ['ScaleFactor','Vblank']}  
                 sensor_coeffs = {'OxygenSensor': ['Soc','offset','A','B','C','D0','D1','D2','E','Tau20','H1','H2','H3']}  
        
        sensor_no: int
            Instrument index for multiple sensors of the same type being deployed
            on the rig.
    
    Returns
    -------------
        dict
            Containing full table of the sensor, serial number, calibration date and
            coefficient configurations for each cast in the cruise and a summary 
            table to show on what cast a sensor may have been swapped and the 
            corresponding coefficient configurations throughout the cruise
    """
    # Get the names of all thefiles in the directory
    files = os.listdir(directory)
    
    # Initialise pandas DataFrame to return
    df_out = pd.DataFrame()
    
    for file in files:
        try:
            if '.XMLCON' in file.upper():
                config_xml = elementTree.parse(os.path.join(directory,file))
                config = config_xml.getroot()
                
                # Find sensor name and the name of it's coefficients
                sensor = list(sensor_coeffs)[0]
                sensor_meta = ['SensorType','SerialNumber','CalibrationDate']
                coeff_labels = sensor_coeffs[sensor]
                sensor_no = int(sensor_no)
                
                # List to store sensor name, serial number and calibration date
                coeff_vals = [sensor]
                
                # Get Serial Number and Calibration Date of the sensor from the XMLCON file
                for item in sensor_meta:
                    if item!='SensorType':
                        x = config.findall('./Instrument/SensorArray/Sensor/%s/%s' % (sensor,item))
                        if x[sensor_no].text==None:
                            coeff_vals.append('%s missing from XMLCON file.' % item)
                        else:
                            coeff_vals.append(str(x[sensor_no].text.replace(' ',''))) # type: ignore
                
                # Find each calibration coefficient in the XMLCON file
                for item in coeff_labels:
                    if sensor!='OxygenSensor':
                        y = config.findall('./Instrument/SensorArray/Sensor/%s/%s' % (sensor,item))
                        if y[sensor_no].text==None:
                            coeff_vals.append('%s missing from XMLCON file.' % item)
                        else:
                            coeff_vals.append(float(y[sensor_no].text.replace(' ',''))) # type: ignore
                    else:
                        y = config.findall('./Instrument/SensorArray/Sensor/OxygenSensor/CalibrationCoefficients[@equation="1"]/%s' % item)
                        if y[sensor_no].text==None:
                            coeff_vals.append('%s missing from XMLCON file.' % item)
                        else:
                            coeff_vals.append(float(y[sensor_no].text.replace(' ',''))) # type: ignore
                
                # Create pandas DataFrame with details of the sensor and it's calibration
                df_coeffs = pd.DataFrame(dict(zip(sensor_meta + coeff_labels,coeff_vals)), index=[file.lower().replace('.xmlcon','')])
                # Append information from this sensor to df_out to have all information in one dataframe
                df_out = pd.concat([df_out,df_coeffs])
        except IndexError:
            print("No %s in file %s" % (sensor, file))
                
    # Return a dictionary with all information in a DataFrame and a summary DataFrame
    return {'sensors_df': df_out, 
            'sensors_df_summary': df_out.drop_duplicates().T
            }
    
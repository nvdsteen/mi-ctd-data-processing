# -*- coding: utf-8 -*-
"""
Created on Tue Mar 26 09:35:40 2024

@author: dosullivan1
"""

import numpy as np
import pandas as pd
import math

#%% 
def heave_flagging(df, vel, window):
    """
    Function iterates down the pressure channel (prDM) and flags:
    1) down-cast rows where velocity is below a user defined threshold (default vel = 0.2 m/s)
    2) a user defined window of cycles prior to the velocity threshold being 
       reached (default window = 2),
    3) cycles where pressure is less than the first cycle below the velocity 
       threshold for each entrainment/heave feature.
    
    Parameters:
        df: pandas.DataFrame
        
        vel: int
            velocity threshold value, any down cast rows will be flagged as heave entrainment
        window: int
            window of cycles prior to the velocity threshold being reached
            
    Returns:
        pandas.DataFrame
        With 
        
    """
    dfo = df.copy(deep=True)
    dfo['prDM_QC'] = '0' # Set all to 0
    # Calculate the velocity of the CTD using pressure and time
    dfo['CTDvel'] = dfo['prDM'].diff(1)/dfo['timeS'].diff(1)
    # Identify down cast data with a velocity below the user defined velocity 
    # threshold and set the pressure QC flag as 4 ()
    mask = (dfo['CTDvel']<vel) & (dfo['cast']=='D')
    dfo.loc[mask,'prDM_QC']='4'
    
    # Identify downcast rows where veolcity is above the user defined velocity
    # threshold and set the pressure QC flag as 1
    good_mask = (dfo['CTDvel']>=vel) & (dfo['cast']=='D')
    dfo.loc[good_mask,'prDM_QC']='1'
    

    dfo['id'] = dfo['prDM_QC'].astype(int).diff()
    
    # Find the rows where there are good down casts before the bad flags
    pre_list = dfo[dfo['id']==3].index
    window1_mask = []
    
    for item in pre_list:
        for i in range(0,window):
            window1_mask.append(item-window+i)
    dfo.loc[window1_mask,'prDM_QC']='4'
    
    # Find the rows 
    post_list = dfo[dfo['id']==-3].index
    window2_mask = []
    for item in post_list:
        for i in range(0,window):
            window2_mask.append(item+i)
    dfo.loc[window2_mask,'prDM_QC']='4'
    
    return dfo

#%% 
def bin_data(input_df, cast, zcord, profile_id, params_out, bin_width=1.):
    """
    Function to bin data based on heave flags in the pressure channel.
    Data are binned between +/-0.5 of the zcord using numeric mean.

    Parameters: 
        input_df: pandas.DataFrame
            Profile data at 2Hz
        cast: str
            'D' or 'U' to specify if data should be subsetted for heave 
            entrainment on the downcast or upcast
            
        zcord: str
            Provide the z variable for binning the data, defined by the user
            using a widget. Either 'depSM' (measured in metre) or 
            'prDM' (measured in decibar)  
            
        profile_id: str
            Name of column containing the profile name

        bin_width: int | float
            The width of the bins.
            
        params_out: list
            Parameters to output, based on the column names in the screen 2Hz
            dataframe
        
    Returns:
        pandas.DataFrame
    """
    # For data not flagged suspect due to heave entrainment subset for cast specified and copy to working table
    bin_df = input_df[(input_df['cast']==cast) & (input_df['prDM_QC']!=4)].copy(deep=True)

    # Set the z-coordinate column for binning as 'bin'
    # changed for more flexibility, same result for now
    # bin_df['bin'] = bin_df[zcord]+0.5
    # bin_df['bin'] = bin_df['bin'].round(0)
    bins = list(np.arange(0, math.ceil(bin_df[zcord].max())+bin_width, bin_width))
    bin_labels = [bi for bi in bins][1:]
    bin_df["bin"] = pd.cut(bin_df[zcord], bins=bins, labels=bin_labels, right=False)

    # Combine the profile_id and z-cord in a list to set the groupby columns 
    # for the binning command then group by the mean for each bin
    gby = [profile_id,'bin']

    bin_df = bin_df.groupby(gby).mean(numeric_only=True).sort_values(by=gby).reset_index(inplace=False)
    
    bin_df = bin_df.drop(columns=[zcord]).rename(columns={'bin': zcord})
    
    bin_df = bin_df[params_out].rename(columns={'bin': zcord})
    bin_df = bin_df.dropna()
    return bin_df


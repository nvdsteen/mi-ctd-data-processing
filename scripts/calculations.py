# -*- coding: utf-8 -*-
"""
Created on Tue Mar 26 09:32:20 2024

@author: dosullivan1
"""
import numpy as np
from bokeh.models import Label, BoxAnnotation

#%% 
def merc_from_arrays(lats, lons):
    """
    Convert lat/lon to northing/eastings
    
    Parameters:
        lats: Series of int
            Latitude (degrees north)
        lons: Series of int
            Longitude (degrees east)
            
    Returns:
        tuple
        Latitude and longitude in Eastings/Northings format
    """
    
    r_major = 6378137.000
    x = r_major * np.radians(lons)
    scale = x/lons
    y = 180.0/np.pi * np.log(np.tan(np.pi/4.0 + lats * (np.pi/180.0)/2.0)) * scale
    
    return (x, y)

#%%
def oxysol(T,S):
    """
    Calculate oxygen value from temperature and salinity values
    
    Parameters:
        T: int
            temperature value
        
        S: int
            salinity value
        
    Returns:
        int
        Oxygen value
    """
    
    Ts = np.log((298.15 - T)/(273.15 + T))
    A0 = 2.00907
    A1 = 3.22014
    A2 = 4.0501
    A3 = 4.94457
    A4 = -0.256847
    A5 = 3.88767
    
    B0 = -0.00624523
    B1 = -0.00737614
    B2 = -0.010341
    B3 = -0.00817083
    
    C0 = -0.000000488682
    
    o2 = np.exp(A0 + A1*Ts + A2*np.power(Ts,2) + A3*np.power(Ts,3) + A4*np.power(Ts,4) + A5*np.power(Ts,5) + S * (B0 + B1*Ts + B2*np.power(Ts,2) + B3*np.power(Ts,3)) + C0*np.power(S,2))

    return o2

#%%
def tau(T, P, tau20, D1, D2):
    """
    Calculates 
    
    Parameters:
        T: int
        Temperature value
        
        P: int
        Pressure value
        
        tau20: int
        
        D1: int
        
        D2: int
        
    Returns:
        int
        Oxygen
    """
    o1 = tau20 * np.exp(D1 * P + D2 * (T-20))
    
    return o1

#%%       
def convert_longitude_to_decimal(longitude_list):
    """
    Parameters:
        longitude_list: list
        
    Returns:
        list
    """
    longdec = []            
    for line in longitude_list:
        x = line.split( )
        #print(x[5])
        dec = float(x[5])/60
        dec = dec + float(x[4])
        if x[6]=='W':
            dec = dec * -1
        longdec.append(dec)
        
    return longdec

#%% 
def convert_latitude_to_decimal(latitude_list):
    """
    Parameters:
        latitude_list: list
        
    Returns:
        list
    """
    
    latdec = []            
    for line in latitude_list:
        x = line.split( )

        dec = float(x[5])/60
        dec = dec + float(x[4])
        if x[6]=='S':
            dec = dec * -1
        latdec.append(dec)
    
    return latdec

#%%
def splitList(filenames):
    """
    To handle the repeating element of arrayItems and split by key and value
    
    Parmeters:
        filenames:
        
    Returns:
        list
    """
    b = []
      
    for index, value in enumerate(filenames):
        b.append({"index": index, "value": value})
        
    return b

#%%    
def sbe43_oxycalc(V, T, P, S, coef, Vdiff, units):
    """
    
    Parameters:
        V: int or Series of int
            
        T: int or Series of int
        Temperature value
        
        P: int or Series of int
        Pressure value
        
        S: int or Series of int
        Salinity value
        
        coef: dict
        TODO: dont know what this looks like, can't find the place where this is being used for the notebook
            
        Vdiff: int or Series of int
            
        units: str
            Units that oxygen should be outputted in. 
            Should be one of 'umol/L' or 'ml/L'             
        
    Returns:
        int or Series of int
        
    """
    oxy_out = (coef['Soc'] * (V + coef['offset'] + tau(T, P, coef['Tau20'], coef['D1'],
                                                       coef['D2']) * Vdiff)) * oxysol(T,S) * (
                                                           1.0 + coef['A']*T + coef['B']*np.power(T,2) + coef['C']*np.power(T,3)
                                                           ) * np.exp(coef['E']*P/(T+273.15))
    
    if units == 'umol/L':
        oxy_out = oxy_out * 44.66
    elif units == 'ml/L':
        oxy_out = oxy_out
    else:
        oxy_out = 'Unknown units specified. Current options are: "umol/L" or "ml/L"'

    return oxy_out

#%%
def oxyVolts_hysteresis(DF, H1, H2, H3, Voffset):
    """
    Parameters:
        DF:
        H1:
        H2:
        H3:
        Voffset:
        
    Returns:
        Series
        Oxygen voltage corrected for hysteresis
    """
    df = DF.copy(deep=True)
    df['D'] =  1 + (H1 * (np.exp(df['prDM'] / H2) - 1))
    df['C'] = np.exp(-1 * df['timeS'].diff() / H3)
    df['OxygenVolts'] = df['oxy_volts'] + Voffset
    
    out_list = []
    prev_OxygenVolts = df.iloc[0,df.columns.get_loc('OxygenVolts')]
    prev_newOxygenVolts = df.iloc[0,df.columns.get_loc('OxygenVolts')]
    count = 0
    for row in df.itertuples():
        if count == 0:
            out_list.append(np.nan)
            count+=1
        else:
            C = row[df.columns.get_loc('C')+1]
            D = row[df.columns.get_loc('D')+1]
            OxygenVolts = row[df.columns.get_loc('OxygenVolts')+1]
            newOxygenVolts = (OxygenVolts + (prev_newOxygenVolts * C * D) - (prev_OxygenVolts * C)) / D
            out_list.append(newOxygenVolts)
            prev_OxygenVolts = OxygenVolts
            prev_newOxygenVolts = newOxygenVolts
    df['OxnewVolts'] = out_list
    df['oxy_volts_corr'] = df['OxnewVolts'].round(4) - Voffset
    
    return df['oxy_volts_corr']

#%%
def hys_calc_binned(df,o2_adv,H1,H3,coefs):
    """ 
    Function to calculate a binned profile of oxygen conc given a combination 
    of H1, H3 and oxygen alignment values
     
    Parameters:
        df: pandas.DataFrame
        
        o2_adv
        adv
        H1
        H3
        coefs: TODO: dont know what this looks like, can't find the place where this is being used for the notebook
        
    Returns:
        pandas.DataFrame
    """
    H2 = coefs['H2']
    Voffset = coefs['offset']
    # Subset from base dataframe
    full24Hz_df = df.copy(deep=True)
    # Update the voltage alignment
    full24Hz_df['oxy_volts'] = full24Hz_df['oxy_volts'].shift(periods=o2_adv*-24)
    # Recalc the oxygen voltage with hysteresis correction
    full24Hz_df['oxy_volts_corr'] = oxyVolts_hysteresis(full24Hz_df, H1, H2, H3, Voffset)
    # Calculate dV/dt using a 2 second rolling window (48 rows of 24Hz data)
    full24Hz_df['oxy1dV/dt'] = full24Hz_df['oxy_volts'].rolling(48, min_periods=1).mean().diff()/full24Hz_df['timeS'].rolling(48, min_periods=1).mean().diff()
    # Regenerate oxygen concentration with hysteresis corrected sensor voltage
    full24Hz_df['oxy_conc_corr_umol'] = sbe43_oxycalc(full24Hz_df['oxy_volts_corr'],
                                                        full24Hz_df['t090C'],
                                                        full24Hz_df['prDM'],
                                                        full24Hz_df['sal00'],
                                                        coefs,
                                                        full24Hz_df['oxy1dV/dt'],
                                                        'umol/L',
                                                       )
    # Bin data to 1 decibar resolution
    full24Hz_df['bin'] = full24Hz_df['prDM'].round(0)
    bin1dbar_df = full24Hz_df.groupby(['cast','bin']).mean().reset_index()

    return bin1dbar_df    


#%%
def hyst_compare_calc(df,H1,H3,coefs,O2_adv):
    """
    Parameters:
        df: pandas.DataFrame
        
        H1:
        
        H3:
            
        coefs:
        TODO: dont know what this looks like, can't find the place where this is being used for the notebook
            
        O2_adv:
    
    Returns:
        list
        
        
    """
    
    # Function to calculate mean difference between down and up-cast for a binned profile given a combination of H1, H3 and oxygen alignment values
    bin1dbar_df = hys_calc_binned(df,O2_adv,H1,H3,coefs)
    
    # Rearrange down and upcast by bin
    compare_df = bin1dbar_df[['cast','bin','oxy_conc_corr_umol']].pivot('bin','cast','oxy_conc_corr_umol')
    # Calculate mean difference between up and down cast by depth
    diff = compare_df['D'].sub(compare_df['U']).mean()
    
    return [O2_adv, H1, H3, diff]

#%%   
def get_water_mass_label(water_mass_type):
    saiw = {'parameters': {'salinity': [34.78,34.99,34.8,34.6,34.78], 
                           'temperature': [6.6,5,4,5.5,6.6]},
            'label': Label(x=34.8, y=5.3, x_units="data", 
                                        y_units="data", text="SAIW",
                                        text_align='center', 
                                        text_baseline='middle')
            }
    lsw = {'parameters': {'salinity': [34.8,34.89,34.89,34.8,34.8], 
                           'temperature': [3.0,3.0,3.6,3.6,3.0]},
            'label': Label(x=34.85, y=3.3, x_units="data", 
                                        y_units="data", text="LSW", 
                                        text_align='center', 
                                        text_baseline='middle')
            }
    neadw = {'parameters': {'salinity': [34.89,34.89,34.89,34.94,34.94], 
                           'temperature':  [2.03,2.03,2.5,2.5,2.03]},
            'label': Label(x=34.925, y=2.5, x_units="data", 
                                        y_units="data", text="NEADW", 
                                        text_align='center', 
                                        text_baseline='middle')
            }
    ldw = {'box': BoxAnnotation(top=2.5, right=34.9, 
                                             fill_color='red', fill_alpha=0.1, 
                                             line_color='red'),
           'label': Label(x=34.8, y=2, x_units="data",
                                       y_units="data", text="AABW/LDW", 
                                       text_align='center', 
                                       text_baseline='middle')
           }
    isow = {'box': BoxAnnotation(top=2.5, left=34.98, 
                                              fill_color='red', fill_alpha=0.1),
           'label': Label(x=35.3, y=2.0, x_units="data", 
                                       y_units="data", text="ISOW", 
                                       text_align='center', 
                                       text_baseline='middle')
           
           }

    if water_mass_type == 'SAIW':
        return saiw
    elif water_mass_type == 'LSW':
        return lsw
    elif water_mass_type == 'NEADW':
        return neadw
    elif water_mass_type == 'LDW':
        return ldw
    elif water_mass_type == 'ISOW':
        return isow
    else:
        print('Water type note recognised. Please try an alternative water mass.')
        return None
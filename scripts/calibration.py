# -*- coding: utf-8 -*-
"""
Created on Tue Mar 26 09:27:17 2024

@author: dosullivan1
"""
from scipy import stats
import numpy as np
import pandas as pd

from bokeh.models import CategoricalColorMapper, ColumnDataSource
from bokeh.plotting import figure
from bokeh.layouts import gridplot, column, row
from bokeh.models.widgets import DataTable, TableColumn

#%%
def cal_regression(df, samp, ctd, factor, qc):
    # TODO: Should NOT be returning multiple items from a function
    # TODO: Need to find where this function is being used so I can understand the parameters
    """
    
    Parameters:
        df: pandas.DataFrame
        
        samp:
            
        ctd:
            
        factor:
            
        qc:
        
    Returns:
        'Sample','Sensor','Factor','Slope','Intercept','R value','P value','Std Error','n','Mean residual','RMS','Correction type','Corrected mean residual','Corrected RMS'
        
    """    
    data = df
    x = samp
    y = ctd
    z = factor
    # Construct the calibration dataset for use in the regression analysis
    cal = pd.DataFrame()
    cal[x] = data[x].copy(deep=True)
    cal[y] = data[y].copy(deep=True)
    cal[z] = data[z].copy(deep=True)
    cal[qc] = data[qc].copy(deep=True)
    # Remove data pairings where flag is bad
    cal = cal[cal[qc]!='4']
    
    # Calculate the residual as the difference between a lab calculated sample value and the concurrent sensor measurement from bottle firing
    cal['residual'] = cal[x]-cal[y]
    
    # Calculate RMS and residual statistics on the uncorrected calibration data set
    mean_residual = cal['residual'].mean()
    n = cal['residual'].count()
    RMS = np.sqrt((cal['residual'].mul(cal['residual']).sum())/float(n))
    
    # Run a linear regression analysis of the factor against the residual
    slope, intercept, r_value, p_value, std_err = stats.linregress(cal[z], cal['residual'])
    
    # Depedning on the significance of results (5% taken as level of confidence)
    if p_value < 0.05:
        # Apply linear regression slope and intercept co-efficients to the calibration dataset as the correction
        cal['linear_cal'] = cal[y] + slope * cal[z] + intercept
        cal_type = 'linear'
        cal['cal_residual'] = cal[x] - cal['linear_cal']
    else:
        # Apply the mean residual as an offset correction
        cal['offset_cal'] = cal[y] + mean_residual
        cal_type = 'offset'
        cal['cal_residual'] = cal[x] - cal['offset_cal']
    
    # Recalculate RMS statistics on the residuals calculated from the sample minus the corrected CTD
    mean_residual_cal = cal['cal_residual'].mean()
    n_cal = cal['cal_residual'].count()
    RMS_cal = np.sqrt(cal['cal_residual'].mul(cal['cal_residual']).sum()/float(n_cal))
        
    return x, y, z, slope, intercept, r_value, p_value, std_err, n, mean_residual, RMS, cal_type, mean_residual_cal, RMS_cal


#%%    
def p_plot(src, x, x1, x2, y, xqc):
    # TODO: Need to understand where this is used and what for
    """
    Create a plot
    
    Returns:
        bokeh.figure
    
    """
    # Set up plot figure
    p = figure(plot_width=450, 
            plot_height=300, 
            x_axis_label=x, 
            y_axis_label=y,
            tools="hover,pan,wheel_zoom,box_zoom,reset", 
            toolbar_location='above')
    # Set the colour mapping
    color_mapper = CategoricalColorMapper(factors=['0','1','4'],
                                          palette=['blue','green','red']
                                          )
    # Plot data
    p.circle(x1, y, 
             source = src, 
             color=dict(field=xqc, transform=color_mapper), 
             fill_alpha=0.2, 
             size=5)
    p.circle(x2, y, 
             source = src, 
             color=dict(field=xqc, transform=color_mapper), 
             fill_alpha=0.2, 
             size=5,
             marker='square')
    
    return p

#%%
def p_plot3(src, x, x1, x2, y, xqc):
    # Set up plot figure
    p = figure(width=450, 
            height=300, 
            x_axis_label=x, 
            y_axis_label=y,
            tools="hover,pan,wheel_zoom,box_zoom,reset", 
            toolbar_location='above')
    # Set the colour mapping
    color_mapper = CategoricalColorMapper(factors=['0','1','4'],
                                      palette=['blue','green','red']
                                     )
    # Plot data
    p.circle(x1, y, 
                 source = src, 
                 color=dict(field=xqc, transform=color_mapper), 
                 fill_alpha=0.2, 
                 size=5)
    p.circle(x2, y, 
                 source = src, 
                 color=dict(field=xqc, transform=color_mapper), 
                 fill_alpha=0.2, 
                 size=5,
             marker='square')
    return p

#%%
def cal_plot(src, x, y, xqc):
    """
    Create calibration plot
    
    Parameters:
        src
        x
        y
        xqc
        
    Returns:
        bokeh.figure
    """
    # Set up tooltips for display
    TOOLTIPS = [("index", "$index"),
                ("CTD", "@CTD"),
                ("Bedford", "@Bedford"),
                ("Pressure", "@prDM"),
               ]
    # Set up plot figure
    p = figure(width=450, 
               height=300, 
               x_axis_label=x, 
               y_axis_label=y,
               tools="hover,pan,wheel_zoom,box_zoom,box_select,tap,lasso_select,reset",
               tooltips=TOOLTIPS,
               toolbar_location='above')
    # Set the colour mapping
    color_mapper = CategoricalColorMapper(factors=['0','1','4'],
                                          palette=['blue','green','red']
                                          )
    # Plot data
    p.circle(x, y, 
             source = src, 
             color=dict(field=xqc, transform=color_mapper), 
             fill_alpha=0.2, 
             size=5)
    
    return p


#%%
def cal_table_gen(cal_df, sample, comparisons, qc):
    # TODO: Can't find this being used - check Calibrations Notebook
    """
    Carry out linear regressions on the calibration dataset using the 
    cal_regression function and return a DataFrame of the results.
    
    Parameters:
        cal_df: pandas.DataFrame
        
        sample
        
        comparisons
        
        qc
    Returns:
        pandas.DataFrame
        
    """
    # Initiate list to store output in
    collect = []
    for key in comparisons.keys():
        for factor in comparisons[key]:
            collect.append(cal_regression(cal_df, sample, key, factor, qc))
    c = ['Sample','Sensor','Factor','Slope','Intercept','R value','P value','Std Error','n','Mean residual','RMS','Correction type','Corrected mean residual','Corrected RMS']
    cal_stats = pd.DataFrame(collect, columns = c)
    cal_stats = cal_stats.round({'Slope': 6, 'Intercept': 6, 'R value': 4, 'Std Error': 4, 'Mean residual': 5, 'RMS': 4, 'Corrected RMS': 4})
    for item in ['P value','Corrected mean residual']:
        cal_stats[item+'format'] = cal_stats[item].apply('{:.2e}'.format)
    cal_stats = cal_stats.sort_values(by=['Sensor','P value'])
    
    return cal_stats

#%%
def calibration(df, metadata, sample, comparisons, qc):
    """
    Parameters:
        df:
        metadata:
        sample:
        comparisons:
        qc:
            
    Returns:
        
    """
    subset = metadata
    subset.append(sample)
    
    for key in comparisons.keys():
        if key not in subset:
            subset.append(key)
        for val in comparisons[key]:
            if val not in subset:
                subset.append(val)
    subset.append(qc)
                
    # Generate calibration dataset as a subset of the full bottle dataset
    cal_df = df[df[sample].notnull()][subset].copy(deep=True)
    cal_df = cal_df.reset_index(drop=True)
    for item in subset:
        if item not in metadata and item!=qc:
            cal_df[item] = cal_df[item].astype(float)
    cal_df[qc] = cal_df[qc].astype(int).astype(str)
    
    for key in comparisons.keys():
        cal_df[key+'_residual'] = cal_df[sample] - cal_df[key]
    
    # Carry out linear regressions on the calibration dataset
    collect = []
    
    for key in comparisons.keys():
        for factor in comparisons[key]:
            collect.append(cal_regression(cal_df, sample, key, factor, qc))
        
    c = ['Sample','Sensor','Factor','Slope','Intercept','R value','P value','Std Error','n','Mean residual','RMS','Correction type','Corrected mean residual','Corrected RMS']
    
    cal_stats = pd.DataFrame(collect, columns = c)
    
    src = ColumnDataSource(cal_df)
    src_cal = ColumnDataSource(cal_stats)
    
    clist = []
    for key in comparisons.keys():
        rlist = []
        rlist.append(cal_plot(src,sample,key,qc))
        for i in comparisons[key]:
            rlist.append(cal_plot(src,i,key+'_residual',qc))
        clist.append(rlist)
    
    grid = gridplot(clist)
    
    cols = []
    for item in c:
        cols.append(TableColumn(field=item, title=item),)
    
    data_table = DataTable(source=src_cal, columns = cols, width=1600)
    
    plots = column(row(grid), row(data_table))

    return plots, cal_stats

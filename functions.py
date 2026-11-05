"""Shared helper functions for the thesis notebooks.

Import with `from functions import *` from a notebook in the repository root.
"""
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sn
plt.style.use("ggplot")
import numpy as np 
import matplotlib.dates as mdates
import os
import datetime
import xarray as xr
import rioxarray
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import math
from calendar import monthrange
from math import comb, log
import statsmodels.api as sm
import pingouin as pg
import geopandas as gpd
from shapely.geometry import shape, Point

# ---------------------------------------------------------------------------
# Paths. Everything is resolved relative to this file (the repository root),
# so the notebooks work regardless of the machine or working directory.
# ---------------------------------------------------------------------------
REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(REPO_ROOT, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
FIGURES_DIR = os.path.join(REPO_ROOT, "figures")
COUNTY_BOUNDARIES = os.path.join(RAW_DIR, "boundaries", "California_County_Boundaries.geojson")
USA_SHAPEFILE = os.path.join(RAW_DIR, "boundaries", "USA.shp")
GRIDDED_DIR = os.path.join(RAW_DIR, "gridded_climate")

# ---------------------------------------------------------------------------
# Dataset creation helpers (gridded climate). These were used while exploring
# NOAA/GPCP gridded products; the final thesis dataset uses the NOAA
# Climate-at-a-Glance county series instead (see 01_dataset_creation.ipynb).
# ---------------------------------------------------------------------------
def get_monthly_temp(file=os.path.join(GRIDDED_DIR, "temperature_anomaly", "air.2x2.250.mon.anom.comb.nc"), county=None):
    ds = xr.open_dataset(file)
    monthly_temp = pd.DataFrame({"temp":[]})
    if county == None:
        shp_data = gpd.read_file(USA_SHAPEFILE)
        aoi = shp_data[shp_data['state_code']=='CA'].reset_index()
    else:
        county_boundary = gpd.read_file(COUNTY_BOUNDARIES)
        aoi = county_boundary.loc[county_boundary["COUNTY_NAME"]==county]["geometry"].reset_index(drop=True).at[0]
    ds = ds.assign_coords(lon=(((ds.lon + 180) % 360) - 180))
    bounds = aoi.bounds
    min_lat = bounds.miny.values[0]
    max_lat = bounds.maxy.values[0]
    min_lon = bounds.minx.values[0]
    max_lon = bounds.maxx.values[0]
    ds = ds.where((ds.lat > min_lat) & (ds.lat < max_lat), drop=True)
    ds = ds.where((ds.lon > min_lon) & (ds.lon < max_lon), drop=True)
    ds = ds.where((ds.time > np.datetime64("2014-12")) & (ds.time < np.datetime64("2023")), drop=True)
    temps = np.average(np.average(ds.air.data, axis=1), axis=1)
    monthly_temp["temp"] = temps
    ind = pd.date_range(start='1/1/2015', end='1/1/2023', freq='M')
    monthly_temp = monthly_temp.set_index(ind)
    return monthly_temp

from tqdm import tqdm
def get_california_average(ds, aoi):
    ds = ds.assign_coords(longitude=(((ds.longitude + 180) % 360) - 180))
    bounds = aoi.bounds
    min_lat = bounds.miny.values[0]
    max_lat = bounds.maxy.values[0]
    min_lon = bounds.minx.values[0]
    max_lon = bounds.maxx.values[0]
    ds = ds.where((ds.latitude > min_lat) & (ds.latitude < max_lat), drop=True)
    ds = ds.where((ds.longitude > min_lon) & (ds.longitude < max_lon), drop=True)
    ds = ds['precip'].rio.write_crs("epsg:4326", inplace=True)
    ds_clipped = ds.rio.clip(geometries = aoi.geometry.values, crs= aoi.crs, drop=True, invert=False,all_touched=True)
    return np.nanmean(ds_clipped.data)

def get_precip_monthly(data_dir):
    # initialized df 
    ca_monthly_df = pd.DataFrame({"Precipitation":[]})
    # for file in data dir
    files = os.listdir(data_dir)
    shp_data = gpd.read_file(USA_SHAPEFILE)
    aoi = shp_data[shp_data['state_code']=='CA'].reset_index()
    for file in tqdm(files):
        if os.path.isfile(os.path.join(data_dir, file)): #gpcp_v02r03_monthly_d201501_c20170616
            # parse filename to get month-year date time
            month = file.split("monthly_d")[1][4:6]
            year = file.split("monthly_d")[1][0:4]
            month_calc = int(month)+1
            year_calc = int(year)
            if month_calc == 13: month_calc = 1; year_calc= year_calc+1
            day = (datetime.date(int(year_calc), int(month_calc), 1) - datetime.date(int(year), int(month), 1)).days
            date = pd.to_datetime(month+"/"+str(day)+"/"+year, format="%m/%d/%Y" )#datetime.date(int(year), int(month))
            ds = xr.open_dataset(os.path.join(data_dir, file))
            # get california average
            average = get_california_average(ds, aoi)
            # save to df
            ca_monthly_df.at[date, "Precipitation"] = average
    return ca_monthly_df

def get_monthly_soil(file=os.path.join(GRIDDED_DIR, "soil_moisture", "soilw.mon.mean.nc"), county=None):
    ds = xr.open_dataset(file)
    monthly_temp = pd.DataFrame({"soil moisture":[]})
    if county == None:
        shp_data = gpd.read_file(USA_SHAPEFILE)
        aoi = shp_data[shp_data['state_code']=='CA'].reset_index()
        bounds = aoi.bounds
        min_lat = bounds.miny.values[0]
        max_lat = bounds.maxy.values[0]
        min_lon = bounds.minx.values[0]
        max_lon = bounds.maxx.values[0]
    else:
        county_boundary = gpd.read_file(COUNTY_BOUNDARIES)
        aoi = shape(county_boundary.loc[county_boundary["COUNTY_NAME"]==county]["geometry"].reset_index(drop=True).at[0])
        bounds = aoi.bounds
        min_lon = bounds[0]
        max_lon = bounds[2]
        min_lat = bounds[1]
        max_lat = bounds[3]

    ds = ds.assign_coords(lon=(((ds.lon + 180) % 360) - 180))
    ds = ds.where((ds.lat > min_lat) & (ds.lat < max_lat), drop=True)
    ds = ds.where((ds.lon > min_lon) & (ds.lon < max_lon), drop=True)
    ds = ds.where((ds.time > np.datetime64("2014-12")) & (ds.time < np.datetime64("2023")), drop=True)
    temps = np.average(np.nanmean(ds.soilw.data, axis=1), axis=1)
    monthly_temp["soil moisture"] = temps
    ind = pd.date_range(start='1/1/2015', end='1/1/2023', freq='M')
    monthly_temp = monthly_temp.set_index(ind)
    return monthly_temp


# ---------------------------------------------------------------------------
# Exploration helpers (used in 02_dataset_exploration / 03_treatment_analysis)
# ---------------------------------------------------------------------------
def convert_acres_degrees(acres, latitude):
    """Radius (in decimal degrees of longitude) of a circle with area `acres`.

    Used only to size the map markers in the prescribed-vs-wildfire maps.
    """
    r_meters = math.sqrt((4046*acres)/math.pi)
    r_decimal = r_meters / (111.32 * 1000 * math.cos(latitude * (math.pi / 180)))
    return r_decimal

def run_stats(data, target_col, predictor_cols, alt="two-sided"):
    """For each boolean column in `predictor_cols`, compare `target_col` between
    rows where it is True (x) and False (y) with a Welch t-test and a
    Mann-Whitney U test (pingouin). alt="less" tests whether x < y.
    Returns (mwu_table, ttest_table)."""
    res_mwu = {col:None for col in predictor_cols}
    res_t = {col:None for col in predictor_cols}
    for col in predictor_cols:
        x = data[data[col]][target_col]
        y = data[~data[col]][target_col]
        res_t[col] = pg.ttest(x,y)
        res_mwu[col] = pg.mwu(x,y, alternative=alt)
    mwu = pd.concat(res_mwu)
    t = pd.concat(res_t)
    return mwu, t

def build_boxplots(data, target, predictors):
    nrows = max(int(np.ceil(len(predictors)/2)),2)
    ncols = 2
    figsize_x = ncols*6
    figsize_y = nrows*3
    fig, ax = plt.subplots(nrows, ncols, figsize=(figsize_x,figsize_y))
    curr_row = 0
    curr_col = 0
    for i in range(len(predictors)):
        data[[predictors[i], "incident_acres_burned"]].boxplot(by=[predictors[i]], ax=ax[curr_row, curr_col])
        ax[curr_row, curr_col].set_ylabel("Wildland Acres")
        ax[curr_row, curr_col].set_xlabel(predictors[i])
        ax[curr_row, curr_col].set_yscale('symlog') 
        ax[curr_row, curr_col].set_title(predictors[i])
        if curr_col  == 1: 
            curr_row += 1
            curr_col = 0
        else:
            curr_col += 1
    if curr_col != 0 :
        fig.delaxes(ax[curr_row, curr_col])
    if (curr_row==nrows-1) and (curr_col == 0):
        fig.delaxes(ax[curr_row, curr_col])
        fig.delaxes(ax[curr_row, curr_col+1])
    if (curr_row==nrows-2):
        fig.delaxes(ax[curr_row+1, curr_col])
        fig.delaxes(ax[curr_row+1, 0])
    plt.subplots_adjust(left=0.1, bottom=0.1, right=0.9, top=0.9, wspace=0.4,hspace=0.5)
    plt.suptitle("")
    plt.show()
    return fig

def scatter_plots(data, target, predictors):
    nrows = int(np.ceil(len(predictors)/2))
    ncols = 2
    figsize_x = ncols*6
    figsize_y = nrows*3
    fig, ax = plt.subplots(nrows, ncols, figsize=(figsize_x,figsize_y))
    curr_row = 0
    curr_col = 0
    for i in range(len(predictors)):
        ax[curr_row, curr_col].scatter( data[predictors[i]], data[target])
        ax[curr_row, curr_col].set_ylabel("wildland fire acres burned")
        ax[curr_row, curr_col].set_xlabel(predictors[i])
        ax[curr_row, curr_col].set_title(target+" vs "+predictors[i])
        if curr_col  == 1: 
            curr_row += 1
            curr_col = 0
        else:
            curr_col += 1
    if curr_col != 0:
        fig.delaxes(ax[curr_row, curr_col])
    plt.subplots_adjust(left=0.1, bottom=0.1, right=0.9, top=0.9, wspace=0.4,hspace=0.5)
    plt.show()
    return fig

def plot_rx_wild_fires(prescribed, wild, prescribed_year, wild_years):
    nrows = max(int(np.ceil(len(wild_years)/2)),2)
    ncols = 2
    figsize_x = ncols*6
    figsize_y = nrows*6
    fig, ax = plt.subplots(nrows, ncols, figsize=(figsize_x,figsize_y), subplot_kw={'projection': ccrs.PlateCarree()})
    curr_row = 0
    curr_col = 0
    prescribed = prescribed.loc[prescribed["year"]==prescribed_year]
    poly = gpd.read_file(COUNTY_BOUNDARIES)["geometry"]
    for year in wild_years:
        curr_wild = wild.loc[wild["year"].astype(int)==year]
        ax[curr_row,curr_col].add_feature(cfeature.LAND)
        ax[curr_row,curr_col].add_feature(cfeature.OCEAN)
        ax[curr_row,curr_col].add_feature(cfeature.COASTLINE)
        ax[curr_row,curr_col].add_feature(cfeature.BORDERS, linestyle=':')
        ax[curr_row,curr_col].add_feature(cfeature.LAKES, alpha=0.5)
        ax[curr_row,curr_col].add_feature(cfeature.RIVERS)
        ax[curr_row,curr_col].add_feature(cfeature.STATES.with_scale('10m'))
        #ax[curr_row,curr_col].add_patch(PolygonPatch(poly))
        #plot prescribed
        ax[curr_row,curr_col].scatter(prescribed["lon_center"], 
                                      prescribed["lat_center"], 
                                      alpha=0.4, 
                                      s=prescribed["acres_decimal"], 
                                      label="prescribed",
                                      c="blue", 
                                      transform=ccrs.PlateCarree())
        #plot wildfire
        ax[curr_row,curr_col].scatter(curr_wild["incident_longitude"], 
                                      curr_wild["incident_latitude"], 
                                      alpha=0.4, 
                                      s=curr_wild["acres_decimal"],#np.log(1+curr_wild["incident_acres_burned"]), 
                                      label="wildland",
                                      c="red", 
                                      transform=ccrs.PlateCarree())
        ax[curr_row,curr_col].set_xlim(-126, -114)
        ax[curr_row,curr_col].set_ylim(32, 43)
        ax[curr_row,curr_col].set_title(str(prescribed_year)+" Prescribed Fires vs "+ str(year)+" Wild Fires")
        ax[curr_row,curr_col].set_ylabel("Latitude", fontsize=14)
        ax[curr_row,curr_col].set_xlabel("Longitude", fontsize=14)
        ax[curr_row,curr_col].legend()
        if curr_col  == 1: 
            curr_row += 1
            curr_col = 0
        else:
            curr_col += 1
    if curr_col != 0 :
        fig.delaxes(ax[curr_row, curr_col])
    if (curr_row==nrows-1) and (curr_col == 0):
        fig.delaxes(ax[curr_row, curr_col])
        fig.delaxes(ax[curr_row, curr_col+1])
    if (curr_row==nrows-2):
        fig.delaxes(ax[curr_row+1, curr_col])
        fig.delaxes(ax[curr_row+1, 0])
    plt.show()
    return fig


def plot_rx_wild_fires_multi_year(prescribed, wild, years, years_to_plot):
    nrows = max(int(np.ceil(len(years_to_plot)/2)),2)
    ncols = 2
    figsize_x = ncols*6
    figsize_y = nrows*6
    fig, ax = plt.subplots(nrows, ncols, figsize=(figsize_x,figsize_y), subplot_kw={'projection': ccrs.PlateCarree()})
    curr_row = 0
    curr_col = 0
    poly = gpd.read_file(COUNTY_BOUNDARIES)["geometry"]
    wild_colors = ["red", "orange", "yellow"]
    for year in years_to_plot:
        curr_prescribed = prescribed.loc[prescribed["year"]==year]
        ax[curr_row,curr_col].add_feature(cfeature.LAND)
        ax[curr_row,curr_col].add_feature(cfeature.OCEAN)
        ax[curr_row,curr_col].add_feature(cfeature.COASTLINE)
        ax[curr_row,curr_col].add_feature(cfeature.BORDERS, linestyle=':')
        ax[curr_row,curr_col].add_feature(cfeature.LAKES, alpha=0.5)
        ax[curr_row,curr_col].add_feature(cfeature.RIVERS)
        ax[curr_row,curr_col].add_feature(cfeature.STATES.with_scale('10m'))
        #ax[curr_row,curr_col].add_patch(PolygonPatch(poly))
        #plot prescribed
        ax[curr_row,curr_col].scatter(curr_prescribed["lon_center"], 
                                      curr_prescribed["lat_center"], 
                                      alpha=0.8, 
                                      #edgecolors= "black",
                                      s=curr_prescribed["acres_decimal"]*100, 
                                      label="prescribed",
                                      c="blue", 
                                      transform=ccrs.PlateCarree())
        #plot wildfire
        years_to_plot = years[years.index(year):years.index(year)+3]
        for wild_year in years_to_plot:
            curr_wild = wild.loc[wild["year"].astype(int)==wild_year]
            ax[curr_row,curr_col].scatter(curr_wild["incident_longitude"], 
                                        curr_wild["incident_latitude"], 
                                        alpha=0.8, 
                                        #edgecolors= "black",
                                        s=curr_wild["acres_decimal"]*100,
                                        label="wildland "+str(wild_year),
                                        c=wild_colors[years_to_plot.index(wild_year)], 
                                        transform=ccrs.PlateCarree())
        ax[curr_row,curr_col].set_xlim(-126, -114)
        ax[curr_row,curr_col].set_ylim(32, 43)
        ax[curr_row,curr_col].set_title(str(year)+" Prescribed Fires vs "+ str(years_to_plot[0])+"-"+str(years_to_plot[-1])+" Wild Fires")
        ax[curr_row,curr_col].set_ylabel("Latitude", fontsize=14)
        ax[curr_row,curr_col].set_xlabel("Longitude", fontsize=14)
        ax[curr_row,curr_col].legend()
        if curr_col  == 1: 
            curr_row += 1
            curr_col = 0
        else:
            curr_col += 1
    if curr_col != 0 :
        fig.delaxes(ax[curr_row, curr_col])
    plt.tight_layout()
    plt.show()
    return fig

def plot_rx_wild_fires_singles(prescribed, wild, years):
    nrows = max(int(np.ceil(len(years)/2)),2)
    ncols = 2
    figsize_x = ncols*6
    figsize_y = nrows*6
    fig, ax = plt.subplots(nrows, ncols, figsize=(figsize_x,figsize_y), subplot_kw={'projection': ccrs.PlateCarree()})
    curr_row = 0
    curr_col = 0
    poly = gpd.read_file(COUNTY_BOUNDARIES)["geometry"]
    for year in years:
        curr_prescribed = prescribed.loc[prescribed["year"]==year]
        curr_wild = wild.loc[wild["year"].astype(int)==year]
        ax[curr_row,curr_col].add_feature(cfeature.LAND)
        ax[curr_row,curr_col].add_feature(cfeature.OCEAN)
        ax[curr_row,curr_col].add_feature(cfeature.COASTLINE)
        ax[curr_row,curr_col].add_feature(cfeature.BORDERS, linestyle=':')
        ax[curr_row,curr_col].add_feature(cfeature.LAKES, alpha=0.5)
        ax[curr_row,curr_col].add_feature(cfeature.RIVERS)
        ax[curr_row,curr_col].add_feature(cfeature.STATES.with_scale('10m'))
        #ax[curr_row,curr_col].add_patch(PolygonPatch(poly))
        #plot prescribed
        ax[curr_row,curr_col].scatter(curr_prescribed["lon_center"], 
                                      curr_prescribed["lat_center"], 
                                      alpha=0.4, 
                                      s=curr_prescribed["acres_decimal"]*100, 
                                      label="prescribed",
                                      c="blue", 
                                      transform=ccrs.PlateCarree())
        #plot wildfire
        ax[curr_row,curr_col].scatter(curr_wild["incident_longitude"], 
                                      curr_wild["incident_latitude"], 
                                      alpha=0.4, 
                                      s=curr_wild["acres_decimal"]*100,#np.log(1+curr_wild["incident_acres_burned"]), 
                                      label="wildland",
                                      c="red", 
                                      transform=ccrs.PlateCarree())
        ax[curr_row,curr_col].set_xlim(-126, -114)
        ax[curr_row,curr_col].set_ylim(32, 43)
        ax[curr_row,curr_col].set_title(str(year)+" Prescribed Fires vs "+ str(year)+" Wild Fires")
        ax[curr_row,curr_col].set_ylabel("Latitude", fontsize=14)
        ax[curr_row,curr_col].set_xlabel("Longitude", fontsize=14)
        ax[curr_row,curr_col].legend()
        if curr_col  == 1: 
            curr_row += 1
            curr_col = 0
        else:
            curr_col += 1
    if curr_col != 0 :
        fig.delaxes(ax[curr_row, curr_col])
    plt.tight_layout()
    plt.show()
    return fig

# ---------------------------------------------------------------------------
# Time series helpers (used in 04_time_series_analysis)
# ---------------------------------------------------------------------------


def graph_timeseries(df, cols, logs, ylabs):
    df = df[cols]
    nrows = int(np.ceil(len(cols)/2))
    ncols = 2
    figsize_x = ncols*6
    figsize_y = nrows*3
    fig, ax = plt.subplots(nrows, ncols, figsize=(figsize_x,figsize_y))
    curr_row = 0
    curr_col = 0
    for i in range(len(cols)):
        ax[curr_row, curr_col].plot(df[cols[i]], label=cols[i])
        ax[curr_row, curr_col].xaxis.set_major_locator(mdates.YearLocator())
        ax[curr_row, curr_col].set_xticklabels(ax[curr_row, curr_col].get_xticklabels(), rotation=75)
        ax[curr_row, curr_col].set_title("Monthly Time Series of "+cols[i])
        if logs[i]: 
            ax[curr_row, curr_col].set_yscale('log')
        ax[curr_row, curr_col].set_ylabel(ylabs[i])
        if curr_col  == 1: 
            curr_row += 1
            curr_col = 0
        else:
            curr_col += 1
    if curr_col != 0:
        fig.delaxes(ax[curr_row, curr_col])
    plt.subplots_adjust(left=0.1, bottom=0.1, right=0.9, top=0.9, wspace=0.4,hspace=0.4)
    plt.show()
    return fig

def autocorrelations(df, cols = None):
    if cols: df = df[cols]
    nrows = int(np.ceil(len(df.columns)/2))
    ncols = 2
    figsize_x = ncols*6
    figsize_y = nrows*3
    fig, ax = plt.subplots(nrows, ncols, figsize=(figsize_x,figsize_y))
    curr_row = 0
    curr_col = 0
    best_lag = {col: 0 for col in df.columns}
    min_corr = {col: 0 for col in df.columns}
    max_corr = {col: 0 for col in df.columns}
    for i in range(len(df.columns)):
        corr = sm.tsa.stattools.ccf(df[df.columns[i]].dropna(), df[df.columns[i]].dropna(), adjusted=False)

        corrs = corr[:24]
        min_corr[df.columns[i]] = min(corrs)
        max_corr[df.columns[i]] = max(corrs)
        best_lag[df.columns[i]] = np.argmax(corrs)

        ax[curr_row, curr_col].plot(corrs)
        ax[curr_row, curr_col].set_xlabel("Lag")
        ax[curr_row, curr_col].set_ylabel("Correlation")
        ax[curr_row, curr_col].set_title("Autocorrelation of "+df.columns[i])
        
        if curr_col  == 1: 
            curr_row += 1
            curr_col = 0
        else:
            curr_col += 1
    if curr_col != 0:
        fig.delaxes(ax[curr_row, curr_col])
    plt.subplots_adjust(left=0.1, bottom=0.1, right=0.9, top=0.9, wspace=0.4,hspace=0.4)
    plt.show()
    results_df = pd.DataFrame([best_lag, min_corr, max_corr], index = ["best lag", "min R", "max R" ])
    return fig, results_df.round(3)

def crosscorrelations(df, cols = None, target = None):
    if cols: df = df[cols]
    nrows = int(np.ceil(comb(len(df.columns),2)/2))
    ncols = 2
    figsize_x = ncols*6
    figsize_y = nrows*3
    fig, ax = plt.subplots(nrows, ncols, figsize=(figsize_x,figsize_y))
    curr_row = 0
    curr_col = 0
    best_lag = {}
    min_corr = {}
    max_corr = {}
    for i in range(len(df.columns)):
        for j in range(i+1, len(df.columns)):
            corr = sm.tsa.stattools.ccf(df[df.columns[i]].dropna(), df[df.columns[j]].dropna(), adjusted=False)

            # Remove padding and reverse the order
            corrs = corr[0:(len(df[df.columns[i]])+1)][::-1][:-1][:24]
            min_corr[(df.columns[i], df.columns[j])] = min(corrs)
            max_corr[(df.columns[i], df.columns[j])] = max(corrs)
            best_lag[(df.columns[i], df.columns[j])] = np.argmax(corrs)

            ax[curr_row, curr_col].plot(corrs)
            ax[curr_row, curr_col].set_xlabel("Lag")
            ax[curr_row, curr_col].set_ylabel("Correlation")
            ax[curr_row, curr_col].set_title("Crosscorrelation of "+df.columns[i]+ " and "+ df.columns[j])
            
            if curr_col  == 1: 
                curr_row += 1
                curr_col = 0
            else:
                curr_col += 1
    if curr_col != 0:
        fig.delaxes(ax[curr_row, curr_col])
    plt.subplots_adjust(left=0.1, bottom=0.1, right=0.9, top=0.9, wspace=0.4,hspace=0.4)
    plt.show()
    results_df = pd.DataFrame([best_lag, min_corr, max_corr], index = ["best lag", "min R", "max R" ])
    return fig, results_df.round(3)


def crosscorrelations_target(df, cols = None, target = None):
    if cols: df = df[cols]
    nrows = int(np.ceil(len(df.columns)/2))
    ncols = 2
    figsize_x = ncols*6
    figsize_y = nrows*3
    fig, ax = plt.subplots(nrows, ncols, figsize=(figsize_x,figsize_y))
    curr_row = 0
    curr_col = 0
    best_lag = {}
    min_corr = {}
    max_corr = {}
    for i in range(len(df.columns)):
        corr = sm.tsa.stattools.ccf(df[target], df[df.columns[i]], adjusted=False)

        corrs = corr[:24]
        min_corr[(df.columns[i], target)] = min(corrs)
        max_corr[(df.columns[i], target)] = max(corrs)
        best_lag[(df.columns[i], target)] = np.argmax(corrs)

        ax[curr_row, curr_col].plot(corrs)
        ax[curr_row, curr_col].set_xlabel("Lag")
        ax[curr_row, curr_col].set_ylabel("Correlation")
        ax[curr_row, curr_col].set_title("Crosscorrelation of "+df.columns[i]+ " and "+ target)
        
        if curr_col  == 1: 
            curr_row += 1
            curr_col = 0
        else:
            curr_col += 1
    if curr_col != 0:
        fig.delaxes(ax[curr_row, curr_col])
    plt.subplots_adjust(left=0.1, bottom=0.1, right=0.9, top=0.9, wspace=0.4,hspace=0.4)
    plt.show()
    results_df = pd.DataFrame([best_lag, min_corr, max_corr], index = ["best lag", "min R", "max R" ])
    return fig, results_df.round(3)

def crosscorrelations_target_single_plot(df, cols = None, target = None, figsize=(8,6)):
    if cols: df = df[cols]
    fig = plt.figure(figsize=figsize)
    best_pos_lag = {}
    best_neg_lag = {}
    min_corr = {}
    max_corr = {}
    cm = sn.color_palette('husl', n_colors=int(len(cols)/2)) #plt.get_cmap("plasma")
    lines = ['dashed', "solid"]
    for i in range(len(df.columns)):
        if df.columns[i] != target:
            corr = sm.tsa.stattools.ccf(df[target], df[df.columns[i]], adjusted=False, fft=False)
            corrs = corr[:24]
            min_corr[(df.columns[i], target)] = min(corrs)
            max_corr[(df.columns[i], target)] = max(corrs)
            best_pos_lag[(df.columns[i], target)] = np.argmax(corrs)
            best_neg_lag[(df.columns[i], target)] = np.argmin(corrs)
            plt.plot(corrs, label=df.columns[i], color=cm[int(i/2)], linestyle=lines[i%len(lines)])

    plt.xlabel("Lag")
    plt.ylabel("Correlation")
    plt.legend(loc="upper right", )
    plt.show()
    results_df = pd.DataFrame([best_pos_lag, max_corr, best_neg_lag, min_corr], index = ["best pos lag",  "max R", "best neg lag", "min R"])
    return fig, results_df.round(3)

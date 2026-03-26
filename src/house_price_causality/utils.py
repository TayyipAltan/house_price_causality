""" 
De gpkg bestanden hebben ook layers
Voor provincies: provincie_gegeneraliseerd
Voor gemeenten: gemeente_gegeneraliseerd
"""

from pathlib import Path
import pandas as pd
import geopandas as gpd
import requests
from typing import List
import numpy as np


def read_prijsindex_data(file_path: Path) -> pd.DataFrame: 
    """Reads CBS prijsindex data and adjust the column names""" 

    df = pd.read_excel(file_path, sheet_name = 'Tabel 1', header = 2) 
    
    # First three column names are unnamed due to excel layout 
    df.columns = ['Periode', 'Gemeentecode', 'Gemeentenaam'] + list(df.columns[3:]) 
    
    return df.iloc[2:, :].reset_index(drop=True)


def transform_dates_prijsindex_data(df: pd.DataFrame) -> pd.DataFrame:
    """Transform the Periode column of the prijsindex data to a datetime column"""
    
    df['jaar'] = df['Periode'].str.split(" ").str[0].astype(int)
    
    df['kwartaal'] = df['Periode'].str.split(" ").str[1].str[0].astype(int)
    
    df['date'] = pd.PeriodIndex.from_fields(
        year = df['jaar'],
        quarter = df['kwartaal'],
        freq = 'Q'
    ).to_timestamp(how = 'end')

    return df


def rename_prijsindex_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename the columns of the prijsindex data to match the gemeente_gegeneraliseerd data"""
    
    df = df.rename({'Index 2020=100': 'price_index', 'Gemeentenaam': 'gemeente'}, axis=1)
    
    return df[['gemeente', 'kwartaal', 'jaar', 'date', 'price_index']]


def read_yearly_cbs_areas(year: int, layer: str, data_dir: Path) -> gpd.GeoDataFrame:
    """Read CBS gebiedsindeling data for a given year and layer"""
    
    gdf = gpd.read_file(data_dir / f'cbsgebiedsindelingen{year}.gpkg', layer = layer)
    gdf['jaar'] = year
    return gdf


def concatenate_cbs_areas(years: List[int], layer: str, data_dir: Path) -> gpd.GeoDataFrame:
    """Concatenate CBS gebiedsindelingen data for all years"""
    
    gdfs = []
    
    for year in years:
        gdf_year = read_yearly_cbs_areas(year, layer, data_dir)
        
        # ensure same projection
        if gdfs and gdf_year.crs != gdfs[0].crs:
            gdf_year = gdf_year.to_crs(gdfs[0].crs)
            
        gdfs.append(gdf_year)
    
    return gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True), crs=gdfs[0].crs)


def join_municipality_with_province(
    gdf_municipality: gpd.GeoDataFrame, 
    gdf_province: gpd.GeoDataFrame
) -> gpd.GeoDataFrame:
    """Join the gemeente_gegeneraliseerd with the provincie_gegeneraliseerd"""
    
    # The loop is not strictly necessary, but it seems the safest alternative to catch mismatches in geoms
    data = []
    
    for year, municipality_year in gdf_municipality.groupby("jaar"):
        province_year = gdf_province[gdf_province["jaar"] == year]

        yearly_areas_joined = gpd.sjoin(
            municipality_year,
            province_year.assign(geometry=province_year.geometry.buffer(0.001)), #buffer to reduce mismathc
            how="left",
            predicate="within",
            lsuffix="_gemeente",
            rsuffix="_provincie"
        )
        
        if yearly_areas_joined['statnaam__provincie'].isna().any():
            print(f"Warning: Some gemeenten in year {year} could not be matched to a provincie.")
            
        data.append(yearly_areas_joined)

    panel_gdf = gpd.GeoDataFrame(
        pd.concat(data, ignore_index=True),
        crs=gdf_municipality.crs
    ).rename(
        {'statnaam__gemeente': "gemeente", 'jaar__gemeente': 'jaar', 
         'statnaam__provincie': 'provincie'}, axis = 1)
    
    return panel_gdf[['gemeente', 'geometry', 'jaar', 'provincie']]


def read_earthquake_data(starttime: str = "1995-01-01", endtime: str = "2025-12-31") -> pd.DataFrame:
    """Reads earthquake data from the KNMI API"""
    
    url = "https://rdsa.knmi.nl/fdsnws/event/1/query"
    params = {
        "format": "json",
        "starttime": starttime,
        "endtime": endtime,
    }

    data = requests.get(url, params=params).json()

    return pd.json_normalize(data["features"])


def filter_earthquake_data(df: pd.DataFrame) -> pd.DataFrame:
    """Filter the eathquake data to only include relevant events and columns"""
    
    df = df[df['properties.status'] != 'preliminary']
    
    df['timestamp'] = pd.to_datetime(df['properties.time'])
    
    df.rename(columns={'properties.mag': 'magnitude', 'properties.event_type': 'event_type', 'properties.depth': 'depth', 'properties.location': 'location'}, inplace=True)
    
    return df[~df['event_type'].isin(['explosion', 'other event'])]
    

def transform_earthquake_data_to_geopandas(df: pd.DataFrame) -> gpd.GeoDataFrame:
    """Transform the aardbevingen data to a geopandas dataframe"""
    
    gdf = gpd.GeoDataFrame(
        df,
        geometry = gpd.points_from_xy(df['properties.lon'], df['properties.lat']),
        crs = "EPSG:4326"
    )

    gdf = gdf[gdf['properties.status'] != 'preliminary']
    
    gdf['timestamp'] = pd.to_datetime(gdf['properties.time'])

    return gdf[['location', 'magnitude', 'depth', 'event_type', 'geometry', 'timestamp']]
    


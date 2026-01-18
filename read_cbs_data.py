""" 
De gpkg bestanden hebben ook layers
Voor provincies: provincie_gegeneraliseerd
Voor gemeenten: gemeente_gegeneraliseerd"""
#%%
import pandas as pd
import geopandas as gpd
from pandas.core.api import Int32Dtype
import fiona
import requests
from typing import List
import matplotlib.pyplot as plt
import contextily as ctx
import numpy as np

import os

CONFOUNDER_FOLDER_PATH = "./data/confounders/"

#%%
def read_prijsindex_data() -> pd.DataFrame:
    """Reads CBS prijsindex data and adjust the column names"""
    
    df = pd.read_excel('./data/Prijsindex Bestaande Koopwoningen PBK naar gemeente 1995Q1  2025Q3.xlsx',
                        sheet_name = 'Tabel 1', header = 2)

    df.columns = ['Periode', 'Gemeentecode', 'Gemeentenaam'] + list(df.columns[3:])
    
    df = df.iloc[2:, :].reset_index(drop=True)
    
    df['Jaar'] = df['Periode'].str.split(" ").str[0]
    df['Jaar'] = df['Jaar'].astype(int)
    
    df['Kwartaal'] = df['Periode'].str.split(" ").str[1].str[0]
    df = df[df['Kwartaal'] == '4']

    return df.drop(['Periode', 'Kwartaal'], axis=1)


def read_cbs_gebieden_per_jaar(year: int, layer: str) -> gpd.GeoDataFrame:
    """
    Read CBS gebiedsindeling data for a given year
    """
    
    gdf = gpd.read_file(f'./data/cbsgebiedsindelingen{year}.gpkg', layer = layer)
    gdf['jaar'] = year
    return gdf


def concatenate_cbs_gebieden(years: List[int], layer: str) -> gpd.GeoDataFrame:
    """
    Concatenate all CBS gebiedsindelingen data for all years
    """
    
    gdfs = []
    
    for year in years:
        
        gdf_year = read_cbs_gebieden_per_jaar(year, layer)
        
        # ensure same projection
        if gdfs and gdf_year.crs != gdfs[0].crs:
            gdf_year = gdf_year.to_crs(gdfs[0].crs)
            
        gdfs.append(gdf_year)
    
    return gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True), crs=gdfs[0].crs)


def join_gemeente_with_provincie(gdf_gemeente_gegeneraliseerd: gpd.GeoDataFrame, gdf_provincie_gegeneraliseerd: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Join the gemeente_gegeneraliseerd with the provincie_gegeneraliseerd
    """
    gdf_gemeente_gegeneraliseerd = gdf_gemeente_gegeneraliseerd.to_crs(gdf_provincie_gegeneraliseerd.crs)
    
    gdf_gemeente_gegeneraliseerd['geometry'] = gdf_gemeente_gegeneraliseerd.geometry.buffer(0)
    gdf_provincie_gegeneraliseerd['geometry'] = gdf_provincie_gegeneraliseerd.geometry.buffer(0)
    
    # Panel data does not work well with sjoin, so we need to join year by year
    results = []
    
    for year, gemeente_year in gdf_gemeente_gegeneraliseerd.groupby("jaar"):
        provincie_year = gdf_provincie_gegeneraliseerd[gdf_provincie_gegeneraliseerd["jaar"] == year]

        joined = gpd.sjoin(
            gemeente_year,
            provincie_year,
            how="left",
            predicate="within",
            lsuffix="_gemeente",
            rsuffix="_provincie"
        )

        results.append(joined)

    panel_result = gpd.GeoDataFrame(
        pd.concat(results, ignore_index=True),
        crs=gdf_gemeente_gegeneraliseerd.crs
    )
    
    cols_to_drop = ['id__gemeente', 'statcode__gemeente', 'jrstatcode__gemeente', 'rubriek__gemeente', 
                'index__provincie', 'id__provincie', 'statcode__provincie', 'jrstatcode__provincie',  
                'rubriek__provincie', 'jaar__provincie']
    
    return panel_result.drop(cols_to_drop, axis=1)


def read_aardbevingen_data(starttime: str = "1995-01-01", endtime: str = "2025-12-31") -> pd.DataFrame:
    """Reads aardbevingen data from the KNMI deprecated API"""
    
    url = "https://rdsa.knmi.nl/fdsnws/event/1/query"
    params = {
        "format": "json",
        "starttime": starttime,
        "endtime": endtime,
    }

    data = requests.get(url, params=params).json()

    df = pd.json_normalize(data["features"])

    return df


def transform_aardbevingen_data(df_aardbevingen: pd.DataFrame) -> gpd.GeoDataFrame:
    """Transform the aardbevingen data to a geopandas dataframe"""
    
    gdf = gpd.GeoDataFrame(
        df_aardbevingen,
        geometry = gpd.points_from_xy(df_aardbevingen['properties.lon'], df_aardbevingen['properties.lat']),
        crs = "EPSG:4326"
    )

    gdf = gdf[gdf['properties.status'] != 'preliminary']

    return gdf.drop(['type', 'id', 'properties.lat', 'properties.lon', 'properties.catalog', 
                     'properties.contributor', 'properties.mode', 'geometry.coordinates', 
                     'geometry.type', 'properties.status'], axis=1)
    

def load_confounder_data(confounder_file_path: str) -> pd.DataFrame:
    """Create the confounder data from the confounder file"""
    
    df = pd.read_csv(os.path.join(CONFOUNDER_FOLDER_PATH, confounder_file_path), sep=";")

    if df['Perioden'].dtype == 'object':
        # Keeping in preliminary data with * behind the year
        df['Perioden'] = df['Perioden'].str.replace('*', '').astype(int)
    
    if confounder_file_path == 'Bevolking__geslacht__leeftijd__regio_18012026_150430.csv':
        df_pivot = df.pivot_table(index=["Regio's", "Perioden"], columns='Burgerlijke staat', values='Bevolking op 1 januari (aantal)').reset_index()
        df_pivot.index.name = None
        return df_pivot
    else:
        return df
    
    
def merge_confounder_data(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Merge the confounder data with the gdf
    """
    for file in os.listdir(CONFOUNDER_FOLDER_PATH):
        df_confounder = load_confounder_data(file)
        gdf = gdf.merge(df_confounder, left_on=["Regio's", 'Perioden'], 
                        right_on=["Regio's", 'Perioden'], how='left')
    
    return gdf




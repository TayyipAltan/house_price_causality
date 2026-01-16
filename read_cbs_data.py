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

#%%
def read_prijsindex_data() -> pd.DataFrame:
    """Reads CBS prijsindex data and adjust the column names"""
    
    df = pd.read_excel('./data/Prijsindex Bestaande Koopwoningen PBK naar gemeente 1995Q1  2025Q3.xlsx',
                        sheet_name = 'Tabel 1', header = 2)

    df.columns = ['Periode', 'Gemeentecode', 'Gemeentenaam'] + list(df.columns[3:])
    
    df = df.iloc[2:, :].reset_index(drop=True)
    
    df['Gemeentecode'] = df['Gemeentecode'].astype(int)
    
    df['Jaar'] = df['Periode'].str.split(" ").str[0]
    df['Kwartaal'] = df['Periode'].str.split(" ").str[1].str[0]

    return df.drop('Periode', axis=1)

# %%
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
    
    
    # Panel data does not work with sjoin, so we need to join year by year
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
    return panel_result


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

# %%

# %%
gdf_gemeenten = concatenate_cbs_gebieden(list(range(1995, 2026)), "gemeente_gegeneraliseerd")
gdf_provincies = concatenate_cbs_gebieden(list(range(1995, 2026)), "provincie_gegeneraliseerd")

# %%
gdf_provincies[gdf_provincies['jaar'] == 1995]

#%%
gdf_joined = join_gemeente_with_provincie(gdf_gemeenten, gdf_provincies)
gdf_joined.head()
#%%
gdf_joined.shape[0] == gdf_gemeenten.shape[0]

# %%

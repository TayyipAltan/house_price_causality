#%%
import pandas as pd
import geopandas as gpd

# df = pd.read_excel("./data/df.xlsx")

# df.head()

# df1 = pd.read_excel('./data/Prijsindex Bestaande Koopwoningen PBK naar gemeente 1995Q1  2025Q3.xlsx')
# df1.head()
# %%
def read_cbs_gebieden_per_jaar(year: int) -> gpd.GeoDataFrame:
    """
    Read CBS gebiedsindeling data for a given year
    """
    
    gdf = gpd.read_file(f'./data/cbsgebiedsindelingen{year}.gpkg')
    gdf['jaar'] = year
    return gdf

def concatenate_cbs_gebieden(years: list[int]) -> gpd.GeoDataFrame:
    """
    Concatenate all CBS gebiedsindelingen data for all years
    """
    
    gdf = read_cbs_gebieden_per_jaar(years[0])
    
    for year in years[1:]:
        gdf_year = read_cbs_gebieden_per_jaar(year)
        
        if gdf.crs != gdf_year.crs:
            gdf_year = gdf_year.to_crs(gdf.crs)
            
        gdf = pd.concat([gdf, gdf_year], ignore_index=True)
        
    return gdf


# %%
gdf_gebieden = concatenate_cbs_gebieden(list(range(1995, 2026)))

# %%
gdf_gebieden.head()
# %%

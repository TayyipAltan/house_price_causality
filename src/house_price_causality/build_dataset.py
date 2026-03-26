"""
Main script to collect and transform CBS and KNMI data for causality analysis
Date: 25-03-2026
"""

import logging
from pathlib import Path

import geopandas as gpd

from house_price_causality.utils import (
    read_prijsindex_data,
    transform_dates_prijsindex_data,
    rename_prijsindex_columns,
    concatenate_cbs_areas,
    join_municipality_with_province,
    read_earthquake_data,
    filter_earthquake_data,
    transform_earthquake_data_to_geopandas
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

PRIJSINDEX_FILE = RAW_DIR / "Prijsindex Bestaande Koopwoningen PBK naar gemeente 1995Q1  2025Q3.xlsx"

GDF_AREA_FILE = PROCESSED_DIR / "gdf_area_prijs.parquet"
GDF_EARTHQUAKE_FILE = PROCESSED_DIR / "gdf_aardbevingen.parquet"


def main():

    #------------
    # areas and housing prices
    #------------
    df_prijsindex_raw = read_prijsindex_data(PRIJSINDEX_FILE)
    logger.info("Prijsindex data read")

    df_prijsindex = transform_dates_prijsindex_data(df_prijsindex_raw)
    df_prijsindex = rename_prijsindex_columns(df_prijsindex)

    gdf_gemeenten = concatenate_cbs_areas(list(range(1995, 2026)), "gemeente_gegeneraliseerd", RAW_DIR)
    gdf_provincies = concatenate_cbs_areas(list(range(1995, 2026)), "provincie_gegeneraliseerd", RAW_DIR)
    logger.info("Gemeente and province data read and concatenated")
       
    gdf_joined = join_municipality_with_province(gdf_gemeenten, gdf_provincies)
    logger.info("Muncipalities joined with provinces. Num records is equal: %s", len(gdf_gemeenten) == len(gdf_joined))

    if gdf_joined['provincie'].isna().any():
        logger.info("Missing provinces during merge for %s", gdf_joined.loc[gdf_joined['provincie'].isna(), 'gemeente'].unique())
    
    # manually look up and fill in the missing province
    gdf_joined.loc[gdf_joined['provincie'].isna(), 'provincie'] = 'Limburg'

    # Adjust province names for consistency
    gdf_joined['provincie'] = gdf_joined['provincie'].replace({'Fryslân': 'Friesland'})

    logger.info("Merging prijsindex data with joined geography")
    gdf_area_prijs = gdf_joined.merge(df_prijsindex, on=['gemeente', 'jaar'], how='inner')

    #------------
    # Earthquake data
    #------------

    df_aardbevingen = read_earthquake_data()
    logger.info("Earthquake data read from KNMI API")

    # filter and transformation steps
    df_aardbevingen = filter_earthquake_data(df_aardbevingen)
    gdf_aardbevingen = transform_earthquake_data_to_geopandas(df_aardbevingen)

    #-----------
    # Exports (in their original crs)
    #----------

    logger.info("Writing gdf_area_prijs to %s", GDF_AREA_FILE)
    gdf_area_prijs = gdf_area_prijs.set_crs("EPSG:28992", allow_override=True)
    gdf_area_prijs.to_parquet(GDF_AREA_FILE, index=False)

    logger.info("Writing gdf_aardbevingen to %s", GDF_EARTHQUAKE_FILE)
    gdf_aardbevingen = gdf_aardbevingen.set_crs("EPSG:4326", allow_override=True)
    gdf_aardbevingen.to_parquet(GDF_EARTHQUAKE_FILE, index=False)
    

if __name__ == "__main__":
    main()
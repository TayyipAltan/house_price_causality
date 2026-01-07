# House Price Causality

A data analysis project investigating causality relationships in Dutch house prices, using CBS (Statistics Netherlands) administrative boundary data and house price indices.

## Overview

This project processes and analyzes:
- **CBS Gebiedsindelingen**: Administrative boundary data (gemeenten/provincies) from 1995-2026
- **House Price Index**: Prijsindex Bestaande Koopwoningen (PBK) data by municipality
- **Earthquake Data**: Seismic activity data (aardbevingen)

## Project Structure

```
house_price_causality/
├── data/                          # Data files (git-ignored)
│   ├── cbsgebiedsindelingen*.gpkg # CBS administrative boundaries (1995-2026)
│   ├── Prijsindex Bestaande Koopwoningen PBK naar gemeente 1995Q1  2025Q3.xlsx
│   └── aardbevingen.xlsx          # Earthquake data
├── read_cbs_data.py               # Functions for reading CBS data
└── README.md
```

## Setup

### Prerequisites

Install the required Python packages:

```bash
pip install pandas geopandas fiona
```

### Data Files

Place your data files in the `data/` directory:
- CBS gebiedsindelingen GPKG files (one per year: `cbsgebiedsindelingen1995.gpkg`, etc.)
- House price index Excel files
- Any other relevant datasets

**Note**: The `data/` folder is git-ignored. Make sure to obtain the required data files separately.

## Usage

### Reading CBS Gebiedsindelingen Data

The `read_cbs_data.py` module provides functions to read and process CBS administrative boundary data.

#### Reading Data for a Single Year

```python
from read_cbs_data import read_cbs_gebieden_per_jaar
import geopandas as gpd

# Read gemeente (municipality) data for 2020
gdf_2020 = read_cbs_gebieden_per_jaar(2020, "gemeente_gegeneraliseerd")

# Read provincie (province) data for 2020
gdf_provincie_2020 = read_cbs_gebieden_per_jaar(2020, "provincie_gegeneraliseerd")
```

#### Concatenating Multiple Years

```python
from read_cbs_data import concatenate_cbs_gebieden

# Load all gemeente data from 1995 to 2026
years = list(range(1995, 2027))
gdf_all_gemeenten = concatenate_cbs_gebieden(years, "gemeente_gegeneraliseerd")

# Load all provincie data
gdf_all_provincies = concatenate_cbs_gebieden(years, "provincie_gegeneraliseerd")
```

### Available Layers

The CBS gebiedsindelingen GPKG files contain multiple layers:

- `gemeente_gegeneraliseerd`: Municipality boundaries (generalized)
- `provincie_gegeneraliseerd`: Province boundaries (generalized)

To check available layers in a file:

```python
import fiona

layers = fiona.listlayers('./data/cbsgebiedsindelingen1995.gpkg')
print(layers)
```

### Joining Data

The module includes a function stub for joining gemeente and provincie data:

```python
from read_cbs_data import join_gemeente_with_provincie

# Join gemeente data with provincie data (example usage)
# gdf_joined = join_gemeente_with_provincie(gdf_gemeenten, gdf_provincies)
```

## Functions

### `read_cbs_gebieden_per_jaar(year: int, layer: str) -> gpd.GeoDataFrame`

Reads CBS gebiedsindeling data for a specific year and layer.

**Parameters:**
- `year`: Year (e.g., 1995, 2020)
- `layer`: Layer name (`"gemeente_gegeneraliseerd"` or `"provincie_gegeneraliseerd"`)

**Returns:**
- `GeoDataFrame` with a `jaar` column added

### `concatenate_cbs_gebieden(years: list[int], layer: str) -> gpd.GeoDataFrame`

Concatenates CBS gebiedsindeling data for multiple years into a single GeoDataFrame.

**Parameters:**
- `years`: List of years (e.g., `[1995, 1996, 1997]`)
- `layer`: Layer name to read from all files

**Returns:**
- Combined `GeoDataFrame` with all years, ensuring consistent CRS

**Features:**
- Automatically handles coordinate reference system (CRS) differences between years
- Adds a `jaar` column to identify the source year

## Data Sources

- **CBS Gebiedsindelingen**: [Centraal Bureau voor de Statistiek](https://www.cbs.nl/)
- **House Price Index**: CBS Prijsindex Bestaande Koopwoningen (PBK)

## Notes

- All data files should be placed in the `data/` directory
- The data folder is excluded from version control (see `.gitignore`)
- Make sure all GPKG files follow the naming convention: `cbsgebiedsindelingen{year}.gpkg`
- The functions automatically handle CRS transformations when concatenating data from different years

## License

[Add your license information here]

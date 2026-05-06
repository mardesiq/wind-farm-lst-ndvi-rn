1. Environment setup and Drive access

The script begins by mounting Google Drive in the Google Colab environment.
For the execution to work properly, all input files must be previously organized in the Drive, following the paths specified in the code.

In addition, authentication to Google Earth Engine is performed, which will be used to extract environmental variables (LST and elevation).

2. Required file: point shapefile for clustering

Required file in Drive:

SHP_editado1.shp (with auxiliary files: .shx, .dbf, .prj)

Function in the script:
This shapefile contains the base points used for spatial clustering.

Processing:

Read shapefile
Extract latitude and longitude
Convert to CSV

Output generated:

pontos1.csv
3. Required file: wind turbine shapefile

Required file in Drive:

Aerogeradores.shp (with all associated files)

Required fields:

UF
OPERACAO
DATUM_EMP
NOME_EOL

Function in the script:
This file contains the main wind turbine dataset.

Processing:

Filtering by:
State: RN
Condition:
In operation (“Sim”)
Not in operation (“Não”)
Coordinate extraction
Conversion to CSV and back to shapefile

Outputs generated:

resultado_filtrado_com_coords.csv
resultado_filtrado_Sim.shp
resultado_filtrado_Nao.csv
resultado_filtrado_Nao.shp
4. Required file: CSV for clustering

File used:

pontos1.csv (generated in Step 2)

Function in the script:
Perform spatial clustering.

Processing:

Compute nearest-neighbor distances
Identify optimal eps value (elbow method)
Apply DBSCAN algorithm

Outputs generated:

aerogeradores_caatinga_clusterizado1.csv
aerogeradores_caatinga_clusterizado1.shp
5. Required file: clustered CSV

Required file in Drive:

aerogeradores_caatinga_clusterizado1.csv

Function in the script:
Serve as the input for LST extraction for wind turbines.

Required fields:

latitude
longitude
cluster
6. Annual LST extraction (wind turbines)

External data (not required in Drive):

MODIS collection MOD11A1 (Earth Engine)

Function:
Extract daytime and nighttime Land Surface Temperature (LST).

Processing:

Loop from 2003 to 2024
Apply quality control (QC) filtering
Convert to °C
Parallel processing
Incremental saving

Outputs generated:

AERO_LSTDay_2003_2025.csv
AERO_LSTNight_2003_2025.csv
7. Seasonal LST extraction (wind turbines)

File used:

aerogeradores_caatinga_clusterizado1.csv

Function:
Compute LST for two seasons:

MAM (March–May)
SON (September–November)

Outputs generated:
Files separated by season and period (day/night), for example:

lst_mam_day_2003_2025.csv
lst_son_night_2003_2025.csv
8. Required file: buffer shapefile

Required file in Drive:

pontos_buffer_revisado_final.shp

Expected fields:

Coordinates (or columns x1, y1)
Cluster identifier (cluster or id)

Function in the script:
Represent control areas (buffers) for comparison with wind turbines.

Processing:

Read and validate shapefile
Plot for visual inspection
Convert to CSV

Output generated:

pontos_buffer_revisado_final.csv
9. Annual LST extraction (buffers)

File used:

pontos_buffer_revisado_final.shp

External data:

MODIS MOD11A2

Function:
Compute annual daytime and nighttime LST for buffer points.

Output generated:

BUFFER_anual_lst_2003_2025_ultimate.csv
10. Seasonal LST extraction (buffers)

File used:

pontos_buffer_revisado_final.shp

Function:
Compute LST for:

MAM
SON

Output generated:

lst_BUFFER_2003_2025_MAM_SON.csv
11. Elevation extraction

Files used:

LST output CSVs (wind turbines or buffers)

External data:

SRTM model (USGS/SRTMGL1_003)

Function:
Add elevation values for each point.

Output generated:

Files with suffix _com_elevacao_real.csv
12. Required files for final analysis (plots)

Required files in Drive:

altitude_media_por_cluster.csv
NDVI_COEF_SAZONAL.csv
Coef_lst_DAY_anual_ajustado.csv
Coef_lst_NIGHT_anual_ajustado.csv

Function:
Analyze relationships between:

Elevation
NDVI
LST (day and night)

Outputs generated:

Regression plots (PNG)
Relationships with coefficient of determination (R²)
Summary of required input files in Drive

You must ensure that the following files are available:

Shapefiles
SHP_editado1.shp
Aerogeradores.shp
pontos_buffer_revisado_final.shp
CSV files (for final analysis)
altitude_media_por_cluster.csv
NDVI_COEF_SAZONAL.csv
Coef_lst_DAY_anual_ajustado.csv
Coef_lst_NIGHT_anual_ajustado.csv
Workflow summary
Convert shapefiles → CSV
Filter wind turbines
Create clusters
Extract LST (annual + seasonal)
Process buffers
Add elevation
Generate analyses and plots



MyDrive/
└── UFRN/
    └── Artigo_Eólicas/
        ├── SHPs/
        │   ├── aero_shp/
        │   │   └── Aerogeradores.shp
        │   ├── SHP_cluster_distancia/
        │   │   └── SHP_editado1.shp
        │   └── shp_BUFFER_pontos/
        │       └── SHP_Buffer_Final/
        │           └── pontos_buffer_revisado_final.shp
        │
        ├── PLOTS/
        │   ├── altitude_media_por_cluster.csv
        │   ├── NDVI_COEF_SAZONAL.csv
        │   ├── Coef_lst_DAY_anual_ajustado.csv
        │   └── Coef_lst_NIGHT_anual_ajustado.csv
        │
        └── (automatically generated)
            ├── LST_Resultados/
            └── intermediate CSV and SHP files

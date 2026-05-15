# wind_farm_2025

Workflow for geospatial processing, clustering, Land Surface Temperature (LST) extraction, elevation enrichment, and exploratory analysis for wind farm studies in Rio Grande do Norte, Brazil.

## Overview

This repository contains a Google Colab / Google Drive–based workflow designed to:

* convert shapefiles to tabular formats;
* filter wind turbine points by operational status and state;
* create spatial clusters using DBSCAN;
* extract annual and seasonal LST from Google Earth Engine (GEE);
* process buffer/control points for comparison;
* add elevation using SRTM;
* generate regression plots relating elevation, NDVI, and LST.

The script is intended to run in **Google Colab**, with data stored in **Google Drive**.

---

## 1) Environment setup

Before running the script, make sure that:

* your Google Drive is mounted in Colab;
* Google Earth Engine is authenticated and initialized;
* the required folders and input files already exist in the expected Drive paths.

The workflow depends on file paths defined in the script. If you change the folder structure, update the paths accordingly.

### Main Python libraries used

* `pandas`
* `geopandas`
* `numpy`
* `matplotlib`
* `seaborn`
* `scikit-learn`
* `shapely`
* `kneed`
* `tqdm`
* `earthengine-api`

---

## 2) Google Drive folder structure

Recommended structure:

```text
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
        └── LST_Resultados/
            ├── AERO_LSTDay_2003_2025.csv
            ├── AERO_LSTNight_2003_2025.csv
            ├── BUFFER_anual_lst_2003_2025_ultimate.csv
            ├── LST_SAZONAL/
            └── intermediate CSV / SHP outputs
```

> **Important:** In the script, some paths appear with slightly different spellings of `Artigo_Eólicas` / `Artigo_Eólicas`. Use one consistent folder name across the project to avoid file-not-found errors.

---

## 3) Required input files

### A. Point shapefile for clustering

**File:** `SHP_editado1.shp`
**Location:** `SHPs/SHP_cluster_distancia/`

This shapefile contains the base points used to create clusters.

**Processing performed:**

* read shapefile;
* extract latitude and longitude;
* convert to CSV.

**Generated output:**

* `pontos1.csv`

---

### B. Wind turbine shapefile

**File:** `Aerogeradores.shp`
**Location:** `SHPs/aero_shp/`

**Required fields:**

* `UF`
* `OPERACAO`
* `DATUM_EMP`
* `NOME_EOL`

This is the main wind turbine dataset.

**Processing performed:**

* filter turbines by state `RN`;
* split records by operational status:

  * `Sim` (in operation)
  * `Não` (not in operation);
* extract coordinates;
* save as CSV;
* convert filtered CSV back to shapefile.

**Generated outputs:**

* `resultado_filtrado_com_coords.csv`
* `resultado_filtrado_Sim.shp`
* `resultado_filtrado_Nao.csv`
* `resultado_filtrado_Nao.shp`

---

### C. Clustered CSV

**File:** `aerogeradores_caatinga_clusterizado1.csv`

This file is generated from the clustering step and is used as input for LST extraction.

**Required fields:**

* `latitude`
* `longitude`
* `cluster`

**Processing performed:**

* compute nearest-neighbor distances;
* identify an optimal `eps` using the elbow method;
* apply DBSCAN clustering.

**Generated outputs:**

* `aerogeradores_caatinga_clusterizado1.csv`
* `aerogeradores_caatinga_clusterizado1.shp`

---

### D. Buffer/control shapefile

**File:** `pontos_buffer_revisado_final.shp`
**Location:** `SHPs/shp_BUFFER_pontos/SHP_Buffer_Final/`

This shapefile represents the control areas (buffers) used for comparison with wind turbines.

**Expected fields:**

* coordinates (`x1`, `y1`) or equivalent
* cluster identifier (`cluster` or `id_cluster`)

**Processing performed:**

* read and validate shapefile;
* plot points for visual inspection;
* convert to CSV.

**Generated output:**

* `pontos_buffer_revisado_final.csv`

---

### E. Final analysis files

These files are required for the regression and relationship plots:

* `altitude_media_por_cluster.csv`
* `NDVI_COEF_SAZONAL.csv`
* `Coef_lst_DAY_anual_ajustado.csv`
* `Coef_lst_NIGHT_anual_ajustado.csv`

---

## 4) Workflow summary

### Step 1 — Convert shapefiles to CSV

The script first converts selected shapefiles to CSV so the coordinates can be used in later processing steps.

### Step 2 — Filter wind turbines

Turbines are filtered by:

* `UF == RN`
* `OPERACAO == Sim` or `OPERACAO == Não`

### Step 3 — Create clusters

Spatial clustering is performed using DBSCAN.

* nearest-neighbor distances are computed;
* the elbow point is used to estimate `eps`;
* clusters are assigned and saved.

### Step 4 — Extract annual LST for wind turbines

Annual daytime and nighttime LST are extracted from Google Earth Engine.

### Step 5 — Extract seasonal LST for wind turbines

Seasonal LST is extracted for:

* **MAM** = March, April, May
* **SON** = September, October, November

### Step 6 — Process buffer points

Buffer/control points are converted and used to extract annual and seasonal LST.

### Step 7 — Add elevation

Elevation is added using the SRTM model.

### Step 8 — Generate plots and regression analyses

The final scripts combine elevation, NDVI, and LST to generate regression plots and summarize relationships.

---

## 5) Google Earth Engine datasets used

### For wind turbines

* **MODIS/061/MOD11A1**

Used for annual and seasonal LST extraction with quality control filtering.

### For buffer points

* **MODIS/061/MOD11A2**

Used for annual LST extraction for control areas.

### Elevation

* **USGS/SRTMGL1_003**

Used to extract elevation values for each point.

---

## 6) Outputs generated

### Wind turbine outputs

* `AERO_LSTDay_2003_2025.csv`
* `AERO_LSTNight_2003_2025.csv`
* seasonal LST CSV files such as:

  * `lst_mam_day_2003_2025.csv`
  * `lst_son_night_2003_2025.csv`
* shapefile and CSV cluster outputs

### Buffer outputs

* `BUFFER_anual_lst_2003_2025_ultimate.csv`
* `lst_BUFFER_2003_2025_MAM_SON.csv`

### Elevation outputs

Files with suffix:

* `_com_elevacao_real.csv`

### Plot outputs

* regression figures in `.png` format
* scatter/regression plots with coefficient of determination (`R²`)

---

## 7) Notes on execution

* The script is designed for **Colab** and uses Drive-mounted paths.
* Earth Engine authentication is required before LST or elevation extraction.
* Some steps use parallel processing and batch saving to reduce data loss and speed up execution.
* The script checks for existing output files in some steps to avoid reprocessing.
* Because the workflow handles many points and years, execution may take a long time depending on Earth Engine quotas and Colab resources.

---

## 8) Tips for reproducibility

* Keep folder names consistent, especially around `Artigo_Eólicas`.
* Verify that all shapefiles include their sidecar files: `.shp`, `.shx`, `.dbf`, `.prj`.
* Ensure coordinate columns are named consistently (`latitude`, `longitude`, `x1`, `y1`).
* Check whether the output year ranges in filenames match the actual processing loop.
* Confirm that the input CSVs used in the final analysis contain the expected columns before generating plots.

---

## 9) Suggested citation / project description

If you want to use this repository in a paper or thesis, a short description could be:

> This project implements a geospatial workflow for wind farm analysis, including turbine clustering, MODIS-based LST extraction, elevation enrichment from SRTM, and exploratory regression analysis of environmental variables over operational and buffer points.

---

## 10) License

Add your preferred license here, for example:

* MIT
* Apache 2.0
* CC BY 4.0

---

## 11) Acknowledgments

* Google Earth Engine
* NASA MODIS
* USGS SRTM
* Colab / Google Drive ecosystem

---

## 12) Repository status

This repository is a research workflow for the `wind_farm_2025` project and may be adapted as the analysis evolves.

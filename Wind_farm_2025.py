# -*- coding: utf-8 -*-
"""artigo_2025_refatorado.ipynb"""

from google.colab import drive
drive.mount('/content/drive', force_remount=True)

import pandas as pd
import ee
from tqdm import tqdm
import geopandas as gpd
from shapely.geometry import Point
import os
import csv
import time
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from sklearn.neighbors import NearestNeighbors
from kneed import KneeLocator
from sklearn.cluster import DBSCAN
from concurrent.futures import ThreadPoolExecutor, as_completed
from scipy import stats
from scipy.spatial import cKDTree
from sklearn.cluster import KMeans

# Initialize Earth Engine
ee.Authenticate()
ee.Initialize(project='grand-aloe-411713')

# ==================== REUSABLE FUNCTIONS ====================

def csv_para_shapefile(csv_path, shapefile_path, col_lat='latitude', col_lon='longitude', crs='EPSG:4674'):
    df = pd.read_csv(csv_path)
    geometry = [Point(xy) for xy in zip(df[col_lon], df[col_lat])]
    gdf = gpd.GeoDataFrame(df, geometry=geometry, crs=crs)
    gdf.to_file(shapefile_path)
    print(f"✅ Shapefile gerado: {shapefile_path}")

def shapefile_para_csv(shapefile_path, csv_path):
    gdf = gpd.read_file(shapefile_path)
    gdf["longitude"] = gdf.geometry.x
    gdf["latitude"] = gdf.geometry.y
    gdf = gdf.drop(columns="geometry")
    gdf.to_csv(csv_path, index=False)
    print(f"✅ CSV gerado: {csv_path}")

def filtrar_aerogeradores(operacao, saida_csv, saida_shp=None):
    shapefile_path = "/content/drive/MyDrive/UFRN/Artigo_Eólicas/SHPs/aero_shp/Aerogeradores.shp"
    gdf = gpd.read_file(shapefile_path)
    filtro = (gdf['UF'] == 'RN') & (gdf['OPERACAO'] == operacao)
    gdf_filtrado = gdf[filtro].copy()
    gdf_filtrado['longitude'] = gdf_filtrado.geometry.x
    gdf_filtrado['latitude'] = gdf_filtrado.geometry.y
    colunas = ['DATUM_EMP', 'NOME_EOL', 'OPERACAO', 'UF', 'longitude', 'latitude']
    gdf_final = gdf_filtrado[colunas]
    gdf_final.to_csv(saida_csv, index=False, encoding='utf-8')
    print(f"✅ CSV gerado: {saida_csv}")
    if saida_shp:
        csv_para_shapefile(saida_csv, saida_shp)

def get_elevation_from_ee(lat, lon):
    point = ee.Geometry.Point([lon, lat])
    elevation_image = ee.Image('USGS/SRTMGL1_003')
    return elevation_image.sample(point, 30).first().get('elevation').getInfo()

def adicionar_elevacao_por_csv(csv_path):
    output_path = csv_path.replace('.csv', '_com_elevacao_real.csv')
    if os.path.exists(output_path):
        print(f"✅ Já existe: {output_path}")
        return output_path
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip().str.lower()
    pontos = df[['latitude', 'longitude']].drop_duplicates()
    elevacoes = {}
    for _, row in tqdm(pontos.iterrows(), total=len(pontos), desc="Elevação"):
        elevacoes[(row.latitude, row.longitude)] = get_elevation_from_ee(row.latitude, row.longitude)
    df['elevation'] = df.apply(lambda r: elevacoes.get((r['latitude'], r['longitude'])), axis=1)
    df.to_csv(output_path, index=False)
    print(f"✅ Salvo: {output_path}")
    return output_path

def safe_slope(x, y):
    x, y = np.array(x, dtype=float), np.array(y, dtype=float)
    mask = ~np.isnan(y)
    if np.sum(mask) >= 2:
        slope, intercept, r, p, _ = stats.linregress(x[mask], y[mask])
        return slope, intercept, r, p
    return np.nan, np.nan, np.nan, np.nan

def processar_ndvi_periodo(lat, lon, inicio, fim):
    ponto = ee.Geometry.Point([lon, lat])
    colecao = (ee.ImageCollection('MODIS/061/MOD13A1')
               .filterBounds(ponto)
               .filterDate(inicio, fim)
               .map(lambda img: img.updateMask(img.select('SummaryQA').eq(0))))
    ndvi = colecao.select('NDVI').mean().reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=ponto,
        scale=500
    ).get('NDVI')
    valor = ndvi.getInfo()
    return valor * 0.0001 if valor else None

def processar_lst_periodo(lat, lon, inicio, fim, banda, qc_banda):
    ponto = ee.Geometry.Point([lon, lat])
    colecao = (ee.ImageCollection('MODIS/061/MOD11A1')
               .filterBounds(ponto)
               .filterDate(inicio, fim)
               .map(lambda img: img.updateMask(img.select(qc_banda).bitwiseAnd(3).lte(1))))
    media = colecao.select(banda).mean().reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=ponto,
        scale=1000,
        maxPixels=1e13
    ).get(banda)
    valor = media.getInfo()
    return valor * 0.02 - 273.15 if valor else None

def extrair_lst_anual(csv_entrada, saida, prefixo, banda_dia, banda_noite, anos):
    df = pd.read_csv(csv_entrada)
    colunas = ['latitude', 'longitude', 'cluster'] + [f'{prefixo}_{ano}' for ano in anos]
    if os.path.exists(saida):
        df_existente = pd.read_csv(saida)
        processados = set(zip(df_existente.latitude, df_existente.longitude))
    else:
        processados = set()
        pd.DataFrame(columns=colunas).to_csv(saida, index=False)

    for _, row in tqdm(df.iterrows(), total=len(df), desc=prefixo):
        if (row.latitude, row.longitude) in processados:
            continue
        linha = [row.latitude, row.longitude, row.get('cluster')]
        for ano in anos:
            lst_dia = processar_lst_periodo(row.latitude, row.longitude, f'{ano}-01-01', f'{ano}-12-31', banda_dia, 'QC_Day')
            linha.append(lst_dia)
        pd.DataFrame([linha], columns=colunas).to_csv(saida, mode='a', header=False, index=False)

# ==================== MAIN EXECUTION ====================

# 1. Shapefile to Points Conversion
shapefile_path = "/content/drive/MyDrive/UFRN/Artigo_Eólicas/SHPs/SHP_cluster_distancia/SHP_editado1.shp"
csv_path = "/content/drive/MyDrive/UFRN/Artigo_Eólicas/SHPs/SHP_cluster_distancia/pontos1.csv"
shapefile_para_csv(shapefile_path, csv_path)

# 2. Wind Turbines in Operation
filtrar_aerogeradores('Sim',
    "/content/drive/MyDrive/UFRN/Artigo_Eólicas/SHPs/aero_shp/resultado_filtrado_com_coords.csv",
    "/content/drive/MyDrive/UFRN/Artigo_Eólicas/SHPs/aero_shp/resultado_filtrado_Sim.shp")

# 3. Wind Turbines Not in Operation
filtrar_aerogeradores('Não',
    "/content/drive/MyDrive/UFRN/Artigo_Eólicas/SHPs/aero_shp/resultado_filtrado_Nao.csv",
    "/content/drive/MyDrive/UFRN/Artigo_Eólicas/SHPs/aero_shp/resultado_filtrado_Nao.shp")

# 4. Distance-Based Clustering
df = pd.read_csv(csv_path)
coords = df[['longitude', 'latitude']].to_numpy()
k = 11
neighbors = NearestNeighbors(n_neighbors=k).fit(coords)
distances, _ = neighbors.kneighbors(coords)
distances = np.sort(distances[:, k-1])
knee = KneeLocator(range(len(distances)), distances, S=1.0, curve='convex', direction='increasing')
eps = distances[knee.knee]
df['cluster'] = DBSCAN(eps=eps, min_samples=5).fit(coords).labels_
df.to_csv('/content/drive/MyDrive/UFRN/Artigo_Eólicas/SHPs/SHP_cluster_distancia/aerogeradores_caatinga_clusterizado1.csv', index=False)
csv_para_shapefile(
    '/content/drive/MyDrive/UFRN/Artigo_Eólicas/SHPs/SHP_cluster_distancia/aerogeradores_caatinga_clusterizado1.csv',
    '/content/drive/MyDrive/UFRN/Artigo_Eólicas/SHPs/SHP_cluster_distancia/aerogeradores_caatinga_clusterizado1.shp'
)

# 5. LST Extraction (Annual)
anos_lst = list(range(2003, 2025))
extrair_lst_anual(
    '/content/drive/MyDrive/UFRN/Artigo_Eólicas/aerogeradores_caatinga_clusterizado1.csv',
    '/content/drive/MyDrive/UFRN/Artigo_Eólicas/LST_Resultados/AERO_LSTDay_2003_2025.csv',
    'LST_Dia', 'LST_Day_1km', None, anos_lst
)

# 6. Altitude Processing
df_aero = pd.read_csv('/content/drive/MyDrive/UFRN/Artigo_Eólicas/aerogeradores_caatinga_clusterizado1.csv')[['longitude', 'latitude', 'cluster']]
df_buffer = pd.read_csv('/content/drive/MyDrive/UFRN/Artigo_Eólicas/SHPs/SHP_cluster_distancia/pontos1.csv')[['longitude', 'latitude', 'cluster']]
pd.concat([df_aero, df_buffer]).drop_duplicates().to_csv('/content/drive/MyDrive/UFRN/Artigo_Eólicas/todos_pontos_altitude.csv', index=False)
adicionar_elevacao_por_csv('/content/drive/MyDrive/UFRN/Artigo_Eólicas/todos_pontos_altitude.csv')

# 7. Centroids Calculation
gdf = gpd.read_file('/content/drive/MyDrive/UFRN/Artigo_Eólicas/SHPs/aerogeradores_caatinga_clusterizado1.shp')
gdf_filtered = gdf[gdf['cluster'] != -1]
gdf_projected = gdf_filtered.to_crs(epsg=5880)
centroids = gdf_projected.dissolve(by='cluster').centroid
centroids = centroids.to_crs(gdf.crs)
centroids.to_file('/content/drive/MyDrive/UFRN/Artigo_Eólicas/SHPs/centroids_clusters.shp')
print("✅ Centróides salvos com sucesso!")

print("✅ Processamento concluído com sucesso!")

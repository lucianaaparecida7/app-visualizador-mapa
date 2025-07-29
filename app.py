import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
from streamlit_folium import st_folium
import zipfile
import os
import json

st.set_page_config(layout="wide")
st.title("🗺️ Visualizador Interativo de Arquivos Geográficos")

uploaded_file = st.file_uploader(
    "Envie um arquivo geográfico (.zip com .shp, .geojson, .json ou .csv com latitude/longitude)",
    type=["zip", "geojson", "json", "csv"]
)

def carregar_shapefile(zip_file):
    with open("shapefile.zip", "wb") as f:
        f.write(zip_file.getbuffer())
    with zipfile.ZipFile("shapefile.zip", "r") as zip_ref:
        zip_ref.extractall("shapefile_data")
    shp_files = [f for f in os.listdir("shapefile_data") if f.endswith(".shp")]
    if not shp_files:
        st.error("Nenhum arquivo .shp encontrado no .zip.")
        return None
    shp_path = os.path.join("shapefile_data", shp_files[0])
    gdf = gpd.read_file(shp_path)
    return gdf

def carregar_geojson(file):
    gdf = gpd.read_file(file)
    return gdf

def carregar_csv(file):
    df = pd.read_csv(file)
    if not {"latitude", "longitude"}.issubset(df.columns):
        st.error("CSV deve conter colunas 'latitude' e 'longitude'")
        return None
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.longitude, df.latitude), crs="EPSG:4326")
    return gdf

if uploaded_file is not None:
    filename = uploaded_file.name.lower()
    gdf = None

    try:
        if filename.endswith(".zip"):
            gdf = carregar_shapefile(uploaded_file)
        elif filename.endswith(".geojson") or filename.endswith(".json"):
            gdf = carregar_geojson(uploaded_file)
        elif filename.endswith(".csv"):
            gdf = carregar_csv(uploaded_file)
    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")

    if gdf is not None:
        try:
            gdf = gdf.to_crs("EPSG:4326")
            centroide = gdf.geometry.unary_union.centroid
            m = folium.Map(location=[centroide.y, centroide.x], zoom_start=13)
            folium.GeoJson(gdf).add_to(m)

            st.subheader("🗺️ Mapa Interativo")
            st_folium(m, width=900, height=600)
        except Exception as e:
            st.error(f"Erro ao gerar o mapa: {e}")

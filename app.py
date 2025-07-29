import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
from streamlit_folium import st_folium
import zipfile
import os

st.set_page_config(layout="wide")
st.title("🗺️ Visualizador Interativo de Arquivos Geográficos")

uploaded_file = st.file_uploader(
    "Envie um arquivo geográfico (.zip com .shp, .geojson, .json ou .csv com latitude/longitude)",
    type=["zip", "geojson", "json", "csv"]
)

if uploaded_file is not None:
    filename = uploaded_file.name

    # === SHAPEFILE (.zip com .shp, .shx, .dbf) ===
    if filename.endswith(".zip"):
        with open("shapefile.zip", "wb") as f:
            f.write(uploaded_file.getbuffer())
        with zipfile.ZipFile("shapefile.zip", "r") as zip_ref:
            zip_ref.extractall("shapefile_data")
        shp_files = [f for f in os.listdir("shapefile_data") if f.endswith(".shp")]
        if len(shp_files) == 0:
            st.error("Nenhum arquivo .shp encontrado no .zip.")
            gdf = None
        else:
            shp_path = os.path.join("shapefile_data", shp_files[0])
            gdf = gpd.read_file(shp_path)

    # === GEOJSON ou JSON ===
    elif filename.endswith((".geojson", ".json")):
        gdf = gpd.read_file(uploaded_file)

    # === CSV com latitude/longitude ===
    elif filename.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
        if {"latitude", "longitude"}.issubset(df.columns):
            gdf = gpd.GeoDataFrame(
                df,
                geometry=gpd.points_from_xy(df.longitude, df.latitude),
                crs="EPSG:4326"
            )
        else:
            st.error("CSV precisa ter colunas chamadas 'latitude' e 'longitude'.")
            gdf = None

    else:
        st.error("Formato de arquivo não suportado.")
        gdf = None

    # === Visualizar o mapa ===
    if gdf is not None:
        if gdf.crs != "EPSG:4326":
            gdf = gdf.to_crs("EPSG:4326")

        centroide = gdf.geometry.centroid.unary_union
        m = folium.Map(location=[centroide.y, centroide.x], zoom_start=12)
        folium.GeoJson(gdf, name="layer").add_to(m)

        st.subheader("🗺️ Mapa Interativo")
        st_folium(m, width=900, height=600)


import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
from streamlit_folium import st_folium
import zipfile
import os
import shutil

st.set_page_config(layout="wide")
st.title("🗺️ Visualizador Interativo de Arquivos Geográficos")

st.markdown("Envie um arquivo `.zip` com `.shp`, `.geojson`, `.json` ou `.csv` com latitude/longitude.")

uploaded_file = st.file_uploader("Arraste e solte aqui", type=["zip", "geojson", "json", "csv"])

def process_geo_dataframe(gdf):
    if gdf.crs != "EPSG:4326":
        gdf = gdf.to_crs("EPSG:4326")
    centroide = gdf.geometry.centroid.unary_union
    m = folium.Map(location=[centroide.y, centroide.x], zoom_start=13)
    folium.GeoJson(gdf).add_to(m)
    return m

if uploaded_file is not None:
    file_ext = uploaded_file.name.split('.')[-1].lower()

    try:
        if file_ext == "zip":
            with open("shapefile.zip", "wb") as f:
                f.write(uploaded_file.getbuffer())
            with zipfile.ZipFile("shapefile.zip", "r") as zip_ref:
                zip_ref.extractall("shapefile_data")
            shp_files = [f for f in os.listdir("shapefile_data") if f.endswith(".shp")]
            if len(shp_files) == 0:
                st.error("Nenhum arquivo .shp encontrado no .zip.")
            else:
                shp_path = os.path.join("shapefile_data", shp_files[0])
                gdf = gpd.read_file(shp_path)
                m = process_geo_dataframe(gdf)
                st.subheader("🗺️ Mapa Interativo")
                st_folium(m, width=900, height=600)

        elif file_ext in ["geojson", "json"]:
            gdf = gpd.read_file(uploaded_file)
            m = process_geo_dataframe(gdf)
            st.subheader("🗺️ Mapa Interativo")
            st_folium(m, width=900, height=600)

        elif file_ext == "csv":
            df = pd.read_csv(uploaded_file)
            if "latitude" in df.columns and "longitude" in df.columns:
                gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.longitude, df.latitude), crs="EPSG:4326")
                m = process_geo_dataframe(gdf)
                st.subheader("🗺️ Mapa Interativo")
                st_folium(m, width=900, height=600)
            else:
                st.error("O CSV precisa conter colunas 'latitude' e 'longitude'.")
        else:
            st.error("Formato de arquivo não suportado.")

    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")

# Limpeza
if os.path.exists("shapefile_data"):
    shutil.rmtree("shapefile_data")

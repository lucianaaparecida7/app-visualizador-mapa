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

# Função para carregar diferentes tipos de arquivos
def carregar_arquivo(uploaded_file):
    filename = uploaded_file.name.lower()

    # Criar pasta temporária
    temp_dir = "temp_data"
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir, exist_ok=True)

    # ZIP (Shapefile)
    if filename.endswith(".zip"):
        with open(os.path.join(temp_dir, "file.zip"), "wb") as f:
            f.write(uploaded_file.getbuffer())
        with zipfile.ZipFile(os.path.join(temp_dir, "file.zip"), "r") as zip_ref:
            zip_ref.extractall(temp_dir)
        shp_files = [f for f in os.listdir(temp_dir) if f.endswith(".shp")]
        if not shp_files:
            st.error("Nenhum arquivo .shp encontrado no .zip.")
            return None
        return gpd.read_file(os.path.join(temp_dir, shp_files[0]))

    # GeoJSON ou JSON
    elif filename.endswith(".geojson") or filename.endswith(".json"):
        return gpd.read_file(uploaded_file)

    # CSV com lat/lon
    elif filename.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
        if not {'latitude', 'longitude'}.issubset(df.columns):
            st.error("O CSV precisa ter colunas 'latitude' e 'longitude'.")
            return None
        return gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.longitude, df.latitude), crs="EPSG:4326")

    else:
        st.error("Formato de arquivo não suportado.")
        return None

# Upload do arquivo
uploaded_file = st.file_uploader("Envie um arquivo (.zip, .geojson, .json ou .csv com lat/lon)", type=["zip", "geojson", "json", "csv"])

if uploaded_file:
    try:
        gdf = carregar_arquivo(uploaded_file)
        if gdf is not None:
            if gdf.crs != "EPSG:4326":
                gdf = gdf.to_crs("EPSG:4326")

            centro = gdf.geometry.unary_union.centroid
            m = folium.Map(location=[centro.y, centro.x], zoom_start=13)

            folium.GeoJson(
                gdf,
                name="Camada",
                tooltip=folium.GeoJsonTooltip(
                    fields=list(gdf.columns),
                    aliases=[f"{col}:" for col in gdf.columns],
                    sticky=True
                )
            ).add_to(m)

            st.subheader("🗺️ Mapa Interativo")
            st_data = st_folium(m, width=900, height=600)
    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")


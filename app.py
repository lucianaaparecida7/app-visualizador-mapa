import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
from streamlit_folium import st_folium
import zipfile
import os
import tempfile

st.set_page_config(layout="wide")
st.title("🗺️ Visualizador Interativo de Arquivos Geográficos")
st.write("Envie um arquivo `.zip` (shapefile) ou `.geojson`, `.json`, `.csv` com coordenadas.")

uploaded_file = st.file_uploader(
    "Arraste e solte o arquivo aqui",
    type=["zip", "geojson", "json", "csv"]
)

def carregar_geodf(file):
    ext = os.path.splitext(file.name)[-1].lower()

    if ext == ".zip":
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = os.path.join(tmpdir, "shapefile.zip")
            with open(zip_path, "wb") as f:
                f.write(file.read())
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(tmpdir)

            shp_files = [f for f in os.listdir(tmpdir) if f.endswith(".shp")]
            if not shp_files:
                st.error("Nenhum arquivo .shp encontrado no .zip.")
                return None
            gdf = gpd.read_file(os.path.join(tmpdir, shp_files[0]))
    elif ext in [".geojson", ".json"]:
        gdf = gpd.read_file(file)
    elif ext == ".csv":
        df = pd.read_csv(file)
        if not {"latitude", "longitude"}.issubset(df.columns):
            st.error("O CSV deve conter colunas 'latitude' e 'longitude'.")
            return None
        gdf = gpd.GeoDataFrame(
            df,
            geometry=gpd.points_from_xy(df.longitude, df.latitude),
            crs="EPSG:4326"
        )
    else:
        st.error("Formato de arquivo não suportado.")
        return None

    # Corrige para WGS84
    if gdf.crs != "EPSG:4326":
        gdf = gdf.to_crs("EPSG:4326")

    # Converte colunas de data para string
    for col in gdf.columns:
        if pd.api.types.is_datetime64_any_dtype(gdf[col]):
            gdf[col] = gdf[col].astype(str)

    return gdf


if uploaded_file:
    gdf = carregar_geodf(uploaded_file)
    if gdf is not None:
        try:
            centro = gdf.geometry.centroid.unary_union.centroid
            m = folium.Map(location=[centro.y, centro.x], zoom_start=12)
            folium.GeoJson(gdf, name="Camada").add_to(m)
            st.subheader("🗺️ Mapa Interativo")
            st_folium(m, width=900, height=600)
        except Exception as e:
            st.error(f"Erro ao gerar o mapa: {e}")


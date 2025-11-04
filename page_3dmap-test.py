import streamlit as st
import geopandas as gpd
import pandas as pd
import numpy as np
import pydeck as pdk
from scipy.ndimage import gaussian_filter

st.title("台北市 停車格密度 DEM（平滑 3D GridLayer）")
st.write("生成網格格點，計算停車格密度，並使用高斯平滑模擬連續 DEM")

# --- 1. 讀取台北市行政區 shapefile ---
taipei = gpd.read_file("臺北市區界圖_20220915/G97_A_CADIST_P.shp")
if taipei.crs and taipei.crs.to_epsg() != 4326:
    taipei = taipei.to_crs(epsg=4326)

# --- 2. 讀取停車格資料 ---
parking = gpd.read_file("park01-clean/park01_202510091630_clean.shp")
if parking.crs and parking.crs.to_epsg() != 4326:
    parking = parking.to_crs(epsg=4326)

# --- 3. 將非 Point 幾何轉成中心點 ---
parking['geometry'] = parking.geometry.centroid

# --- 4. 生成網格 ---
# 設定網格解析度
grid_size = 50  # 可以調整格子數量，越大格子越小
min_lon, min_lat, max_lon, max_lat = taipei.total_bounds

x_edges = np.linspace(min_lon, max_lon, grid_size)
y_edges = np.linspace(min_lat, max_lat, grid_size)

# 5. 計算每個格子停車格數量
H, xedges, yedges = np.histogram2d(
    parking.geometry.x, parking.geometry.y,
    bins=[x_edges, y_edges]
)

# --- 5. 高斯平滑 ---
H_smooth = gaussian_filter(H.T, sigma=10)  # sigma 可調整平滑程度

# --- 6. 生成網格點 DataFrame ---
x_centers = (xedges[:-1] + xedges[1:]) / 2
y_centers = (yedges[:-1] + yedges[1:]) / 2

grid_data = []
for i in range(len(x_centers)):
    for j in range(len(y_centers)):
        elev = float(H_smooth[j, i])
        if elev > 1:  # 只保留有停車格的格子
            grid_data.append({
                "lon": x_centers[i],
                "lat": y_centers[j],
                "elevation": elev
            })
grid_df = pd.DataFrame(grid_data)

# --- 7. PolygonLayer：行政區邊界 ---
taipei['coordinates'] = taipei['geometry'].apply(lambda x: x.__geo_interface__['coordinates'])
polygon_layer = pdk.Layer(
    "PolygonLayer",
    data=taipei,
    get_polygon="coordinates",
    get_fill_color=[0,0,0,0],  # 透明
    get_line_color=[0,0,0],
    line_width_min_pixels=2,
    extruded=False,
    pickable=True
)

# --- 8. GridLayer：平滑 DEM ---
color_range = [
    [255, 255, 204, 150],
    [255, 237, 160, 150],
    [254, 217, 118, 150],
    [254, 178, 76, 150],
    [253, 141, 60, 150],
    [240, 59, 32, 150],
    [189, 0, 38, 150]
]

grid_layer = pdk.Layer(
    "GridLayer",
    data=grid_df,
    get_position='[lon, lat]',
    get_elevation_weight='elevation',
    elevation_scale=5,  # 可以調整高度放大倍率
    cell_size=1000,      # 每格大小（單位公尺）
    extruded=True,
    pickable=True,
    get_color_weight='elevation', 
    color_range=color_range  
)

# --- 9. 設定視角 ---
view_state = pdk.ViewState(
    latitude=25.0330,
    longitude=121.5654,
    zoom=12,
    pitch=50
)

# --- 10. 組合並顯示 ---
r = pdk.Deck(
    layers=[polygon_layer, grid_layer],
    initial_view_state=view_state,
    tooltip={"text": "停車格密度: {elevationValue}"}
)

st.pydeck_chart(r)

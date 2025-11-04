import streamlit as st
import geopandas as gpd
import pandas as pd
import numpy as np
import pydeck as pdk
import scipy
from scipy.ndimage import gaussian_filter

st.title("Pydeck 3D 地圖：台北市各區停車格數量")
st.write("因檔案過大，資料經採樣處理過，非實際數字")

# --- 1. 讀取台北市行政區 shapefile ---
taipei = gpd.read_file("臺北市區界圖_20220915/G97_A_CADIST_P.shp")

# 確保為 WGS84 經緯度座標
if taipei.crs and taipei.crs.to_epsg() != 4326:
    taipei = taipei.to_crs(epsg=4326)

# --- 2. 讀取第二個 GeoDataFrame ---
data = gpd.read_file("park01-clean/park01_202510091630_clean.shp")

if data.crs and data.crs.to_epsg() != 4326:
    data = data.to_crs(epsg=4326)

# --- 3. 空間相交：判斷每個點屬於哪個行政區 (TNAME) ---
joined = gpd.sjoin(data, taipei[['TNAME', 'geometry']], predicate='within', how='left')

# --- 4. 統計每個行政區內的資料數量 ---
count_by_tname = joined.groupby('TNAME').size().reset_index(name='count')

# --- 5. 合併回台北市行政區 ---
taipei_count = taipei.merge(count_by_tname, on='TNAME', how='left').fillna({'count': 0})

# --- 6. 產生行政區中心點 (作為柱狀圖位置) ---
taipei_count["centroid_lon"] = taipei_count.geometry.centroid.x
taipei_count["centroid_lat"] = taipei_count.geometry.centroid.y

# --- 7. 計算柱狀圖高度縮放 ---
# 方法：將 count / 最大值 * 最大高度
max_height = 5000  # 可以調整整體柱子最大高度
taipei_count['elevation'] = taipei_count['count'] / taipei_count['count'].max() * max_height

# --- 8. 建立行政區底圖顏色 (可設定透明度) ---
# 這裡底圖顏色可以調整，例如用灰色系 + 半透明
# taipei_count['fill_color'] = [[255, 255, 255, 50] for _ in range(len(taipei_count))] # R,G,B,透明度 0~255

layer_boundary = pdk.Layer(
    "GeoJsonLayer",
    taipei_count.__geo_interface__,
    stroked=True,
    filled=True,
    get_fill_color= [255,255,255,100],
    get_line_color=[0, 0, 0, 255],
    pickable=True,
    extruded=True,
    elevation_scale=0.3, 
)

# --- 9. 建立柱狀圖圖層 (顏色可依資料數量漸層) ---
# 這裡用紅色到藍色漸層示範
def get_column_color(count, max_count):
    r = int(255 * count / max_count)
    g = 50
    b = int(255 * (1 - count / max_count))
    return [r, g, b, 200]  # 透明度200

max_count = taipei_count['count'].max()
taipei_count['column_color'] = taipei_count['count'].apply(lambda x: get_column_color(x, max_count))

layer_columns = pdk.Layer(
    "ColumnLayer",
    data=taipei_count,
    get_position='[centroid_lon, centroid_lat]',
    get_elevation='elevation',
    radius=300,
    get_fill_color='column_color',
    pickable=True,
)

# --- 10. 設定視角 ---
view_state = pdk.ViewState(
    latitude=25.0330,
    longitude=121.5654,
    zoom=11.5,
    pitch=45,
)

# --- 11. 組合圖層並顯示 ---
r = pdk.Deck(
    layers=[layer_boundary, layer_columns],
    initial_view_state=view_state,
    tooltip={"text": "行政區: {TNAME}\n資料數量: {count}"}
)

st.pydeck_chart(r)

# ===============================================
#          第二個地圖：模擬 DEM
# ===============================================

st.title("台北市 停車格密度 DEM（平滑 3D GridLayer）")
st.write("生成網格格點，計算停車格密度，並使用高斯平滑模擬連續 DEM")

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
    zoom=11,
    pitch=50
)

# --- 10. 組合並顯示 ---
r = pdk.Deck(
    layers=[polygon_layer, grid_layer],
    initial_view_state=view_state,
    tooltip={"text": "停車格密度: {elevationValue}"}
)

st.pydeck_chart(r)

import streamlit as st
import geopandas as gpd
import pydeck as pdk

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
    latitude=25.0478,
    longitude=121.5170,
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

st.title("Pydeck 3D 地圖 (網格 - DEM 模擬)")

# --- 1. 模擬 DEM 網格資料 ---
x, y = np.meshgrid(np.linspace(-1, 1, 50), np.linspace(-1, 1, 50))
z = np.exp(-(x**2 + y**2) * 2) * 1000

data_dem_list = [] # 修正: 建立一個列表來收集字典
base_lat, base_lon = 25.0, 121.5
for i in range(50):
    for j in range(50):
        data_dem_list.append({ # 修正: 將字典附加到列表中
            "lon": base_lon + x[i, j] * 0.1,
            "lat": base_lat + y[i, j] * 0.1,
            "elevation": z[i, j]
        })
df_dem = pd.DataFrame(data_dem_list) # 從列表創建 DataFrame

# --- 2. 設定 Pydeck 圖層 (GridLayer) ---
layer_grid = pdk.Layer( # 稍微改個名字避免混淆
    'GridLayer',
    data=df_dem,
    get_position='[lon, lat]',
    get_elevation_weight='elevation', # 使用 'elevation' 欄位當作高度
    elevation_scale=1,
    cell_size=2000,
    extruded=True,
    pickable=True # 加上 pickable 才能顯示 tooltip
)

# --- 3. 設定視角 (View) ---
view_state_grid = pdk.ViewState( # 稍微改個名字避免混淆
    latitude=base_lat, longitude=base_lon, zoom=10, pitch=50
)

# --- 4. 組合並顯示 (第二個地圖) ---
r_grid = pdk.Deck( # 稍微改個名字避免混淆
    layers=[layer_grid],
    initial_view_state=view_state_grid,
    # mapbox_key=MAPBOX_KEY, # <--【修正點】移除這裡的 mapbox_key
    tooltip={"text": "海拔高度: {elevationValue} 公尺"} # GridLayer 用 elevationValue
)
st.pydeck_chart(r_grid)
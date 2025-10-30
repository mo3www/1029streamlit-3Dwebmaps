import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import rasterio
import numpy as np

st.title("Plotly 3D 地圖 (向量 - 地球儀)")
st.write("pop 與 lifeExp 關係，點的顏色越深 lifeExp 越高")

# --- 1. 載入 Plotly 內建的範例資料 ---
df = px.data.gapminder().query("year == 2007")

# px.data 提供了幾個內建的範例資料集，方便使用者練習或展示。
# gapminder() 是其中一個內建函式，它會載入著名的 Gapminder 資料集。
# 這個資料集包含了世界各國多年的平均壽命 (lifeExp)、人均 GDP (gdpPercap) 和人口 (pop) 等數據。
# .query("year == 2007")是 pandas DataFrame 提供的一個方法，用於根據字串表達式來篩選資料框的列 (rows)。
# "year == 2007" 是一個字串形式的查詢條件，意思是「選取 'year' 欄位的值等於 2007 的那些列」。

# --- 2. 建立 3D 地理散點圖 (scatter_geo) ---
fig = px.scatter_geo(
    df,
    locations="iso_alpha",  # 國家代碼
    color="lifeExp",      # 依據平勳壽命上色
    hover_name="country",   # 滑鼠懸停時顯示國家名稱
    size="pop",             # 點的大小代表人口數
    color_continuous_scale="Turbo",

    # *** 關鍵：使用 "orthographic" 投影法來建立 3D 地球儀 ***
    projection="orthographic"
)

fig.update_geos(
    showland=True, landcolor="lightgreen",
    showocean=True, oceancolor="lightblue",
    showrivers=True, rivercolor="blue",
    showcountries=True, countrycolor="gray",
    lataxis_showgrid=True, lonaxis_showgrid=True
)
# "orthographic" 投影會將地球渲染成一個從太空中看到的球體，
# 從而產生類似 3D 地球儀的視覺效果。
# 其他常見投影如 "natural earth", "mercator" 等通常是 2D 平面地圖。


# --- 3. 在 Streamlit 中顯示 ---
st.plotly_chart(fig, use_container_width=True)
# use_container_width=True:當設定為 True 時，Streamlit 會忽略 Plotly 圖表物件本身可能設定的寬度，
# 並強制讓圖表的寬度自動延展，以填滿其所在的 Streamlit 容器 (例如，主頁面的寬度、某個欄位 (column) 的寬度，
# 或是一個展開器 (expander) 的寬度)。

st.title("Plotly 3D 地圖 (網格 - DEM 表面)")
st.write("資料：不分幅_澎湖20公尺網格數值地形模型")

# --- 1. 讀取 DEM 資料 (GeoTIFF) ---
file_path = "phDEM_20m_121.tif"  # 檢查檔案的正確路徑
with rasterio.open(file_path) as src:
    # 讀取高程資料，這會是一個 2D 陣列 (高程值)
    dem_data = src.read(1)

    height, width = dem_data.shape
    x = np.linspace(0, width - 1, width)  # 修正網格範圍
    y = np.linspace(0, height - 1, height)

    # 使用 meshgrid 生成 2D 網格
    x, y = np.meshgrid(x, y)

    # 確認 NoData 值
    nodata_value = src.nodata
    # print("NoData 值:", nodata_value)

    if nodata_value is not None:
        dem_data = np.where(dem_data == nodata_value, np.nan, dem_data)
    else:
        print("DEM 資料沒有設定 NoData 值")

    # 將 NaN 值替換為 0 或其他值
    dem_data = np.nan_to_num(dem_data, nan=0)

    # 查看數據範圍，確認 NoData 值已經處理
    # print("清理後高程數據範圍：", np.nanmin(dem_data), "到", np.nanmax(dem_data))

# --- 2. 降採樣 DEM 數據 ---
# 假設我們要將數據降採樣 2 倍，將每 2x2 像素合併為一個像素
factor = 4  # 降採樣因子

# 這裡使用步長選擇來降採樣
dem_data_resampled = dem_data[::factor, ::factor]
x_resampled = x[::factor]
y_resampled = y[::factor]

# 打印降採樣後的數據範圍
print("降採樣後的高程數據範圍：", np.nanmin(dem_data_resampled), "到", np.nanmax(dem_data_resampled))

# --- 3. 建立 3D Surface 圖 ---
custom_colorscale = [
    [0.0, "lightblue"],    # 最小值顯示為淺藍色
    [0.25, "lightgreen"],   # 40% 時顯示為淺綠色
    [0.5, "lightyellow"],  # 60% 時顯示為淺黃色
    [0.75, "lightsalmon"],  # 80% 時顯示為淺橙色
    [1.0, "lightcoral"]    # 最大值顯示為淡紅色
]

fig = go.Figure(
    data=[
        go.Surface(
            z=dem_data_resampled,
            x=x_resampled,
            y=y_resampled,
            colorscale=custom_colorscale
        )
    ]
)

# --- 4. 調整 3D 視角和外觀 ---
z_max = 100

fig.update_layout(
    title="降採樣後的 DEM 3D 地形圖 (可旋轉)",
    width=800 ,
    height=700,
    scene=dict(
        xaxis_title='經度 (X)',
        yaxis_title='緯度 (Y)',
        zaxis_title='海拔 (Z)',
        zaxis=dict(range=[np.nanmin(dem_data_resampled), z_max])  # 設置 z 軸範圍
    ),
    margin=dict(l=0, r=0, b=0, t=0)
)

# --- 5. 在 Streamlit 中顯示 ---
st.plotly_chart(fig)
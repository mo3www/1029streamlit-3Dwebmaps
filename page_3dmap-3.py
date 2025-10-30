import rasterio
import numpy as np
import plotly.graph_objects as go
import streamlit as st

# --- 1. 讀取 DEM 資料 (GeoTIFF) ---
# 使用 rasterio 讀取 .tif 檔案
# /workspaces/1029streamlit-3Dwebmaps/page_3dmap-3.py
with rasterio.open("/workspaces/1029streamlit-3Dwebmaps/不分幅_全台及澎湖DEM/phDEM_20m_121.tif") as src:
    # 讀取高程資料，這會是一個 2D 陣列 (高程值)
    dem_data = src.read(1)

# --- 2. 建立 3D Surface 圖 ---
# 使用 Plotly 的 Surface 圖來顯示 DEM 資料
fig = go.Figure(
    data=[
        go.Surface(
            z=dem_data,  # 這是從 .tif 讀取的高程資料
            colorscale="Viridis",  # 可選顏色方案
            colorbar=dict(title="Elevation (m)")  # 顏色條的標題
        )
    ]
)

# --- 3. 調整 3D 視角和外觀 ---
fig.update_layout(
    title="3D 地形圖",
    width=800,
    height=700,
    scene=dict(
        xaxis_title='X 軸 (經度)',
        yaxis_title='Y 軸 (緯度)',
        zaxis_title='海拔 (Z)'
    )
)

# --- 4. 在 Streamlit 中顯示 ---
st.plotly_chart(fig, use_container_width=True)

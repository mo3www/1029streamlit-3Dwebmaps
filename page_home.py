import streamlit as st

# 這裡放所有您想在首頁顯示的內容
st.title("歡迎來到林彥伶的 3D GIS 專案！")
st.header("GIS專題")
st.write("這是一個來自資管系，使用 Streamlit 建立的3D互動式地圖應用程式")

video_url = "https://i.meee.com.tw/TuZ68Gp.gif"
st.write(f"展示GIF：這是一個奮鬥後光榮失敗的畫面，但我們仍在嘗試")
st.image(video_url)
import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import folium
from streamlit_folium import folium_static

def load_streamlit_data():
    streamlit_df = pd.read_csv("./data/streamlit_df.csv")
    st_data = streamlit_df.loc[(streamlit_df['기준_년'] == 2023) & (streamlit_df['기준_분기'] == 3), :]
    return st_data

def main_page():
    st.markdown("<h1 style='text-align: center;'>🏪 강남구 편의점 매출 예측 서비스</h1>", unsafe_allow_html=True)

def commercial_page():
    st.markdown("<h2 style='text-align: center;'>강남구 상권 분석</h2>", unsafe_allow_html=True)
    st_data = load_streamlit_data()

    # 강남구 중심 좌표
    map_center = [37.5172, 127.0473]

    # Folium 맵 생성
    mymap = folium.Map(location=map_center, zoom_start=15)

    # Folium 맵을 HTML 형식으로 변환
    html_code = mymap._repr_html_()

    # HTML 및 CSS를 사용하여 중앙 정렬
    centered_html = f"""
        <div style="display: flex; justify-content: center;">
            {html_code}
        </div>
    """

    # Streamlit에 중앙 정렬된 Folium 맵 표시
    st.components.v1.html(centered_html, width=1200, height=600)

def main():
    st.set_page_config(
        page_title="강남구 편의점 매출 예측 서비스",
        page_icon="🏪",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # 사이드바 메뉴
    with st.sidebar:
        menu = option_menu("메뉴 선택", ['홈', '강남구 상권 분석', '강남구 편의점 매출 현황', '매출 예측'],
                   icons=['house', 'bi bi-clipboard2-data', 'bi bi-currency-dollar', 'bi bi-graph-up-arrow'], 
                   menu_icon="cast", 
                   default_index=0)        
        
        if menu == "홈":
            choice = "홈"

        elif menu == "강남구 상권 분석":
            choice = "강남구 상권 분석"

    # 페이지 보이기
    if choice == '홈':
        main_page()
    
    elif choice == '강남구 상권 분석':
        commercial_page()
    

if __name__ == '__main__':
    main()
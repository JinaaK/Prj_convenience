import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import folium
from streamlit_folium import folium_static
import geopandas as gpd
from folium.plugins import MarkerCluster
from shapely.geometry import Polygon
from shapely import wkt
import matplotlib.pyplot as plt


def load_streamlit_data():
    streamlit_df = pd.read_csv("./data/streamlit_df.csv")
    return streamlit_df 

def load_quarter_data():
    quarter_df = pd.read_csv("./data/final_merged_update_store_age_df.csv")
    return quarter_df 

def main_page():
    st.markdown("<h1 style='text-align: center;'>🏪 강남구 편의점 매출 예측 서비스</h1>", unsafe_allow_html=True)

def commercial_page(streamlit_df):
    st.markdown("<h2 style='text-align: center;'>강남구 상권 분석</h2>", unsafe_allow_html=True)

    streamlit_df = streamlit_df.loc[(streamlit_df['기준_년'] == 2023) & (streamlit_df['기준_분기'] == 3), :]

    col1, col2 = st.columns([1.5,1])

    with col1: 
        # 지도 생성
        m = folium.Map(location=[37.5172, 127.0473], zoom_start=13)  # 서울 위도, 경도를 중심으로 지도 생성
        
        # 각 점에 대한 정보를 Folium으로 추가
        for idx, row in streamlit_df.iterrows():
            # 툴팁에 표시할 내용 설정
            tooltip = f"상권명: {row['상권_코드_명']}<br>" \
                    f"매출금액: {row['당월_매출_금액']:,.0f}원<br>" \
                    f"유동인구: {row['총_유동인구_수']:,.0f}명<br>" \
                    f"총상주인구: {row['총_상주인구_수']:,.0f}명"


            folium.CircleMarker(                         # 원 표시
                location=[row['위도'], row['경도']],      # 원 중심- 위도, 경도
                radius=row['유사_업종_점포_수'],          # 원의 반지름
                color=None,                              # 원의 테두리 색상
                fill_color='orange',                           # 원을 채움
                fill_opacity=0.4,                     # 원의 내부를 채울 때의 투명도
                tooltip=tooltip
            ).add_to(m)                         # my_map에 원형 마커 추가

            folium.Marker(                           # 값 표시
                location=[row['위도'], row['경도']],   # 값 표시 위치- 위도, 경도
                icon=folium.DivIcon(
                    html=f"<div style='font-size: 8pt; font-weight: bold;'>{row['유사_업종_점포_수']}</div>"), # 값 표시 방식
            ).add_to(m)                         # my_map에 값 추가

        # Streamlit에 Folium 맵 표시
        folium_static(m)

        st.caption('2023년 3분기 기준')


    with col2:
        option = st.selectbox(
        '원하는 정보를 선택하세요',
        ('유동인구', '상주인구', '매출', '점포수'))

        if option == '유동인구':
            # 선택된 열의 데이터를 출력
            st.write(streamlit_df[['상권_코드_명', '행정동_코드_명', '총_유동인구_수']].
                        sort_values(by='총_유동인구_수', ascending=False).reset_index(drop=True), width=800)
            
        if option == '상주인구':
            # 선택된 열의 데이터를 출력
            st.write(streamlit_df[['상권_코드_명', '행정동_코드_명', '총_상주인구_수']].
                        sort_values(by='총_상주인구_수', ascending=False).reset_index(drop=True), width=800)

        if option == '매출':
            # 선택된 열의 데이터를 출력
            st.dataframe(streamlit_df[['상권_코드_명', '행정동_코드_명', '당월_매출_금액']].
                        sort_values(by='당월_매출_금액', ascending=False).reset_index(drop=True), width=800)
            
        if option == '점포수':
            # 선택된 열의 데이터를 출력
            st.dataframe(streamlit_df[['상권_코드_명', '행정동_코드_명', '영역_면적', '유사_업종_점포_수']].
                        sort_values(by='유사_업종_점포_수', ascending=False).reset_index(drop=True), width=800)
            
def AnalysisbyCommercialArea_page(streamlit_df, selected_TRDAR_CD_N, quarter_df):

    st.markdown("<h2 style='text-align: center;'>상권별 분석</h2>", unsafe_allow_html=True)
    st.caption('2023년 3분기 기준')

    # 3분기 데이터만 필터링
    streamlit_df_3 = streamlit_df.loc[(streamlit_df['기준_년'] == 2023) & (streamlit_df['기준_분기'] == 3), :]

    if not streamlit_df_3[streamlit_df_3['상권_코드_명'] == selected_TRDAR_CD_N].empty:
        # meteric 값
        formatted_sales = streamlit_df_3[streamlit_df_3['상권_코드_명'] == selected_TRDAR_CD_N]['당월_매출_금액'].iloc[0]
        count_store = streamlit_df_3[streamlit_df_3['상권_코드_명'] == selected_TRDAR_CD_N]['유사_업종_점포_수'].iloc[0]
        floating_population = streamlit_df_3[streamlit_df_3['상권_코드_명'] == selected_TRDAR_CD_N]['총_유동인구_수'].iloc[0]

        # 2분기 데이터만 필터링
        streamlit_df_2 = streamlit_df.loc[(streamlit_df['기준_년'] == 2023) & (streamlit_df['기준_분기'] == 2), :]

        # 2분기와의 차이값 계산
        formatted_sales_diff = formatted_sales - streamlit_df_2[streamlit_df_2['상권_코드_명'] == selected_TRDAR_CD_N]['당월_매출_금액'].iloc[0]
        count_store_diff = count_store - streamlit_df_2[streamlit_df_2['상권_코드_명'] == selected_TRDAR_CD_N]['유사_업종_점포_수'].iloc[0]
        floating_population_diff = floating_population - streamlit_df_2[streamlit_df_2['상권_코드_명'] == selected_TRDAR_CD_N]['총_유동인구_수'].iloc[0]

        # 상단 col
        col1, col2, col3 = st.columns(3)
        col1.metric("매출액", f"{formatted_sales:,.0f}원", f"{formatted_sales_diff:,.0f}원")
        col2.metric("점포수", f"{count_store:,.0f}개", f"{count_store_diff:,.0f}개")
        col3.metric("유동인구", f"{floating_population:,.0f}명", f"{floating_population_diff:,.0f}명")

        # 공백 추가
        st.empty()

        # 하단 col
        col1, col2 = st.columns(2)
        selected_3 = quarter_df.loc[(quarter_df['기준_년'] == 2023) & 
                                    (quarter_df['기준_분기'] == 3) & 
                                    (quarter_df['상권_코드_명'] == selected_TRDAR_CD_N), :]
        
        col1.write("<h6 style='text-align: center;'>시간대별 매출 금액</h6>", unsafe_allow_html=True)
        col1.bar_chart(selected_3, x="시간대", y="시간대_매출금액")

        col2.write("<h6 style='text-align: center;'>시간대별 유동인구</h6>", unsafe_allow_html=True)
        col2.bar_chart(selected_3, x="시간대", y="시간대_유동인구_수")


    else:
            st.error("해당 상권의 3분기 데이터가 없습니다.", icon="🚨")
            st.write("다른 상권을 선택해주세요")

def main():

    quarter_df = load_quarter_data()
    streamlit_df = load_streamlit_data()


    st.set_page_config(
        page_title="강남구 편의점 매출 예측 서비스",
        page_icon="🏪",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    choice = ""  # choice 변수를 미리 정의

    # 사이드바 메뉴
    with st.sidebar:
        menu = option_menu("메뉴 선택", ['홈', '강남구 상권 분석', '상권별 분석', '매출 예측'],
                   icons=['house', 'bi bi-clipboard2-data', 'bi bi-currency-dollar', 'bi bi-graph-up-arrow'], 
                   menu_icon="cast", 
                   default_index=0)        
        
        if menu == "홈":
            choice = "홈"

        elif menu == "강남구 상권 분석":
            choice = "강남구 상권 분석"

        elif menu == "상권별 분석":
            # 행정동 선택
            ADSTRD_CD = quarter_df['행정동_코드_명'].unique()
            selected_ADSTRD_CD = st.selectbox('행정동', ADSTRD_CD)

            # 선택된 행정동에 해당하는 상권명 가져오기
            TRDAR_CD_N = quarter_df[quarter_df['행정동_코드_명'] == selected_ADSTRD_CD]['상권_코드_명'].unique()

            # 상권명 선택
            selected_TRDAR_CD_N = st.selectbox('상권명', TRDAR_CD_N)

            choice = "상권별 분석"

    # 페이지 보이기
    if choice == '홈':
        main_page()
    
    elif choice == '강남구 상권 분석':
        commercial_page(streamlit_df)

    elif choice == '상권별 분석':
        AnalysisbyCommercialArea_page(streamlit_df, selected_TRDAR_CD_N, quarter_df)
    
    

if __name__ == '__main__':
    main()

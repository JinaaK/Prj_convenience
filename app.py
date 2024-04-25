# -*- coding:utf-8 -*-
import streamlit as st
from streamlit_option_menu import option_menu
import numpy as np
import pandas as pd
import folium
from streamlit_folium import folium_static
import plotly.express as px
import joblib
from sklearn.preprocessing import StandardScaler
from scipy.special import inv_boxcox
import re

# Streamlit 데이터 로드 함수
def load_streamlit_data():
    streamlit_df = pd.read_csv("./data/streamlit_df.csv")
    streamlit_df['점포당_매출액'] = (streamlit_df['당월_매출_금액'] / streamlit_df['유사_업종_점포_수']).round()
    streamlit_df['기준_년분기'] = streamlit_df['기준_년'].astype(str) + '년' + streamlit_df['기준_분기'].astype(str) + '분기'
    streamlit_df['점포당_남성_매출_금액'] = streamlit_df['남성_매출_금액'] / streamlit_df['유사_업종_점포_수'].round()
    streamlit_df['점포당_여성_매출_금액'] = streamlit_df['여성_매출_금액'] / streamlit_df['유사_업종_점포_수'].round()
    # 요일 목록
    weekdays = ['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일']

    # 요일별 매출액 계산
    for day in weekdays:
        col_name = f'점포당_{day}_매출액'
        streamlit_df[col_name] = streamlit_df[f'{day}_매출_금액'] / streamlit_df['유사_업종_점포_수'].round()
    return streamlit_df

# 시간대별 데이터 로드 함수
def load_quarter_data():
    quarter_df = pd.read_csv("./data/final_merged_update_store_age_df.csv")
    quarter_df['시간대별_점포당_매출액'] = (quarter_df['시간대_매출금액'] / quarter_df['유사_업종_점포_수']).round()
    return quarter_df

# 강남구 상권 분석 페이지 렌더링 함수
def commercial_page(streamlit_df):
    st.markdown("<h2 style='text-align: center;'>강남구 상권 분석</h2>", unsafe_allow_html=True)

    # 필요한 데이터만 추출
    streamlit_df = streamlit_df.loc[(streamlit_df['기준_년'] == 2023) & (streamlit_df['기준_분기'] == 3), :]

    col1, col2 = st.columns([5, 3])

    with col2:
        option_mapping = {
            '유동인구': '총_유동인구_수',
            '상주인구': '총_상주인구_수',
            '매출': '점포당_매출액',
            '점포수': '유사_업종_점포_수'
        }

        option = st.selectbox(
            '원하는 정보를 선택하세요',
            options=['유동인구', '상주인구', '매출', '점포수'],
            help= "매출 = 해당 상권 매출 금액 / 점포수"
            )

        if option in option_mapping:
            column_name = option_mapping[option]
            # 선택된 열의 데이터를 출력
            st.write(streamlit_df[['상권_코드_명', '행정동_코드_명', column_name]]
                        .sort_values(by=column_name, ascending=False)
                        .reset_index(drop=True),
                        use_container_width=True)

    with col1: 
        # 지도 생성
        m = folium.Map(location=[37.5172, 127.0473], zoom_start=13)  # 서울 위도, 경도를 중심으로 지도 생성
        
        # 각 점에 대한 정보를 Folium으로 추가
        for idx, row in streamlit_df.iterrows():

            # 툴팁에 표시할 내용 설정
            if option == '유동인구':
                radius = row['총_유동인구_수']/100000
                value = f"{int(row['총_유동인구_수'] / 10000)}만"
            elif option == '상주인구':
                radius = row['총_상주인구_수']/200
                value = f"{int(row['총_상주인구_수']/1000)}천"
            elif option == '매출':
                radius = row['점포당_매출액']/10000000
                value = f"{int(row['점포당_매출액']/1000000)}백만"
            elif option == '점포수':
                radius = row['유사_업종_점포_수']
                value = f"{int(row['유사_업종_점포_수'])}"

            # 툴팁에 표시할 내용 설정
            tooltip = f"상권명: {row['상권_코드_명']}<br>" \
                    f"매출금액: {row['당월_매출_금액']:,.0f}원<br>" \
                    f"유동인구: {row['총_유동인구_수']:,.0f}명<br>" \
                    f"총상주인구: {row['총_상주인구_수']:,.0f}명<br>"\
                    f"점포수: {row['유사_업종_점포_수']:,.0f}개<br>"\
                    
            

            folium.CircleMarker(                         # 원 표시
                location=[row['위도'], row['경도']],      # 원 중심- 위도, 경도
                radius=radius,          # 원의 반지름
                color=None,                              # 원의 테두리 색상
                fill_color='orange',                           # 원을 채움
                fill_opacity=0.4,                     # 원의 내부를 채울 때의 투명도
                tooltip=tooltip
            ).add_to(m)                         # my_map에 원형 마커 추가

            folium.Marker(                           # 값 표시
                location=[row['위도'], row['경도']],   # 값 표시 위치- 위도, 경도
                icon=folium.DivIcon(
                    html=f"<div style='font-size: 8pt; font-weight: bold; white-space: nowrap;'>{value}</div>"), # 값 표시 방식
            ).add_to(m)                         # my_map에 값 추가

        # Streamlit에 Folium 맵 표시
        folium_static(m, width=600)

        st.caption('2023년 3분기 기준')

# 상권별 분석 페이지 렌더링 함수
def AnalysisbyCommercialArea_page(streamlit_df, selected_TRDAR_CD_N, quarter_df):

    st.markdown("<h2 style='text-align: center;'>상권별 분석</h2>", unsafe_allow_html=True)
    st.caption('2023년 3분기 기준')

    # 3분기 데이터만 필터링
    streamlit_df_3 = streamlit_df.loc[(streamlit_df['기준_년'] == 2023) & (streamlit_df['기준_분기'] == 3), :]
    selected_streamlit_df_3 = streamlit_df_3[streamlit_df_3['상권_코드_명'] == selected_TRDAR_CD_N]

    if not selected_streamlit_df_3.empty:
        # meteric 값
        formatted_sales = streamlit_df_3[streamlit_df_3['상권_코드_명'] == selected_TRDAR_CD_N]['점포당_매출액'].iloc[0]
        count_store = streamlit_df_3[streamlit_df_3['상권_코드_명'] == selected_TRDAR_CD_N]['유사_업종_점포_수'].iloc[0]
        floating_population = streamlit_df_3[streamlit_df_3['상권_코드_명'] == selected_TRDAR_CD_N]['총_유동인구_수'].iloc[0]

        # 2분기 데이터만 필터링
        streamlit_df_2 = streamlit_df.loc[(streamlit_df['기준_년'] == 2023) & (streamlit_df['기준_분기'] == 2), :]

        # 2분기와의 차이값 계산
        formatted_sales_diff = formatted_sales - streamlit_df_2[streamlit_df_2['상권_코드_명'] == selected_TRDAR_CD_N]['점포당_매출액'].iloc[0]
        count_store_diff = count_store - streamlit_df_2[streamlit_df_2['상권_코드_명'] == selected_TRDAR_CD_N]['유사_업종_점포_수'].iloc[0]
        floating_population_diff = floating_population - streamlit_df_2[streamlit_df_2['상권_코드_명'] == selected_TRDAR_CD_N]['총_유동인구_수'].iloc[0]

        # 상단 col
        col1, col2, col3 = st.columns(3)
        col1.metric("매출액", f"{formatted_sales:,.0f}원", f"{formatted_sales_diff:,.0f}원", help= "2023년 3분기 기준 해당 상권 매출 금액 / 점포수")
        col2.metric("점포수", f"{count_store:,.0f}개", f"{count_store_diff:,.0f}개", help= "2023년 3분기 기준 해당 상권의 총 점포수입니다.")
        col3.metric("유동인구", f"{floating_population:,.0f}명", f"{floating_population_diff:,.0f}명", help= "2023년 3분기 기준 해당 상권의 총 유동인구수입니다.")

        # 공백 추가
        st.empty()

        # 하단 col
        selected_3 = quarter_df.loc[(quarter_df['기준_년'] == 2023) & 
                                    (quarter_df['기준_분기'] == 3) & 
                                    (quarter_df['상권_코드_명'] == selected_TRDAR_CD_N), :]
        
        selected = streamlit_df[streamlit_df['상권_코드_명'] == selected_TRDAR_CD_N]


        tab1, tab2, tab3, tab4 = st.tabs(["📈 매출", "🚉 유동인구", "👨‍👨‍👧‍👦 상주인구", "🏬 점포수"])

        with tab1:
            # 분기별 매출 추이
            st.subheader("분기별 매출 추이")
            fig_quarterly_sales = px.line(selected, x='기준_년분기', y='점포당_매출액')
            fig_quarterly_sales.update_layout(xaxis=dict(tickangle=0), autosize=True, width=1000)
            fig_quarterly_sales.update_yaxes(title="매출액")
            st.plotly_chart(fig_quarterly_sales)

            # 시간대 및 요일별 매출
            st.subheader("시간대 및 요일별 매출")
            col1, col2 = st.columns([1,1])

            with col1:
                fig_time_sales = px.bar(selected_3, x='시간대', y='시간대별_점포당_매출액', title='시간대별 매출', width=500)
                fig_time_sales.update_layout(xaxis=dict(tickangle=0), autosize=True)
                fig_time_sales.update_yaxes(title_text='매출액')  # y 축 이름 변경
                st.plotly_chart(fig_time_sales)

            with col2:
                week_sale_data = selected_streamlit_df_3[['상권_코드_명', 
                                                        '점포당_월요일_매출액', 
                                                        '점포당_화요일_매출액', 
                                                        '점포당_수요일_매출액', 
                                                        '점포당_목요일_매출액', 
                                                        '점포당_금요일_매출액',
                                                        '점포당_토요일_매출액',
                                                        '점포당_일요일_매출액']]
                            
                # 월요일 매출액 컬럼 이름 변경
                week_sale_data = week_sale_data.rename(columns={'점포당_월요일_매출액': '월요일',
                                                                '점포당_화요일_매출액': '화요일',
                                                                '점포당_수요일_매출액': '수요일',
                                                                '점포당_목요일_매출액': '목요일',
                                                                '점포당_금요일_매출액': '금요일',
                                                                '점포당_토요일_매출액': '토요일',
                                                                '점포당_일요일_매출액': '일요일'})
                # 요일 데이터
                week_sale_data = pd.melt(week_sale_data, 
                                        id_vars=['상권_코드_명'], 
                                        value_vars=['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일'], 
                                        var_name='요일', 
                                        value_name='매출_금액')

                fig_week_sales = px.bar(week_sale_data, x='요일', y='매출_금액', title='요일별 매출', width=500)
                fig_week_sales.update_layout(xaxis=dict(tickangle=0), autosize=True)
                fig_week_sales.update_yaxes(title_text='매출액')  # y 축 이름 변경
                st.plotly_chart(fig_week_sales)

            # demo
            st.subheader("성별 및 연령대별 매출")
            col1, col2 = st.columns([1,1])

            with col1:

                gender_data = selected_streamlit_df_3[['상권_코드_명', '점포당_남성_매출_금액', '점포당_여성_매출_금액']]
                # '성별' 열 추가 및 데이터 재구성
                gender_data = pd.melt(gender_data, 
                                    id_vars=['상권_코드_명'], 
                                    value_vars=['점포당_남성_매출_금액', '점포당_여성_매출_금액'], 
                                    var_name='성별', 
                                    value_name='매출_금액')
                # 파이차트 생성
                gender_sale = px.pie(gender_data, values='매출_금액', names='성별', title='성별 매출 비율', width=500)

                # 레이아웃 수정하여 범례를 왼쪽으로 옮기기
                gender_sale.update_layout(legend=dict(
                    x=0,  # x 위치를 0으로 설정하여 왼쪽으로 옮김
                    y=1.1  # y 위치 조정           
                ))

                # 그래프 출력
                st.plotly_chart(gender_sale)

            with col2:
                # 연령별 그래프
                age_data = selected_streamlit_df_3[['상권_코드_명', 
                                                    '연령대_10_매출_금액', 
                                                    '연령대_20_매출_금액', 
                                                    '연령대_30_매출_금액', 
                                                    '연령대_40_매출_금액', 
                                                    '연령대_50_매출_금액', 
                                                    '연령대_60_이상_매출_금액']]
                
                # 연령대 컬럼 이름 변경
                age_data = age_data.rename(columns={'연령대_10_매출_금액': '10대',
                                                    '연령대_20_매출_금액': '20대',
                                                    '연령대_30_매출_금액': '30대',
                                                    '연령대_40_매출_금액': '40대',
                                                    '연령대_50_매출_금액': '50대',
                                                    '연령대_60_이상_매출_금액': '60대 이상'})
                
                # 데이터 재구성 (열 변환)
                age_data = age_data.melt(id_vars='상권_코드_명', var_name='연령대', value_name='매출_금액')

                age_sale = px.bar(age_data, x='연령대', y='매출_금액', title='연령대별 매출 금액', width=500)
                age_sale.update_yaxes(title_text='매출액')  # y 축 이름 변경
                st.plotly_chart(age_sale)
        
        with tab2:
            st.subheader("분기별 유동인구 수 추이")
            fig_quarterly_population = px.line(selected, x='기준_년분기', y='총_유동인구_수')
            fig_quarterly_population.update_layout(xaxis=dict(tickangle=0), autosize=True, width=1000)
            fig_quarterly_population.update_yaxes(title_text='총 유동인구 수')  # y 축 이름 변경
            st.plotly_chart(fig_quarterly_population)

            # 시간대 및 요일별 매출
            st.subheader("시간대 및 요일별 유동인구 수")
            col1, col2 = st.columns(2)

            with col1:
                fig_time_population = px.bar(selected_3, x='시간대', y='시간대_유동인구_수', title='시간대별 유동인구 수', width=500)
                fig_time_population.update_layout(xaxis=dict(tickangle=0), autosize=True)
                fig_time_population.update_yaxes(title_text='유동인구 수')  # y 축 이름 변경
                st.plotly_chart(fig_time_population)

            with col2:

                week_floating_population_data = selected_streamlit_df_3[['상권_코드_명', 
                                                        '월요일_유동인구_수', 
                                                        '화요일_유동인구_수', 
                                                        '수요일_유동인구_수', 
                                                        '목요일_유동인구_수', 
                                                        '금요일_유동인구_수',
                                                        '토요일_유동인구_수',
                                                        '일요일_유동인구_수']]
                
                # 월요일 매출액 컬럼 이름 변경
                week_floating_population_data = week_floating_population_data.rename(columns={'월요일_유동인구_수': '월요일',
                                                                                            '화요일_유동인구_수': '화요일',
                                                                                            '수요일_유동인구_수': '수요일',
                                                                                            '목요일_유동인구_수': '목요일',
                                                                                            '금요일_유동인구_수': '금요일',
                                                                                            '토요일_유동인구_수': '토요일',
                                                                                            '일요일_유동인구_수': '일요일'})
                
                # 요일 데이터
                week_floating_population_data = pd.melt(week_floating_population_data, 
                                                        id_vars=['상권_코드_명'], 
                                                        value_vars=['월요일', 
                                                                    '화요일', 
                                                                    '수요일', 
                                                                    '목요일', 
                                                                    '금요일',
                                                                    '토요일',
                                                                    '일요일'], 
                                                        var_name='요일', 
                                                        value_name='유동인구 수')
                fig_week_floating = px.bar(week_floating_population_data, x='요일', y='유동인구 수', title='요일별 유동인구 수', width=500)
                fig_week_floating.update_layout(xaxis=dict(tickangle=0), autosize=True)
                st.plotly_chart(fig_week_floating)

            # demo
            st.subheader("성별 및 연령대별 유동인구 수")
            col1, col2 = st.columns(2)

            with col1:
                gender_floating_data = selected_streamlit_df_3[['상권_코드_명', '남성_유동인구_수', '여성_유동인구_수']]
                # '성별' 열 추가 및 데이터 재구성
                gender_floating_data = pd.melt(gender_floating_data, 
                                    id_vars=['상권_코드_명'], 
                                    value_vars=['남성_유동인구_수', '여성_유동인구_수'], 
                                    var_name='성별', 
                                    value_name='유동인구 수')
                # 파이차트 생성
                gender_floating = px.pie(gender_floating_data, values='유동인구 수', names='성별', title='성별 유동인구 비율', width=500)

                # 레이아웃 수정하여 범례를 왼쪽으로 옮기기
                gender_floating.update_layout(legend=dict(
                    x=0,  # x 위치를 0으로 설정하여 왼쪽으로 옮김
                    y=1.1  # y 위치 조정
                ))

                # 그래프 출력
                st.plotly_chart(gender_floating)

            with col2:
                # 연령별 그래프
                age_floating_data = selected_streamlit_df_3[['상권_코드_명', 
                                                    '연령대_10_유동인구_수', 
                                                    '연령대_20_유동인구_수', 
                                                    '연령대_30_유동인구_수', 
                                                    '연령대_40_유동인구_수', 
                                                    '연령대_50_유동인구_수', 
                                                    '연령대_60_이상_유동인구_수']]
                
                # 연령대 컬럼 이름 변경
                age_floating_data = age_floating_data.rename(columns={'연령대_10_유동인구_수': '10대',
                                                                '연령대_20_유동인구_수': '20대',
                                                                '연령대_30_유동인구_수': '30대',
                                                                '연령대_40_유동인구_수': '40대',
                                                                '연령대_50_유동인구_수': '50대',
                                                                '연령대_60_이상_유동인구_수': '60대 이상'})

                # 데이터 재구성 (열 변환)
                age_floating_data = age_floating_data.melt(id_vars='상권_코드_명', var_name='연령대', value_name='유동인구 수')

                age_floating_pop = px.bar(age_floating_data, x='연령대', y='유동인구 수', title='연령대별 유동인구 수', width=500)
                st.plotly_chart(age_floating_pop)

        with tab3:
            # demo
            st.subheader("성별 및 연령대별 상주인구 수")
            st.write(f"총 세대수는 {selected_3['총_가구_수'].iloc[0]:,.0f}세대입니다.")
            col1, col2 = st.columns(2)

            with col1:
                gender_resident_data = selected_streamlit_df_3[['상권_코드_명', '남성_상주인구_수', '여성_상주인구_수']]
                # '성별' 열 추가 및 데이터 재구성
                gender_resident_data = pd.melt(gender_resident_data, 
                                    id_vars=['상권_코드_명'], 
                                    value_vars=['남성_상주인구_수', '여성_상주인구_수'], 
                                    var_name='성별', 
                                    value_name='상주인구 수')
                # 파이차트 생성
                gender_resident = px.pie(gender_resident_data, values='상주인구 수', names='성별', title='성별 상주인구 비율', width=500)

                # 레이아웃 수정하여 범례를 왼쪽으로 옮기기
                gender_resident.update_layout(legend=dict(
                    x=0,  # x 위치를 0으로 설정하여 왼쪽으로 옮김
                    y=1.1  # y 위치 조정
                ))

                # 그래프 출력
                st.plotly_chart(gender_resident)

            with col2:
                # 연령별 그래프
                age_resident_data = selected_streamlit_df_3[['상권_코드_명', 
                                                    '연령대_10_상주인구_수', 
                                                    '연령대_20_상주인구_수', 
                                                    '연령대_30_상주인구_수', 
                                                    '연령대_40_상주인구_수', 
                                                    '연령대_50_상주인구_수', 
                                                    '연령대_60_이상_상주인구_수']]
                
                # 연령대 컬럼 이름 변경
                age_resident_data = age_resident_data.rename(columns={'연령대_10_상주인구_수': '10대',
                                                                '연령대_20_상주인구_수': '20대',
                                                                '연령대_30_상주인구_수': '30대',
                                                                '연령대_40_상주인구_수': '40대',
                                                                '연령대_50_상주인구_수': '50대',
                                                                '연령대_60_이상_상주인구_수': '60대 이상'})

                # 데이터 재구성 (열 변환)
                age_resident_data = age_resident_data.melt(id_vars='상권_코드_명', var_name='연령대', value_name='상주인구 수')

                age_resident = px.bar(age_resident_data, x='연령대', y='상주인구 수', title='연령대별 상주인구 수', width=500)
                st.plotly_chart(age_resident)
        
        with tab4:
            # 첫 번째 그래프 생성
            store = px.line(selected, x='기준_년분기', y='유사_업종_점포_수', title='점포수', width=1000)
            # 첫 번째 그래프의 Y축 범위 조정
            store.update_layout(yaxis=dict(range=[0, selected['유사_업종_점포_수'].max() + 10]), autosize=True)

            # 두 번째 그래프 생성
            store_openclose = px.bar(selected, x='기준_년분기', y=['개업_점포_수', '폐업_점포_수'], barmode='group', title='개·폐업수', width=1000)

            # 두 번째 그래프를 첫 번째 그래프에 추가
            for data in store_openclose.data:
                store.add_trace(data)

            # 그래프 출력
            st.plotly_chart(store)
            
    else:
        st.error("해당 상권의 3분기 데이터가 없습니다.", icon="🚨")
        st.write("다른 상권을 선택해주세요")

def Predict(quarter_df, Predict_selected_ADSTRD_CD, Predict_selected_TRDAR_CD_N):
    st.markdown("<h2>매출 예측</h2>", unsafe_allow_html=True)
    st.markdown("<h5>각 항목에 해당하는 값을 입력해주세요</h5>", unsafe_allow_html=True)
    st.caption('2023년 3분기 기준 해당 상권의 값이 설정되어 있습니다.', help='논현목련공원은 2023년 3분기 자료가 없어 2023년 2분기 기준으로 설정되어있습니다.')
 
    if Predict_selected_TRDAR_CD_N == '논현목련공원':
        selected_3 = quarter_df.loc[(quarter_df['기준_년'] == 2023) & 
                                        (quarter_df['기준_분기'] == 2) & 
                                        (quarter_df['상권_코드_명'] == Predict_selected_TRDAR_CD_N), :]
        
    else:
        selected_3 = quarter_df.loc[(quarter_df['기준_년'] == 2023) & 
                                    (quarter_df['기준_분기'] == 3) & 
                                    (quarter_df['상권_코드_명'] == Predict_selected_TRDAR_CD_N), :]
    
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            year = st.selectbox("기준 년도", list(range(2023, 2029)))
        with col2:
            quarter = st.selectbox("기준 분기", list(range(1, 5)))

        hour_ranges = ['00~06', '06~11', '11~14', '14~17', '17~21', '21~24']  # 시간대 범위
        floating_values = []  # 유동인구 수를 저장할 리스트

        # 각 시간대 범위에 대해 반복문 실행
        for hour_range in hour_ranges:
            # 해당 시간대 범위에 대한 유동인구 수 선택 슬라이더 생성
            floating_value = st.slider(f'{hour_range} 사이의 유동인구 수를 선택해주세요.', 
                                    round(min(quarter_df['시간대_유동인구_수'])), 
                                    round(max(quarter_df['시간대_유동인구_수'])), 
                                    value=int(round(selected_3.loc[selected_3['시간대'] == hour_range, '시간대_유동인구_수'])))
            # 생성된 슬라이더의 값을 리스트에 추가
            floating_values.append(floating_value)
                
        working_total = st.slider('총 직장인구 수를 선택해주세요.', round(min(quarter_df['총_직장_인구_수'])), 
                                  round(max(quarter_df['총_직장_인구_수'])),
                                  value=int(round(selected_3['총_직장_인구_수'].unique()[0])))

        st.write("각 연령대별 직장인구 비율을 입력하세요.(%)")
        # 10대부터 60대까지의 연령대 리스트
        age_groups = [10, 20, 30, 40, 50, 60]

        # 컬럼 리스트
        working_columns = st.columns(len(age_groups))

        # 각 연령대에 대한 직장인구 비율을 저장할 리스트 초기화
        working_population_ratios = []

        # 각 연령대에 대해 직장인구 비율 입력받음
        for i, age_group in enumerate(age_groups):
            with working_columns[i]:
                if age_group == 60:
                    column_name = "연령대_60_이상_직장_인구_비율"
                    selected_value = selected_3[column_name].unique() * 100
                    working_value = st.number_input(f"{age_group}대 이상 직장인구", min_value=0.0, max_value=100.0, value=float(selected_value[0]))
                else:
                    selected_value = selected_3[f'연령대_{age_group}_직장인구_비율'].unique() * 100
                    working_value = st.number_input(f"{age_group}대 직장인구", min_value=0.0, max_value=100.0, value=float(selected_value[0]))
                
                # 입력값을 리스트에 추가
                working_population_ratios.append(working_value)


        living_total = st.slider('총 상주인구 수를 선택해주세요.', round(min(quarter_df['총_상주인구_수'])), 
                                 round(max(quarter_df['총_상주인구_수'])),
                                 value=int(round(selected_3['총_상주인구_수'].unique()[0])))
        
        st.write("각 연령대별 상주인구 비율을 입력하세요.(%)")

        # 10대부터 60대까지의 연령대 리스트
        age_groups = [10, 20, 30, 40, 50, 60]

        # 컬럼 리스트
        living_columns = st.columns(len(age_groups))

        # 각 연령대에 대한 상주인구 비율을 저장할 리스트 초기화
        living_ratios = []

        for i, age_group in enumerate(age_groups):
            if i < len(living_columns):
                with living_columns[i]:
                    if age_group == 60:
                        column_name = "연령대_60_이상_상주인구_비율"
                        living_selected_value = selected_3[column_name].unique() * 100
                        living_value = st.number_input(f"{age_group}대 이상 상주인구", min_value=0.0, max_value=100.0, value=float(living_selected_value[0]))
                    else:
                        living_selected_value = selected_3[f'연령대_{age_group}_상주인구_비율'].unique() * 100
                        living_value = st.number_input(f"{age_group}대 상주인구", min_value=0.0, max_value=100.0, value=float(living_selected_value[0]))
                    
                    # 입력값을 리스트에 추가
                    living_ratios.append(living_value)

        house = st.slider('총 가구 수를 선택해주세요.', round(min(quarter_df['총_가구_수'])), 
                             round(max(quarter_df['총_가구_수'])),
                             value=int(round(selected_3['총_가구_수'].unique()[0])))        


        facility = st.slider('집객시설 수를 선택해주세요.', round(min(quarter_df['집객시설_수'])), 
                             round(max(quarter_df['집객시설_수'])),
                             value=int(round(selected_3['집객시설_수'].unique()[0])))
        
        income = st.slider('월평균 소득금액 선택해주세요.', round(min(quarter_df['월_평균_소득_금액'])), 
                           round(max(quarter_df['월_평균_소득_금액'])),
                           value=int(round(selected_3['월_평균_소득_금액'].unique()[0])))
        
        spending = st.slider('지출 총 금액을 선택해주세요.', round(min(quarter_df['지출_총금액'])), 
                             round(max(quarter_df['지출_총금액'])),
                             value=int(round(selected_3['지출_총금액'].unique()[0])))
        
        store = st.slider('편의점 점포 수를 선택해주세요.', round(min(quarter_df['유사_업종_점포_수'])), 
                          round(max(quarter_df['유사_업종_점포_수'])),
                          value=int(round(selected_3['유사_업종_점포_수'].unique()[0])))
        
        open = st.slider('개업 점포 수를 선택해주세요.', round(min(quarter_df['개업_점포_수'])), 
                         round(max(quarter_df['개업_점포_수'])),
                         value=int(round(selected_3['개업_점포_수'].unique()[0])))

    # 사용자 입력값을 딕셔너리로 변환
    user_data = {
        '기준_년': [year] * 6,
        '시간대': ['00_06', '06_11', '11_14', '14_17', '17_21', '21_24'],
        '시간대_유동인구_수': floating_values,
        '총_직장_인구_수': [working_total] * 6,
        '연령대_10_직장인구_비율': [working_population_ratios[0]] * 6,
        '연령대_20_직장인구_비율': [working_population_ratios[1]] * 6,
        '연령대_30_직장인구_비율': [working_population_ratios[2]] * 6,
        '연령대_40_직장인구_비율': [working_population_ratios[3]] * 6,
        '연령대_50_직장인구_비율': [working_population_ratios[4]] * 6,
        '총_상주인구_수': [living_total] * 6,
        '연령대_10_상주인구_비율': [living_ratios[0]] * 6,
        '연령대_20_상주인구_비율': [living_ratios[1]] * 6,
        '연령대_30_상주인구_비율': [living_ratios[2]] * 6,
        '연령대_40_상주인구_비율': [living_ratios[3]] * 6,
        '연령대_50_상주인구_비율': [living_ratios[4]] * 6,
        '연령대_60_이상_상주인구_비율': [living_ratios[5]] * 6,
        '총_가구_수': [house] * 6,
        '월_평균_소득_금액': [income] * 6,
        '유사_업종_점포_수': [store] * 6,
        '개업_점포_수': [open] * 6
    }
    user_data = pd.DataFrame(user_data)
    user_data['편의점_밀도'] = user_data['유사_업종_점포_수']/selected_3['영역_면적'].unique()
    user_data['편의점_밀도'] = user_data['편의점_밀도'].round(10) 
    
    # 분기에 해당하는 컬럼을 추가하고 초기화
    for i in range(1, 5):
        user_data[f'기준_분기_{i}'] = 0

    # 해당 분기에 해당하는 컬럼에 값을 할당
    user_data[f'기준_분기_{quarter}'] = 1

    # 상권코드명
    for code_name in quarter_df['상권_코드_명'].unique():
        user_data[f'상권_코드_명_{code_name}'] = 0

    user_data[f'상권_코드_명_{Predict_selected_TRDAR_CD_N}'] = 1

    # 행정동 코드 명
    for code_name in quarter_df['행정동_코드_명'].unique():
        user_data[f'행정동_코드_명_{code_name}'] = 0

    selected_code_name = selected_3['행정동_코드_명'].unique()[0]
    user_data[f'행정동_코드_명_{selected_code_name}'] = 1

    # 상권 구분 코드 명
    for code_name in quarter_df['상권_구분_코드_명'].unique():
        user_data[f'상권_구분_코드_명_{code_name}'] = 0

    selected_code_name = selected_3['상권_구분_코드_명'].unique()[0]
    user_data[f'상권_구분_코드_명_{selected_code_name}'] = 1

    # 특수 문자를 제거하고 언더스코어(_)로 대체합니다.
    user_data.columns = [re.sub(r'\W+', '_', col) for col in user_data.columns]

    if st.button('예측하기'):
        # 모델과 lambda 값을 로드
        model, lambda_ = joblib.load("model/best_lgbm_regression_bystore_model.pkl")
        # 범주형 변수와 숫자형 변수 구분
        cat_cols = ['시간대', '상권_구분_코드_명', '상권_코드_명', '행정동_코드_명']
        num_cols = user_data.columns.difference(cat_cols).tolist()

        ## 범주형 변수 더미화
        user_data = pd.get_dummies(user_data, columns=['시간대'])

        ## 더미 변수화된 값이 불리언 형태로 나왔다면 0과 1로 변환
        user_data.replace({True: 1, False: 0}, inplace=True)

        ## 숫자형 변수 정규화
        scaler = StandardScaler()
        user_data[num_cols] = scaler.fit_transform(user_data[num_cols])

        #예측
        pred = model.predict(user_data)
        # 예측 결과를 원래의 스케일로 되돌리기 위해 역 Box-Cox 변환 적용
        prediction = inv_boxcox(pred, lambda_)
        
        # 예측 결과(prediction)를 DataFrame으로 변환
        prediction_df = pd.DataFrame(prediction, columns=['추정_매출'])

        # 시간대 컬럼 추가
        prediction_df['시간대'] = ['00~06', '06~11', '11~14', '14~17', '17~21', '21~24']
        
        # 예측 결과와 시간대를 함께 출력
        #st.write(prediction_df)
        predict_total_sale = format(int(prediction_df['추정_매출'].sum()), ',')
        st.write(f'{Predict_selected_TRDAR_CD_N} 상권의 {year}년 {quarter}분기 추정 매출액은 {predict_total_sale}원입니다.')
        predict_time_sales = px.bar(prediction_df, x='시간대', y='추정_매출', title='시간대별 추정 매출')
        predict_time_sales.update_layout(xaxis=dict(tickangle=0), autosize=True)
        predict_time_sales.update_yaxes(title_text='추정 매출액')
        st.plotly_chart(predict_time_sales)

# 메인 함수
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
        menu = option_menu("메뉴 선택", ['강남구 상권 분석', '상권별 분석', '매출 예측'],
                   icons=['bi bi-clipboard2-data', 'bi bi-currency-dollar', 'bi bi-graph-up-arrow'], 
                   menu_icon="cast", 
                   default_index=0)        
        
        if menu == "강남구 상권 분석":
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

        elif menu == "매출 예측":
           # 행정동 선택
            ADSTRD_CD = quarter_df['행정동_코드_명'].unique()
            Predict_selected_ADSTRD_CD = st.selectbox('행정동', ADSTRD_CD)

            # 선택된 행정동에 해당하는 상권명 가져오기
            TRDAR_CD_N = quarter_df[quarter_df['행정동_코드_명'] == Predict_selected_ADSTRD_CD]['상권_코드_명'].unique()

            # 상권명 선택
            Predict_selected_TRDAR_CD_N = st.selectbox('상권명', TRDAR_CD_N)

            choice = "매출 예측"

    # 페이지 보이기
    if choice == '강남구 상권 분석':
        commercial_page(streamlit_df)

    elif choice == '상권별 분석':
        AnalysisbyCommercialArea_page(streamlit_df, selected_TRDAR_CD_N, quarter_df)

    elif choice == '매출 예측':
        Predict(quarter_df, Predict_selected_ADSTRD_CD, Predict_selected_TRDAR_CD_N)
    
# 메인 함수 호출
if __name__ == '__main__':
    main()

import plotly.express as px
import altair as alt
import pydeck as pdk
import matplotlib.pyplot as plt
import geopandas as gpd
import transbigdata as tbd
import re
import numpy as np
import pandas as pd
import os
import streamlit as st
from millify import millify
# page config
st.set_page_config(
    page_title="出租车数据仪表盘",
    page_icon="🏂",
    layout="wide",
    initial_sidebar_state="expanded")


@st.cache_resource
# 放入缓存
def load_data(subdirectory):
    # 初始化一个空的DataFrame用于存储数据
    merged_data = pd.DataFrame()

    # 遍历所选子目录下的所有文件
    for filename in os.listdir(subdirectory):
        file_path = os.path.join(subdirectory, filename)
        # 检查文件是否为txt文件
        if file_path.endswith('.txt'):
            # 尝试读取文件数据，并合并到已有数据中
            try:
                data = pd.read_csv(file_path)
                merged_data = pd.concat([merged_data, data], ignore_index=True)
            except Exception as e:
                print(f"Error processing file {file_path}: {e}")
    return merged_data


with st.sidebar:
    st.sidebar.title('出租车数据仪表盘')
    week_list = ['week1', 'week2', 'week3', 'week4']
    selected_week = st.selectbox('周选择', week_list)
    color_theme_list = ['blues', 'cividis', 'greens', 'inferno',
                        'magma', 'plasma', 'reds', 'rainbow', 'turbo', 'viridis']
    selected_color_theme = st.selectbox(
        '主题', color_theme_list)
# 选择对应的子目录
    subdirectory = os.path.join('static/1000taxidata/odddata', selected_week)


def make_scattermap():
    merged_data = load_data(subdirectory)
    s_data = merged_data[['slat', 'slon']]
    e_data = merged_data[['elat', 'elon']]
    s_data.rename(columns={'slat': 'lat', 'slon': 'lon'}, inplace=True)
    e_data.rename(columns={'elat': 'lat', 'elon': 'lon'}, inplace=True)
    radius = st.slider('半径', 1, 20, 5)

    st.pydeck_chart(pdk.Deck(
        initial_view_state=pdk.ViewState(
            latitude=30.659462,
            longitude=104.065735,
            zoom=11,
            pitch=0,
            bearing=0,
            max_zoom=16
        ),
        # map_style='https://basemaps.cartocdn.com/gl/positron-nolabels-gl-style/style.json',
        layers=[
            pdk.Layer(
                'ScatterplotLayer',
                data=s_data,
                get_position='[lon, lat]',
                pickable=True,
                extruded=True,
                opacity=0.8,
                get_color='[255, 0, 128,160]',
                get_radius=radius,
            ),
            pdk.Layer(
                'ScatterplotLayer',
                data=e_data,
                get_position='[lon, lat]',
                pickable=True,
                extruded=True,
                opacity=0.8,
                get_color='[0, 128, 255,160]',
                get_radius=radius,
            )
        ]
    ))


col = st.columns((1.5, 4.5, 2), gap='medium')
with col[0]:
    st.markdown('#### 收益/损失')
    data = load_data(subdirectory)
    selected_index = week_list.index(selected_week)
    previous_index = (selected_index - 1) % len(week_list)  # 获取上一周的索引
    previous_week = week_list[previous_index]  # 获取上一周的名称
    pre_subdirectory = os.path.join(
        'static/1000taxidata/odddata', previous_week)
    pre_data = load_data(pre_subdirectory)

    pre_num_records = len(pre_data)
    num_records = len(data)

    with st.container(border=True):
        st.metric(label="订单总数", value=millify(num_records),
                  delta=millify(num_records - pre_num_records))

    # 将 'stime' 和 'etime' 列转换为日期时间类型
    data['stime'] = pd.to_datetime(data['stime'])
    data['etime'] = pd.to_datetime(data['etime'])
    pre_data['stime'] = pd.to_datetime(pre_data['stime'])
    pre_data['etime'] = pd.to_datetime(pre_data['etime'])
    # 计算每辆出租车的行程持续时间
    data['duration'] = (data['etime'] - data['stime']
                        ).dt.total_seconds() / 3600
    pre_data['duration'] = (pre_data['etime'] - pre_data['stime']
                            ).dt.total_seconds() / 3600
    # 其余部分不变
    total_working_hours = 18  # 总工作时间为18小时

    total_trip_duration = data.groupby('id')['duration'].sum()
    pre_total_trip_duration = pre_data.groupby('id')['duration'].sum()
    utilization_rate = total_trip_duration / total_working_hours
    pre_utilization_rate = pre_total_trip_duration / total_working_hours
    # 输出利用率
    with st.container(border=True):
        st.metric(label="利用率", value=str(round(utilization_rate.mean()*100))+'%',
                  delta=str(round(utilization_rate.mean()*100 - pre_utilization_rate.mean()*100))+'%')

    # 首先，将时间列转换为日期，以便按天进行分组
    data['date'] = pd.to_datetime(data['stime']).dt.date

    # 然后，按日期进行分组并计算每天的订单数
    daily_orders = data.groupby('date').size().reset_index(name='orders')
    order_list = daily_orders['orders'].to_list()
    order_df = pd.DataFrame(
        {
            'orders': [order_list]
        }
    )
    st.data_editor(
        order_df,
        column_config={
            "orders": st.column_config.LineChartColumn(
                "订单数(每天)",
                width="medium",
                help="The sales volume in the last 6 months",
                y_min=30000,
                y_max=max(order_list),
            ),
        },
        hide_index=True,
        use_container_width=True,
    )

with col[1]:
    st.markdown('#### 乘客目的地和热门地点')
    make_scattermap()
with col[2]:
    st.markdown('#### Top States')
    df_groupby_id = data.groupby('id').size().sort_values(
        ascending=False).reset_index(name='orders')
    st.dataframe(df_groupby_id,
                 column_order=("id", "orders"),
                 hide_index=True,
                 width=None,
                 use_container_width=True,
                 column_config={
                     "id": st.column_config.TextColumn(
                         "id",
                     ),
                     "orders": st.column_config.ProgressColumn(
                         "订单总数",
                         format="%f",
                         min_value=0,
                         max_value=df_groupby_id['orders'].max(),
                     )}
                 )

    with st.expander('About', expanded=True):
        st.write('''
            - 数据来源: 成都2014八月出租车数据,随机抽取1000辆出租车
            - :orange[**收入/损失**]: 以周计，订单总数是这一周1000辆出租车的总订单数，以及较上周的数据浮动情况，:green[**绿色**]表示上升，:red[**红色**]表示下降.
            ''')

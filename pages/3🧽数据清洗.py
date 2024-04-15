import streamlit as st
from time import sleep
from stqdm import stqdm
from datetime import datetime
import pandas as pd
import transbigdata as tbd

st.title('🧽数据清洗中心')


@st.cache_data  # 保存函数
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode('utf-8')


# 文件上传
uploaded_file = st.file_uploader(
    "# 文件上传", type=['txt', 'csv'])

clear_opt = st.multiselect(
    '清洗方法',
    ['删除瞬时变化', '删除漂移', '稀疏化', '轨迹致密化', '删除相同的数据'],
    help='删除瞬时变化:\n从出租车数据中删除乘客携带状态的瞬时变化记录。这些异常记录会影响旅行订单判断。判断方法：如果同一车辆上一条记录和下一条记录的乘客状态与该记录不同,则应删除该记录。删除轨迹数据中的漂移:漂移定义为速度大于速度限制或当前点与下一个点之间的距离大于距离限制或当前点与前一点和下一个点之间的角度小于角度限制的数据。限速默认为80km/h，距离限制默认为1000m'
)
if '稀疏化' in clear_opt:
    time_gap = st.number_input('输入时间间隔,以秒为单位', step=60, value=60*60)
op_opt = st.multiselect(
    '处理过程',    ['提取OD', '提取配送和闲置轨迹'])
encoding_opt = st.selectbox(
    '编码格式',
    ['utf', 'gbk']
)
if uploaded_file is not None:
    # To read file as bytes:
    dataframe = pd.read_csv(uploaded_file, encoding=encoding_opt)
    # 显示读取的信息
    st.write(dataframe)
    if dataframe is not None:
        # 数据不包含行，则取第一行的结果展示
        if dataframe.columns is None:
            col_list = dataframe[0]
        col_list = dataframe.columns

        # 4行用来选择具体的行信息
        col1, col2, col3, col4 = st.columns(4)
        # 选择车牌号
        with col1:
            id_sel = st.selectbox(
                'id(车牌号)',
                col_list,
                help='选择数据表中的id行,它用来标识车辆,通常是车牌号(VehicleNum)或者字符串(id)'
            )
        col_list = col_list.delete(col_list.get_loc(id_sel))

        # 选择时间行
        with col2:
            time_sel = st.selectbox(
                '时间',
                col_list
            )
        col_list = col_list.delete(col_list.get_loc(time_sel))

        # 选择经度行
        with col3:
            lon_sel = st.selectbox(
                '经度',
                col_list
            )
        col_list = col_list.delete(col_list.get_loc(lon_sel))

        # 选择纬度行
        with col4:
            lat_sel = st.selectbox(
                '纬度',
                col_list
            )

    # 若包含载客信息
    if st.checkbox('包含载客信息'):
        col_list = col_list.delete(col_list.get_loc(lat_sel))
        OpenStatus_sel = st.selectbox(
            '选择载客状态/乘客状态/空重车状态',
            col_list,
            help='选择载客信息行,代表出租车是否载客,常见的行名为OpenStatus'
        )

placeholder = st.empty()
if st.button('点击开始'):
    placeholder.txt('转换时间格式中')
    try:
        dataframe[time_sel] = pd.to_datetime(dataframe[time_sel])
    except TypeError:
        placeholder.warning(TypeError)
    placeholder.txt('finish🍪')
    if '稀疏化' in clear_opt:
        placeholder.txt('开始轨迹稀疏化...')
        if (time_gap is None) & (int(time_gap) == 0):
            time_gap = 60*60
        try:
            dataframe = tbd.traj_sparsify(
                dataframe, col=[id_sel, time_sel, lon_sel, lat_sel], timegap=time_gap, method='subsample')
        except Exception:
            placeholder.warning(Exception)
        placeholder.txt('完成')

    if '删除漂移' in clear_opt:
        # 删除轨迹数据中的漂移。
        placeholder.txt('删除轨迹数据中的漂移')
        try:
            dataframe = tbd.traj_clean_drift(dataframe, col=[
                id_sel, time_sel, lon_sel, lat_sel], method='twoside', speedlimit=80, dislimit=1000)
        except:
            placeholder.warning(Exception)

    if '删除相同的数据' in clear_opt:
        placeholder.txt("删除与前后数据信息相同的数据")
        try:
            dataframe = tbd.traj_clean_redundant(
                dataframe, col=[id_sel, time_sel, lon_sel, lat_sel])
        except Exception:
            placeholder.warning(Exception)

    if '删除相同的数据' in clear_opt:
        placeholder.txt('从出租车数据中删除乘客携带状态的瞬时变化记录')
        try:
            dataframe = tbd.clean_taxi_status(
                dataframe, col=[id_sel, time_sel, OpenStatus_sel], timelimit=None)
        except Exception:
            placeholder.warning(Exception)

    if '提取OD' in op_opt:

        placeholder.write('提取OD信息')
        try:
            oddata = tbd.taxigps_to_od(
                dataframe, col=[id_sel, time_sel, lon_sel, lat_sel, OpenStatus_sel])
        except Exception:
            placeholder.warning(Exception)

    if '提取配送和闲置轨迹' in op_opt:
        placeholder.txt("提取配送和闲置行程的轨迹点")
        try:
            data_deliver, data_idle = tbd.taxigps_traj_point(
                dataframe, oddata, col=[id_sel, time_sel, lon_sel, lat_sel, OpenStatus_sel])
        except Exception:
            placeholder.warning(Exception)
# 假的进度条
    for _ in stqdm(range(50)):
        sleep(0.05)
# 获取当前时间
    placeholder.empty()
    current_time = datetime.now()
# download data
    col_1, col_2, col_3, col_4 = st.columns(4)
    with col_1:
        st.download_button(
            label="下载清洗后的数据",
            data=convert_df(dataframe),
            file_name=f'clear_data-{current_time}.csv',
            mime='txt/csv',
            key='download_clear'
        )
    with col_2:
        st.download_button(
            label="下载OD数据CSV",
            data=convert_df(oddata),
            file_name=f'oddata-{current_time}.csv',
            mime='txt/csv',
            key='download_od'
        )
    with col_3:
        st.download_button(
            label="下载闲置轨迹数据",
            data=convert_df(data_idle),
            file_name=f'data_idel-{current_time}.csv',
            mime='txt/csv',
            key='download_idle'
        )
    with col_4:
        st.download_button(
            label="下载配送轨迹数据",
            data=convert_df(data_deliver),
            file_name=f'datad_liver_{current_time}.csv',
            mime='txt/csv',
            key='download_deliver'
        )

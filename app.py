import streamlit as st
import os
import plotly.express as px
import json
import pandas as pd

# 配置页面标题和图标
st.set_page_config(page_title="物流订单异常分析与处理助手", page_icon="💻️", layout="wide")
st.title("物流订单异常分析与处理助手")
st.caption("💻️ 基于Python数据分析和大模型的物流异常监控平台")

# 定义文件
DATA_DIR = 'data/processed data'
CLEANED_PATH = os.path.join(DATA_DIR, 'cleaned_olist_orders_dataset.csv')  # join的意思是连接
ANOMALY_PATH = os.path.join(DATA_DIR, 'anomaly_orders.csv')
AI_PATH = os.path.join(DATA_DIR, 'ai_analysis_results.csv')

# 读取文件(函数)
@st.cache_data  # streamlit装饰器，缓存数据
def load_data(path):
    if os.path.exists(path):
        return pd.read_csv(path)
    else:
        return pd.DataFrame()

cleaned_df = load_data(CLEANED_PATH)
anomaly_df = load_data(ANOMALY_PATH)
ai_df = load_data(AI_PATH)


# 检查数据是否存在
if cleaned_df.empty:
    st.error("数据不存在")
    st.stop()
if anomaly_df.empty:
    st.warning("异常数据不存在")
if ai_df.empty:
    st.warning("AI分析数据不存在")


# 订单运营的总览

total_orders = len(cleaned_df)
anomaly_orders = len(anomaly_df)

if total_orders > 0:
    anomaly_rate = round(anomaly_orders / total_orders * 100, 2)
else:
    anomaly_rate = 0

# 将指标展示在网页上
st.subheader("一、订单运营总览")
col1, col2, col3 = st.columns(3)  # 将网页横向分成3列
col1.metric("总订单数", f"{total_orders:,}")   # metric()用来展示关键指标卡片
col2.metric("异常订单数", f"{anomaly_orders:,}")
col3.metric("异常订单率", f"{anomaly_rate:.2f}%")

st.divider()  # 添加分割线


# 订单异常分析
st.subheader("二、订单异常分析")
if (not anomaly_df.empty and 'anomaly_type' in anomaly_df.columns):
    anomaly_counts = (anomaly_df['anomaly_type'].fillna('未知类型').value_counts().reset_index())

    anomaly_counts.columns = ['异常类型', '异常订单数']
    col1, col2 = st.columns(2)

    with col1:  # 绘制柱形图
        fig_bar = px.bar(anomaly_counts, x='异常类型', y='异常订单数',title='不同异常类型订单数量', text='异常订单数')
        st.plotly_chart(fig_bar, use_container_width=True)

    with col2:  # 绘制饼图
        fig_pie = px.pie(anomaly_counts, names='异常类型', values='异常订单数', title='不同异常类型订单占比')
        st.plotly_chart(fig_pie, use_container_width=True)

else:
    st.info("异常订单数据中暂无anomaly_type字段，请检查数据")

st.divider()    # 添加分割线

# 异常订单的查询
st.subheader("三、异常订单查询")

if not anomaly_df.empty:
    filtered_df = anomaly_df.copy()

    # 异常类型筛选
    if 'anomaly_type' in filtered_df.columns:
        anomaly_types = filtered_df['anomaly_type'].dropna().unique().tolist()  # dropna()用来删除空值，unique()用来获取唯一值，tolist()用来转换为列表

        selected_type = st.multiselect("选择异常类型", anomaly_types, default=anomaly_types)  # multiselect()用来创建多选框
        filtered_df = filtered_df[filtered_df['anomaly_type'].isin(selected_type)]  # isin()用来表示筛选是否满足条件,在外面再套一个filtered_df,使结果返回

    # 风险等级筛选
    if 'risk_level' in filtered_df.columns:
        risk_levels = filtered_df['risk_level'].dropna().unique().tolist()

        selected_level = st.multiselect("选择风险等级", risk_levels, default=risk_levels)
        filtered_df = filtered_df[filtered_df['risk_level'].isin(selected_level)]

    # 订单编号搜索
    if 'order_id' in filtered_df.columns:
        search_id = st.text_input("输入订单编号")
        if search_id:
            filtered_df = filtered_df[filtered_df['order_id'].astype(str).str.contains(search_id, na=False, case=False)]
            # str.contains()用来筛选包含指定字符串的行，na=False表示忽略空值，case=False表示忽略大小写

    st.write(f"已找到 {len(filtered_df)} 个订单")

    st.dataframe(filtered_df, use_container_width=True, hide_index=True)  # 将表格转化为网页,use_container_width=True表示使用容器宽度，hide_index=True表示隐藏索引

else:
    filtered_df = pd.DataFrame()

st.divider()    # 添加分割线



# AI 智能诊断
st.subheader("四、AI智能诊断")

if (not filtered_df.empty and 'order_id' in filtered_df.columns):
    selected_order = st.selectbox("选择订单编号", filtered_df['order_id'].astype(str).tolist())
    # selectbox 用来创建下拉选择框

    st.markdown(f"### 选择的订单编号是: {selected_order}")  # markdown()用来添加标题

    # 查找订单原始异常信息
    order_info = filtered_df[filtered_df['order_id'].astype(str) == selected_order]
    with st.expander("订单原始异常信息"):   # expander()用来创建可展开也可收起的区域
        st.json(order_info.iloc[0].to_dict())   # iloc[0]表示获取第一行数据，to_dict()用来转换为字典

    # 查找对应AI分析的结果
    if (not ai_df.empty and 'order_id' in ai_df.columns):
        ai_result = ai_df[ai_df['order_id'].astype(str) == selected_order]
        if (not ai_result.empty and ai_result.iloc[0].get('analysis_status') == 'success'):
            result = ai_result.iloc[0]

    # 展示AI分析结果
            st.markdown(f"### AI分析结果")  # markdown()用来添加标题
            st.info(str(result.get('analysis_summary', '暂无分析结果')))  # info()用来添加信息,如果result.get('analysis_summary')为空，则显示暂无分析结果

    # 将AI分析的结果的json形式转化为容易查看的网页展示方式
            def show_json_field(title, value):
                st.markdown(f"#### {title}")
                try:
                    if isinstance(value, str):
                        value = json.loads(value)
                        st.json(value)
                except Exception:
                    st.write(value)

            show_json_field("可能原因:", result.get('possible_causes', []))
            show_json_field("分析依据:", result.get('evidence', []))
            show_json_field("处理建议:", result.get('recommendations', []))
            show_json_field("待核实事项:", result.get('verification_items', []))

            st.write('AI分析置信度:', result.get('confidence', '未知'))
            st.write('Python计算风险等级:', result.get('risk_level', '暂无'))
        else:
            st.warning("暂无对应订单的AI分析结果")
    else:
        st.warning("暂无AI分析结果文件")
else:
    st.info("请先筛选出异常订单，再选择订单编号进行AI智能诊断")
st.divider()    # 添加分割线


# 数据导出
st.subheader("五、异常数据导出")

if not filtered_df.empty:
    csv_data = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button("下载当前筛选的异常订单文件", data = csv_data, file_name="异常订单分析结果.csv", mime="text/csv")

st.caption('物流订单异常分析助手 | Python + Pandas + Streamlit + 大语言模型')


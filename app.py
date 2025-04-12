import streamlit as st
import akshare as ak
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os
import httpx
from dotenv import load_dotenv
from technical_analysis import calculate_all_indicators
from deepseek_client import DeepSeekClient
import numpy as np
from datetime import date, time

# 加载环境变量
load_dotenv()

# 设置页面配置
st.set_page_config(
    page_title="期货策略分析",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化DeepSeek客户端
deepseek_client = DeepSeekClient()

# 获取期货实时价格
def get_current_price(symbol):
    try:
        # 使用内盘期货实时行情接口
        df = ak.futures_zh_realtime(symbol=symbol)
        if df.empty:
            return {"error": f"未找到期货代码 {symbol}"}
        return df.iloc[0].to_dict()
    except Exception as e:
        return {"error": str(e)}

# 获取期货历史价格
def get_prices(symbol, start_date=None, end_date=None):
    try:
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y%m%d")
            
        # 获取历史数据
        # 首先获取主力合约代码
        symbol_info = ak.futures_zh_realtime(symbol=symbol)
        if symbol_info.empty:
            return {"error": f"未找到期货代码 {symbol}"}
        
        main_contract = symbol_info.iloc[0]['symbol']
        # 使用期货历史行情接口
        df = ak.futures_main_sina(symbol=main_contract, start_date=start_date, end_date=end_date)
        
        # 确保列名统一
        if 'date' not in df.columns and '日期' in df.columns:
            df = df.rename(columns={
                '日期': 'date',
                '开盘价': 'open',
                '最高价': 'high',
                '最低价': 'low',
                '收盘价': 'close',
                '成交量': 'volume'
            })
        return df
    except Exception as e:
        return {"error": str(e)}

# 获取期货相关新闻
def get_news(symbol):
    try:
        df = ak.futures_news_shmet(symbol="全部")
        # 使用模糊匹配查找相关新闻
        result = df[df['内容'].str.contains(symbol, case=False, na=False)]
        # 取最新的10条新闻
        result = result.head(10)
        return result.rename(columns={"发布时间": "date", "内容": "title"})
    except Exception as e:
        return {"error": str(e)}

# 获取技术分析指标
def get_technical_indicators(df):
    try:
        return calculate_all_indicators(df)
    except Exception as e:
        return {"error": str(e)}

# 调用DeepSeek API进行分析
def analyze_with_deepseek(symbol, data):
    try:
        # 处理日期序列化问题
        def json_serial(obj):
            """JSON序列化函数，处理日期/时间和其他特殊类型"""
            if isinstance(obj, (datetime, pd.Timestamp)):
                return obj.isoformat()
            if isinstance(obj, pd.DatetimeIndex):
                return obj.astype(str).tolist()
            if isinstance(obj, pd.Series):
                return obj.tolist()
            if isinstance(obj, pd.DataFrame):
                return obj.to_dict(orient='records')
            if isinstance(obj, np.integer):
                return int(obj)
            if isinstance(obj, np.floating):
                return float(obj)
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            if isinstance(obj, (date, time)):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")
        
        messages = [
            {
                "role": "system",
                "content": "你是一个专业的期货分析师，请根据提供的数据进行简明扼要的分析。"
            },
            {
                "role": "user",
                "content": f"请分析{symbol}的以下数据：\n{json.dumps(data, default=json_serial, ensure_ascii=False)}"
            }
        ]
        
        # 使用DeepSeekClient进行调用
        response = deepseek_client.client.chat.completions.create(
            model="bot-20250329163710-8zcqm",
            messages=messages,
            temperature=0.7,
            max_tokens=2000
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"AI分析调用失败: {str(e)}"

# 页面标题
st.title("期货策略分析平台")

# 侧边栏 - 期货品种选择
with st.sidebar:
    st.header("参数设置")
    # 获取期货品种列表，使用内盘期货品种表
    with st.spinner("加载期货列表..."):
        try:
            # 获取所有期货品种的标记
            futures_list = ak.futures_symbol_mark()
            if 'symbol' not in futures_list.columns:
                st.error("加载期货列表失败: 返回数据格式不正确")
                futures_list = pd.DataFrame({"symbol": ["白糖"]})  # 提供默认值
        except Exception as e:
            st.error(f"加载期货列表失败: {e}")
            futures_list = pd.DataFrame({"symbol": ["白糖"]})  # 提供默认值
    symbol = st.selectbox(
        "选择期货品种",
        options=futures_list['symbol'].tolist(),
        index=0
    )
    
    # 时间范围选择
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    date_range = st.date_input(
        "选择时间范围",
        value=(start_date, end_date),
        max_value=end_date
    )
    
    # 分析按钮
    analyze_clicked = st.button("开始分析")
    
    st.markdown("---")
    
    # MCP服务信息
    st.info("本应用同时提供MCP服务，可与Claude等AI助手集成")
    if st.button("如何使用MCP?"):
        st.write("""
        **MCP集成步骤:**
        1. 运行 `python mcp_server.py`
        2. 在Claude Desktop中配置MCP
        3. 通过AI助手使用期货分析工具
        """)

# 主页面
tab1, tab2, tab3, tab4 = st.tabs(["行情概览", "技术指标", "相关新闻", "AI分析"])

with tab1:
    # 行情概览标签页
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("实时行情")
        with st.spinner("获取实时行情..."):
            current_data = get_current_price(symbol)
        
        if "error" in current_data:
            st.error(f"获取实时行情失败: {current_data['error']}")
        else:
            st.metric(
                label="最新价格",
                value=current_data.get("last_price"),
                delta=current_data.get("change")
            )
            
            # 显示更多行情信息
            st.dataframe(pd.DataFrame([current_data]))
    
    with col2:
        st.subheader("历史走势")
        with st.spinner("获取历史数据..."):
            # 确保日期是字符串格式
            start_str = date_range[0].strftime("%Y%m%d") if isinstance(date_range[0], (datetime, date)) else date_range[0]
            end_str = date_range[1].strftime("%Y%m%d") if isinstance(date_range[1], (datetime, date)) else date_range[1]
            
            df_hist = get_prices(
                symbol, 
                start_date=start_str,
                end_date=end_str
            )
        
        if isinstance(df_hist, pd.DataFrame) and not df_hist.empty:
            # 绘制K线图
            fig = go.Figure(data=[go.Candlestick(
                x=df_hist['date'],
                open=df_hist['open'],
                high=df_hist['high'],
                low=df_hist['low'],
                close=df_hist['close']
            )])
            
            fig.update_layout(
                title=f"{symbol} K线图",
                yaxis_title="价格",
                xaxis_title="日期"
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error(f"无法获取历史数据: {df_hist}")

with tab2:
    # 技术指标标签页
    st.subheader("技术分析指标")
    
    with st.spinner("计算技术指标..."):
        # 确保日期是字符串格式
        start_str = date_range[0].strftime("%Y%m%d") if isinstance(date_range[0], (datetime, date)) else date_range[0]
        end_str = date_range[1].strftime("%Y%m%d") if isinstance(date_range[1], (datetime, date)) else date_range[1]
        
        df_hist = get_prices(
            symbol, 
            start_date=start_str,
            end_date=end_str
        )
        
        if isinstance(df_hist, pd.DataFrame) and not df_hist.empty:
            df = get_technical_indicators(df_hist)
            
            if isinstance(df, pd.DataFrame):
                # 技术指标子标签页
                subtab1, subtab2, subtab3, subtab4 = st.tabs(["移动平均", "MACD", "RSI & KDJ", "布林带"])
                
                with subtab1:
                    # 移动平均线
                    fig_ma = go.Figure()
                    fig_ma.add_trace(go.Scatter(x=df['date'], y=df['close'], name='价格'))
                    for period in [5, 10, 20, 60]:
                        if f'MA{period}' in df.columns:
                            fig_ma.add_trace(go.Scatter(x=df['date'], y=df[f'MA{period}'], name=f'MA{period}'))
                    fig_ma.update_layout(title='移动平均线')
                    st.plotly_chart(fig_ma, use_container_width=True)
                    
                with subtab2:
                    # MACD
                    if 'MACD' in df.columns and 'Signal' in df.columns and 'MACD_Hist' in df.columns:
                        fig_macd = go.Figure()
                        fig_macd.add_trace(go.Scatter(x=df['date'], y=df['MACD'], name='MACD'))
                        fig_macd.add_trace(go.Scatter(x=df['date'], y=df['Signal'], name='Signal'))
                        fig_macd.add_trace(go.Bar(x=df['date'], y=df['MACD_Hist'], name='Histogram'))
                        fig_macd.update_layout(title='MACD')
                        st.plotly_chart(fig_macd, use_container_width=True)
                    else:
                        st.info("MACD数据不完整")
                
                with subtab3:
                    col1, col2 = st.columns(2)
                    with col1:
                        # RSI
                        if 'RSI' in df.columns:
                            fig_rsi = go.Figure()
                            fig_rsi.add_trace(go.Scatter(x=df['date'], y=df['RSI'], name='RSI'))
                            fig_rsi.add_hline(y=70, line_dash="dash", line_color="red")
                            fig_rsi.add_hline(y=30, line_dash="dash", line_color="green")
                            fig_rsi.update_layout(title='RSI')
                            st.plotly_chart(fig_rsi, use_container_width=True)
                        else:
                            st.info("RSI数据不完整")
                    
                    with col2:
                        # KDJ
                        if 'K' in df.columns and 'D' in df.columns and 'J' in df.columns:
                            fig_kdj = go.Figure()
                            fig_kdj.add_trace(go.Scatter(x=df['date'], y=df['K'], name='K'))
                            fig_kdj.add_trace(go.Scatter(x=df['date'], y=df['D'], name='D'))
                            fig_kdj.add_trace(go.Scatter(x=df['date'], y=df['J'], name='J'))
                            fig_kdj.update_layout(title='KDJ')
                            st.plotly_chart(fig_kdj, use_container_width=True)
                        else:
                            st.info("KDJ数据不完整")
                
                with subtab4:
                    # 布林带
                    if 'BB_Upper' in df.columns and 'BB_Middle' in df.columns and 'BB_Lower' in df.columns:
                        fig_bb = go.Figure()
                        fig_bb.add_trace(go.Scatter(x=df['date'], y=df['close'], name='价格'))
                        fig_bb.add_trace(go.Scatter(x=df['date'], y=df['BB_Upper'], name='上轨', line=dict(dash='dash')))
                        fig_bb.add_trace(go.Scatter(x=df['date'], y=df['BB_Middle'], name='中轨'))
                        fig_bb.add_trace(go.Scatter(x=df['date'], y=df['BB_Lower'], name='下轨', line=dict(dash='dash')))
                        fig_bb.update_layout(title='布林带')
                        st.plotly_chart(fig_bb, use_container_width=True)
                    else:
                        st.info("布林带数据不完整")
            else:
                st.error(f"技术指标计算失败: {df}")
        else:
            st.error(f"无法获取历史数据: {df_hist}")

with tab3:
    # 相关新闻标签页
    st.subheader("相关新闻")
    
    with st.spinner("获取相关新闻..."):
        news_df = get_news(symbol)
    
    if isinstance(news_df, pd.DataFrame):
        if not news_df.empty:
            for idx, news in news_df.iterrows():
                st.write(f"- {news['title']} ({news['date']})")
        else:
            st.info(f"未找到与 {symbol} 相关的新闻")
    else:
        st.error(f"获取新闻失败: {news_df}")

with tab4:
    # AI分析标签页
    st.subheader("AI 分析结果")
    
    if analyze_clicked or ('analysis_result' in st.session_state and st.session_state.analysis_result.get('symbol') == symbol):
        if analyze_clicked:
            with st.spinner("正在分析数据..."):
                # 获取所需数据
                current_data = get_current_price(symbol)
                df_hist = get_prices(symbol)
                
                if isinstance(df_hist, pd.DataFrame) and not df_hist.empty:
                    # 确保日期列是字符串类型，避免JSON序列化问题
                    if 'date' in df_hist.columns:
                        df_hist['date'] = df_hist['date'].astype(str)
                    
                    df_tech = get_technical_indicators(df_hist)
                    
                    # 确保技术指标中的日期列是字符串
                    if isinstance(df_tech, pd.DataFrame) and 'date' in df_tech.columns:
                        df_tech['date'] = df_tech['date'].astype(str)
                        
                    historical_data = df_hist.to_dict(orient='records')
                    
                    if isinstance(df_tech, pd.DataFrame):
                        indicators = df_tech.to_dict(orient='records')
                        
                        news_df = get_news(symbol)
                        if isinstance(news_df, pd.DataFrame):
                            news = news_df.to_dict(orient='records')
                            
                            # 整合数据
                            data = {
                                "current_price": current_data,
                                "historical_data": historical_data[-5:],  # 最近5条记录
                                "technical_indicators": indicators[-5:],  # 最近5条记录
                                "news": news[:5] if len(news) > 0 else []  # 最新5条新闻
                            }
                            
                            # 调用DeepSeek API进行分析
                            analysis = analyze_with_deepseek(symbol, data)
                            
                            # 保存结果到session_state
                            st.session_state.analysis_result = {
                                "symbol": symbol,
                                "analysis": analysis,
                                "timestamp": datetime.now().isoformat()
                            }
                        else:
                            st.error(f"获取新闻失败: {news_df}")
                    else:
                        st.error(f"计算技术指标失败: {df_tech}")
                else:
                    st.error(f"获取历史数据失败: {df_hist}")
        
        # 显示分析结果
        st.markdown(st.session_state.analysis_result.get("analysis", ""))
        st.caption(f"分析时间: {st.session_state.analysis_result.get('timestamp', '')}")
    else:
        st.info("点击侧边栏中的\"开始分析\"按钮生成AI分析报告")

# 页脚
st.markdown("---")
st.caption("期货策略分析平台 © 2025 - 基于 Streamlit、akshare、MCP 和 DeepSeek AI")

if __name__ == "__main__":
    pass
import json
import os
import httpx
import logging
import sys
import akshare as ak
from datetime import datetime, timedelta, date, time
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from technical_analysis import calculate_all_indicators
from deepseek_client import DeepSeekClient
import pandas as pd
import numpy as np

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("futures-mcp")

# 初始化MCP服务器
mcp = FastMCP("futures-mcp")

# 初始化DeepSeek客户端
deepseek_client = DeepSeekClient()

# 自定义JSON序列化函数
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

# 工具定义
@mcp.tool()
async def get_current_price(symbol: str) -> str:
    """获取期货实时价格
    
    Args:
        symbol: 期货代码，例如 M2509
    """
    try:
        df = ak.futures_zh_realtime(symbol=symbol)
        if df.empty:
            return json.dumps({"error": f"未找到期货代码 {symbol}"}, indent=2, ensure_ascii=False)
        # 不需要再过滤，直接返回第一行数据
        result = df.iloc[0].to_dict()
        return json.dumps(result, indent=2, ensure_ascii=False, default=json_serial)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2, ensure_ascii=False)

@mcp.tool()
async def get_prices(
    symbol: str,
    start_date: str = None,
    end_date: str = None,
    interval: str = "daily"
) -> str:
    """获取期货历史价格数据
    
    Args:
        symbol: 期货代码，例如 白糖
        start_date: 开始日期，格式：YYYYMMDD，默认30天前
        end_date: 结束日期，格式：YYYYMMDD，默认当前日期
        interval: 时间间隔，默认daily
    """
    try:
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y%m%d")
            
        # 首先获取主力合约代码
        symbol_info = ak.futures_zh_realtime(symbol=symbol)
        if symbol_info.empty:
            return json.dumps({"error": f"未找到期货代码 {symbol}"}, indent=2)
        
        main_contract = symbol_info.iloc[0]['symbol']
        logger.info(f"获取{symbol}的主力合约: {main_contract}")
        
        # 使用期货历史行情接口
        df = ak.futures_main_sina(symbol=main_contract, start_date=start_date, end_date=end_date)
        
        if df.empty:
            logger.warning(f"获取{main_contract}的历史数据为空")
            return json.dumps({"error": f"未找到{main_contract}的历史数据"}, indent=2)
        
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
        
        # 确保日期列是字符串类型
        if 'date' in df.columns:
            df['date'] = df['date'].astype(str)
            
        return json.dumps(df.to_dict(orient='records'), indent=2, default=json_serial)
    except Exception as e:
        logger.error(f"获取历史价格数据失败: {str(e)}", exc_info=True)
        return json.dumps({"error": str(e)}, indent=2)

@mcp.tool()
async def get_news(symbol: str) -> str:
    """获取期货相关新闻
    
    Args:
        symbol: 期货代码，例如 M2509
    """
    try:
        df_news = ak.futures_news_shmet(symbol="全部")
        # 使用模糊匹配查找相关新闻
        news_df = df_news[df_news['内容'].str.contains(symbol, case=False, na=False)]
        # 取最新的10条新闻
        news_df = news_df.head(10)
        # 重命名列名
        news_df = news_df.rename(columns={"发布时间": "date", "内容": "title"})
        return json.dumps(news_df.to_dict(orient='records'), indent=2, default=json_serial)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)

@mcp.tool()
async def get_technical_indicators(
    symbol: str,
    start_date: str = None,
    end_date: str = None
) -> str:
    """获取技术分析指标
    
    Args:
        symbol: 期货代码，例如 白糖
        start_date: 开始日期，格式：YYYYMMDD，默认30天前
        end_date: 结束日期，格式：YYYYMMDD，默认当前日期
    """
    try:
        # 首先获取历史数据
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y%m%d")
        
        # 获取历史价格数据
        prices_response = await get_prices(
            symbol=symbol, 
            start_date=start_date,
            end_date=end_date
        )
        
        # 解析历史价格数据
        try:
            prices_data = json.loads(prices_response)
            
            # 如果返回了错误信息而不是数据
            if isinstance(prices_data, dict) and 'error' in prices_data:
                return prices_response  # 直接返回错误
            
            # 确保有数据才创建DataFrame
            if not prices_data:
                return json.dumps({"error": "没有可用的历史价格数据"}, indent=2)
                
            df_hist = pd.DataFrame(prices_data)
                
            # 计算技术指标
            df = calculate_all_indicators(df_hist)
            
            # 确保日期列是字符串类型
            if 'date' in df.columns:
                df['date'] = df['date'].astype(str)
                
            return json.dumps(df.to_dict(orient='records'), indent=2, default=json_serial)
        except Exception as e:
            logger.error(f"解析历史数据失败: {str(e)}", exc_info=True)
            return json.dumps({"error": f"解析历史数据失败: {str(e)}"}, indent=2)
    except Exception as e:
        logger.error(f"获取技术指标失败: {str(e)}", exc_info=True)
        return json.dumps({"error": str(e)}, indent=2)

@mcp.tool()
async def analyze_futures(symbol: str) -> str:
    """使用AI分析期货数据
    
    Args:
        symbol: 期货代码，例如 白糖
    """
    try:
        # 获取实时价格
        current_price_resp = await get_current_price(symbol)
        try:
            current_data = json.loads(current_price_resp)
            if "error" in current_data:
                # 如果获取实时价格失败，创建基本信息
                current_data = {"symbol": symbol, "price": "未知", "error": current_data["error"]}
        except Exception as e:
            logger.warning(f"解析实时价格数据失败: {str(e)}")
            current_data = {"symbol": symbol, "price": "未知", "error": str(e)}
        
        # 获取历史数据
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
        end_date = datetime.now().strftime("%Y%m%d")
        
        prices_response = await get_prices(symbol, start_date, end_date)
        try:
            prices_data = json.loads(prices_response)
            if isinstance(prices_data, dict) and "error" in prices_data:
                # 处理错误情况
                logger.warning(f"获取历史数据失败: {prices_data['error']}")
                historical_data = []
                df_hist = None
            else:
                historical_data = prices_data
                if historical_data:
                    df_hist = pd.DataFrame(historical_data)
                else:
                    logger.warning("历史数据为空")
                    df_hist = None
        except Exception as e:
            logger.warning(f"解析历史数据失败: {str(e)}")
            historical_data = []
            df_hist = None
        
        # 获取技术指标
        indicators = []
        if df_hist is not None and not df_hist.empty:
            try:
                # 计算技术指标
                df_tech = calculate_all_indicators(df_hist)
                
                # 确保日期列是字符串类型
                if 'date' in df_tech.columns:
                    df_tech['date'] = df_tech['date'].astype(str)
                    
                indicators = df_tech.to_dict(orient='records')
            except Exception as e:
                logger.warning(f"计算技术指标失败: {str(e)}")
        
        # 获取新闻
        news_response = await get_news(symbol)
        try:
            news_data = json.loads(news_response)
            if isinstance(news_data, dict) and "error" in news_data:
                logger.warning(f"获取新闻失败: {news_data['error']}")
                news = []
            else:
                news = news_data
        except Exception as e:
            logger.warning(f"解析新闻数据失败: {str(e)}")
            news = []
        
        # 整合数据
        data = {
            "current_price": current_data,
            "historical_data": historical_data[-5:] if historical_data else [],  # 最近5条记录
            "technical_indicators": indicators[-5:] if indicators else [],  # 最近5条记录
            "news": news[:5] if news and isinstance(news, list) else []  # 最新5条新闻
        }
        
        # 准备AI分析请求
        messages = [
            {
                "role": "system",
                "content": "你是一个专业的期货分析师，请根据提供的数据进行简明扼要的分析。"
            },
            {
                "role": "user",
                "content": f"请分析{symbol}的以下数据：\n{json.dumps(data, ensure_ascii=False, default=json_serial)}"
            }
        ]
        
        # 调用DeepSeek API
        try:
            analysis = await deepseek_client.chat_completion(
                messages=messages, 
                model="bot-20250329163710-8zcqm"
            )
            analysis_text = analysis.choices[0].message.content
        except Exception as e:
            analysis_text = f"AI分析调用失败: {str(e)}"
        
        # 返回分析结果
        result = {
            "symbol": symbol,
            "analysis": analysis_text,
            "timestamp": datetime.now().isoformat()
        }
        return json.dumps(result, ensure_ascii=False, indent=2, default=json_serial)
    except Exception as e:
        logger.error(f"分析期货数据失败: {str(e)}", exc_info=True)
        return json.dumps({"error": str(e)}, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    # 记录服务器启动
    logger.info("启动期货MCP服务器...")
    # 初始化并运行服务器
    mcp.run(transport="stdio") 
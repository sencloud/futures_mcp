import pandas as pd
import numpy as np
from typing import Dict, Any, List

def calculate_ma(data: pd.DataFrame, periods: List[int] = [5, 10, 20, 60]) -> pd.DataFrame:
    """计算移动平均线
    
    Args:
        data: 包含OHLC数据的DataFrame
        periods: MA周期列表
        
    Returns:
        添加了MA列的DataFrame
    """
    df = data.copy()
    for period in periods:
        df[f'MA{period}'] = df['close'].rolling(window=period).mean()
    return df

def calculate_macd(data: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    """计算MACD指标
    
    Args:
        data: 包含OHLC数据的DataFrame
        fast: 快线周期
        slow: 慢线周期
        signal: 信号线周期
        
    Returns:
        添加了MACD相关列的DataFrame
    """
    df = data.copy()
    exp1 = df['close'].ewm(span=fast, adjust=False).mean()
    exp2 = df['close'].ewm(span=slow, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal'] = df['MACD'].ewm(span=signal, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['Signal']
    return df

def calculate_rsi(data: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """计算RSI指标
    
    Args:
        data: 包含OHLC数据的DataFrame
        period: RSI周期
        
    Returns:
        添加了RSI列的DataFrame
    """
    df = data.copy()
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

def calculate_bollinger_bands(data: pd.DataFrame, period: int = 20, std: int = 2) -> pd.DataFrame:
    """计算布林带
    
    Args:
        data: 包含OHLC数据的DataFrame
        period: 周期
        std: 标准差倍数
        
    Returns:
        添加了布林带相关列的DataFrame
    """
    df = data.copy()
    df['BB_Middle'] = df['close'].rolling(window=period).mean()
    df['BB_Std'] = df['close'].rolling(window=period).std()
    df['BB_Upper'] = df['BB_Middle'] + (df['BB_Std'] * std)
    df['BB_Lower'] = df['BB_Middle'] - (df['BB_Std'] * std)
    return df

def calculate_kdj(data: pd.DataFrame, n: int = 9, m1: int = 3, m2: int = 3) -> pd.DataFrame:
    """计算KDJ指标
    
    Args:
        data: 包含OHLC数据的DataFrame
        n: RSV周期
        m1: K值平滑系数
        m2: D值平滑系数
        
    Returns:
        添加了KDJ相关列的DataFrame
    """
    df = data.copy()
    low_list = df['low'].rolling(window=n, min_periods=n).min()
    high_list = df['high'].rolling(window=n, min_periods=n).max()
    rsv = (df['close'] - low_list) / (high_list - low_list) * 100
    
    df['K'] = rsv.ewm(alpha=1/m1, adjust=False).mean()
    df['D'] = df['K'].ewm(alpha=1/m2, adjust=False).mean()
    df['J'] = 3 * df['K'] - 2 * df['D']
    return df

def calculate_volume_ma(data: pd.DataFrame, periods: List[int] = [5, 10, 20]) -> pd.DataFrame:
    """计算成交量移动平均
    
    Args:
        data: 包含OHLC数据的DataFrame
        periods: MA周期列表
        
    Returns:
        添加了成交量MA列的DataFrame
    """
    df = data.copy()
    for period in periods:
        df[f'Volume_MA{period}'] = df['volume'].rolling(window=period).mean()
    return df

def calculate_all_indicators(data: pd.DataFrame) -> pd.DataFrame:
    """计算所有技术指标
    
    Args:
        data: 包含OHLC数据的DataFrame
        
    Returns:
        添加了所有技术指标的DataFrame
    """
    df = data.copy()
    df = calculate_ma(df)
    df = calculate_macd(df)
    df = calculate_rsi(df)
    df = calculate_bollinger_bands(df)
    df = calculate_kdj(df)
    df = calculate_volume_ma(df)
    return df 
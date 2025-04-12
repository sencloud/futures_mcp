import httpx
from typing import Dict, Any, List
from config import DEEPSEEK_API_KEY, DEEPSEEK_API_BASE
from openai import OpenAI

class DeepSeekClient:
    """DeepSeek API客户端"""
    
    def __init__(self):
        self.api_key = DEEPSEEK_API_KEY
        self.base_url = DEEPSEEK_API_BASE
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "bot-20250329163710-8zcqm",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = False
    ) -> Any:
        """调用DeepSeek聊天完成API
        
        Args:
            messages: 消息列表
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            stream: 是否流式输出
            
        Returns:
            API响应
        """
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream
        )
        return response
    
    async def analyze_futures(
        self,
        symbol: str,
        data: Dict[str, Any],
        stream: bool = False
    ) -> Any:
        """分析期货数据
        
        Args:
            symbol: 期货代码
            data: 期货数据
            stream: 是否流式输出
            
        Returns:
            分析结果
        """
        messages = [
            {
                "role": "system",
                "content": "你是一个专业的期货分析师，请根据提供的数据进行分析。"
            },
            {
                "role": "user",
                "content": f"请分析{symbol}的以下数据：\n{data}"
            }
        ]
        
        response = await self.chat_completion(messages, stream=stream)
        if not stream:
            return response.choices[0].message.content
        return response
    
    async def close(self):
        """关闭客户端"""
        await self.client.aclose() 
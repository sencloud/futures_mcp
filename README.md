# Futures MCP - 期货交易策略分析平台

期货交易策略分析的 MCP (Model Content Protocol) 服务和 Streamlit 交互平台。

## 项目简介

本项目是一个期货交易策略分析平台，集成了实时行情、技术分析、新闻资讯和 AI 分析等功能。提供两种使用方式：

1. **MCP 服务**：与 Claude 等 AI 助手集成，通过对话方式获取期货分析
2. **Streamlit 界面**：提供直观的图形界面，直接查看期货数据和分析结果

主要特点：

- 实时期货行情数据
- 丰富的技术分析指标
- 相关新闻资讯
- AI 驱动的市场分析
- 友好的 Web 界面
- 标准 MCP 协议实现
- DeepSeek AI 集成

## 技术栈

- Python 3.10+
- MCP 标准协议 - 与 AI 助手交互
- Streamlit - 交互式 Web 界面
- akshare - 期货数据获取
- DeepSeek API - AI 分析支持
- Plotly - 数据可视化

## 功能特性

### 1. 数据获取
- 实时期货行情
- 历史价格数据
- 相关新闻资讯

### 2. 技术分析
- 移动平均线 (MA)
- MACD 指标
- RSI 指标
- 布林带
- KDJ 指标
- 成交量分析

### 3. AI 分析
- 市场趋势分析
- 技术指标解读
- 新闻情绪分析
- 交易建议

## 安装说明

1. 克隆项目：
```bash
git clone https://github.com/sencloud/futures_mcp.git
cd futures_mcp
```

2. 创建虚拟环境：
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 配置环境变量：
```bash
cp .env.example .env
# 编辑 .env 文件，设置 DEEPSEEK_API_KEY
```

## 使用说明

本项目提供两种使用方式：MCP 服务和 Streamlit 界面。

### 方式一：MCP 服务 + AI 助手

1. 启动 MCP 服务器：
```bash
python mcp_server.py
```

2. 配置 Claude Desktop：
   - 创建或编辑 Claude Desktop 配置文件，注意如果启动失败需要确认直接在命令提示符下执行python /absolute/path/to/futures_mcp/mcp_server.py是否正常：

   **macOS**:
   ```bash
   mkdir -p ~/Library/Application\ Support/Claude/
   nano ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

   **Windows**:
   ```
   %APPDATA%\Claude\claude_desktop_config.json
   ```

   - 添加以下配置（替换路径为你的实际路径）：
   ```json
   {
     "mcpServers": {
       "futures-mcp": {
         "command": "python",
         "args": [
           "/absolute/path/to/futures_mcp/mcp_server.py"
         ]
       }
     }
   }
   ```

3. 重启 Claude Desktop

4. 现在你可以在 Claude Desktop 中使用期货工具
![image](https://github.com/user-attachments/assets/1fa2978f-3412-46f9-b6ba-1022d282d838)

5. 可以尝试向 Claude 提问：
   - "获取 豆粕 的当前价格"
   - "分析近期 豆粕 的技术指标"
   - "给我最近的期货新闻"

### 方式二：Streamlit 界面

如果你想使用直观的图形界面：

```bash
streamlit run app.py
```

访问浏览器 http://localhost:8501
![image](https://github.com/user-attachments/assets/9b42117f-e049-4305-955b-9e693324f322)

### Streamlit 界面使用流程

1. **选择期货品种**：在侧边栏选择要分析的期货代码
2. **设置时间范围**：选择历史数据的起止日期
3. **查看行情数据**：查看实时价格和K线图
4. **分析技术指标**：查看各种技术分析指标
5. **获取新闻资讯**：阅读相关新闻
6. **获取AI分析**：点击"开始分析"按钮，获取 DeepSeek AI 提供的专业分析

## 获取 DeepSeek API 密钥

要使用 AI 分析功能，您需要一个 DeepSeek API 密钥（注意，如果要联网功能，请用火山引擎，目前代码库里的功能是用了火山引擎）：

1. 访问 [DeepSeek 官网](https://deepseek.com/)
2. 注册/登录账户
3. 导航至 API 设置页面
4. 创建新的 API 密钥
5. 将获取的密钥添加到 `.env` 文件

## MCP 工具

本项目提供以下 MCP 工具：

1. **get_current_price**
   - 获取期货实时价格
   - 参数：symbol (期货代码，例如 M2509)

2. **get_prices**
   - 获取历史价格数据
   - 参数：symbol, start_date (选填), end_date (选填), interval (选填)

3. **get_news**
   - 获取相关新闻
   - 参数：symbol

4. **get_technical_indicators**
   - 获取技术分析指标
   - 参数：symbol, start_date (选填), end_date (选填)

5. **analyze_futures**
   - AI 分析期货数据
   - 参数：symbol

## 项目结构

```
futures_mcp/
├── app.py                 # Streamlit 应用主文件
├── mcp_server.py          # MCP 服务器
├── technical_analysis.py  # 技术分析工具
├── .env.example           # 环境变量示例
├── claude_desktop_config.example.json  # Claude Desktop配置示例
├── requirements.txt       # 项目依赖
└── README.md              # 项目文档
```

## 贡献指南

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

MIT License

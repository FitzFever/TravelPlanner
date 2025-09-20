# config.py
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

class Settings(BaseSettings):
    # API配置 - 支持 Claude (Anthropic) 和其他 LLM
    # Claude API 配置
    anthropic_api_key: str = "sk-zd91Lk9LYpIm8RQL7e15Cd196d1b4986BfCdAb8633DdDd97"  # 请设置 ANTHROPIC_API_KEY 环境变量
    anthropic_base_url: str = "https://api.mjdjourney.cn"  # Claude API base URL，支持代理或自定义端点
    
    # 或者使用兼容 OpenAI 格式的 API（如原 Moonshot）
    api_key: str = "sk-sSMzOmEJVEWA5c8bpJwDkcWePgGxYsxpahrNj9YEcW65lqnQ"
    base_url: str = "https://api.moonshot.cn/v1"
    
    # 模型选择: "claude" 或 "openai"
    model_type: str = "openai"
    
    # Claude 模型名称
    claude_model: str = "claude-sonnet-4-20250514"  # 或 claude-3-opus-20240229
    
    # 搜索配置 - 实际值从.env文件读取
    tavily_api_key: str = "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"

    # MCP工具路径配置
    xhs_mcp_directory: str = "/Users/geng/py/xhs-mcp"  # 小红书MCP项目路径
    
    # AgentScope Studio配置 - 实际值从.env文件读取
    studio_url: str = "http://localhost:3000"
    enable_studio: bool = True

    # 应用配置
    debug: bool = True
    stream_output: bool = True  # 是否启用流式输出
    
    class Config:
        env_file = ".env"

def get_settings():
    return Settings()
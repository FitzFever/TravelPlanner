# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API配置 - 实际值从.env文件读取
    api_key: str = "sk-lAMdhOrqDo6LtM6cPqbb8MSke8xLbe47GDEe808Ts7TcFyrH"
    base_url: str = "https://api.moonshot.cn/v1"
    
    # 搜索配置 - 实际值从.env文件读取
    tavily_api_key: str = "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"
    
    # AgentScope Studio配置 - 实际值从.env文件读取
    studio_url: str = "http://localhost:3000"
    enable_studio: bool = True
    
    # Agent配置 - 控制专家Agent数量
    agent_mode: str = "basic"  # basic, standard, full
    
    # 应用配置
    debug: bool = True
    
    class Config:
        env_file = ".env"

def get_settings():
    return Settings()
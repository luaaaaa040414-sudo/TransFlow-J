"""
核心配置 - 从 .env 文件读取所有配置项
"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # 应用设置
    app_name: str = "学术中译英质量保障平台"
    app_version: str = "1.0.0"
    debug: bool = True
    secret_key: str = "change-this-in-production"

    # 数据库
    database_url: str = "sqlite:///./data/app.db"

    # 文件存储
    upload_dir: str = "./data/uploads"
    projects_dir: str = "./data/projects"

    # AI API Keys
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    anthropic_api_key: str = ""
    google_api_key: str = ""
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    custom_api_key: str = ""
    custom_base_url: str = ""
    custom_model_id: str = ""

    # 默认模型
    default_translation_provider: str = "openai"
    default_translation_model: str = "gpt-4o"

    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

# 确保必要目录存在
os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs(settings.projects_dir, exist_ok=True)
os.makedirs(os.path.dirname(settings.database_url.replace("sqlite:///", "")), exist_ok=True)

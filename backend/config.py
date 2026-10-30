"""
配置管理模块
使用 pydantic-settings 从环境变量加载配置
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置"""

    # 数据库配置
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = ""
    MYSQL_DATABASE: str = "db_meeting_minutes"

    @property
    def MYSQL_DSN(self) -> str:
        """构建 MySQL 连接字符串"""
        return f"mysql+aiomysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}?charset=utf8mb4"

    # JWT 配置（阶段2使用）
    JWT_SECRET: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7天

    # 文件上传配置
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 500 * 1024 * 1024  # 500MB
    ALLOWED_EXTENSIONS: list = [".mp3", ".wav", ".m4a", ".mp4", ".avi", ".mov"]

    # 头像上传配置
    MAX_AVATAR_SIZE: int = 2 * 1024 * 1024  # 2MB
    ALLOWED_AVATAR_EXTENSIONS: list = [".jpg", ".jpeg", ".png", ".gif", ".webp"]

    # 公网访问地址（必须配置，用于 ASR 下载音频）
    PUBLIC_BASE_URL: str = "http://localhost:8000"

    # ASR 配置
    ASR_PROVIDER: str = "funasr"  # funasr | mock
    ASR_BASE_URL: str = "https://dashscope.aliyuncs.com/api/v1"  # 阿里云百炼 API 基础地址
    ASR_MODEL: str = "paraformer-v2"  # 录音文件识别模型（支持说话人分离）
    DASHSCOPE_API_KEY: str = ""  # 阿里云百炼 API Key

    # LLM 配置
    LLM_PROVIDER: str = "qwen"  # qwen | mock
    LLM_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"  # 通义千问 OpenAI 兼容端点
    LLM_MODEL: str = "qwen-plus"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 2000

    # 调度器配置
    ASR_POLL_INTERVAL: int = 10  # ASR 轮询间隔（秒）

    # 应用配置
    DEBUG: bool = True
    API_PREFIX: str = "/api"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# 全局配置实例
settings = Settings()

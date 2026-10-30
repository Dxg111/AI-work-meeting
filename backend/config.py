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

    # 文件存储：local | cos
    STORAGE_PROVIDER: str = "local"

    # 腾讯云 COS（STORAGE_PROVIDER=cos 时必填）
    COS_SECRET_ID: str = ""
    COS_SECRET_KEY: str = ""
    COS_REGION: str = ""
    COS_BUCKET: str = ""  # 含 APPID，例如 meeting-1250000000
    COS_PREFIX: str = "meetings"
    COS_ACL: str = "public-read"  # public-read | private
    COS_SET_OBJECT_ACL: bool = True  # 大规模场景可关闭，改用桶策略
    COS_PUBLIC_BASE_URL: str = ""  # 可选自定义域名/CDN
    COS_PRESIGNED_EXPIRES: int = 7200  # 私有桶预签名有效期（秒）

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

    # 长文本 Map-Reduce
    LLM_MAP_THRESHOLD_CHARS: int = 8000  # 超过该字符数启用分段处理
    LLM_MAP_CHUNK_CHARS: int = 6000  # 每段字符数
    LLM_MAP_MAX_CHUNKS: int = 20  # 最大分段数，防止异常长文本产生过多调用

    # 调度器配置
    ASR_POLL_INTERVAL: int = 10  # ASR 轮询间隔（秒）
    ASR_TASK_TIMEOUT_SECONDS: int = 2 * 60 * 60  # ASR 任务超时（2小时）
    PIPELINE_RECOVERY_INTERVAL: int = 60  # 卡住流水线恢复扫描间隔（秒）
    LLM_STUCK_TIMEOUT_SECONDS: int = 30 * 60  # summarizing 卡住判定（30分钟）
    TRANSCRIBED_STUCK_TIMEOUT_SECONDS: int = 2 * 60  # transcribed 未继续 LLM 判定（2分钟）
    UPLOADED_STUCK_TIMEOUT_SECONDS: int = 2 * 60  # uploaded+auto_process 未启动 ASR 判定（2分钟）

    # 应用配置
    DEBUG: bool = True
    API_PREFIX: str = "/api"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# 全局配置实例
settings = Settings()

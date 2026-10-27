"""
文件存储服务
"""
import os
import uuid
from pathlib import Path
from datetime import datetime
from fastapi import UploadFile
from config import settings
from core.exceptions import BusinessException


class StorageService:
    """文件存储服务"""

    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.public_base_url = settings.PUBLIC_BASE_URL
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def save_upload_file(self, file: UploadFile, meeting_id: int) -> tuple[str, str]:
        """
        保存上传的音视频文件

        Args:
            file: 上传的文件对象
            meeting_id: 会议ID

        Returns:
            (file_path, file_url): 本地路径和公网访问URL
        """
        # 1. 校验文件扩展名
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in settings.ALLOWED_EXTENSIONS:
            raise BusinessException(
                f"不支持的文件格式 {file_ext}，仅支持: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )

        # 2. 生成唯一文件名
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_name = f"{meeting_id}_{timestamp}_{uuid.uuid4().hex[:8]}{file_ext}"

        # 3. 保存文件到本地
        file_path = self.upload_dir / unique_name

        try:
            content = await file.read()

            # 校验文件大小
            if len(content) > settings.MAX_UPLOAD_SIZE:
                raise BusinessException(
                    f"文件大小超过限制 {settings.MAX_UPLOAD_SIZE / 1024 / 1024:.0f}MB"
                )

            with open(file_path, "wb") as f:
                f.write(content)

        except Exception as e:
            if isinstance(e, BusinessException):
                raise
            raise BusinessException(f"文件保存失败: {str(e)}")

        # 4. 生成公网访问URL
        file_url = f"{self.public_base_url}/uploads/{unique_name}"

        return str(file_path), file_url

    def check_public_url_accessibility(self) -> tuple[bool, str]:
        """
        检查公网URL是否合法（不能是本地回环地址）

        Returns:
            (is_valid, message): 是否合法和提示信息
        """
        url_lower = self.public_base_url.lower()

        # 检测本地回环地址
        localhost_patterns = ["127.0.0.1", "localhost", "0.0.0.0", "::1"]

        for pattern in localhost_patterns:
            if pattern in url_lower:
                return False, f"公网地址配置为本地回环地址 ({pattern})，云端 Fun-ASR 无法下载音频，请配置 ngrok/frp 等公网地址"

        return True, "OK"

    def delete_file(self, file_path: str) -> None:
        """删除文件"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"[Storage] 删除文件失败: {file_path}, 错误: {e}")


# 全局实例
storage_service = StorageService()

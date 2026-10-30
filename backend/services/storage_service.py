"""
文件存储服务
"""
import ipaddress
import os
import uuid
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse
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

        total_size = 0
        try:
            # 分块写入，避免把 500MB 文件一次性读入内存
            with open(file_path, "wb") as f:
                while True:
                    chunk = await file.read(1024 * 1024)
                    if not chunk:
                        break

                    total_size += len(chunk)
                    if total_size > settings.MAX_UPLOAD_SIZE:
                        raise BusinessException(
                            f"文件大小超过限制 {settings.MAX_UPLOAD_SIZE / 1024 / 1024:.0f}MB"
                        )

                    f.write(chunk)

        except Exception as e:
            # 失败时清理已写入的半截文件
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError:
                    pass

            if isinstance(e, BusinessException):
                raise
            raise BusinessException(f"文件保存失败: {str(e)}")

        # 4. 生成公网访问URL
        file_url = f"{self.public_base_url}/uploads/{unique_name}"

        return str(file_path), file_url

    def check_public_url_accessibility(self) -> tuple[bool, str]:
        """
        检查公网 URL 是否合法

        真实 Fun-ASR 必须能从公网下载音频，因此以下地址会被拒绝：
        - localhost
        - 回环地址、私网地址、链路本地地址、保留地址、未指定地址
        - 非 http(s) 地址

        域名只做格式校验，是否能被云端访问需部署侧保证。

        Returns:
            (is_valid, message): 是否合法和提示信息
        """
        raw = (self.public_base_url or "").strip()
        parsed = urlparse(raw)

        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            return False, "PUBLIC_BASE_URL 配置不正确，必须是 http(s) 公网地址"

        host = parsed.hostname.lower()

        if host == "localhost":
            return False, (
                "公网地址配置为 localhost，云端 Fun-ASR 无法下载音频，"
                "请配置 OSS、frp 或固定公网域名"
            )

        try:
            ip = ipaddress.ip_address(host)
        except ValueError:
            # 域名，放行
            return True, "OK"

        if not ip.is_global:
            return False, (
                f"公网地址配置为内网/回环地址 ({host})，"
                "云端 Fun-ASR 无法下载音频，请配置 OSS、frp 或固定公网域名"
            )

        return True, "OK"

    async def save_avatar(self, file: UploadFile, user_id: int) -> str:
        """
        保存用户头像

        Returns:
            相对访问路径，例如 /uploads/avatars/avatar_1_xxx.png
        """
        file_ext = os.path.splitext(file.filename or "")[1].lower()
        if file_ext not in settings.ALLOWED_AVATAR_EXTENSIONS:
            allowed = ", ".join(settings.ALLOWED_AVATAR_EXTENSIONS)
            raise BusinessException(f"不支持的头像格式 {file_ext or '未知'}，仅支持: {allowed}")

        if file.content_type and not file.content_type.startswith("image/"):
            raise BusinessException("头像文件必须是图片")

        content = await file.read()
        if len(content) > settings.MAX_AVATAR_SIZE:
            raise BusinessException(
                f"头像大小不能超过 {settings.MAX_AVATAR_SIZE / 1024 / 1024:.0f}MB"
            )

        avatar_dir = self.upload_dir / "avatars"
        avatar_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"avatar_{user_id}_{timestamp}_{uuid.uuid4().hex[:8]}{file_ext}"
        file_path = avatar_dir / filename

        try:
            with open(file_path, "wb") as f:
                f.write(content)
        except Exception as e:
            raise BusinessException(f"头像保存失败: {str(e)}")

        return f"/uploads/avatars/{filename}"

    def delete_avatar(self, avatar_url: str) -> None:
        """删除旧头像文件（仅处理本地上传目录下的头像）"""
        if not avatar_url or not avatar_url.startswith("/uploads/avatars/"):
            return

        relative = avatar_url[len("/uploads/"):]
        self.delete_file(str(self.upload_dir / relative))

    def delete_file(self, file_path: str) -> None:
        """删除文件"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"[Storage] 删除文件失败: {file_path}, 错误: {e}")


# 全局实例
storage_service = StorageService()

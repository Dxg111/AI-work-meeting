"""
文件存储服务

支持两种后端：
- local：本地磁盘（默认）
- cos：腾讯云对象存储 COS
"""
import ipaddress
import mimetypes
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from fastapi import UploadFile
from starlette.concurrency import run_in_threadpool

from config import settings
from core.exceptions import BusinessException


class StorageService:
    """文件存储服务（本地 / 腾讯云 COS）"""

    def __init__(self):
        self.provider = (settings.STORAGE_PROVIDER or "local").strip().lower()
        if self.provider not in ("local", "cos"):
            raise BusinessException(f"不支持的存储类型: {self.provider}，仅支持 local / cos")

        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.public_base_url = settings.PUBLIC_BASE_URL
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self._cos_client_instance = None

    # ==================== 通用校验 ====================

    @staticmethod
    def _validate_extension(file: UploadFile) -> str:
        file_ext = os.path.splitext(file.filename or "")[1].lower()
        if file_ext not in settings.ALLOWED_EXTENSIONS:
            raise BusinessException(
                f"不支持的文件格式 {file_ext or '未知'}，"
                f"仅支持: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )
        return file_ext

    @staticmethod
    def _get_upload_size(file: UploadFile) -> Optional[int]:
        """尽量在不读取全部内容的情况下获取上传大小"""
        size = getattr(file, "size", None)
        if size is not None:
            return int(size)

        try:
            position = file.file.tell()
            file.file.seek(0, os.SEEK_END)
            size = file.file.tell()
            file.file.seek(position)
            return int(size)
        except Exception:
            return None

    @staticmethod
    def _size_limit_message() -> str:
        return f"文件大小超过限制 {settings.MAX_UPLOAD_SIZE / 1024 / 1024:.0f}MB"

    # ==================== 上传 ====================

    async def save_upload_file(self, file: UploadFile, meeting_id: int) -> tuple[str, str]:
        """
        保存上传的音视频文件

        Returns:
            (file_path, file_url)
            - local：本地路径 + PUBLIC_BASE_URL 访问地址
            - cos：cos://bucket/key + COS 公网/预签名地址
        """
        file_ext = self._validate_extension(file)

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_name = f"{meeting_id}_{timestamp}_{uuid.uuid4().hex[:8]}{file_ext}"

        if self.provider == "cos":
            return await self._save_to_cos(file, unique_name, file_ext)

        return await self._save_to_local(file, unique_name)

    async def _save_to_local(self, file: UploadFile, unique_name: str) -> tuple[str, str]:
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
                        raise BusinessException(self._size_limit_message())

                    f.write(chunk)

        except Exception as e:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError:
                    pass

            if isinstance(e, BusinessException):
                raise
            raise BusinessException(f"文件保存失败: {str(e)}")

        file_url = f"{self.public_base_url}/uploads/{unique_name}"
        return str(file_path), file_url

    async def _save_to_cos(self, file: UploadFile, unique_name: str, file_ext: str) -> tuple[str, str]:
        size = self._get_upload_size(file)
        if size is not None and size > settings.MAX_UPLOAD_SIZE:
            raise BusinessException(self._size_limit_message())

        prefix = (settings.COS_PREFIX or "meetings").strip("/")
        key = f"{prefix}/{unique_name}" if prefix else unique_name

        acl = (settings.COS_ACL or "public-read").strip().lower()
        if acl not in ("public-read", "private"):
            raise BusinessException("COS_ACL 仅支持 public-read 或 private")

        content_type = mimetypes.guess_type(unique_name)[0] or "application/octet-stream"
        client = self._get_cos_client()

        kwargs = {
            "Bucket": settings.COS_BUCKET,
            "Body": file.file,
            "Key": key,
            "ContentType": content_type,
        }
        # 对象级 ACL 有数量限制；大规模场景可关闭，改用桶策略
        if settings.COS_SET_OBJECT_ACL:
            kwargs["ACL"] = acl
        if size is not None:
            kwargs["ContentLength"] = str(size)

        try:
            file.file.seek(0)
            await run_in_threadpool(client.put_object, **kwargs)
        except BusinessException:
            raise
        except Exception as e:
            raise BusinessException(f"COS 上传失败: {str(e)}")

        file_path = f"cos://{settings.COS_BUCKET}/{key}"

        if acl == "public-read":
            file_url = self._cos_public_url(key)
        else:
            file_url = self._cos_presigned_url(key)

        return file_path, file_url

    # ==================== 访问地址 ====================

    def get_accessible_url(self, file_path: str, file_url: Optional[str] = None) -> str:
        """
        获取可用于 ASR 下载的地址

        - 公有读 COS：返回公网 URL
        - 私有 COS：每次重新生成预签名 URL，避免过期
        - 本地：返回上传时保存的 file_url
        """
        if self.provider == "cos" and file_path and file_path.startswith("cos://"):
            acl = (settings.COS_ACL or "public-read").strip().lower()
            if acl == "private":
                bucket, key = self._cos_key_from_path(file_path)
                return self._cos_presigned_url(key, bucket)

            # 公有读：始终按当前配置重新拼装，避免旧的预签名 URL 过期或域名变更
            _, key = self._cos_key_from_path(file_path)
            return self._cos_public_url(key)

        return file_url or ""

    def check_public_url_accessibility(self, url: Optional[str] = None) -> tuple[bool, str]:
        """
        检查音频 URL 是否能被云端 ASR 下载

        拒绝 localhost、回环/私网/链路本地/保留地址、非 http(s) 地址。
        域名只做格式校验，实际可达性由部署侧保证。
        """
        raw = (url or self.public_base_url or "").strip()
        parsed = urlparse(raw)

        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            return False, "音频公网地址配置不正确，必须是 http(s) 地址"

        host = parsed.hostname.lower()

        if host == "localhost":
            return False, (
                "音频地址是 localhost，云端 Fun-ASR 无法下载，"
                "请配置 COS、OSS、frp 或固定公网域名"
            )

        try:
            ip = ipaddress.ip_address(host)
        except ValueError:
            # 域名，放行
            return True, "OK"

        if not ip.is_global:
            return False, (
                f"音频地址是内网/回环地址 ({host})，云端 Fun-ASR 无法下载，"
                "请配置 COS、OSS、frp 或固定公网域名"
            )

        return True, "OK"

    # ==================== COS 内部方法 ====================

    def _get_cos_client(self):
        if self._cos_client_instance is not None:
            return self._cos_client_instance

        missing = [
            name
            for name, value in (
                ("COS_SECRET_ID", settings.COS_SECRET_ID),
                ("COS_SECRET_KEY", settings.COS_SECRET_KEY),
                ("COS_REGION", settings.COS_REGION),
                ("COS_BUCKET", settings.COS_BUCKET),
            )
            if not (value or "").strip()
        ]
        if missing:
            raise BusinessException(f"COS 配置不完整，缺少: {', '.join(missing)}")

        try:
            from qcloud_cos import CosConfig, CosS3Client
        except ImportError:
            raise BusinessException(
                "未安装 cos-python-sdk-v5。请使用 backend/venv 运行项目，"
                "或执行 venv/Scripts/pip.exe install cos-python-sdk-v5"
                "（Linux/macOS 使用 venv/bin/pip）"
            )

        config = CosConfig(
            Region=settings.COS_REGION,
            SecretId=settings.COS_SECRET_ID,
            SecretKey=settings.COS_SECRET_KEY,
            Scheme="https",
        )
        self._cos_client_instance = CosS3Client(config)
        return self._cos_client_instance

    @staticmethod
    def _cos_key_from_path(file_path: str) -> tuple[str, str]:
        """解析 cos://bucket/key"""
        rest = file_path[len("cos://"):]
        bucket, _, key = rest.partition("/")
        if not bucket or not key:
            raise BusinessException(f"无效的 COS 文件路径: {file_path}")
        return bucket, key

    def _cos_public_url(self, key: str) -> str:
        if not settings.COS_BUCKET or not settings.COS_REGION:
            raise BusinessException("COS_BUCKET / COS_REGION 未配置")

        base = (settings.COS_PUBLIC_BASE_URL or "").strip().rstrip("/")
        if not base:
            base = f"https://{settings.COS_BUCKET}.cos.{settings.COS_REGION}.myqcloud.com"

        return f"{base}/{key}"

    def _cos_presigned_url(self, key: str, bucket: Optional[str] = None) -> str:
        client = self._get_cos_client()
        return client.get_presigned_url(
            Bucket=bucket or settings.COS_BUCKET,
            Key=key,
            Method="GET",
            Expired=settings.COS_PRESIGNED_EXPIRES,
        )

    # ==================== 头像（保持本地存储） ====================

    async def save_avatar(self, file: UploadFile, user_id: int) -> str:
        """
        保存用户头像（头像仍保存本地，不随 STORAGE_PROVIDER 切换）

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

    async def delete_avatar(self, avatar_url: str) -> None:
        """删除旧头像文件（仅处理本地上传目录下的头像）"""
        if not avatar_url or not avatar_url.startswith("/uploads/avatars/"):
            return

        relative = avatar_url[len("/uploads/"):]
        await self.delete_file(str(self.upload_dir / relative))

    # ==================== 删除 ====================

    async def delete_file(self, file_path: str) -> None:
        """删除文件：cos:// 走 COS，其他按本地路径处理"""
        if not file_path:
            return

        if file_path.startswith("cos://"):
            try:
                bucket, key = self._cos_key_from_path(file_path)
                client = self._get_cos_client()
                await run_in_threadpool(client.delete_object, Bucket=bucket, Key=key)
            except Exception as e:
                print(f"[Storage] 删除 COS 文件失败: {file_path}, 错误: {e}")
            return

        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"[Storage] 删除文件失败: {file_path}, 错误: {e}")


# 全局实例
storage_service = StorageService()

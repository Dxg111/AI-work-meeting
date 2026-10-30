# FunASR URL 错误问题排查与解决方案

> **2026-10-30 更新**
>
> 代码层已按阿里云百炼官方异步录音文件识别接口重写：
> - 提交：`POST /api/v1/services/audio/asr/transcription` + `X-DashScope-Async: enable`
> - 查询：`GET /api/v1/tasks/{task_id}`
> - 成功后下载 `output.results[].transcription_url` 解析句子
>
> 已用阿里云公开示例音频验证真实转写成功。
> 存储层已新增**腾讯云 COS** 后端：配置 `STORAGE_PROVIDER=cos` 即可让上传的音频获得公网/预签名 URL，详见《COS存储接入说明.md》。
> ngrok 免费地址仍不可用；可改用 **腾讯云 COS、阿里云 OSS 或 frp + 固定域名**。

## 问题描述

提交音频到阿里云 FunASR 服务时，返回错误：
```
InvalidParameter: url error, please check url！
```

## 问题原因

经过测试发现：
1. ✅ ngrok 隧道正常运行
2. ✅ 音频文件可以通过 ngrok 公网地址正常访问（返回 200 OK）
3. ✅ FastAPI 静态文件服务配置正确
4. ❌ **阿里云 FunASR 无法访问 ngrok 免费版提供的 URL**

**根本原因**：ngrok 免费版对某些云服务商的访问有限制，或者阿里云 FunASR 对 ngrok 域名有黑名单策略。

## 解决方案

### 方案 0：腾讯云 COS（已实现，推荐用于替代 ngrok）

代码已支持腾讯云对象存储，配置即可启用：

```env
STORAGE_PROVIDER=cos

COS_SECRET_ID=你的SecretId
COS_SECRET_KEY=你的SecretKey
COS_REGION=ap-guangzhou
COS_BUCKET=your-bucket-1250000000
COS_PREFIX=meetings
COS_ACL=public-read          # 或 private（私有桶 + 预签名）
COS_PRESIGNED_EXPIRES=7200

ASR_PROVIDER=funasr
```

- 公有读：上传后返回 COS 公网 URL；
- 私有桶：每次提交 ASR 前重新生成预签名 URL；
- 本地存储仍可通过 `STORAGE_PROVIDER=local` 回退。

完整步骤、权限配置和常见问题见《COS存储接入说明.md》。

### 方案 1：使用 Mock ASR 模式（临时测试）✅ 已配置

临时切换到 Mock 模式，用于测试完整流程：

```env
# backend/.env
ASR_PROVIDER=mock
```

**优点**：
- 不需要公网地址
- 快速验证整个流程
- 返回模拟的转写数据

**缺点**：
- 不是真实的语音识别
- 仅用于开发测试

### 方案 2：使用自己的云服务器 + frp（推荐生产环境）

如果您有云服务器（阿里云/腾讯云等），使用 frp 内网穿透：

#### 2.1 服务器端配置

```bash
# 下载 frp
wget https://github.com/fatedier/frp/releases/download/v0.52.0/frp_0.52.0_linux_amd64.tar.gz
tar -xzf frp_0.52.0_linux_amd64.tar.gz
cd frp_0.52.0_linux_amd64

# 编辑 frps.ini
cat > frps.ini << EOF
[common]
bind_port = 7000
vhost_http_port = 8080
EOF

# 启动服务端
./frps -c frps.ini
```

#### 2.2 本地客户端配置

```bash
# 下载 frp 客户端（Windows）
# 访问：https://github.com/fatedier/frp/releases

# 编辑 frpc.ini
[common]
server_addr = 你的云服务器IP
server_port = 7000

[meeting_backend]
type = http
local_ip = 127.0.0.1
local_port = 8000
custom_domains = 你的域名.com
```

```bash
# 启动客户端
frpc.exe -c frpc.ini
```

#### 2.3 修改配置

```env
# backend/.env
PUBLIC_BASE_URL=http://你的域名.com:8080
ASR_PROVIDER=funasr
```

### 方案 3：使用阿里云 OSS（最佳生产方案）

将音频文件上传到阿里云 OSS，FunASR 直接从 OSS 读取：

#### 3.1 安装 OSS SDK

```bash
cd backend
pip install oss2
```

#### 3.2 修改存储服务

创建 `backend/services/oss_storage_service.py`：

```python
import oss2
from config import settings

class OSSStorageService:
    def __init__(self):
        auth = oss2.Auth(settings.OSS_ACCESS_KEY, settings.OSS_SECRET_KEY)
        self.bucket = oss2.Bucket(
            auth, 
            settings.OSS_ENDPOINT, 
            settings.OSS_BUCKET_NAME
        )
    
    async def save_upload_file(self, file, meeting_id):
        # 生成文件名
        filename = f"meetings/{meeting_id}_{uuid.uuid4().hex[:8]}.mp3"
        
        # 上传到 OSS
        content = await file.read()
        self.bucket.put_object(filename, content)
        
        # 生成公网 URL
        file_url = f"https://{settings.OSS_BUCKET_NAME}.{settings.OSS_ENDPOINT}/{filename}"
        
        return filename, file_url
```

#### 3.3 配置环境变量

```env
# backend/.env
ASR_PROVIDER=funasr

# OSS 配置
OSS_ACCESS_KEY=your_access_key
OSS_SECRET_KEY=your_secret_key
OSS_ENDPOINT=oss-cn-beijing.aliyuncs.com
OSS_BUCKET_NAME=your_bucket_name
```

**优点**：
- ✅ 阿里云内网访问，速度快
- ✅ 无需内网穿透
- ✅ 可靠稳定
- ✅ 适合生产环境

### 方案 4：使用付费版 ngrok

ngrok 付费版提供稳定域名和更少限制：

```bash
ngrok http 8000 --domain=your-reserved-domain.ngrok.app
```

```env
PUBLIC_BASE_URL=https://your-reserved-domain.ngrok.app
ASR_PROVIDER=funasr
```

## 当前配置状态

✅ 已临时切换到 Mock ASR 模式，可以测试完整流程

```env
ASR_PROVIDER=mock
```

## 建议

1. **开发阶段**：使用 `mock` 模式快速迭代
2. **测试阶段**：使用腾讯云 COS（公有读或私有桶预签名）或 frp + 自己的服务器
3. **生产环境**：腾讯云 COS 私有桶 + 预签名，或阿里云 OSS（与 Fun-ASR 同云、链路更短）

## 重启后端服务

修改 `.env` 后需要重启：

```bash
# 停止当前服务（Ctrl+C）
# 重新启动
cd backend
python main.py
```

## 验证

重新上传音频文件，查看流程是否正常：
- Mock 模式会返回模拟的转写结果
- 可以验证 LLM 纪要生成是否正常

---

**更新时间**：2026-10-27  
**问题状态**：已临时解决（使用 Mock 模式）

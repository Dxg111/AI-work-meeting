# 腾讯云 COS 存储接入说明

> **状态**：代码已实现，配置待填写
> **完成日期**：2026-10-30
> **关联文档**：《FunASR_URL问题解决方案.md》
>
> **安全提醒**：SecretId / SecretKey 一旦出现在聊天、截图、日志中，应立即到腾讯云控制台禁用并轮换；新密钥只写入 `backend/.env`，不要提交 Git。

## 一、为什么 COS 能解决 Fun-ASR 的 URL 问题

阿里云 Fun-ASR 只要求音频能通过**公网 HTTP/HTTPS** 下载，不关心文件存储在哪个云。

腾讯云 COS 提供的对象 URL：

```
https://<bucket>-<appid>.cos.<region>.myqcloud.com/<key>
```

只要对象是公有读，或者生成有效的预签名 URL，Fun-ASR 就能正常下载并转写。

## 二、代码实现

### 2.1 存储后端切换

`backend/services/storage_service.py` 支持两种后端：

| 配置 | 行为 |
|---|---|
| `STORAGE_PROVIDER=local` | 保存到 `backend/uploads/`，保持原有行为 |
| `STORAGE_PROVIDER=cos` | 保存到腾讯云 COS |

切换只需要改 `.env`，ASR、LLM、前端代码不需要改。

### 2.2 上传流程

1. 校验扩展名与大小；
2. 生成对象 Key：`{COS_PREFIX}/{meeting_id}_{timestamp}_{uuid}.{ext}`；
3. 上传到 COS；
4. 返回：
   - `file_path`：`cos://{bucket}/{key}`（用于删除）；
   - `file_url`：公有读 URL，或私有桶预签名 URL。

### 2.3 私有桶预签名

`COS_ACL=private` 时：

- 上传后返回一个预签名 URL；
- 每次提交 ASR 前，`get_accessible_url()` 会重新生成预签名 URL，避免过期；
- 预签名有效期由 `COS_PRESIGNED_EXPIRES` 控制。

### 2.4 公网地址校验

`check_public_url_accessibility()` 现在校验**实际传入 ASR 的音频 URL**，而不是固定的 `PUBLIC_BASE_URL`：

- COS 公网域名 / 预签名 URL：通过；
- localhost、127.0.0.1、192.168.x、10.x、0.0.0.0、::1：拒绝。

### 2.5 删除

- `cos://bucket/key`：删除 COS 对象；
- 本地路径：删除本地文件；
- 兼容切换前创建的本地会议记录。

### 2.6 头像

头像目前仍保存在本地 `uploads/avatars/`，不随 `STORAGE_PROVIDER` 切换。
如果后续部署在无持久磁盘的容器中，可以再扩展头像走 COS。

## 三、运行环境

项目依赖安装在 `backend/venv`。如果直接执行 `python main.py`，使用的可能是全局 Python，
会提示“未安装 cos-python-sdk-v5”。请使用：

```bash
cd backend
venv/Scripts/python.exe main.py          # Windows
# source venv/bin/activate && python main.py   # macOS/Linux
```

或先激活虚拟环境再启动。

## 四、配置项

在 `backend/.env` 中填写：

```env
# 切换到 COS
STORAGE_PROVIDER=cos

# 腾讯云 COS
COS_SECRET_ID=你的SecretId
COS_SECRET_KEY=你的SecretKey
COS_REGION=ap-guangzhou
COS_BUCKET=your-bucket-1250000000
COS_PREFIX=meetings
COS_ACL=public-read
COS_PUBLIC_BASE_URL=
COS_PRESIGNED_EXPIRES=7200

# 真实 ASR
ASR_PROVIDER=funasr
```

字段说明：

| 变量 | 说明 |
|---|---|
| `COS_SECRET_ID` / `COS_SECRET_KEY` | 腾讯云 API 密钥，只放 `.env`，不要提交 |
| `COS_REGION` | 存储桶地域，例如 `ap-guangzhou`、`ap-beijing`、`ap-shanghai` |
| `COS_BUCKET` | 存储桶名称，**必须包含 APPID**，例如 `meeting-1250000000` |
| `COS_PREFIX` | 对象前缀，默认 `meetings` |
| `COS_ACL` | `public-read`（简单）或 `private`（推荐，预签名） |
| `COS_SET_OBJECT_ACL` | 是否给每个对象设置 ACL，默认 `true`；对象量大时可设为 `false`，改用桶策略 |
| `COS_PUBLIC_BASE_URL` | 可选，自定义域名/CDN；留空使用 COS 默认域名 |
| `COS_PRESIGNED_EXPIRES` | 私有桶预签名有效期，单位秒，默认 7200 |

## 四、COS 控制台准备

1. 创建存储桶，记录**地域**和**桶名（含 APPID）**；
2. 在“访问管理 → API 密钥管理”创建 SecretId / SecretKey；
3. 权限：
   - **公有读**：给对象或 `meetings/` 前缀配置公有读 ACL/桶策略；
   - **私有**：保持私有，代码会自动生成预签名 URL；
4. 如果前端需要直接用 `<audio>` 播放 COS 文件，再配置 CORS；仅服务端 ASR 下载不需要 CORS。

## 五、验证步骤

1. 填写 `.env`，重启后端；
2. 上传一个会议音频（建议先关闭自动处理）；
3. 检查数据库：

   ```sql
   SELECT meeting_id, file_path, file_url FROM t_meeting ORDER BY meeting_id DESC LIMIT 1;
   ```

   - `file_path` 应为 `cos://...`；
   - `file_url` 应为 COS 域名或预签名 URL；
4. 在公网浏览器打开 `file_url`，应能下载音频；
5. 开启真实 ASR（`ASR_PROVIDER=funasr`），点击处理，观察日志：

   ```
   [ASR] 会议 xx 提交转写任务成功，task_id=...
   ```

## 六、常见问题

| 现象 | 原因 | 处理 |
|---|---|---|
| `COS 配置不完整，缺少: ...` | `.env` 缺少配置 | 补齐 SecretId/SecretKey/Region/Bucket |
| `未安装 cos-python-sdk-v5` | 依赖未安装 | `venv/Scripts/pip.exe install cos-python-sdk-v5` |
| `403 AccessDenied` | 桶/对象私有，且未使用预签名 | 设置公有读，或 `COS_ACL=private` |
| `404 NoSuchKey` | Key 或 Region/Bucket 不匹配 | 检查 `COS_REGION`、`COS_BUCKET`、`COS_PREFIX` |
| Fun-ASR `url error` | URL 不可公网访问或已过期 | 检查 `file_url` 浏览器能否打开；私有桶用预签名 |
| `SSLEOFError` / `SSL/TLS connection failed` / `schannel: failed to receive handshake` | DNS 被代理/VPN 劫持：COS 域名被解析到 `198.18.x.x` 等 fake-IP 段 | 关闭 Clash/VPN 的 TUN 模式，或给 `*.myqcloud.com` 配直连规则；更换 DNS 后重试 |
| 上传 `403 AccessDenied`（对象 ACL） | 密钥没有 `cos:PutObjectACL` 权限 | 设置 `COS_SET_OBJECT_ACL=false`，改用桶策略配置公有读；或改用 `COS_ACL=private` |
| 上传慢 | 跨云/公网链路 | 会议量大时考虑阿里云 OSS 或 COS 同地域加速 |

## 七、安全建议

1. **优先使用私有桶 + 预签名**，避免音频 URL 被随意传播；
2. 公有读时使用随机 Key，并配置生命周期规则定期清理；
   - COS 对象级 ACL 有数量限制（约 1000 条）；会议量大时建议把 `COS_SET_OBJECT_ACL=false`，在桶策略中给 `meetings/*` 配置公有读；
3. SecretId/SecretKey 只放 `.env`，不要提交 Git、不要打印到日志；
4. 生产环境使用子账号密钥，只授予该桶 `meetings/` 前缀的上传/删除/读取权限。

## 八、回退到本地存储

```env
STORAGE_PROVIDER=local
```

- 新上传文件回到本地 `uploads/`；
- 历史 `cos://` 记录仍可通过 COS 删除（只要保留 COS 配置）；
- 不需要修改数据库。

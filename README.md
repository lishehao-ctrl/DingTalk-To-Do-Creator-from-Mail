# DingTalk To-Do Creator from Email

一句话：轮询 IMAP 邮箱 → 解析/过滤业务邮件 → 生成钉钉待办 → 本地 JSON 记录实现幂等。

## 流程概览
```
IMAP Inbox
   │ (safe_get)
   ▼
Raw Emails (bytes)
   │ parse (mail_parser)
   │ filter (mail_filter: dedup, date window, subject keyword)
   ▼
Useful Parts (subject/date/body fields)
   │ build TODO payload
   │ compute due time (offsets)
   │ get access_token → unionId
   ▼
DingTalk TODO created
   │
   ▼
processed_messages.json (idempotency: Message-ID -> processed time)
```

## Quickstart
1. 安装依赖  
   ```bash
   pip install -r requirements.txt
   ```
2. 配置环境变量  
   ```bash
   cp .env.example .env
   # 填写邮件密码和钉钉应用凭证
   ```
3. 配置钉钉接收人  
   ```bash
   cp config/dingtalk_recipients.example.json config/dingtalk_recipients.json
   # 填写 eco_todo_user_ids 和 error_todo_user_ids
   ```
4. 运行  
   ```bash
   python main.py
   ```

## 配置说明
### 环境变量（.env）
- `ECO_MAIL_ADDRESS`：IMAP 登录邮箱地址。
- `ECO_MAIL_PASSWORD`：IMAP 登录邮箱的密码或应用专用密码。
- `DINGTALK_CLIENT_ID`：钉钉应用 appKey。
- `DINGTALK_CLIENT_SECRET`：钉钉应用 appSecret。

### 钉钉接收人配置（config/dingtalk_recipients.json）
- `eco_todo_user_ids`：业务待办接收人的 userId 列表。
- `error_todo_user_ids`：错误待办接收人的 userId 列表（至少 1 个）。

## 安全说明
- 真实凭证不入库：`.env` 和 `config/dingtalk_recipients.json` 已在 `.gitignore` 中。
- 示例文件仅提供键名：`.env.example`、`config/dingtalk_recipients.example.json`。
- 程序启动时缺失必要配置会立即抛出 RuntimeError，避免静默失败。

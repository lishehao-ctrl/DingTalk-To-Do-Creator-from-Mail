# DingTalk To-Do Creator from Email

One line: poll IMAP → parse/filter business mail → create DingTalk TODO → record Message-ID in local JSON for idempotency.

## Flow
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
1. Install deps  
   ```bash
   pip install -r requirements.txt
   ```
2. Env vars  
   ```bash
   cp .env.example .env
   # fill mail password and DingTalk app credentials
   ```
3. Recipients config  
   ```bash
   cp config/dingtalk_recipients.example.json config/dingtalk_recipients.json
   # fill eco_todo_user_ids and error_todo_user_ids
   ```
4. Run  
   ```bash
   python main.py
   ```

## Configuration
### Env (.env)
- `ECO_MAIL_ADDRESS`: IMAP mailbox address.
- `ECO_MAIL_PASSWORD`: IMAP password or app-specific password.
- `DINGTALK_CLIENT_ID`: DingTalk appKey.
- `DINGTALK_CLIENT_SECRET`: DingTalk appSecret.
- `ECO_IMAP_HOST`: IMAP host; defaults to `imap.qiye.aliyun.com` if unset.
- `ECO_IMAP_PORT`: IMAP port (SSL), defaults to `993`; must be an integer 1..65535.

### DingTalk recipients (config/dingtalk_recipients.json)
- `eco_todo_user_ids`: userId list for business TODOs.
- `error_todo_user_ids`: userId list for error TODOs (at least one).

## Security
- Secrets stay local: `.env` and `config/dingtalk_recipients.json` are gitignored.
- Only template files are tracked: `.env.example`, `config/dingtalk_recipients.example.json`.
- Missing required config raises RuntimeError early to avoid silent failures.

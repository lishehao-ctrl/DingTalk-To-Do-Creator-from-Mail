from __future__ import annotations
import os
from dingtalk_recipients import load_dingtalk_recipients, DingtalkRecipientConfigError


def _get_env_or_raise(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Environment variable {name} is required but not set or is empty.")
    return value


class mapping:
    # ----------Email content extraction----------
    # Business keywords
    ECO_requried_subject = "ECO审批流程"

    # Email header fields
    subject = "Subject"
    sent_date = "Date"
    message_id = "Message-ID"

    # Email body fields
    ecn_index = "ecn编码"
    ecn_name = "ecn名称"
    product_name = "产品名称"
    product_organizer = "工作负责人"

    # ----------DingTalk TODO settings----------

    # TODO creation date offset from sent time
    time_month_to_create_todo = 0  # month offset
    time_days_to_create_todo = 0  # day offset
    # Due date offset after creation offset
    due_date_from_created = 1 # week offset
    # Absolute due time
    due_time_hour = 18  # hour
    due_time_minute = 0  # minute
    due_time_second = 0  # second

    # ----------Email search window-----------
    # IMAP search window days before target date
    # Helps cover outages or network drops
    mapping_search_window = 10  # days

    # ----------Local state file----------
    # JSON filename and timestamp format for processed mail
    json_fn = "processed_messages.json"
    json_time_format = "%Y-%m-%d %H:%M:%S"

    # -----------DingTalk assignees-----------
    # UserIDs from DingTalk config file
    try:
        _recipients = load_dingtalk_recipients("config/dingtalk_recipients.json")
    except DingtalkRecipientConfigError as e:
        raise RuntimeError(str(e))
    DingDing_ids = _recipients.get("eco_todo_user_ids", [])

    # ----------Error TODO forwarding----------
    error_subject = "ECO自动创建代办-错误"
    error_description = "在处理邮件时发生错误，请及时处理。"
    # DingTalk UserIDs to receive error TODO
    error_user_ids = _recipients.get("error_todo_user_ids", [])
    if not error_user_ids:
        raise RuntimeError(
            "error_todo_user_ids must include at least one user ID in "
            "config/dingtalk_recipients.json."
        )
    # Absolute due time for error TODO
    error_due_time_hour = 18
    error_due_time_minute = 0
    error_due_time_second = 0

    # ----------Mail and DingTalk config----------
    # IMAP server settings
    mail_address = _get_env_or_raise("ECO_MAIL_ADDRESS")
    mail_password = _get_env_or_raise("ECO_MAIL_PASSWORD")
    imap_host = os.getenv("ECO_IMAP_HOST", "imap.qiye.aliyun.com")
    port_str = os.getenv("ECO_IMAP_PORT", "993")
    try:
        port = int(port_str)
    except ValueError as e:
        raise RuntimeError("ECO_IMAP_PORT must be an integer") from e
    if not (1 <= port <= 65535):
        raise RuntimeError("ECO_IMAP_PORT must be between 1 and 65535")

    # DingTalk app settings
    client_id = _get_env_or_raise("DINGTALK_CLIENT_ID")
    client_secret = _get_env_or_raise("DINGTALK_CLIENT_SECRET")

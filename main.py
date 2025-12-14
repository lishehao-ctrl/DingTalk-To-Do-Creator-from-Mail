from datetime import datetime
from dateutil.relativedelta import relativedelta
from mapping import mapping
import time
import mailparser
import dingtalk
import state
import inbox
import sys

try:
    # 通过 IMAP 安全拉取最近的原始邮件（bytes 列表）
    raw_emails = inbox.safe_get(
        mail_address=mapping.mail_address,
        mail_password=mapping.mail_password,
        imap_host=mapping.imap_host,
        port=mapping.port,
    )
    filtered_emails = []
    json_data_to_save = state.load_json()

    # 逐封过滤邮件
    for raw_email in raw_emails:
        # 解析原始邮件为 EmailMessage 对象
        msg = mailparser.mail_parser(raw_email)

        # 过滤：仅保留符合业务条件的邮件（不符合返回 None）
        msg_filtered = mailparser.mail_filter(msg=msg)

        if msg_filtered:
            filtered_emails.append(msg_filtered)

    # 如果没有符合条件的邮件，则退出
    if filtered_emails is None or len(filtered_emails) == 0:
        print("没有新邮件")
        time.sleep(15)
        sys.exit(0)

    for filtered_email in filtered_emails:
        # 如果过滤后的邮件为空，则跳过
        if not filtered_email:
            continue

        # 提取主题/发送时间/正文关键信息为字典
        contents = mailparser.extract_useful_parts(msg=filtered_email)
        if not contents or mapping.message_id not in contents:
            print(f"提取邮件关键信息失败，跳过处理{mapping.message_id}{contents.get(mapping.message_id, '无ID')}")
            continue

        # 发送钉钉待办：按配置的接收人和应用凭据
        dingtalk.send_eco_todo_task(
            contents=contents,
            user_ids=mapping.DingDing_ids,
            client_id=mapping.client_id,
            client_secret=mapping.client_secret,
        )
        print(f"钉钉待办发送成功: {mapping.ecn_index}{contents.get(mapping.ecn_index, '无主题')}")

        # 记录本次处理时间，避免后续重复处理同一邮件
        now_time = datetime.now().strftime(mapping.json_time_format)
        json_data_to_save[contents[mapping.message_id]] = now_time

    state.save_json(data=json_data_to_save)
except Exception as e:
    # 捕获所有异常，发送报错代办
    print(f"脚本运行失败: {str(e)}")
    try:
        # 计算报错代办的截止时间（相对于当前时间的下一个指定时间点）
        target_time = datetime.now().replace(
            hour=mapping.error_due_time_hour, 
            minute=mapping.error_due_time_minute, 
            second=mapping.error_due_time_second, 
            tzinfo=None
        )
        # 如果当前时间已过今天的指定时间点，则设为明天的该时间点
        if target_time < datetime.now().replace(tzinfo=None):
            target_time += relativedelta(days=1)
        # 改成钉钉兼容时间戳
        due_time = int(target_time.timestamp() * 1000)

        # 发送报错代办
        dingtalk.send_general_todo_task(
            subject=mapping.error_subject,
            contents=[
                mapping.error_description,
                f"错误详情: {str(e)}",
                f"时间: {datetime.now().strftime(mapping.json_time_format)}"
            ],
            user_ids=[mapping.error_user_ids],
            client_id=mapping.client_id,
            client_secret=mapping.client_secret,
            due_time=due_time,
        )
        print(f"发送报错代办成功: {str(e)}")
    except Exception as e2:
        print(f"发送报错代办失败: {str(e2)}")
finally:
    time.sleep(15)  # 避免脚本过快退出
    sys.exit(0)
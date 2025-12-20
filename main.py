from dotenv import load_dotenv

load_dotenv()

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
    # Fetch recent raw emails via IMAP securely (bytes list)
    raw_emails = inbox.safe_get(
        mail_address=mapping.mail_address,
        mail_password=mapping.mail_password,
        imap_host=mapping.imap_host,
        port=mapping.port,
    )
    filtered_emails = []
    json_data_to_save = state.load_json()

    # Filter emails one by one
    for raw_email in raw_emails:
        # Parse raw email into EmailMessage
        msg = mailparser.mail_parser(raw_email)

        # Keep only emails that meet business rules (else None)
        msg_filtered = mailparser.mail_filter(msg=msg)

        if msg_filtered:
            filtered_emails.append(msg_filtered)

    # Exit if no matching emails
    if filtered_emails is None or len(filtered_emails) == 0:
        print("没有新邮件")
        time.sleep(15)
        sys.exit(0)

    for filtered_email in filtered_emails:
        # Skip if filtered email is empty
        if not filtered_email:
            continue

        # Extract subject/sent time/body info into dict
        contents = mailparser.extract_useful_parts(msg=filtered_email)
        if not contents or mapping.message_id not in contents:
            print(f"提取邮件关键信息失败，跳过处理{mapping.message_id}{contents.get(mapping.message_id, '无ID')}")
            continue

        # Send DingTalk TODO using configured recipients and credentials
        dingtalk.send_eco_todo_task(
            contents=contents,
            user_ids=mapping.DingDing_ids,
            client_id=mapping.client_id,
            client_secret=mapping.client_secret,
        )
        print(f"钉钉待办发送成功: {mapping.ecn_index}{contents.get(mapping.ecn_index, '无主题')}")

        # Record processing time to avoid reprocessing
        now_time = datetime.now().strftime(mapping.json_time_format)
        json_data_to_save[contents[mapping.message_id]] = now_time

    state.save_json(data=json_data_to_save)
except Exception as e:
    # Catch all exceptions and send error TODO
    print(f"脚本运行失败: {str(e)}")
    try:
        # Compute error TODO due time at next configured moment
        target_time = datetime.now().replace(
            hour=mapping.error_due_time_hour, 
            minute=mapping.error_due_time_minute, 
            second=mapping.error_due_time_second, 
            tzinfo=None
        )
        # If now past cutoff, move to same time tomorrow
        if target_time < datetime.now().replace(tzinfo=None):
            target_time += relativedelta(days=1)
        # Convert to DingTalk-compatible timestamp
        due_time = int(target_time.timestamp() * 1000)

        # Send error TODO
        dingtalk.send_general_todo_task(
            subject=mapping.error_subject,
            contents=[
                mapping.error_description,
                f"错误详情: {str(e)}",
                f"时间: {datetime.now().strftime(mapping.json_time_format)}"
            ],
            user_ids=mapping.error_user_ids,
            client_id=mapping.client_id,
            client_secret=mapping.client_secret,
            due_time=due_time,
        )
        print(f"发送报错代办成功: {str(e)}")
    except Exception as e2:
        print(f"发送报错代办失败: {str(e2)}")
finally:
    time.sleep(15)  # Prevent script from exiting too fast
    sys.exit(0)

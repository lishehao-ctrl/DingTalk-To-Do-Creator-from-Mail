from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from mapping import mapping
import os
from dotenv import load_dotenv
import mailparser
import dingtalk
import state
import inbox

def cal_due_time() -> int:
    due = datetime.now() + relativedelta(months=mapping.time_month_to_create_todo)
    due_time = int(due.timestamp() * 1000)
    return due_time

load_dotenv(".api.env")
token = os.getenv("dingtalk_token")

due_time = cal_due_time(3)

raw_emails = inbox.safe_get(
    mail_address=os.getenv("mail_address"), 
    mail_password=os.getenv("mail_password"), 
    imap_host=os.getenv("imap_host"), 
    port=int(os.getenv("port"))
)

for raw_email in raw_emails:
    msg = mailparser.mail_parser(raw_email)
    msg = mailparser.mail_filter(msg=msg)
    if msg:
        contents = mailparser.extract_useful_parts(msg=msg)

        time = datetime.now().strftime(mapping.json_time_format)
        # state.save_json(data={contents[mapping.message_id]: time})

        dingtalk.send_eco_todo_task(
            contents=contents,
            user_ids=mapping.DingDing_ids,
            due_time=due_time,
            client_id=os.getenv("client_id"),
            client_secret=os.getenv("client_secret"),
        )

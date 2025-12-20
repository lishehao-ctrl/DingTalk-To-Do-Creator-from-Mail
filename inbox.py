import time, imaplib, ssl
from typing import List
from datetime import timedelta, datetime
from dateutil.relativedelta import relativedelta
from mapping import mapping

def safe_get(mail_address: str, mail_password: str, imap_host: str, port: int) -> List:
    """Safely pull raw email bytes from an IMAP inbox."""

    def get_inbox() -> List[str]:
        """Log in, filter by date, and return matching raw emails."""
        raw_emails = [] # Clear previous emails to avoid duplicates
        context = ssl.create_default_context()

        # Connect and log in to mailbox
        with imaplib.IMAP4_SSL(imap_host, port, ssl_context=context) as imap:
            # Login
            typ, _ = imap.login(mail_address, mail_password)
            print("邮箱登录:", typ)

            # Select inbox
            typ, count = imap.select("INBOX", readonly=True)
            print("选择收件箱:", typ, f"共{count[0].decode()}封邮件")

            # Filter emails by date
            # Start = now - creation offset - search window
            since = (
                datetime.now() 
                - relativedelta(months=mapping.time_month_to_create_todo, days=mapping.time_days_to_create_todo) 
                - timedelta(days=mapping.mapping_search_window)
                - timedelta(days=1)  # Include end date
            ).strftime("%d-%b-%Y")
             # End = now - creation offset
            before = (
                datetime.now() 
                - relativedelta(months=mapping.time_month_to_create_todo, days=mapping.time_days_to_create_todo) 
                + timedelta(days=1)  # Include end date
            ).strftime("%d-%b-%Y")
            typ, data = imap.search(None, 'SINCE', since, 'BEFORE', before)
            print("搜索邮件:", typ, f"搜索到{len(data[0].split())}封邮件")

            # Fetch matching emails
            seq_ids = data[0].split()
            for seq in reversed(seq_ids):
                typ, data = imap.fetch(seq, "(BODY.PEEK[])")
                raw_email = data[0][1]
                raw_emails.append(raw_email)

        return raw_emails

    raw_emails = []
    i = 0
    timeout = 0.5

    # Retry up to 3 times with backoff to handle network issues
    while i < 3:
        try:
            raw_emails = get_inbox()
            return raw_emails
        except Exception as e:
            print(f"调用IMAP接口失败, {str(e)}，等待{timeout}秒后重试")
            i += 1
            time.sleep(timeout)
            timeout *= 2

    return raw_emails

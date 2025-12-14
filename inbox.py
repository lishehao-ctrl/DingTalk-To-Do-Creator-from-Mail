import time, imaplib, ssl
from typing import List
from datetime import timedelta, datetime
from dateutil.relativedelta import relativedelta
from mapping import mapping

def safe_get(mail_address: str, mail_password: str, imap_host: str, port: int) -> List:
    """从 IMAP 邮箱安全拉取原始邮件字节列表。"""

    def get_inbox() -> List[str]:
        """登陆邮箱并按时间过滤，返回符合条件的原始邮件。"""
        raw_emails = [] # 忽略上一轮的邮件 避免重复处理
        context = ssl.create_default_context()

        # 连接并登录邮箱
        with imaplib.IMAP4_SSL(imap_host, port, ssl_context=context) as imap:
            # 登录
            typ, _ = imap.login(mail_address, mail_password)
            print("邮箱登录:", typ)

            # 选择收件箱
            typ, count = imap.select("INBOX", readonly=True)
            print("选择收件箱:", typ, f"共{count[0].decode()}封邮件")

            # 按时间过滤邮件
            # 逻辑：起始时间 = 当前时间 - 代办创建日期偏移 - 邮件搜索窗口
            since = (
                datetime.now() 
                - relativedelta(months=mapping.time_month_to_create_todo, days=mapping.time_days_to_create_todo) 
                - timedelta(days=mapping.mapping_search_window)
                - timedelta(days=1)  # 包含截止当天的邮件
            ).strftime("%d-%b-%Y")
             # 逻辑：结束时间 = 当前时间 - 代办创建日期偏移
            before = (
                datetime.now() 
                - relativedelta(months=mapping.time_month_to_create_todo, days=mapping.time_days_to_create_todo) 
                + timedelta(days=1)  # 包含截止当天的邮件
            ).strftime("%d-%b-%Y")
            typ, data = imap.search(None, 'SINCE', since, 'BEFORE', before)
            print("搜索邮件:", typ, f"搜索到{len(data[0].split())}封邮件")

            # 获取符合条件的邮件
            seq_ids = data[0].split()
            for seq in reversed(seq_ids):
                typ, data = imap.fetch(seq, "(BODY.PEEK[])")
                raw_email = data[0][1]
                raw_emails.append(raw_email)

        return raw_emails

    raw_emails = []
    i = 0
    timeout = 0.5

    # 最多尝试3次，避免偶发网络问题，每次尝试完暂停时间，间隔逐步加倍
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


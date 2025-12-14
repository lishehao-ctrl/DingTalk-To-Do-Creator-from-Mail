import io
from datetime import datetime, time
from dateutil.relativedelta import relativedelta
from email import policy, message
from email.parser import BytesParser
from email.header import decode_header
from email.utils import parsedate_to_datetime
from bs4 import BeautifulSoup
import re
from typing import List, Dict

from mapping import mapping
import state


def mail_parser(eml: bytes) -> message.EmailMessage:
    """将输入转成 EmailMessage，方便后续统一处理。"""
    if isinstance(eml, message.EmailMessage):
        return eml
    elif isinstance(eml, bytes):
        return BytesParser(policy=policy.default).parsebytes(eml)
    elif isinstance(eml, io.BufferedReader):
        return BytesParser(policy=policy.default).parse(eml)
    else:
        raise TypeError(f"邮件解析格式错误: {type(eml)}")

def decode_mime(s: bytes):
    """解码 MIME 头字段，返回可读字符串。"""
    parts = decode_header(s)
    return "".join([(b.decode(enc or "utf-8") if isinstance(b, bytes) else b) for b, enc in parts])

def mail_filter(msg: message.EmailMessage) -> message.EmailMessage|None:
    """过滤掉已处理或主题不匹配的邮件或未来邮件，返回 None；否则返回原始邮件对象。"""

    # 初始化变量
    Subject = ""
    date_to_create_todo = None
    ID = ""

    # 遍历邮件头，提取主题、发送时间、Message-ID
    for header in msg.keys():
        if header == mapping.subject:
            Subject = decode_mime(msg[header])
        elif header == mapping.sent_date:
            date = parsedate_to_datetime(decode_mime(msg[header]))
            # 计算待办创建日期：发送日期 + 代办创建日期的月/日数
            date_to_create_todo = (
                date 
                + relativedelta(months=mapping.time_month_to_create_todo) 
                + relativedelta(days=mapping.time_days_to_create_todo)
            )
            # 将创建日期的时间部分设为当天的最早时间（00:00:00），方便后续比较
            date_to_create_todo = datetime.combine(date_to_create_todo.date(), time.min)
        elif header == mapping.message_id:
            ID = decode_mime(msg[header])

    json_info = state.load_json()
    # 如果邮件已处理, 则返回 None
    if not ID or ID in list(json_info.keys()):
        return None

    # 如果代办创建日期在今天之后, 则返回 None
    if not date_to_create_todo or date_to_create_todo > datetime.now():
        return None
    
    # 如果主题不包含业务关键词, 则返回 None
    if not mapping.ECO_requried_subject in Subject:
        return None
    
    return msg
    
def extract_useful_parts(msg: message.EmailMessage) -> Dict[str, str | datetime]:

    def extract_header(msg: message.EmailMessage, result: Dict[str, str | datetime]) -> Dict[str, str | datetime]:
        """采集邮件头部的主题、时间、Message-ID。"""
        for header in msg.keys():
            if header == mapping.subject:
                result[mapping.subject] = decode_mime(msg[header])
            elif header == mapping.sent_date:
                # 将邮件发送日期转成 datetime 对象
                result[mapping.sent_date] = parsedate_to_datetime(decode_mime(msg[header]))
            elif header == mapping.message_id:
                result[mapping.message_id] = decode_mime(msg[header])
        return result
    
    def extract_body(content: str, result: Dict[str, str]) -> Dict[str, str]:
        """从正文中抓取 ECO 关键字段。"""
        content_str = content.strip()

        # 用正则表达式提取关键字段
        # 如果找不到则返回 None
        ecn_index = re.search(rf"(?:{mapping.ecn_index}[:：]\s*)([^\n\s]+)", content_str)
        if ecn_index:
            ecn_index = ecn_index.group(1)

        ecn_name = re.search(rf"(?:{mapping.ecn_name}[:：]\s*)([^\n]+)", content_str)
        if ecn_name:
            ecn_name = ecn_name.group(1)

        product_name = re.search(rf"(?:{mapping.product_name}[:：]\s*)([^\n]+)", content_str)
        if product_name:
            product_name = product_name.group(1)

        product_organizer = re.search(rf"(?:{mapping.product_organizer}[:：]\s*)([^\n]+)", content_str)
        if product_organizer:
            product_organizer = product_organizer.group(1)

        # 将提取到的关键字段加入结果字典
        if ecn_index:
            useful_parts[mapping.ecn_index] = ecn_index
        if ecn_name:
            useful_parts[mapping.ecn_name] = ecn_name
        if product_name:
            useful_parts[mapping.product_name] = product_name
        if product_organizer:
            useful_parts[mapping.product_organizer] = product_organizer

        return result

    useful_parts: Dict[str, str | datetime] = {}

    useful_parts = extract_header(msg=msg, result=useful_parts)

    for part in msg.walk():
        if part.is_multipart():
            continue

        # 仅处理文本和 HTML 内容
        if part.get_content_type() not in ["text/plain", "text/html"]:
            continue
        elif part.get_content_type() == "text/plain":
            txt = part.get_content()
            useful_parts = extract_body(content=txt, result=useful_parts)
            break
        elif part.get_content_type() == "text/html":
            soup = BeautifulSoup(part.get_content(), "html.parser")
            txt = soup.getText("\n",strip=True)
            useful_parts = extract_body(content=txt, result=useful_parts)
            break
        
    return useful_parts


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
    """Convert input to EmailMessage for uniform handling."""
    if isinstance(eml, message.EmailMessage):
        return eml
    elif isinstance(eml, bytes):
        return BytesParser(policy=policy.default).parsebytes(eml)
    elif isinstance(eml, io.BufferedReader):
        return BytesParser(policy=policy.default).parse(eml)
    else:
        raise TypeError(f"邮件解析格式错误: {type(eml)}")

def decode_mime(s: bytes):
    """Decode a MIME header and return readable text."""
    parts = decode_header(s)
    return "".join([(b.decode(enc or "utf-8") if isinstance(b, bytes) else b) for b, enc in parts])

def mail_filter(msg: message.EmailMessage) -> message.EmailMessage|None:
    """Filter processed, future, or mismatched emails; return None or the msg."""

    # Init variables
    Subject = ""
    date_to_create_todo = None
    ID = ""

    # Walk headers to get subject, sent time, and Message-ID
    for header in msg.keys():
        if header == mapping.subject:
            Subject = decode_mime(msg[header])
        elif header == mapping.sent_date:
            date = parsedate_to_datetime(decode_mime(msg[header]))
            # Calc TODO creation date: send date + month/day offsets
            date_to_create_todo = (
                date 
                + relativedelta(months=mapping.time_month_to_create_todo) 
                + relativedelta(days=mapping.time_days_to_create_todo)
            )
            # Set creation time to 00:00:00 for comparison
            date_to_create_todo = datetime.combine(date_to_create_todo.date(), time.min)
        elif header == mapping.message_id:
            ID = decode_mime(msg[header])

    json_info = state.load_json()
    # Return None if email already processed
    if not ID or ID in list(json_info.keys()):
        return None

    # Return None if creation date is in the future
    if not date_to_create_todo or date_to_create_todo > datetime.now():
        return None
    
    # Return None if subject misses business keyword
    if not mapping.ECO_requried_subject in Subject:
        return None
    
    return msg
    
def extract_useful_parts(msg: message.EmailMessage) -> Dict[str, str | datetime]:

    def extract_header(msg: message.EmailMessage, result: Dict[str, str | datetime]) -> Dict[str, str | datetime]:
        """Collect subject, sent time, and Message-ID."""
        for header in msg.keys():
            if header == mapping.subject:
                result[mapping.subject] = decode_mime(msg[header])
            elif header == mapping.sent_date:
                # Convert sent date to datetime
                result[mapping.sent_date] = parsedate_to_datetime(decode_mime(msg[header]))
            elif header == mapping.message_id:
                result[mapping.message_id] = decode_mime(msg[header])
        return result
    
    def extract_body(content: str, result: Dict[str, str]) -> Dict[str, str]:
        """Pull ECO key fields from body."""
        content_str = content.strip()

        # Use regex to extract key fields
        # Skip if not found
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

        # Add extracted fields to result dict
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

        # Only handle text or HTML content
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


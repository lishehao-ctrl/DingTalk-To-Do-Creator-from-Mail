from typing import List, Dict, Tuple
import requests

from datetime import datetime, timezone
import time
from dateutil.relativedelta import relativedelta

from alibabacloud_dingtalk.todo_1_0.client import Client as dingtalktodo_1_0Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_dingtalk.todo_1_0 import models as dingtalktodo__1__0_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_tea_util.client import Client as UtilClient
from alibabacloud_dingtalk.oauth2_1_0.client import Client as dingtalkoauth2_1_0Client
from alibabacloud_dingtalk.oauth2_1_0 import models as dingtalkoauth_2__1__0_models

from mapping import mapping

def send_eco_todo_task(
    contents: Dict[str, str],
    user_ids: List[str],
    client_id: str,
    client_secret: str,
):
    """Create a DingTalk TODO task from parsed email content."""

    def split_subject_content() -> Tuple[str, Dict]:
        """Prepare TODO subject and body fields with defaults."""
        subject = f"海外ECO{contents.get(mapping.ecn_index, '无编号')}导入提醒"

        content = {}
        content[mapping.ecn_index] = contents.get(mapping.ecn_index, "无内容").strip()
        content[mapping.ecn_name] = contents.get(mapping.ecn_name, "无内容").strip()
        content[mapping.product_name] = contents.get(mapping.product_name, "无内容").strip()
        content[mapping.product_organizer] = contents.get(mapping.product_organizer, "无内容").strip()

        return subject, content
    
    def cal_due_time() -> int:
        """Compute due time with configured offsets, return milliseconds."""
        # Due date = send date + creation offsets + due weeks + due time
        due_date = contents[mapping.sent_date] + relativedelta(
            months=mapping.time_month_to_create_todo,
            weeks=mapping.due_date_from_created,
            days=mapping.time_days_to_create_todo,
            hour=mapping.due_time_hour,
            minute=mapping.due_time_minute,
            second=mapping.due_time_second
        )
        # If due date is before tomorrow, shift to tomorrow's due time
        due_date = max(due_date.replace(tzinfo=None), (datetime.now() + relativedelta(days=1)).replace(tzinfo=None)) + relativedelta(
            hour=mapping.due_time_hour,
            minute=mapping.due_time_minute,
            second=mapping.due_time_second
        )
        # Required by DingTalk API
        due_time = int(due_date.timestamp() * 1000)
        return due_time
    
    # Build TODO subject and content
    subject, content = split_subject_content()

    # Get app access_token
    try:
        app_access_token = get_app_token(client_id=client_id, client_secret=client_secret)
        if not app_access_token:
            raise Exception("app_access_token为空")
    except Exception:
        time.sleep(1)  # Avoid being rate limited by DingTalk
        try:
            app_access_token = get_app_token(client_id=client_id, client_secret=client_secret)
            if not app_access_token:
                raise Exception("app_access_token为空")
        except Exception as e:
            raise Exception(f"获取app_access_token失败，{e.code}: {e.message}")
    
    # Get union_id list for TODO recipients
    union_ids = []
    union_id_fails = []
    try:
        # Get union_id for all users
        union_ids = [get_union_id(token=app_access_token, user_id=id) for id in user_ids]
        # Ensure union_ids were fetched
        if not union_ids:
            raise Exception("union_ids为空")
    except Exception:
        time.sleep(1)  # Avoid being rate limited by DingTalk
        for id in user_ids:
            # Keep others even if some fetch fail
            try:
                union_id = get_union_id(token=app_access_token, user_id=id)
                union_ids.append(union_id)
            except Exception:
                # Record user_ids that failed
                union_id_fails.append(id)
        if not union_ids:
            raise Exception("union_ids为空")
        # Raise if some union_ids failed
        if union_id_fails:
            raise Exception(f"部分union_id获取失败，失败的user_id列表：{' '.join(f'UserID: {id}' for id in union_id_fails)}")

    config = open_api_models.Config()
    config.protocol = 'https'
    config.region_id = 'central'
    todo_client = dingtalktodo_1_0Client(config)

    # Create TODO for each recipient
    for union_id in union_ids:
        create_todo_task_headers = dingtalktodo__1__0_models.CreateTodoTaskHeaders()
        create_todo_task_headers.x_acs_dingtalk_access_token = app_access_token
        create_todo_task_request = dingtalktodo__1__0_models.CreateTodoTaskRequest(
            subject=subject,
            description=create_description(content=content),
            creator_id=union_id,
            executor_ids=[union_id],
            participant_ids=[union_id],
            due_time=cal_due_time(contents[mapping.sent_date]),
        )

        # Try to create TODO, retry once on failure
        try:
            todo_client.create_todo_task_with_options(union_id=union_id, request=create_todo_task_request, headers=create_todo_task_headers, runtime=util_models.RuntimeOptions())
        except Exception:
            time.sleep(1)  # Avoid being rate limited by DingTalk
            try:
                todo_client.create_todo_task_with_options(union_id=union_id, request=create_todo_task_request, headers=create_todo_task_headers, runtime=util_models.RuntimeOptions())
            except Exception as e:
                raise Exception(f"创建待办失败，{e.code}: {e.message}")

def send_general_todo_task(
        client_id: str, 
        client_secret: str, 
        subject: str, 
        contents: List[str], 
        user_ids: List[str],
        due_time: int,
    ):
    """Send a generic TODO task, e.g., for error distribution."""
    # Get app access_token
    try:
        app_access_token = get_app_token(client_id=client_id, client_secret=client_secret)
        if not app_access_token:
            raise Exception("app_access_token为空")
    except Exception:
        time.sleep(1)  # Avoid being rate limited by DingTalk
        try:
            app_access_token = get_app_token(client_id=client_id, client_secret=client_secret)
            if not app_access_token:
                raise Exception("app_access_token为空")
        except Exception as e:
            raise Exception(f"获取app_access_token失败，{e.code}: {e.message}")
        
    # Get union_id list for TODO recipients
    try:
        union_ids = [get_union_id(token=app_access_token, user_id=userid) for userid in user_ids]
        if not union_ids:
            raise Exception("union_ids为空")
    except Exception:
        time.sleep(1)  # Avoid being rate limited by DingTalk
        try:
            union_ids = [get_union_id(token=app_access_token, user_id=userid) for userid in user_ids]
            if not union_ids:
                raise Exception("union_ids为空")
        except Exception as e:
            raise Exception(f"获取union_ids失败，{e.code}: {e.message}")
    
    config = open_api_models.Config()
    config.protocol = 'https'
    config.region_id = 'central'
    todo_client = dingtalktodo_1_0Client(config)

    # Create TODO for each recipient
    for union_id in union_ids:
        create_todo_task_headers = dingtalktodo__1__0_models.CreateTodoTaskHeaders()
        create_todo_task_headers.x_acs_dingtalk_access_token = app_access_token
        create_todo_task_request = dingtalktodo__1__0_models.CreateTodoTaskRequest(
            subject=subject,
            description=create_description(contents),
            creator_id=union_id,
            executor_ids=[union_id],
            participant_ids=[union_id],
            due_time=due_time,
        )
        # Try to create TODO, retry once on failure
        try:
            todo_client.create_todo_task_with_options(union_id=union_id, request=create_todo_task_request, headers=create_todo_task_headers, runtime=util_models.RuntimeOptions())
        except Exception:
            time.sleep(1)  # Avoid being rate limited by DingTalk
            try:
                todo_client.create_todo_task_with_options(union_id=union_id, request=create_todo_task_request, headers=create_todo_task_headers, runtime=util_models.RuntimeOptions())
            except Exception as e:
                raise Exception(f"创建待办失败，{str(e)}")
            
def create_description(content: Dict[str, str] | List[str]) -> str:
    """Build TODO description, one field per line."""
    description = ""

    if isinstance(content, list):
        for item in content:
            description += f"- {item}\n"
    elif isinstance(content, dict):
        for key, value in content.items():
            description += f"{key}：{value}\n"

    return description

def get_app_token(client_id: str, client_secret: str) -> str:
    """Use appKey/appSecret to obtain a DingTalk app access_token."""
    config = open_api_models.Config()
    config.protocol = 'https'
    config.region_id = 'central'
    token_client = dingtalkoauth2_1_0Client(config)

    get_access_token_request = dingtalkoauth_2__1__0_models.GetAccessTokenRequest(
        app_key=client_id,
        app_secret=client_secret,
    )

    token = token_client.get_access_token(get_access_token_request).body.access_token
    return token

def get_union_id(token: str, user_id: str) -> str:
    """Query unionId by userId using the enterprise access_token."""
    url = f"https://oapi.dingtalk.com/topapi/v2/user/get?access_token={token}"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "userid": user_id
    }
    response = requests.post(url, headers=headers, json=data)
    result = response.json()

    return result["result"]["unionid"]

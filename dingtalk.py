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
    """根据解析到的邮件内容，创建钉钉待办任务。"""

    def split_subject_content() -> Tuple[str, Dict]:
        """准备待办主题和正文字段，填充缺省值。"""
        subject = f"海外ECO{contents.get(mapping.ecn_index, '无编号')}导入提醒"

        content = {}
        content[mapping.ecn_index] = contents.get(mapping.ecn_index, "无内容").strip()
        content[mapping.ecn_name] = contents.get(mapping.ecn_name, "无内容").strip()
        content[mapping.product_name] = contents.get(mapping.product_name, "无内容").strip()
        content[mapping.product_organizer] = contents.get(mapping.product_organizer, "无内容").strip()

        return subject, content
    
    def cal_due_time() -> int:
        """按配置月份偏移计算截止时间，返回毫秒时间戳。"""
        # 截止日期 = 邮件发送日期 + 代办创建日期的月/日数 + 代办截止日期的周数 + 代办截止时间的时分秒
        due_date = contents[mapping.sent_date] + relativedelta(
            months=mapping.time_month_to_create_todo,
            weeks=mapping.due_date_from_created,
            days=mapping.time_days_to_create_todo,
            hour=mapping.due_time_hour,
            minute=mapping.due_time_minute,
            second=mapping.due_time_second
        )
        # 如果截止日期早于明天，则调整为明天的截止时间
        due_date = max(due_date.replace(tzinfo=None), (datetime.now() + relativedelta(days=1)).replace(tzinfo=None)) + relativedelta(
            hour=mapping.due_time_hour,
            minute=mapping.due_time_minute,
            second=mapping.due_time_second
        )
        # 钉钉api要求
        due_time = int(due_date.timestamp() * 1000)
        return due_time
    
    # 获得所需的代办标题和内容
    subject, content = split_subject_content()

    # 获取应用 access_token
    try:
        app_access_token = get_app_token(client_id=client_id, client_secret=client_secret)
        if not app_access_token:
            raise Exception("app_access_token为空")
    except Exception:
        time.sleep(1)  # 避免频率过快被钉钉拒绝
        try:
            app_access_token = get_app_token(client_id=client_id, client_secret=client_secret)
            if not app_access_token:
                raise Exception("app_access_token为空")
        except Exception as e:
            raise Exception(f"获取app_access_token失败，{e.code}: {e.message}")
    
    # 获取待办接收人的 union_id 列表
    union_ids = []
    union_id_fails = []
    try:
        # 获取所有用户的 union_id
        union_ids = [get_union_id(token=app_access_token, user_id=id) for id in user_ids]
        # 检查是否成功获取到 union_ids
        if not union_ids:
            raise Exception("union_ids为空")
    except Exception:
        time.sleep(1)  # 避免频率过快被钉钉拒绝
        for id in user_ids:
            # 避免部分失败导致全部失败
            try:
                union_id = get_union_id(token=app_access_token, user_id=id)
                union_ids.append(union_id)
            except Exception:
                # 获取 union_id 失败，记录失败的 user_id
                union_id_fails.append(id)
        if not union_ids:
            raise Exception("union_ids为空")
        # 将部分失效的id报错
        if union_id_fails:
            raise Exception(f"部分union_id获取失败，失败的user_id列表：{' '.join(f'UserID: {id}' for id in union_id_fails)}")

    config = open_api_models.Config()
    config.protocol = 'https'
    config.region_id = 'central'
    todo_client = dingtalktodo_1_0Client(config)

    # 逐个接收人创建待办
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

        # 尝试创建待办，失败则重试一次
        try:
            todo_client.create_todo_task_with_options(union_id=union_id, request=create_todo_task_request, headers=create_todo_task_headers, runtime=util_models.RuntimeOptions())
        except Exception:
            time.sleep(1)  # 避免频率过快被钉钉拒绝
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
    """发送通用待办任务，可用于报错分发等场景。"""
    # 获取应用 access_token
    try:
        app_access_token = get_app_token(client_id=client_id, client_secret=client_secret)
        if not app_access_token:
            raise Exception("app_access_token为空")
    except Exception:
        time.sleep(1)  # 避免频率过快被钉钉拒绝
        try:
            app_access_token = get_app_token(client_id=client_id, client_secret=client_secret)
            if not app_access_token:
                raise Exception("app_access_token为空")
        except Exception as e:
            raise Exception(f"获取app_access_token失败，{e.code}: {e.message}")
        
    # 获取待办接收人的 union_id 列表
    try:
        union_ids = [get_union_id(token=app_access_token, user_id=userid) for userid in user_ids]
        if not union_ids:
            raise Exception("union_ids为空")
    except Exception:
        time.sleep(1)  # 避免频率过快被钉钉拒绝
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

    # 逐个接收人创建待办
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
        # 尝试创建待办，失败则重试一次
        try:
            todo_client.create_todo_task_with_options(union_id=union_id, request=create_todo_task_request, headers=create_todo_task_headers, runtime=util_models.RuntimeOptions())
        except Exception:
            time.sleep(1)  # 避免频率过快被钉钉拒绝
            try:
                todo_client.create_todo_task_with_options(union_id=union_id, request=create_todo_task_request, headers=create_todo_task_headers, runtime=util_models.RuntimeOptions())
            except Exception as e:
                raise Exception(f"创建待办失败，{str(e)}")
            
def create_description(content: Dict[str, str] | List[str]) -> str:
    """生成待办描述，每行一个字段。"""
    description = ""

    if isinstance(content, list):
        for item in content:
            description += f"- {item}\n"
    elif isinstance(content, dict):
        for key, value in content.items():
            description += f"{key}：{value}\n"

    return description

def get_app_token(client_id: str, client_secret: str) -> str:
    """用 appKey/appSecret 向钉钉换取应用 access_token。"""
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
    """通过 userId 查询 unionId，需携带企业 access_token。"""
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
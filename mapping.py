from __future__ import annotations

class mapping:
    # ----------邮件内容提取相关----------
    # 业务相关的关键词
    ECO_requried_subject = "ECO审批流程"

    # 邮件头部关键字段
    subject = "Subject"
    sent_date = "Date"
    message_id = "Message-ID"

    # 邮件内容关键字段
    ecn_index = "ecn编码"
    ecn_name = "ecn名称"
    product_name = "产品名称"
    product_organizer = "工作负责人"

    # ----------钉钉待办相关----------

    # 代办创建日期（相对于邮件发送日期）
    time_month_to_create_todo = 0  # 月
    time_days_to_create_todo = 0  # 天
    # 代办截止日期（相对于邮件发送日期+代办创建日期偏移）
    due_date_from_created = 1 # 周
    # 代办截止日期（绝对时间）
    due_time_hour = 18  # 时
    due_time_minute = 0  # 分
    due_time_second = 0  # 秒

    # ----------邮件搜索条件-----------
    # IMAP 搜索窗口：在目标筛选日期前额外回溯的天数
    # 用于弥补脚本停机或网络闪断时可能错过的邮件
    mapping_search_window = 10  # 天

    # ----------本地状态文件----------
    # 用于存储已处理邮件的 JSON 文件名和时间格式
    json_fn = "processed_messages.json"
    json_time_format = "%Y-%m-%d %H:%M:%S"

    # -----------钉钉待办人-----------
    # UserID：需要从钉钉开发者平台获取
    # [0]: 朱莹莹
    # [1]: 高哲
    DingDing_ids = [
        # "16853271524727069",
        # "17182654619213200",
    ]

    # ----------报错分发代办----------
    error_subject = "ECO自动创建代办-错误"
    error_description = "在处理邮件时发生错误，请及时处理。"
    # 接收报错代办的钉钉 UserID
    error_user_ids = "16606118044638944" #Viego
    # 报错代办截止时间（绝对时间）
    error_due_time_hour = 18
    error_due_time_minute = 0
    error_due_time_second = 0

    # ----------邮箱和钉钉应用配置----------
    # 邮箱 IMAP 服务器配置
    mail_address = "eco.service@intalight.com"
    mail_password = "RzvC4d82aB"
    imap_host = "imap.qiye.aliyun.com"
    port = 993

    # 钉钉应用配置
    client_id = "dingawvuo4tev3ugi9fm"
    client_secret = "F_ubFc2GC3MwmyBB9KrmcZkHjoSs2RbKX9cYtUri5Jqlgf30dyivLh21JFZO681d"
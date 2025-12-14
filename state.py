import os
import sys
import json
from typing import Dict
from mapping import mapping

def fn_relative(fn=None, sub_folder=None):
    """获取相对于当前脚本的文件路径"""
    if fn and os.path.isabs(fn):
        return fn
    else:
        if getattr(sys, 'frozen', False):
            hd = os.path.dirname(sys.executable)
        else:
            hd, _ = os.path.split(os.path.realpath(__file__))

        if sub_folder is None:
            # 没有 sub_folder，也没有 fn → 就是程序目录
            path = hd if fn is None else os.path.join(hd, fn)
        else:
            # 先拼子目录
            folder = os.path.join(hd, sub_folder)
            if fn is None:
                path = folder   # 只要文件夹路径
            else:
                path = os.path.join(folder, fn)

        path = os.path.realpath(path)

        # 如果是文件 → 确保父目录存在；如果是目录 → 确保自己存在
        if fn is None:
            os.makedirs(path, exist_ok=True)
        else:
            os.makedirs(os.path.dirname(path), exist_ok=True)

        return path

def save_json(data: Dict):
    """保存已处理的消息状态"""
    fp = fn_relative(mapping.json_fn)
    with open(fp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_json() -> Dict:
    """
    加载已处理的消息状态
    如果文件不存在或无法解析，则创建空文件并返回空字典
    """
    fp = fn_relative(mapping.json_fn)
    try:
        with open(fp, "r", encoding="utf-8") as f:
            data_loaded = json.load(f)
    except:
        save_json(data={})
        data_loaded = {}

    return data_loaded

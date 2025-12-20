import os
import sys
import json
from typing import Dict
from mapping import mapping

def fn_relative(fn=None, sub_folder=None):
    """Get file path relative to this script."""
    if fn and os.path.isabs(fn):
        return fn
    else:
        if getattr(sys, 'frozen', False):
            hd = os.path.dirname(sys.executable)
        else:
            hd, _ = os.path.split(os.path.realpath(__file__))

        if sub_folder is None:
            # No sub_folder and no fn → use program directory
            path = hd if fn is None else os.path.join(hd, fn)
        else:
            # Build subfolder path first
            folder = os.path.join(hd, sub_folder)
            if fn is None:
                path = folder   # Only need folder path
            else:
                path = os.path.join(folder, fn)

        path = os.path.realpath(path)

        # If file ensure parent exists; if folder ensure folder exists
        if fn is None:
            os.makedirs(path, exist_ok=True)
        else:
            os.makedirs(os.path.dirname(path), exist_ok=True)

        return path

def save_json(data: Dict):
    """Save processed message state."""
    fp = fn_relative(mapping.json_fn)
    with open(fp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_json() -> Dict:
    """Load processed message state, creating an empty file if missing or invalid."""
    fp = fn_relative(mapping.json_fn)
    try:
        with open(fp, "r", encoding="utf-8") as f:
            data_loaded = json.load(f)
    except:
        save_json(data={})
        data_loaded = {}

    return data_loaded

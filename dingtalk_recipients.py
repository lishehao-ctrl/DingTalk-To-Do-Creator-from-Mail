import json
from pathlib import Path
from typing import Dict, List


class DingtalkRecipientConfigError(RuntimeError):
    pass


def load_dingtalk_recipients(path: str) -> Dict[str, List[str]]:
    """
    Load DingTalk recipient config.
    Expected keys:
      eco_todo_user_ids: list[str]
      error_todo_user_ids: list[str]
    """
    cfg_path = Path(path)
    if not cfg_path.exists():
        example_path = cfg_path.parent / "dingtalk_recipients.example.json"
        if example_path.exists():
            try:
                with open(example_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                raise DingtalkRecipientConfigError(
                    "Failed to read example recipient config; "
                    "please create config/dingtalk_recipients.json."
                ) from e
            _validate_payload(data, allow_empty=True)
            raise DingtalkRecipientConfigError(
                "Missing config/dingtalk_recipients.json. "
                "Copy config/dingtalk_recipients.example.json and fill user IDs."
            )
        raise DingtalkRecipientConfigError(
            "Missing config/dingtalk_recipients.json. "
            "Create it based on config/dingtalk_recipients.example.json."
        )

    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        raise DingtalkRecipientConfigError(
            "Failed to read config/dingtalk_recipients.json."
        ) from e

    _validate_payload(data, allow_empty=False)
    return data


def _validate_payload(data: dict, allow_empty: bool) -> None:
    if not isinstance(data, dict):
        raise DingtalkRecipientConfigError("Recipient config must be a JSON object.")
    for key in ("eco_todo_user_ids", "error_todo_user_ids"):
        if key not in data:
            raise DingtalkRecipientConfigError(f"Missing key: {key}")
        if not isinstance(data[key], list):
            raise DingtalkRecipientConfigError(f"{key} must be a list of strings.")
        if not allow_empty and len(data[key]) == 0:
            raise DingtalkRecipientConfigError(f"{key} cannot be empty.")
        for v in data[key]:
            if not isinstance(v, str):
                raise DingtalkRecipientConfigError(f"All {key} entries must be strings.")

import os
import yaml
from pathlib import Path
from types import SimpleNamespace as config


def get_workspace() -> Path:
    """返回 workspace/novels 路径"""
    return Path(__file__).parent.parent.parent / "workspace" / "novels"


def remove_fields(data, fields=None):
    """递归移除结构中的指定字段"""
    if fields is None:
        fields = ['text']
    if isinstance(data, dict):
        return {k: remove_fields(v, fields)
                for k, v in data.items() if k not in fields}
    elif isinstance(data, list):
        return [remove_fields(item, fields) for item in data]
    return data


def count_tokens(text, model=None):
    """简单 token 估算"""
    if not text:
        return 0
    try:
        import litellm
        return litellm.token_counter(model=model, text=text)
    except Exception:
        return len(text) // 4


class ConfigLoader:
    """从 config.yaml 加载配置"""

    def __init__(self, default_path: str = None):
        if default_path is None:
            default_path = Path(__file__).parent / "config.yaml"
        self._default_dict = self._load_yaml(default_path)

    @staticmethod
    def _load_yaml(path):
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def _validate_keys(self, user_dict):
        unknown_keys = set(user_dict) - set(self._default_dict)
        if unknown_keys:
            raise ValueError(f"Unknown config keys: {unknown_keys}")

    def load(self, user_opt=None) -> config:
        """加载配置，合并用户选项与默认值"""
        if user_opt is None:
            user_dict = {}
        elif isinstance(user_opt, config):
            user_dict = vars(user_opt)
        elif isinstance(user_opt, dict):
            user_dict = user_opt
        else:
            raise TypeError("user_opt must be dict, config(SimpleNamespace) or None")

        self._validate_keys(user_dict)
        merged = {**self._default_dict, **user_dict}
        return config(**merged)
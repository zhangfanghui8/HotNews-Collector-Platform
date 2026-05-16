import os
from pathlib import Path
from typing import Any, Dict

import yaml

ROOT = Path(__file__).resolve().parent.parent.parent.parent
CONFIG_PATH = ROOT / "config.yaml"


def load_config() -> Dict[str, Any]:
    """加载项目配置（当前主要为推送渠道配置）"""
    if not CONFIG_PATH.exists():
        return {}

    with open(CONFIG_PATH, encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    _apply_push_env_overrides(config)
    return config


def _apply_push_env_overrides(config: Dict[str, Any]) -> None:
    push = config.setdefault("push", {})
    channels = push.setdefault("channels", {})
    wecom = channels.setdefault("wecom", {})
    pushplus = channels.setdefault("pushplus", {})
    dingtalk = channels.setdefault("dingtalk", {})

    wecom_key = os.getenv("WECOM_WEBHOOK_KEY", "").strip()
    if wecom_key:
        wecom["webhook_key"] = wecom_key
        wecom["enabled"] = True

    pushplus_token = os.getenv("PUSHPLUS_TOKEN", "").strip()
    if pushplus_token:
        pushplus["token"] = pushplus_token
        pushplus["enabled"] = True

    dingtalk_token = os.getenv("DINGTALK_ACCESS_TOKEN", "").strip()
    if dingtalk_token:
        dingtalk["access_token"] = dingtalk_token
        dingtalk["enabled"] = True
    dingtalk_secret = os.getenv("DINGTALK_SECRET", "").strip()
    if dingtalk_secret:
        dingtalk["secret"] = dingtalk_secret

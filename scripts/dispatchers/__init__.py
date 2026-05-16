from typing import Any, Dict, List

from .dingtalk import DingTalkDispatcher
from .pushplus import PushPlusDispatcher
from .push_guide import DispatchResult
from .wecom import WeComDispatcher


def build_dispatchers(config: Dict[str, Any]) -> List:
    channels = config.get("push", {}).get("channels", {})
    dispatchers = []

    wecom_cfg = channels.get("wecom", {})
    if wecom_cfg.get("enabled") and wecom_cfg.get("webhook_key"):
        dispatchers.append(WeComDispatcher(wecom_cfg["webhook_key"]))

    pushplus_cfg = channels.get("pushplus", {})
    if pushplus_cfg.get("enabled") and pushplus_cfg.get("token"):
        dispatchers.append(
            PushPlusDispatcher(
                pushplus_cfg["token"],
                pushplus_cfg.get("channel", ""),
            )
        )

    dingtalk_cfg = channels.get("dingtalk", {})
    if dingtalk_cfg.get("enabled") and dingtalk_cfg.get("access_token"):
        dispatchers.append(
            DingTalkDispatcher(
                dingtalk_cfg["access_token"],
                dingtalk_cfg.get("secret", ""),
            )
        )

    return dispatchers


def dispatch_all(title: str, content: str, config: Dict[str, Any]) -> List[DispatchResult]:
    results = []
    for dispatcher in build_dispatchers(config):
        results.append(dispatcher.send(title, content))
    return results

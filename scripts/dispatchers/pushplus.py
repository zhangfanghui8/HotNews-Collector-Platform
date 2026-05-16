import requests

from .core.base import BaseDispatcher
from .push_guide import DispatchResult

PUSHPLUS_SEND_URL = "https://www.pushplus.plus/send"

# PushPlus 常见错误码 → 内部错误码
_ERROR_CODE_MAP = {
    905: "PUSHPLUS_NOT_VERIFIED",
    903: "PUSHPLUS_INVALID_TOKEN",
    904: "PUSHPLUS_INVALID_TOKEN",
}


class PushPlusDispatcher(BaseDispatcher):
    """PushPlus：推送到个人微信（需注册获取 token）"""

    name = "pushplus"

    def __init__(self, token: str, channel: str = ""):
        self.token = token.strip()
        self.channel = channel.strip()

    def send(self, title: str, content: str) -> DispatchResult:
        if not self.token:
            return DispatchResult(
                channel=self.name,
                success=False,
                error_code="PUSHPLUS_MISSING_TOKEN",
                raw_message="未配置 token",
            )

        payload = {
            "token": self.token,
            "title": title,
            "content": content,
            "template": "markdown",
        }
        if self.channel:
            payload["channel"] = self.channel

        try:
            resp = requests.post(PUSHPLUS_SEND_URL, json=payload, timeout=15)
            resp.raise_for_status()
            result = resp.json()
            if result.get("code") != 200:
                api_code = result.get("code")
                error_code = _ERROR_CODE_MAP.get(api_code, "SEND_FAILED")
                msg = result.get("msg") or str(result)
                return DispatchResult(
                    channel=self.name,
                    success=False,
                    error_code=error_code,
                    raw_message=msg,
                )
            return DispatchResult(channel=self.name, success=True)
        except Exception as e:
            return DispatchResult(
                channel=self.name,
                success=False,
                error_code="SEND_FAILED",
                raw_message=str(e),
            )

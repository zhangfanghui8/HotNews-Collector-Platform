import base64
import hashlib
import hmac
import time
import urllib.parse

import requests

from .core.base import BaseDispatcher
from .push_guide import DispatchResult

DINGTALK_WEBHOOK_URL = "https://oapi.dingtalk.com/robot/send"
# 钉钉 markdown 单条 text 建议不超过约 20000 字符，保守截断
MAX_TEXT_BYTES = 18000


def _build_signed_url(access_token: str, secret: str) -> str:
    timestamp = str(round(time.time() * 1000))
    string_to_sign = f"{timestamp}\n{secret}"
    sign_bytes = hmac.new(
        secret.encode("utf-8"),
        string_to_sign.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(sign_bytes))
    return (
        f"{DINGTALK_WEBHOOK_URL}?access_token={access_token}"
        f"&timestamp={timestamp}&sign={sign}"
    )


def _map_error(errcode, errmsg: str) -> str:
    if errcode in (88, 300001):
        return "DINGTALK_INVALID_TOKEN"
    errmsg_lower = (errmsg or "").lower()
    if "sign" in errmsg_lower or "签名" in errmsg:
        return "DINGTALK_SIGN_ERROR"
    if "keyword" in errmsg_lower or "关键词" in errmsg:
        return "DINGTALK_KEYWORD_MISMATCH"
    if "limit" in errmsg_lower or "频率" in errmsg:
        return "DINGTALK_RATE_LIMIT"
    return "SEND_FAILED"


class DingTalkDispatcher(BaseDispatcher):
    """钉钉群自定义机器人"""

    name = "dingtalk"

    def __init__(self, access_token: str, secret: str = ""):
        self.access_token = access_token.strip()
        self.secret = secret.strip()

    def _webhook_url(self) -> str:
        if self.secret:
            return _build_signed_url(self.access_token, self.secret)
        return f"{DINGTALK_WEBHOOK_URL}?access_token={self.access_token}"

    def send(self, title: str, content: str) -> DispatchResult:
        if not self.access_token:
            return DispatchResult(
                channel=self.name,
                success=False,
                error_code="DINGTALK_MISSING_TOKEN",
                raw_message="未配置 access_token",
            )

        text = f"## {title}\n\n{content}"
        encoded = text.encode("utf-8")
        if len(encoded) > MAX_TEXT_BYTES:
            text = encoded[: MAX_TEXT_BYTES - 20].decode("utf-8", errors="ignore") + "\n\n...(内容已截断)"

        payload = {
            "msgtype": "markdown",
            "markdown": {"title": title, "text": text},
        }

        try:
            resp = requests.post(self._webhook_url(), json=payload, timeout=15)
            resp.raise_for_status()
            result = resp.json()
            if result.get("errcode") != 0:
                errcode = result.get("errcode")
                errmsg = result.get("errmsg") or str(result)
                return DispatchResult(
                    channel=self.name,
                    success=False,
                    error_code=_map_error(errcode, errmsg),
                    raw_message=errmsg,
                )
            return DispatchResult(channel=self.name, success=True)
        except Exception as e:
            return DispatchResult(
                channel=self.name,
                success=False,
                error_code="SEND_FAILED",
                raw_message=str(e),
            )

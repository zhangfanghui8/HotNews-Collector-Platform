import requests

from .core.base import BaseDispatcher
from .push_guide import DispatchResult

WECOM_WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send"
MAX_CONTENT_BYTES = 4096

# 企业微信 errcode → 内部错误码
_ERROR_CODE_MAP = {
    93000: "WECOM_INVALID_KEY",
    93004: "WECOM_INVALID_KEY",
    45009: "WECOM_RATE_LIMIT",
    45033: "WECOM_RATE_LIMIT",
}


class WeComDispatcher(BaseDispatcher):
    """企业微信群机器人（推送到企业微信群，属微信生态）"""

    name = "wecom"

    def __init__(self, webhook_key: str):
        self.webhook_key = webhook_key.strip()

    def send(self, title: str, content: str) -> DispatchResult:
        if not self.webhook_key:
            return DispatchResult(
                channel=self.name,
                success=False,
                error_code="WECOM_MISSING_KEY",
                raw_message="未配置 webhook_key",
            )

        body = f"## {title}\n\n{content}"
        encoded = body.encode("utf-8")
        if len(encoded) > MAX_CONTENT_BYTES:
            body = encoded[: MAX_CONTENT_BYTES - 20].decode("utf-8", errors="ignore") + "\n\n...(内容已截断)"

        try:
            resp = requests.post(
                WECOM_WEBHOOK_URL,
                params={"key": self.webhook_key},
                json={"msgtype": "markdown", "markdown": {"content": body}},
                timeout=15,
            )
            resp.raise_for_status()
            result = resp.json()
            if result.get("errcode") != 0:
                errcode = result.get("errcode")
                error_code = _ERROR_CODE_MAP.get(errcode, "SEND_FAILED")
                msg = result.get("errmsg") or str(result)
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

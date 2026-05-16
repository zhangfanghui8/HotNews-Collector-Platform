from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config.yaml"
EXAMPLE_PATH = CONFIG_PATH.parent / "config.yaml.example"


@dataclass
class PushIssue:
    code: str
    title: str
    steps: List[str] = field(default_factory=list)


@dataclass
class PushReadiness:
    ready: bool
    issues: List[PushIssue] = field(default_factory=list)

    def format_message(self) -> str:
        if self.ready:
            return ""
        lines = [
            "",
            "=" * 50,
            "【推送未就绪】请按以下步骤完成配置后再试",
            "=" * 50,
        ]
        for i, issue in enumerate(self.issues, 1):
            lines.append(f"\n{i}. {issue.title}（{issue.code}）")
            for j, step in enumerate(issue.steps, 1):
                lines.append(f"   {j}) {step}")
        lines.extend(
            [
                "",
                "配置完成后执行：python main.py --push",
                f"配置模板参考：{EXAMPLE_PATH.name}",
                "=" * 50,
            ]
        )
        return "\n".join(lines)


def check_push_readiness(config: Dict[str, Any]) -> PushReadiness:
    issues: List[PushIssue] = []

    if not CONFIG_PATH.exists():
        issues.append(
            PushIssue(
                code="NO_CONFIG_FILE",
                title="尚未创建 config.yaml",
                steps=[
                    f"在项目根目录复制模板：copy {EXAMPLE_PATH.name} config.yaml",
                    "打开 config.yaml，选择一种推送方式并完成下方对应步骤",
                ],
            )
        )
        return PushReadiness(ready=False, issues=issues)

    channels = config.get("push", {}).get("channels", {})
    wecom = channels.get("wecom", {}) or {}
    pushplus = channels.get("pushplus", {}) or {}
    dingtalk = channels.get("dingtalk", {}) or {}

    wecom_key = (wecom.get("webhook_key") or "").strip()
    wecom_enabled = bool(wecom.get("enabled"))
    pushplus_token = (pushplus.get("token") or "").strip()
    pushplus_enabled = bool(pushplus.get("enabled"))
    dingtalk_token = (dingtalk.get("access_token") or "").strip()
    dingtalk_enabled = bool(dingtalk.get("enabled"))

    if wecom_key and not wecom_enabled:
        issues.append(
            PushIssue(
                code="WECOM_NOT_ENABLED",
                title="企业微信已填写 webhook_key，但未启用",
                steps=[
                    "编辑 config.yaml → push.channels.wecom.enabled 改为 true",
                    "webhook_key 填写企业微信群机器人 Webhook 地址中 key= 后面的字符串",
                ],
            )
        )

    if pushplus_token and not pushplus_enabled:
        issues.append(
            PushIssue(
                code="PUSHPLUS_NOT_ENABLED",
                title="PushPlus 已填写 token，但未启用",
                steps=[
                    "编辑 config.yaml → push.channels.pushplus.enabled 改为 true",
                    "token 从 https://www.pushplus.plus 登录后复制",
                    "微信关注「PushPlus 推送加」完成绑定",
                ],
            )
        )

    if wecom_enabled and not wecom_key:
        issues.append(
            PushIssue(
                code="WECOM_MISSING_KEY",
                title="企业微信已启用，但 webhook_key 为空",
                steps=[
                    "企业微信 → 目标群聊 → 群设置 → 群机器人 → 添加",
                    "复制 Webhook 地址里 key= 后面的内容，填入 webhook_key",
                ],
            )
        )

    if pushplus_enabled and not pushplus_token:
        issues.append(
            PushIssue(
                code="PUSHPLUS_MISSING_TOKEN",
                title="PushPlus 已启用，但 token 为空",
                steps=[
                    "打开 https://www.pushplus.plus 注册并登录",
                    "复制 Token 填入 config.yaml 的 push.channels.pushplus.token",
                    "微信关注「PushPlus 推送加」完成绑定",
                ],
            )
        )

    if dingtalk_token and not dingtalk_enabled:
        issues.append(
            PushIssue(
                code="DINGTALK_NOT_ENABLED",
                title="钉钉已填写 access_token，但未启用",
                steps=[
                    "编辑 config.yaml → push.channels.dingtalk.enabled 改为 true",
                    "access_token 为钉钉机器人 Webhook 地址中 access_token= 后面的字符串",
                ],
            )
        )

    if dingtalk_enabled and not dingtalk_token:
        issues.append(
            PushIssue(
                code="DINGTALK_MISSING_TOKEN",
                title="钉钉已启用，但 access_token 为空",
                steps=[
                    "钉钉 → 目标群 → 群设置 → 智能群助手 → 添加机器人 → 自定义",
                    "安全设置可选「加签」：若启用，需同时填写 secret",
                    "复制 Webhook 中 access_token= 后的内容填入 access_token",
                ],
            )
        )

    has_ready_channel = (
        (wecom_enabled and wecom_key)
        or (pushplus_enabled and pushplus_token)
        or (dingtalk_enabled and dingtalk_token)
    )

    if not has_ready_channel and not issues:
        issues.append(
            PushIssue(
                code="NO_CHANNEL_CONFIGURED",
                title="未启用任何可用的推送渠道",
                steps=[
                    "方式 A（企业微信群）：启用 wecom，填写 webhook_key",
                    "方式 B（个人微信）：启用 pushplus，填写 token 并完成微信绑定",
                    "方式 C（钉钉群）：启用 dingtalk，填写 access_token（及可选 secret）",
                    f"详见 {EXAMPLE_PATH.name} 中的注释说明",
                ],
            )
        )

    if issues:
        return PushReadiness(ready=False, issues=issues)

    return PushReadiness(ready=True)


# 发送失败后的排查指引（与 API 返回对应）
SEND_FAILURE_GUIDES: Dict[str, PushIssue] = {
    "PUSHPLUS_NOT_VERIFIED": PushIssue(
        code="PUSHPLUS_NOT_VERIFIED",
        title="PushPlus 账户未完成实名认证",
        steps=[
            "打开 https://verify.pushplus.plus 完成实名认证",
            "认证通过后重新执行：python main.py --push",
        ],
    ),
    "PUSHPLUS_INVALID_TOKEN": PushIssue(
        code="PUSHPLUS_INVALID_TOKEN",
        title="PushPlus Token 无效或已失效",
        steps=[
            "登录 https://www.pushplus.plus 重新复制 Token",
            "更新 config.yaml 中 push.channels.pushplus.token",
        ],
    ),
    "WECOM_INVALID_KEY": PushIssue(
        code="WECOM_INVALID_KEY",
        title="企业微信 Webhook Key 无效",
        steps=[
            "确认 key 为群机器人 Webhook 地址中 key= 后的完整字符串",
            "若机器人已删除，需在群里重新添加机器人并更新 webhook_key",
        ],
    ),
    "WECOM_RATE_LIMIT": PushIssue(
        code="WECOM_RATE_LIMIT",
        title="企业微信机器人发送频率超限",
        steps=["请等待 1 分钟后重试", "避免短时间内多次执行 --push"],
    ),
    "DINGTALK_INVALID_TOKEN": PushIssue(
        code="DINGTALK_INVALID_TOKEN",
        title="钉钉 access_token 无效",
        steps=[
            "确认 access_token 为机器人 Webhook 地址中 access_token= 后的完整字符串",
            "若机器人已删除，需在群里重新添加并更新 access_token",
        ],
    ),
    "DINGTALK_SIGN_ERROR": PushIssue(
        code="DINGTALK_SIGN_ERROR",
        title="钉钉加签 secret 错误或缺失",
        steps=[
            "若机器人安全设置为「加签」，将 SEC 开头的 secret 填入 config.yaml 的 secret 字段",
            "若未启用加签，将 secret 留空",
        ],
    ),
    "DINGTALK_KEYWORD_MISMATCH": PushIssue(
        code="DINGTALK_KEYWORD_MISMATCH",
        title="钉钉机器人关键词校验未通过",
        steps=[
            "在钉钉机器人安全设置中查看自定义关键词",
            "确保推送标题或正文包含该关键词（可在 format_push_markdown 标题中预留）",
        ],
    ),
    "DINGTALK_RATE_LIMIT": PushIssue(
        code="DINGTALK_RATE_LIMIT",
        title="钉钉机器人发送频率超限",
        steps=["请等待 1 分钟后重试", "每个机器人约 20 条/分钟"],
    ),
}


@dataclass
class DispatchResult:
    channel: str
    success: bool
    error_code: str = ""
    raw_message: str = ""

    def failure_guide(self) -> Optional[PushIssue]:
        if self.success:
            return None
        guide = SEND_FAILURE_GUIDES.get(self.error_code)
        if guide:
            return guide
        return PushIssue(
            code=self.error_code or "SEND_FAILED",
            title=f"{self.channel} 推送失败",
            steps=[
                f"错误信息：{self.raw_message or '未知'}",
                "检查网络与 config.yaml 配置后重试",
                f"仍失败可参考 {EXAMPLE_PATH.name} 或联系渠道官方文档",
            ],
        )


def format_send_results(results: List[DispatchResult]) -> str:
    failures = [r for r in results if not r.success]
    if not failures:
        return ""

    lines = [
        "",
        "=" * 50,
        "【推送失败】请根据原因排查",
        "=" * 50,
    ]
    for i, result in enumerate(failures, 1):
        guide = result.failure_guide()
        if not guide:
            continue
        lines.append(f"\n{i}. [{result.channel}] {guide.title}（{guide.code}）")
        for j, step in enumerate(guide.steps, 1):
            lines.append(f"   {j}) {step}")

    lines.append("\n修复后执行：python main.py --push")
    lines.append("=" * 50)
    return "\n".join(lines)

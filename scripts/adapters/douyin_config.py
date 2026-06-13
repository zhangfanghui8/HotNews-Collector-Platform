"""抖音采集配置：TikHub / 官方开放平台，支持 config.yaml 与环境变量。"""

import os
from pathlib import Path
from typing import Any, Dict, Literal, Optional

import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = ROOT / "config.yaml"

ProviderName = Literal["tikhub", "official"]


def load_douyin_config() -> Dict[str, Any]:
    """读取 douyin 配置块；密钥优先环境变量。"""
    raw: Dict[str, Any] = {}
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, encoding="utf-8") as f:
            raw = (yaml.safe_load(f) or {}).get("douyin") or {}

    provider = (os.getenv("DOUYIN_PROVIDER") or raw.get("provider") or "auto").strip().lower()
    tikhub = raw.get("tikhub") or {}
    official = raw.get("official") or {}

    tikhub_key = (os.getenv("TIKHUB_API_KEY") or tikhub.get("api_key") or "").strip()
    client_key = (os.getenv("DOUYIN_CLIENT_KEY") or official.get("client_key") or "").strip()
    client_secret = (
        os.getenv("DOUYIN_CLIENT_SECRET") or official.get("client_secret") or ""
    ).strip()

    return {
        "provider": provider,
        "tikhub_api_key": tikhub_key,
        "client_key": client_key,
        "client_secret": client_secret,
    }


def resolve_provider(cfg: Dict[str, Any]) -> Optional[ProviderName]:
    """
    解析实际使用的数据源。

    provider: auto | tikhub | official
    auto 时优先 TikHub（有 api_key），否则官方（有 client_key + client_secret）。
    """
    pref = cfg.get("provider", "auto")
    has_tikhub = bool(cfg.get("tikhub_api_key"))
    has_official = bool(cfg.get("client_key") and cfg.get("client_secret"))

    if pref == "tikhub":
        return "tikhub" if has_tikhub else None
    if pref == "official":
        return "official" if has_official else None
    if has_tikhub:
        return "tikhub"
    if has_official:
        return "official"
    return None

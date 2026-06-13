"""抖音热榜采集：支持 TikHub（第三方 API）与抖音开放平台（官方）。"""

import time
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import requests

from .core.article import Article
from .core.base_fetch import BaseFetch
from .douyin_config import load_douyin_config, resolve_provider

TIKHUB_BASE = "https://api.tikhub.io"
TIKHUB_HOT_URL = f"{TIKHUB_BASE}/api/v1/douyin/app/v3/fetch_hot_search_list"
TIKHUB_RISING_URL = f"{TIKHUB_BASE}/api/v1/douyin/web/fetch_real_time_rising_hot_list"

DOUYIN_TOKEN_URL = "https://open.douyin.com/oauth/client_token/"
DOUYIN_HOT_VIDEO_URL = "https://open.douyin.com/data/extern/billboard/hot_video/"
DOUYIN_HOT_SENTENCES_URL = "https://open.douyin.com/hotsearch/sentences/"

_HEADERS_JSON = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Content-Type": "application/json",
}

_token_cache: Dict[str, Any] = {"token": "", "expires_at": 0.0}
_warned_no_config_global = False


class DouyinFetcher(BaseFetch):
    """
    抖音热点采集。

    mode:
      - hot: 热点榜（TikHub 热搜榜 / 官方热门视频榜）
      - latest: 最新上升（TikHub 实时上升榜 / 官方实时热点词）

    数据源由 config.yaml 的 douyin 段或环境变量决定，用户自行配置密钥与付费。
    """

    def __init__(self, mode: str = "hot"):
        if mode not in ("hot", "latest"):
            raise ValueError(f"不支持的抖音采集模式: {mode}，请使用 hot 或 latest")

        self.mode = mode
        self._cfg = load_douyin_config()
        provider = resolve_provider(self._cfg)
        label = "热榜" if mode == "hot" else "上升"
        if provider == "tikhub":
            source = f"抖音·{label}·TikHub"
        elif provider == "official":
            source = f"抖音·{label}·官方" if mode == "hot" else "抖音·实时热点·官方"
        else:
            source = f"抖音·{label}"

        super().__init__(url="", source=source)
        self._provider = provider

    def fetch(self, limit: int = 10) -> List[Article]:
        provider = resolve_provider(self._cfg)
        if not provider:
            global _warned_no_config_global
            if not _warned_no_config_global:
                print(
                    "[抖音] 未配置数据源，已跳过。"
                    "请在 config.yaml 填写 douyin.tikhub.api_key 或 "
                    "douyin.official.client_key/client_secret；"
                    "或设置环境变量 TIKHUB_API_KEY / DOUYIN_CLIENT_KEY / DOUYIN_CLIENT_SECRET。"
                    "详见 config.yaml.example。"
                )
                _warned_no_config_global = True
            return []

        try:
            if provider == "tikhub":
                return (
                    self._fetch_tikhub_hot(limit)
                    if self.mode == "hot"
                    else self._fetch_tikhub_rising(limit)
                )
            return (
                self._fetch_official_hot_video(limit)
                if self.mode == "hot"
                else self._fetch_official_sentences(limit)
            )
        except Exception as e:
            print(f"[{self.source}] 获取失败: {e}")
            return []

    def _fetch_tikhub_hot(self, limit: int) -> List[Article]:
        payload = self._tikhub_get(
            TIKHUB_HOT_URL,
            params={"board_type": "0", "board_sub_type": ""},
        )
        items = _extract_list(payload)
        return _parse_tikhub_items(items, self.source, limit, title_keys=("word", "title", "sentence"))

    def _fetch_tikhub_rising(self, limit: int) -> List[Article]:
        payload = self._tikhub_get(
            TIKHUB_RISING_URL,
            params={"page": 1, "page_size": limit, "order": "rank"},
        )
        items = _extract_list(payload)
        return _parse_tikhub_items(items, self.source, limit, title_keys=("sentence", "word", "title"))

    def _tikhub_get(self, url: str, params: Optional[Dict[str, Any]] = None) -> Any:
        api_key = self._cfg["tikhub_api_key"]
        resp = requests.get(
            url,
            params=params,
            headers={**_HEADERS_JSON, "Authorization": f"Bearer {api_key}"},
            timeout=15,
        )
        resp.raise_for_status()
        body = resp.json()
        if isinstance(body, dict) and body.get("code") not in (None, 0, 200):
            raise RuntimeError(f"TikHub 返回异常: {body}")
        return _unwrap_payload(body)

    def _fetch_official_hot_video(self, limit: int) -> List[Article]:
        token = _get_official_token(self._cfg["client_key"], self._cfg["client_secret"])
        resp = requests.get(
            DOUYIN_HOT_VIDEO_URL,
            headers={**_HEADERS_JSON, "access-token": token},
            timeout=15,
        )
        resp.raise_for_status()
        data = _unwrap_official(resp.json())
        items = data.get("list") or []
        result: List[Article] = []
        for idx, item in enumerate(items[:limit], 1):
            title = (item.get("hot_words") or item.get("title") or "").strip()
            if not title:
                author = (item.get("author") or "").strip()
                title = f"{author} 热门视频" if author else ""
            if not title:
                continue
            result.append(
                Article(
                    title=title,
                    summary=f"播放 {item.get('play_count', '')} | 点赞 {item.get('digg_count', '')}".strip(),
                    source=self.source,
                    url=(item.get("share_url") or "").strip(),
                    publish_time="",
                    category="短视频",
                    rank=int(item.get("rank") or idx),
                    hot_score=int(item.get("hot_value") or 0),
                )
            )
        return result

    def _fetch_official_sentences(self, limit: int) -> List[Article]:
        token = _get_official_token(self._cfg["client_key"], self._cfg["client_secret"])
        resp = requests.get(
            DOUYIN_HOT_SENTENCES_URL,
            headers={**_HEADERS_JSON, "access-token": token},
            timeout=15,
        )
        resp.raise_for_status()
        data = _unwrap_official(resp.json())
        items = data.get("list") or []
        active_time = str(data.get("active_time") or "")
        result: List[Article] = []
        for idx, item in enumerate(items[:limit], 1):
            sentence = (item.get("sentence") or "").strip()
            if not sentence:
                continue
            result.append(
                Article(
                    title=sentence,
                    summary="抖音实时热点词",
                    source=self.source,
                    url=f"https://www.douyin.com/search/{quote(sentence)}",
                    publish_time=active_time,
                    category="短视频",
                    rank=idx,
                    hot_score=int(item.get("hot_level") or 0),
                )
            )
        return result


def _get_official_token(client_key: str, client_secret: str) -> str:
    now = time.time()
    if _token_cache["token"] and now < _token_cache["expires_at"]:
        return _token_cache["token"]

    resp = requests.post(
        DOUYIN_TOKEN_URL,
        json={
            "client_key": client_key,
            "client_secret": client_secret,
            "grant_type": "client_credential",
        },
        headers=_HEADERS_JSON,
        timeout=15,
    )
    resp.raise_for_status()
    data = (resp.json() or {}).get("data") or {}
    token = (data.get("access_token") or "").strip()
    if not token:
        raise RuntimeError(f"抖音 client_token 获取失败: {resp.json()}")

    expires_in = int(data.get("expires_in") or 7200)
    _token_cache["token"] = token
    _token_cache["expires_at"] = now + max(expires_in - 120, 60)
    return token


def _unwrap_official(payload: Dict[str, Any]) -> Dict[str, Any]:
    data = payload.get("data") or {}
    err = data.get("error_code")
    if err not in (None, 0, "0"):
        raise RuntimeError(f"抖音开放平台错误: {data.get('description') or payload}")
    return data


def _unwrap_payload(payload: Any) -> Any:
    if not isinstance(payload, dict):
        return payload
    inner = payload.get("data", payload)
    if isinstance(inner, dict) and "data" in inner:
        return inner.get("data")
    return inner


def _extract_list(payload: Any) -> List[Dict[str, Any]]:
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        return []
    for key in (
        "word_list",
        "words_list",
        "ob_list",
        "list",
        "data",
        "hot_list",
        "trending_list",
    ):
        val = payload.get(key)
        if isinstance(val, list):
            return val
    return []


def _parse_tikhub_items(
    items: List[Dict[str, Any]],
    source: str,
    limit: int,
    *,
    title_keys: tuple,
) -> List[Article]:
    result: List[Article] = []
    for idx, item in enumerate(items[:limit], 1):
        title = ""
        for key in title_keys:
            title = (item.get(key) or "").strip()
            if title:
                break
        if not title:
            continue

        hot_score = int(
            item.get("hot_value")
            or item.get("hot_score")
            or item.get("hot_level")
            or item.get("view_count")
            or 0
        )
        rank = int(item.get("position") or item.get("rank") or idx)
        url = (item.get("link") or item.get("url") or "").strip()
        if not url:
            url = f"https://www.douyin.com/search/{quote(title)}"

        result.append(
            Article(
                title=title,
                summary=(item.get("label") or item.get("word_type") or "").strip(),
                source=source,
                url=url,
                publish_time=str(item.get("event_time") or item.get("active_time") or ""),
                category="短视频",
                rank=rank,
                hot_score=hot_score or max(1000 - (idx - 1) * 10, 1),
            )
        )
    return result

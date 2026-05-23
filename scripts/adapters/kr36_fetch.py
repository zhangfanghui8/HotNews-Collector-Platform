import time
from typing import List

import requests

from .core.article import Article
from .core.base_fetch import BaseFetch

KR36_HOT_RANK_URL = "https://gateway.36kr.com/api/mis/nav/home/nav/rank/hot"

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Content-Type": "application/json",
    "Referer": "https://36kr.com/",
}


class Kr36HotFetcher(BaseFetch):
    """36氪人气热榜（gateway 接口）"""

    def __init__(self):
        super().__init__(url=KR36_HOT_RANK_URL, source="36氪·热榜")

    def fetch(self, limit: int = 10) -> List[Article]:
        try:
            resp = requests.post(
                self.url,
                json={
                    "partner_id": "wap",
                    "param": {"siteId": 1, "platformId": 2},
                    "timestamp": int(time.time()),
                },
                headers=_HEADERS,
                timeout=10,
            )
            resp.raise_for_status()
            payload = resp.json()
            hot_list = (payload.get("data") or {}).get("hotRankList") or []
            if not hot_list and payload.get("code") not in (None, 0):
                print(f"[{self.source}] API 异常: {payload}")
                return []

            result: List[Article] = []
            for idx, item in enumerate(hot_list[:limit], 1):
                material = item.get("templateMaterial") or {}
                title = (material.get("widgetTitle") or "").strip()
                if not title:
                    continue

                item_id = item.get("itemId", "")
                stat = item.get("stat") or material.get("stat") or {}
                hot_score = int(stat.get("hot") or stat.get("read") or (limit - idx + 1) * 100)

                result.append(
                    Article(
                        title=title,
                        summary=(material.get("widgetSubTitle") or "").strip(),
                        source=self.source,
                        url=f"https://36kr.com/p/{item_id}" if item_id else "",
                        publish_time=str(item.get("publishTime") or ""),
                        category="科技",
                        rank=idx,
                        hot_score=hot_score,
                    )
                )
            return result

        except Exception as e:
            print(f"[{self.source}] 获取失败: {e}")
            return []

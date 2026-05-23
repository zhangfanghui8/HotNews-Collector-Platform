from typing import List

import requests

from .core.article import Article
from .core.base_fetch import BaseFetch

INFOQ_TOPIC_INFO_URL = "https://www.infoq.cn/public/v1/topic/getInfo"
INFOQ_ARTICLE_LIST_URL = "https://www.infoq.cn/public/v1/article/getList"

# 话题 alias → 展示名（getInfo 会返回正式名称）
INFOQ_TOPIC_AI = "AI"
INFOQ_TOPIC_AI_ID = 31

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Content-Type": "application/json",
}


class InfoQFetcher(BaseFetch):
    """InfoQ 中文站话题文章列表（按发布时间，非热榜）"""

    def __init__(self, topic_alias: str = INFOQ_TOPIC_AI, topic_id: int = INFOQ_TOPIC_AI_ID):
        self.topic_alias = topic_alias
        self.topic_id = topic_id
        self._topic_name = "AI"
        super().__init__(url=INFOQ_ARTICLE_LIST_URL, source="InfoQ·AI")

    def _resolve_topic(self) -> bool:
        try:
            resp = requests.post(
                INFOQ_TOPIC_INFO_URL,
                json={"alias": self.topic_alias},
                headers={
                    **_HEADERS,
                    "Referer": f"https://www.infoq.cn/topic/{self.topic_alias}",
                },
                timeout=10,
            )
            resp.raise_for_status()
            data = (resp.json().get("data") or {})
            if data.get("id"):
                self.topic_id = int(data["id"])
            if data.get("name"):
                self._topic_name = data["name"]
                self.source = f"InfoQ·{self._topic_name}"
            return True
        except Exception as e:
            print(f"[InfoQ] 话题解析失败，使用默认 id={self.topic_id}: {e}")
            return False

    def fetch(self, limit: int = 10) -> List[Article]:
        self._resolve_topic()
        referer = f"https://www.infoq.cn/topic/{self.topic_id}"

        try:
            resp = requests.post(
                self.url,
                json={
                    "id": self.topic_id,
                    "ptype": 0,
                    "size": limit,
                    "type": 0,
                },
                headers={**_HEADERS, "Referer": referer},
                timeout=10,
            )
            resp.raise_for_status()
            payload = resp.json()
            if payload.get("code") != 0:
                print(f"[{self.source}] API 异常: {payload}")
                return []

            rows = payload.get("data") or []
            result: List[Article] = []
            for idx, row in enumerate(rows[:limit], 1):
                title = (row.get("article_title") or "").strip()
                if not title:
                    continue

                uuid = (row.get("uuid") or "").strip()
                summary = (row.get("article_summary") or "").strip()
                score = int(row.get("score") or row.get("publish_time") or 0)

                result.append(
                    Article(
                        title=title,
                        summary=summary,
                        source=self.source,
                        url=f"https://www.infoq.cn/article/{uuid}" if uuid else "",
                        publish_time=str(row.get("publish_time") or row.get("ctime") or ""),
                        category="人工智能",
                        rank=idx,
                        hot_score=score if score else max(1000 - (idx - 1) * 10, 1),
                    )
                )
            return result

        except Exception as e:
            print(f"[{self.source}] 获取失败: {e}")
            return []

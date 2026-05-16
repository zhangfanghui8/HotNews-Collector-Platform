import html
import re
from typing import List

import requests

from .core.article import Article
from .core.base_fetch import BaseFetch

# 量子位基于 WordPress，公开 REST API 按时间返回最新文章（非热榜接口）
QBITAI_POSTS_URL = "https://www.qbitai.com/wp-json/wp/v2/posts"

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.qbitai.com/",
}


def _strip_html(text: str) -> str:
    if not text:
        return ""
    text = html.unescape(text)
    return re.sub(r"<[^>]+>", "", text).strip()


class QbitaiFetcher(BaseFetch):
    """量子位最新资讯（WordPress REST API，按发布时间倒序）"""

    def __init__(self):
        super().__init__(url=QBITAI_POSTS_URL, source="量子位")

    def fetch(self, limit: int = 10) -> List[Article]:
        try:
            resp = requests.get(
                self.url,
                params={
                    "per_page": limit,
                    "orderby": "date",
                    "order": "desc",
                    "_fields": "id,date,link,title,excerpt",
                },
                headers=_HEADERS,
                timeout=10,
            )
            resp.raise_for_status()
            posts = resp.json()
            if not isinstance(posts, list):
                print(f"量子位 API 响应异常: {posts}")
                return []

            result: List[Article] = []
            for idx, post in enumerate(posts[:limit], 1):
                title = _strip_html((post.get("title") or {}).get("rendered", ""))
                if not title:
                    continue

                summary = _strip_html((post.get("excerpt") or {}).get("rendered", ""))
                url = (post.get("link") or "").strip()
                publish_time = post.get("date", "")
                # 无官方热度字段，用排名生成递减分值便于多源排序
                hot_score = max(1000 - (idx - 1) * 10, 1)

                result.append(
                    Article(
                        title=title,
                        summary=summary,
                        source=self.source,
                        url=url,
                        publish_time=publish_time,
                        category="人工智能",
                        rank=idx,
                        hot_score=hot_score,
                    )
                )

            return result

        except Exception as e:
            print(f"量子位资讯获取失败: {e}")
            return []

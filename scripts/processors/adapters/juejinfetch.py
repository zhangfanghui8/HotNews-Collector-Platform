import requests
from typing import List

from .core.article import Article
from .core.base_fetch import BaseFetch

# 官方热榜：GET content_api/v1/content/article_rank
# category_id 与首页分类一致（见 tag_api/v1/query_category_briefs）
JUEJIN_ARTICLE_RANK_URL = "https://api.juejin.cn/content_api/v1/content/article_rank"
JUEJIN_CATEGORY_GENERAL = "1"  # 综合热榜
JUEJIN_CATEGORY_AI = "6809637773935378440"  # 人工智能


class JuejinFetcher(BaseFetch):
    def __init__(self, category_id: str = JUEJIN_CATEGORY_AI):
        self.category_id = category_id
        if category_id == JUEJIN_CATEGORY_AI:
            source, self._article_category = "掘金·人工智能", "人工智能"
        elif category_id == JUEJIN_CATEGORY_GENERAL:
            source, self._article_category = "掘金·综合", "综合"
        else:
            source, self._article_category = "掘金", ""
        super().__init__(url=JUEJIN_ARTICLE_RANK_URL, source=source)

    def fetch(self, limit=10) -> List[Article]:
        try:
            # 请求头模拟浏览器
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://juejin.cn/"
            }

            resp = requests.get(
                self.url,
                params={"category_id": self.category_id, "type": "hot"},
                headers=headers,
                timeout=10,
            )
            resp.raise_for_status()
            payload = resp.json()
            if payload.get("err_msg") != "success":
                print(f"掘金热点 API 异常: {payload}")
                return []

            result: List[Article] = []
            hot_list = payload.get("data") or []

            for idx, item in enumerate(hot_list[:limit], 1):
                content = item.get("content") or {}
                counter = item.get("content_counter") or {}

                title = (content.get("title") or "").strip()
                summary = (content.get("brief") or "").strip()
                content_id = content.get("content_id", "")
                url = f"https://juejin.cn/post/{content_id}" if content_id else ""
                ctime = str(content.get("ctime", ""))
                hot_score = int(counter.get("hot_rank") or 0)

                result.append(
                    Article(
                        title=title,
                        summary=summary,
                        source=self.source,
                        url=url,
                        publish_time=ctime,
                        category=self._article_category or "科技",
                        rank=idx,
                        hot_score=hot_score,
                    )
                )

            return result

        except Exception as e:
            print(f"掘金热点获取失败: {e}")
            return []

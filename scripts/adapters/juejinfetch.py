import requests
from typing import List

from .core.article import Article
from .core.base_fetch import BaseFetch

# 热榜：GET content_api/v1/content/article_rank?type=hot
JUEJIN_ARTICLE_RANK_URL = "https://api.juejin.cn/content_api/v1/content/article_rank"
# 分类最新：POST recommend_api/v1/article/recommend_cate_feed（sort_type=300）
JUEJIN_RECOMMEND_FEED_URL = "https://api.juejin.cn/recommend_api/v1/article/recommend_cate_feed"

JUEJIN_CATEGORY_GENERAL = "1"
JUEJIN_CATEGORY_AI = "6809637773935378440"
JUEJIN_SORT_TYPE_LATEST = 300

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://juejin.cn/",
}


class JuejinFetcher(BaseFetch):
    def __init__(self, category_id: str = JUEJIN_CATEGORY_AI, mode: str = "hot"):
        self.category_id = category_id
        self.mode = mode
        base_label, self._article_category = self._resolve_category(category_id)

        if mode == "hot":
            source = f"{base_label}·热榜"
            url = JUEJIN_ARTICLE_RANK_URL
        elif mode == "latest":
            source = f"{base_label}·最新"
            url = JUEJIN_RECOMMEND_FEED_URL
        else:
            raise ValueError(f"不支持的掘金采集模式: {mode}，请使用 hot 或 latest")

        super().__init__(url=url, source=source)

    @staticmethod
    def _resolve_category(category_id: str):
        if category_id == JUEJIN_CATEGORY_AI:
            return "掘金·人工智能", "人工智能"
        if category_id == JUEJIN_CATEGORY_GENERAL:
            return "掘金·综合", "综合"
        return "掘金", "科技"

    def fetch(self, limit: int = 10) -> List[Article]:
        if self.mode == "hot":
            return self._fetch_hot(limit)
        return self._fetch_latest(limit)

    def _fetch_hot(self, limit: int) -> List[Article]:
        try:
            resp = requests.get(
                self.url,
                params={"category_id": self.category_id, "type": "hot"},
                headers=_HEADERS,
                timeout=10,
            )
            resp.raise_for_status()
            payload = resp.json()
            if payload.get("err_msg") != "success":
                print(f"[{self.source}] API 异常: {payload}")
                return []

            result: List[Article] = []
            for idx, item in enumerate((payload.get("data") or [])[:limit], 1):
                content = item.get("content") or {}
                counter = item.get("content_counter") or {}

                title = (content.get("title") or "").strip()
                if not title:
                    continue

                content_id = content.get("content_id", "")
                result.append(
                    Article(
                        title=title,
                        summary=(content.get("brief") or "").strip(),
                        source=self.source,
                        url=f"https://juejin.cn/post/{content_id}" if content_id else "",
                        publish_time=str(content.get("ctime", "")),
                        category=self._article_category,
                        rank=idx,
                        hot_score=int(counter.get("hot_rank") or 0),
                    )
                )
            return result

        except Exception as e:
            print(f"[{self.source}] 获取失败: {e}")
            return []

    def _fetch_latest(self, limit: int) -> List[Article]:
        try:
            resp = requests.post(
                self.url,
                json={
                    "cate_id": self.category_id,
                    "cursor": "0",
                    "limit": limit,
                    "sort_type": JUEJIN_SORT_TYPE_LATEST,
                },
                headers=_HEADERS,
                timeout=10,
            )
            resp.raise_for_status()
            payload = resp.json()
            if payload.get("err_msg") != "success":
                print(f"[{self.source}] API 异常: {payload}")
                return []

            result: List[Article] = []
            for idx, item in enumerate((payload.get("data") or [])[:limit], 1):
                info = item.get("article_info") or {}
                title = (info.get("title") or "").strip()
                if not title:
                    continue

                article_id = info.get("article_id", "")
                ctime = int(info.get("ctime") or 0)
                result.append(
                    Article(
                        title=title,
                        summary=(info.get("brief_content") or "").strip(),
                        source=self.source,
                        url=f"https://juejin.cn/post/{article_id}" if article_id else "",
                        publish_time=str(ctime),
                        category=self._article_category,
                        rank=idx,
                        # 最新榜无 hot_rank，用发布时间作排序参考
                        hot_score=ctime,
                    )
                )
            return result

        except Exception as e:
            print(f"[{self.source}] 获取失败: {e}")
            return []

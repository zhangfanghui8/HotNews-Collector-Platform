class Article:
    """文章模型"""

    def __init__(
        self,
        title: str,
        url: str,
        source: str,
        publish_time: str = "",
        summary: str = "",
        category: str = "",
        rank: int = 0,
        hot_score: int = 0,
    ):
        self.title = title
        self.url = url
        self.source = source
        self.publish_time = publish_time
        self.summary = summary
        self.category = category
        self.rank = rank
        self.hot_score = hot_score

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "url": self.url,
            "source": self.source,
            "publish_time": self.publish_time,
            "summary": self.summary,
            "category": self.category,
            "rank": self.rank,
            "hot_score": self.hot_score,
        }

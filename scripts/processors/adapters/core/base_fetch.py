from abc import ABC, abstractmethod
from typing import List

from .article import Article


class BaseFetch(ABC):
    """基础抓取器"""

    def __init__(self, url: str, source: str):
        self.url = url
        self.source = source

    @abstractmethod
    def fetch(self, limit: int = 10) -> List[Article]:
        """抓取热点，返回统一 Article 结构"""
        pass


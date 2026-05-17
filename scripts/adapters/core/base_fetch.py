from abc import ABC, abstractmethod
from typing import List

from .article import Article


class BaseFetch(ABC):
    """基础抓取器。

    约定：一平台一文件；最热/最新用子类 ``mode`` 区分，在 main.ADAPTERS 中按维度注册。
    详见项目根目录 prompt.md
    """

    def __init__(self, url: str, source: str):
        self.url = url
        self.source = source

    @abstractmethod
    def fetch(self, limit: int = 10) -> List[Article]:
        """抓取热点，返回统一 Article 结构"""
        pass


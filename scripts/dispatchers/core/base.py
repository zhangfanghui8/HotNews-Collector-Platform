from abc import ABC, abstractmethod

from ..push_guide import DispatchResult


class BaseDispatcher(ABC):
    """消息推送基类"""

    name: str = "base"

    @abstractmethod
    def send(self, title: str, content: str) -> DispatchResult:
        """发送消息，返回结构化结果"""
        pass

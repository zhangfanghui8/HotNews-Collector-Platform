import argparse
import json
from dataclasses import dataclass
from datetime import datetime
from typing import List, Literal

from scripts.adapters.core.base_fetch import BaseFetch
from scripts.adapters.douyin_fetch import DouyinFetcher
from scripts.adapters.infoq_fetch import InfoQFetcher
from scripts.adapters.juejinfetch import JuejinFetcher
from scripts.adapters.kr36_fetch import Kr36HotFetcher
from scripts.adapters.qbitai_fetch import QbitaiFetcher
from scripts.dispatchers import build_dispatchers, dispatch_all
from scripts.dispatchers.core.config import load_config
from scripts.dispatchers.push_guide import (
    check_push_readiness,
    format_send_results,
)
from scripts.format_report import format_markdown, format_push_markdown
from scripts.post_process import process_articles

Dimension = Literal["hot", "latest"]

DIMENSION_CHOICES = ("all", "hot", "latest")
DIMENSION_LABELS = {"all": "全部维度", "hot": "最热", "latest": "最新"}


@dataclass(frozen=True)
class AdapterEntry:
    """注册表：每个实例对应一个「平台 × 维度」采集能力。"""

    adapter: BaseFetch
    dimension: Dimension
    platform: str


ADAPTERS: List[AdapterEntry] = [
    AdapterEntry(JuejinFetcher(mode="hot"), "hot", "juejin"),
    AdapterEntry(JuejinFetcher(mode="latest"), "latest", "juejin"),
    AdapterEntry(QbitaiFetcher(), "latest", "qbitai"),
    AdapterEntry(Kr36HotFetcher(), "hot", "kr36"),
    AdapterEntry(InfoQFetcher(), "latest", "infoq"),
    AdapterEntry(DouyinFetcher(mode="hot"), "hot", "douyin"),
    AdapterEntry(DouyinFetcher(mode="latest"), "latest", "douyin"),
]

DEFAULT_LIMIT = 10


def collect(limit: int = DEFAULT_LIMIT, dimension: str = "all"):
    articles = []
    for entry in ADAPTERS:
        if dimension != "all" and entry.dimension != dimension:
            continue
        articles.extend(entry.adapter.fetch(limit=limit))
    return articles


def push_report(articles, grouped, config) -> None:
    readiness = check_push_readiness(config)
    if not readiness.ready:
        print(readiness.format_message())
        return

    title = f"AI技术热点 {datetime.now().strftime('%Y-%m-%d')}"
    content = format_push_markdown(articles, grouped=grouped)
    results = dispatch_all(title, content, config)

    any_success = False
    for result in results:
        status = "成功" if result.success else "失败"
        print(f"推送 [{result.channel}]: {status}")
        any_success = any_success or result.success

    failure_guide = format_send_results(results)
    if failure_guide:
        print(failure_guide)

    if any_success:
        print("\n✓ 至少一个渠道推送成功，请在微信 / 企业微信 / 钉钉中查收。")


def main():
    parser = argparse.ArgumentParser(description="采集热点并生成报告")
    parser.add_argument(
        "--push",
        action="store_true",
        help="推送到 config.yaml 中已启用的微信渠道",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        metavar="N",
        help=f"每个采集维度拉取条数（默认 {DEFAULT_LIMIT}）",
    )
    parser.add_argument(
        "--dimension",
        choices=DIMENSION_CHOICES,
        default="all",
        metavar="MODE",
        help="采集维度：all=全部，hot=各渠道最热能力，latest=各渠道最新能力（默认 all）",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="输出 JSON（含 stats、分源 articles），供 Agent 筛选",
    )
    args = parser.parse_args()

    if args.limit < 1:
        parser.error("--limit 须为正整数")

    config = load_config()
    raw_articles = collect(limit=args.limit, dimension=args.dimension)
    articles, stats, grouped = process_articles(raw_articles)

    if args.json:
        payload = {
            "meta": {
                "dimension": args.dimension,
                "dimension_label": DIMENSION_LABELS[args.dimension],
                "limit": args.limit,
            },
            "stats": stats.to_dict(),
            "sources": {
                source: [a.to_dict() for a in items]
                for source, items in grouped.items()
            },
            "articles": [a.to_dict() for a in articles],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(
            format_markdown(
                articles,
                grouped=grouped,
                stats=stats,
                dimension=args.dimension,
            )
        )

    push_enabled = args.push or config.get("push", {}).get("enabled", False)
    if push_enabled:
        push_report(articles, grouped, config)


if __name__ == "__main__":
    main()

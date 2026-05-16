import argparse
from datetime import datetime

from scripts.adapters.juejinfetch import JuejinFetcher
from scripts.adapters.qbitai_fetch import QbitaiFetcher
from scripts.dispatchers import build_dispatchers, dispatch_all
from scripts.dispatchers.core.config import load_config
from scripts.dispatchers.push_guide import (
    check_push_readiness,
    format_send_results,
)
from scripts.format_report import format_markdown, format_push_markdown

ADAPTERS = [
    JuejinFetcher(mode="hot"),
    JuejinFetcher(mode="latest"),
    QbitaiFetcher(),
]

DEFAULT_LIMIT = 10


def collect(limit: int = DEFAULT_LIMIT):
    articles = []
    for adapter in ADAPTERS:
        articles.extend(adapter.fetch(limit=limit))
    return articles


def push_report(articles, config) -> None:
    readiness = check_push_readiness(config)
    if not readiness.ready:
        print(readiness.format_message())
        return

    title = f"AI技术热点 {datetime.now().strftime('%Y-%m-%d')}"
    content = format_push_markdown(articles)
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
    args = parser.parse_args()

    config = load_config()
    articles = collect(limit=DEFAULT_LIMIT)
    print(format_markdown(articles))

    push_enabled = args.push or config.get("push", {}).get("enabled", False)
    if push_enabled:
        push_report(articles, config)


if __name__ == "__main__":
    main()

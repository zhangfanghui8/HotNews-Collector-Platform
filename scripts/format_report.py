from datetime import datetime
from typing import List

from scripts.adapters.core.article import Article


def _format_item(index: int, article: Article) -> List[str]:
    summary = article.summary.strip() or "（暂无摘要，可结合标题理解）"
    return [
        f"{index}. **{article.title}**  ",
        f"   摘要：{summary}  ",
        f"   来源：{article.source} | 热度：{article.hot_score} | [链接]({article.url})",
        "",
    ]


def format_markdown(articles: List[Article], *, top_headlines: int = 5) -> str:
    if not articles:
        return "未采集到热点数据，请检查网络连接或项目适配器配置。"

    sorted_articles = sorted(articles, key=lambda a: a.hot_score, reverse=True)
    now = datetime.now()
    date_str = now.strftime("%Y年%m月%d日")
    time_str = now.strftime("%Y-%m-%d %H:%M:%S")
    sources = sorted({a.source for a in articles})

    lines = [
        f"# 📅 国内 AI 与技术热点资讯汇总（{date_str}）",
        "",
        "## 📊 今日概览",
        f"- 信息来源：{'、'.join(sources)}（共 {len(sources)} 个平台，{len(articles)} 条）",
        "- 主要热点主题：（请根据下方列表提炼 3-5 个关键词）",
        "",
        f"## 🔥 头条热点（Top {min(top_headlines, len(sorted_articles))}）",
    ]

    for i, article in enumerate(sorted_articles[:top_headlines], 1):
        lines.extend(_format_item(i, article))

    lines.extend(["## 📌 分类热点", "", "### 科技与AI"])

    rest = sorted_articles[top_headlines:15]
    if rest:
        for article in rest:
            snippet = (article.summary.strip() or article.title)[:100]
            lines.append(
                f"- **{article.title}** — {snippet}… "
                f"[{article.source}]({article.url}) | 热度：{article.hot_score}"
            )
    else:
        lines.append("- （其余条目已列入头条热点）")

    lines.extend(
        [
            "",
            "## 💡 总结与洞察",
            "- 今日最值得关注的趋势：（请根据以上热点提炼 1-2 句）",
            "- 建议关注方向：（请结合用户关心的领域给出建议）",
            "",
            f"**数据更新时间**：{time_str}",
            "**提示**：本汇总为 AI 辅助生成，仅供参考。如需深入某条新闻详情，请告诉我具体标题。",
        ]
    )

    return "\n".join(lines)


def format_push_markdown(articles: List[Article], *, top_headlines: int = 5) -> str:
    """生成适合微信推送的精简 Markdown（控制长度，避免超限）"""
    if not articles:
        return "未采集到热点数据。"

    sorted_articles = sorted(articles, key=lambda a: a.hot_score, reverse=True)
    sources = sorted({a.source for a in articles})

    lines = [
        f"> 来源：{'、'.join(sources)} | 共 {len(articles)} 条",
        "",
    ]

    for i, article in enumerate(sorted_articles[:top_headlines], 1):
        lines.append(f"### {i}. {article.title}")
        lines.append(f"热度 **{article.hot_score}** | [查看]({article.url})")
        lines.append("")

    rest = sorted_articles[top_headlines:10]
    if rest:
        lines.append("**更多热点**")
        for article in rest:
            lines.append(f"- [{article.title}]({article.url})")

    return "\n".join(lines)

from datetime import datetime
from typing import Dict, List, Optional

from scripts.adapters.core.article import Article
from scripts.post_process import ProcessStats, pick_balanced_samples


def _format_item(index: int, article: Article) -> List[str]:
    summary = article.summary.strip() or "（暂无摘要，可结合标题理解）"
    rank_part = f"排名 {article.rank} | " if article.rank > 0 else ""
    score_part = f"热度 {article.hot_score} | " if article.hot_score > 0 else ""
    return [
        f"{index}. **{article.title}**  ",
        f"   摘要：{summary}  ",
        f"   {rank_part}{score_part}[链接]({article.url})",
        "",
    ]


def format_markdown(
    articles: List[Article],
    *,
    grouped: Optional[Dict[str, List[Article]]] = None,
    stats: Optional[ProcessStats] = None,
) -> str:
    if not articles:
        return "未采集到热点数据，请检查网络连接或项目适配器配置。"

    now = datetime.now()
    date_str = now.strftime("%Y年%m月%d日")
    time_str = now.strftime("%Y-%m-%d %H:%M:%S")
    sources = sorted({a.source for a in articles})

    if stats:
        dedupe_note = (
            f"采集 {stats.raw_count} 条 → 规则层去重后 {stats.final_count} 条"
            f"（URL 重复 {stats.url_duplicates_removed}，标题合并 {stats.title_merges}）"
        )
    else:
        dedupe_note = f"共 {len(articles)} 条"

    lines = [
        f"# 📅 国内 AI 与技术热点资讯汇总（{date_str}）",
        "",
        "## 📊 今日概览",
        f"- 数据处理：{dedupe_note}",
        f"- 信息来源：{'、'.join(sources)}（{len(sources)} 个维度）",
        "- 主要热点主题：（请 Agent 根据下方列表提炼 3-5 个关键词）",
        "",
        "## 🔍 各源速览（每源 Top 1，轮流采样，供 Agent 快速浏览）",
    ]

    if grouped:
        for article in pick_balanced_samples(grouped, max_items=len(sources)):
            lines.append(
                f"- **{article.title}** — {article.source} | [链接]({article.url})"
            )
    else:
        lines.append("- （无分源数据）")

    lines.extend(["", "## 📰 分源列表（同源内按 rank / 热度排序，勿跨源比 hot_score）", ""])

    if grouped:
        for source, items in grouped.items():
            lines.append(f"### {source}（{len(items)} 条）")
            lines.append("")
            for i, article in enumerate(items, 1):
                lines.extend(_format_item(i, article))
    else:
        for source in sources:
            source_items = [a for a in articles if a.source == source]
            lines.append(f"### {source}（{len(source_items)} 条）")
            lines.append("")
            for i, article in enumerate(source_items, 1):
                lines.extend(_format_item(i, article))

    lines.extend(
        [
            "## 💡 总结与洞察",
            "- 今日最值得关注的趋势：（请 Agent 根据以上热点提炼 1-2 句）",
            "- 建议关注方向：（请 Agent 结合用户关心的领域给出建议）",
            "",
            f"**数据更新时间**：{time_str}",
            "**提示**：规则层已做 URL/标题去重与分源排序；最终精选条数与主题筛选由 Agent 按用户诉求完成。",
        ]
    )

    return "\n".join(lines)


def format_push_markdown(
    articles: List[Article],
    *,
    grouped: Optional[Dict[str, List[Article]]] = None,
    top_headlines: int = 5,
) -> str:
    """生成适合微信推送的精简 Markdown（各源轮流采样，避免单源霸榜）"""
    if not articles:
        return "未采集到热点数据。"

    sources = sorted({a.source for a in articles})
    if grouped:
        headlines = pick_balanced_samples(grouped, max_items=top_headlines)
    else:
        headlines = articles[:top_headlines]

    headline_ids = {id(a) for a in headlines}

    lines = [
        f"> 来源：{'、'.join(sources)} | 共 {len(articles)} 条（已规则层去重）",
        "",
    ]

    for i, article in enumerate(headlines, 1):
        lines.append(f"### {i}. {article.title}")
        lines.append(f"{article.source} | [查看]({article.url})")
        lines.append("")

    rest = [a for a in articles if id(a) not in headline_ids][:5]
    if rest:
        lines.append("**更多热点**")
        for article in rest:
            lines.append(f"- [{article.title}]({article.url})")

    return "\n".join(lines)

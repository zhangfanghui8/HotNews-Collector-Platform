"""采集后规则层：分源排序、URL 去重、标题相似合并。"""

import re
from dataclasses import dataclass
from typing import Dict, List, Tuple
from urllib.parse import urlparse, urlunparse

from scripts.adapters.core.article import Article

# 标题字符 bigram Jaccard 超过此阈值视为同题（跨源合并）
_TITLE_SIMILARITY_THRESHOLD = 0.72


@dataclass
class ProcessStats:
    """后处理统计，便于报告概览与 JSON 输出。"""

    raw_count: int = 0
    final_count: int = 0
    url_duplicates_removed: int = 0
    title_merges: int = 0

    def to_dict(self) -> dict:
        return {
            "raw_count": self.raw_count,
            "final_count": self.final_count,
            "url_duplicates_removed": self.url_duplicates_removed,
            "title_merges": self.title_merges,
        }


def normalize_url(url: str) -> str:
    """URL 规范化，用于完全相同链接去重。"""
    url = (url or "").strip()
    if not url:
        return ""
    parsed = urlparse(url)
    path = parsed.path.rstrip("/") or "/"
    # 忽略 fragment；query 保留（部分平台链接含 id）
    return urlunparse((parsed.scheme, parsed.netloc.lower(), path, "", parsed.query, ""))


def _normalize_title(title: str) -> str:
    text = (title or "").strip().lower()
    text = re.sub(r"[\s\W_]+", "", text, flags=re.UNICODE)
    return text


def _char_bigrams(text: str) -> set:
    if len(text) < 2:
        return {text} if text else set()
    return {text[i : i + 2] for i in range(len(text) - 1)}


def title_similarity(a: str, b: str) -> float:
    """字符 bigram Jaccard，适用于中文标题近似判断。"""
    na, nb = _normalize_title(a), _normalize_title(b)
    if not na or not nb:
        return 0.0
    if na == nb or na in nb or nb in na:
        return 1.0
    ga, gb = _char_bigrams(na), _char_bigrams(nb)
    if not ga or not gb:
        return 0.0
    inter = len(ga & gb)
    union = len(ga | gb)
    return inter / union if union else 0.0


def _sort_key(article: Article) -> tuple:
    """同源内：有 rank 则按榜单序，否则按 hot_score 降序。"""
    if article.rank > 0:
        return (0, article.rank)
    return (1, -article.hot_score)


def group_by_source(articles: List[Article]) -> Dict[str, List[Article]]:
    grouped: Dict[str, List[Article]] = {}
    for article in articles:
        grouped.setdefault(article.source, []).append(article)
    for source in grouped:
        grouped[source] = sorted(grouped[source], key=_sort_key)
    return dict(sorted(grouped.items(), key=lambda x: x[0]))


def _merge_sources(existing: str, incoming: str) -> str:
    parts = [p.strip() for p in existing.split("|")]
    for part in incoming.split("|"):
        part = part.strip()
        if part and part not in parts:
            parts.append(part)
    return " | ".join(parts)


def _pick_primary(keep: Article, other: Article) -> Article:
    """合并时保留摘要更完整、榜单更靠前的一条为主记录。"""
    if len(other.summary.strip()) > len(keep.summary.strip()):
        keep.summary = other.summary
    if other.rank > 0 and (keep.rank == 0 or other.rank < keep.rank):
        keep.rank = other.rank
    if other.hot_score > keep.hot_score:
        keep.hot_score = other.hot_score
    keep.source = _merge_sources(keep.source, other.source)
    return keep


def dedupe_by_url(articles: List[Article]) -> Tuple[List[Article], int]:
    seen: Dict[str, Article] = {}
    no_url: List[Article] = []
    removed = 0
    for article in articles:
        key = normalize_url(article.url)
        if not key:
            no_url.append(article)
            continue
        if key in seen:
            seen[key] = _pick_primary(seen[key], article)
            removed += 1
        else:
            seen[key] = article
    return list(seen.values()) + no_url, removed


def dedupe_by_title(articles: List[Article]) -> Tuple[List[Article], int]:
    merged: List[Article] = []
    merges = 0
    for article in articles:
        matched_idx = None
        for idx, existing in enumerate(merged):
            if title_similarity(existing.title, article.title) >= _TITLE_SIMILARITY_THRESHOLD:
                matched_idx = idx
                break
        if matched_idx is None:
            merged.append(article)
        else:
            merged[matched_idx] = _pick_primary(merged[matched_idx], article)
            merges += 1
    return merged, merges


def process_articles(articles: List[Article]) -> Tuple[List[Article], ProcessStats, Dict[str, List[Article]]]:
    """
    规则层流水线：分源排序 → URL 去重 → 标题相似合并 → 再分源。

    不做跨源 hot_score 全局排序；各源热度仅在源内比较。
    """
    stats = ProcessStats(raw_count=len(articles))
    if not articles:
        stats.final_count = 0
        return [], stats, {}

    grouped = group_by_source(articles)
    flat = [a for items in grouped.values() for a in items]

    flat, url_removed = dedupe_by_url(flat)
    stats.url_duplicates_removed = url_removed

    flat, title_merged = dedupe_by_title(flat)
    stats.title_merges = title_merged

    stats.final_count = len(flat)
    return flat, stats, group_by_source(flat)


def pick_balanced_samples(
    grouped: Dict[str, List[Article]], *, max_items: int = 5
) -> List[Article]:
    """各源轮流取 Top，避免推送/速览被单一源霸占。"""
    if not grouped:
        return []
    sources = list(grouped.keys())
    result: List[Article] = []
    rank_idx = 0
    while len(result) < max_items:
        added = False
        for source in sources:
            items = grouped[source]
            if rank_idx < len(items) and len(result) < max_items:
                result.append(items[rank_idx])
                added = True
        if not added:
            break
        rank_idx += 1
    return result

---
name: daily-china-hot-news-digest
description: |
  汇总国内主流技术与 AI 资讯平台热榜，生成结构化中文摘要报告，并可推送到微信、钉钉等（企业微信 / PushPlus / 钉钉机器人）。
  当用户说「今天 AI 热点」「技术资讯汇总」「推送到微信」「推送到钉钉」「发送热榜通知」「每日资讯总结」「最新 AI 动态」等时使用本技能。
  默认聚焦科技与 AI 领域，可按用户要求调整范围。
tags: [新闻汇总, 热点资讯, AI资讯, 技术热榜, 每日摘要, 信息聚合, 微信推送, 钉钉推送]
version: 1.6
author: 辉方
---

# 国内 AI 与技术热点资讯汇总

本技能通过**本仓库根目录**的 Python 脚本采集多平台数据；脚本规则层做去重与分源排序，Agent 基于**真实输出**做语义筛选并交付报告。

**适用环境**：Cursor、Claude Code、Windsurf 等任意能执行 shell 的 AI 助手。clone 仓库后在根目录执行命令即可。

## 何时使用本技能

- 用户想快速了解当天国内 AI / 技术圈热点
- 需要结构化报告，而非零散链接列表
- 用户要求推送到微信 / 钉钉

## 已接入数据源（与 `main.py` 同步）

**4 个渠道、5 个采集维度**；默认 `--limit 10`，原始约 50 条/次。

| 渠道 | 维度 | `source` | 适配器 |
|------|------|----------|--------|
| 掘金 | 最热 | 掘金·人工智能·热榜 | `juejinfetch.py` |
| 掘金 | 最新 | 掘金·人工智能·最新 | `juejinfetch.py` |
| 量子位 | 最新 | 量子位 | `qbitai_fetch.py` |
| 36氪 | 最热 | 36氪·热榜 | `kr36_fetch.py` |
| InfoQ | 专题最新 | InfoQ·AI&大模型 | `infoq_fetch.py` |

## 数据处理分工（三层）

| 层级 | 执行者 | 做什么 |
|------|--------|--------|
| **L1 采集** | `python main.py` | 各维度 `fetch(limit)`，合并原始池 |
| **L2 规则层** | `post_process.py`（脚本自动） | 分源内排序；URL 完全相同去重；标题高度相似合并（跨源 `source` 用 ` \| ` 连接） |
| **L3 语义层** | **Agent** | 按用户诉求选条数/主题；写「主要热点主题」「总结与洞察」；勿编造条目 |

**禁止跨源比较 `hot_score`**：各平台量纲不同；报告已按 **source 分栏** 展示，速览区为各源轮流 Top 1。

## 数据采集（必须优先执行）

```bash
python main.py                    # 分源 Markdown（默认 --limit 10）
python main.py --limit 15           # 每维度多拉几条
python main.py --json               # 完整 JSON 候选池（Agent 深度筛选推荐）
python main.py --push               # 采集 + 推送
```

- 数据必须来自**本次运行**；不得跳过脚本或编造标题/链接
- Markdown 输出含：概览统计、各源速览、**分源完整列表**、总结占位符
- `--json` 含 `stats`（raw/final/url_dupes/title_merges）、`sources`（分源）、`articles`（扁平列表）

## 筛选与条数（Agent 职责）

1. **先跑脚本**（需要精细筛选时用 `--json`）。
2. **最终条数由用户诉求决定**（默认精选 10–15 条交付；「5 条精华」或「尽量全」相应调整）。
3. 从**分源列表或 JSON** 中选条目；规则层已去重，Agent  focus 语义相关与来源多样性。
4. 用户指定平台/主题时，只选对应 `source` 或标题/摘要匹配项。

## 推送到微信 / 钉钉（按需）

```bash
python main.py --push
```

- 推送正文由 `format_push_markdown` 生成（各源轮流采样 Top 5，**勿自行构造**）
- 配置见 `config.yaml.example` 或环境变量
- 根据终端「推送未就绪 / 失败 / 成功」如实引导用户

## 推送失败与用户引导（Agent 必须遵守）

### A. 推送未就绪

终端含 `【推送未就绪】`：**不要声称已推送**。常见：`NO_CONFIG_FILE`、`NO_CHANNEL_CONFIGURED`、`WECOM_*`、`PUSHPLUS_*`、`DINGTALK_*` 系列 — 见 `config.yaml.example`。

### B. 推送失败

终端含 `【推送失败】`：采集已成功。常见：`PUSHPLUS_NOT_VERIFIED`、`PUSHPLUS_INVALID_TOKEN`、`WECOM_INVALID_KEY`、`WECOM_RATE_LIMIT`、`DINGTALK_*`。

### C. 推送成功

终端出现 `至少一个渠道推送成功` 方可告知已送达。

## 执行步骤

1. 确认用户范围（平台、主题、条数）。
2. 运行 `python main.py` 或 `python main.py --json`。
3. 从输出候选池筛选（规则层已去重分源；Agent 做语义精选）。
4. 补全占位符与总结。
5. 可选：`python main.py --push` 并处理推送结果。

## 输出格式（Agent 交付）

```markdown
# 📅 国内 AI 与技术热点资讯汇总（{日期}）

## 📊 今日概览
- 主要热点主题：（3-5 关键词）
- 信息来源：{sources}
- 说明：规则层候选 {N} 条，以下精选 {K} 条

## 🔥 头条热点（Top 5）
...

## 💡 总结与洞察
...
```

## 依赖与环境

```bash
pip install -r requirements.txt
```

Python 3.8+。扩展新平台见 `README.md`、`prompt.md`。

---
name: daily-china-hot-news-digest
description: |
  汇总国内主流技术与 AI 资讯平台热榜，生成结构化中文摘要报告，并可推送到微信、钉钉等（企业微信 / PushPlus / 钉钉机器人）。
  当用户说「今天 AI 热点」「技术资讯汇总」「推送到微信」「推送到钉钉」「发送热榜通知」「每日资讯总结」「最新 AI 动态」等时使用本技能。
  默认聚焦科技与 AI 领域，可按用户要求调整范围。
tags: [新闻汇总, 热点资讯, AI资讯, 技术热榜, 每日摘要, 信息聚合, 微信推送, 钉钉推送]
version: 1.9
author: 辉方
---

# 国内 AI 与技术热点资讯汇总

本技能通过**本仓库根目录**的 Python 脚本采集多平台数据；脚本规则层做去重与分源排序，Agent 基于**真实输出**做语义筛选并交付报告。

**适用环境**：Cursor、Claude Code、Windsurf 等能执行终端的 AI 助手。**用户无需会编程**，用自然语言提需求即可。

## 环境准备（Agent 必读）

**核心原则**：使用本技能前，若缺少运行条件（Python、依赖包、项目目录、推送配置等），Agent **须先检测 → 用白话告知缺什么、打算做什么 → 征得用户同意 → 再自行在终端处理**。不要把 `pip install`、`python main.py` 等命令丢给用户执行。

**典型流程：**

1. **检测**：工作目录是否为项目根（含 `main.py`）、Python 3.8+ 是否可用、依赖是否已装、推送所需 `config.yaml` 是否存在。
2. **说明并征得同意**（示例）：「当前还没装依赖，我可以在项目里执行安装，大约 1 分钟，是否继续？」
3. **用户同意后，Agent 自行完成**：切换目录、`pip install -r requirements.txt`、必要时创建 venv、执行采集/推送命令。
4. **仅 Agent 无法代劳时再请用户配合**：如本机未装 Python（引导安装并勾选 PATH）、推送 Token 需用户在 PushPlus/钉钉/企微复制后**粘贴给 Agent**、IDE 未授权终端需用户点允许。

**禁止**：跳过环境检查直接编造热榜；未经用户同意擅自安装软件或修改系统级配置。

### Cursor 用户

打开本仓库 → 对话输入 `@SKILL.md` + 需求（如「汇总今天 AI 热点」）→ 其余由 Agent 按上文处理。

## 何时使用本技能

- 用户想快速了解当天国内 AI / 技术圈热点
- 需要结构化报告，而非零散链接列表
- 用户要求推送到微信 / 钉钉

## 已接入数据源（与 `main.py` 同步）

**5 个渠道、7 个采集维度**（含可选抖音）；默认 `--limit 10`。抖音未配置密钥时自动跳过。

| 渠道 | 维度 | `source` | 适配器 |
|------|------|----------|--------|
| 掘金 | 最热 | 掘金·人工智能·热榜 | `juejinfetch.py` |
| 掘金 | 最新 | 掘金·人工智能·最新 | `juejinfetch.py` |
| 量子位 | 最新 | 量子位 | `qbitai_fetch.py` |
| 36氪 | 最热 | 36氪·热榜 | `kr36_fetch.py` |
| InfoQ | 专题最新 | InfoQ·AI&大模型 | `infoq_fetch.py` |
| 抖音 | 最热 | 抖音·热榜·TikHub / 官方 | `douyin_fetch.py`（需配置，见下） |
| 抖音 | 上升/实时 | 抖音·上升·TikHub / 实时热点·官方 | `douyin_fetch.py` |

### 抖音（可选）

用户自行在 `config.yaml` 配置 **TikHub API Key** 或 **抖音开放平台 client_key/secret**（及付费/企业资质由用户自理）。未配置时跳过，不影响其他源。

```yaml
douyin:
  provider: auto   # auto | tikhub | official
  tikhub:
    api_key: ""
  official:
    client_key: ""
    client_secret: ""
```

环境变量：`TIKHUB_API_KEY`、`DOUYIN_CLIENT_KEY`、`DOUYIN_CLIENT_SECRET`、`DOUYIN_PROVIDER`。

## 数据处理分工（三层）

| 层级 | 执行者 | 做什么 |
|------|--------|--------|
| **L1 采集** | `python main.py` | 按 `--dimension` 选择各渠道 hot/latest 能力，`fetch(limit)` |
| **L2 规则层** | `post_process.py`（脚本自动） | 分源内排序；URL 完全相同去重；标题高度相似合并（跨源 `source` 用 ` \| ` 连接） |
| **L3 语义层** | **Agent** | 按用户诉求选条数/主题；写「主要热点主题」「总结与洞察」；勿编造条目 |

**禁止跨源比较 `hot_score`**：各平台量纲不同；报告已按 **source 分栏** 展示，速览区为各源轮流 Top 1。

## 数据采集（Agent 在终端执行，用户无需手动运行）

```bash
python main.py                        # 全部维度，分源 Markdown
python main.py --dimension hot        # 各渠道「最热」能力（掘金热榜、36氪热榜、抖音热榜等）
python main.py --dimension latest     # 各渠道「最新」能力（掘金最新、量子位、InfoQ 等）
python main.py --json                 # JSON 候选池（精细筛选推荐）
python main.py --push                 # 采集 + 推送
```

**用户意图 → 命令（Agent 必须遵守）**

| 用户说法 | 必须执行 |
|----------|----------|
| 最热 / 热榜 / 热门 top N | `python main.py --dimension hot --limit N` |
| 最新 / 快讯 / 动态 / 资讯流 | `python main.py --dimension latest --limit N` |
| 未说明范围（默认汇总） | `python main.py --limit N`（`--dimension all`） |

说明：部分平台只有一种维度（如 36氪仅 hot、量子位仅 latest）；按维度过滤时**只跑该平台具备的能力**。用户说「最热」时**不得**展示 `source` 含「最新」「上升」「实时热点」的维度。

环境就绪后 Agent 执行上述命令；数据必须来自**本次运行**，不得编造标题/链接。

## 筛选与条数（Agent 职责）

1. **先识别维度意图**，选用上表对应 `--dimension`；需要精细筛选时用 `--json`。
2. **最终条数由用户诉求决定**（默认精选 10–15 条交付；「5 条精华」或「尽量全」相应调整）。
3. 从**分源列表或 JSON** 中选条目；规则层已去重，Agent 关注语义相关与来源多样性。
4. 用户指定**平台/主题**时，在已选维度结果内只保留对应 `source` 或标题/摘要匹配项。

## 推送到微信 / 钉钉（按需，Agent 执行）

Agent 执行 `python main.py --push`。若尚无 `config.yaml`，Agent 应：

1. 复制 `config.yaml.example` → `config.yaml`
2. 用 plain language 说明如何获取 Token，请用户**粘贴密钥**
3. Agent 写入配置后再次执行推送命令

- 推送正文由 `format_push_markdown` 生成（各源轮流采样 Top 5，**勿自行构造**）
- 根据终端「推送未就绪 / 失败 / 成功」如实引导用户

## 推送失败与用户引导（Agent 必须遵守）

### A. 推送未就绪

终端含 `【推送未就绪】`：**不要声称已推送**。常见：`NO_CONFIG_FILE`、`NO_CHANNEL_CONFIGURED`、`WECOM_*`、`PUSHPLUS_*`、`DINGTALK_*` 系列 — 见 `config.yaml.example`。

### B. 推送失败

终端含 `【推送失败】`：采集已成功。常见：`PUSHPLUS_NOT_VERIFIED`、`PUSHPLUS_INVALID_TOKEN`、`WECOM_INVALID_KEY`、`WECOM_RATE_LIMIT`、`DINGTALK_*`。

### C. 推送成功

终端出现 `至少一个渠道推送成功` 方可告知已送达。

## 执行步骤

1. **环境准备**（见上文）：检测 → 说明 → 用户同意 → Agent 处理。
2. 确认用户范围（**维度：最热/最新/全部**、平台、主题、条数）。
3. Agent 按意图运行采集命令（含 `--dimension`），从输出中筛选并补全报告。
4. 可选：推送（缺配置时同样先说明、征得同意、Agent 写 `config.yaml`）。

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

## 依赖

Python 3.8+，`requirements.txt`（`requests`、`pyyaml`）。由 Agent 在征得用户同意后安装，见「环境准备」。

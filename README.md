# HotNews Collector Platform

模块化 AI 资讯采集与推送平台，同时作为 **Cursor Agent Skill** 使用：从国内技术与 AI 平台拉取热榜，生成结构化 Markdown 报告，并可推送到微信、钉钉等即时通讯工具。

## 功能特性

- **热榜采集**：适配器模式接入多平台（掘金：最热+最新；量子位、36氪、InfoQ 等）
- **结构化报告**：终端输出完整 Markdown；推送使用精简版正文
- **多渠道推送**：企业微信群机器人、PushPlus（个人微信）、钉钉群机器人
- **配置引导**：推送未就绪或失败时，终端输出分步骤排查指引
- **Skill 工作流**：通过 `SKILL.md` 指导 Agent 执行采集、补全摘要并处理推送结果

## 架构设计

```
采集 (Adapter) → 格式化 (format_report) → 分发 (Dispatcher)
```

| 层级 | 目录 | 职责 |
|------|------|------|
| **Adapter** | `scripts/adapters/` | 各平台 HTTP 请求与数据清洗，统一返回 `Article` |
| **Report** | `scripts/format_report.py` | 生成完整报告 / 推送用精简 Markdown |
| **Dispatcher** | `scripts/dispatchers/` | 读取配置，向微信、钉钉等渠道发送消息 |

## 目录结构

```
HotNews-Collector-Platform/
├── main.py                      # 入口：采集、出报告、可选推送
├── SKILL.md                     # Cursor Agent 技能说明
├── README.md
├── requirements.txt
├── config.yaml.example          # 配置模板（复制为 config.yaml）
├── config.yaml                  # 本地配置（已 gitignore，需自行创建）
├── scripts/
│   ├── adapters/
│   │   ├── core/
│   │   │   ├── article.py       # 统一文章模型
│   │   │   └── base_fetch.py    # 适配器抽象基类
│   │   ├── juejinfetch.py       # 掘金热榜 / 最新
│   │   ├── qbitai_fetch.py      # 量子位最新
│   │   ├── kr36_fetch.py        # 36氪热榜
│   │   └── infoq_fetch.py       # InfoQ AI 话题
│   ├── format_report.py         # Markdown 报告生成
│   └── dispatchers/
│       ├── core/
│       │   ├── base.py          # 推送器基类
│       │   └── config.py        # 配置加载
│       ├── wecom.py             # 企业微信
│       ├── pushplus.py          # PushPlus → 个人微信
│       ├── dingtalk.py          # 钉钉
│       └── push_guide.py        # 配置检查与失败引导
└── docs/
    └── ARCHITECTURE.md
```

## 统一数据模型 (`Article`)

| 字段 | 说明 |
|------|------|
| `title` | 标题 |
| `url` | 详情链接 |
| `source` | 来源平台名称 |
| `publish_time` | 发布时间 |
| `summary` | 摘要 |
| `category` | 分类 |
| `rank` | 榜单排名 |
| `hot_score` | 热度值 |

## 资讯渠道对接情况

**概念约定**

- **渠道**：指资讯平台（如掘金、量子位），一个平台算一个渠道。
- **维度**：同一渠道下的不同列表类型，常见为 **最热**、**最新**（另有推荐、专题等，视平台而定）。
- 报告中 `source` 字段会带上维度后缀（如 `掘金·人工智能·热榜`），便于区分条目来源；统计渠道数量时仍按**平台**计。

默认每个「渠道 × 维度」组合各拉取 **10 条**（`DEFAULT_LIMIT = 10`），多源**不做去重**。当前 **4 个渠道**、**5 个采集维度**、合计约 **50 条/次**。

### 已对接一览（按渠道）

| 渠道 | 维度 | 报告中的 `source` | 适配器 | 接口 | 状态 |
|------|------|-------------------|--------|------|------|
| **掘金** | 最热 | 掘金·人工智能·热榜 | `juejinfetch.py` | `GET article_rank?type=hot` | ✅ |
| **掘金** | 最新 | 掘金·人工智能·最新 | `juejinfetch.py` | `POST recommend_cate_feed`（`sort_type=300`） | ✅ |
| **量子位** | 最新 | 量子位 | `qbitai_fetch.py` | WordPress `GET /wp-json/wp/v2/posts` | ✅ |
| **36氪** | 最热 | 36氪·热榜 | `kr36_fetch.py` | gateway `POST .../nav/rank/hot` | ✅ |
| **InfoQ 中文** | 专题最新 | InfoQ·AI&大模型 | `infoq_fetch.py` | `topic/getInfo` + `article/getList` | ✅ |

### 各渠道说明

#### 掘金（1 个渠道，2 个维度）

| 维度 | 说明 |
|------|------|
| **最热** | 人工智能分类热榜，含 `hot_rank`，与官网热榜一致。 |
| **最新** | 同分类按发布时间倒序；非热榜。 |

实现：`JuejinFetcher(mode="hot")` 与 `JuejinFetcher(mode="latest")` 共用 `juejinfetch.py`，在 `ADAPTERS` 中注册两次。

未接入维度：综合分类热榜（可改 `category_id`）、推荐流等。

#### 量子位（1 个渠道，1 个维度）

| 维度 | 说明 |
|------|------|
| **最新** | WordPress 公开接口，按发布时间。 |

未接入维度：首页「热门文章」（需 HTML 解析，约 5 条）。

#### 36氪（1 个渠道，1 个维度）

| 维度 | 说明 |
|------|------|
| **最热** | 人气榜。 |

未接入维度：最新/快讯（需签名）、热议榜、收藏榜、视频榜。

#### InfoQ 中文（1 个渠道，1 个维度）

| 维度 | 说明 |
|------|------|
| **专题最新** | 默认 AI 话题（「AI&大模型」），非全站热榜。 |

未接入维度：全站推荐 RSS、其他话题（架构、云原生等）。

### 当前 `main.py` 注册

```python
ADAPTERS = [
    JuejinFetcher(mode="hot"),      # 掘金·人工智能·热榜
    JuejinFetcher(mode="latest"),   # 掘金·人工智能·最新
    QbitaiFetcher(),                # 量子位
    Kr36HotFetcher(),               # 36氪·热榜
    InfoQFetcher(),                 # InfoQ·AI&大模型
]
```

### 计划对接（未实现）

| 平台 | 维度 | 说明 |
|------|------|------|
| 知乎 | 热榜 | RSSHub 或站内接口 |
| 机器之心 | 最新 / 热榜 | 待调研稳定数据源 |
| 36氪 | 快讯、热议榜等 | 快讯需签名；其他榜可用第三方聚合 |
| 量子位 | 首页「热门文章」 | 需 HTML 解析，约 5 条 |
| 掘金 | 综合分类热榜 | 修改 `category_id` 即可扩展 |
| GitHub Trending | 日/周/月趋势 | 见 `docs/GITHUB_TRENDING_COLLECTION.md`，偏仓库非资讯站 |

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

需 Python 3.8+，可访问各平台 API 的网络环境。

### 2. 采集并生成报告

```bash
python main.py
```

终端将输出完整 Markdown 热点报告。

### 3. 推送到微信 / 钉钉（可选）

```bash
copy config.yaml.example config.yaml   # Windows
# cp config.yaml.example config.yaml   # macOS / Linux
```

编辑 `config.yaml`，启用至少一个渠道并填写密钥，然后：

```bash
python main.py --push
```

或在 `config.yaml` 中设置 `push.enabled: true`，仅执行 `python main.py` 也会自动推送。

### 推送渠道说明

| 渠道 | 配置项 | 说明 |
|------|--------|------|
| 企业微信 | `wecom.webhook_key` | 群机器人 Webhook 中 `key=` 后的字符串 |
| 个人微信 | `pushplus.token` | 注册 [PushPlus](https://www.pushplus.plus)，需实名认证 |
| 钉钉 | `dingtalk.access_token` | 群自定义机器人 Webhook；加签时需填 `secret` |

**环境变量（可选）**：`WECOM_WEBHOOK_KEY`、`PUSHPLUS_TOKEN`、`DINGTALK_ACCESS_TOKEN`、`DINGTALK_SECRET`

推送失败时，终端会打印错误码与修复步骤（如 `PUSHPLUS_NOT_VERIFIED`、`DINGTALK_SIGN_ERROR` 等）。

## 作为 Cursor Skill 使用

1. 在对话中引用 `@SKILL.md`
2. 例如：「汇总今天 AI 技术热点」或「获取热点并推送到钉钉」
3. Agent 将执行 `python main.py`（及可选的 `--push`），并基于真实输出补全报告

安装到 Cursor 技能目录（`~/.cursor/skills/` 或 `.cursor/skills/`）后，可在任意项目中通过触发词自动加载。

## 扩展新平台

1. 在 `scripts/adapters/` 下新建适配器，继承 `BaseFetch`，实现 `fetch() -> List[Article]`
2. 在 `main.py` 的 `ADAPTERS` 列表中注册实例

```python
ADAPTERS = [
    JuejinFetcher(mode="hot"),
    JuejinFetcher(mode="latest"),
    QbitaiFetcher(),
    Kr36HotFetcher(),
    InfoQFetcher(),
    # YourPlatformFetcher(),
]
```

## Roadmap

- [x] 掘金（最热 + 最新两个维度）
- [x] 量子位最新
- [x] 36氪人气热榜
- [x] InfoQ AI 话题
- [x] Markdown 结构化报告
- [x] 多渠道推送（企业微信 / PushPlus / 钉钉）
- [x] 推送配置检查与失败引导
- [x] Cursor Skill 文档（`SKILL.md`）
- [ ] 知乎、机器之心等平台适配器
- [ ] 多源去重（基于标题相似度）
- [ ] LLM 智能摘要（接入 API 自动提炼要点）
- [ ] 定时任务与飞书推送

## 许可证

见项目仓库说明。

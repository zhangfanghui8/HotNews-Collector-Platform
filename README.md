# HotNews Collector Platform

模块化 AI 资讯采集与推送平台，同时作为 **Cursor Agent Skill** 使用：从国内技术与 AI 平台拉取热榜，生成结构化 Markdown 报告，并可推送到微信、钉钉等即时通讯工具。

## 功能特性

- **热榜采集**：适配器模式接入各平台（当前已接入掘金 AI 热榜）
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
│   │   └── juejinfetch.py       # 掘金热榜
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

1. 在 `scripts/adapters/` 下新建 **一个** 适配器文件（一平台一文件），继承 `BaseFetch`，实现 `fetch() -> List[Article]`
2. 若平台同时有「最热」与「最新」，在同一类中用 `mode` 区分（如 `hot` / `latest`），勿拆成两个 py
3. 在 `main.py` 的 `ADAPTERS` 中，**每个维度注册一行**

```python
ADAPTERS = [
    JuejinFetcher(mode="hot"),
    JuejinFetcher(mode="latest"),
    QbitaiFetcher(),
    # Kr36Fetcher(mode="hot"),
    # Kr36Fetcher(mode="latest"),
]
```

详见 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) 与 [prompt.md](prompt.md)。

## Roadmap

- [x] 掘金 AI 热榜适配器
- [x] Markdown 结构化报告
- [x] 多渠道推送（企业微信 / PushPlus / 钉钉）
- [x] 推送配置检查与失败引导
- [x] Cursor Skill 文档（`SKILL.md`）
- [ ] 36氪、知乎等平台适配器
- [ ] 多源去重（基于标题相似度）
- [ ] LLM 智能摘要（接入 API 自动提炼要点）
- [ ] 定时任务与飞书推送

## 许可证

见项目仓库说明。

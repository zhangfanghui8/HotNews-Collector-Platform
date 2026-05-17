---
name: daily-china-hot-news-digest
description: |
  汇总国内主流技术与 AI 资讯平台热榜，生成结构化中文摘要报告，并可推送到微信、钉钉等（企业微信 / PushPlus / 钉钉机器人）。
  当用户说「今天 AI 热点」「技术资讯汇总」「推送到微信」「推送到钉钉」「发送热榜通知」「每日资讯总结」「最新 AI 动态」等时使用本技能。
  默认聚焦科技与 AI 领域，可按用户要求调整范围。
tags: [新闻汇总, 热点资讯, AI资讯, 技术热榜, 每日摘要, 信息聚合, 微信推送, 钉钉推送]
version: 1.4
author: 辉方
---

# 国内 AI 与技术热点资讯汇总

本技能通过项目内置采集脚本，从已接入的国内资讯平台拉取热榜数据，再经去重、分类与要点提炼，输出结构化 Markdown 报告。

## 何时使用本技能

- 用户想快速了解当天国内 AI / 技术圈热点
- 用户说「今天有什么技术大事」「帮我汇总资讯」「整理热榜」等
- 需要结构化报告，而非零散链接列表
- 用户要求将汇总**推送到微信 / 钉钉**等即时通讯工具

## 数据采集（必须优先执行）

在**本项目根目录**执行采集入口，使用已注册的适配器拉取数据：

```bash
python main.py
```

- 采集逻辑位于 `scripts/adapters/`，各平台实现统一 `fetch()` 接口，返回标准 `Article` 结构
- 新平台接入：在 `adapters/` 下**一平台一文件**；有最热/最新时用同一类的 `mode` 区分，在 `main.py` 的 `ADAPTERS` 中每个维度注册一行（见 `prompt.md` / `docs/ARCHITECTURE.md`）
- 将终端输出的 Markdown **作为报告主体**；不得跳过脚本、凭空编造热榜条目

若脚本执行失败或返回空数据，向用户说明原因（网络、依赖、适配器异常），再视情况协助排查；勿伪造标题与链接。

## 推送到微信 / 钉钉（按需执行）

用户明确要求推送，或 `config.yaml` 中 `push.enabled: true` 时，在采集完成后执行：

```bash
python main.py --push
```

- 推送逻辑位于 `scripts/dispatchers/`（`wecom` 企业微信、`pushplus` 个人微信、`dingtalk` 钉钉群机器人）
- 配置：复制 `config.yaml.example` 为 `config.yaml`，填写对应渠道密钥并 `enabled: true`
- 也可用环境变量：`WECOM_WEBHOOK_KEY`、`PUSHPLUS_TOKEN`、`DINGTALK_ACCESS_TOKEN`、`DINGTALK_SECRET`（见 `scripts/dispatchers/core/config.py`）
- 推送内容为精简版 Markdown（Top 5 + 更多链接），与终端完整报告不同；**勿自行构造推送正文**，由脚本生成
- 脚本会在终端输出**分步骤配置指引**（见下方「推送失败与用户引导」）；Agent 必须**原文转述或概括**这些步骤给用户，勿假装已推送成功

仅生成报告、不推送时：执行 `python main.py`（不加 `--push`）。

## 推送失败与用户引导（Agent 必须遵守）

执行 `python main.py --push` 后，根据终端输出处理：

### A. 推送未就绪（配置问题，尚未发送）

终端含 `【推送未就绪】` 时，说明 `config.yaml` 缺失或未正确启用渠道。**不要声称已推送**。按终端中的编号步骤引导用户，常见情况：

| 错误码 | 含义 | 引导要点 |
|--------|------|----------|
| `NO_CONFIG_FILE` | 无 config.yaml | 复制 `config.yaml.example` 为 `config.yaml` |
| `NO_CHANNEL_CONFIGURED` | 未启用任何渠道 | 在 wecom / pushplus / dingtalk 中择一配置并 `enabled: true` |
| `WECOM_NOT_ENABLED` | 有 key 未启用 | `wecom.enabled: true` |
| `PUSHPLUS_NOT_ENABLED` | 有 token 未启用 | `pushplus.enabled: true` |
| `DINGTALK_NOT_ENABLED` | 有 token 未启用 | `dingtalk.enabled: true` |
| `WECOM_MISSING_KEY` | 已启用但 key 为空 | 企业微信群机器人 Webhook 的 key |
| `PUSHPLUS_MISSING_TOKEN` | 已启用但 token 为空 | 在 pushplus.plus 获取 Token 并绑定微信 |
| `DINGTALK_MISSING_TOKEN` | 已启用但 token 为空 | 钉钉机器人 Webhook 的 access_token |

配置模板与注释见 `config.yaml.example`。

### B. 推送已尝试但失败（配置已有，API 拒绝）

终端含 `【推送失败】` 时，采集已成功，但消息未送达。按错误码引导：

| 错误码 | 含义 | 引导要点 |
|--------|------|----------|
| `PUSHPLUS_NOT_VERIFIED` | PushPlus 未实名 | 打开 https://verify.pushplus.plus 完成认证 |
| `PUSHPLUS_INVALID_TOKEN` | Token 无效 | 在 pushplus.plus 重新复制 Token 并更新配置 |
| `WECOM_INVALID_KEY` | Webhook Key 无效 | 检查 key 或重新添加群机器人 |
| `WECOM_RATE_LIMIT` | 发送过频 | 等待 1 分钟后重试 |
| `DINGTALK_INVALID_TOKEN` | 钉钉 token 无效 | 检查 access_token 或重新添加机器人 |
| `DINGTALK_SIGN_ERROR` | 加签 secret 错误 | 启用加签时填写 secret，未启用则留空 |
| `DINGTALK_KEYWORD_MISMATCH` | 关键词不匹配 | 消息中需包含机器人设置的关键词 |
| `DINGTALK_RATE_LIMIT` | 钉钉发送过频 | 等待 1 分钟后重试 |

修复后让用户重新执行：`python main.py --push`。

### C. 推送成功

终端出现 `推送 [wecom/pushplus/dingtalk]: 成功` 或 `至少一个渠道推送成功` 时，方可告知用户「已发送到对应群聊」。

### D. Agent 回复结构（推送场景）

用户要求推送时，回复中应包含：

1. **资讯摘要**（基于采集结果，已补全占位内容）
2. **推送状态**：成功 / 未配置 / 失败及原因
3. **下一步**（仅失败或未配置时）：列出终端中的 1-2-3 步骤，便于用户逐项完成

## 执行步骤（严格按顺序）

1. **确认范围**：默认「今天 / 最近 24 小时」科技与 AI 热点；用户指定领域或时间段时按要求调整。
2. **运行采集**：执行 `python main.py`，获取各适配器合并后的热榜原始数据。
3. **去重与排序**：多源时按标题相似度去重，按 `hot_score` 降序排列（单源时脚本已排序）。
4. **补全报告**：
   - 将脚本输出中的「主要热点主题」「总结与洞察」两处占位符替换为基于真实数据的提炼（各 1-2 句，勿夸大）
   - 条目摘要优先使用脚本中的 `summary`；缺失时可结合标题简要补充，并标注为推断
5. **交付用户**：输出完整 Markdown，控制总长适中，重点保留 Top 10-15 条。
6. **推送（可选）**：若用户要求发微信 / 通知，执行 `python main.py --push`；根据终端「推送未就绪 / 推送失败 / 成功」三类输出，按上一节表格向用户说明原因与修复步骤，**不得省略失败引导**。

## 输出格式要求（必须严格遵守）

在脚本生成结构的基础上补全占位内容，整体形如：

```markdown
# 📅 国内 AI 与技术热点资讯汇总（{今天日期}）

## 📊 今日概览
- 主要热点主题：（3-5 个关键词）
- 信息来源：{脚本中的平台列表}

## 🔥 头条热点（Top 5）
1. **新闻标题**
   摘要：一句话核心内容。
   来源：平台 | 热度：xxx | [链接](url)

## 📌 分类热点

### 科技与AI
- ...

（其他类别仅在有对应数据时展示）

## 💡 总结与洞察
- 今日最值得关注的趋势：...
- 建议关注方向：...

**数据更新时间**：{当前时间}
**提示**：本汇总为 AI 辅助生成，仅供参考。如需深入某条新闻详情，请告诉我具体标题。
```

## 依赖与环境

```bash
pip install -r requirements.txt
```

需 Python 3.8+，可访问各平台 API 的网络环境。推送功能依赖 `config.yaml` 或环境变量中的渠道密钥。

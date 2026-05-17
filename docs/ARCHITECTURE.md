# 系统架构

## 数据流

```
采集 (Adapter) → 格式化 (format_report) → 分发 (Dispatcher，可选)
```

## 适配器约定

| 规则 | 说明 |
|------|------|
| 一平台一文件 | `scripts/adapters/{platform}_fetch.py` |
| 最热 + 最新 | 同一类 + `mode="hot"` / `mode="latest"`（或 `newsflash` 表示快讯） |
| 注册 | `main.py` 的 `ADAPTERS` 中，每个维度一行实例 |
| 数据模型 | `Article`（`scripts/adapters/core/article.py`） |

### 参考实现

- **双维度**：`juejinfetch.py` — `JuejinFetcher(mode="hot")` / `mode="latest"`
- **单维度**：`qbitai_fetch.py` — 仅按发布时间拉取最新文章

### `mode` 语义

- `hot`：热榜、人气榜、按阅读/点赞等互动排序
- `latest`：最新列表、时间线、快讯流（按发布时间）

详细约束见项目根目录 [prompt.md](../prompt.md)（会话说明）与 [.cursor/rules/general_coding_rules.mdc](../.cursor/rules/general_coding_rules.mdc)（全局编码规范）。

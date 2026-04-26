概述
HotNews-Collector 是一个模块化的自动化技能，旨在统一采集国内主流技术与资讯平台（掘金、36氪、知乎等）的热榜数据，并提供标准化的数据输出，以便于后续进行 AI 摘要分析或推送。

2. 架构设计
本 Skill 采用适配器模式 (Adapter Pattern)，确保核心逻辑与各平台的爬取细节解耦。

Adapter 层：负责各平台的 HTTP 请求及数据清洗，映射为统一标准格式。

Processor 层：负责对采集到的 Raw Data 进行聚合、去重及 LLM 智能摘要。

Dispatcher 层：负责将处理后的数据发送至钉钉/微信/飞书。

3. 统一数据结构 (Standard Schema)
无论来源如何，所有插件必须返回如下 JSON 格式：

JSON
{
  "source": "平台名称",
  "title": "标题",
  "url": "详情页链接",
  "heat": 0,
  "timestamp": "ISO8601时间"
}
4. 目录结构
Plaintext
hotnews-skill/
├── README.md               # 本说明文档
├── main.py                 # 核心控制逻辑 (Processor)
├── adapters/               # 平台适配器目录
│   ├── base.py             # 抽象基类
│   ├── juejin.py           # 掘金实现
│   └── example_platform.py # 其他平台模板
├── requirements.txt        # 依赖包
└── config.yaml             # 配置文件 (Webhook, 定时参数等)
5. 如何扩展新平台
要在本 Skill 中增加一个新平台（例如：知乎），仅需三步：

继承基类：在 adapters/ 下创建 zhihu.py，继承 BaseAdapter。

实现逻辑：实现 fetch() 方法，调用目标 API 并映射为 第3节 定义的标准格式。

注册插件：在 main.py 的 ADAPTERS 列表中添加 ZhihuAdapter() 实例。

6. 使用说明
环境依赖
Bash
pip install requests pyyaml
快速启动
配置：修改 config.yaml，填入你的 DINGTALK_WEBHOOK 地址。

运行：

Bash
python main.py
7. 待办功能 (Roadmap)
[x] 掘金热榜适配器

[ ] 36氪/知乎适配器集成

[ ] AI 智能摘要 (集成 LLM API 进行每日内容提炼)

[ ] 自动去重逻辑 (基于标题相似度)

[ ] 多渠道分发 (钉钉/微信/飞书)
# 爬虫策略与配置化设计汇总

## 总思路

把爬虫做成“配置驱动”的系统：以后不再每次从零写代码，而是选择爬取目的、目标网站、请求方式、解析方式、翻页方式、反爬处理、存储方式、运行频率等配置，然后由统一的爬虫引擎执行。

可以理解为：

```text
爬虫任务 = 目的 + 入口 + 抓取策略 + 解析规则 + 清洗规则 + 存储规则 + 调度规则
```

## 一、爬虫的常见目的

### 1. 信息采集

用于收集网页中的结构化或半结构化信息。

常见场景：

- 商品信息：标题、价格、销量、库存、评价数、店铺
- 新闻资讯：标题、正文、发布时间、作者、来源
- 招聘信息：岗位、薪资、城市、公司、要求
- 房产信息：小区、价格、面积、位置、户型
- 政策公告：标题、发布时间、正文、附件
- 学术资料：论文标题、作者、摘要、DOI、引用量

### 2. 数据监控

用于定时检查某些信息是否变化。

常见场景：

- 价格监控
- 库存监控
- 舆情监控
- 招标公告监控
- 竞争对手动态监控
- 网站内容更新监控

### 3. 数据归档

用于把网页内容长期保存下来，方便后续检索或分析。

常见场景：

- 保存新闻历史
- 保存公告原文
- 保存商品历史价格
- 保存网页快照
- 保存附件、图片、PDF

### 4. 数据分析

用于后续统计、可视化、模型训练或业务决策。

常见场景：

- 市场价格趋势
- 热点词分析
- 用户评论情感分析
- 招聘岗位需求分析
- 行业竞争分析
- 文本分类或知识库构建

### 5. 自动化辅助

用于减少重复性人工操作。

常见场景：

- 批量下载文件
- 自动查询结果
- 自动提交搜索条件
- 自动翻页采集
- 自动整理网页表格

## 二、爬虫策略总览

### 1. 按页面类型划分

#### 静态网页爬虫

适合 HTML 里直接包含目标数据的网站。

常用技术：

- `requests`
- `httpx`
- `BeautifulSoup`
- `lxml`
- `parsel`
- `xpath`
- `css selector`

优点：

- 快
- 稳定
- 资源消耗小
- 适合大规模采集

缺点：

- 无法直接处理复杂 JavaScript 渲染页面

适用场景：

- 普通新闻列表
- 政府公告
- 静态商品页面
- 博客文章
- 简单表格页面

#### 动态网页爬虫

适合页面依赖 JavaScript 渲染的网站。

常用技术：

- `Playwright`
- `Selenium`
- 浏览器开发者工具分析
- 页面等待、点击、滚动、输入

优点：

- 接近真实用户访问
- 能处理 JS 渲染、登录、点击、滚动加载

缺点：

- 慢
- 资源消耗大
- 容易受页面结构变化影响

适用场景：

- React / Vue / Angular 页面
- 需要点击展开的页面
- 无限滚动页面
- 需要登录后查看的数据
- 有复杂交互的网站

#### API 接口爬虫

适合页面通过接口加载数据的网站。

常用技术：

- 浏览器 Network 面板
- `requests`
- `httpx`
- JSON 解析
- 参数构造
- 分页接口分析

优点：

- 快
- 数据结构清晰
- 比解析 HTML 更稳定

缺点：

- 接口可能有签名、Token、时间戳、加密参数
- 接口规则变动后需要更新

适用场景：

- 商品搜索接口
- 评论接口
- 新闻列表接口
- 地图 POI 接口
- 后台 JSON 数据接口

#### 文件下载爬虫

适合批量下载附件或资源文件。

常用技术：

- 文件链接提取
- 流式下载
- 断点续传
- 文件去重
- 文件类型识别

适用场景：

- PDF
- Excel
- Word
- 图片
- 压缩包
- 政府公告附件

### 2. 按访问方式划分

#### 单页爬取

只抓一个页面。

配置重点：

- URL
- 请求头
- 解析规则
- 存储位置

#### 列表页爬取

先抓列表，再进入详情页。

配置重点：

- 列表页 URL
- 翻页规则
- 详情页链接提取规则
- 详情页字段解析规则

#### 搜索式爬取

根据关键词、城市、分类、时间范围等条件搜索。

配置重点：

- 搜索入口
- 查询参数
- 关键词列表
- 分类参数
- 分页参数
- 结果解析规则

#### 增量爬取

只爬新增或变化的数据。

配置重点：

- 唯一 ID
- 上次爬取时间
- 去重字段
- 更新时间字段
- 停止条件

#### 全量爬取

从头到尾完整采集。

配置重点：

- 起始页
- 最大页数
- 最大深度
- 去重规则
- 失败重试

#### 定时监控爬取

按固定频率运行。

配置重点：

- 运行周期
- 监控字段
- 变化判断
- 通知方式
- 历史记录

### 3. 按翻页方式划分

#### URL 页码翻页

示例：

```text
https://example.com/list?page=1
https://example.com/list?page=2
```

配置字段：

- `page_param`
- `start_page`
- `end_page`
- `page_step`

#### Path 页码翻页

示例：

```text
https://example.com/list/1
https://example.com/list/2
```

配置字段：

- `url_template`
- `start_page`
- `end_page`

#### 下一页链接翻页

从页面中提取“下一页”按钮的链接。

配置字段：

- `next_page_selector`
- `max_pages`
- `stop_when_no_next`

#### POST 参数翻页

通过 POST 请求提交页码。

配置字段：

- `method`
- `payload_template`
- `page_field`

#### API cursor 翻页

接口返回 `cursor`、`nextToken`、`offset` 等参数。

配置字段：

- `cursor_field`
- `next_cursor_path`
- `stop_when_empty`

#### 无限滚动翻页

页面滚动后自动加载更多内容。

配置字段：

- `scroll_times`
- `scroll_pause`
- `item_selector`
- `stop_when_count_unchanged`

### 4. 按解析方式划分

#### CSS Selector

适合结构清晰的 HTML。

示例：

```yaml
title: "h1::text"
price: ".price::text"
link: ".item a::attr(href)"
```

#### XPath

适合复杂层级或需要精准定位的 HTML。

示例：

```yaml
title: "//h1/text()"
price: "//span[@class='price']/text()"
```

#### JSON Path

适合 API 返回的 JSON。

示例：

```yaml
title: "$.data.items[*].title"
price: "$.data.items[*].price"
```

#### 正则表达式

适合从文本中抽取特定模式。

示例：

```yaml
phone: "\\d{3,4}-\\d{7,8}"
email: "[\\w.-]+@[\\w.-]+"
```

建议：正则适合补充，不建议作为主要解析方式。

#### 表格解析

适合网页表格或 Excel 文件。

常用技术：

- `pandas.read_html`
- `openpyxl`
- `xlrd`

#### PDF / Word 解析

适合公告附件、报告、论文等。

常用技术：

- `pypdf`
- `pdfplumber`
- `python-docx`

## 三、常用请求策略

### 1. 请求头策略

常见字段：

- `User-Agent`
- `Referer`
- `Accept`
- `Accept-Language`
- `Cookie`
- `Authorization`

配置示例：

```yaml
headers:
  User-Agent: "Mozilla/5.0 ..."
  Referer: "https://example.com"
```

### 2. Cookie 策略

适用场景：

- 登录后访问
- 地区选择
- 年龄确认
- 站点偏好

配置方式：

```yaml
cookies:
  sessionid: "xxx"
```

### 3. 代理策略

适用场景：

- 访问频率较高
- 目标站限制 IP
- 多地区采集

配置方式：

```yaml
proxy:
  enabled: true
  pool: "default"
  rotate: true
```

注意：代理需要合法合规使用，不建议对明确禁止自动化访问的网站进行高频采集。

### 4. 限速策略

用于降低对目标网站的压力，也能减少被封风险。

配置方式：

```yaml
rate_limit:
  delay_min: 1
  delay_max: 3
  concurrency: 3
```

### 5. 重试策略

适合网络波动或临时失败。

配置方式：

```yaml
retry:
  times: 3
  backoff: 2
  retry_status: [429, 500, 502, 503, 504]
```

### 6. 超时策略

配置方式：

```yaml
timeout:
  connect: 10
  read: 30
```

### 7. 编码处理

常见编码：

- `utf-8`
- `gbk`
- `gb2312`

配置方式：

```yaml
encoding: "auto"
```

## 四、常见反爬场景与处理方法

### 1. User-Agent 检测

方法：

- 设置真实浏览器 UA
- 多 UA 轮换

### 2. Referer 检测

方法：

- 设置来源页面
- 按真实访问链路请求

### 3. Cookie / Session 检测

方法：

- 先访问首页获取 Cookie
- 登录后保存 Cookie
- 定期刷新 Session

### 4. 频率限制

方法：

- 限速
- 随机延迟
- 降低并发
- 指数退避重试

### 5. IP 限制

方法：

- 降低频率
- 合规代理池
- 分布式任务队列

### 6. JavaScript 渲染

方法：

- 优先分析接口
- 必要时使用 Playwright

### 7. 验证码

建议：

- 遇到验证码时暂停任务
- 使用人工处理流程
- 避免绕过访问控制

### 8. 参数签名 / 加密

方法：

- 优先寻找公开 API 或页面内数据
- 分析前端 JS 参数生成逻辑
- 封装签名函数

注意：不要绕过网站的安全机制或访问权限。

### 9. 动态字体 / 图片混淆

方法：

- 字体映射
- OCR
- 页面接口分析

这类成本较高，适合单独做专项适配。

## 五、数据清洗方法

### 1. 文本清洗

常见处理：

- 去除空格、换行、制表符
- HTML 实体解码
- 全角半角转换
- 去除无关符号

### 2. 时间标准化

示例：

```text
今天 10:30 -> 2026-05-05 10:30:00
3小时前 -> 当前时间减 3 小时
2026年5月5日 -> 2026-05-05
```

### 3. 数值标准化

示例：

```text
1.2万 -> 12000
￥99.00 -> 99.00
15k-25k -> 最低 15000，最高 25000
```

### 4. URL 标准化

处理内容：

- 相对链接转绝对链接
- 去除跟踪参数
- 统一协议
- 去重

### 5. 去重

常见唯一键：

- URL
- 标题 + 发布时间
- 平台 ID
- 商品 ID
- 内容 Hash

配置方式：

```yaml
dedupe:
  enabled: true
  key_fields: ["url"]
```

## 六、存储方式

### 1. CSV

适合简单数据导出。

优点：

- 易查看
- 易导入 Excel

缺点：

- 不适合复杂结构
- 不适合频繁更新

### 2. JSON / JSONL

适合半结构化数据和中间结果。

推荐大批量数据使用 JSONL。

### 3. Excel

适合人工查看和交付。

### 4. SQLite

适合本地项目、轻量级去重和增量更新。

### 5. MySQL / PostgreSQL

适合正式业务系统。

### 6. MongoDB

适合字段变化较多的网页数据。

### 7. 文件系统

适合保存：

- 图片
- PDF
- Word
- HTML 快照
- 原始响应

## 七、任务调度方式

### 1. 手动运行

适合临时采集。

### 2. 命令行运行

示例：

```text
python crawl.py --config configs/news.yaml
```

### 3. 定时任务

可选方案：

- Windows 任务计划程序
- Linux cron
- APScheduler
- Celery Beat

### 4. 队列任务

适合大量 URL 或多站点采集。

可选方案：

- Redis Queue
- Celery
- Kafka

## 八、建议的配置模板

下面是一个通用 YAML 模板，未来可以把它做成表单，让你勾选或填写。

```yaml
task:
  name: "示例任务"
  purpose: "信息采集"
  description: "采集列表页和详情页数据"

target:
  site_name: "example"
  base_url: "https://example.com"
  entry_urls:
    - "https://example.com/list?page=1"
  allowed_domains:
    - "example.com"

request:
  method: "GET"
  type: "static"   # static / dynamic / api / file
  headers:
    User-Agent: "Mozilla/5.0 ..."
  cookies: {}
  params: {}
  payload: {}
  encoding: "auto"
  timeout:
    connect: 10
    read: 30

browser:
  enabled: false
  engine: "playwright"
  headless: true
  wait_until: "networkidle"
  actions:
    - type: "scroll"
      times: 3
      pause: 1

pagination:
  enabled: true
  type: "page_param"  # page_param / url_template / next_link / cursor / infinite_scroll
  page_param: "page"
  start_page: 1
  end_page: 10
  next_page_selector: ""
  cursor_field: ""

list:
  item_selector: ".item"
  fields:
    title:
      selector: ".title::text"
      required: true
    detail_url:
      selector: "a::attr(href)"
      required: true
      transform: "absolute_url"

detail:
  enabled: true
  fields:
    title:
      selector: "h1::text"
    publish_time:
      selector: ".time::text"
      transform: "datetime"
    content:
      selector: ".content::text"
      join: "\n"

api:
  enabled: false
  data_path: "$.data.items"
  fields:
    title: "$.title"
    url: "$.url"

cleaning:
  strip: true
  normalize_space: true
  html_unescape: true
  remove_tracking_params: true

dedupe:
  enabled: true
  key_fields:
    - "detail_url"

rate_limit:
  delay_min: 1
  delay_max: 3
  concurrency: 3

retry:
  times: 3
  backoff: 2
  retry_status:
    - 429
    - 500
    - 502
    - 503
    - 504

storage:
  type: "sqlite"  # csv / jsonl / excel / sqlite / mysql / postgres / mongodb
  path: "data/example.db"
  table: "items"
  save_raw_html: false
  raw_dir: "data/raw"

schedule:
  enabled: false
  type: "interval"  # once / interval / cron
  interval_minutes: 60
  cron: ""

notification:
  enabled: false
  type: "console"  # console / email / webhook
```

## 九、以后可以勾选的核心选项

### 1. 选择爬虫目的

- 信息采集
- 数据监控
- 数据归档
- 数据分析
- 文件下载
- 自动化查询

### 2. 选择目标类型

- 静态 HTML
- 动态 JS 页面
- JSON API
- 文件附件
- 表格页面
- PDF / Word 文档

### 3. 选择入口方式

- 单个 URL
- 多个 URL
- 列表页
- 搜索页
- 关键词列表
- 站点地图
- API 接口

### 4. 选择翻页方式

- 页码参数
- URL 模板
- 下一页按钮
- cursor / token
- offset / limit
- 无限滚动

### 5. 选择解析方式

- CSS Selector
- XPath
- JSON Path
- 正则
- 表格解析
- PDF 文本解析

### 6. 选择详情页策略

- 不进入详情页
- 进入详情页采集
- 只保存详情页 URL
- 详情页失败时跳过
- 详情页失败时重试

### 7. 选择反爬与稳定性策略

- 请求头
- Cookie
- 登录态
- 代理
- 限速
- 随机延迟
- 失败重试
- 浏览器渲染

### 8. 选择数据处理方式

- 文本清洗
- 时间标准化
- 数值标准化
- URL 标准化
- 去重
- 字段校验
- 缺失值处理

### 9. 选择存储方式

- CSV
- Excel
- JSONL
- SQLite
- MySQL
- PostgreSQL
- MongoDB
- 文件目录

### 10. 选择运行方式

- 立即运行
- 定时运行
- 批量运行
- 增量运行
- 失败续跑

## 十、推荐的程序结构

建议后续把代码拆成这些模块：

```text
Crawl/
  configs/
    news.yaml
    product.yaml
    api.yaml
  crawler/
    engine.py
    fetcher.py
    browser_fetcher.py
    parser.py
    paginator.py
    cleaner.py
    storage.py
    scheduler.py
    dedupe.py
  data/
    raw/
    output/
  main.py
  CRAWLER_STRATEGY_TEMPLATE.md
```

模块职责：

- `engine.py`：读取配置并组织整个流程
- `fetcher.py`：处理普通 HTTP 请求
- `browser_fetcher.py`：处理 Playwright / Selenium 动态页面
- `parser.py`：根据 CSS、XPath、JSON Path 提取字段
- `paginator.py`：处理翻页
- `cleaner.py`：清洗和标准化字段
- `dedupe.py`：去重和增量判断
- `storage.py`：保存到 CSV、JSONL、SQLite 等
- `scheduler.py`：定时任务
- `main.py`：命令行入口

## 十一、最小可行版本

第一版不建议一口气做得很复杂，可以先支持：

- 静态网页
- API JSON
- CSS Selector
- XPath
- JSON Path
- 页码翻页
- 下一页翻页
- CSV / JSONL / SQLite 存储
- 限速
- 重试
- 去重

第二版再加入：

- Playwright 动态页面
- 登录 Cookie
- 无限滚动
- 文件下载
- 定时任务
- 代理池
- 可视化配置界面

## 十二、判断一个新网站应该选什么策略

可以按这个顺序判断：

1. 打开网页，查看目标数据是否直接出现在 HTML 里。
2. 如果 HTML 里有数据，优先用静态爬虫。
3. 如果 HTML 里没有数据，打开浏览器 Network 面板，看是否有 JSON 接口。
4. 如果有 JSON 接口，优先用 API 爬虫。
5. 如果接口参数复杂，分析请求参数、Cookie、Referer。
6. 如果必须依赖页面交互，再使用 Playwright。
7. 如果数据在附件里，则使用文件下载 + 文件解析。

推荐优先级：

```text
API 接口 > 静态 HTML > 文件下载 > 浏览器自动化
```

## 十三、合规与风险提醒

爬虫需要注意：

- 遵守目标网站的 robots.txt、用户协议和相关法律法规
- 不采集敏感个人信息
- 不绕过登录权限、验证码、付费墙或安全控制
- 控制访问频率，避免影响目标网站服务
- 对采集数据标注来源和时间
- 商业用途前建议做合规审查

## 十四、最终目标形态

未来理想的使用方式可以是：

```text
1. 新建任务
2. 填目标网站和入口 URL
3. 选择页面类型：静态 / 动态 / API / 文件
4. 选择翻页方式
5. 填字段提取规则
6. 选择清洗、去重、存储方式
7. 点击运行
8. 查看结果和日志
```

也可以做成命令行：

```text
python main.py --config configs/example.yaml
```

或者做成一个简单 Web 界面：

```text
选择配置 -> 测试解析 -> 运行任务 -> 导出数据
```

## 十五、简短答案

可行。

最合理的方向不是“为每个网站写一个完整爬虫”，而是搭建一个“通用爬虫引擎 + 站点配置文件”的系统。不同网站之间变化最大的部分通常是入口 URL、请求参数、翻页规则、字段选择器和清洗规则；这些内容都可以配置化。真正需要写代码的部分，是通用请求、解析、清洗、去重、存储、调度这套底层能力。


# Crawl

这是一个配置化爬虫项目骨架。目标是把常见爬虫能力沉淀成通用引擎，以后针对新网站时，优先改配置文件，而不是每次从零写代码。

## 当前支持

- 静态 HTML 页面抓取
- JSON API 抓取
- Playwright 动态页面抓取入口
- CSS Selector 字段提取
- XPath 字段提取
- 简单正则字段提取
- JSONPath 风格字段提取
- 页码参数分页
- URL 模板分页
- 下一页链接分页
- API cursor 游标分页
- 动态页面滚动加载
- 详情页二级抓取
- 图片、音频、视频、字幕、附件直链下载
- srt / vtt / ass 字幕转纯文本
- PDF / Word / Excel / CSV / TXT 附件下载后解析文本
- 文本清洗
- URL 跟踪参数清理
- 内存去重和文件持久化去重
- 任务日志、错误日志、运行摘要
- 失败 URL 记录和失败续跑
- JSONL / CSV / SQLite 存储
- 请求超时、重试、限速
- 完整配置协议示例，未实现的高级能力会被配置加载器安全忽略

## 安装依赖

```powershell
pip install -r requirements.txt
```

## 运行示例

静态 HTML 示例：

```powershell
python main.py --config configs/example_static.yaml
```

JSON API 示例：

```powershell
python main.py --config configs/example_api.yaml
```

动态页面需要额外安装浏览器：

```powershell
pip install playwright
playwright install
python main.py --config configs/example_dynamic_scroll.yaml
```

## 配置示例

- [configs/all_options_annotated.yaml](h:/code/python/project/Crawl/configs/all_options_annotated.yaml)：完整注释版配置字典，列出各种可选值和写法。
- [configs/template.yaml](h:/code/python/project/Crawl/configs/template.yaml)：普通任务模板。
- [configs/example_static.yaml](h:/code/python/project/Crawl/configs/example_static.yaml)：静态 HTML 示例。
- [configs/example_api.yaml](h:/code/python/project/Crawl/configs/example_api.yaml)：JSON API 示例。
- [configs/example_dynamic_scroll.yaml](h:/code/python/project/Crawl/configs/example_dynamic_scroll.yaml)：动态页面滚动加载示例。
- [configs/example_cursor_comments.yaml](h:/code/python/project/Crawl/configs/example_cursor_comments.yaml)：社交评论 cursor 接口示例。
- [configs/example_video_subtitle.yaml](h:/code/python/project/Crawl/configs/example_video_subtitle.yaml)：视频字幕下载并转纯文本示例。
- [configs/example_image_gallery.yaml](h:/code/python/project/Crawl/configs/example_image_gallery.yaml)：图片图集下载示例。
- [configs/example_attachments.yaml](h:/code/python/project/Crawl/configs/example_attachments.yaml)：PDF / Word 附件下载示例。

## 新建一个爬虫任务

复制模板：

```powershell
Copy-Item configs/template.yaml configs/my_task.yaml
```

然后主要修改这些位置：

- `task.name`：任务名称
- `target.base_url`：目标网站根地址
- `target.entry_urls`：入口 URL
- `request.type`：`static` 或 `api`
- `browser.enabled`：是否启用动态渲染
- `pagination`：翻页规则
- `list.item_selector`：列表项选择器
- `list.fields`：HTML 字段提取规则
- `api.data_path` 和 `api.fields`：JSON API 字段提取规则
- `media`：图片、视频、音频、字幕、附件下载规则
- `dedupe.key_fields`：去重字段
- `storage.type` 和 `storage.path`：保存方式和输出路径

## HTML 字段规则

CSS Selector：

```yaml
title:
  selector: ".title::text"
```

属性提取：

```yaml
detail_url:
  selector: "a::attr(href)"
  transform: "absolute_url"
```

XPath：

```yaml
title:
  mode: "xpath"
  selector: "//h1/text()"
```

正则：

```yaml
phone:
  mode: "regex"
  selector: "\\d{3,4}-\\d{7,8}"
```

多个结果合并：

```yaml
content:
  selector: ".content p::text"
  many: true
  join: "\n"
```

## API 字段规则

数组接口：

```yaml
api:
  enabled: true
  data_path: "$"
  fields:
    id: "$.id"
    title: "$.title"
```

嵌套接口：

```yaml
api:
  enabled: true
  data_path: "$.data.items"
  fields:
    title: "$.title"
    url: "$.url"
```

## 详情页抓取

列表页先提取 `detail_url`，再进入详情页补充正文、发布时间等字段：

```yaml
list:
  item_selector: ".item"
  fields:
    title:
      selector: ".title::text"
    detail_url:
      selector: "a::attr(href)"
      transform: "absolute_url"

detail:
  enabled: true
  url_field: "detail_url"
  keep_on_detail_failed: true
  fields:
    content:
      selector: ".article p::text"
      many: true
      join: "\n"
    publish_time:
      selector: ".publish-time::text"
```

## 分页规则

页码参数：

```yaml
pagination:
  enabled: true
  type: "page_param"
  page_param: "page"
  start_page: 1
  end_page: 10
```

URL 模板：

```yaml
pagination:
  enabled: true
  type: "url_template"
  url_template: "https://example.com/list/{page}"
  start_page: 1
  end_page: 10
```

下一页链接：

```yaml
pagination:
  enabled: true
  type: "next_link"
  next_page_selector: "a.next"
  max_pages: 10
```

API cursor：

```yaml
pagination:
  enabled: true
  type: "cursor"
  cursor_param: "cursor"
  cursor_start: ""
  next_cursor_path: "$.data.next_cursor"
  max_pages: 20
```

动态滚动：

```yaml
request:
  type: "dynamic"

browser:
  enabled: true
  actions:
    - type: "scroll"
      times: 5
      pause: 1
```

## 富媒体下载

图片：

```yaml
media:
  enabled: true
  output_dir: "data/media/gallery"
  resources:
    - name: "images"
      type: "image"
      url_fields: ["image_urls"]
      filename_prefix: "gallery"
```

字幕：

```yaml
media:
  enabled: true
  output_dir: "data/media/subtitles"
  resources:
    - name: "subtitles"
      type: "subtitle"
      url_fields: ["subtitle_url"]
      filename_prefix: "subtitle"
```

字幕文件下载后会自动把 `.srt`、`.vtt`、`.ass` 转成同名 `.txt` 纯文本。

附件解析：

```yaml
media:
  enabled: true
  parse_attachments: true
  resources:
    - name: "attachments"
      type: "attachment"
      url_fields: ["pdf_url", "word_url", "excel_url"]
      parse: true
      include_text: true
```

当前支持 `.pdf`、`.docx`、`.xlsx`、`.xlsm`、`.csv`、`.txt`。解析后会生成同名 `.txt`，并可把文本写入结果字段。

## 去重

单次运行内存去重：

```yaml
dedupe:
  enabled: true
  type: "memory"
  key_fields: ["id"]
```

跨运行持久化去重：

```yaml
dedupe:
  enabled: true
  type: "persistent"
  key_fields: ["id"]
  path: "data/state/my_task_dedupe.txt"
```

## 日志和失败续跑

```yaml
resume:
  enabled: true
  retry_failed_first: true
  completed_path: "data/state/my_task_completed_urls.txt"
  failed_path: "data/state/my_task_failed.jsonl"

logging:
  enabled: true
  request_log: "data/logs/my_task_requests.jsonl"
  error_log: "data/logs/my_task_errors.jsonl"
  summary_log: "data/logs/my_task_summary.jsonl"
```

启用后，成功的页面会记录到 `completed_path`，失败请求会写入 `failed_path`。下次运行如果 `retry_failed_first: true`，会优先重试失败队列，并跳过已完成 URL。

## 本地可视化配置页面

启动：

```powershell
python ui_app.py
```

然后打开：

```text
http://127.0.0.1:5000
```

页面可以选择爬虫类型、翻页方式、字段规则、媒体下载、日志、失败续跑和存储方式，并生成 YAML 配置。也可以从页面直接运行当前配置。

## 合规边界

这个项目适合采集你有权访问、允许自动化访问或公开发布的数据。对于登录权限、验证码、付费内容、平台安全控制、个人敏感信息等场景，请先确认目标站点规则和法律合规要求。

配置协议里保留了 `anti_bot`、`auth`、`browser` 等字段，但项目不会默认提供绕过验证码、绕过付费墙、绕过访问控制的实现。遇到验证码建议使用人工处理或停止任务。

## 建议工作流

1. 先用浏览器打开目标页面，判断是静态 HTML 还是 API。
2. 如果是 API，优先配置 `request.type: api`。
3. 如果是普通 HTML，配置 `list.item_selector` 和 `list.fields`。
4. 先把 `pagination.enabled` 设为 `false`，只测试第一页。
5. 字段能正确提取后，再打开分页。
6. 输出先用 `jsonl`，稳定后再切 CSV 或 SQLite。

## 后续优化方向

- 增加任务日志和失败续跑
- 增加本地可视化配置页面
- 增加 PDF、Word、Excel 附件解析
- 增加 Excel / Parquet / MySQL / PostgreSQL 存储
- 增加 Redis / Bloom Filter 海量去重
- 增加 WebSocket 实时数据采集

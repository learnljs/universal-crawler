# 通用爬虫能力矩阵

这份矩阵用于区分三类状态：

- `已接入`：当前代码已经能根据配置运行。
- `配置协议已预留`：配置文件可以先写，加载时不会报错，但还需要后续代码实现。
- `谨慎处理`：涉及登录权限、验证码、平台安全控制或强站点定制，需要合规确认和人工介入。

## 基础爬取

| 能力 | 状态 | 主要配置 |
| --- | --- | --- |
| 静态 HTML | 已接入 | `request.type: static` |
| JSON API | 已接入 | `request.type: api`, `api.enabled: true` |
| 动态 JS 页面 | 已接入入口 | `request.type: dynamic`, `browser.enabled: true` |
| Ajax / Fetch 接口 | 已接入 | 按 API 配置处理 |
| 表单 POST | 部分已接入 | `request.method: POST`, `request.payload` |
| WebSocket 实时数据 | 配置协议已预留 | 后续可增加 `websocket` 配置 |
| 加密签名接口 | 配置协议已预留 | 后续按站点增加签名插件 |

## 数据提取

| 能力 | 状态 | 主要配置 |
| --- | --- | --- |
| CSS Selector | 已接入 | `list.fields.*.selector` |
| XPath | 已接入 | `mode: xpath` |
| 正则 | 已接入 | `mode: regex` |
| JSONPath 风格提取 | 已接入 | `api.data_path`, `api.fields` |
| 富媒体 URL 字段提取 | 已接入 | `media.resources.*.url_fields` |
| 富媒体 URL 自动识别 | 已接入 | `media.resources.*.auto_extract` |
| OCR | 配置协议已预留 | 后续可接 PaddleOCR / Tesseract |
| HTML / Markdown 转纯文本 | 部分已接入 | 字段文本清洗、字幕转文本已接入 |

## 分页

| 能力 | 状态 | 主要配置 |
| --- | --- | --- |
| 页码参数 | 已接入 | `pagination.type: page_param` |
| URL 模板 | 已接入 | `pagination.type: url_template` |
| 下一页链接 | 已接入 | `pagination.type: next_link` |
| API cursor / last_id | 已接入 | `pagination.type: cursor` |
| 无限滚动 | 已接入入口 | `request.type: dynamic`, `browser.actions.scroll` |

## 多级抓取

| 能力 | 状态 | 主要配置 |
| --- | --- | --- |
| 详情页二级抓取 | 已接入 | `detail.enabled: true` |
| 评论页 / 子页面 | 可用配置组合实现 | 列表字段 + API / cursor 配置 |
| 多级递归深度限制 | 配置协议已预留 | `filters.max_depth` |

## 富媒体

| 能力 | 状态 | 主要配置 |
| --- | --- | --- |
| 图片下载 | 已接入 | `media.type: image` |
| 音频下载 | 已接入直链 | `media.type: audio` |
| 视频 MP4 下载 | 已接入直链 | `media.type: video` |
| m3u8 分段合并 | 配置协议已预留 | 后续接 ffmpeg / m3u8 解析 |
| 字幕下载 | 已接入 | `media.type: subtitle` |
| srt / vtt / ass 转纯文本 | 已接入 | 自动生成 `.txt` |
| PDF / Word / Excel 附件下载 | 已接入直链下载 | `media.type: attachment` |
| PDF / Word / Excel 内容解析 | 配置协议已预留 | 后续接 pdfplumber / python-docx / openpyxl |

## 登录与权限

| 能力 | 状态 | 主要配置 |
| --- | --- | --- |
| Cookie 登录 | 已可手工配置 | `request.cookies` |
| Bearer Token | 已可手工配置 | `request.headers.Authorization` |
| API Key | 已可手工配置 | `request.headers` 或 `request.params` |
| 表单登录 | 配置协议已预留 | `auth.type: form_login` |
| 扫码登录 | 谨慎处理 | 建议人工扫码后保存 Cookie |

## 反爬与稳定性

| 能力 | 状态 | 主要配置 |
| --- | --- | --- |
| User-Agent | 已接入 | `request.headers.User-Agent` |
| Referer / Origin | 已接入 | `request.headers` |
| 限速 | 已接入 | `rate_limit.delay_min`, `delay_max` |
| 重试 | 已接入 | `retry` |
| 代理池 | 配置协议已预留 | `anti_bot.proxy` |
| 浏览器指纹 | 配置协议已预留 | `anti_bot.fingerprint` |
| 验证码 | 谨慎处理 | 建议 `captcha.mode: manual` |

## 去重与存储

| 能力 | 状态 | 主要配置 |
| --- | --- | --- |
| 内存去重 | 已接入 | `dedupe.type: memory` |
| 文件持久化去重 | 已接入 | `dedupe.type: persistent` |
| 业务字段去重 | 已接入 | `dedupe.key_fields` |
| Bloom Filter | 配置协议已预留 | 后续大数据量扩展 |
| JSONL | 已接入 | `storage.type: jsonl` |
| CSV | 已接入 | `storage.type: csv` |
| SQLite | 已接入 | `storage.type: sqlite` |
| Excel / Parquet / MySQL / PostgreSQL | 配置协议已预留 | 后续扩展 |
| MinIO / OSS | 配置协议已预留 | 后续扩展 |

## 任务控制

| 能力 | 状态 | 主要配置 |
| --- | --- | --- |
| 命令行运行 | 已接入 | `python main.py --config ...` |
| 定时任务 | 配置协议已预留 | `schedule` |
| 并发 | 配置协议已预留 | `rate_limit.concurrency` |
| 断点续爬 | 部分已接入 | 持久化去重可避免重复保存 |
| 日志系统 | 配置协议已预留 | `logging` |
| 监控告警 | 配置协议已预留 | `monitoring` |


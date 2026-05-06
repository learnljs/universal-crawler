# Crawl Studio 部署路径与目录说明

这个项目不是纯静态页面。`templates/index.html` 是 Flask/Jinja 模板，必须由 `ui_app.py` 渲染后访问。

如果直接双击打开 `templates/index.html`，或者把 `templates/` 当静态目录部署，会看到类似：

```text
{{ config }}
Unexpected token '<', '<!DOCTYPE ... is not valid JSON
```

这说明前端请求 API 时拿到的是 HTML 页面，不是 JSON。

## 一、不能按本地方式随便安排的路径

### 1. 模板路径

本地：

```text
templates/index.html
```

部署时不能直接暴露给浏览器访问。必须通过 Flask：

```text
GET /
```

原因：`{{ ... }}`、`{% ... %}` 这些内容需要后端渲染。

### 2. API 路径

当前 API：

```text
/api/configs
/api/config/<name>
/api/generate
/api/save
/api/run
```

部署时反向代理必须把 `/api/*` 转发到 Flask 应用，不能让前端静态服务器接管。

如果部署在子路径，例如：

```text
https://example.com/crawl-studio/
```

就要保证 API 也在同一个应用路径下正确转发。前端已经通过 `url_for` 注入接口地址，避免硬编码 `/api/...`。

### 3. 静态资源路径

静态资源：

```text
static/styles.css
static/app.js
```

部署时可以由 Flask 提供，也可以由 Nginx/CDN 提供，但路径必须和页面里的资源路径一致。

如果看到页面有结构但没有样式，多半是 `/static/...` 没转发或被缓存。

### 4. 配置文件目录

本地：

```text
configs/
```

部署时这个目录不能当成普通公开静态目录随便暴露，因为里面可能包含：

- Cookie
- Authorization Token
- API Key
- 目标站点参数
- 业务规则

建议：

```text
configs/            # 只给后端读写，不公开
```

### 5. 输出数据目录

本地：

```text
data/output/
data/media/
data/logs/
data/state/
```

部署时这些应该放到持久化存储卷，不要放在容器临时文件系统里，否则重启后会丢：

```text
/var/lib/crawl-studio/output
/var/lib/crawl-studio/media
/var/lib/crawl-studio/logs
/var/lib/crawl-studio/state
```

后续可以把这些路径做成环境变量。

### 6. 爬虫运行入口

当前 UI 运行任务时会调用：

```text
python main.py --config configs/xxx.yaml
```

部署时要注意：

- 服务器必须有 Python 环境和依赖
- 工作目录必须是项目根目录
- Web 进程需要有写入 `configs/`、`data/` 的权限
- 长任务不建议一直阻塞 Web 请求，正式部署最好改成后台队列

## 二、推荐部署形态

### 轻量部署

适合个人使用、内网使用：

```text
Flask/Gunicorn 或 Waitress
Nginx 反向代理
本地磁盘持久化 data/
```

Windows 上可以用：

```powershell
waitress-serve --host=127.0.0.1 --port=5000 ui_app:app
```

Linux 上可以用：

```bash
gunicorn -w 2 -b 127.0.0.1:5000 ui_app:app
```

### 正式部署

建议拆成：

```text
Web UI 服务
任务队列服务
爬虫 Worker
数据库
对象存储
日志/监控
```

原因：爬虫任务可能很久，直接在 Web 请求里跑，容易超时。

## 三、Nginx 反向代理要点

如果部署在根路径：

```nginx
location / {
    proxy_pass http://127.0.0.1:5000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

如果部署在子路径，例如 `/crawl-studio/`，需要额外处理路径前缀。更稳的做法是先部署到独立子域名：

```text
https://crawl.example.com/
```

## 四、哪些目录不要公开

不要用静态服务器公开这些目录：

```text
configs/
data/state/
data/logs/
data/output/
data/media/
```

原因：

- `configs/` 可能含登录态或 Token
- `data/state/` 有去重和失败队列
- `data/logs/` 有请求 URL、错误信息
- `data/output/` 和 `data/media/` 是采集结果，可能有版权或隐私风险

如果确实要下载结果，应做受控下载接口和权限校验。

## 五、现在截图里问题的含义

如果页面显示：

```text
{{ config }}
```

说明模板没有经过 Flask 渲染。

如果页面提示：

```text
Unexpected token '<', '<!DOCTYPE ... is not valid JSON
```

说明前端请求 API，但服务器返回了 HTML 页面。常见原因：

- 直接打开了 HTML 文件
- 静态站点托管没有后端 API
- 反向代理没有转发 `/api/*`
- 部署到子路径后 API 路径错了

正确打开方式：

```text
http://127.0.0.1:5000
```

而不是：

```text
templates/index.html
```


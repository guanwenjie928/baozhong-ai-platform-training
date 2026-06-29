---
model: kimi-k2.5
name: deploy-anywhere
version: "1.1.0"
description: "通用 Web 应用一键部署技能 — 容器/K8s 环境下，nginx 反向代理 + FastAPI + React SPA 的标准部署方案，支持多应用路径隔离共存，自动分配空闲端口"
author: "知雀团队"
tags:
  - deployment
  - nginx
  - fastapi
  - react
  - spa
  - kubernetes
  - docker
  - multi-app
entrypoint: deploy-template.sh
language: bash
runtime: bash
dependencies:
  - python3
  - node
  - nginx
ports:
  - dynamic
env:
  - name: BASE_PATH
    description: "URL 路径前缀，默认 /yourapp/"
    required: false
  - name: SERVER_PORT
    description: "后端服务期望端口（被占用时自动递增到空闲端口），默认 9000"
    required: false
  - name: NGINX_PORT
    description: "nginx 对外端口，默认 8080"
    required: false
---

# deploy-anywhere — Web 应用一键部署技能

> 一次配置，到处部署。容器/K8s 环境下 Python FastAPI + React/Vue SPA 的标准部署方案。

## 解决的痛点

在容器/K8s 环境中部署 Web 应用，你会反复遇到这些烦人的问题：

| 问题 | 本技能的解法 |
|------|-------------|
| 远程浏览器自动加 UUID 前缀，路由全炸 | `StripPathPrefixMiddleware` 自动剥离 |
| 多个应用要共用一个域名 | nginx 路径隔离模板，自动检测共存应用 |
| 前端 base 路径跟 nginx 对不上 | deploy.sh 自动 `sed` 替换 vite base 和 API base |
| 端口被占用不敢部署，怕影响其他应用 | **自动查找空闲端口，绝不 kill 任何进程** |
| 多个应用部署时 nginx 配置互相覆盖 | **按应用名独立命名配置文件**（`{{APP_NAME}}.conf`） |

## 核心理念

整套方案就一条数据链：

```
用户 → nginx(NGINX_PORT) → server.py(自动分配的空闲端口) → 你的后端逻辑
                                  ↓
                          frontend/dist/ (SPA 静态文件)
```

三个模板文件覆盖所有场景：

| 文件 | 作用 |
|------|------|
| `deploy-template.sh` | 一键部署脚本（9 步自动化，含智能端口分配） |
| `server-template.py` | FastAPI 一体化服务（API + 静态文件 + SPA fallback + 路径剥离） |
| `nginx-template.conf` | nginx 配置模板（路径隔离模式 + 独占模式，含排查指南） |

## 快速上手

### 第一步：改模板占位符

拿到模板后，全局替换以下占位符：

```
{{APP_NAME}}     → 你的应用名（英文，如 myapp）
{{APP_TITLE}}    → 你的应用标题（中文，如 我的应用）
{{DEFAULT_PATH}} → 默认 URL 前缀（如 /myapp/）
```

可以一键替换：

```bash
sed -i 's/{{APP_NAME}}/myapp/g' server-template.py deploy-template.sh
sed -i 's/{{APP_TITLE}}/我的应用/g' server-template.py deploy-template.sh
sed -i 's/{{DEFAULT_PATH}}/\/myapp\//g' deploy-template.sh
```

### 第二步：放入你的业务代码

1. 把 `server-template.py` 重命名为 `server.py`，在 `# TODO` 区域添加你的 API 路由
2. 把前端代码放入 `frontend/` 目录，确保 `npm run build` 输出到 `frontend/dist/`
3. 如果有 Python 依赖，写入 `backend/requirements.txt`

### 第三步：部署

```bash
chmod +x deploy-template.sh

# 路径隔离模式（与其他应用共存）
./deploy-template.sh /myapp/ 9000 8080

# 独占根路径（唯一应用）
./deploy-template.sh / 9000 8080

# 端口被占用时自动分配空闲端口，无需手动换端口
```

## 部署脚本 9 步流程

```
① 环境检查  → 确认 python3 / node / nginx 就绪
② 安装依赖  → pip install + npm install
③ 配置路径  → sed 自动修改 vite base 和 API base
④ 构建前端  → npm run build
⑤ 端口分配  → 自动检测端口占用，被占时递增查找空闲端口（不 kill 任何进程）
⑥ 清理旧版  → 仅按进程名清理本应用的旧实例，不影响其他应用
⑦ 配置 nginx → 自动检测共存应用，选隔离/独占模式，写入独立配置文件
⑧ 启动服务  → nohup 启动 server.py
⑨ 健康检查  → 直连 + nginx 双重验证
```

## 端口分配策略（核心亮点）

本技能采用 **零破坏** 的端口分配策略：

```
期望端口 9000 → 被占用？
  ├── 否 → 直接使用 9000
  └── 是 → 9001 空闲？
          ├── 是 → 使用 9001
          └── 否 → 9002 空闲？
                  └── ... 递增扫描，最多 100 次
```

**绝不会** kill 占用端口的进程。如果你在其他端口上运行着关键服务，部署新应用时完全不会受到影响。

清理旧进程也采用精确匹配策略——只通过进程名 `python3.*{{APP_NAME}}` 清理本应用的旧实例，不依赖端口号，不会误伤其他应用。

## 两种部署模式

### 路径隔离模式（多应用共存）

```
nginx(8080)
├── /        → 其他应用(5000)
├── /zhique/ → 知雀(自动分配的空闲端口)
└── /admin/  → 后台(自动分配的空闲端口)
```

deploy.sh 会自动检测端口 5000 是否有应用在跑，有则自动选用此模式。

**nginx 配置隔离**：每个应用写入独立的 `/etc/nginx/conf.d/{{APP_NAME}}.conf`，不再共用 `default.conf`，多应用部署互不覆盖。

### 独占模式（单应用）

```
nginx(8080)
└── / → 你的应用(自动分配的空闲端口)
```

端口 5000 无应用时自动选择此模式。

## 路径前缀剥离原理

这是本方案最精妙的部分。在这个容器环境中，有两个来源会给 URL 加前缀：

**来源 1 — 远程浏览器**：自动在路径前插入 UUID
```
用户访问 /api/config
浏览器实际请求 /abc123-def456-.../api/config
                          ↑ UUID 前缀
```

**来源 2 — nginx 分流**：按路径前缀转发
```
用户访问 /zhique/api/config
nginx 转发到 server.py 时保留完整路径 /zhique/api/config
                                        ↑ 自定义前缀
```

`StripPathPrefixMiddleware` 在请求到达路由之前，自动剥离这两种前缀：

```python
# 剥离前: /abc123-def456-.../api/config  或  /zhique/api/config
# 剥离后: /api/config
# 你的路由只需写: @app.get("/api/config")
```

## 常见问题

### 前端 404 / 白屏？

检查 `vite.config.ts` 的 `base` 是否与 nginx 的 `location` 路径一致：
```ts
// vite.config.ts
base: '/myapp/',   // 必须与 nginx location /myapp/ 一致
```

### API 返回 HTML 而非 JSON？

前端 `api.ts` 中的 BASE 常量需要用路径前缀：
```ts
const BASE = '/myapp/api';   // 路径隔离模式
const BASE = '/api';          // 独占模式
```

### 远程浏览器 502？

1. 检查后端是否在运行：`curl http://127.0.0.1:<实际端口>/api/health`
2. 检查 nginx 配置：`nginx -t`
3. 查看日志：`tail -f /tmp/myapp-server.log`

### 端口冲突？

**不用担心，本技能已自动处理。** 如果指定端口被占用，自动递增查找空闲端口。如果要手动指定，传参即可：

```bash
./deploy-template.sh /myapp/ 9001 8080   # 期望端口 9001
./deploy-template.sh /myapp/ 9000 8081   # nginx 换到 8081
```

### 如何查看实际分配的端口？

部署成功后会打印实际端口号：
```
✅ 部署成功！我的应用 已上线
Server:    http://0.0.0.0:9003    ← 实际分配的端口
```

## 适用场景

- 知雀平台容器环境（本方案的诞生地）
- Kubernetes Pod 内多容器共享域名
- Docker Compose 多应用部署
- 任何需要 nginx 反向代理 + 多应用路径隔离的场景
- 需要快速搭建 FastAPI + React SPA 原型的场景

## 技术栈

| 层 | 技术 |
|---|---|
| 反向代理 | nginx |
| 后端框架 | Python FastAPI + Uvicorn |
| 前端框架 | React/Vue + TypeScript + Vite |
| 进程管理 | nohup + pgrep（按进程名精确清理） |
| 端口分配 | 智能递增扫描（零破坏，不 kill 任何进程） |
| 健康检查 | curl 双重验证（直连 + nginx） |

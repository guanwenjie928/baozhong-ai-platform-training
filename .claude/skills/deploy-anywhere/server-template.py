"""
{{APP_NAME}} - 一体化服务器模板
================================
适用场景: 容器/K8s 环境，nginx 反向代理 + FastAPI + React/Vue SPA
核心能力: ① API 路由  ② 静态文件服务  ③ SPA fallback  ④ UUID/路径前缀自动剥离

使用方式:
  1. 替换所有 {{APP_NAME}}、{{APP_TITLE}}、{{SERVER_PORT}} 为实际值
  2. 在 "# -- 你的 API 路由 --" 区域添加业务路由
  3. 前端构建到 frontend/dist/ 目录
  4. python server.py 启动

路径剥离说明:
  - 远程浏览器会自动添加 UUID 前缀: /abc123.../api/xxx → /api/xxx
  - nginx 分流添加 /yourapp/ 前缀:    /yourapp/api/xxx → /api/xxx
  - 两种前缀都会被中间件自动剥离，后端路由只需写 /api/xxx
"""

import re
import sys
import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

# ─── 项目配置 ──────────────────────────────────────────────
ROOT = Path(__file__).parent
DIST_DIR = ROOT / "frontend" / "dist"    # 前端构建产物目录
SERVER_PORT = {{SERVER_PORT}}             # 服务端口（默认 9000）

# ─── 路径前缀剥离中间件 ────────────────────────────────────
# 适配两种场景:
#   场景1: 远程浏览器自动添加 UUID 前缀 → 剥离
#   场景2: nginx 反向代理添加路径前缀 → 剥离
# 后端路由只需关心 /api/xxx，所有前缀在到达路由前已被移除

# UUID 格式: /xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/
UUID_PATTERN = re.compile(
    r'^/[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}/'
)

# 自定义路径前缀（由 nginx 分流时设置，留空则不生效）
CUSTOM_PREFIX = "{{BASE_PATH}}"  # 例如: "/yourapp/"


class StripPathPrefixMiddleware(BaseHTTPMiddleware):
    """自动剥离路径前缀，支持 UUID 和自定义前缀两种模式"""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # 1) 剥离远程浏览器 UUID 前缀
        m = UUID_PATTERN.match(path)
        if m:
            new_path = path[m.end() - 1:]  # 保留开头 /
            request.scope["path"] = new_path
            request.scope["raw_path"] = new_path.encode()
            return await call_next(request)

        # 2) 剥离自定义路径前缀（如 /yourapp/）
        if CUSTOM_PREFIX and CUSTOM_PREFIX != "/" and path.startswith(CUSTOM_PREFIX):
            new_path = path[len(CUSTOM_PREFIX) - 1:]  # 保留开头 /
            request.scope["path"] = new_path
            request.scope["raw_path"] = new_path.encode()

        return await call_next(request)


# ─── FastAPI 应用 ──────────────────────────────────────────
app = FastAPI(title="{{APP_TITLE}}", version="1.0.0")

app.add_middleware(StripPathPrefixMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ════════════════════════════════════════════════════════════
#  你的 API 路由 —— 在这里添加业务逻辑
# ════════════════════════════════════════════════════════════

@app.get("/api/health")
async def health_check():
    """健康检查接口（必须保留，deploy.sh 依赖此接口验证部署）"""
    return JSONResponse({"status": "ok", "app": "{{APP_NAME}}"})


# TODO: 在此处添加你的业务路由
# @app.post("/api/your-endpoint")
# async def your_handler(...):
#     ...


# ════════════════════════════════════════════════════════════
#  前端静态文件 & SPA fallback（无需修改）
# ════════════════════════════════════════════════════════════

@app.get("/{path:path}")
async def serve_frontend(path: str):
    """服务前端静态文件，非 API 路径回退到 SPA index.html"""

    # 防止 API 路径被 catch-all 误捕获
    if path.startswith("api/"):
        return JSONResponse({"detail": "API endpoint not found"}, status_code=404)

    file_path = DIST_DIR / path
    if file_path.exists() and file_path.is_file():
        return FileResponse(file_path)

    # SPA fallback
    index_path = DIST_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)

    return JSONResponse(
        {"message": "前端文件未找到，请先构建: cd frontend && npm run build"},
        status_code=404,
    )


# ─── 启动入口 ──────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=SERVER_PORT)

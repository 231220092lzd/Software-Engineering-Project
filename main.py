# main.py (最终修正版)

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# 导入所有模块
from api import products, users, sellers, recommendations
import models
from database import engine

# 创建数据库表
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="全栈电商平台",
    description="一个集成了前端和后端的电商服务。",
    version="1.3.0",
)

# --- CORS中间件配置 ---
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 1. 挂载API路由 ---
# (所有 /api/... 的请求都会被转发到这里)
api_router = FastAPI()
api_router.include_router(users.router)
api_router.include_router(products.router)
api_router.include_router(sellers.router)
api_router.include_router(recommendations.router)
# 错误修正：移除了多余的 api_router.include_router()
app.mount("/api", api_router)


# --- 2. 为每个HTML页面创建专门的路由 ---
# (这部分必须在下面的 StaticFiles 挂载之前)

@app.get("/", response_class=FileResponse, tags=["Frontend Pages"])
async def serve_login_page():
    return "frontend/login.html"

@app.get("/register.html", response_class=FileResponse, tags=["Frontend Pages"])
async def serve_register_page():
    return "frontend/register.html"

@app.get("/product-list.html", response_class=FileResponse, tags=["Frontend Pages"])
async def serve_product_list_page():
    return "frontend/product-list.html"

@app.get("/product-detail.html", response_class=FileResponse, tags=["Frontend Pages"])
async def serve_product_detail_page():
    return "frontend/product-detail.html"

@app.get("/favorites.html", response_class=FileResponse, tags=["Frontend Pages"])
async def serve_favorites_page():
    """
    这个路由就是用来处理“我的收藏”页面请求的。
    当用户点击链接访问 /favorites.html 时，这个函数会被触发，
    并以正确的 HTML 格式返回文件。
    """
    return "frontend/favorites.html"

@app.get("/coupon.html", response_class=FileResponse, tags=["Frontend Pages"])
async def serve_coupon_page():
    return "frontend/coupon.html"


# --- 3. 挂载静态文件目录 ---
# (这个必须放在所有精确的HTML页面路由之后)
app.mount("/", StaticFiles(directory="frontend"), name="static")


# --- 4. 启动事件 ---
# 错误修正：合并了两个重复的 startup 事件
@app.on_event("startup")
def startup_event():
    # 这里可以放你的种子数据填充逻辑（如果需要的话）
    print("应用已启动!")
    print("访问 http://127.0.0.1:8000 进入登录页面")
    print("API文档位于 http://127.0.0.1:8000/api/docs")


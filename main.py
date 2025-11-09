import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles  # 1. 导入StaticFiles
from fastapi.responses import FileResponse   # 2. 导入FileResponse

from api import products, users, sellers, recommendations

app = FastAPI(
    title="全栈电商平台",
    description="一个集成了前端和后端的电商服务。",
    version="1.3.0",
)

# --- CORS配置 (保持不变) ---
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 3. 挂载API路由 (把所有API都放在一个前缀下，避免冲突) ---
# 这样做的好处是，所有API请求都以 /api/ 开头，
# 不会和前端页面的路径 (如 /product-list.html) 发生冲突。
api_router = FastAPI()
api_router.include_router(users.router)
api_router.include_router(products.router)
api_router.include_router(sellers.router)
api_router.include_router(recommendations.router)
app.mount("/api", api_router)


# --- 4. 创建一个端点，当用户访问根路径 ("/") 时，返回登录页面 ---
@app.get("/", response_class=FileResponse)
async def serve_login_page():
    # FileResponse会读取文件并将其作为HTTP响应返回
    # 浏览器会将其渲染为HTML页面
    return "frontend/login.html"

# --- 5. 挂载静态文件目录 ---
# 这会让FastAPI自动处理所有对 "frontend" 文件夹中文件的请求
# 例如，浏览器请求 /product-list.html 时，FastAPI会找到并返回 frontend/product-list.html 文件
app.mount("/", StaticFiles(directory="frontend"), name="static")


# --- 简单的启动信息 ---
@app.on_event("startup")
def startup_event():
    print("应用已启动!")
    print("访问 http://127.0.0.1:8000 进入登录页面")
    print("API文档位于 http://127.0.0.1:8000/api/docs")


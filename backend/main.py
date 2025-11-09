# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # 导入CORS中间件
from api import products, users, sellers, recommendations

app = FastAPI(
    title="轻量级电商平台 API",
    description="一个专注于促成买卖双方联系的电商平台后端服务。",
    version="1.0.0",
)

# --- 新增代码：配置CORS ---
# 定义允许的源列表，"*" 表示允许所有源
origins = [
    "*", 
    # 在生产环境中，应该指定具体的前端域名，例如:
    # "http://localhost",
    # "http://127.0.0.1",
    # "http://example.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # 允许所有HTTP方法
    allow_headers=["*"], # 允许所有HTTP头
)
# --- 新增代码结束 ---


# 包含各个模块的路由
app.include_router(users.router)
app.include_router(products.router)
app.include_router(sellers.router)
app.include_router(recommendations.router)

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "欢迎使用电商平台API，请访问 /docs 查看API文档。"}

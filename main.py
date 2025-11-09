# main.py
from fastapi import FastAPI
from api import products, users, sellers, recommendations

app = FastAPI(
    title="轻量级电商平台 API",
    description="一个专注于促成买卖双方联系的电商平台后端服务。",
    version="1.0.0",
)

# 包含各个模块的路由
app.include_router(users.router)
app.include_router(products.router)
app.include_router(sellers.router)
app.include_router(recommendations.router)

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "欢迎使用电商平台API，请访问 /docs 查看API文档。"}

# 此处可添加后台管理模块（Req003）的路由，为简化暂略
# from api import admin
# app.include_router(admin.router)

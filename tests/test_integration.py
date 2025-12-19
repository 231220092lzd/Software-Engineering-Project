import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models
from database import get_db
from fastapi import FastAPI

# 导入所有需要测试的路由
from api.users import router as users_router
from api.products import router as products_router
from api.sellers import router as sellers_router
from api.recommendations import router as recommendations_router
from api.admin import router as admin_router

# 为集成测试创建一个完整的应用（包含更多路由）
app = FastAPI()
app.include_router(users_router, prefix="/api")
app.include_router(products_router, prefix="/api")
app.include_router(sellers_router, prefix="/api")
app.include_router(recommendations_router, prefix="/api")
app.include_router(admin_router, prefix="/api")

# 使用 SQLite 内存数据库作为测试数据库（可在跨线程中共享）
TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 在内存 DB 中创建表
models.Base.metadata.create_all(bind=engine)

@pytest.fixture(scope="function")
def db_session():
    # 每个测试保证干净的表结构
    models.Base.metadata.drop_all(bind=engine)
    models.Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture(scope="function")
def client(db_session):
    def _get_test_db():
        try:
            yield db_session
        finally:
            db_session.rollback()

    # 覆写应用的依赖项
    app.dependency_overrides[get_db] = _get_test_db
    with TestClient(app) as c:
        yield c


def test_end_to_end_publish_favorite_and_delete(client):
    # 创建商家
    payload_seller = {"shop_name": "集成测试商家", "contact_info": "seller@example.test"}
    r = client.post("/api/sellers/", json=payload_seller)
    assert r.status_code == 201
    seller = r.json()

    # 发布商品
    payload_product = {"name": "集成商品", "price": 12.34, "description": "desc", "image_url": "img"}
    r2 = client.post(f"/api/products/?seller_id={seller['id']}", json=payload_product)
    assert r2.status_code == 201
    prod = r2.json()

    # 注册用户
    payload_user = {"username": "int_user", "password": "pwd12345"}
    r3 = client.post("/api/users/register", json=payload_user)
    assert r3.status_code == 201
    user = r3.json()

    # 添加收藏
    r4 = client.post(f"/api/users/{user['id']}/favorites/{prod['id']}")
    assert r4.status_code == 201
    assert r4.json()["status"] == "success"

    # 确认收藏在用户收藏列表中
    r5 = client.get(f"/api/users/{user['id']}/favorites")
    assert r5.status_code == 200
    favs = r5.json()
    assert any(item['id'] == prod['id'] for item in favs)

    # 管理员删除该商品
    r6 = client.delete(f"/api/admin/products/{prod['id']}")
    assert r6.status_code == 204

    # 商品详情应返回 404
    r7 = client.get(f"/api/products/{prod['id']}")
    assert r7.status_code == 404

    # 收藏列表中不应再包含已删除商品
    r8 = client.get(f"/api/users/{user['id']}/favorites")
    assert r8.status_code == 200
    favs2 = r8.json()
    assert not any(item['id'] == prod['id'] for item in favs2)


def test_recommendations_returns_created_products(client):
    # 创建商家
    payload_seller = {"shop_name": "rec_seller", "contact_info": "rec@example.test"}
    r = client.post("/api/sellers/", json=payload_seller)
    assert r.status_code == 201
    seller = r.json()

    # 创建多个商品
    created = []
    for i in range(3):
        payload_product = {"name": f"商品_{i}", "price": 10 + i, "description": "x", "image_url": "img"}
        pr = client.post(f"/api/products/?seller_id={seller['id']}", json=payload_product)
        assert pr.status_code == 201
        created.append(pr.json())

    # 请求推荐
    r2 = client.get("/api/recommendations/")
    assert r2.status_code == 200
    recs = r2.json()
    # 至少包含我们刚创建的3个商品中的一部分（顺序/数量不强依赖）
    rec_ids = {p['id'] for p in recs}
    assert any(p['id'] in rec_ids for p in created)

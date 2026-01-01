import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import bcrypt # 需要导入 bcrypt 来创建管理员密码

import models
from database import get_db
from fastapi import FastAPI

# 导入所有需要测试的路由
from api.users import router as users_router
from api.products import router as products_router
from api.sellers import router as sellers_router
from api.recommendations import router as recommendations_router
from api.admin import router as admin_router

# 为集成测试创建一个完整的应用
app = FastAPI()
app.include_router(users_router, prefix="/api")
app.include_router(products_router, prefix="/api")
app.include_router(sellers_router, prefix="/api")
app.include_router(recommendations_router, prefix="/api")
app.include_router(admin_router, prefix="/api")

# 使用 SQLite 内存数据库
TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

models.Base.metadata.create_all(bind=engine)

@pytest.fixture(scope="function")
def db_session():
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

    app.dependency_overrides[get_db] = _get_test_db
    with TestClient(app) as c:
        yield c

# 注意：这里增加了 db_session 参数，以便直接操作数据库创建管理员
def test_end_to_end_publish_favorite_and_delete(client, db_session):
    # 1. 创建商家
    payload_seller = {"shop_name": "集成测试商家", "contact_info": "seller@example.test"}
    r = client.post("/api/sellers/", json=payload_seller)
    assert r.status_code == 201
    seller = r.json()

    # 2. 发布商品 (假设此接口仍未加锁，或者是商家端接口)
    payload_product = {"name": "集成商品", "price": 12.34, "description": "desc", "image_url": "img"}
    r2 = client.post(f"/api/products/?seller_id={seller['id']}", json=payload_product)
    assert r2.status_code == 201
    prod = r2.json()

    # 3. 注册普通用户
    payload_user = {"username": "int_user", "password": "pwd12345"}
    r3 = client.post("/api/users/register", json=payload_user)
    assert r3.status_code == 201
    user = r3.json()

    # 4. 普通用户登录获取 token
    login = client.post("/api/users/login", json={"username": payload_user["username"], "password": payload_user["password"]})
    assert login.status_code == 200
    user_token = login.json()["access_token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}

    # 5. 添加收藏 (修复点：URL 不再包含 user['id'])
    r4 = client.post(f"/api/users/favorites/{prod['id']}", headers=user_headers)
    assert r4.status_code == 201
    assert r4.json()["status"] == "success"

    # 6. 确认收藏在用户收藏列表中 (修复点：URL 不再包含 user['id'])
    r5 = client.get(f"/api/users/favorites", headers=user_headers)
    assert r5.status_code == 200
    favs = r5.json()
    assert any(item['id'] == prod['id'] for item in favs)

    # --- 修复点开始：管理员操作 ---
    
    # 7. 创建管理员账号 (因为 admin 接口现在有权限验证)
    salt = bcrypt.gensalt()
    hashed_pwd = bcrypt.hashpw(b"admin_pass", salt).decode('utf-8')
    admin_user = models.User(username="admin_integ", hashed_password=hashed_pwd, role="admin")
    db_session.add(admin_user)
    db_session.commit()

    # 8. 管理员登录
    admin_login = client.post("/api/users/login", json={"username": "admin_integ", "password": "admin_pass"})
    assert admin_login.status_code == 200
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 9. 管理员删除该商品 (修复点：带上 admin header)
    r6 = client.delete(f"/api/admin/products/{prod['id']}", headers=admin_headers)
    assert r6.status_code == 204

    # --- 修复点结束 ---

    # 10. 商品详情应返回 404
    r7 = client.get(f"/api/products/{prod['id']}")
    assert r7.status_code == 404

    # 11. 收藏列表中不应再包含已删除商品 
    # (修复点：URL 修正，且必须带上 user_headers，因为 get_favorites 现在需要认证)
    r8 = client.get(f"/api/users/favorites", headers=user_headers)
    assert r8.status_code == 200
    favs2 = r8.json()
    assert not any(item['id'] == prod['id'] for item in favs2)


def test_recommendations_returns_created_products(client):
    # 这个测试基本不需要变，只要 recommendations 接口是公开的
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
    
    rec_ids = {p['id'] for p in recs}
    assert any(p['id'] in rec_ids for p in created)

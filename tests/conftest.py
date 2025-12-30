import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import models
from database import get_db
from fastapi import FastAPI
from api.users import router as users_router
from api.products import router as products_router

# 为测试创建一个最小化的 FastAPI 应用，只包含用户与商品路由，避免导入可选的第三方依赖（如 openai）
app = FastAPI()
# 路由已在各自模块中声明前缀，这里统一挂到 /api 下
app.include_router(users_router, prefix="/api")
app.include_router(products_router, prefix="/api")

# 使用 SQLite 内存数据库作为测试数据库
from sqlalchemy.pool import StaticPool

TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
# 使用 StaticPool 使同一个内存数据库可以跨线程/连接共享（适用于测试）
engine = create_engine(
    TEST_SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 在内存 DB 中创建所有表
models.Base.metadata.create_all(bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """为每个测试函数提供一个新的 DB 会话，并在会话开始前确保表已创建"""
    # 清理并在测试引擎上重建表结构，确保每个测试用例的数据库是干净的
    models.Base.metadata.drop_all(bind=engine)
    models.Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture(scope="function")
def client(db_session):
    """提供一个 TestClient，并覆写应用的 get_db 依赖以使用测试会话"""
    def _get_test_db():
        try:
            yield db_session
        finally:
            db_session.rollback()

    app.dependency_overrides[get_db] = _get_test_db
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="function")
def seed_data(db_session):
    """在每个测试中填充基础数据：一个商家、两件商品和一个用户"""
    from api.users import get_password_hash

    seller = models.Seller(shop_name="测试商家", contact_info="test@seller.local")
    db_session.add(seller)
    db_session.commit()
    db_session.refresh(seller)

    p1 = models.Product(name="商品A", price=100.0, description="描述A", seller_id=seller.id, image_url="url_A")
    p2 = models.Product(name="商品B", price=200.0, description="描述B", seller_id=seller.id, image_url="url_B")
    db_session.add_all([p1, p2])
    db_session.commit()

    # 添加一个普通用户 alice，密码为 password123
    hashed = get_password_hash("password123")
    user = models.User(username="alice", hashed_password=hashed.decode('utf-8'))
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # 返回创建的实体以备测试使用
    return {
        "seller": seller,
        "products": [p1, p2],
        "user": user
    }
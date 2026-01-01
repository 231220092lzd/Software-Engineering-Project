import pytest
from api import users

def test_get_password_hash_and_verify():
    pwd = "mysecret"
    hashed = users.get_password_hash(pwd)
    assert isinstance(hashed, (bytes, bytearray))
    assert users.verify_password(pwd, hashed)
    assert not users.verify_password("wrong", hashed)


def test_register_creates_user(client, seed_data):
    payload = {"username": "bob", "password": "pass1234"}
    r = client.post("/api/users/register", json=payload)
    assert r.status_code == 201
    data = r.json()
    assert data["username"] == "bob"
    assert "id" in data


def test_register_existing_username(client, seed_data):
    # alice 已由 seed_data 创建
    payload = {"username": "alice", "password": "password123"}
    r = client.post("/api/users/register", json=payload)
    assert r.status_code == 400
    assert r.json()["detail"] == "Username already registered"


def test_login_admin(client, seed_data):
    payload = {"username": "root", "password": "root123"}
    r = client.post("/api/users/login", json=payload)
    assert r.status_code == 200
    assert r.json()["role"] == "admin"
    assert r.json()["user_id"] == seed_data["admin"].id


def test_login_user_success(client, seed_data):
    payload = {"username": "alice", "password": "password123"}
    r = client.post("/api/users/login", json=payload)
    assert r.status_code == 200
    assert r.json()["role"] == "customer"
    assert r.json()["user_id"] == seed_data["user"].id


def test_login_invalid_credentials(client, seed_data):
    payload = {"username": "alice", "password": "wrongpass"}
    r = client.post("/api/users/login", json=payload)
    assert r.status_code == 401


def test_add_and_get_and_remove_favorite(client, seed_data):
    user = seed_data["user"]
    p1 = seed_data["products"][0]

    # 登录获取 token
    login_resp = client.post("/api/users/login", json={"username": user.username, "password": "password123"})
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 添加收藏 (修复点：URL 不再包含 user.id)
    r = client.post(f"/api/users/favorites/{p1.id}", headers=headers)
    assert r.status_code == 201
    assert r.json()["status"] == "success"

    # 重复添加应返回 400
    r2 = client.post(f"/api/users/favorites/{p1.id}", headers=headers)
    assert r2.status_code == 400

    # 获取收藏列表 (修复点：URL 不再包含 user.id)
    r3 = client.get(f"/api/users/favorites", headers=headers)
    assert r3.status_code == 200
    favs = r3.json()
    assert isinstance(favs, list)
    assert any(item["id"] == p1.id for item in favs)

    # 删除收藏 (修复点：URL 不再包含 user.id)
    r4 = client.delete(f"/api/users/favorites/{p1.id}", headers=headers)
    assert r4.status_code == 204

    # 再删除一次（不存在）仍然返回 204
    r5 = client.delete(f"/api/users/favorites/{p1.id}", headers=headers)
    assert r5.status_code == 204


def test_add_favorite_product_not_found(client, seed_data):
    # 修复点：添加了 seed_data 参数，确保 admin 用户存在
    admin = seed_data["admin"]
    login_resp = client.post("/api/users/login", json={"username": admin.username, "password": "root123"})
    headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}
    
    # 测试添加不存在的商品 ID
    r = client.post(f"/api/users/favorites/9999", headers=headers)
    assert r.status_code == 404
    assert r.json()['detail'] == "Product not found"


# 原 test_get_favorites_user_not_found 已废弃
# 因为现在的 API 结构 /users/favorites 隐式使用 Token 中的 ID，
# 不存在 "URL 中的 User ID 不存在" 这种 404 错误。
# 如果 Token 无效，会返回 401。

def test_access_favorites_without_token(client):
    # 测试未登录访问收藏
    r = client.get("/api/users/favorites")
    assert r.status_code == 401

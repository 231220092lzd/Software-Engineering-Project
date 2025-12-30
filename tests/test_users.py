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


def test_login_admin_hardcoded(client, seed_data):
    payload = {"username": "root", "password": "root123"}
    r = client.post("/api/users/login", json=payload)
    assert r.status_code == 200
    assert r.json()["role"] == "admin"
    assert r.json()["user_id"] == 0


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

    # 添加收藏
    r = client.post(f"/api/users/{user.id}/favorites/{p1.id}")
    assert r.status_code == 201
    assert r.json()["status"] == "success"

    # 重复添加应返回 400
    r2 = client.post(f"/api/users/{user.id}/favorites/{p1.id}")
    assert r2.status_code == 400

    # 获取收藏列表
    r3 = client.get(f"/api/users/{user.id}/favorites")
    assert r3.status_code == 200
    favs = r3.json()
    assert isinstance(favs, list)
    assert any(item["id"] == p1.id for item in favs)

    # 删除收藏
    r4 = client.delete(f"/api/users/{user.id}/favorites/{p1.id}")
    assert r4.status_code == 204

    # 再删除一次（不存在）仍然返回 204
    r5 = client.delete(f"/api/users/{user.id}/favorites/{p1.id}")
    assert r5.status_code == 204


def test_add_favorite_user_or_product_not_found(client, seed_data):
    r = client.post(f"/api/users/9999/favorites/9999")
    assert r.status_code == 404


def test_get_favorites_user_not_found(client):
    r = client.get(f"/api/users/9999/favorites")
    assert r.status_code == 404


def test_remove_favorite_user_or_product_not_found(client):
    r = client.delete(f"/api/users/9999/favorites/9999")
    assert r.status_code == 404

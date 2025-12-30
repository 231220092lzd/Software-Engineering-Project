import pytest


def test_get_products_basic_and_sorting(client, seed_data):
    # 不带排序
    r = client.get("/api/products/")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) >= 2

    # 按价格升序
    r2 = client.get("/api/products/?sort_by=price_asc")
    assert r2.status_code == 200
    prices = [p["price"] for p in r2.json()]
    assert prices == sorted(prices)

    # 按价格降序
    r3 = client.get("/api/products/?sort_by=price_desc")
    assert r3.status_code == 200
    prices_desc = [p["price"] for p in r3.json()]
    assert prices_desc == sorted(prices_desc, reverse=True)


def test_get_product_details_success_and_404(client, seed_data):
    p1 = seed_data["products"][0]

    r = client.get(f"/api/products/{p1.id}")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == p1.id
    assert data["name"] == p1.name

    r2 = client.get("/api/products/9999")
    assert r2.status_code == 404


def test_publish_product_success_and_seller_not_found(client, seed_data):
    seller = seed_data["seller"]
    payload = {"name": "新商品", "price": 55.5, "description": "赫赫", "image_url": "img"}
    r = client.post(f"/api/products/?seller_id={seller.id}", json=payload)
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "新商品"
    assert data["seller_id"] == seller.id

    # seller 不存在
    r2 = client.post(f"/api/products/?seller_id=9999", json=payload)
    assert r2.status_code == 404


def test_comments_basic_flow(client, seed_data):
    p1 = seed_data["products"][0]

    # 初始评论为空
    r = client.get(f"/api/products/{p1.id}/comments")
    assert r.status_code == 200
    assert r.json() == []

    # 添加评论
    payload = {"content": "这是一个很有帮助的评论"}
    r2 = client.post(f"/api/products/{p1.id}/comments", json=payload)
    assert r2.status_code == 201
    c = r2.json()
    assert c["content"] == payload["content"]
    assert c["product_id"] == p1.id

    # 添加到不存在商品
    r3 = client.post(f"/api/products/9999/comments", json=payload)
    assert r3.status_code == 404

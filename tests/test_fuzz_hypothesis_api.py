import os
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck

# 使用 fixtures 中的 client 和 seed_data

# 允许通过环境变量控制每个测试的示例数量，便于在 CI 中短跑与长跑之间切换
MAX_EXAMPLES = int(os.getenv("HYPOTHESIS_MAX_EXAMPLES", "100"))

# 一些通用设置，禁用 deadline 以避免 CI 环境的网络延迟导致虚假失败
# 并抑制使用 function-scoped fixture 的 health check（TestClient fixture 是函数作用域）
hypothesis_settings = settings(max_examples=MAX_EXAMPLES, deadline=None, suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture])


@hypothesis_settings
@given(username=st.text(max_size=300), password=st.text(max_size=300))
def test_fuzz_register(username, password, client):
    """对 /api/users/register 进行模糊测试，主要关注是否产生 5xx 崩溃"""
    resp = client.post("/api/users/register", json={"username": username, "password": password})
    # 关注：不应产生 5xx
    assert resp.status_code < 500


@hypothesis_settings
@given(username=st.text(max_size=300), password=st.text(max_size=300))
def test_fuzz_login(username, password, client):
    """对 /api/users/login 进行模糊测试"""
    resp = client.post("/api/users/login", json={"username": username, "password": password})
    assert resp.status_code < 500


@hypothesis_settings
@given(
    name=st.text(max_size=200),
    price=st.floats(allow_nan=False, allow_infinity=False, width=32),
    description=st.text(max_size=500),
    image_url=st.text(max_size=300)
)
def test_fuzz_publish_product(name, price, description, image_url, client, seed_data):
    """对商家发布商品接口进行模糊测试（使用 seed 中的 seller_id=1）"""
    payload = {
        "name": name,
        "price": price if price is not None else 0.0,
        "description": description,
        "image_url": image_url
    }
    resp = client.post("/api/products/?seller_id=1", json=payload)
    assert resp.status_code < 500


@hypothesis_settings
@given(product_id=st.integers(min_value=-100000, max_value=1000000))
def test_fuzz_get_product_details(product_id, client):
    """对 /api/products/{product_id} 的路径参数进行边界/畸形值测试"""
    resp = client.get(f"/api/products/{product_id}")
    assert resp.status_code < 500


@hypothesis_settings
@given(content=st.text(min_size=0, max_size=1000))
def test_fuzz_comments(content, client, seed_data):
    """对添加评论接口进行 fuzz（会尝试使用 seed 中第一个 product）"""
    product = seed_data["products"][0]
    resp = client.post(f"/api/products/{product.id}/comments", json={"content": content})
    assert resp.status_code < 500

import os
import time
from hypothesis import given, strategies as st, settings, HealthCheck
import pytest

# 使用与之前相同的 Hypothesis 设置
MAX_EXAMPLES = int(os.getenv("HYPOTHESIS_MAX_EXAMPLES", "200"))
settings_common = settings(max_examples=MAX_EXAMPLES, deadline=None, suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture])

# 更丰富的 payload 列表（SQLi/XSS/路径遍历/二进制/长载荷/格式化字符串等）
PAYLOADS = [
    "' OR '1'='1' -- ",
    "' OR '1'='1' /*comment*/ --",
    "\" OR \"\"=\"\" --",
    "<script>alert(1)</script>",
    "<img src=x onerror=alert(1)>",
    "../../../../etc/passwd",
    r"..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
    "\x00\x00\x00",
    "${@print('x')}",
    '\" onmouseover=alert(1) \"',
    "' OR sleep(5)--",
    '"); DROP TABLE users; --',
    "1; DROP TABLE users;",
    "admin' --",
    "' UNION SELECT NULL,NULL--",
    "\"; EXEC xp_cmdshell('whoami') --",
    "../../../../proc/self/environ",
    "../../../../etc/shadow",
    "../../../../var/www/html/index.php",
    "\"; cat /etc/passwd; #",
    "\xEF\xBB\xBF<svg onload=alert(1)>",
    "<svg><script>alert(1)</script></svg>",
    "\u202E\u202E\u202E",  # 方向重排字符
    "\"; sleep(2); \"",
    "✨🔥🚀",
]

# 一些超长/高熵载荷
LONG_PAYLOADS = ["A" * 1024, "B" * 4096, "C" * 20000]

# 一些二进制或非 UTF-8 载荷
BINARY_PAYLOADS = [b"\x00\xff\xfe\x00", b"\x90" * 100]

# 会尝试在 headers 中注入 payload
HEADER_KEYS = ["User-Agent", "Referer", "X-Forwarded-For"]


# 输出失败用例到此目录便于最小化与复现
FAIL_DIR = os.path.join(os.path.dirname(__file__), "fuzz_failures")
os.makedirs(FAIL_DIR, exist_ok=True)


def record_failure(test_name, payload, resp):
    ts = int(time.time())
    fname = os.path.join(FAIL_DIR, f"{test_name}_{ts}.txt")
    with open(fname, "w", encoding="utf-8") as f:
        f.write(f"TEST: {test_name}\n")
        f.write(f"PAYLOAD: {repr(payload)}\n")
        f.write(f"STATUS: {resp.status_code}\n")
        f.write("HEADERS:\n")
        for k, v in resp.headers.items():
            f.write(f"{k}: {v}\n")
        f.write("\nBODY:\n")
        try:
            f.write(resp.text)
        except Exception as e:
            f.write(f"<could not decode body: {e}>")


# 检测器：判断响应中是否包含明显的 SQL 错误指纹
SQL_ERROR_MARKERS = [
    "sqlalchemy",
    "operationalerror",
    "syntaxerror",
    "mysql",
    "sqlite3",
    "traceback",
    "exception",
]

# 检测器：判断是否成功读取了敏感文件（/etc/passwd 的常见模式）
FILE_READ_MARKERS = [
    "root:",
    "daemon:",
    "127.0.0.1",
    "localhost",
    "[global]",
]


def analyze_and_record(test_name, payload, resp):
    text = (resp.text or "").lower()
    # SQL 错误指纹
    if any(marker in text for marker in SQL_ERROR_MARKERS):
        record_failure(f"{test_name}_sql_err", payload, resp)
    # 文件读取指纹
    if any(marker in text for marker in FILE_READ_MARKERS):
        record_failure(f"{test_name}_file_read", payload, resp)
    # 反射 XSS 简单检测：payload 含 <script> 或 <svg> 并且出现在响应中
    if isinstance(payload, str) and ("<script" in payload.lower() or "<svg" in payload.lower()):
        if payload.lower() in text:
            record_failure(f"{test_name}_reflect_xss", payload, resp)



@settings_common
@given(payload=st.one_of(st.sampled_from(PAYLOADS + LONG_PAYLOADS), st.text(max_size=2000)))
def test_security_fuzz_register(payload, client):
    headers = {}
    # 只在 payload 为纯 ASCII 时注入到 headers，避免 httpx 头部编码错误
    if isinstance(payload, str) and all(ord(c) < 128 for c in payload):
        headers = {k: payload for k in HEADER_KEYS}
    resp = client.post("/api/users/register", json={"username": payload, "password": payload}, headers=headers)
    # 记录 server error 或 可疑响应
    if resp.status_code >= 500:
        record_failure("register_5xx", payload, resp)
    analyze_and_record("register", payload, resp)
    assert resp.status_code < 500


@settings_common
@given(payload=st.one_of(st.sampled_from(PAYLOADS + LONG_PAYLOADS), st.text(max_size=2000)))
def test_security_fuzz_login(payload, client):
    headers = {k: payload for k in HEADER_KEYS if isinstance(payload, str)}
    resp = client.post("/api/users/login", json={"username": payload, "password": payload}, headers=headers)
    if resp.status_code >= 500:
        record_failure("login_5xx", payload, resp)
    analyze_and_record("login", payload, resp)
    assert resp.status_code < 500


@settings_common
@given(payload=st.one_of(st.sampled_from(PAYLOADS + LONG_PAYLOADS), st.text(max_size=2000)))
def test_security_fuzz_publish(payload, client, seed_data):
    headers = {}
    if isinstance(payload, str) and all(ord(c) < 128 for c in payload):
        headers = {k: payload for k in HEADER_KEYS}
    product = {"name": payload, "price": 1.23, "description": payload, "image_url": payload}
    # 尝试多种 seller_id（验证权限/验证缺陷）
    for seller_id in [1, -1, 0, 99999]:
        resp = client.post(f"/api/products/?seller_id={seller_id}", json=product, headers=headers)
        if resp.status_code >= 500:
            record_failure("publish_5xx", payload, resp)
        analyze_and_record("publish", payload, resp)
        assert resp.status_code < 500


@settings_common
@given(payload=st.one_of(st.sampled_from(PAYLOADS + LONG_PAYLOADS), st.text(max_size=2000)))
def test_security_fuzz_comments(payload, client, seed_data):
    headers = {k: payload for k in HEADER_KEYS if isinstance(payload, str)}
    product = seed_data["products"][0]
    resp = client.post(f"/api/products/{product.id}/comments", json={"content": payload}, headers=headers)
    if resp.status_code >= 500:
        record_failure("comments_5xx", payload, resp)
    analyze_and_record("comments", payload, resp)


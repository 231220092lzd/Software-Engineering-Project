import frelatage
from frelatage import Input
import os
import sys
from fastapi.testclient import TestClient
from sqlalchemy import text
import models
from database import engine, SessionLocal, Base
from main import app

# --- 1. 配置环境 ---
# 增加递归深度，防止某些深度递归的 Bug 导致 Fuzzer 自身崩溃
sys.setrecursionlimit(2000)

# 初始化 TestClient
client = TestClient(app)

# --- 2. 数据库初始化工具 ---
def setup_database():
    """
    初始化数据库：清空重建并注入基础种子数据
    """
    print("--- [Setup] 初始化数据库 ---")
    db = SessionLocal()
    try:
        # MySQL 特有的外键检查关闭
        if "mysql" in engine.url.drivername:
            with engine.connect() as connection:
                connection.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
                connection.commit()
        
        Base.metadata.drop_all(bind=engine)

        if "mysql" in engine.url.drivername:
            with engine.connect() as connection:
                connection.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
                connection.commit()
        
        Base.metadata.create_all(bind=engine)
        
        # 注入一个商家用于测试
        seller = models.Seller(shop_name="Fuzz Seller", contact_info="fuzz@test.com")
        db.add(seller)
        db.commit()
        print(f"--- [Setup] 商家已创建 ID: {seller.id} ---")
        
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        sys.exit(1)
    finally:
        db.close()

# --- 3. 目标函数 1: 测试商品发布接口 ---

@frelatage.instrument
def fuzz_publish_product(name, price_input, description, image_url):
    """
    测试 /api/products/ 接口
    注意：我们允许 price_input 为任意字符串，测试 Pydantic 解析能力
    """
    # 构造 Payload
    # 注意：这里不进行 float() 转换，直接传给 API，看它是否会因为奇怪的类型崩溃
    payload = {
        "name": str(name),
        "price": price_input, # Fuzzer 可能会生成非数字字符串
        "description": str(description),
        "image_url": str(image_url)
    }
    
    # 发送请求 (假设 seller_id=1 存在)
    try:
        response = client.post("/api/products/?seller_id=1", json=payload)
        
        # 逻辑检查
        # 5xx: 服务器崩溃 (Bug)
        if response.status_code >= 500:
            # 打印导致崩溃的 payload 方便调试
            print(f"\n[CRASH DETECTED] Payload: {payload}")
            raise RuntimeError(f"Server Error 500! Body: {response.text}")
            
    except Exception as e:
        # 如果是 RuntimeError (上面的 500) 则抛出，让 Frelatage 记录
        if "Server Error 500" in str(e):
            raise e
        # 其他网络库层面的错误通常忽略，继续下一次 Fuzz
        pass

# --- 4. 目标函数 2: 测试用户注册接口 ---

@frelatage.instrument
def fuzz_user_register(username, password):
    """
    测试 /api/users/register 接口
    重点测试：超长字符串导致的哈希计算溢出、特殊字符导致的 SQL 注入(虽然用了ORM)
    """
    payload = {
        "username": str(username),
        "password": str(password)
    }
    
    try:
        response = client.post("/api/users/register", json=payload)
        
        if response.status_code >= 500:
            print(f"\n[CRASH DETECTED] Register Payload: {payload}")
            raise RuntimeError(f"Register 500 Error! Body: {response.text}")
            
    except Exception as e:
        if "Register 500 Error" in str(e):
            raise e
        pass

# --- 5. 主程序 ---

if __name__ == "__main__":
    # 1. 初始化数据库
    setup_database()

    print("\n🚀 开始 Fuzzing 测试...\n")
    
    # 2. 从环境变量读取要测试的目标，实现分模块测试
    # 默认测试商品发布
    target = os.getenv("FUZZ_TARGET", "product")

    if target == "product":
        print(">>> 正在 Fuzzing: 商品发布接口 (Publish Product)")
        # 语料库：必须是 [ [arg1, arg2, arg3, arg4], ... ] 的格式
        samples = [
            [
                Input(value="Normal Phone"), 
                Input(value="199.9"), # 正常数字
                Input(value="A good phone"), 
                Input(value="http://img.com")
            ],
            [
                Input(value="<script>alert(1)</script>"), # XSS 尝试
                Input(value="NOT_A_NUMBER"), # 类型错误尝试
                Input(value="A" * 1000), # 缓冲区溢出尝试
                Input(value="")
            ]
        ]
        
        f = frelatage.Fuzzer(fuzz_publish_product, samples)
        # infinite_fuzz=True 会一直运行直到手动停止或发现 Crash
        f.fuzz()

    elif target == "user":
        print(">>> 正在 Fuzzing: 用户注册接口 (User Register)")
        samples = [
            [
                Input(value="test_user"),
                Input(value="password123")
            ],
            [
                Input(value="admin' OR 1=1 --"), # SQL 注入尝试
                Input(value="A" * 5000) # 超长密码测试 bcrypt 性能/崩溃
            ]
        ]
        
        f = frelatage.Fuzzer(fuzz_user_register, samples)
        f.fuzz()
    
    else:
        print("未知目标。请设置环境变量 FUZZ_TARGET 为 'product' 或 'user'")


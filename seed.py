# seed.py

from database import SessionLocal, engine
import models

# 绑定元数据，这样 create_all 才能知道要创建哪些表
models.Base.metadata.create_all(bind=engine)

# 获取一个数据库会话
db = SessionLocal()

def seed_data():
    print("开始填充初始数据...")

    # --- 清空旧数据 (可选，但在开发阶段很有用) ---
    # 注意执行顺序，先删除依赖别人的表（如product），再删除被依赖的表（如seller）
    db.query(models.Comment).delete()
    db.query(models.Product).delete()
    db.query(models.Seller).delete()
    # 注意：user_favorites 是一个关联表，删除 user 或 product 时会自动处理。
    # 如果有其他复杂关系，可能需要手动清空关联表。
    
    # --- 创建商家 ---
    seller1 = models.Seller(shop_name="京西旗舰店", contact_info="support@jd-clone.com")
    seller2 = models.Seller(shop_name="数码先锋", contact_info="contact@digital-pioneer.com")
    
    db.add(seller1)
    db.add(seller2)
    
    # 提交商家以获取它们的 ID
    db.commit()
    db.refresh(seller1)
    db.refresh(seller2)
    
    print(f"创建了商家: {seller1.shop_name} (ID: {seller1.id}), {seller2.shop_name} (ID: {seller2.id})")

    # --- 创建商品 ---
    products_to_add = [
        models.Product(name="智能手机 Pro Max", price=5999.0, description="最新款旗舰手机，摄影功能强大", seller_id=seller1.id, image_url="url1"),
        models.Product(name="降噪蓝牙耳机", price=799.0, description="沉浸式音乐体验，长效续航", seller_id=seller1.id, image_url="url2"),
        models.Product(name="高性能机械键盘", price=899.0, description="RGB光效，电竞玩家首选", seller_id=seller2.id, image_url="url3"),
        models.Product(name="4K高清显示器", price=2499.0, description="色彩精准，设计、游戏两相宜", seller_id=seller2.id, image_url="url4"),
        models.Product(name="便携式笔记本电脑", price=7899.0, description="轻薄设计，性能卓越", seller_id=seller1.id, image_url="url5"),
    ]
    
    db.add_all(products_to_add)
    db.commit()
    
    print(f"成功添加了 {len(products_to_add)} 件商品。")

    print("数据填充完成！")


if __name__ == "__main__":
    try:
        seed_data()
    finally:
        db.close()


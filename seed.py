# seed.py (最终修复版)

from database import SessionLocal, engine
import models
import bcrypt
# 导入 sqlalchemy 的 delete 和 text 用于处理关联表
from sqlalchemy import text

# 绑定元数据
models.Base.metadata.create_all(bind=engine)

db = SessionLocal()

def seed_data():
    print("开始清洗并填充数据...")

    # --- 1. 清空旧数据 (顺序非常重要！) ---
    
    # 方法 A: 简单粗暴法 (推荐开发环境使用)
    # 暂时关闭外键检查，清空所有表，再重新开启。
    # 这样可以忽略删除顺序，彻底解决 IntegrityError。
    try:
        db.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        
        # 清空所有相关表
        db.execute(models.user_favorites.delete()) # 清空关联表
        db.query(models.Comment).delete()
        db.query(models.Product).delete()
        db.query(models.Seller).delete()
        db.query(models.User).delete()
        
        db.commit() # 提交删除操作
        print("旧数据已清空。")
        
    except Exception as e:
        db.rollback()
        print(f"清空数据时出错: {e}")
        return
    finally:
        # 无论如何都要把外键检查开回来，保证以后数据的完整性
        db.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
        db.commit()

    # --- 2. 创建商家 ---
    seller1 = models.Seller(shop_name="京西旗舰店", contact_info="support@jd.com")
    # 如果为了防止外键报错，也可以先创建一个自营兜底
    # seller_self = models.Seller(shop_name="京西自营", contact_info="admin@jd.com")
    
    db.add(seller1)
    db.commit()
    db.refresh(seller1)
    
    print(f"创建了商家 ID: {seller1.id}")

    # --- 3. 创建管理员和用户 ---
    salt = bcrypt.gensalt()
    
    # 管理员
    admin_pwd = bcrypt.hashpw(b"admin123", salt).decode('utf-8')
    admin_user = models.User(username="admin", hashed_password=admin_pwd, role="admin")
    
    # 普通用户
    user_pwd = bcrypt.hashpw(b"user123", salt).decode('utf-8')
    normal_user = models.User(username="testuser", hashed_password=user_pwd, role="customer")
    
    db.add(admin_user)
    db.add(normal_user)
    db.commit()
    db.refresh(normal_user) # 获取 ID 用于后面的评论

    print("创建了管理员账号: admin / admin123")
    print("创建了普通用户: testuser / user123")

    # --- 4. 创建商品 ---
    # 注意：seller_id 使用上面刚刚创建的 seller1.id
    products_to_add = [
        models.Product(name="智能手机 Pro Max", price=5999.0, description="性能怪兽", seller_id=seller1.id, image_url=""),
        models.Product(name="降噪蓝牙耳机", price=799.0, description="静享音乐", seller_id=seller1.id, image_url=""),
        models.Product(name="机械键盘", price=399.0, description="手感极佳", seller_id=seller1.id, image_url=""),
    ]
    
    db.add_all(products_to_add)
    db.commit()
    
    # 重新获取商品ID以便添加评论
    p1 = db.query(models.Product).filter(models.Product.name == "智能手机 Pro Max").first()

    # --- 5. 创建初始评论 ---
    if p1:
        c1 = models.Comment(
            content="手机运行速度很快，物流也很给力！", 
            likes=10, 
            user_id=normal_user.id, 
            product_id=p1.id
        )
        db.add(c1)
        db.commit()

    print("数据填充完成！")

if __name__ == "__main__":
    try:
        seed_data()
    finally:
        db.close()

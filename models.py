# models.py
#定义核心业务对象
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, Integer, String, TIMESTAMP
from sqlalchemy.sql import func
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

# 注意：之前的模拟数据模型可以删除了，因为我们不再使用它们


class Product:
    def __init__(self, product_id: str, name: str, price: float, description: str, seller_id: str, image_urls: List[str]):
        self.product_id = product_id
        self.name = name
        self.price = price
        self.description = description
        self.seller_id = seller_id
        self.image_urls = image_urls

class Seller:
    def __init__(self, seller_id: str, shop_name: str, contact_info: str):
        self.seller_id = seller_id
        self.shop_name = shop_name
        self.contact_info = contact_info

class Comment:
    def __init__(self, comment_id: str, content: str, user_id: str, likes: int = 0):
        self.comment_id = comment_id
        self.content = content
        self.user_id = user_id
        self.likes = likes

class Coupon:
    def __init__(self, coupon_id: str, seller_id: str, discount_value: float, expiry_date: datetime):
        self.coupon_id = coupon_id
        self.seller_id = seller_id
        self.discount_value = discount_value
        self.expiry_date = expiry_date

class Order:
    def __init__(self, order_id: str, user_id: str, product_id: str, status: str = "交易达成"):
        self.order_id = order_id
        self.user_id = user_id
        self.product_id = product_id
        self.status = status


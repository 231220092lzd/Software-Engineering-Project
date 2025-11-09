# schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# --- User Schemas ---
class UserCreate(BaseModel):
    username: str
    password: str
    contact_info: str = Field(..., example="wechat:user123")

class User(BaseModel):
    user_id: str
    username: str
    contact_info: str

    class Config:
        from_attributes = True # 修正点

# --- Product Schemas ---
class ProductCreate(BaseModel):
    name: str = Field(..., example="新款智能手表")
    price: float = Field(..., example=1299.99)
    description: str = Field(..., example="功能强大，续航持久")
    image_urls: List[str] = Field(..., example=["http://example.com/img1.jpg"])

class Product(BaseModel):
    product_id: str
    name: str
    price: float
    description: str
    seller_id: str
    image_urls: List[str]

    class Config:
        from_attributes = True # 修正点

# --- Comment Schemas ---
class CommentCreate(BaseModel):
    content: str = Field(..., min_length=5, max_length=500)

class Comment(BaseModel):
    comment_id: str
    content: str
    user_id: str
    likes: int

    class Config:
        from_attributes = True # 修正点

# --- Order Schemas (Core Requirement) ---
class OrderCreate(BaseModel):
    product_id: str

class ContactExchange(BaseModel):
    """Req005 & Req011: 核心交易模型，用于交换联系方式"""
    order_id: str
    message: str = "交易意向已达成，请通过以下方式联系对方"
    seller_contact: str
    buyer_contact: str

# --- Coupon Schemas ---
class CouponCreate(BaseModel):
    discount_value: float = Field(..., gt=0, description="优惠金额")
    expiry_date: datetime = Field(..., description="优惠券过期时间")

class Coupon(BaseModel):
    coupon_id: str
    seller_id: str
    discount_value: float
    expiry_date: datetime

    class Config:
        from_attributes = True # 修正点

# schemas.py

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# --- User Schemas ---
class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int

    class Config:
        from_attributes = True # 修正点

# --- Seller Schemas ---
class SellerBase(BaseModel):
    shop_name: str
    contact_info: Optional[str] = None

class SellerCreate(SellerBase):
    pass

class Seller(SellerBase):
    id: int
    
    class Config:
        from_attributes = True # 修正点

# --- Product Schemas ---
class ProductBase(BaseModel):
    name: str = Field(..., example="新款智能手表")
    price: float = Field(..., example=1299.99)
    description: Optional[str] = Field(None, example="功能强大，续航持久")
    image_url: Optional[str] = Field(None, example="http://example.com/img1.jpg")

class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    id: int
    seller_id: int

    class Config:
        from_attributes = True # 修正点

# --- Comment Schemas ---
class CommentBase(BaseModel):
    content: str = Field(..., min_length=5, max_length=500)

class CommentCreate(CommentBase):
    pass

class Comment(CommentBase):
    id: int
    user_id: int
    product_id: int
    likes: int

    class Config:
        from_attributes = True # 修正点
        
# --- 用于用户收藏列表的特殊 Schema ---
class UserWithFavorites(User):
    favorite_products: List[Product] = []

    class Config:
        from_attributes = True # 修正点

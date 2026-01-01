from sqlalchemy import (Column, Integer, String, Float, TIMESTAMP, ForeignKey, Table)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

# 用户-商品 收藏关联表
user_favorites = Table('user_favorites', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('product_id', Integer, ForeignKey('products.id'), primary_key=True)
)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, server_default="customer")
    created_at = Column(TIMESTAMP, server_default=func.now())
    favorite_products = relationship("Product", secondary=user_favorites, back_populates="favorited_by_users")

class Seller(Base):
    __tablename__ = "sellers"
    id = Column(Integer, primary_key=True, index=True)
    shop_name = Column(String(100), nullable=False)
    contact_info = Column(String(100))
    products = relationship("Product", back_populates="seller")

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    price = Column(Float, nullable=False)
    description = Column(String(500))
    seller_id = Column(Integer, ForeignKey("sellers.id"))
    image_url = Column(String(255))
    seller = relationship("Seller", back_populates="products")
    favorited_by_users = relationship("User", secondary=user_favorites, back_populates="favorite_products")

class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True, index=True)
    content = Column(String(500), nullable=False)
    likes = Column(Integer, default=0)
    
    user_id = Column(Integer, ForeignKey("users.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    
    # --- 修复点：添加 user 关系，以便查询评论时能获取用户名 ---
    user = relationship("User") 

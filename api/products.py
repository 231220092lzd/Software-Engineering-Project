# api/products.py

from fastapi import APIRouter, Query, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional

# 导入数据库模型、Pydantic schemas 和数据库会话依赖
import models
import schemas
from database import get_db

router = APIRouter(
    prefix="/products",
    tags=["Products"],
)

@router.get("/", response_model=List[schemas.Product], summary="查询商品列表")
def get_products(
    sort_by: Optional[str] = Query(None, description="按价格排序: 'price_asc' 或 'price_desc'"),
    db: Session = Depends(get_db)  # 注入数据库会话
):
    """
    从数据库获取所有商品列表。
    - 支持按价格升序或降序排序。
    """
    query = db.query(models.Product) # 创建查询对象
    
    if sort_by == 'price_asc':
        query = query.order_by(models.Product.price.asc())
    elif sort_by == 'price_desc':
        query = query.order_by(models.Product.price.desc())
        
    products = query.all()
    return products

@router.get("/{product_id}", response_model=schemas.Product, summary="查询商品详情")
def get_product_details(product_id: int, db: Session = Depends(get_db)):
    """
    从数据库获取单个商品的详细信息。
    """
    # 使用数据库查询替代字典查找
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.post("/", response_model=schemas.Product, status_code=201, summary="商家发布商品")
def publish_product(product: schemas.ProductCreate, seller_id: int, db: Session = Depends(get_db)):
    """
    在数据库中创建一个新商品。
    注意：在真实应用中，seller_id应该从认证信息（如JWT Token）中获取，而不是作为参数传入。
    """
    # 检查商家是否存在
    seller = db.query(models.Seller).filter(models.Seller.id == seller_id).first()
    if not seller:
        raise HTTPException(status_code=404, detail=f"Seller with id {seller_id} not found")

    new_product = models.Product(**product.dict(), seller_id=seller_id)
    
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    
    return new_product

# --- 评论相关API (从sellers.py移动至此更符合RESTful风格) ---

@router.get("/{product_id}/comments", response_model=List[schemas.Comment], summary="获取商品评论")
def get_product_comments(product_id: int, db: Session = Depends(get_db)):
    comments = db.query(models.Comment).filter(models.Comment.product_id == product_id).all()
    return comments

@router.post("/{product_id}/comments", response_model=schemas.Comment, status_code=201, summary="为商品添加评论")
def add_comment_to_product(product_id: int, comment: schemas.CommentCreate, db: Session = Depends(get_db)):
    # 假设当前用户是 user_id=1, 实际应从Token获取
    current_user_id = 1 
    
    # 检查商品是否存在
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    new_comment = models.Comment(
        **comment.dict(),
        product_id=product_id,
        user_id=current_user_id
    )
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    return new_comment

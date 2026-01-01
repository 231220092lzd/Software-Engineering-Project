# api/admin.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import models, schemas, database
from api.users import get_current_user

router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)

# 依赖项：检查是否是管理员
def get_current_admin(current_user: models.User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="需要管理员权限"
        )
    return current_user

@router.post("/products", response_model=schemas.Product, status_code=status.HTTP_201_CREATED)
def create_product(
    product: schemas.ProductCreate, 
    db: Session = Depends(database.get_db),
    admin_user: models.User = Depends(get_current_admin)
):
    # --- 修复逻辑开始 ---
    # 1. 尝试获取第一个存在的商家
    seller = db.query(models.Seller).first()
    
    # 2. 如果数据库里完全没有商家，为了防止报错，我们自动创建一个 "自营店"
    if not seller:
        seller = models.Seller(shop_name="京西自营", contact_info="admin@jd.com")
        db.add(seller)
        db.commit()
        db.refresh(seller)
    
    # 3. 使用获取到的有效 seller_id
    new_product = models.Product(**product.dict(), seller_id=seller.id) 
    # --- 修复逻辑结束 ---

    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product

@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int, 
    db: Session = Depends(database.get_db),
    admin_user: models.User = Depends(get_current_admin)
):
    product_query = db.query(models.Product).filter(models.Product.id == product_id)
    
    if product_query.first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        
    product_query.delete(synchronize_session=False)
    db.commit()
    return

# api/admin.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import models, schemas, database

router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)

# 接口1: 添加新商品
@router.post("/products", response_model=schemas.Product, status_code=status.HTTP_201_CREATED)
def create_product(product: schemas.ProductCreate, db: Session = Depends(database.get_db)):
    # 假设 seller_id 为 1 (因为只有一个商家)
    new_product = models.Product(**product.dict(), seller_id=1) 
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product

# 接口2: 删除商品
@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, db: Session = Depends(database.get_db)):
    product_query = db.query(models.Product).filter(models.Product.id == product_id)
    
    if product_query.first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        
    product_query.delete(synchronize_session=False)
    db.commit()
    return

# (优惠券发放的API已经在sellers.py中，这里我们假设管理员就是这个商家，所以可以直接用)

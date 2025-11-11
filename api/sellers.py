# api/sellers.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

import models
import schemas
from database import get_db

router = APIRouter(
    prefix="/sellers",
    tags=["Sellers"],
)

@router.post("/", response_model=schemas.Seller, status_code=201, summary="创建商家")
def create_seller(seller: schemas.SellerCreate, db: Session = Depends(get_db)):
    new_seller = models.Seller(**seller.dict())
    db.add(new_seller)
    db.commit()
    db.refresh(new_seller)
    return new_seller

@router.get("/{seller_id}", response_model=schemas.Seller, summary="获取商家信息")
def get_seller(seller_id: int, db: Session = Depends(get_db)):
    seller = db.query(models.Seller).filter(models.Seller.id == seller_id).first()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")
    return seller

# 注意：之前的优惠券和顾客列表API是纯模拟数据，
# 如果要实现它们，需要先在 models.py 和 schemas.py 中定义 Coupon 和 Customer 模型。
# 这里暂时移除它们，以保持项目的一致性。

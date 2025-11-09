# api/users.py
import uuid
from fastapi import APIRouter, HTTPException, Body
from schemas import UserCreate, User, OrderCreate, ContactExchange
from models import User as UserModel
from typing import List

router = APIRouter()

# 模拟数据库
mock_db_users = {
    "u001": UserModel(user_id="u001", username="Alice", password_hash="hashed_pw", contact_info="tel:13800138000"),
}
mock_db_orders = {}
mock_db_sellers = {
    "s001": {"seller_id": "s001", "shop_name": "TechShop", "contact_info": "email:seller1@tech.com"}
}
# 引用 products.py 中的模拟数据
from .products import mock_db_products


@router.post("/register", response_model=User, tags=["Users"], summary="用户注册 (Req001)")
def register_user(user: UserCreate):
    # 简单模拟，真实世界需要检查用户名是否已存在
    user_id = f"u{len(mock_db_users) + 1:03d}"
    # 真实世界需要对密码进行哈希处理
    new_user = UserModel(user_id=user_id, username=user.username, password_hash="hashed_"+user.password, contact_info=user.contact_info)
    mock_db_users[user_id] = new_user
    return new_user

# 登录接口通常会返回一个JWT Token，这里简化处理
@router.post("/login", tags=["Users"], summary="用户登录 (Req001)")
def login():
    return {"message": "Login successful (mocked)."}


@router.post("/users/me/favorites/{product_id}", status_code=204, tags=["Users"], summary="添加商品到收藏夹 (Req006)")
def add_to_favorites(product_id: str):
    # 假设当前用户是 u001
    current_user_id = "u001"
    if product_id not in mock_db_products:
        raise HTTPException(status_code=404, detail="Product not found")
    
    user = mock_db_users.get(current_user_id)
    if product_id not in user.favorites:
        user.favorites.append(product_id)
    # 204 No Content 表示成功，无需返回内容
    return

@router.get("/users/me/favorites", response_model=List[str], tags=["Users"], summary="查看收藏夹")
def get_favorites():
    # 假设当前用户是 u001
    current_user_id = "u001"
    return mock_db_users.get(current_user_id).favorites


@router.post("/orders", response_model=ContactExchange, tags=["Orders"], summary="发起交易并交换联系方式 (Req005, Req011)")
def create_order(order: OrderCreate):
    """
    核心交易流程:
    不涉及支付，创建订单后立即返回买卖双方的联系方式。
    """
    # 假设当前用户是 "u001"
    current_user_id = "u001"
    
    product = mock_db_products.get(order.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    buyer = mock_db_users.get(current_user_id)
    seller = mock_db_sellers.get(product.seller_id)

    if not buyer or not seller:
         raise HTTPException(status_code=500, detail="Internal error: user or seller data missing")

    order_id = f"order-{uuid.uuid4().hex[:6]}"
    
    # 将订单存入模拟数据库
    mock_db_orders[order_id] = {"user_id": current_user_id, "product_id": order.product_id, "status": "交易达成"}

    return ContactExchange(
        order_id=order_id,
        seller_contact=seller["contact_info"],
        buyer_contact=buyer.contact_info
    )

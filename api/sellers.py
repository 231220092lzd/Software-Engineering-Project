# api/sellers.py
from fastapi import APIRouter, Query, HTTPException
from typing import List
from schemas import Comment, CommentCreate, Coupon, CouponCreate
import uuid
from datetime import datetime

# --- 修正点: 确保 router 的定义是正确的 ---
router = APIRouter(
    prefix="/sellers",
    tags=["Sellers"],
)

# 模拟评论数据
mock_db_comments = {
    "s001": [
        Comment(comment_id="c001", user_id="u001", content="这家店的手机很棒！", likes=150),
        Comment(comment_id="c002", user_id="u002", content="发货速度很快。", likes=99),
    ]
}
mock_db_coupons = {}

@router.get("/{seller_id}/comments", response_model=List[Comment], summary="获取商家评论区 (Req009)")
def get_seller_comments(
    seller_id: str,
    page: int = Query(1, ge=1),
    size: int = Query(15, ge=1, le=100)
):
    """
    分页获取商家评论，并按点赞数降序排序。
    """
    comments = mock_db_comments.get(seller_id, [])
    
    # 按点赞数排序
    sorted_comments = sorted(comments, key=lambda c: c.likes, reverse=True)
    
    # 分页
    start = (page - 1) * size
    end = start + size
    return sorted_comments[start:end]

@router.post("/{seller_id}/comments", response_model=Comment, status_code=201, summary="添加评论")
def add_comment(seller_id: str, comment: CommentCreate):
    # 假设当前用户是 "u001"
    current_user_id = "u001"
    new_comment = Comment(
        comment_id=f"c{uuid.uuid4().hex[:4]}",
        user_id=current_user_id,
        content=comment.content,
        likes=0
    )
    if seller_id not in mock_db_comments:
        mock_db_comments[seller_id] = []
    mock_db_comments[seller_id].append(new_comment)
    return new_comment


@router.post("/me/coupons", response_model=Coupon, summary="商家发放优惠券 (Req012, Req013)")
def send_coupon(coupon: CouponCreate):
    # 假设当前商家是 "s001"
    current_seller_id = "s001"
    coupon_id = f"coupon-{uuid.uuid4().hex[:6]}"
    new_coupon = Coupon(
        coupon_id=coupon_id,
        seller_id=current_seller_id,
        discount_value=coupon.discount_value,
        expiry_date=coupon.expiry_date
    )
    mock_db_coupons[coupon_id] = new_coupon
    return new_coupon

# api/sellers.py
# ... (保留之前的所有代码)
# 在文件末尾添加以下代码

# 为优惠券页面提供模拟顾客数据
mock_db_customers = {
    "customers": [
        {"id": "cust001", "name": "顾客1"},
        {"id": "cust002", "name": "顾客2"},
        {"id": "cust003", "name": "顾客3"},
        {"id": "cust004", "name": "顾客4"},
        {"id": "cust005", "name": "顾客5"},
    ],
    "groups": [
        {"id": "groupA", "name": "顾客群1"},
        {"id": "groupB", "name": "顾客群2"},
        {"id": "groupC", "name": "顾客群3"},
    ]
}

@router.get("/me/customers", tags=["Sellers"], summary="获取商家的顾客列表")
def get_my_customers():
    # 假设当前商家是 s001，直接返回模拟数据
    return mock_db_customers

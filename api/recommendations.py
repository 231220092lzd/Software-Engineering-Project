# api/recommendations.py
from fastapi import APIRouter
from typing import List
from schemas import Product

router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendations"],
)

# 引用 products.py 中的模拟数据
from .products import mock_db_products

@router.get("/", response_model=List[Product], summary="获取智能推荐商品 (Req010)")
def get_recommendations():
    """
    模拟大模型推荐功能。
    在真实场景中，这里会调用一个复杂的推荐服务，
    该服务会分析用户的历史购买记录、浏览行为等。
    
    此处为模拟实现，随机返回最多10件商品。
    """
    all_products = list(mock_db_products.values())
    # 模拟智能推荐，简单返回前10个或所有（如果不足10个）
    return all_products[:10]


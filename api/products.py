# api/products.py
from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from schemas import Product, ProductCreate

router = APIRouter(
    prefix="/products",
    tags=["Products"],
)

# 模拟数据库
mock_db_products = {
    "p001": Product(product_id="p001", name="智能手机", price=2999.0, description="最新款旗舰手机", seller_id="s001", image_urls=["url1", "url2"]),
    "p002": Product(product_id="p002", name="蓝牙耳机", price=599.0, description="降噪效果一流", seller_id="s001", image_urls=["url3"]),
    "p003": Product(product_id="p003", name="机械键盘", price=899.0, description="电竞玩家首选", seller_id="s002", image_urls=["url4"]),
}

@router.get("/", response_model=List[Product], summary="查询商品列表 (Req002, Req007)")
def get_products(
    sort_by: Optional[str] = Query(None, description="按价格排序: 'price_asc' 或 'price_desc'")
):
    """
    获取所有商品列表。
    - 支持按价格升序或降序排序。
    """
    products = list(mock_db_products.values())
    if sort_by == 'price_asc':
        products.sort(key=lambda p: p.price)
    elif sort_by == 'price_desc':
        products.sort(key=lambda p: p.price, reverse=True)
    return products

@router.get("/{product_id}", response_model=Product, summary="查询商品详情 (Req008)")
def get_product_details(product_id: str):
    """
    获取单个商品的详细信息，包括图片预览URL列表。
    """
    product = mock_db_products.get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

# 此接口应由商家调用, 为简化先放在这里
@router.post("/", response_model=Product, status_code=201, summary="商家发布商品 (Req002)")
def publish_product(product: ProductCreate):
    # 此处应有认证逻辑，确保是商家操作
    # 模拟创建商品
    new_id = f"p{len(mock_db_products) + 1:03d}"
    seller_id = "s001" # 假设是来自认证系统的商家ID
    new_product = Product(
        product_id=new_id, 
        seller_id=seller_id, 
        **product.dict()
    )
    mock_db_products[new_id] = new_product
    return new_product

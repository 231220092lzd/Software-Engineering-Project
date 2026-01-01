# api/users.py

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List
import bcrypt
import models
import schemas
from database import get_db

# --- JWT 相关导入 ---
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta
import os

router = APIRouter(prefix="/users", tags=["Users"])

# JWT 配置
SECRET_KEY = os.getenv("JWT_SECRET", "please-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/users/login")

# --- 辅助函数 ---
def get_password_hash(password: str) -> bytes:
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt)

def verify_password(plain_password: str, hashed_password: bytes) -> bool:
    plain_password_bytes = plain_password.encode('utf-8')
    return bcrypt.checkpw(plain_password_bytes, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
    except (JWTError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

# --- 路由定义 ---

@router.post("/register", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = get_password_hash(user.password)
    new_user = models.User(username=user.username, hashed_password=hashed_password.decode('utf-8'))
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login")
async def login(request: Request, db: Session = Depends(get_db)):
    username = None
    password = None
    try:
        payload = await request.json()
    except Exception:
        payload = None

    if payload and isinstance(payload, dict):
        username = payload.get("username")
        password = payload.get("password")

    if not username or not password:
        try:
            form = await request.form()
            username = username or form.get("username")
            password = password or form.get("password")
        except Exception:
            pass

    if not username or not password:
        raise HTTPException(status_code=400, detail="username and password required")

    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    hashed_password_bytes = user.hashed_password.encode('utf-8')
    if not verify_password(password, hashed_password_bytes):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    access_token = create_access_token({"sub": str(user.id), "role": user.role})
    return {"access_token": access_token, "token_type": "bearer", "user_id": user.id, "role": user.role}

# --- 修复重点：移除路径中的 {user_id} ---

@router.post("/favorites/{product_id}", status_code=status.HTTP_201_CREATED, summary="添加收藏")
def add_favorite(product_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if product in current_user.favorite_products:
        raise HTTPException(status_code=400, detail="Product already in favorites")
    
    current_user.favorite_products.append(product)
    db.commit()
    return {"status": "success", "message": "Favorite added"}

@router.get("/favorites", response_model=List[schemas.Product], summary="获取用户的收藏列表")
def get_favorites(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # 直接返回当前登录用户的收藏
    return current_user.favorite_products

@router.delete("/favorites/{product_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除收藏")
def remove_favorite(product_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if product in current_user.favorite_products:
        current_user.favorite_products.remove(product)
        db.commit()
    return

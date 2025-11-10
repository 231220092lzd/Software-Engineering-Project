from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

# 导入新的库
import bcrypt

# 导入我们的模块
import models
import schemas
from database import get_db

router = APIRouter(prefix="/users", tags=["Users"])

# --- 使用 bcrypt 进行密码处理 ---

def get_password_hash(password: str) -> bytes:
    """对字符串密码进行哈希，返回哈希后的字节串"""
    # 1. 将密码字符串编码为 UTF-8 字节
    password_bytes = password.encode('utf-8')
    # 2. 生成盐值
    salt = bcrypt.gensalt()
    # 3. 哈希密码
    hashed_password = bcrypt.hashpw(password_bytes, salt)
    return hashed_password

def verify_password(plain_password: str, hashed_password: bytes) -> bool:
    """验证明文密码是否与哈希后的密码匹配"""
    # 1. 将明文密码编码为 UTF-8 字节
    plain_password_bytes = plain_password.encode('utf-8')
    # 2. 使用 bcrypt.checkpw 进行验证
    return bcrypt.checkpw(plain_password_bytes, hashed_password)

# --- ---

@router.post("/register", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # 直接调用我们新的哈希函数
    hashed_password = get_password_hash(user.password)
    
    # 注意：我们的数据库模型需要能存储字节。VARCHAR/STRING 类型通常可以。
    new_user = models.User(username=user.username, hashed_password=hashed_password.decode('utf-8'))
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == request.username).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # 从数据库取出的哈希是字符串，需要编码回字节
    hashed_password_bytes = user.hashed_password.encode('utf-8')

    if not verify_password(request.password, hashed_password_bytes):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
        
    return {"status": "success", "message": "Login successful", "user_id": user.id}

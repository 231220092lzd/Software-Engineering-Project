from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 数据库连接URL
# 格式: "mysql+pymysql://<user>:<password>@<host>:<port>/<dbname>"
# 请根据您的MySQL设置修改以下信息
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:LXb75315@127.0.0.1:3306/my_ecommerce_db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

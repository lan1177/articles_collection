import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    # 飞书应用配置
    FEISHU_APP_ID = os.getenv("FEISHU_APP_ID", "cli_a7716f1ed63cd01c")
    FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET", "JGjdVIbF6On96l8mJBM72cevqTmVQHtE")
    
    # 多维表格配置
    BASE_ID = os.getenv("BASE_ID", "Neqabr2EIaANJEsjg2DcK0Osn8g")
    TABLE_ID = os.getenv("TABLE_ID", "tblEqTy7bRR4Hdau")
    
    # Flask配置
    SECRET_KEY = os.urandom(24)
    DEBUG = True
    
    # 缓存配置
    CACHE_TYPE = "SimpleCache"
    CACHE_DEFAULT_TIMEOUT = 300  # 缓存5分钟

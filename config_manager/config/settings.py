"""
配置常量和设置
"""
import os
from pathlib import Path

# Flask配置
SECRET_KEY = os.environ.get("SECRET_KEY", "samsung-trendradar-secret-key-2024")

# 服务器配置
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "5001"))
DEBUG = os.environ.get("DEBUG", "False").lower() == "true"

# 配置文件路径
CONFIG_PATH = os.environ.get("CONFIG_PATH", "config/config.yaml")
SUBSCRIPTIONS_PATH = os.environ.get("SUBSCRIPTIONS_PATH", "config/subscriptions.json")
CONFIG_DIR = Path(CONFIG_PATH).parent

# 用户凭证配置
USERS = {
    "admin": {
        "password": "samsung00@",
        "role": "admin"
    },
    "user": {
        "password": "samsung1!",
        "role": "user"
    }
}

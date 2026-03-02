#!/usr/bin/env python
# coding=utf-8
"""
智通星资讯管理 - 新版启动脚本
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config_manager.app import app, create_app, HOST, PORT

if __name__ == "__main__":
    app = create_app()
    print("=" * 60)
    print("智通星资讯管理 - 模块化配置管理界面")
    print("=" * 60)
    print(f"访问地址: http://{HOST}:{PORT}")
    print(f"调试模式: {app.debug}")
    print("=" * 60)
    print("说明：")
    print("  - 管理员账号: admin / samsung00@")
    print("  - 普通用户账号: user / samsung1!")
    print("=" * 60)
    app.run(host=HOST, port=PORT, debug=app.debug)

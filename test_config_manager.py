#!/usr/bin/env python
# coding=utf-8
"""
测试模块化版本的config_manager
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 60)
print("测试模块化版本")
print("=" * 60)

# 测试配置模块
try:
    from config_manager.config import settings, utils
    print("✓ config 模块导入成功")
    print(f"  - CONFIG_PATH: {settings.CONFIG_PATH}")
    print(f"  - SUBSCRIPTIONS_PATH: {settings.SUBSCRIPTIONS_PATH}")
    print(f"  - PORT: {settings.PORT}")
except Exception as e:
    print(f"✗ config 模块导入失败: {e}")
    sys.exit(1)

# 测试认证模块
try:
    from config_manager.auth import decorators
    print("✓ auth 模块导入成功")
    print(f"  - login_required: {decorators.login_required}")
    print(f"  - admin_required: {decorators.admin_required}")
except Exception as e:
    print(f"✗ auth 模块导入失败: {e}")
    sys.exit(1)

# 测试API模块
try:
    from config_manager.api import auth_routes, config_routes, execution_routes
    print("✓ api 模块导入成功")
except Exception as e:
    print(f"✗ api 模块导入失败: {e}")
    sys.exit(1)

# 测试Flask应用
try:
    from config_manager.app import app, create_app
    print("✓ Flask 应用导入成功")
    print(f"  - app.name: {app.name}")
except Exception as e:
    print(f"✗ Flask 应用导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("=" * 60)
print("所有测试通过！模块化版本可以正常使用。")
print("=" * 60)
print("\n启动方法：")
print("  python run_config_manager.py")
print("或者：")
print("  python config_manager/app.py")
print("=" * 60)

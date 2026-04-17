"""
认证装饰器
"""
import functools
from flask import session, jsonify


def login_required(f):
    """登录检查装饰器"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return jsonify({"success": False, "error": "需要登录"}), 401
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """管理员权限检查装饰器"""
    @functools.wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            return jsonify({"success": False, "error": "需要管理员权限"}), 403
        return f(*args, **kwargs)
    return decorated_function

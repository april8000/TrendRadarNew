"""
认证相关路由
"""
from flask import request, jsonify, session, render_template_string
from config_manager.auth.decorators import login_required, admin_required
from config_manager.config.settings import USERS


def register_routes(app):
    """注册认证路由"""
    
    @app.route("/api/login", methods=["POST"])
    def login():
        """用户登录"""
        try:
            data = request.get_json()
            username = data.get("username", "")
            password = data.get("password", "")
            
            if username in USERS and USERS[username]["password"] == password:
                session['logged_in'] = True
                session['username'] = username
                session['role'] = USERS[username]["role"]
                return jsonify({"success": True, "message": "登录成功", "role": USERS[username]["role"]})
            else:
                return jsonify({"success": False, "error": "用户名或密码错误"}), 401
        except Exception as e:
            return jsonify({"success": False, "error": f"登录失败: {str(e)}"}), 500

    @app.route("/api/logout", methods=["POST"])
    def logout():
        """用户登出"""
        session.pop('logged_in', None)
        session.pop('username', None)
        session.pop('role', None)
        return jsonify({"success": True, "message": "已登出"})

    @app.route("/api/check_login", methods=["GET"])
    def check_login():
        """检查登录状态"""
        return jsonify({
            "logged_in": session.get('logged_in', False),
            "role": session.get('role', None),
            "username": session.get('username', None)
        })

"""
配置文件相关路由
"""
from flask import request, jsonify
from config_manager.auth.decorators import login_required, admin_required
from config_manager.config.utils import load_config, save_config, load_subscriptions, save_subscriptions


def register_routes(app):
    """注册配置路由"""
    
    @app.route("/api/config", methods=["GET"])
    @admin_required
    def get_config():
        """获取配置"""
        config = load_config()
        if "error" in config:
            return jsonify(config), 500
        return jsonify(config)

    @app.route("/api/config", methods=["POST"])
    @admin_required
    def update_config():
        """更新配置"""
        try:
            config_data = request.get_json()
            if not config_data:
                return jsonify({"success": False, "error": "请求数据为空"}), 400
            
            result = save_config(config_data)
            if result.get("success"):
                return jsonify(result)
            else:
                return jsonify(result), 500
        except Exception as e:
            return jsonify({"success": False, "error": f"处理请求失败: {str(e)}"}), 500

    @app.route("/api/subscriptions", methods=["GET"])
    @login_required
    def get_subscriptions():
        """获取订阅配置"""
        subscriptions = load_subscriptions()
        if "error" in subscriptions:
            return jsonify(subscriptions), 500
        return jsonify(subscriptions)

    @app.route("/api/subscriptions", methods=["POST"])
    @login_required
    def update_subscriptions():
        """更新订阅配置"""
        try:
            subscriptions_data = request.get_json()
            if not subscriptions_data:
                return jsonify({"success": False, "error": "请求数据为空"}), 400
            
            result = save_subscriptions(subscriptions_data)
            if result.get("success"):
                return jsonify(result)
            else:
                return jsonify(result), 500
        except Exception as e:
            return jsonify({"success": False, "error": f"处理请求失败: {str(e)}"}), 500

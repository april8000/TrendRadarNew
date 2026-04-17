"""
智通星资讯管理 - 模块化版本
基于关键词监控的 Webhook 消息推送服务的可视化配置管理界面
"""
import os
import sys
from flask import Flask, render_template, session
from flask_cors import CORS

# 添加项目根目录到路径，以便导入config_manager模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_manager.config.settings import SECRET_KEY, HOST, PORT, DEBUG
from config_manager.api.auth_routes import register_routes as register_auth_routes
from config_manager.api.config_routes import register_routes as register_config_routes
from config_manager.api.execution_routes import register_routes as register_execution_routes

app = Flask(__name__)
app.secret_key = SECRET_KEY
CORS(app)


def create_app():
    """创建Flask应用"""
    # 注册所有路由
    register_auth_routes(app)
    register_config_routes(app)
    register_execution_routes(app)
    
    # 主页面路由
    @app.route("/")
    def index():
        """主页面"""
        if not session.get('logged_in'):
            return render_template('login.html')
        return render_template('index.html')
    
    return app


if __name__ == "__main__":
    app = create_app()
    print("=" * 60)
    print("智通星资讯管理 - 配置管理界面")
    print("=" * 60)
    print(f"访问地址: http://{HOST}:{PORT}")
    print(f"调试模式: {DEBUG}")
    print("=" * 60)
    app.run(host=HOST, port=PORT, debug=DEBUG)

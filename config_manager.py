#!/usr/bin/env python
# coding=utf-8
"""
智通星资讯管理
基于关键词监控的 Webhook 消息推送服务的可视化配置管理界面
提供可视化的 config.yaml 和 subscriptions.json 配置文件管理功能
支持多平台热点监控、关键词匹配、Webhook 推送等功能
"""

import os
import json
import yaml
from pathlib import Path
from flask import Flask, render_template_string, request, jsonify, session
from flask_cors import CORS
import functools

# 自定义YAML Dumper以保持列表格式
class ListDumper(yaml.SafeDumper):
    pass

def represent_list(dumper, data):
    return dumper.represent_sequence('tag:yaml.org,2002:seq', data, flow_style=False)

ListDumper.add_representer(list, represent_list)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "samsung-trendradar-secret-key-2024")  # 用于session加密
CORS(app)

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

# 配置文件路径
CONFIG_PATH = os.environ.get("CONFIG_PATH", "config/config.yaml")
SUBSCRIPTIONS_PATH = os.environ.get("SUBSCRIPTIONS_PATH", "config/subscriptions.json")
CONFIG_DIR = Path(CONFIG_PATH).parent


# ========== Config.yaml 管理 ==========

def load_config():
    """加载配置文件"""
    if not Path(CONFIG_PATH).exists():
        return {"error": f"配置文件不存在: {CONFIG_PATH}"}
    
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)
        return config_data
    except Exception as e:
        return {"error": f"配置文件加载失败: {str(e)}"}


def save_config(config_data):
    """保存配置文件"""
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        
        if Path(CONFIG_PATH).exists():
            backup_path = f"{CONFIG_PATH}.backup"
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                backup_content = f.read()
            with open(backup_path, "w", encoding="utf-8") as f:
                f.write(backup_content)
        
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f, allow_unicode=True, default_flow_style=False, 
                     sort_keys=False, Dumper=ListDumper, width=1000)
        
        return {"success": True, "message": "配置保存成功"}
    except Exception as e:
        return {"success": False, "error": f"配置保存失败: {str(e)}"}


# ========== Subscriptions.json 管理 ==========

def load_subscriptions():
    """加载订阅配置文件"""
    if not Path(SUBSCRIPTIONS_PATH).exists():
        return {"error": f"订阅配置文件不存在: {SUBSCRIPTIONS_PATH}"}
    
    try:
        with open(SUBSCRIPTIONS_PATH, "r", encoding="utf-8") as f:
            subscriptions_data = json.load(f)
        return subscriptions_data
    except json.JSONDecodeError as e:
        return {"error": f"订阅配置文件JSON格式错误: {str(e)}"}
    except Exception as e:
        return {"error": f"订阅配置文件加载失败: {str(e)}"}


def save_subscriptions(subscriptions_data):
    """保存订阅配置文件"""
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        
        if Path(SUBSCRIPTIONS_PATH).exists():
            backup_path = f"{SUBSCRIPTIONS_PATH}.backup"
            with open(SUBSCRIPTIONS_PATH, "r", encoding="utf-8") as f:
                backup_content = f.read()
            with open(backup_path, "w", encoding="utf-8") as f:
                f.write(backup_content)
        
        with open(SUBSCRIPTIONS_PATH, "w", encoding="utf-8") as f:
            json.dump(subscriptions_data, f, ensure_ascii=False, indent=2)
        
        return {"success": True, "message": "订阅配置保存成功"}
    except Exception as e:
        return {"success": False, "error": f"订阅配置保存失败: {str(e)}"}


# ========== API 路由 ==========

@app.route("/")
def index():
    """主页面"""
    if not session.get('logged_in'):
        return render_template_string(LOGIN_TEMPLATE)
    return render_template_string(HTML_TEMPLATE)

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


@app.route("/api/execute", methods=["POST"])
@login_required
def execute_main():
    """执行 main.py"""
    import subprocess
    import sys
    from io import StringIO
    
    try:
        # 切换到项目根目录
        project_root = Path(__file__).parent
        main_py = project_root / "main.py"
        
        if not main_py.exists():
            return jsonify({
                "success": False,
                "error": f"main.py 文件不存在: {main_py}"
            }), 404
        
        # 执行 main.py
        process = subprocess.Popen(
            [sys.executable, str(main_py)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace',
            cwd=str(project_root),
            bufsize=1
        )
        
        # 读取输出（实时）
        output_lines = []
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                output_lines.append(line.rstrip())
        
        # 等待进程结束
        return_code = process.wait()
        
        output = '\n'.join(output_lines)
        
        if return_code == 0:
            return jsonify({
                "success": True,
                "output": output,
                "return_code": return_code
            })
        else:
            return jsonify({
                "success": False,
                "output": output,
                "error": f"进程返回码: {return_code}",
                "return_code": return_code
            })
            
    except Exception as e:
        import traceback
        error_msg = f"执行失败: {str(e)}\n{traceback.format_exc()}"
        return jsonify({
            "success": False,
            "error": error_msg
        }), 500


# HTML模板 - 由于太长，将在下一个工具调用中完成
# 登录页面模板
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>登录 - 智通星资讯管理</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .login-container {
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            padding: 48px;
            width: 100%;
            max-width: 420px;
        }
        .login-header {
            text-align: center;
            margin-bottom: 40px;
        }
        .login-header h1 {
            font-size: 28px;
            color: #1f2937;
            margin-bottom: 8px;
        }
        .login-header p {
            color: #6b7280;
            font-size: 14px;
        }
        .form-group {
            margin-bottom: 24px;
        }
        .form-group label {
            display: block;
            margin-bottom: 8px;
            color: #374151;
            font-weight: 500;
            font-size: 14px;
        }
        .form-group input {
            width: 100%;
            padding: 12px 16px;
            border: 2px solid #e5e7eb;
            border-radius: 8px;
            font-size: 15px;
            transition: all 0.3s;
        }
        .form-group input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        .btn-login {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .btn-login:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }
        .btn-login:active {
            transform: translateY(0);
        }
        .error-message {
            background: #fee2e2;
            color: #991b1b;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-size: 14px;
            display: none;
        }
        .error-message.show {
            display: block;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="login-header">
            <h1>📡 智通星资讯管理</h1>
            <p style="color: #6b7280; font-size: 14px; margin-top: 8px;">基于关键词监控的 Webhook 消息推送服务</p>
            <p style="color: #9ca3af; font-size: 13px; margin-top: 4px;">请登录以继续</p>
        </div>
        <div class="error-message" id="errorMessage"></div>
        <form id="loginForm" onsubmit="handleLogin(event)">
            <div class="form-group">
                <label for="username">用户名</label>
                <input type="text" id="username" name="username" required autofocus>
            </div>
            <div class="form-group">
                <label for="password">密码</label>
                <input type="password" id="password" name="password" required>
            </div>
            <button type="submit" class="btn-login">登录</button>
        </form>
    </div>
    <script>
        async function handleLogin(event) {
            event.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const errorDiv = document.getElementById('errorMessage');
            
            errorDiv.classList.remove('show');
            
            try {
                const response = await fetch('/api/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    window.location.reload();
                } else {
                    errorDiv.textContent = result.error || '登录失败';
                    errorDiv.classList.add('show');
                }
            } catch (error) {
                errorDiv.textContent = '登录请求失败: ' + error.message;
                errorDiv.classList.add('show');
            }
        }
    </script>
</body>
</html>
"""

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>智通星资讯管理 - 基于关键词监控的 Webhook 消息推送服务</title>
    <style>
        * { 
            box-sizing: border-box; 
            margin: 0; 
            padding: 0; 
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            line-height: 1.6;
        }
        
        .container {
            max-width: 1600px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 25px 80px rgba(0, 0, 0, 0.15);
            overflow: hidden;
            animation: fadeIn 0.5s ease-in;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 32px 30px;
            text-align: left;
            position: relative;
            overflow: hidden;
            z-index: 1000;
        }
        
        .header::before {
            content: '';
            position: absolute;
            top: -50%;
            right: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
            animation: rotate 20s linear infinite;
        }
        
        @keyframes rotate {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
        
        .header h1 { 
            font-size: 32px; 
            margin-bottom: 8px; 
            font-weight: 700;
            position: relative;
            z-index: 1;
            text-shadow: 0 2px 10px rgba(0,0,0,0.2);
        }
        
        .header p {
            font-size: 14px;
            opacity: 0.95;
            position: relative;
            z-index: 1;
            margin: 0;
        }
        
        .tabs {
            display: flex;
            background: linear-gradient(to bottom, #f8f9fa, #ffffff);
            border-bottom: 2px solid #e9ecef;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        
        .tab {
            flex: 1;
            padding: 18px 30px;
            background: transparent;
            border: none;
            cursor: pointer;
            font-size: 15px;
            font-weight: 600;
            color: #6b7280;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            border-bottom: 3px solid transparent;
            position: relative;
        }
        
        .tab::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            width: 0;
            height: 3px;
            background: linear-gradient(90deg, #667eea, #764ba2);
            transition: width 0.3s ease;
        }
        
        .tab.active {
            background: white;
            color: #667eea;
        }
        
        .tab.active::after {
            width: 100%;
        }
        
        .tab:hover {
            background: rgba(102, 126, 234, 0.05);
            color: #667eea;
        }
        
        .tab-content {
            display: none;
            padding: 0;
            background: #fafbfc;
        }
        
        .tab-content.active {
            display: block;
        }
        
        .toolbar {
            padding: 24px 32px;
            background: white;
            border-bottom: 1px solid #e9ecef;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        }
        
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            display: inline-flex;
            align-items: center;
            gap: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        
        .btn:active {
            transform: translateY(0);
        }
        
        .btn-primary { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; 
        }
        
        .btn-primary:hover { 
            background: linear-gradient(135deg, #5568d3 0%, #6b3fa8 100%);
        }
        
        .btn-success { 
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white; 
        }
        
        .btn-success:hover { 
            background: linear-gradient(135deg, #059669 0%, #047857 100%);
        }
        
        .btn-danger {
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
            color: white;
        }
        
        .btn-danger:hover {
            background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
        }
        
        .btn-warning {
            background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
            color: white;
            animation: pulse 2s infinite;
        }
        
        .btn-warning:hover {
            background: linear-gradient(135deg, #d97706 0%, #b45309 100%);
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.8; }
        }
        
        .status {
            padding: 10px 18px;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 500;
            display: none;
            animation: slideIn 0.3s ease;
        }
        
        @keyframes slideIn {
            from { opacity: 0; transform: translateX(-10px); }
            to { opacity: 1; transform: translateX(0); }
        }
        
        .status.success { 
            background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
            color: #065f46; 
            border: 1px solid #6ee7b7;
        }
        
        .status.error { 
            background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
            color: #991b1b; 
            border: 1px solid #fca5a5;
            white-space: pre-line;
            max-width: 600px;
        }
        
        .status.loading { 
            background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
            color: #1e40af; 
            border: 1px solid #93c5fd;
        }
        
        /* 自定义提示框样式 */
        .custom-toast {
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 16px 24px;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
            z-index: 10000;
            display: none;
            animation: slideInRight 0.3s ease, fadeOut 0.3s ease 2.7s forwards;
            max-width: 400px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            backdrop-filter: blur(10px);
        }
        
        .custom-toast.success {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            box-shadow: 0 10px 30px rgba(16, 185, 129, 0.4);
        }
        
        .custom-toast.info {
            background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
            box-shadow: 0 10px 30px rgba(59, 130, 246, 0.4);
        }
        
        .custom-toast .toast-header {
            font-weight: 600;
            font-size: 14px;
            margin-bottom: 6px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .custom-toast .toast-message {
            font-size: 13px;
            opacity: 0.95;
        }
        
        @keyframes slideInRight {
            from { opacity: 0; transform: translateX(100px); }
            to { opacity: 1; transform: translateX(0); }
        }
        
        @keyframes fadeOut {
            from { opacity: 1; transform: translateX(0); }
            to { opacity: 0; transform: translateX(20px); }
        }
        
        .main-layout {
            display: flex;
            min-height: calc(100vh - 250px);
        }
        
        .sidebar {
            width: 280px;
            background: linear-gradient(180deg, #f8f9fa 0%, #ffffff 100%);
            border-right: 2px solid #e5e7eb;
            padding: 20px 0;
            overflow-y: auto;
            box-shadow: 2px 0 8px rgba(0,0,0,0.05);
        }
        
        .sidebar::-webkit-scrollbar {
            width: 6px;
        }
        
        .sidebar::-webkit-scrollbar-thumb {
            background: #cbd5e1;
            border-radius: 3px;
        }
        
        .menu-item {
            padding: 14px 24px;
            cursor: pointer;
            transition: all 0.3s ease;
            border-left: 3px solid transparent;
            display: flex;
            align-items: center;
            gap: 12px;
            color: #4b5563;
            font-weight: 500;
        }
        
        .menu-item:hover {
            background: rgba(102, 126, 234, 0.08);
            color: #667eea;
        }
        
        .menu-item.active {
            background: linear-gradient(90deg, rgba(102, 126, 234, 0.1) 0%, rgba(102, 126, 234, 0.05) 100%);
            color: #667eea;
            border-left-color: #667eea;
            font-weight: 600;
        }
        
        .menu-item .icon {
            font-size: 18px;
            width: 24px;
            text-align: center;
        }
        
        .menu-group {
            margin-bottom: 8px;
        }
        
        .menu-group-title {
            padding: 12px 24px;
            font-size: 12px;
            font-weight: 700;
            color: #9ca3af;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .content-area {
            flex: 1;
            padding: 32px;
            overflow-y: auto;
            background: #fafbfc;
        }
        
        .content-panel {
            display: none;
            animation: fadeIn 0.3s ease;
        }
        
        .content-panel.active {
            display: block;
        }
        
        .content-area::-webkit-scrollbar {
            width: 8px;
        }
        
        .content-area::-webkit-scrollbar-track {
            background: #f1f1f1;
            border-radius: 10px;
        }
        
        .content-area::-webkit-scrollbar-thumb {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 10px;
        }
        
        .section {
            margin-bottom: 24px;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            overflow: hidden;
            background: white;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            transition: all 0.3s ease;
        }
        
        .section:hover {
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        
        .section-header {
            background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
            padding: 18px 24px;
            cursor: pointer;
            font-weight: 600;
            font-size: 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: all 0.3s ease;
            border-bottom: 1px solid #e5e7eb;
        }
        
        .section-header:hover {
            background: linear-gradient(135deg, #f1f3f5 0%, #f8f9fa 100%);
        }
        
        .section-header .icon {
            color: #667eea;
            font-size: 14px;
            font-weight: bold;
            display: inline-block;
            width: 20px;
            text-align: center;
            transition: transform 0.3s ease;
        }
        
        .section-header .icon::before {
            content: '▼';
        }
        
        .section.expanded .section-header .icon::before {
            content: '▲';
        }
        
        .section-content {
            padding: 24px;
            display: none;
            background: white;
        }
        
        .section.expanded .section-content {
            display: block;
            animation: slideDown 0.3s ease;
        }
        
        @keyframes slideDown {
            from { opacity: 0; max-height: 0; }
            to { opacity: 1; max-height: 2000px; }
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            font-size: 14px;
            color: #374151;
        }
        
        .form-group input[type="text"],
        .form-group input[type="number"],
        .form-group input[type="url"],
        .form-group textarea,
        .form-group select {
            width: 100%;
            padding: 12px 16px;
            border: 2px solid #e5e7eb;
            border-radius: 10px;
            font-size: 14px;
            transition: all 0.3s ease;
            background: #fafbfc;
        }
        
        .form-group input:focus,
        .form-group textarea:focus,
        .form-group select:focus {
            outline: none;
            border-color: #667eea;
            background: white;
            box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
        }
        
        .form-group textarea {
            min-height: 100px;
            resize: vertical;
            font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
            line-height: 1.6;
        }
        
        .form-group input[type="checkbox"] {
            width: 20px;
            height: 20px;
            cursor: pointer;
            accent-color: #667eea;
        }
        
        .subscription-item {
            border: 2px solid #e5e7eb;
            border-radius: 16px;
            padding: 28px;
            margin-bottom: 24px;
            background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            transition: all 0.3s ease;
        }
        
        .subscription-item:hover {
            border-color: #667eea;
            box-shadow: 0 4px 16px rgba(102, 126, 234, 0.15);
            transform: translateY(-2px);
        }
        
        .subscription-item h3 {
            margin-bottom: 20px;
            color: #667eea;
            font-size: 20px;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .subscription-item h3::before {
            content: '📌';
            font-size: 24px;
        }
        
        .keyword-list {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 12px;
        }
        
        .keyword-tag {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 500;
            box-shadow: 0 2px 4px rgba(102, 126, 234, 0.3);
        }
        
        .loading {
            text-align: center;
            padding: 60px 40px;
            color: #6b7280;
        }
        
        .loading::after {
            content: '...';
            animation: dots 1.5s steps(4, end) infinite;
        }
        
        @keyframes dots {
            0%, 20% { content: '.'; }
            40% { content: '..'; }
            60%, 100% { content: '...'; }
        }
        
        h4 {
            margin: 24px 0 16px 0;
            color: #374151;
            font-size: 16px;
            font-weight: 600;
        }
        
        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
            margin-left: 8px;
        }
        
        .badge-primary {
            background: #dbeafe;
            color: #1e40af;
        }
        
        .badge-success {
            background: #d1fae5;
            color: #065f46;
        }
        
        .badge-danger {
            background: #fee2e2;
            color: #991b1b;
        }
        
        .subscription-actions {
            transition: all 0.3s ease;
        }
        
        .subscription-actions.has-changes {
            border-color: #f59e0b !important;
            background: #fffbeb !important;
        }
        
        .subscription-status {
            display: flex;
            align-items: center;
            gap: 6px;
        }
        
        .subscription-status::before {
            content: '⚠️';
            font-size: 14px;
        }
        
        .field-error {
            color: #ef4444;
            font-size: 12px;
            margin-top: 4px;
            font-weight: 500;
            display: block;
        }
        
        .form-group input.error,
        .form-group textarea.error {
            border-color: #ef4444 !important;
            box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1);
        }
        
        /* 帮助弹窗样式 */
        .modal-overlay {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.5);
            z-index: 10000;
            animation: fadeIn 0.3s ease;
        }
        
        .modal-overlay.show {
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        
        .modal {
            background: white;
            border-radius: 16px;
            max-width: 900px;
            width: 100%;
            max-height: 90vh;
            overflow-y: auto;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            animation: slideUp 0.3s ease;
            position: relative;
        }
        
        @keyframes slideUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .modal-header {
            padding: 24px 30px;
            border-bottom: 1px solid #e5e7eb;
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: sticky;
            top: 0;
            background: white;
            z-index: 1;
            border-radius: 16px 16px 0 0;
        }
        
        .modal-header h2 {
            font-size: 24px;
            font-weight: 700;
            color: #1e293b;
            margin: 0;
        }
        
        .modal-close {
            background: none;
            border: none;
            font-size: 24px;
            cursor: pointer;
            color: #6b7280;
            padding: 0;
            width: 32px;
            height: 32px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 6px;
            transition: all 0.2s;
        }
        
        .modal-close:hover {
            background: #f3f4f6;
            color: #1e293b;
        }
        
        .modal-body {
            padding: 30px;
        }
        
        .help-section {
            margin-bottom: 32px;
        }
        
        .help-section:last-child {
            margin-bottom: 0;
        }
        
        .help-section h3 {
            font-size: 18px;
            font-weight: 600;
            color: #1e293b;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .help-features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 24px;
        }
        
        .help-feature-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 12px;
            border: 1px solid #e5e7eb;
        }
        
        .help-feature-card .icon {
            font-size: 28px;
            margin-bottom: 12px;
        }
        
        .help-feature-card h4 {
            font-size: 16px;
            font-weight: 600;
            color: #1e293b;
            margin-bottom: 8px;
        }
        
        .help-feature-card p {
            font-size: 13px;
            color: #64748b;
            line-height: 1.6;
            margin: 0;
        }
        
        .help-steps {
            background: #f0f9ff;
            padding: 20px;
            border-radius: 12px;
            border-left: 4px solid #667eea;
        }
        
        .help-steps ol {
            margin: 0;
            padding-left: 24px;
        }
        
        .help-steps li {
            margin-bottom: 12px;
            color: #475569;
            font-size: 14px;
            line-height: 1.7;
        }
        
        .help-steps li:last-child {
            margin-bottom: 0;
        }
        
        .help-steps strong {
            color: #1e293b;
        }
        
        .help-steps p {
            margin-bottom: 12px;
            color: #475569;
            font-size: 14px;
            line-height: 1.7;
        }
        
        .help-steps p:last-child {
            margin-bottom: 0;
        }
        
        .help-steps code {
            background: #e5e7eb;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
            font-size: 12px;
            color: #1e293b;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div style="display: flex; justify-content: space-between; align-items: center; width: 100%; position: relative; z-index: 1001;">
                <div style="flex: 1;">
                    <h1>📡 智通星资讯管理</h1>
                    <p style="font-size: 18px; margin-top: 12px; margin-bottom: 8px;">基于关键词监控的 Webhook 消息推送服务</p>
                    <p style="font-size: 14px; opacity: 0.9; margin-top: 8px;">实时监控多平台热点资讯，通过关键词匹配自动推送到企业微信、飞书、钉钉等 Webhook</p>
                </div>
                <div style="display: flex; gap: 12px; align-items: center;">
                    <button type="button" class="btn btn-secondary" onclick="showHelpModal()" style="padding: 8px 16px; font-size: 14px; position: relative; z-index: 1002; pointer-events: auto; cursor: pointer; background: rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.3);">
                        <span>📖</span> 系统帮助手册
                    </button>
                    <button type="button" class="btn btn-secondary" onclick="handleLogout()" style="padding: 8px 16px; font-size: 14px; position: relative; z-index: 1002; pointer-events: auto; cursor: pointer;">
                        <span>🚪</span> 退出登录
                    </button>
                </div>
            </div>
        </div>
        
        <div class="tabs">
            <button class="tab active" onclick="switchTab('subscriptions')">
                📋 订阅配置 (subscriptions.json) - 主要配置
            </button>
            <button class="tab" onclick="switchTab('config')">
                ⚙️ 系统配置 (config.yaml)
            </button>
            <button class="tab" onclick="switchTab('execute')">
                📤 手动消息推送
            </button>
        </div>
        
        <div id="subscriptions-tab" class="tab-content active">
            <div class="toolbar">
                <div style="display: flex; gap: 12px; align-items: center;">
                    <button type="button" class="btn btn-primary" onclick="loadSubscriptions()">
                        <span>🔄</span> 重新加载
                    </button>
                    <button type="button" class="btn btn-success" id="save-subscriptions-btn" onclick="saveSubscriptions()">
                        <span>💾</span> <span id="save-btn-text">保存所有订阅</span>
                    </button>
                </div>
                <div id="status-subscriptions" class="status"></div>
            </div>
            <div class="main-layout">
                <div class="sidebar" id="subscriptions-sidebar">
                    <div class="menu-group">
                        <div class="menu-group-title">全局设置</div>
                        <div class="menu-item active" onclick="showPanel('global', this)">
                            <span class="icon">⚙️</span>
                            <span>全局配置</span>
                        </div>
                    </div>
                    <div class="menu-group">
                        <div class="menu-group-title">订阅管理</div>
                        <div id="subscriptions-menu-items"></div>
                        <div class="menu-item" onclick="addSubscription()" style="color: #10b981;">
                            <span class="icon">➕</span>
                            <span>添加新订阅</span>
                        </div>
                    </div>
                </div>
                <div class="content-area">
                    <div id="subscriptionsForm" class="loading">正在加载订阅配置</div>
                </div>
            </div>
        </div>
        
        <div id="config-tab" class="tab-content">
            <div class="toolbar">
                <div style="display: flex; gap: 12px; align-items: center;">
                    <button type="button" class="btn btn-primary" onclick="loadConfig()">
                        <span>🔄</span> 重新加载
                    </button>
                    <button type="button" class="btn btn-success" onclick="saveConfig()">
                        <span>💾</span> 保存配置
                    </button>
                </div>
                <div id="status-config" class="status"></div>
            </div>
            <div class="main-layout">
                <div class="sidebar" id="config-sidebar">
                    <div class="menu-group">
                        <div class="menu-group-title">系统配置</div>
                        <div class="menu-item active" onclick="showConfigPanel('app', this)">
                            <span class="icon">📱</span>
                            <span>应用设置</span>
                        </div>
                        <div class="menu-item" onclick="showConfigPanel('crawler', this)">
                            <span class="icon">🕷️</span>
                            <span>爬虫设置</span>
                        </div>
                        <div class="menu-item" onclick="showConfigPanel('report', this)">
                            <span class="icon">📊</span>
                            <span>报告设置</span>
                        </div>
                        <div class="menu-item" onclick="showConfigPanel('notification', this)">
                            <span class="icon">🔔</span>
                            <span>通知设置</span>
                        </div>
                        <div class="menu-item" onclick="showConfigPanel('weight', this)">
                            <span class="icon">⚖️</span>
                            <span>权重设置</span>
                        </div>
                        <div class="menu-item" onclick="showConfigPanel('ai_search', this)">
                            <span class="icon">🤖</span>
                            <span>AI 搜索</span>
                        </div>
                        <div class="menu-item" onclick="showConfigPanel('platforms', this)">
                            <span class="icon">🌐</span>
                            <span>平台配置</span>
                        </div>
                    </div>
                </div>
                <div class="content-area">
                    <div id="configForm" class="loading">正在加载系统配置</div>
                </div>
            </div>
        </div>
        
        <div id="execute-tab" class="tab-content">
            <div class="toolbar">
                <div style="display: flex; gap: 12px; align-items: center;">
                    <button type="button" class="btn btn-success" onclick="executeMain()">
                        <span>📤</span> 立即推送消息
                    </button>
                </div>
                <div id="status-execute" class="status"></div>
            </div>
            <div class="content-area">
                <div style="background: white; border-radius: 12px; padding: 40px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); text-align: center;">
                    <div style="font-size: 48px; margin-bottom: 16px;">📤</div>
                    <h3 style="margin-bottom: 12px; color: #374151; font-size: 20px;">手动消息推送</h3>
                    <p style="color: #6b7280; font-size: 14px; margin-bottom: 24px;">点击上方按钮立即触发消息推送任务</p>
                    <div style="background: #f8f9fa; padding: 16px; border-radius: 8px; border-left: 4px solid #667eea;">
                        <p style="color: #475569; font-size: 13px; margin: 0; line-height: 1.6;">
                            💡 <strong>提示：</strong>推送结果将在弹窗中显示，您可以在弹窗中查看详细的推送日志和结果。
                        </p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- 帮助弹窗 -->
    <div id="helpModal" class="modal-overlay" onclick="if(event.target === this) closeHelpModal()">
        <div class="modal" onclick="event.stopPropagation()">
            <div class="modal-header">
                <h2>📖 系统帮助手册</h2>
                <button class="modal-close" onclick="closeHelpModal()">×</button>
            </div>
            <div class="modal-body">
                <div class="help-section">
                    <h3>🎯 系统功能</h3>
                    <div class="help-features">
                        <div class="help-feature-card">
                            <div class="icon">🔍</div>
                            <h4>多平台监控</h4>
                            <p>实时监控微博、知乎、抖音、今日头条、百度热搜、B站等主流平台的热点资讯，自动抓取最新内容</p>
                        </div>
                        <div class="help-feature-card">
                            <div class="icon">🔑</div>
                            <h4>关键词匹配</h4>
                            <p>配置关键词规则（普通关键词、必含词、排除词），系统自动匹配相关新闻标题，精准筛选目标内容</p>
                        </div>
                        <div class="help-feature-card">
                            <div class="icon">📤</div>
                            <h4>Webhook 推送</h4>
                            <p>配置企业微信、飞书、钉钉等 Webhook 地址，匹配到的新闻自动推送到指定群组，支持定时推送和即时推送</p>
                        </div>
                    </div>
                </div>
                
                <div class="help-section">
                    <h3>🚀 快速开始</h3>
                    <div class="help-steps">
                        <div id="help-quick-start">
                            <ol>
                                <li>在 <strong>订阅配置</strong> 标签页创建订阅规则，填写关键词（用于匹配新闻）和 Webhook 地址（用于接收推送）；</li>
                                <li>在 <strong>系统配置</strong> 标签页配置监控平台、爬虫参数、AI 搜索等系统级设置；</li>
                                <li>在 <strong>手动消息推送</strong> 标签页手动触发一次推送测试，验证配置是否正确。</li>
                            </ol>
                        </div>
                    </div>
                </div>
                
                <div class="help-section">
                    <h3>📋 订阅配置说明</h3>
                    <div class="help-steps">
                        <p style="margin-bottom: 12px; color: #475569; font-size: 14px; line-height: 1.7;">
                            <strong>关键词配置：</strong><br>
                            • <strong>普通关键词</strong>：新闻标题包含任意一个关键词即可匹配<br>
                            • <strong>必含词</strong>：新闻标题必须包含所有必含词才会匹配<br>
                            • <strong>排除词</strong>：包含排除词的新闻将被过滤掉<br>
                            • <strong>数量限制</strong>：限制每个订阅最多推送的新闻数量（0 表示不限制）
                        </p>
                        <p style="margin-bottom: 12px; color: #475569; font-size: 14px; line-height: 1.7;">
                            <strong>Webhook 配置：</strong><br>
                            • 支持企业微信、飞书、钉钉等多种 Webhook 类型<br>
                            • 每个订阅可以配置多个 Webhook，消息会同时推送到所有配置的地址<br>
                            • Webhook URL 格式：企业微信为 <code>https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx</code>
                        </p>
                        <p style="margin-bottom: 0; color: #475569; font-size: 14px; line-height: 1.7;">
                            <strong>定时推送：</strong><br>
                            • 使用 Cron 表达式配置推送时间，例如 <code>0 8 * * *</code> 表示每天 8 点推送<br>
                            • 支持时区设置，默认为 Asia/Shanghai
                        </p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- 帮助弹窗 -->
    <div id="helpModal" class="modal-overlay" onclick="if(event.target === this) closeHelpModal()">
        <div class="modal" onclick="event.stopPropagation()">
            <div class="modal-header">
                <h2>📖 系统帮助手册</h2>
                <button class="modal-close" onclick="closeHelpModal()">×</button>
            </div>
            <div class="modal-body">
                <div class="help-section">
                    <h3>🎯 系统功能</h3>
                    <div class="help-features">
                        <div class="help-feature-card">
                            <div class="icon">🔍</div>
                            <h4>多平台监控</h4>
                            <p>实时监控微博、知乎、抖音、今日头条、百度热搜、B站等主流平台的热点资讯，自动抓取最新内容</p>
                        </div>
                        <div class="help-feature-card">
                            <div class="icon">🔑</div>
                            <h4>关键词匹配</h4>
                            <p>配置关键词规则（普通关键词、必含词、排除词），系统自动匹配相关新闻标题，精准筛选目标内容</p>
                        </div>
                        <div class="help-feature-card">
                            <div class="icon">📤</div>
                            <h4>Webhook 推送</h4>
                            <p>配置企业微信、飞书、钉钉等 Webhook 地址，匹配到的新闻自动推送到指定群组，支持定时推送和即时推送</p>
                        </div>
                    </div>
                </div>
                
                <div class="help-section">
                    <h3>🚀 快速开始</h3>
                    <div class="help-steps">
                        <div id="help-quick-start">
                            <ol>
                                <li>在 <strong>订阅配置</strong> 标签页创建订阅规则，填写关键词（用于匹配新闻）和 Webhook 地址（用于接收推送）；</li>
                                <li>在 <strong>系统配置</strong> 标签页配置监控平台、爬虫参数、AI 搜索等系统级设置；</li>
                                <li>在 <strong>手动消息推送</strong> 标签页手动触发一次推送测试，验证配置是否正确。</li>
                            </ol>
                        </div>
                    </div>
                </div>
                
                <div class="help-section">
                    <h3>📋 订阅配置说明</h3>
                    <div class="help-steps">
                        <p style="margin-bottom: 12px; color: #475569; font-size: 14px; line-height: 1.7;">
                            <strong>关键词配置：</strong><br>
                            • <strong>普通关键词</strong>：新闻标题包含任意一个关键词即可匹配<br>
                            • <strong>必含词</strong>：新闻标题必须包含所有必含词才会匹配<br>
                            • <strong>排除词</strong>：包含排除词的新闻将被过滤掉<br>
                            • <strong>数量限制</strong>：限制每个订阅最多推送的新闻数量（0 表示不限制）
                        </p>
                        <p style="margin-bottom: 12px; color: #475569; font-size: 14px; line-height: 1.7;">
                            <strong>Webhook 配置：</strong><br>
                            • 支持企业微信、飞书、钉钉等多种 Webhook 类型<br>
                            • 每个订阅可以配置多个 Webhook，消息会同时推送到所有配置的地址<br>
                            • Webhook URL 格式：企业微信为 <code>https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx</code>
                        </p>
                        <p style="margin-bottom: 0; color: #475569; font-size: 14px; line-height: 1.7;">
                            <strong>定时推送：</strong><br>
                            • 使用 Cron 表达式配置推送时间，例如 <code>0 8 * * *</code> 表示每天 8 点推送<br>
                            • 支持时区设置，默认为 Asia/Shanghai
                        </p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- 推送结果弹窗 -->
    <div id="pushResultModal" class="modal-overlay" onclick="if(event.target === this) closePushResultModal()">
        <div class="modal" onclick="event.stopPropagation()" style="max-width: 1000px;">
            <div class="modal-header">
                <h2>📤 推送结果</h2>
                <button class="modal-close" onclick="closePushResultModal()">×</button>
            </div>
            <div class="modal-body" style="padding: 0;">
                <div id="execute-result" style="background: #1e293b; color: #e2e8f0; padding: 24px; font-family: 'Monaco', 'Menlo', 'Consolas', monospace; font-size: 13px; line-height: 1.6; min-height: 300px; max-height: 70vh; overflow-y: auto; white-space: pre-wrap; word-wrap: break-word; border-radius: 0 0 16px 16px;">
                    <div style="color: #94a3b8;">等待推送任务...</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let subscriptionsData = {};
        let configData = {};
        let currentTab = 'subscriptions';
        let userRole = 'admin'; // 默认管理员，页面加载后会更新
        
        // 显示帮助弹窗
        function showHelpModal() {
            const modal = document.getElementById('helpModal');
            if (modal) {
                // 根据用户角色更新帮助内容
                updateHelpContent();
                modal.classList.add('show');
                document.body.style.overflow = 'hidden'; // 防止背景滚动
            }
        }
        
        // 根据用户角色更新帮助内容
        function updateHelpContent() {
            const quickStartSection = document.getElementById('help-quick-start');
            if (quickStartSection) {
                if (userRole === 'admin') {
                    // 管理员：显示完整步骤
                    quickStartSection.innerHTML = `
                        <ol>
                            <li>在 <strong>订阅配置</strong> 标签页创建订阅规则，填写关键词（用于匹配新闻）和 Webhook 地址（用于接收推送）；</li>
                            <li>在 <strong>系统配置</strong> 标签页配置监控平台、爬虫参数、AI 搜索等系统级设置；</li>
                            <li>在 <strong>手动消息推送</strong> 标签页手动触发一次推送测试，验证配置是否正确。</li>
                        </ol>
                    `;
                } else {
                    // 普通用户：不显示系统配置步骤
                    quickStartSection.innerHTML = `
                        <ol>
                            <li>在 <strong>订阅配置</strong> 标签页创建订阅规则，填写关键词（用于匹配新闻）和 Webhook 地址（用于接收推送）；</li>
                            <li>在 <strong>手动消息推送</strong> 标签页手动触发一次推送测试，验证配置是否正确。</li>
                        </ol>
                        <p style="margin-top: 12px; color: #64748b; font-size: 13px; font-style: italic;">
                            💡 提示：系统级配置需要管理员权限，如有需要请联系管理员。
                        </p>
                    `;
                }
            }
        }
        
        // 关闭帮助弹窗
        function closeHelpModal() {
            const modal = document.getElementById('helpModal');
            if (modal) {
                modal.classList.remove('show');
                document.body.style.overflow = ''; // 恢复滚动
            }
        }
        
        // 按 ESC 键关闭弹窗（统一处理，在下面定义）
        
        function switchTab(tab) {
            // 权限检查：普通用户不能访问系统配置
            if (tab === 'config' && userRole === 'user') {
                alert('您没有权限访问系统配置');
                return;
            }
            
            currentTab = tab;
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            
            // 安全地激活对应的 tab 按钮
            const tabs = document.querySelectorAll('.tab');
            tabs.forEach(tabEl => {
                const onclickAttr = tabEl.getAttribute('onclick');
                if (onclickAttr && onclickAttr.includes(`switchTab('${tab}')`)) {
                    tabEl.classList.add('active');
                }
            });
            
            // 安全地激活对应的 tab 内容
            const tabContent = document.getElementById(`${tab}-tab`);
            if (tabContent) {
                tabContent.classList.add('active');
            }
            
            if (tab === 'subscriptions' && !subscriptionsData.version) {
                loadSubscriptions();
            } else if (tab === 'config' && !configData.app) {
                loadConfig();
            }
            // execute 标签页不需要预加载
        }
        
        // 手动推送消息
        async function executeMain() {
            // 显示推送结果弹窗
            showPushResultModal();
            const resultDiv = document.getElementById('execute-result');
            resultDiv.innerHTML = '<div style="color: #94a3b8;">正在执行推送任务，请稍候...</div>';
            showStatus('execute', 'loading', '正在推送消息...');
            
            try {
                const response = await fetch('/api/execute', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
                
                const result = await response.json();
                
                if (result.success) {
                    // 显示执行结果
                    let output = result.output || '';
                    if (result.error) {
                        output += '\\n\\n[错误]\\n' + result.error;
                    }
                    
                    // 格式化输出：先转义HTML，然后替换所有换行符（包括 \\n、\\r\\n、\\r）
                    let escapedOutput = escapeHtml(output);
                    // 替换所有类型的换行符为 <br>
                    escapedOutput = escapedOutput.replace(/\\r\\n/g, '<br>').replace(/\\n/g, '<br>').replace(/\\r/g, '<br>');
                    resultDiv.innerHTML = escapedOutput;
                    showStatus('execute', 'success', '任务执行完成');
                } else {
                    let errorOutput = result.output || '';
                    if (result.error) {
                        errorOutput += '\\n\\n[错误]\\n' + result.error;
                    }
                    // 同样处理错误输出的换行符
                    let escapedError = escapeHtml(errorOutput);
                    escapedError = escapedError.replace(/\\r\\n/g, '<br>').replace(/\\n/g, '<br>').replace(/\\r/g, '<br>');
                    resultDiv.innerHTML = '<div style="color: #fca5a5;">' + escapedError + '</div>';
                    showStatus('execute', 'error', result.error || '执行失败');
                }
            } catch (error) {
                resultDiv.innerHTML = '<div style="color: #fca5a5;">请求失败: ' + escapeHtml(error.message) + '</div>';
                showError('execute', '推送任务失败: ' + error.message);
            }
        }
        
        // 显示推送结果弹窗
        function showPushResultModal() {
            const modal = document.getElementById('pushResultModal');
            if (modal) {
                modal.classList.add('show');
                document.body.style.overflow = 'hidden';
            }
        }
        
        // 关闭推送结果弹窗
        function closePushResultModal() {
            const modal = document.getElementById('pushResultModal');
            if (modal) {
                modal.classList.remove('show');
                document.body.style.overflow = '';
            }
        }
        
        // 按 ESC 键关闭推送结果弹窗
        document.addEventListener('keydown', function(event) {
            if (event.key === 'Escape') {
                const helpModal = document.getElementById('helpModal');
                const pushModal = document.getElementById('pushResultModal');
                if (helpModal && helpModal.classList.contains('show')) {
                    closeHelpModal();
                } else if (pushModal && pushModal.classList.contains('show')) {
                    closePushResultModal();
                }
            }
        });
        
        // 自定义提示框函数
        function showToast(message, type = 'info', duration = 3000) {
            // 移除现有的提示框
            const existingToast = document.querySelector('.custom-toast');
            if (existingToast) {
                existingToast.remove();
            }
            
            // 创建新的提示框
            const toast = document.createElement('div');
            toast.className = `custom-toast ${type}`;
            toast.innerHTML = `
                <div class="toast-header">
                    <span>🌟</span>
                    <span>智通星资讯管理提醒</span>
                </div>
                <div class="toast-message">${message}</div>
            `;
            
            // 添加到页面
            document.body.appendChild(toast);
            
            // 显示提示框
            toast.style.display = 'block';
            
            // 自动移除
            setTimeout(() => {
                if (toast && toast.parentNode) {
                    toast.remove();
                }
            }, duration);
        }
        
        // 处理401未授权错误
        function handleUnauthorized(response) {
            if (response.status === 401) {
                window.location.reload();
                return true;
            }
            return false;
        }
        
        // 登出功能 - 提前定义确保全局可用
        async function handleLogout() {
            try {
                if (confirm('确定要退出登录吗？')) {
                    const response = await fetch('/api/logout', { method: 'POST' });
                    if (response.ok) {
                        window.location.reload();
                    } else {
                        alert('退出登录失败，请刷新页面重试');
                        window.location.reload();
                    }
                }
            } catch (error) {
                console.error('登出失败:', error);
                alert('退出登录失败: ' + error.message);
                window.location.reload();
            }
        }
        
        // 订阅配置相关函数
        async function loadSubscriptions() {
            const form = document.getElementById('subscriptionsForm');
            // 显示加载状态
            if (form) {
                form.innerHTML = '<div class="loading">正在加载订阅配置</div>';
            }
            showStatus('subscriptions', 'loading', '正在加载订阅配置...');
            try {
                const response = await fetch('/api/subscriptions');
                if (handleUnauthorized(response)) return;
                
                if (!response.ok) {
                    throw new Error(`HTTP错误: ${response.status}`);
                }
                
                const data = await response.json();
                if (data.error) {
                    if (form) {
                        form.innerHTML = `<div style="padding: 40px; text-align: center; color: #ef4444;">加载失败: ${escapeHtml(data.error)}</div>`;
                    }
                    showError('subscriptions', data.error);
                    return;
                }
                
                if (!data || !data.subscriptions) {
                    throw new Error('返回的数据格式不正确');
                }
                
                subscriptionsData = data;
                originalSubscriptionsData = JSON.parse(JSON.stringify(data)); // 深拷贝保存原始数据
                
                // 确保form存在再渲染
                if (form) {
                    renderSubscriptionsForm(data);
                } else {
                    console.error('无法找到subscriptionsForm元素');
                    showError('subscriptions', '页面元素未找到，请刷新页面重试');
                }
                
                hasUnsavedChanges = false;
                updateSaveButtonState();
                showStatus('subscriptions', 'success', '订阅配置加载成功');
            } catch (error) {
                console.error('加载订阅配置失败:', error);
                if (form) {
                    form.innerHTML = `<div style="padding: 40px; text-align: center; color: #ef4444;">加载失败: ${escapeHtml(error.message)}<br><button onclick="loadSubscriptions()" style="margin-top: 20px; padding: 8px 16px; background: #667eea; color: white; border: none; border-radius: 6px; cursor: pointer;">重试</button></div>`;
                }
                showError('subscriptions', '加载订阅配置失败: ' + error.message);
            }
        }
        
        async function saveSubscriptions() {
            if (!collectSubscriptionsData()) {
                showError('subscriptions', '请先填写完整的配置信息');
                return;
            }
            
            // 保存前验证必填项，并跳转到第一个错误字段
            const firstErrorField = validateAndFindFirstError();
            if (firstErrorField) {
                // 确保对应的订阅面板是展开的
                const subscriptionItem = firstErrorField.closest('.subscription-item');
                if (subscriptionItem) {
                    const subIndex = subscriptionItem.getAttribute('data-index');
                    if (subIndex !== null) {
                        // 切换到对应的订阅面板
                        showPanel(`sub_${subIndex}`);
                        // 展开包含该字段的section
                        const section = firstErrorField.closest('.section');
                        if (section) {
                            section.classList.add('expanded');
                        }
                    }
                }
                
                // 滚动到错误字段并聚焦
                setTimeout(() => {
                    firstErrorField.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    setTimeout(() => {
                        firstErrorField.focus();
                        // 如果是textarea，选中所有文本
                        if (firstErrorField.tagName === 'TEXTAREA') {
                            firstErrorField.select();
                        }
                    }, 300);
                }, 100);
                
                showError('subscriptions', '请先填写所有必填项');
                return;
            }
            
            showStatus('subscriptions', 'loading', '正在保存订阅配置...');
            try {
                const response = await fetch('/api/subscriptions', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(subscriptionsData)
                });
                if (handleUnauthorized(response)) return;
                const result = await response.json();
                if (result.success) {
                    showStatus('subscriptions', 'success', result.message || '订阅配置保存成功');
                    // 更新原始数据
                    originalSubscriptionsData = JSON.parse(JSON.stringify(subscriptionsData));
                    // 更新所有订阅的原始数据
                    subscriptionsData.subscriptions.forEach((sub, index) => {
                        originalSubscriptions[index] = JSON.parse(JSON.stringify(sub));
                        subscriptionChanges[index] = false;
                    });
                    hasUnsavedChanges = false;
                    updateSaveButtonState();
                    updateSubscriptionChangeStatus();
                    // 清除所有验证错误提示
                    clearAllValidationErrors();
                } else {
                    showError('subscriptions', result.error || '保存失败');
                }
            } catch (error) {
                showError('subscriptions', '保存订阅配置失败: ' + error.message);
            }
        }
        
        // 验证必填项并返回第一个错误字段
        function validateAndFindFirstError() {
            let firstErrorField = null;
            
            subscriptionsData.subscriptions.forEach((sub, index) => {
                // 验证订阅名称（必填项）
                const subName = sub.name || '';
                if (!subName.trim()) {
                    const field = document.getElementById(`sub_${index}_name`);
                    if (field && !firstErrorField) {
                        firstErrorField = field;
                        showFieldError(field, '订阅名称不能为空');
                    }
                }
                
                // 验证普通关键词（必填项）
                const normalKeywords = sub.keywords?.normal || [];
                if (normalKeywords.length === 0 || normalKeywords.every(k => !k.trim())) {
                    const field = document.getElementById(`sub_${index}_keywords_normal`);
                    if (field && !firstErrorField) {
                        firstErrorField = field;
                        showFieldError(field, '普通关键词不能为空，至少填写一个关键词');
                    }
                }
                
                // 验证AI搜索关键词（如果启用AI搜索）
                // 从DOM读取当前值，而不是从数据对象读取
                const aiEnabledField = document.getElementById(`sub_${index}_ai_enabled`);
                if (aiEnabledField && aiEnabledField.checked === true) {
                    const keywordsField = document.getElementById(`sub_${index}_ai_keywords`);
                    if (keywordsField) {
                        const keywordsValue = keywordsField.value || '';
                        const keywords = keywordsValue.split(String.fromCharCode(10)).filter(k => k.trim());
                        if (keywords.length === 0) {
                            if (!firstErrorField) {
                                firstErrorField = keywordsField;
                                showFieldError(keywordsField, 'AI搜索已启用，搜索关键词不能为空');
                            }
                        }
                    }
                }
                
                // 验证Webhooks
                if (sub.webhooks && sub.webhooks.length > 0) {
                    sub.webhooks.forEach((wh, whIndex) => {
                        if (!wh.url || !wh.url.trim()) {
                            const field = document.getElementById(`sub_${index}_webhook_${whIndex}_url`);
                            if (field && !firstErrorField) {
                                firstErrorField = field;
                                showFieldError(field, 'Webhook URL 不能为空');
                            }
                        }
                        if (!wh.name || !wh.name.trim()) {
                            const field = document.getElementById(`sub_${index}_webhook_${whIndex}_name`);
                            if (field && !firstErrorField) {
                                firstErrorField = field;
                                showFieldError(field, 'Webhook 名称不能为空');
                            }
                        }
                    });
                }
            });
            
            return firstErrorField;
        }
        
        // 显示字段错误
        function showFieldError(field, message) {
            const errorMsgId = field.id + '_error';
            let errorMsg = document.getElementById(errorMsgId);
            
            if (!errorMsg) {
                errorMsg = document.createElement('div');
                errorMsg.id = errorMsgId;
                errorMsg.className = 'field-error';
                field.parentElement.appendChild(errorMsg);
            }
            errorMsg.textContent = message;
            field.classList.add('error');
        }
        
        // 实时验证函数
        function validateField(fieldId, fieldType, subIndex, whIndex) {
            const field = document.getElementById(fieldId);
            if (!field) return;
            
            const errorMsgId = fieldId + '_error';
            let errorMsg = document.getElementById(errorMsgId);
            
            let isValid = true;
            let message = '';
            
            if (fieldType === 'ai_keywords') {
                // 验证AI搜索关键词
                const aiEnabled = document.getElementById(`sub_${subIndex}_ai_enabled`)?.checked === true;
                if (aiEnabled) {
                    const value = field.value || '';
                    const keywords = value.split(String.fromCharCode(10)).filter(k => k.trim());
                    if (keywords.length === 0) {
                        isValid = false;
                        message = 'AI搜索已启用，搜索关键词不能为空';
                    }
                }
            } else if (fieldType === 'webhook_url') {
                // 验证Webhook URL
                const value = field.value || '';
                if (!value.trim()) {
                    isValid = false;
                    message = 'Webhook URL 不能为空';
                }
            } else if (fieldType === 'webhook_name') {
                // 验证Webhook 名称
                const value = field.value || '';
                if (!value.trim()) {
                    isValid = false;
                    message = 'Webhook 名称不能为空';
                }
            }
            
            // 显示或隐藏错误提示
            if (!isValid) {
                if (!errorMsg) {
                    errorMsg = document.createElement('div');
                    errorMsg.id = errorMsgId;
                    errorMsg.className = 'field-error';
                    field.parentElement.appendChild(errorMsg);
                }
                errorMsg.textContent = message;
                field.classList.add('error');
            } else {
                if (errorMsg) {
                    errorMsg.remove();
                }
                field.classList.remove('error');
            }
            
            return isValid;
        }
        
        // 清除所有验证错误
        function clearAllValidationErrors() {
            document.querySelectorAll('.field-error').forEach(el => el.remove());
            document.querySelectorAll('#subscriptionsForm input, #subscriptionsForm textarea').forEach(field => {
                field.classList.remove('error');
            });
        }
        
        let currentSubscriptionsPanel = 'global';
        let currentConfigPanel = 'app';
        let hasUnsavedChanges = false;
        let originalSubscriptionsData = null;
        let subscriptionChanges = {}; // 跟踪每个订阅的变更状态 {index: true/false}
        let originalSubscriptions = {}; // 保存每个订阅的原始数据
        
        function showPanel(panelName, element, skipChangeCheck = false) {
            // 权限检查：普通用户不能访问全局设置面板
            if (panelName === 'global' && userRole === 'user') {
                // 普通用户尝试访问全局设置时，切换到第一个订阅
                const firstSub = document.querySelector('#subscriptions-sidebar .menu-item[onclick*="sub_"]');
                if (firstSub) {
                    firstSub.click();
                } else {
                    alert('您没有权限访问全局设置');
                }
                return;
            }
            
            // 检查当前订阅是否有未保存的变更
            if (!skipChangeCheck && panelName.startsWith('sub_')) {
                const currentSubIndex = parseInt(currentSubscriptionsPanel.replace('sub_', ''));
                if (!isNaN(currentSubIndex) && subscriptionChanges[currentSubIndex]) {
                    if (!confirm('当前订阅有未保存的变更，是否先保存或取消？\\n\\n点击"确定"继续切换（变更将丢失），点击"取消"返回。')) {
                        return;
                    }
                }
            }
            
            currentSubscriptionsPanel = panelName;
            document.querySelectorAll('#subscriptions-sidebar .menu-item').forEach(item => {
                item.classList.remove('active');
            });
            if (element) {
                element.closest('.menu-item').classList.add('active');
            } else {
                document.querySelector(`#subscriptions-sidebar .menu-item[onclick*="${panelName}"]`)?.classList.add('active');
            }
            
            document.querySelectorAll('#subscriptionsForm .content-panel').forEach(panel => {
                panel.classList.remove('active');
            });
            const targetPanel = document.getElementById(`panel-${panelName}`);
            if (targetPanel) {
                targetPanel.classList.add('active');
            }
            
            // 更新当前订阅的变更状态显示
            updateSubscriptionChangeStatus();
        }
        
        function showConfigPanel(panelName, element) {
            currentConfigPanel = panelName;
            document.querySelectorAll('#config-sidebar .menu-item').forEach(item => {
                item.classList.remove('active');
            });
            if (element) {
                element.closest('.menu-item').classList.add('active');
            } else {
                document.querySelector(`#config-sidebar .menu-item[onclick*="${panelName}"]`)?.classList.add('active');
            }
            
            document.querySelectorAll('#configForm .content-panel').forEach(panel => {
                panel.classList.remove('active');
            });
            const targetPanel = document.getElementById(`config-panel-${panelName}`);
            if (targetPanel) {
                targetPanel.classList.add('active');
            }
        }
        
        function renderSubscriptionsForm(data) {
            const form = document.getElementById('subscriptionsForm');
            if (!form) {
                console.error('无法找到subscriptionsForm元素');
                return;
            }
            
            if (!data) {
                console.error('数据为空');
                form.innerHTML = '<div style="padding: 40px; text-align: center; color: #ef4444;">数据为空</div>';
                return;
            }
            
            // 保存原始订阅数据
            (data.subscriptions || []).forEach((sub, index) => {
                originalSubscriptions[index] = JSON.parse(JSON.stringify(sub));
                subscriptionChanges[index] = false;
            });
            
            // 渲染菜单项
            const menuItems = document.getElementById('subscriptions-menu-items');
            let menuHtml = '';
            (data.subscriptions || []).forEach((sub, index) => {
                menuHtml += `
                    <div class="menu-item" onclick="showPanel('sub_${index}', this)" data-sub-index="${index}">
                        <span class="icon">📋</span>
                        <span>${sub.name || '未命名订阅'}</span>
                        ${subscriptionChanges[index] ? '<span style="color: #f59e0b; margin-left: 8px;">●</span>' : ''}
                    </div>
                `;
            });
            menuItems.innerHTML = menuHtml;
            
            // 根据用户角色决定是否渲染全局设置面板
            let html = '';
            if (userRole === 'admin') {
                html = `
                <div id="panel-global" class="content-panel active">
                    <div class="section expanded">
                        <div class="section-header" onclick="this.parentElement.classList.toggle('expanded')">
                            <span>全局设置</span>
                            <span class="icon"></span>
                        </div>
                        <div class="section-content">
                            <div class="form-group">
                                <label>版本</label>
                                <input type="text" id="sub_version" value="${escapeHtml(data.version || '1.0')}" />
                            </div>
                            <div class="form-group">
                                <label>描述</label>
                                <input type="text" id="sub_description" value="${escapeHtml(data.description || '')}" />
                            </div>
                            <h4>报告模式</h4>
                            <div class="form-group">
                                <label>报告模式</label>
                                <select id="sub_report_mode">
                                    <option value="daily" ${data.global_settings?.report_mode === 'daily' ? 'selected' : ''}>daily</option>
                                    <option value="incremental" ${data.global_settings?.report_mode === 'incremental' ? 'selected' : ''}>incremental</option>
                                    <option value="current" ${data.global_settings?.report_mode === 'current' ? 'selected' : ''}>current</option>
                                </select>
                            </div>
                            <h4>平台列表</h4>
                            <div class="form-group">
                                <label>平台ID (每行一个)</label>
                                <textarea id="sub_platforms" style="min-height: 100px;">${escapeHtml((data.global_settings?.platforms || []).join(String.fromCharCode(10)))}</textarea>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            }
            
            // 渲染订阅列表面板
            const subscriptions = data.subscriptions || [];
            if (subscriptions.length === 0) {
                // 如果没有订阅，显示提示信息
                html += '<div class="content-panel active" style="padding: 40px; text-align: center; color: #6b7280;">暂无订阅配置</div>';
            } else {
                // 普通用户：默认显示第一个订阅
                const startIndex = userRole === 'user' ? 0 : -1;
                const firstPanelActive = userRole === 'user' ? 'active' : '';
                
                subscriptions.forEach((sub, index) => {
                    const isActive = (userRole === 'user' && index === 0) ? 'active' : '';
                    html += `
                        <div id="panel-sub_${index}" class="content-panel ${isActive}">
                            ${renderSubscriptionItem(sub, index)}
                        </div>
                    `;
                });
            }
            
            form.innerHTML = html;
            attachChangeListeners(); // 绑定变更监听
        }
        
        // 自动生成订阅ID
        function generateSubscriptionId() {
            const timestamp = Date.now();
            const random = Math.floor(Math.random() * 1000);
            return `sub_${timestamp}_${random}`;
        }
        
        function renderSubscriptionItem(sub, index) {
            const keywords = (sub.keywords?.normal || []).join(String.fromCharCode(10));
            const required = (sub.keywords?.required || []).join(String.fromCharCode(10));
            const excluded = (sub.keywords?.excluded || []).join(String.fromCharCode(10));
            const aiKeywords = (sub.ai_search?.search_keywords || []).join(String.fromCharCode(10));
            const webhooks = sub.webhooks || [];
            
            // 转义HTML特殊字符
            const escapeValue = (val) => {
                if (val == null) return '';
                return String(val).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
            };
            
            // 确保订阅有ID，如果没有则生成一个
            const subscriptionId = sub.id || generateSubscriptionId();
            
            // 判断Cron表达式是否为预设值
            const cronValue = sub.schedule?.cron || '0 8 * * *';
            const presetCrons = ['0 8 * * *', '0 9 * * *', '0 10 * * *', '0 12 * * *', '0 14 * * *', '0 18 * * *', '0 20 * * *', '0 */2 * * *', '0 */6 * * *', '0 0 * * *', '0 0 * * 1'];
            const isPresetCron = presetCrons.includes(cronValue);
            const selectedPreset = isPresetCron ? cronValue : 'custom';
            
            return `
                <div class="subscription-item" data-index="${index}">
                    <h3>${escapeValue(sub.name) || '未命名订阅'}</h3>
                    <div class="form-group">
                        <label>订阅ID</label>
                        <input type="text" id="sub_${index}_id" value="${escapeValue(subscriptionId)}" readonly style="background-color: #f5f5f5; cursor: not-allowed;" />
                        <div class="help-text" style="color: #6b7280; font-size: 12px; margin-top: 4px;">订阅ID自动生成，不可编辑</div>
                    </div>
                    <div class="form-group">
                        <label>订阅名称 <span style="color: #ef4444;">*</span></label>
                        <input type="text" id="sub_${index}_name" value="${escapeValue(sub.name)}" />
                        <div class="help-text" style="color: #6b7280; font-size: 12px; margin-top: 4px;">此字段为必填项</div>
                    </div>
                    <div class="form-group">
                        <label>
                            <input type="checkbox" id="sub_${index}_enabled" ${sub.enabled !== false ? 'checked' : ''} />
                            启用此订阅
                        </label>
                    </div>
                    <div class="section">
                        <div class="section-header" onclick="this.parentElement.classList.toggle('expanded')">
                            <span>关键词配置</span>
                            <span class="icon"></span>
                        </div>
                        <div class="section-content">
                            <div class="form-group">
                                <label>普通关键词 (每行一个) <span style="color: #ef4444;">*</span></label>
                                <textarea id="sub_${index}_keywords_normal" style="min-height: 120px;" placeholder="至少填写一个关键词，每行一个，例如：&#10;关键词1&#10;关键词2">${escapeValue(keywords)}</textarea>
                                <div class="help-text" style="color: #6b7280; font-size: 12px; margin-top: 4px;">此字段为必填项，用于匹配新闻内容</div>
                            </div>
                            <div class="form-group">
                                <label>必须包含关键词 (每行一个)</label>
                                <textarea id="sub_${index}_keywords_required" style="min-height: 60px;">${escapeValue(required)}</textarea>
                            </div>
                            <div class="form-group">
                                <label>排除关键词 (每行一个)</label>
                                <textarea id="sub_${index}_keywords_excluded" style="min-height: 60px;">${escapeValue(excluded)}</textarea>
                            </div>
                            <div class="form-group">
                                <label>数量限制 (0=不限制)</label>
                                <input type="number" id="sub_${index}_keywords_limit" value="${sub.keywords?.limit || 0}" />
                            </div>
                        </div>
                    </div>
                    <div class="section">
                        <div class="section-header" onclick="this.parentElement.classList.toggle('expanded')">
                            <span>Webhooks 配置</span>
                            <span class="icon"></span>
                        </div>
                        <div class="section-content">
                            ${webhooks.map((wh, whIndex) => `
                                <div style="border: 1px solid #ddd; padding: 15px; margin-bottom: 10px; border-radius: 6px;">
                                    <div class="form-group">
                                        <label>类型</label>
                                        <select id="sub_${index}_webhook_${whIndex}_type">
                                            <option value="wework" ${wh.type === 'wework' ? 'selected' : ''}>企业微信</option>
                                            <option value="feishu" ${wh.type === 'feishu' ? 'selected' : ''}>飞书</option>
                                            <option value="dingtalk" ${wh.type === 'dingtalk' ? 'selected' : ''}>钉钉</option>
                                        </select>
                                    </div>
                                    <div class="form-group">
                                        <label>Webhook URL <span style="color: #ef4444;">*</span></label>
                                        <input type="text" id="sub_${index}_webhook_${whIndex}_url" value="${escapeValue(wh.url)}" placeholder="请输入Webhook URL" data-validate="webhook_url" data-sub-index="${index}" data-wh-index="${whIndex}" />
                                    </div>
                                    <div class="form-group">
                                        <label>名称 <span style="color: #ef4444;">*</span></label>
                                        <input type="text" id="sub_${index}_webhook_${whIndex}_name" value="${escapeValue(wh.name)}" placeholder="请输入Webhook名称" data-validate="webhook_name" data-sub-index="${index}" data-wh-index="${whIndex}" />
                                    </div>
                                    <button type="button" class="btn btn-danger" onclick="removeWebhook(${index}, ${whIndex})">🗑️ 删除</button>
                                </div>
                            `).join('')}
                            <button type="button" class="btn btn-success" onclick="addWebhook(${index})">➕ 添加 Webhook</button>
                        </div>
                    </div>
                    <div class="section">
                        <div class="section-header" onclick="this.parentElement.classList.toggle('expanded')">
                            <span>AI 搜索配置</span>
                            <span class="icon"></span>
                        </div>
                        <div class="section-content">
                            <div class="form-group">
                                <label>
                                    <input type="checkbox" id="sub_${index}_ai_enabled" ${sub.ai_search?.enabled === true ? 'checked' : ''} />
                                    启用 AI 搜索
                                </label>
                            </div>
                            <div class="form-group">
                                <label>触发阈值</label>
                                <input type="number" id="sub_${index}_ai_threshold" value="${sub.ai_search?.trigger_threshold || 3}" />
                                <div class="help-text" style="color: #6b7280; font-size: 12px; margin-top: 4px;">当热搜榜获取数据小于触发阈值时才会触发AI搜索</div>
                            </div>
                            <div class="form-group">
                                <label>搜索关键词 (每行一个) <span style="color: #ef4444;">*</span></label>
                                <textarea id="sub_${index}_ai_keywords" style="min-height: 100px;" placeholder="至少填写一个关键词，每行一个">${escapeValue(aiKeywords)}</textarea>
                                <div class="help-text" style="color: #6b7280; font-size: 12px; margin-top: 4px;">启用AI搜索时，此字段为必填项</div>
                            </div>
                            <div class="form-group">
                                <label>时间范围 (小时)</label>
                                <input type="number" id="sub_${index}_ai_time_range" value="${sub.ai_search?.time_range_hours || 24}" />
                            </div>
                            <div class="form-group">
                                <label>最大结果数</label>
                                <input type="number" id="sub_${index}_ai_max_results" value="${sub.ai_search?.max_results || 30}" />
                            </div>
                        </div>
                    </div>
                    <div class="section">
                        <div class="section-header" onclick="this.parentElement.classList.toggle('expanded')">
                            <span>定时任务配置</span>
                            <span class="icon"></span>
                        </div>
                        <div class="section-content">
                            <div class="form-group">
                                <label>
                                    <input type="checkbox" id="sub_${index}_schedule_enabled" ${sub.schedule?.enabled !== false ? 'checked' : ''} />
                                    启用定时任务
                                </label>
                            </div>
                            <div class="form-group">
                                <label>执行时间</label>
                                <select id="sub_${index}_schedule_preset" onchange="updateCronFromPreset(${index})" style="margin-bottom: 8px;">
                                    <option value="0 8 * * *" ${selectedPreset === '0 8 * * *' ? 'selected' : ''}>每天 08:00</option>
                                    <option value="0 9 * * *" ${selectedPreset === '0 9 * * *' ? 'selected' : ''}>每天 09:00</option>
                                    <option value="0 10 * * *" ${selectedPreset === '0 10 * * *' ? 'selected' : ''}>每天 10:00</option>
                                    <option value="0 12 * * *" ${selectedPreset === '0 12 * * *' ? 'selected' : ''}>每天 12:00</option>
                                    <option value="0 14 * * *" ${selectedPreset === '0 14 * * *' ? 'selected' : ''}>每天 14:00</option>
                                    <option value="0 18 * * *" ${selectedPreset === '0 18 * * *' ? 'selected' : ''}>每天 18:00</option>
                                    <option value="0 20 * * *" ${selectedPreset === '0 20 * * *' ? 'selected' : ''}>每天 20:00</option>
                                    <option value="0 */2 * * *" ${selectedPreset === '0 */2 * * *' ? 'selected' : ''}>每2小时</option>
                                    <option value="0 */6 * * *" ${selectedPreset === '0 */6 * * *' ? 'selected' : ''}>每6小时</option>
                                    <option value="0 0 * * *" ${selectedPreset === '0 0 * * *' ? 'selected' : ''}>每天 00:00（午夜）</option>
                                    <option value="0 0 * * 1" ${selectedPreset === '0 0 * * 1' ? 'selected' : ''}>每周一 00:00</option>
                                    <option value="custom" ${selectedPreset === 'custom' ? 'selected' : ''}>自定义</option>
                                </select>
                                <input type="text" id="sub_${index}_schedule_cron" value="${escapeValue(cronValue)}" placeholder="Cron表达式（如：0 8 * * *）" style="display: ${isPresetCron ? 'none' : 'block'};" />
                                <div class="help-text" style="color: #6b7280; font-size: 12px; margin-top: 4px;">选择预设时间或使用自定义Cron表达式</div>
                            </div>
                            <div class="form-group">
                                <label>时区</label>
                                <input type="text" id="sub_${index}_schedule_timezone" value="${escapeValue(sub.schedule?.timezone || 'Asia/Shanghai')}" />
                            </div>
                        </div>
                    </div>
                    <div class="subscription-actions" style="margin-top: 20px; padding: 16px; background: #f8f9fa; border-radius: 8px; border: 2px solid #e5e7eb;">
                        <div style="display: flex; gap: 12px; align-items: center; justify-content: space-between;">
                            <div style="display: flex; gap: 12px;">
                                <button type="button" class="btn btn-success" id="save-sub-${index}" onclick="saveSingleSubscription(${index})" style="display: none;">
                                    <span>💾</span> 保存订阅变更
                                </button>
                                <button type="button" class="btn btn-secondary" id="cancel-sub-${index}" onclick="cancelSingleSubscription(${index})" style="display: none;">
                                    <span>❌</span> 取消订阅配置
                                </button>
                            </div>
                            <div id="sub-${index}-status" class="subscription-status" style="font-size: 12px; color: #6b7280; display: none;">
                                <span>有未保存的变更</span>
                            </div>
                        </div>
                    </div>
                    <div style="display: flex; gap: 12px; margin-top: 16px;">
                        <button type="button" class="btn btn-success" id="save-sub-top-${index}" onclick="saveSingleSubscription(${index})" style="flex: 1;" disabled>
                            <span>💾</span><span> 保存订阅变更</span>
                        </button>
                        <button type="button" class="btn btn-danger" onclick="removeSubscription(${index})" style="flex: 1;">
                            🗑️ 删除此订阅
                        </button>
                    </div>
                </div>
            `;
        }
        
        function collectSubscriptionsData() {
            try {
                // 如果是普通用户，保留原有的全局设置；如果是管理员，从DOM读取
                let globalSettings = {};
                if (userRole === 'admin') {
                    globalSettings = {
                        report_mode: document.getElementById('sub_report_mode')?.value || 'incremental',
                        platforms: (document.getElementById('sub_platforms')?.value || '').split(String.fromCharCode(10)).filter(p => p.trim()),
                        weight: { rank_weight: 0.6, frequency_weight: 0.3, hotness_weight: 0.1 },
                        push_window: { enabled: false }
                    };
                } else {
                    // 普通用户：保留原有的全局设置
                    globalSettings = subscriptionsData.global_settings || {
                        report_mode: 'incremental',
                        platforms: [],
                        weight: { rank_weight: 0.6, frequency_weight: 0.3, hotness_weight: 0.1 },
                        push_window: { enabled: false }
                    };
                }
                
                subscriptionsData = {
                    version: userRole === 'admin' ? (document.getElementById('sub_version')?.value || '1.0') : (subscriptionsData.version || '1.0'),
                    description: userRole === 'admin' ? (document.getElementById('sub_description')?.value || '') : (subscriptionsData.description || ''),
                    subscriptions: [],
                    global_settings: globalSettings
                };
                
                // 收集所有订阅
                document.querySelectorAll('.subscription-item').forEach((item, index) => {
                    let subId = document.getElementById(`sub_${index}_id`)?.value || '';
                    // 如果ID为空，自动生成
                    if (!subId) {
                        subId = generateSubscriptionId();
                    }
                    const sub = {
                        id: subId,
                        name: document.getElementById(`sub_${index}_name`)?.value || '',
                        enabled: document.getElementById(`sub_${index}_enabled`)?.checked !== false,
                        keywords: {
                            normal: (document.getElementById(`sub_${index}_keywords_normal`)?.value || '').split(String.fromCharCode(10)).filter(k => k.trim()),
                            required: (document.getElementById(`sub_${index}_keywords_required`)?.value || '').split(String.fromCharCode(10)).filter(k => k.trim()),
                            excluded: (document.getElementById(`sub_${index}_keywords_excluded`)?.value || '').split(String.fromCharCode(10)).filter(k => k.trim()),
                            limit: parseInt(document.getElementById(`sub_${index}_keywords_limit`)?.value || '0')
                        },
                        webhooks: [],
                        ai_search: {
                            enabled: document.getElementById(`sub_${index}_ai_enabled`)?.checked === true,
                            trigger_threshold: parseInt(document.getElementById(`sub_${index}_ai_threshold`)?.value || '3'),
                            search_keywords: (document.getElementById(`sub_${index}_ai_keywords`)?.value || '').split(String.fromCharCode(10)).filter(k => k.trim()),
                            time_range_hours: parseInt(document.getElementById(`sub_${index}_ai_time_range`)?.value || '24'),
                            max_results: parseInt(document.getElementById(`sub_${index}_ai_max_results`)?.value || '30')
                        },
                        schedule: {
                            enabled: document.getElementById(`sub_${index}_schedule_enabled`)?.checked !== false,
                            cron: document.getElementById(`sub_${index}_schedule_cron`)?.value || '0 8 * * *',
                            timezone: document.getElementById(`sub_${index}_schedule_timezone`)?.value || 'Asia/Shanghai'
                        }
                    };
                    
                    // 收集 webhooks
                    let whIndex = 0;
                    while (document.getElementById(`sub_${index}_webhook_${whIndex}_type`)) {
                        sub.webhooks.push({
                            type: document.getElementById(`sub_${index}_webhook_${whIndex}_type`)?.value || '',
                            url: document.getElementById(`sub_${index}_webhook_${whIndex}_url`)?.value || '',
                            name: document.getElementById(`sub_${index}_webhook_${whIndex}_name`)?.value || ''
                        });
                        whIndex++;
                    }
                    
                    subscriptionsData.subscriptions.push(sub);
                });
                
                return true;
            } catch (error) {
                console.error('收集订阅数据失败:', error);
                return false;
            }
        }
        
        function addSubscription() {
            const newSub = {
                id: generateSubscriptionId(),
                name: '新订阅',
                enabled: true,
                keywords: { normal: [], required: [], excluded: [], limit: 0 },
                webhooks: [{
                    type: 'wework',
                    url: '',
                    name: ''
                }],
                ai_search: { enabled: false, trigger_threshold: 3, search_keywords: [], time_range_hours: 24, max_results: 30 },
                schedule: { enabled: true, cron: '0 8 * * *', timezone: 'Asia/Shanghai' }
            };
            const newIndex = subscriptionsData.subscriptions.length;
            subscriptionsData.subscriptions.push(newSub);
            originalSubscriptions[newIndex] = JSON.parse(JSON.stringify(newSub));
            subscriptionChanges[newIndex] = false;
            renderSubscriptionsForm(subscriptionsData);
            hasUnsavedChanges = true;
            updateSaveButtonState();
            // 切换到新添加的订阅
            setTimeout(() => {
                const menuItem = document.querySelector(`#subscriptions-sidebar .menu-item[data-sub-index="${newIndex}"]`);
                if (menuItem) {
                    showPanel(`sub_${newIndex}`, menuItem);
                }
            }, 100);
        }
        
        function removeSubscription(index) {
            // 检查是否有未保存的变更
            if (subscriptionChanges[index]) {
                if (!confirm('此订阅有未保存的变更，确定要删除吗？\\n\\n删除后未保存的变更将丢失。')) {
                    return;
                }
            } else {
                if (!confirm('确定要删除此订阅吗？')) {
                    return;
                }
            }
            
            subscriptionsData.subscriptions.splice(index, 1);
            delete subscriptionChanges[index];
            delete originalSubscriptions[index];
            renderSubscriptionsForm(subscriptionsData);
            hasUnsavedChanges = true;
            updateSaveButtonState();
            // 删除后切换到全局配置
            showPanel('global');
            document.querySelector('#subscriptions-sidebar .menu-item').classList.add('active');
        }
        
        // 保存单个订阅
        async function saveSingleSubscription(index) {
            // 先收集当前订阅的数据
            if (!collectSingleSubscriptionData(index)) {
                showError('subscriptions', '收集订阅数据失败');
                return;
            }
            
            // 验证必填项
            const firstErrorField = validateSingleSubscription(index);
            if (firstErrorField) {
                setTimeout(() => {
                    firstErrorField.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    setTimeout(() => {
                        firstErrorField.focus();
                        if (firstErrorField.tagName === 'TEXTAREA') {
                            firstErrorField.select();
                        }
                    }, 300);
                }, 100);
                showError('subscriptions', '请先填写所有必填项');
                return;
            }
            
            // 更新原始数据
            originalSubscriptions[index] = JSON.parse(JSON.stringify(subscriptionsData.subscriptions[index]));
            subscriptionChanges[index] = false;
            updateSubscriptionChangeStatus(index);
            
            // 更新全局原始数据中对应订阅的数据
            if (originalSubscriptionsData && originalSubscriptionsData.subscriptions) {
                originalSubscriptionsData.subscriptions[index] = JSON.parse(JSON.stringify(subscriptionsData.subscriptions[index]));
            }
            
            // 检查是否还有其他订阅有变更
            const hasAnyChanges = Object.values(subscriptionChanges).some(hasChange => hasChange === true);
            
            // 重新收集所有数据并检查是否有全局变更（包括全局设置等）
            collectSubscriptionsData();
            const currentDataStr = JSON.stringify(subscriptionsData);
            const originalDataStr = JSON.stringify(originalSubscriptionsData);
            hasUnsavedChanges = currentDataStr !== originalDataStr || hasAnyChanges;
            updateSaveButtonState();
            
            showStatus('subscriptions', 'success', '订阅变更已保存');
        }
        
        // 取消单个订阅的变更
        function cancelSingleSubscription(index) {
            if (!confirm('确定要取消此订阅的变更吗？所有未保存的修改将丢失。')) {
                return;
            }
            
            // 恢复原始数据
            if (originalSubscriptions[index]) {
                subscriptionsData.subscriptions[index] = JSON.parse(JSON.stringify(originalSubscriptions[index]));
                // 重新渲染该订阅
                const panel = document.getElementById(`panel-sub_${index}`);
                if (panel) {
                    panel.innerHTML = renderSubscriptionItem(subscriptionsData.subscriptions[index], index);
                    attachChangeListeners();
                }
                subscriptionChanges[index] = false;
                updateSubscriptionChangeStatus(index);
                showStatus('subscriptions', 'success', '已取消订阅变更');
            }
        }
        
        // 收集单个订阅的数据
        function collectSingleSubscriptionData(index) {
            try {
                const item = document.querySelector(`.subscription-item[data-index="${index}"]`);
                if (!item) return false;
                
                const sub = {
                    id: document.getElementById(`sub_${index}_id`)?.value || '',
                    name: document.getElementById(`sub_${index}_name`)?.value || '',
                    enabled: document.getElementById(`sub_${index}_enabled`)?.checked !== false,
                    keywords: {
                        normal: (document.getElementById(`sub_${index}_keywords_normal`)?.value || '').split(String.fromCharCode(10)).filter(k => k.trim()),
                        required: (document.getElementById(`sub_${index}_keywords_required`)?.value || '').split(String.fromCharCode(10)).filter(k => k.trim()),
                        excluded: (document.getElementById(`sub_${index}_keywords_excluded`)?.value || '').split(String.fromCharCode(10)).filter(k => k.trim()),
                        limit: parseInt(document.getElementById(`sub_${index}_keywords_limit`)?.value || '0')
                    },
                    webhooks: [],
                    ai_search: {
                        enabled: document.getElementById(`sub_${index}_ai_enabled`)?.checked === true,
                        trigger_threshold: parseInt(document.getElementById(`sub_${index}_ai_threshold`)?.value || '3'),
                        search_keywords: (document.getElementById(`sub_${index}_ai_keywords`)?.value || '').split(String.fromCharCode(10)).filter(k => k.trim()),
                        time_range_hours: parseInt(document.getElementById(`sub_${index}_ai_time_range`)?.value || '24'),
                        max_results: parseInt(document.getElementById(`sub_${index}_ai_max_results`)?.value || '30')
                    },
                    schedule: {
                        enabled: document.getElementById(`sub_${index}_schedule_enabled`)?.checked !== false,
                        cron: document.getElementById(`sub_${index}_schedule_cron`)?.value || '0 8 * * *',
                        timezone: document.getElementById(`sub_${index}_schedule_timezone`)?.value || 'Asia/Shanghai'
                    }
                };
                
                // 收集 webhooks
                let whIndex = 0;
                while (document.getElementById(`sub_${index}_webhook_${whIndex}_type`)) {
                    sub.webhooks.push({
                        type: document.getElementById(`sub_${index}_webhook_${whIndex}_type`)?.value || '',
                        url: document.getElementById(`sub_${index}_webhook_${whIndex}_url`)?.value || '',
                        name: document.getElementById(`sub_${index}_webhook_${whIndex}_name`)?.value || ''
                    });
                    whIndex++;
                }
                
                subscriptionsData.subscriptions[index] = sub;
                return true;
            } catch (error) {
                console.error('收集单个订阅数据失败:', error);
                return false;
            }
        }
        
        // 验证单个订阅
        function validateSingleSubscription(index) {
            const sub = subscriptionsData.subscriptions[index];
            if (!sub) return null;
            
            // 验证AI搜索关键词（如果启用AI搜索）
            if (sub.ai_search && sub.ai_search.enabled === true) {
                const keywords = sub.ai_search.search_keywords || [];
                if (keywords.length === 0 || keywords.every(k => !k.trim())) {
                    const field = document.getElementById(`sub_${index}_ai_keywords`);
                    if (field) {
                        showFieldError(field, 'AI搜索已启用，搜索关键词不能为空');
                        return field;
                    }
                }
            }
            
            // 验证Webhooks
            if (sub.webhooks && sub.webhooks.length > 0) {
                for (let whIndex = 0; whIndex < sub.webhooks.length; whIndex++) {
                    const wh = sub.webhooks[whIndex];
                    if (!wh.url || !wh.url.trim()) {
                        const field = document.getElementById(`sub_${index}_webhook_${whIndex}_url`);
                        if (field) {
                            showFieldError(field, 'Webhook URL 不能为空');
                            return field;
                        }
                    }
                    if (!wh.name || !wh.name.trim()) {
                        const field = document.getElementById(`sub_${index}_webhook_${whIndex}_name`);
                        if (field) {
                            showFieldError(field, 'Webhook 名称不能为空');
                            return field;
                        }
                    }
                }
            }
            
            return null;
        }
        
        // 检测单个订阅的变更
        function checkSingleSubscriptionChange(index) {
            if (!originalSubscriptions[index]) return false;
            
            collectSingleSubscriptionData(index);
            const current = subscriptionsData.subscriptions[index];
            const original = originalSubscriptions[index];
            
            const currentStr = JSON.stringify(current);
            const originalStr = JSON.stringify(original);
            
            subscriptionChanges[index] = currentStr !== originalStr;
            updateSubscriptionChangeStatus(index);
            
            return subscriptionChanges[index];
        }
        
        // 更新订阅变更状态显示
        function updateSubscriptionChangeStatus(index) {
            if (index !== undefined) {
                // 更新单个订阅的状态
                const saveBtn = document.getElementById(`save-sub-${index}`);
                const saveBtnTop = document.getElementById(`save-sub-top-${index}`);
                const cancelBtn = document.getElementById(`cancel-sub-${index}`);
                const statusDiv = document.getElementById(`sub-${index}-status`);
                const actionsDiv = saveBtn?.closest('.subscription-actions');
                
                if (subscriptionChanges[index]) {
                    if (saveBtn) saveBtn.style.display = 'inline-flex';
                    // 保存按钮始终显示，但有变更时高亮并启用，并显示提示
                    if (saveBtnTop) {
                        saveBtnTop.style.display = 'flex';
                        saveBtnTop.classList.add('btn-warning');
                        saveBtnTop.classList.remove('btn-success');
                        saveBtnTop.disabled = false; // 有变更时启用
                        // 更新按钮文本，显示有变更提示
                        const spans = saveBtnTop.querySelectorAll('span');
                        if (spans.length >= 2) {
                            spans[1].textContent = ' 保存订阅变更 (有变更)';
                        } else if (spans.length === 1) {
                            const newSpan = document.createElement('span');
                            newSpan.textContent = ' 保存订阅变更 (有变更)';
                            saveBtnTop.appendChild(newSpan);
                        }
                    }
                    if (cancelBtn) cancelBtn.style.display = 'inline-flex';
                    if (statusDiv) statusDiv.style.display = 'flex';
                    if (actionsDiv) actionsDiv.classList.add('has-changes');
                } else {
                    if (saveBtn) saveBtn.style.display = 'none';
                    // 保存按钮始终显示，无变更时正常样式但禁用
                    if (saveBtnTop) {
                        saveBtnTop.style.display = 'flex';
                        saveBtnTop.classList.remove('btn-warning');
                        saveBtnTop.classList.add('btn-success');
                        saveBtnTop.disabled = true; // 无变更时禁用
                        // 更新按钮文本，移除变更提示
                        const spans = saveBtnTop.querySelectorAll('span');
                        if (spans.length >= 2) {
                            spans[1].textContent = ' 保存订阅变更';
                        } else if (spans.length === 1) {
                            const newSpan = document.createElement('span');
                            newSpan.textContent = ' 保存订阅变更';
                            saveBtnTop.appendChild(newSpan);
                        }
                    }
                    if (cancelBtn) cancelBtn.style.display = 'none';
                    if (statusDiv) statusDiv.style.display = 'none';
                    if (actionsDiv) actionsDiv.classList.remove('has-changes');
                }
                
                // 更新菜单项上的标记
                const menuItem = document.querySelector(`#subscriptions-sidebar .menu-item[data-sub-index="${index}"]`);
                if (menuItem) {
                    let indicator = menuItem.querySelector('.change-indicator');
                    if (subscriptionChanges[index]) {
                        if (!indicator) {
                            indicator = document.createElement('span');
                            indicator.className = 'change-indicator';
                            indicator.style.cssText = 'color: #f59e0b; margin-left: 8px; font-size: 12px;';
                            indicator.textContent = '●';
                            menuItem.appendChild(indicator);
                        }
                    } else {
                        if (indicator) indicator.remove();
                    }
                }
            } else {
                // 更新所有订阅的状态
                Object.keys(subscriptionChanges).forEach(idx => {
                    updateSubscriptionChangeStatus(parseInt(idx));
                });
            }
        }
        
        function addWebhook(subIndex) {
            // 确保在订阅配置标签页
            if (currentTab !== 'subscriptions') {
                switchTab('subscriptions');
            }
            
            if (!subscriptionsData.subscriptions[subIndex]) {
                console.error('Subscription not found:', subIndex);
                return;
            }
            
            // 先切换到对应的订阅面板，跳过变更检查（因为我们要添加webhook，这是用户主动操作）
            showPanel(`sub_${subIndex}`, null, true);
            
            // 简单版本：直接使用原来的renderSubscriptionsForm方法，但避免闪烁
            if (!subscriptionsData.subscriptions[subIndex].webhooks) {
                subscriptionsData.subscriptions[subIndex].webhooks = [];
            }
            subscriptionsData.subscriptions[subIndex].webhooks.push({
                type: 'wework',
                url: '',
                name: ''
            });
            
            // 只更新当前订阅面板，而不是整个表单
            const currentPanel = document.getElementById(`panel-sub_${subIndex}`);
            if (currentPanel) {
                const subscription = subscriptionsData.subscriptions[subIndex];
                currentPanel.innerHTML = renderSubscriptionItem(subscription, subIndex);
                // 重新绑定事件监听器
                attachChangeListeners();
            }
            
            // 更新状态
            hasUnsavedChanges = true;
            updateSaveButtonState();
            checkSingleSubscriptionChange(subIndex);
            
            // 展开webhook配置部分并滚动
            setTimeout(() => {
                // 展开webhook配置部分
                const webhookSection = Array.from(document.querySelectorAll(`#panel-sub_${subIndex} .section`)).find(section => {
                    const header = section.querySelector('.section-header');
                    return header && header.textContent.includes('Webhooks 配置');
                });
                
                if (webhookSection) {
                    webhookSection.classList.add('expanded');
                    
                    // 滚动到新添加的webhook
                    setTimeout(() => {
                        const newWebhook = webhookSection.querySelector('div[style*="border: 1px solid #ddd"]:last-child');
                        if (newWebhook) {
                            newWebhook.scrollIntoView({ behavior: 'smooth', block: 'center' });
                            setTimeout(() => {
                                const firstInput = newWebhook.querySelector('input[id*="_url"]');
                                if (firstInput) {
                                    firstInput.focus();
                                }
                            }, 300);
                        }
                    }, 100);
                }
            }, 100);
        }
        
        function removeWebhook(subIndex, whIndex) {
            if (!subscriptionsData.subscriptions[subIndex] || !subscriptionsData.subscriptions[subIndex].webhooks) return;
            if (confirm('确定要删除此 Webhook 吗？')) {
                // 从数据中删除
                subscriptionsData.subscriptions[subIndex].webhooks.splice(whIndex, 1);
                
                // 添加删除动画效果
                const webhookDiv = document.querySelector(`#panel-sub_${subIndex} .section-content > div[style*="border: 1px solid #ddd"]:nth-child(${whIndex + 1})`);
                if (webhookDiv) {
                    webhookDiv.style.opacity = '0';
                    webhookDiv.style.transform = 'translateX(-20px)';
                    webhookDiv.style.transition = 'all 0.3s ease';
                    
                    // 动画完成后移除DOM元素
                    setTimeout(() => {
                        webhookDiv.remove();
                        
                        // 重新编号剩余的webhook元素ID
                        const remainingWebhooks = document.querySelectorAll(`#panel-sub_${subIndex} .section-content > div[style*="border: 1px solid #ddd"]`);
                        remainingWebhooks.forEach((webhook, index) => {
                            // 更新选择框
                            const select = webhook.querySelector('select[id*="_webhook_"][id*="_type"]');
                            if (select) {
                                const newId = `sub_${subIndex}_webhook_${index}_type`;
                                select.id = newId;
                                // 更新事件处理函数中的索引
                                const deleteBtn = webhook.querySelector('.btn-danger');
                                if (deleteBtn) {
                                    deleteBtn.setAttribute('onclick', `removeWebhook(${subIndex}, ${index})`);
                                }
                            }
                            
                            // 更新输入框ID和事件
                            const urlInput = webhook.querySelector('input[id*="_webhook_"][id*="_url"]');
                            const nameInput = webhook.querySelector('input[id*="_webhook_"][id*="_name"]');
                            if (urlInput) {
                                urlInput.id = `sub_${subIndex}_webhook_${index}_url`;
                                urlInput.setAttribute('onblur', `validateField('sub_${subIndex}_webhook_${index}_url', 'webhook_url', ${subIndex}, ${index})`);
                            }
                            if (nameInput) {
                                nameInput.id = `sub_${subIndex}_webhook_${index}_name`;
                                nameInput.setAttribute('onblur', `validateField('sub_${subIndex}_webhook_${index}_name', 'webhook_name', ${subIndex}, ${index})`);
                            }
                        });
                    }, 300);
                }
                
                // 更新状态
                hasUnsavedChanges = true;
                updateSaveButtonState();
                checkSingleSubscriptionChange(subIndex);
            }
        }
        
        // 系统配置相关函数（完整实现）
        async function loadConfig() {
            showStatus('config', 'loading', '正在加载系统配置...');
            try {
                const response = await fetch('/api/config');
                if (handleUnauthorized(response)) return;
                const data = await response.json();
                if (data.error) {
                    showError('config', data.error);
                    return;
                }
                configData = data;
                renderConfigForm(data);
                showStatus('config', 'success', '系统配置加载成功');
            } catch (error) {
                showError('config', '加载系统配置失败: ' + error.message);
            }
        }
        
        async function saveConfig() {
            if (!collectConfigFormData()) {
                showError('config', '请先填写完整的配置信息');
                return;
            }
            showStatus('config', 'loading', '正在保存系统配置...');
            try {
                const response = await fetch('/api/config', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(configData)
                });
                const result = await response.json();
                if (result.success) {
                    showStatus('config', 'success', result.message || '系统配置保存成功');
                } else {
                    showError('config', result.error || '保存失败');
                }
            } catch (error) {
                showError('config', '保存系统配置失败: ' + error.message);
            }
        }
        
        function renderConfigForm(config) {
            const form = document.getElementById('configForm');
            form.innerHTML = `
                <div id="config-panel-app" class="content-panel active">
                    ${renderConfigSection('app', '应用设置', config.app || {}, [
                        {key: 'version_check_url', label: '版本检查URL', type: 'text'},
                        {key: 'show_version_update', label: '显示版本更新', type: 'checkbox'}
                    ])}
                </div>
                <div id="config-panel-crawler" class="content-panel">
                    ${renderConfigSection('crawler', '爬虫设置', config.crawler || {}, [
                        {key: 'request_interval', label: '请求间隔(毫秒)', type: 'number'},
                        {key: 'enable_crawler', label: '启用爬虫', type: 'checkbox'},
                        {key: 'use_proxy', label: '使用代理', type: 'checkbox'},
                        {key: 'default_proxy', label: '默认代理地址', type: 'text'}
                    ])}
                </div>
                <div id="config-panel-report" class="content-panel">
                    ${renderConfigSection('report', '报告设置', config.report || {}, [
                        {key: 'mode', label: '报告模式', type: 'select', options: ['daily', 'incremental', 'current']},
                        {key: 'rank_threshold', label: '排名高亮阈值', type: 'number'},
                        {key: 'sort_by_position_first', label: '先按位置排序', type: 'checkbox'},
                        {key: 'max_news_per_keyword', label: '每个关键词最大数量', type: 'number'},
                        {key: 'reverse_content_order', label: '反转内容顺序', type: 'checkbox'}
                    ])}
                </div>
                <div id="config-panel-notification" class="content-panel">
                    ${renderConfigNotificationSection(config.notification || {})}
                </div>
                <div id="config-panel-weight" class="content-panel">
                    ${renderConfigSection('weight', '权重设置', config.weight || {}, [
                        {key: 'rank_weight', label: '排名权重', type: 'number', step: '0.1'},
                        {key: 'frequency_weight', label: '频率权重', type: 'number', step: '0.1'},
                        {key: 'hotness_weight', label: '热度权重', type: 'number', step: '0.1'}
                    ])}
                </div>
                <div id="config-panel-ai_search" class="content-panel">
                    ${renderConfigAISearchSection(config.ai_search || {})}
                </div>
                <div id="config-panel-platforms" class="content-panel">
                    ${renderConfigPlatformsSection(config.platforms || [])}
                </div>
            `;
            document.querySelectorAll('.section-header').forEach(header => {
                header.addEventListener('click', function() {
                    this.parentElement.classList.toggle('expanded');
                });
            });
        }
        
        function renderConfigSection(key, title, data, fields) {
            let html = `<div class="section"><div class="section-header"><span>${title}</span><span class="icon"></span></div><div class="section-content">`;
            fields.forEach(field => {
                const value = data[field.key] !== undefined ? data[field.key] : '';
                html += renderConfigField(key, field, value);
            });
            html += '</div></div>';
            return html;
        }
        
        function renderConfigField(prefix, field, value) {
            const fieldId = `${prefix}_${field.key}`;
            let html = `<div class="form-group"><label for="${fieldId}">${field.label}</label>`;
            if (field.type === 'checkbox') {
                html += `<input type="checkbox" id="${fieldId}" ${value ? 'checked' : ''} />`;
            } else if (field.type === 'select') {
                html += `<select id="${fieldId}">`;
                field.options.forEach(opt => {
                    html += `<option value="${opt}" ${value === opt ? 'selected' : ''}>${opt}</option>`;
                });
                html += `</select>`;
            } else {
                const step = field.step ? `step="${field.step}"` : '';
                html += `<input type="${field.type || 'text'}" id="${fieldId}" value="${escapeHtml(value)}" ${step} />`;
            }
            html += `</div>`;
            return html;
        }
        
        function renderConfigNotificationSection(notification) {
            return `
                <div class="section"><div class="section-header"><span>通知设置</span><span class="icon"></span></div><div class="section-content">
                    ${renderConfigField('notification', {key: 'enable_notification', label: '启用通知', type: 'checkbox'}, notification.enable_notification)}
                    ${renderConfigField('notification', {key: 'message_batch_size', label: '消息分批大小', type: 'number'}, notification.message_batch_size)}
                    ${renderConfigField('notification', {key: 'batch_send_interval', label: '分批发送间隔', type: 'number'}, notification.batch_send_interval)}
                    <h4 style="margin: 20px 0 10px 0;">Webhooks 配置</h4>
                    ${renderConfigField('notification_webhooks', {key: 'feishu_url', label: '飞书 Webhook URL', type: 'url'}, notification.webhooks?.feishu_url || '')}
                    ${renderConfigField('notification_webhooks', {key: 'dingtalk_url', label: '钉钉 Webhook URL', type: 'url'}, notification.webhooks?.dingtalk_url || '')}
                    ${renderConfigField('notification_webhooks', {key: 'wework_url', label: '企业微信 Webhook URL', type: 'url'}, notification.webhooks?.wework_url || '')}
                    ${renderConfigField('notification_webhooks', {key: 'telegram_bot_token', label: 'Telegram Bot Token', type: 'text'}, notification.webhooks?.telegram_bot_token || '')}
                    ${renderConfigField('notification_webhooks', {key: 'telegram_chat_id', label: 'Telegram Chat ID', type: 'text'}, notification.webhooks?.telegram_chat_id || '')}
                    ${renderConfigField('notification_webhooks', {key: 'slack_webhook_url', label: 'Slack Webhook URL', type: 'url'}, notification.webhooks?.slack_webhook_url || '')}
                </div></div>
            `;
        }
        
        function renderConfigAISearchSection(aiSearch) {
            const keywords = (aiSearch.search_keywords || []).map(k => escapeHtml(k)).join(String.fromCharCode(10));
            return `
                <div class="section"><div class="section-header"><span>AI 搜索设置</span><span class="icon"></span></div><div class="section-content">
                    ${renderConfigField('ai_search', {key: 'enabled', label: '启用AI搜索', type: 'checkbox'}, aiSearch.enabled)}
                    ${renderConfigField('ai_search', {key: 'trigger_threshold', label: '触发阈值', type: 'number'}, aiSearch.trigger_threshold)}
                    <div class="help-text" style="color: #6b7280; font-size: 12px; margin-top: 4px; margin-bottom: 16px;">当热搜榜获取数据小于触发阈值时才会触发AI搜索</div>
                    ${renderConfigField('ai_search', {key: 'serper_api_key', label: 'Serper API Key', type: 'text'}, aiSearch.serper_api_key || '')}
                    ${renderConfigField('ai_search', {key: 'ai_api_key', label: 'AI API Key (硅基流动)', type: 'text'}, aiSearch.ai_api_key || '')}
                    ${renderConfigField('ai_search', {key: 'ai_api_base', label: 'AI API Base URL', type: 'url'}, aiSearch.ai_api_base || '')}
                    ${renderConfigField('ai_search', {key: 'time_range_hours', label: '时间范围(小时)', type: 'number'}, aiSearch.time_range_hours)}
                    ${renderConfigField('ai_search', {key: 'max_results', label: '最大结果数', type: 'number'}, aiSearch.max_results)}
                    ${renderConfigField('ai_search', {key: 'relevance_threshold', label: '相关性阈值', type: 'number'}, aiSearch.relevance_threshold)}
                    <div class="form-group"><label>搜索关键词 (每行一个)</label><textarea id="ai_search_search_keywords" style="font-family: monospace;">${keywords}</textarea></div>
                </div></div>
            `;
        }
        
        function renderConfigPlatformsSection(platforms) {
            let html = `<div class="section"><div class="section-header"><span>平台配置</span><span class="icon"></span></div><div class="section-content"><div class="platform-list">`;
            platforms.forEach((platform, index) => {
                html += `<div class="platform-item"><div class="form-group"><label>平台ID</label><input type="text" id="platform_${index}_id" value="${escapeHtml(platform.id || '')}" /></div><div class="form-group"><label>平台名称</label><input type="text" id="platform_${index}_name" value="${escapeHtml(platform.name || '')}" /></div></div>`;
            });
            html += '</div></div></div>';
            return html;
        }
        
        function collectConfigFormData() {
            try {
                configData.app = {
                    version_check_url: document.getElementById('app_version_check_url')?.value || '',
                    show_version_update: document.getElementById('app_show_version_update')?.checked || false
                };
                configData.crawler = {
                    request_interval: parseInt(document.getElementById('crawler_request_interval')?.value || '1000'),
                    enable_crawler: document.getElementById('crawler_enable_crawler')?.checked || false,
                    use_proxy: document.getElementById('crawler_use_proxy')?.checked || false,
                    default_proxy: document.getElementById('crawler_default_proxy')?.value || ''
                };
                configData.report = {
                    mode: document.getElementById('report_mode')?.value || 'daily',
                    rank_threshold: parseInt(document.getElementById('report_rank_threshold')?.value || '5'),
                    sort_by_position_first: document.getElementById('report_sort_by_position_first')?.checked || false,
                    max_news_per_keyword: parseInt(document.getElementById('report_max_news_per_keyword')?.value || '0'),
                    reverse_content_order: document.getElementById('report_reverse_content_order')?.checked || false
                };
                configData.notification = {
                    enable_notification: document.getElementById('notification_enable_notification')?.checked || false,
                    message_batch_size: parseInt(document.getElementById('notification_message_batch_size')?.value || '4000'),
                    batch_send_interval: parseInt(document.getElementById('notification_batch_send_interval')?.value || '3'),
                    webhooks: {
                        feishu_url: document.getElementById('notification_webhooks_feishu_url')?.value || '',
                        dingtalk_url: document.getElementById('notification_webhooks_dingtalk_url')?.value || '',
                        wework_url: document.getElementById('notification_webhooks_wework_url')?.value || '',
                        telegram_bot_token: document.getElementById('notification_webhooks_telegram_bot_token')?.value || '',
                        telegram_chat_id: document.getElementById('notification_webhooks_telegram_chat_id')?.value || '',
                        slack_webhook_url: document.getElementById('notification_webhooks_slack_webhook_url')?.value || ''
                    }
                };
                configData.weight = {
                    rank_weight: parseFloat(document.getElementById('weight_rank_weight')?.value || '0.6'),
                    frequency_weight: parseFloat(document.getElementById('weight_frequency_weight')?.value || '0.3'),
                    hotness_weight: parseFloat(document.getElementById('weight_hotness_weight')?.value || '0.1')
                };
                const keywordsText = document.getElementById('ai_search_search_keywords')?.value || '';
                configData.ai_search = {
                    enabled: document.getElementById('ai_search_enabled')?.checked || false,
                    trigger_threshold: parseInt(document.getElementById('ai_search_trigger_threshold')?.value || '3'),
                    serper_api_key: document.getElementById('ai_search_serper_api_key')?.value || '',
                    ai_api_key: document.getElementById('ai_search_ai_api_key')?.value || '',
                    ai_api_base: document.getElementById('ai_search_ai_api_base')?.value || '',
                    search_keywords: keywordsText.split(String.fromCharCode(10)).filter(k => k.trim()),
                    time_range_hours: parseInt(document.getElementById('ai_search_time_range_hours')?.value || '24'),
                    max_results: parseInt(document.getElementById('ai_search_max_results')?.value || '15'),
                    relevance_threshold: parseInt(document.getElementById('ai_search_relevance_threshold')?.value || '5')
                };
                configData.platforms = [];
                document.querySelectorAll('.platform-item').forEach((item, index) => {
                    const id = document.getElementById(`platform_${index}_id`)?.value;
                    const name = document.getElementById(`platform_${index}_name`)?.value;
                    if (id && name) {
                        configData.platforms.push({id, name});
                    }
                });
                return true;
            } catch (error) {
                console.error('收集系统配置数据失败:', error);
                return false;
            }
        }
        
        function showStatus(tab, type, message) {
            const status = document.getElementById(`status-${tab}`);
            status.className = `status ${type}`;
            status.textContent = message;
            status.style.display = 'block';
            if (type === 'success') {
                setTimeout(() => status.style.display = 'none', 3000);
            }
        }
        
        function showError(tab, message) {
            showStatus(tab, 'error', message);
        }
        
        // HTML转义函数
        function escapeHtml(text) {
            if (text === null || text === undefined) {
                return '';
            }
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        // 更新保存按钮状态
        function updateSaveButtonState() {
            const saveBtn = document.getElementById('save-subscriptions-btn');
            const saveBtnText = document.getElementById('save-btn-text');
            if (saveBtn && saveBtnText) {
                if (hasUnsavedChanges) {
                    saveBtn.classList.add('btn-warning');
                    saveBtn.classList.remove('btn-success');
                    saveBtnText.textContent = '保存所有订阅 (有未保存的更改)';
                } else {
                    saveBtn.classList.remove('btn-warning');
                    saveBtn.classList.add('btn-success');
                    saveBtnText.textContent = '保存所有订阅';
                }
            }
        }
        
        // 检测配置变更
        function checkForChanges() {
            if (!originalSubscriptionsData) return;
            
            collectSubscriptionsData();
            const currentDataStr = JSON.stringify(subscriptionsData);
            const originalDataStr = JSON.stringify(originalSubscriptionsData);
            
            hasUnsavedChanges = currentDataStr !== originalDataStr;
            updateSaveButtonState();
        }
        
        // 绑定输入事件监听器
        function attachChangeListeners() {
            // 监听所有输入框的变化
            setTimeout(() => {
                const allInputs = document.querySelectorAll('#subscriptionsForm input, #subscriptionsForm textarea, #subscriptionsForm select');
                allInputs.forEach(input => {
                    input.addEventListener('input', checkForChanges);
                    input.addEventListener('change', checkForChanges);
                });
                
                // 为带有data-validate属性的输入框添加blur事件监听
                document.querySelectorAll('[data-validate]').forEach(input => {
                    input.addEventListener('blur', function() {
                        const validateType = this.getAttribute('data-validate');
                        const subIndex = parseInt(this.getAttribute('data-sub-index'));
                        const whIndex = parseInt(this.getAttribute('data-wh-index'));
                        if (this.id) {
                            validateField(this.id, validateType, subIndex, whIndex);
                        }
                    });
                });
                
                // 为订阅名称输入框添加实时更新菜单栏的监听
                // 只监听订阅名称（sub_${index}_name），不包括：
                // - 订阅ID（sub_${index}_id）
                // - Webhook名称（sub_${index}_webhook_${whIndex}_name）
                document.querySelectorAll('input[id^="sub_"]').forEach(input => {
                    const id = input.id;
                    // 精确匹配订阅名称：格式必须是 sub_数字_name，且不包含 webhook
                    // 这样可以排除：
                    // - sub_0_id（订阅ID，以_id结尾）
                    // - sub_0_webhook_0_name（Webhook名称，包含webhook）
                    const subNamePattern = /^sub_(\d+)_name$/;
                    const match = id.match(subNamePattern);
                    if (match) {
                        // 确认这是订阅名称输入框，不是订阅ID或Webhook名称
                        const subIndex = parseInt(match[1]);
                        input.addEventListener('input', function() {
                            const menuItem = document.querySelector(`#subscriptions-sidebar .menu-item[data-sub-index="${subIndex}"]`);
                            if (menuItem) {
                                // 找到菜单项中显示名称的span（排除icon和变更标记）
                                const spans = menuItem.querySelectorAll('span');
                                if (spans.length >= 2) {
                                    // 第二个span通常是名称（第一个是icon）
                                    const nameSpan = spans[1];
                                    const newName = this.value.trim() || '未命名订阅';
                                    nameSpan.textContent = newName;
                                }
                            }
                        });
                    }
                });
                
                // 为AI搜索启用状态变化添加监听，当启用/禁用时重新验证关键词
                document.querySelectorAll('[id^="sub_"][id$="_ai_enabled"]').forEach(checkbox => {
                    checkbox.addEventListener('change', function() {
                        const id = this.id;
                        // 从ID中提取索引：sub_0_ai_enabled -> 0
                        const parts = id.split('_');
                        if (parts.length >= 3) {
                            const subIndex = parseInt(parts[1]);
                            const keywordsField = document.getElementById(`sub_${subIndex}_ai_keywords`);
                            if (keywordsField) {
                                validateField(`sub_${subIndex}_ai_keywords`, 'ai_keywords', subIndex);
                            }
                        }
                    });
                });
            }, 500);
        }
        
        // 更新Cron表达式（从预设选项）
        function updateCronFromPreset(subIndex) {
            const presetSelect = document.getElementById(`sub_${subIndex}_schedule_preset`);
            const cronInput = document.getElementById(`sub_${subIndex}_schedule_cron`);
            if (presetSelect && cronInput) {
                const selectedValue = presetSelect.value;
                if (selectedValue === 'custom') {
                    // 显示自定义输入框
                    cronInput.style.display = 'block';
                    cronInput.focus();
                } else {
                    // 使用预设值，隐藏自定义输入框
                    cronInput.value = selectedValue;
                    cronInput.style.display = 'none';
                }
                // 触发变更检测
                checkForChanges();
            }
        }
        
        // 根据用户角色控制菜单显示
        function setupUserPermissions(role) {
            userRole = role; // 保存用户角色到全局变量
            
            if (userRole === 'user') {
                // 普通用户：隐藏系统配置标签页
                // 使用更可靠的选择器：选择所有tab，然后找到包含'config'的那个
                const tabs = document.querySelectorAll('.tab');
                tabs.forEach(tab => {
                    if (tab.getAttribute('onclick') && tab.getAttribute('onclick').includes("switchTab('config')")) {
                        tab.style.display = 'none';
                    }
                });
                
                // 隐藏订阅配置中的全局设置菜单项
                const globalMenuItem = document.querySelector('#subscriptions-sidebar .menu-group:first-child');
                if (globalMenuItem) {
                    globalMenuItem.style.display = 'none';
                }
                
                // 如果当前在系统配置标签页，切换到订阅配置
                if (currentTab === 'config') {
                    switchTab('subscriptions');
                }
            }
            
            // 更新帮助内容以匹配用户角色
            updateHelpContent();
            
            // 普通用户登录后显示帮助手册提示
            if (userRole === 'user') {
                // 延迟一下显示，让页面先加载完成
                setTimeout(() => {
                    showUserWelcomeModal();
                }, 500);
            }
        }
        
        // 显示普通用户欢迎弹窗
        function showUserWelcomeModal() {
            const modal = document.createElement('div');
            modal.className = 'modal-overlay show';
            modal.style.cssText = 'position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0, 0, 0, 0.5); z-index: 10001; display: flex; align-items: center; justify-content: center; padding: 20px;';
            modal.onclick = function(e) {
                if (e.target === modal) {
                    modal.remove();
                }
            };
            
            modal.innerHTML = `
                <div class="modal" onclick="event.stopPropagation()" style="max-width: 500px; background: white; border-radius: 16px; box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3); animation: slideUp 0.3s ease;">
                    <div class="modal-header" style="padding: 24px 30px; border-bottom: 1px solid #e5e7eb; display: flex; justify-content: space-between; align-items: center;">
                        <h2 style="font-size: 24px; font-weight: 700; color: #1e293b; margin: 0;">👋 欢迎使用智通星资讯管理</h2>
                        <button onclick="this.closest('.modal-overlay').remove()" style="background: none; border: none; font-size: 24px; cursor: pointer; color: #6b7280; padding: 0; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; border-radius: 6px; transition: all 0.2s;" onmouseover="this.style.background='#f3f4f6'; this.style.color='#1e293b';" onmouseout="this.style.background='none'; this.style.color='#6b7280';">×</button>
                    </div>
                    <div class="modal-body" style="padding: 30px;">
                        <p style="color: #475569; font-size: 15px; line-height: 1.7; margin-bottom: 24px;">
                            欢迎使用智通星资讯管理系统！为了帮助您更好地使用系统，建议您先查看 <strong>系统帮助手册</strong>，了解如何配置订阅规则和推送设置。
                        </p>
                        <div style="display: flex; gap: 12px; justify-content: flex-end;">
                            <button onclick="this.closest('.modal-overlay').remove()" style="padding: 10px 20px; background: #f3f4f6; color: #374151; border: none; border-radius: 8px; font-size: 14px; font-weight: 600; cursor: pointer; transition: all 0.2s;" onmouseover="this.style.background='#e5e7eb';" onmouseout="this.style.background='#f3f4f6';">稍后查看</button>
                            <button onclick="this.closest('.modal-overlay').remove(); showHelpModal();" style="padding: 10px 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 8px; font-size: 14px; font-weight: 600; cursor: pointer; transition: all 0.2s;" onmouseover="this.style.opacity='0.9';" onmouseout="this.style.opacity='1';">📖 查看帮助手册</button>
                        </div>
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
        }
        
        // 页面加载时检查登录状态并加载订阅配置
        window.addEventListener('DOMContentLoaded', async () => {
            try {
                // 检查登录状态
                const response = await fetch('/api/check_login');
                if (!response.ok) {
                    console.error('检查登录状态失败: HTTP', response.status);
                    window.location.reload();
                    return;
                }
                
                const result = await response.json();
                if (!result.logged_in) {
                    window.location.reload();
                    return;
                }
                
                // 根据用户角色设置权限
                if (result.role) {
                    setupUserPermissions(result.role);
                }
                
                // 已登录，加载订阅配置
                loadSubscriptions();
            } catch (error) {
                console.error('页面初始化失败:', error);
                const form = document.getElementById('subscriptionsForm');
                if (form) {
                    form.innerHTML = `<div style="padding: 40px; text-align: center; color: #ef4444;">页面初始化失败: ${escapeHtml(error.message)}<br><button onclick="window.location.reload()" style="margin-top: 20px; padding: 8px 16px; background: #667eea; color: white; border: none; border-radius: 6px; cursor: pointer;">刷新页面</button></div>`;
                }
            }
        });
        
        // 全局错误处理
        window.addEventListener('error', function(event) {
            console.error('JavaScript错误:', event.error);
            // 不阻止默认行为，让错误正常显示在控制台
        });
        
        // 未处理的Promise拒绝
        window.addEventListener('unhandledrejection', function(event) {
            console.error('未处理的Promise拒绝:', event.reason);
            // 不阻止默认行为
        });
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    print(f"启动配置管理界面...")
    print(f"订阅配置文件: {SUBSCRIPTIONS_PATH}")
    print(f"系统配置文件: {CONFIG_PATH}")
    print(f"访问地址: http://localhost:5001")
    app.run(host="0.0.0.0", port=5001, debug=True)

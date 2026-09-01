"""
执行相关路由
"""
from flask import request, jsonify
from pathlib import Path
from config_manager.auth.decorators import login_required


def register_routes(app):
    """注册执行路由"""
    
    @app.route("/api/execute", methods=["POST"])
    @login_required
    def execute_main():
        """执行 main.py"""
        import subprocess
        import sys
        
        try:
            # 切换到项目根目录
            project_root = Path(__file__).parent.parent.parent
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

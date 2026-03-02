"""
配置文件读写工具函数
"""
import yaml
import json
from pathlib import Path
from .settings import CONFIG_PATH, SUBSCRIPTIONS_PATH, CONFIG_DIR


# 自定义YAML Dumper以保持列表格式
class ListDumper(yaml.SafeDumper):
    pass


def represent_list(dumper, data):
    return dumper.represent_sequence('tag:yaml.org,2002:seq', data, flow_style=False)


ListDumper.add_representer(list, represent_list)


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

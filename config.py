"""项目配置管理，从 .env 文件读取。"""

import os
import re
from dotenv import load_dotenv

from paths import data_path

_ = load_dotenv(data_path(".env"))

# IP 地址正则（仅允许 IPv4，防止 SSRF）
_IP_PATTERN = re.compile(r"^(\d{1,3}\.){3}\d{1,3}$")


def _validate_ip(value: str, default: str) -> str:
    """校验 IP 地址格式，不合法则返回默认值。"""
    if _IP_PATTERN.match(value):
        return value
    return default


class Config:
    """全局配置。"""

    # 拨号模式: app（HTTP 直连手机 App，推荐）或 adb（ADB 无线调试，备用）
    DIAL_MODE: str = os.getenv("DIAL_MODE", "app")

    # 手机 App HTTP 连接（推荐方式）
    APP_HOST: str = _validate_ip(os.getenv("APP_HOST", "192.168.1.100"), "192.168.1.100")
    APP_PORT: int = int(os.getenv("APP_PORT", "8888"))

    # ADB 无线连接（备用方式）
    ADB_DEVICE_IP: str = _validate_ip(os.getenv("ADB_DEVICE_IP", "192.168.1.100"), "192.168.1.100")
    ADB_DEVICE_PORT: str = os.getenv("ADB_DEVICE_PORT", "5555")

    # Flask
    FLASK_PORT: int = int(os.getenv("FLASK_PORT", "5000"))
    FLASK_DEBUG: bool = os.getenv("FLASK_DEBUG", "True").lower() == "true"

    # ADB 设备地址 (IP:Port)
    ADB_DEVICE_ADDRESS: str = f"{ADB_DEVICE_IP}:{ADB_DEVICE_PORT}"

    # App 完整 URL
    APP_URL: str = f"http://{APP_HOST}:{APP_PORT}"


def update_app_host(new_host: str) -> bool:
    """运行时更新 APP_HOST 并持久化到 .env 文件。"""
    new_host = _validate_ip(new_host, "")
    if not new_host:
        return False
    Config.APP_HOST = new_host
    Config.APP_URL = f"http://{new_host}:{Config.APP_PORT}"
    # 写入 .env
    env_path = data_path(".env")
    lines = []
    found = False
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("APP_HOST="):
                    lines.append(f"APP_HOST={new_host}\n")
                    found = True
                else:
                    lines.append(line)
    if not found:
        lines.append(f"APP_HOST={new_host}\n")
    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    return True

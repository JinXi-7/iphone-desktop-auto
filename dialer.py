"""拨号核心逻辑 - 支持 App(HTTP) 和 ADB 双模式。"""

import os
import subprocess
import shutil
from typing import Any

import requests

from config import Config
from paths import data_path

# 项目根目录下的 platform-tools（打包后放在 exe 同级目录）
_LOCAL_ADB = data_path(os.path.join("platform-tools", "adb.exe"))

# HTTP 请求超时（秒）
_HTTP_TIMEOUT = 5


# ==================== App (HTTP) 模式 ====================

def check_app_available() -> bool:
    """检查手机 App 是否在线（HTTP /ping 健康检查）。"""
    try:
        resp = requests.get(
            f"{Config.APP_URL}/ping",
            timeout=_HTTP_TIMEOUT,
        )
        return resp.status_code == 200
    except (requests.RequestException, ConnectionError, TimeoutError):
        return False


def get_app_status() -> dict[str, Any] | None:
    """获取手机 App 状态信息。"""
    try:
        resp = requests.get(
            f"{Config.APP_URL}/ping",
            timeout=_HTTP_TIMEOUT,
        )
        if resp.status_code == 200:
            return resp.json()
        return None
    except (requests.RequestException, ConnectionError, TimeoutError, ValueError):
        return None


def dial_number_http(phone: str) -> tuple[bool, str]:
    """通过 HTTP 请求触发手机 App 拨号。

    Args:
        phone: 要拨打的电话号码

    Returns:
        (成功与否, 消息)
    """
    clean_phone = "".join(c for c in phone if c.isdigit() or c == "+")
    if not clean_phone:
        return False, "号码为空"

    try:
        resp = requests.post(
            f"{Config.APP_URL}/dial",
            json={"phone": clean_phone},
            timeout=_HTTP_TIMEOUT,
        )
        data = resp.json()
        if resp.status_code == 200 and data.get("success"):
            return True, data.get("message", f"正在拨打 {clean_phone}")
        return False, data.get("message", f"拨号失败（HTTP {resp.status_code}）")
    except requests.Timeout:
        return False, "手机 App 响应超时，请确认 App 正在运行"
    except requests.ConnectionError:
        return False, f"无法连接手机 App ({Config.APP_URL})，请确认 IP 地址和 App 状态"
    except (requests.RequestException, ValueError) as e:
        return False, f"拨号请求异常：{e}"


# ==================== ADB 模式（备用） ====================

def _find_adb() -> str | None:
    """查找 adb 可执行文件路径，找不到返回 None。

    优先从系统 PATH 查找，找不到则尝试项目内置的 platform-tools。
    """
    path = shutil.which("adb")
    if path:
        return path
    if os.path.exists(_LOCAL_ADB):
        return _LOCAL_ADB
    return None


def check_adb_available() -> bool:
    """检查系统是否安装了 adb。"""
    return _find_adb() is not None


def get_adb_devices() -> list[str]:
    """获取当前已连接的 ADB 设备列表。"""
    adb_path = _find_adb()
    if not adb_path:
        return []

    try:
        result = subprocess.run(
            [adb_path, "devices"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        devices = []
        for line in result.stdout.strip().split("\n")[1:]:
            line = line.strip()
            if line and "\tdevice" in line:
                devices.append(line.split("\t")[0])
        return devices
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []


def connect_device() -> tuple[bool, str]:
    """连接 ADB 无线设备。

    Returns:
        (成功与否, 消息)
    """
    adb_path = _find_adb()
    if not adb_path:
        return False, "系统未找到 adb，请确认已安装 Android Platform Tools 并加入 PATH"

    address = Config.ADB_DEVICE_ADDRESS
    try:
        result = subprocess.run(
            [adb_path, "connect", address],
            capture_output=True,
            text=True,
            timeout=10,
        )
        output = (result.stdout + result.stderr).strip()
        if "connected" in output and "cannot" not in output:
            return True, f"设备 {address} 连接成功"
        return False, f"连接失败：{output}"
    except subprocess.TimeoutExpired:
        return False, f"连接超时：{address}"
    except FileNotFoundError:
        return False, "adb 命令未找到"


def is_device_connected() -> bool:
    """检查目标设备是否在已连接列表中。"""
    address = Config.ADB_DEVICE_ADDRESS
    return address in get_adb_devices()


def dial_number_adb(phone: str) -> tuple[bool, str]:
    """通过 ADB 触发手机拨号（备用模式）。

    策略：先尝试 ACTION_CALL（全自动拨号），若因权限不足失败，
    自动降级为 ACTION_DIAL（打开拨号界面预填号码，需手动按拨号键）。

    Args:
        phone: 要拨打的电话号码

    Returns:
        (成功与否, 消息)
    """
    adb_path = _find_adb()
    if not adb_path:
        return False, "系统未找到 adb"

    if not is_device_connected():
        success, msg = connect_device()
        if not success:
            return False, msg

    clean_phone = "".join(c for c in phone if c.isdigit() or c == "+")

    # 方案1：尝试全自动拨号 (ACTION_CALL)
    try:
        result = subprocess.run(
            [adb_path, "shell", "am", "start", "-a",
             "android.intent.action.CALL", "-d", f"tel:{clean_phone}"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        output = (result.stdout + result.stderr).strip()
        if result.returncode == 0 and "SecurityException" not in output and "Error" not in output:
            return True, f"全自动拨号成功：{clean_phone}"
    except subprocess.TimeoutExpired:
        return False, "拨号命令超时"

    # 方案2：降级为半自动拨号 (ACTION_DIAL)
    try:
        result = subprocess.run(
            [adb_path, "shell", "am", "start", "-a",
             "android.intent.action.DIAL", "-d", f"tel:{clean_phone}"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        output = (result.stdout + result.stderr).strip()
        if result.returncode == 0 and "SecurityException" not in output:
            return True, f"已打开拨号界面：{clean_phone}（请在手机上按拨号键确认）"
        return False, f"拨号失败：{output}"
    except subprocess.TimeoutExpired:
        return False, "拨号命令超时"


# ==================== 统一拨号入口 ====================

def dial_number(phone: str) -> tuple[bool, str]:
    """拨号统一入口，根据配置选择 App 或 ADB 模式。

    Args:
        phone: 要拨打的电话号码

    Returns:
        (成功与否, 消息)
    """
    if Config.DIAL_MODE == "adb":
        return dial_number_adb(phone)
    return dial_number_http(phone)

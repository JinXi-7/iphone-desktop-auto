"""Flask 主程序 - 一键拨号 Web 服务。"""

import os
import tempfile
from typing import Any

from flask import Flask, render_template, jsonify, request

from paths import resource_path
from config import Config, update_app_host
from dialer import (
    check_adb_available,
    get_adb_devices,
    connect_device,
    is_device_connected,
    dial_number,
    check_app_available,
    get_app_status,
)
from models import (
    init_db,
    get_all_contacts,
    add_contact,
    update_contact,
    delete_contact,
    update_last_dialed,
    add_dial_history,
    get_dial_history,
)
from importer import import_excel

app = Flask(
    __name__,
    template_folder=resource_path("templates"),
    static_folder=resource_path("static"),
)
init_db()


# ==================== 页面路由 ====================

@app.route("/")
def index():
    """主页面。"""
    return render_template("index.html", config=Config)


# ==================== API 路由 ====================

@app.route("/api/status")
def api_status():
    """获取连接状态（根据拨号模式返回不同信息）。"""
    mode = Config.DIAL_MODE

    if mode == "app":
        app_ok = check_app_available()
        app_info = get_app_status()
        return jsonify({
            "mode": "app",
            "connected": app_ok,
            "app_url": Config.APP_URL,
            "device": app_info.get("device", "未知") if app_info else "未知",
        })

    # ADB 模式
    adb_ok = check_adb_available()
    devices = get_adb_devices() if adb_ok else []
    connected = is_device_connected() if adb_ok else False
    return jsonify({
        "mode": "adb",
        "connected": connected,
        "adb_installed": adb_ok,
        "devices": devices,
        "target_device": Config.ADB_DEVICE_ADDRESS,
    })


@app.route("/api/connect", methods=["POST"])
def api_connect():
    """连接设备（App 模式为健康检查，ADB 模式为无线连接）。"""
    if Config.DIAL_MODE == "app":
        app_ok = check_app_available()
        if app_ok:
            return jsonify({"success": True, "message": "手机 App 连接正常"})
        return jsonify({"success": False, "message": f"无法连接手机 App ({Config.APP_URL})，请确认 App 已启动"})

    success, message = connect_device()
    return jsonify({"success": success, "message": message})


@app.route("/api/config", methods=["POST"])
def api_config():
    """更新手机 App 的 IP 地址并测试连接。"""
    data: dict[str, Any] | None = request.get_json()
    if not data or not data.get("app_host"):
        return jsonify({"success": False, "message": "请提供 IP 地址"}), 400

    host = str(data["app_host"]).strip()
    if not update_app_host(host):
        return jsonify({"success": False, "message": "IP 地址格式无效，请输入正确的 IPv4 地址"}), 400

    app_ok = check_app_available()
    if app_ok:
        app_info = get_app_status()
        device = app_info.get("device", "未知") if app_info else "未知"
        return jsonify({
            "success": True,
            "message": f"连接成功！设备：{device}",
            "app_url": Config.APP_URL,
            "device": device,
        })
    return jsonify({
        "success": False,
        "message": f"IP 已更新为 {Config.APP_HOST}，但无法连接手机 App，请确认 App 已启动",
        "app_url": Config.APP_URL,
    })


@app.route("/api/dial", methods=["POST"])
def api_dial():
    """触发拨号。"""
    data: dict[str, Any] | None = request.get_json()
    if not data or not data.get("phone"):
        return jsonify({"success": False, "message": "请提供电话号码"}), 400

    phone: str = str(data["phone"])
    success, message = dial_number(phone)

    # 记录拨号历史
    contact_name = str(data.get("name", phone))
    status = "success" if success else "fail"
    add_dial_history(name=contact_name, phone=phone, status=status, message=message)

    # 如果拨号成功且关联了联系人ID，更新最后拨号时间
    if success and data.get("contact_id"):
        try:
            update_last_dialed(int(data["contact_id"]))
        except (ValueError, TypeError):
            pass

    return jsonify({"success": success, "message": message})


# ==================== 联系人 CRUD ====================

@app.route("/api/contacts")
def api_contacts():
    """获取联系人列表，支持搜索。"""
    search = request.args.get("search", "")
    contacts = get_all_contacts(search)
    return jsonify(contacts)


@app.route("/api/contacts", methods=["POST"])
def api_add_contact():
    """添加联系人。"""
    data: dict[str, Any] | None = request.get_json()
    if not data or not data.get("name") or not data.get("phone"):
        return jsonify({"success": False, "message": "请提供姓名和电话号码"}), 400

    contact = add_contact(
        name=str(data["name"]),
        phone=str(data["phone"]),
        group_name=str(data.get("group_name", "")),
    )
    return jsonify({"success": True, "contact": contact}), 201


@app.route("/api/contacts/<int:contact_id>", methods=["PUT"])
def api_update_contact(contact_id: int):
    """更新联系人。"""
    data: dict[str, Any] | None = request.get_json()
    if not data or not data.get("name") or not data.get("phone"):
        return jsonify({"success": False, "message": "请提供姓名和电话号码"}), 400

    ok = update_contact(
        contact_id=contact_id,
        name=str(data["name"]),
        phone=str(data["phone"]),
        group_name=str(data.get("group_name", "")),
    )
    if not ok:
        return jsonify({"success": False, "message": "联系人不存在"}), 404
    return jsonify({"success": True})


@app.route("/api/contacts/<int:contact_id>", methods=["DELETE"])
def api_delete_contact(contact_id: int):
    """删除联系人。"""
    ok = delete_contact(contact_id)
    if not ok:
        return jsonify({"success": False, "message": "联系人不存在"}), 404
    return jsonify({"success": True})


# ==================== Excel 导入 ====================

@app.route("/api/import", methods=["POST"])
def api_import():
    """Excel 批量导入联系人。"""
    if "file" not in request.files:
        return jsonify({"success": False, "message": "请上传文件"}), 400

    file = request.files["file"]
    if not file.filename or not file.filename.endswith((".xlsx", ".xls")):
        return jsonify({"success": False, "message": "请上传 .xlsx 或 .xls 文件"}), 400

    # 保存到临时文件后导入（先关闭句柄再给 openpyxl 打开，避免 Windows 文件锁）
    suffix = os.path.splitext(file.filename)[1]
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.close()
    file.save(tmp.name)
    try:
        result = import_excel(tmp.name)
        return jsonify({"success": True, "result": result})
    except Exception as e:
        return jsonify({"success": False, "message": f"导入失败: {e}"}), 500
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass


# ==================== 拨号历史 ====================

@app.route("/api/history")
def api_history():
    """获取拨号历史记录。"""
    limit = request.args.get("limit", 50, type=int)
    history = get_dial_history(limit)
    return jsonify(history)


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=Config.FLASK_PORT,
        debug=Config.FLASK_DEBUG,
    )

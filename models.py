"""联系人数据模型 - SQLite 存储。"""

import sqlite3
from datetime import datetime
from typing import Any

from paths import data_path

DB_PATH = data_path("contacts.db")


def get_conn() -> sqlite3.Connection:
    """获取数据库连接（启用外键支持，结果按字典返回）。"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """初始化数据库表。"""
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            phone       TEXT    NOT NULL,
            group_name  TEXT    DEFAULT '',
            created_at  TEXT    NOT NULL,
            last_dialed TEXT    DEFAULT ''
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS dial_history (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            name     TEXT    NOT NULL,
            phone    TEXT    NOT NULL,
            status   TEXT    NOT NULL,
            message  TEXT    DEFAULT '',
            dialed_at TEXT   NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def get_all_contacts(search: str = "") -> list[dict[str, Any]]:
    """获取所有联系人，支持按姓名或号码搜索。"""
    conn = get_conn()
    if search:
        rows = conn.execute(
            "SELECT * FROM contacts WHERE name LIKE ? OR phone LIKE ? ORDER BY name",
            (f"%{search}%", f"%{search}%"),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM contacts ORDER BY name"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_contact(contact_id: int) -> dict[str, Any] | None:
    """获取单个联系人。"""
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM contacts WHERE id = ?", (contact_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def add_contact(name: str, phone: str, group_name: str = "") -> dict[str, Any]:
    """添加联系人。"""
    conn = get_conn()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor = conn.execute(
        "INSERT INTO contacts (name, phone, group_name, created_at) VALUES (?, ?, ?, ?)",
        (name, phone, group_name, now),
    )
    conn.commit()
    contact_id = cursor.lastrowid
    conn.close()
    return {"id": contact_id, "name": name, "phone": phone,
            "group_name": group_name, "created_at": now, "last_dialed": ""}


def update_contact(contact_id: int, name: str, phone: str,
                   group_name: str = "") -> bool:
    """更新联系人。"""
    conn = get_conn()
    cursor = conn.execute(
        "UPDATE contacts SET name = ?, phone = ?, group_name = ? WHERE id = ?",
        (name, phone, group_name, contact_id),
    )
    conn.commit()
    conn.close()
    return cursor.rowcount > 0


def delete_contact(contact_id: int) -> bool:
    """删除联系人。"""
    conn = get_conn()
    cursor = conn.execute(
        "DELETE FROM contacts WHERE id = ?", (contact_id,)
    )
    conn.commit()
    conn.close()
    return cursor.rowcount > 0


def update_last_dialed(contact_id: int) -> None:
    """更新联系人最后拨号时间。"""
    conn = get_conn()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "UPDATE contacts SET last_dialed = ? WHERE id = ?",
        (now, contact_id),
    )
    conn.commit()
    conn.close()


# ==================== 拨号历史 ====================

def add_dial_history(name: str, phone: str, status: str, message: str = "") -> None:
    """记录一条拨号历史。"""
    conn = get_conn()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "INSERT INTO dial_history (name, phone, status, message, dialed_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (name, phone, status, message, now),
    )
    conn.commit()
    conn.close()


def get_dial_history(limit: int = 50) -> list[dict[str, Any]]:
    """获取拨号历史记录（按号码去重，每个号码只保留最近一次）。"""
    conn = get_conn()
    # 用 GROUP BY phone 去重，取每个号码最新的一条记录
    rows = conn.execute(
        "SELECT * FROM ("
        "  SELECT *, ROW_NUMBER() OVER (PARTITION BY phone ORDER BY id DESC) AS rn "
        "  FROM dial_history"
        ") WHERE rn = 1 ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        d.pop("rn", None)  # 移除内部排序字段
        result.append(d)
    return result

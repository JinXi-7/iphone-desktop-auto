"""路径处理 - 兼容开发模式和 PyInstaller 打包模式。"""

import sys
import os


def is_frozen() -> bool:
    """是否在 PyInstaller 打包环境下运行。"""
    return getattr(sys, "frozen", False)


def resource_path(relative_path: str) -> str:
    """获取内置资源路径（templates, static 等）。

    打包后资源在 sys._MEIPASS 临时目录中。
    """
    if is_frozen():
        base = sys._MEIPASS  # type: ignore[union-attr]
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative_path)


def data_path(relative_path: str) -> str:
    """获取用户数据路径（.env, contacts.db, platform-tools 等）。

    打包后数据文件放在 exe 同级目录，确保可读写。
    """
    if is_frozen():
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative_path)

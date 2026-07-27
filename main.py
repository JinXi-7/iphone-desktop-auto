"""桌面程序入口 - 启动 Flask 服务并打开原生窗口。"""

import os
import sys
import threading
import time
import urllib.request

import webview

from app import app
from config import Config
from paths import data_path


class NullDevice:
    """空输出设备，--windowed 模式下 sys.stdout/stderr 为 None 时的回退。"""
    def write(self, _s: str) -> int:
        return 0

    def flush(self) -> None:
        pass


# --windowed 打包后 stdout/stderr 为 None，需回退
if sys.stdout is None:
    sys.stdout = NullDevice()
if sys.stderr is None:
    sys.stderr = NullDevice()


def start_flask():
    """在后台线程中启动 Flask 服务。"""
    app.run(
        host="127.0.0.1",
        port=Config.FLASK_PORT,
        debug=False,
        use_reloader=False,
    )


def wait_for_server(url: str, timeout: int = 10) -> bool:
    """等待 Flask 服务就绪。"""
    for _ in range(timeout * 10):
        try:
            urllib.request.urlopen(url, timeout=1)
            return True
        except Exception:
            time.sleep(0.1)
    return False


def main():
    # 启动 Flask 后台服务
    flask_thread = threading.Thread(target=start_flask, daemon=True)
    flask_thread.start()

    # 等待服务就绪
    url = f"http://127.0.0.1:{Config.FLASK_PORT}"
    if not wait_for_server(url):
        print("Flask 服务启动失败", file=sys.stderr)
        sys.exit(1)

    # 打开桌面窗口（Flask 线程为 daemon，窗口关闭后自动退出）
    webview.create_window(
        title="一键拨号",
        url=url,
        width=900,
        height=700,
        min_size=(600, 500),
    )
    webview.start()


if __name__ == "__main__":
    main()

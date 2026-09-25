import os
import sys
import webbrowser
import threading
import time

# 将 backend 路径添加到 Python 模块搜索路径
BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
sys.path.insert(0, BACKEND_DIR)

if sys.platform == "win32":
    import io
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from routers.system import get_lan_ip

def open_browser(url: str):
    time.sleep(1.2)
    try:
        webbrowser.open(url)
    except Exception:
        pass

def main():
    port = 8000
    lan_ip = get_lan_ip()
    local_url = f"http://localhost:{port}"
    mobile_url = f"http://{lan_ip}:{port}"

    print("=" * 64)
    print(" [*] 考研政治刷题掌上宝 (PolicyMaster) 正在启动...")
    print("=" * 64)
    print(f" [电脑浏览器访问]  ->  {local_url}")
    print(f" [手机自习室/床上] ->  {mobile_url}")
    print(" (手机连接同一Wi-Fi或手机热点，扫描界面右上角二维码即可同步刷题)")
    print("=" * 64)

    # 自动在电脑浏览器打开
    threading.Thread(target=open_browser, args=(local_url,), daemon=True).start()

    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=port, app_dir=BACKEND_DIR, reload=False)

if __name__ == "__main__":
    main()

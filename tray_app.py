import sys
import os
import threading
import webbrowser
import time
from pathlib import Path

def get_resource_path(name):
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS) / name
    return Path(__file__).parent / name

def create_icon_image():
    try:
        from PIL import Image, ImageDraw
        img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle([4, 4, 60, 60], radius=12, fill=(231, 76, 60))
        draw.text((18, 12), 'P', fill='white')
        draw.text((14, 30), 'DD', fill='white')
        return img
    except Exception:
        return None

def start_server():
    from main import start_server
    start_server()

def on_open(tray):
    webbrowser.open('http://127.0.0.1:8765')

def on_exit(tray):
    tray.stop()
    os._exit(0)

def main():
    import pystray

    icon_image = create_icon_image()
    if icon_image is None:
        from main import start_server
        print('PDD Agent 启动中...')
        start_server()
        return

    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    time.sleep(1)
    webbrowser.open('http://127.0.0.1:8765')

    menu = pystray.Menu(
        pystray.MenuItem('打开退货分析', on_open, default=True),
        pystray.MenuItem('退出', on_exit)
    )

    tray = pystray.Icon('PDD Agent', icon_image, 'PDD 竞品监控 + 退货分析', menu)
    tray.run()

if __name__ == '__main__':
    main()

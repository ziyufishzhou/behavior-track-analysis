import os
import socket
import sys
import threading
import time
import webbrowser

_project_root = os.path.dirname(os.path.abspath(__file__))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from web import create_app

HOST = "127.0.0.1"
PORT = 5000
URL = f"http://{HOST}:{PORT}"

app = create_app()


def _is_port_open(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex((host, port)) == 0


def _open_when_ready():
    for _ in range(30):
        if _is_port_open(HOST, PORT):
            webbrowser.open(URL)
            return
        time.sleep(0.2)


if __name__ == "__main__":
    if _is_port_open(HOST, PORT):
        print(f"Web server is already running: {URL}")
        webbrowser.open(URL)
    else:
        threading.Thread(target=_open_when_ready, daemon=True).start()
        app.run(host=HOST, port=PORT, debug=False, threaded=True)

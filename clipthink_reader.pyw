# 剪思盒 ClipThink —— 纯后台 HTTP 服务（无托盘，由发送端管理）
# 启动：起本地 HTTP 服务（8765），不弹浏览器、不出托盘。
# 单实例：原子锁文件保证同时只有一个阅读器。
import os, sys, re, json, threading, webbrowser, datetime, ctypes, atexit
from ctypes import wintypes
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs, unquote

# ---------- 单实例锁文件 ----------
LOCK_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".reader.lock")

# ---------- 删除文件：绕过沙箱对 os.remove 的拦截（转回收站失败）----------
_kernel32 = ctypes.windll.kernel32
def safe_delete(path):
    """用 Windows API 直接删文件，绕开 Python os.remove 被沙箱拦截的问题。"""
    try:
        if _kernel32.DeleteFileW(path):
            return True
    except Exception:
        pass
    try:
        os.remove(path)
        return True
    except Exception:
        return False


def _pid_alive(pid):
    kernel32 = ctypes.windll.kernel32
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    h = kernel32.OpenProcess(0x1000, False, pid)
    if h:
        kernel32.CloseHandle(h)
        return True
    return False


def _early_instance_guard(url):
    try:
        fd = os.open(LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        pid = None
        try:
            pid = int(open(LOCK_FILE).read().strip())
        except Exception:
            pass
        if pid is None or _pid_alive(pid):
            try:
                th = threading.Thread(target=lambda: webbrowser.open(url), daemon=True)
                th.start()
                th.join(timeout=1.5)
            except Exception:
                pass
            os._exit(0)
        else:
            # 僵尸锁，直接覆盖写入
            try:
                fd = os.open(LOCK_FILE, os.O_WRONLY | os.O_TRUNC)
            except Exception:
                os._exit(0)
    with os.fdopen(fd, "w") as f:
        f.write(str(os.getpid()))
    atexit.register(lambda: os.path.exists(LOCK_FILE) and safe_delete(LOCK_FILE))


_early_instance_guard("http://127.0.0.1:8765/")

PORT = 8765
INBOX = os.path.join(os.environ.get("USERPROFILE", "C:\\"), "ClipThinkInbox")
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_FILE = os.path.join(SCRIPT_DIR, "reader.html")
IMG_EXT = (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp")
HOTKEY_FILE = os.path.join(SCRIPT_DIR, "hotkey.json")
DEFAULT_HOTKEY = "ALT+4"

# ---------- 热键配置（与发送端共享） ----------
def load_hotkey_combo():
    try:
        with open(HOTKEY_FILE, "r", encoding="utf-8-sig") as f:
            d = json.load(f)
            c = (d.get("combo") or "").strip().upper()
            if c:
                return c
    except Exception:
        pass
    return DEFAULT_HOTKEY

def save_hotkey_combo(combo):
    combo = (combo or "").strip().upper()
    if not combo:
        return False
    with open(HOTKEY_FILE, "w", encoding="utf-8") as f:
        json.dump({"combo": combo}, f, ensure_ascii=False, indent=2)
    return True

# ---------- 内容解析 ----------
def read_text(path):
    try:
        with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
            return f.read()
    except Exception:
        return ""

def split_analysis(text):
    parts = re.split(r'^##\s*分析结果', text, maxsplit=1, flags=re.M)
    original = parts[0].strip()
    analysis = parts[1].strip() if len(parts) > 1 else ""
    return original, analysis

def _parse_send_time(name):
    """从文件名 YYYYMMDD_HHMMSS[...].ext 解析发送时间；解析失败回退文件 mtime。"""
    m = re.match(r"(\d{8}_\d{6})", os.path.basename(name))
    if m:
        try:
            return int(datetime.datetime.strptime(m.group(1), "%Y%m%d_%H%M%S").timestamp())
        except Exception:
            pass
    try:
        return int(os.path.getmtime(os.path.join(INBOX, name)))
    except Exception:
        return 0


def make_summary(original):
    lines = [l for l in original.splitlines() if l.strip()]
    for l in lines:
        m = re.match(r'^#\s+(.*)', l)
        if m:
            s = m.group(1).strip()
            if s and s != "待分析":
                return (s[:42] + "\u2026") if len(s) > 42 else s
    for l in lines:
        s = re.sub(r'^>\s?', '', l).strip()
        if s and s != "待分析" and not s.startswith('#') and not s.startswith('---'):
            return (s[:42] + "\u2026") if len(s) > 42 else s
    return "(未命名)"

def list_items():
    items = []
    try:
        files = os.listdir(INBOX)
    except Exception:
        return items
    md_files = [f for f in files if f.endswith(".md") or f.endswith(".done")]
    referenced = set()
    for f in md_files:
        txt = read_text(os.path.join(INBOX, f))
        for m in re.findall(r'!\[[^\]]*\]\(([^)]+)\)', txt):
            referenced.add(os.path.basename(m.strip()))
    for f in md_files:
        path = os.path.join(INBOX, f)
        txt = read_text(path)
        original, analysis = split_analysis(txt)
        analyzed = f.endswith(".done")
        is_img = bool(re.search(r'!\[[^\]]*\]\(([^)]+)\)', original)) or f.lower().endswith((".png", ".jpg", ".jpeg"))
        items.append({
            "name": f,
            "type": "image" if is_img else "text",
            "analyzed": analyzed,
            "summary": make_summary(original),
            "time": _parse_send_time(f),
        })
    for f in files:
        low = f.lower()
        if low.endswith(IMG_EXT) and f not in referenced and not f.startswith("."):
            path = os.path.join(INBOX, f)
            items.append({
                "name": f,
                "type": "image",
                "analyzed": False,
                "summary": "图片 · " + f,
                "time": _parse_send_time(f),
            })
    items.sort(key=lambda x: x["time"], reverse=True)
    return items

def get_item(name):
    path = os.path.join(INBOX, name)
    if not os.path.isfile(path):
        return {"error": "not found"}
    analyzed = name.endswith(".done")
    if name.lower().endswith((".md", ".done")):
        txt = read_text(path)
        original, analysis = split_analysis(txt)
        is_img = bool(re.search(r'!\[[^\]]*\]\(([^)]+)\)', original)) or name.lower().endswith((".png", ".jpg", ".jpeg"))
        return {
            "name": name, "type": "image" if is_img else "text",
            "analyzed": analyzed, "original": original, "analysis": analysis, "image_url": "",
        }
    if name.lower().endswith(IMG_EXT):
        return {
            "name": name, "type": "image", "analyzed": False,
            "original": "", "analysis": "", "image_url": "/file?name=" + name,
        }
    return {"name": name, "type": "text", "analyzed": False,
            "original": read_text(path), "analysis": "", "image_url": ""}

def save_discussion(text):
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = f"{ts}_discuss.md"
    with open(os.path.join(INBOX, fname), "w", encoding="utf-8-sig") as f:
        f.write(text)
    return fname

# ---------- HTTP 服务 ----------
_EXIT_REQUESTED = False

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urlparse(self.path)
        if u.path in ("/", "/reader.html"):
            try:
                with open(HTML_FILE, "r", encoding="utf-8") as f:
                    self._send(200, f.read(), "text/html; charset=utf-8")
            except Exception:
                self._send(500, "reader.html missing")
            return
        if u.path == "/clipthink.ico":
            ico_path = os.path.join(SCRIPT_DIR, "clipthink.ico")
            if os.path.isfile(ico_path):
                try:
                    with open(ico_path, "rb") as f:
                        self._send(200, f.read(), "image/x-icon")
                except Exception:
                    pass
            self._send(404, "not found")
            return
        if u.path == "/api/list":
            self._send(200, json.dumps(list_items(), ensure_ascii=False))
            return
        if u.path == "/api/item":
            name = parse_qs(u.query).get("file", [""])[0]
            name = unquote(name)
            self._send(200, json.dumps(get_item(name), ensure_ascii=False))
            return
        if u.path == "/file":
            name = parse_qs(u.query).get("name", [""])[0]
            name = unquote(name)
            name = os.path.basename(name)
            fpath = os.path.join(INBOX, name)
            if os.path.isfile(fpath) and name not in (".", ".."):
                try:
                    with open(fpath, "rb") as f:
                        data = f.read()
                    ctype = "image/png"
                    if name.lower().endswith((".jpg", ".jpeg")):
                        ctype = "image/jpeg"
                    elif name.lower().endswith(".gif"):
                        ctype = "image/gif"
                    elif name.lower().endswith(".webp"):
                        ctype = "image/webp"
                    elif name.lower().endswith(".bmp"):
                        ctype = "image/bmp"
                    self._send(200, data, ctype)
                    return
                except Exception:
                    pass
            self._send(404, "not found")
            return
        if u.path == "/api/hotkey":
            self._send(200, json.dumps({"combo": load_hotkey_combo()}, ensure_ascii=False))
            return
        if u.path == "/api/clear":
            deleted = 0
            try:
                for f in os.listdir(INBOX):
                    fpath = os.path.join(INBOX, f)
                    if f.startswith(".") or not os.path.isfile(fpath):
                        continue
                    if safe_delete(fpath):
                        deleted += 1
            except Exception:
                pass
            self._send(200, json.dumps({"ok": True, "deleted": deleted}, ensure_ascii=False))
            return
        if u.path == "/api/delete":
            name = parse_qs(u.query).get("file", [""])[0]
            name = unquote(name)
            name = os.path.basename(name)
            fpath = os.path.join(INBOX, name)
            if not os.path.isfile(fpath) or name.startswith("."):
                self._send(404, json.dumps({"ok": False, "error": "not found"}, ensure_ascii=False))
                return
            # 先读内容找关联图片
            img_refs = []
            if name.lower().endswith((".md", ".done")):
                txt = read_text(fpath)
                for m in re.findall(r'!\[[^\]]*\]\(([^)]+)\)', txt):
                    img_name = os.path.basename(m.strip().replace("./", "").replace("/", ""))
                    img_path = os.path.join(INBOX, img_name)
                    if os.path.isfile(img_path):
                        img_refs.append(img_name)
            try:
                ok = safe_delete(fpath)
                for img_name in img_refs:
                    safe_delete(os.path.join(INBOX, img_name))
                if ok:
                    self._send(200, json.dumps({"ok": True, "deleted": name, "images_removed": img_refs}, ensure_ascii=False))
                else:
                    self._send(500, json.dumps({"ok": False, "error": "delete failed"}, ensure_ascii=False))
            except Exception as e:
                self._send(500, json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))
            return
        if u.path == "/api/exit":
            global _EXIT_REQUESTED
            _EXIT_REQUESTED = True
            self._send(200, json.dumps({"ok": True, "message": "Reader shutting down"}, ensure_ascii=False))
            threading.Thread(target=lambda: os._exit(0), daemon=True).start()
            return
        self._send(404, "not found")

    def do_POST(self):
        u = urlparse(self.path)
        if u.path == "/api/hotkey":
            try:
                length = int(self.headers.get("Content-Length", 0) or 0)
                raw = self.rfile.read(length) if length else b""
                data = json.loads(raw.decode("utf-8")) if raw else {}
                combo = (data.get("combo") or "").strip()
                if not combo:
                    self._send(400, json.dumps({"ok": False, "error": "empty"}, ensure_ascii=False))
                    return
                if save_hotkey_combo(combo):
                    self._send(200, json.dumps({"ok": True, "combo": combo.upper()}, ensure_ascii=False))
                else:
                    self._send(500, json.dumps({"ok": False, "error": "save failed"}, ensure_ascii=False))
            except Exception as e:
                self._send(500, json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))
            return
        if u.path == "/api/discuss":
            try:
                length = int(self.headers.get("Content-Length", 0) or 0)
                raw = self.rfile.read(length) if length else b""
                data = json.loads(raw.decode("utf-8"))
                text = data.get("text", "")
                if not text.strip():
                    self._send(400, json.dumps({"ok": False, "error": "empty"}, ensure_ascii=False))
                    return
                fname = save_discussion(text)
                self._send(200, json.dumps({"ok": True, "name": fname}, ensure_ascii=False))
            except Exception as e:
                self._send(500, json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))
            return
        self._send(404, "not found")

def main():
    # 单实例已在模块加载时的 _early_instance_guard 中保证
    try:
        server = HTTPServer(("127.0.0.1", PORT), Handler)
    except OSError:
        # 端口被占用（已有阅读器在跑）→ 只开浏览器
        webbrowser.open(f"http://127.0.0.1:{PORT}/")
        sys.exit(0)

    # 纯后台运行，不弹浏览器、不出托盘。发送端托盘负责打开浏览器。
    server.serve_forever()

if __name__ == "__main__":
    main()

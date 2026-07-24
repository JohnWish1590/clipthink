# -*- coding: utf-8 -*-
"""
剪思盒热键监听器（Python 版，带系统托盘图标 + 运行日志）
- 全局热键（可在阅读器里自定义）→ 把剪贴板（文字/图片）发到 剪思盒
- 系统托盘常驻图标，右键可「立即执行」/ 打开日志 / 打开收件箱 / 打开阅读器 / 退出
- 使用 Windows 原生 RegisterHotKey，稳定可靠
- 所有事件（含错误）写入 log.txt，便于排查
- 单实例：用锁文件（原子 O_EXCL 抢锁）保证同时只有一个发送端，避免重复发送
"""
import os
import sys
import re
import json
import time
import ctypes
import logging
import threading
import subprocess
import shutil
from ctypes import wintypes
import atexit
import urllib.request
import urllib.error
from datetime import datetime

# ---------- 单实例锁文件：必须在导入 tkinter/PIL/pystray 之前检测，否则重复实例会卡在重型导入 ----------
LOCK_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".sender.lock")
# 命令文件：已在运行的实例通过它接收其它启动参数（桌面快捷方式带 --open-reader / --open-inbox 时）
CMD_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".sender.cmd")


def _parse_action_arg():
    """从命令行解析动作参数（供桌面快捷方式带动作启动）。"""
    for a in sys.argv[1:]:
        if a in ("--open-reader", "--open-inbox"):
            return a
    return None


REQUESTED_ACTION = _parse_action_arg()


def _pid_alive(pid):
    kernel32 = ctypes.windll.kernel32
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    h = kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
    if h:
        kernel32.CloseHandle(h)
        return True
    return False


def _early_sender_guard():
    # 用原子 O_EXCL 抢锁，杜绝竞态：先创建者胜，后到者直接判重退出
    try:
        fd = os.open(LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        pid = None
        try:
            pid = int(open(LOCK_FILE).read().strip())
        except Exception:
            pass
        if pid is None or _pid_alive(pid):
            # 已在运行且本次带动作参数：把动作写入命令文件，交给运行实例处理
            if REQUESTED_ACTION:
                try:
                    with open(CMD_FILE, "w", encoding="utf-8") as cf:
                        cf.write(REQUESTED_ACTION)
                except Exception:
                    pass
            os._exit(0)  # 重复实例：静默强制退出，不导入重型模块
        else:
            # 锁是僵尸（上次崩溃残留），接管：直接覆盖写入（避免 os.remove 被沙箱拦截）
            try:
                fd = os.open(LOCK_FILE, os.O_WRONLY | os.O_TRUNC)
            except Exception:
                os._exit(0)
    with os.fdopen(fd, "w") as f:
        f.write(str(os.getpid()))
    atexit.register(lambda: os.path.exists(LOCK_FILE) and os.remove(LOCK_FILE))


_early_sender_guard()

import tkinter as tk
from PIL import Image, ImageDraw, ImageFont
import pystray
from pystray import Icon, Menu, MenuItem

# Windows 常量：以无窗口方式启动子进程（彻底消除后台黑框）
CREATE_NO_WINDOW = 0x08000000

# ---------- 路径配置 ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "log.txt")
INBOX = r"C:\Users\user\ClipThinkInbox"
SEND_SCRIPT = os.path.join(BASE_DIR, "send_clipboard.py")
HOTKEY_FILE = os.path.join(BASE_DIR, "hotkey.json")
CONFIG_FILE = os.path.join(BASE_DIR, "clipthink.json")
DEFAULT_HOTKEY = "ALT+4"

# ---------- 收件箱分析（WorkBuddy 本地 HTTP API / serve 实例）----------
CODEBUDDY_CLI = r"C:\Program Files\WorkBuddy\resources\app.asar.unpacked\cli\bin\codebuddy"
ANALYSIS_PORT = 8090
SERVE_SESSION = "inbox-analysis"  # 仅 serve 实例标识；runs 实际会话由提交时 sessionId 决定
# 所有收件箱分析统一归到用户建的专用会话（WorkBuddy 里叫"分析WorkBuddy收件箱待处理文件"），
# 这样手动触发与定时任务的分析都落到一个地方，便于在 WorkBuddy 里回看。
ANALYSIS_SESSION_ID = "inbox-analysis"
ANALYSIS_RUN_TIMEOUT = 180  # 单次分析超时（秒）。注意：serve 的 X-Codebuddy-Run-Timeout 头以毫秒为单位，发送时须 ×1000
# 严格限定：只写 .done，不污染收件箱；分析控制在 250 字内，避免超长生成卡死
ANALYSIS_PROMPT = (
    "你是 剪思盒分析助手。请执行：\n"
    "1. 遍历 C:\\Users\\user\\ClipThinkInbox 下所有扩展名为 .md 但不是 .done 的文件（这些是尚未分析的待处理项）。\n"
    "2. 对每个文件：\n"
    "   a. 读取全文。文件以 '# 待分析' 开头，其后为原文内容。\n"
    "   b. 用中文做简洁结构化分析（金融投研视角），总字数控制在 250 字以内：要点提炼、关键事实/数据、判断与疑问。\n"
    "   c. 保留原文整体不变，在原文末尾追加一个空行、然后 '## 分析结果'、再一个空行、再写分析内容。\n"
    "   d. 将结果以 UTF-8 带 BOM 编码写入同名 .done 文件（例如 'x.md' → 'x.md.done'）。\n"
    "   e. 原 .md 文件可保留，不要删除。\n"
    "3. 严格约束：只写 .done 文件，不要创建任何其它文件（不要写新的 .md、不要写笔记或日志文件）。\n"
    "4. 全部完成后，回复一行：'已分析 N 条'（N 为实际分析条数；若没有任何待分析项，回复'没有待分析项'）。\n"
    "注意：已存在对应 .done 的文件不要重复分析；只处理没有 .done 的 .md 文件。"
)
# 用 python.exe（非 pythonw.exe）调发送脚本，确保能捕获 stdout
PYTHON_EXE = os.path.join(os.path.dirname(sys.executable), "python.exe")
if not os.path.exists(PYTHON_EXE):
    PYTHON_EXE = sys.executable  # 回退

# ---------- 日志 ----------
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    encoding="utf-8",
)
log = logging.getLogger("wb-sender")


def log_info(msg):
    log.info(msg)


def log_err(msg):
    log.error(msg, exc_info=True)


log_info("==== 程序启动 ====")
log_info(f"BASE_DIR={BASE_DIR}")
log_info(f"SEND_SCRIPT exists={os.path.exists(SEND_SCRIPT)}")


# ---------- 托盘图标（与阅读器一致：3D 玻璃质感，蓝紫渐变 + 对话气泡） ----------
def make_icon():
    S = 128
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    px = img.load()
    c1 = (108, 142, 255)   # 左上 蓝
    c2 = (156, 92, 255)    # 右下 紫
    for y in range(S):
        for x in range(S):
            t = (x + y) / (2.0 * S)
            r = int(c1[0] + (c2[0] - c1[0]) * t)
            g = int(c1[1] + (c2[1] - c1[1]) * t)
            b = int(c1[2] + (c2[2] - c1[2]) * t)
            px[x, y] = (r, g, b, 255)
    # 圆角遮罩
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle([5, 5, S - 5, S - 5], radius=30, fill=255)
    img.putalpha(mask)
    # 顶部高光（玻璃光泽）
    gloss = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    gd = ImageDraw.Draw(gloss)
    gd.ellipse([6, -36, S - 6, 74], fill=(255, 255, 255, 72))
    gd.rounded_rectangle([5, 5, S - 5, S - 5], radius=30, outline=(255, 255, 255, 130), width=2)
    img = Image.alpha_composite(img, gloss)
    # 底部内阴影（立体感）
    sh = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    sd.ellipse([6, S - 52, S - 6, S + 32], fill=(0, 0, 0, 45))
    img = Image.alpha_composite(img, sh)
    # 白色对话气泡（阴影 + 气泡 + 小尾巴 + 三点）
    d = ImageDraw.Draw(img)
    d.ellipse([34, 92, 96, 104], fill=(0, 0, 0, 50))                 # 气泡投影
    d.polygon([(46, 82), (38, 100), (64, 82)], fill=(255, 255, 255, 255))  # 尾巴
    d.rounded_rectangle([30, 34, 98, 84], radius=16, fill=(255, 255, 255, 255))  # 气泡主体
    for dx in (48, 60, 72):                                          # 三点
        d.ellipse([dx, 53, dx + 9, 62], fill=(120, 110, 240, 255))
    return img


# ---------- 剪贴板发送（内嵌，不依赖外部子进程） ----------
def _recent_texts(limit=60):
    """返回收件箱最近 limit 个 .md/.done 的正文（strip），用于去重。"""
    res = []
    try:
        files = sorted(
            [f for f in os.listdir(INBOX) if f.endswith(".md") or f.endswith(".done")],
            key=lambda f: os.path.getmtime(os.path.join(INBOX, f)),
            reverse=True,
        )
    except Exception:
        return res
    for f in files[:limit]:
        try:
            with open(os.path.join(INBOX, f), "r", encoding="utf-8-sig", errors="replace") as fh:
                txt = fh.read()
            # 去掉标题前缀（兼容旧文件用字面量 \\n 或新文件用真实换行）
            if txt.startswith("# 待分析"):
                txt = txt[len("# 待分析"):].lstrip("\r\n")
                # 旧版 bug：文件里可能写了字面量 \\n
                if txt.startswith("\\n"):
                    txt = txt[2:].lstrip("\\n")
            res.append(txt.strip())
        except Exception:
            pass
    return res


def _recent_image_hashes(limit=60):
    import hashlib
    res = set()
    try:
        files = sorted(
            [f for f in os.listdir(INBOX)
             if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"))],
            key=lambda f: os.path.getmtime(os.path.join(INBOX, f)),
            reverse=True,
        )
    except Exception:
        return res
    for f in files[:limit]:
        try:
            with open(os.path.join(INBOX, f), "rb") as fh:
                res.add(hashlib.md5(fh.read()).hexdigest())
        except Exception:
            pass
    return res


def send_clipboard_direct():
    """把当前剪贴板内容写入 ClipThinkInbox，返回 md_path 或 None/错误字符串。"""
    from PIL import ImageGrab

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(INBOX, exist_ok=True)

    # 1. 尝试图片
    img = None
    try:
        img = ImageGrab.grabclipboard()
    except Exception as e:
        log_info(f"ImageGrab.grabclipboard() 失败: {e}")

    if img is not None:
        try:
            import io, hashlib
            buf = io.BytesIO()
            img.save(buf, "PNG")
            data = buf.getvalue()
            new_hash = hashlib.md5(data).hexdigest()
            if new_hash in _recent_image_hashes():
                log_info("图片与收件箱已有内容相同，跳过重复发送")
                return "DUP_IMAGE"
            png_path = os.path.join(INBOX, f"{ts}.png")
            with open(png_path, "wb") as f:
                f.write(data)
            md_path = os.path.join(INBOX, f"{ts}.md")
            content = f"# 待分析图片\n\n![clipboard]({ts}.png)\n"
            with open(md_path, "w", encoding="utf-8-sig") as f:
                f.write(content)
            return md_path
        except Exception as e:
            log_info(f"图片保存失败，回退文字模式: {e}")
            img = None

    # 2. 文字模式（用 tkinter，因为 show_toast 已依赖它）
    text = ""
    try:
        root = tk.Tk()
        root.withdraw()
        try:
            text = root.clipboard_get()
        except tk.TclError as e:
            log_info(f"clipboard_get() TclError: {e}")
        try:
            root.destroy()
        except Exception:
            pass
    except Exception as e:
        log_info(f"tkinter 读取剪贴板失败: {e}")

    if text and text.strip():
        norm = text.strip()
        if norm in _recent_texts():
            log_info("文字与收件箱已有内容相同，跳过重复发送")
            return "DUP_TEXT"
        md_path = os.path.join(INBOX, f"{ts}.md")
        content = f"# 待分析\n\n{text}"
        with open(md_path, "w", encoding="utf-8-sig") as f:
            f.write(content)
        return md_path
    return "剪贴板为空或非文字/图片"


# ---------- 热键动作 ----------
def do_send():
    log_info("热键/立即执行触发，准备发送剪贴板")
    try:
        result = send_clipboard_direct()
        if result == "剪贴板为空或非文字/图片":
            log_info("剪贴板为空，未发送")
            threading.Thread(target=show_toast, args=("剪贴板为空",),
                             kwargs={"kind": "err"}, daemon=True).start()
        elif result == "DUP_TEXT" or result == "DUP_IMAGE":
            log_info("内容与收件箱已有条目相同，未重复发送")
            threading.Thread(target=show_toast, args=("已发送过，不重复",),
                             daemon=True).start()
        elif result and os.path.exists(result):
            log_info(f"发送成功：{result}")
            threading.Thread(target=show_toast, args=("已发送",), daemon=True).start()
        else:
            log_err(f"发送未成功：result={result}")
            threading.Thread(target=show_toast, args=("发送失败",),
                             kwargs={"kind": "err"}, daemon=True).start()
    except Exception as e:
        log_err(f"发送异常：{e}")
        threading.Thread(target=show_toast, args=("发送异常",),
                         kwargs={"kind": "err"}, daemon=True).start()


def on_activate():
    do_send()


def show_toast(text="已发送", dwell_ms=600, kind="ok"):
    """在鼠标指针旁边弹一个轻量提示（ok=绿框浅底，err=红框浅底，半透明，自动消失）"""
    bg = "#f4fbf5" if kind == "ok" else "#fdecea"
    border = "#43a047" if kind == "ok" else "#e53935"
    fg = "#1b5e20" if kind == "ok" else "#b71c1c"
    try:
        root = tk.Tk()
        root.overrideredirect(True)
        root.attributes("-topmost", True)
        root.attributes("-alpha", 0.92)
        # 浅色卡片 + 彩色边框（类似系统通知的轻量风格，不刺眼）
        card = tk.Frame(root, bg=bg, highlightbackground=border,
                        highlightthickness=2)
        card.pack()
        label = tk.Label(
            card, text=text, bg=bg, fg=fg,
            font=("Microsoft YaHei UI", 13, "bold"),
            padx=20, pady=11,
        )
        label.pack()
        root.update_idletasks()
        w = root.winfo_width()
        h = root.winfo_height()
        px = root.winfo_pointerx()
        py = root.winfo_pointery()
        # 放在鼠标右下方 14px，避免遮住指针；越界则翻到左/上方
        x = px + 14
        y = py + 14
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        if x + w > sw:
            x = px - w - 14
        if y + h > sh:
            y = py - h - 14
        root.geometry(f"+{x}+{y}")
        root.after(dwell_ms, root.destroy)
        root.mainloop()
    except Exception as e:
        log_err(f"提示框异常：{e}")


# ---------- 全局热键（Windows 原生 RegisterHotKey，可配置 + 热重载） ----------
WM_HOTKEY = 0x0312
WM_QUIT = 0x0012
PM_REMOVE = 0x0001
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
user32 = ctypes.windll.user32


def _load_config():
    """读取用户配置（阅读器位置、退出时是否关闭阅读器等）。"""
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_config(cfg):
    """保存用户配置。"""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        log_err(f"保存配置失败：{e}")
        return False


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


def get_hotkey_mtime():
    try:
        return os.path.getmtime(HOTKEY_FILE)
    except Exception:
        return 0


def keyname_to_vk(key):
    key = key.upper()
    if len(key) == 1 and "A" <= key <= "Z":
        return 0x41 + (ord(key) - ord("A"))
    if len(key) == 1 and "0" <= key <= "9":
        return 0x30 + (ord(key) - ord("0"))
    if key.startswith("F") and key[1:].isdigit():
        n = int(key[1:])
        if 1 <= n <= 24:
            return 0x70 + (n - 1)
    m = {"SPACE": 0x20, "TAB": 0x09, "ENTER": 0x0D, "RETURN": 0x0D, "ESC": 0x1B,
         "ESCAPE": 0x1B, "BACKSPACE": 0x08, "DELETE": 0x2E, "INSERT": 0x2D,
         "HOME": 0x24, "END": 0x23, "PAGEUP": 0x21, "PAGEDOWN": 0x22,
         "LEFT": 0x25, "RIGHT": 0x27, "UP": 0x26, "DOWN": 0x28,
         "CAPSLOCK": 0x14, "NUMLOCK": 0x90, "SCROLLLOCK": 0x91,
         "PRINTSCREEN": 0x2C, "PAUSE": 0x13, "BACKTICK": 0xC0}
    if key in m:
        return m[key]
    if len(key) == 1:
        return ord(key)
    return None


def combo_to_regs(combo):
    """把 'Ctrl+Alt+4' 之类解析成 [(id, mods, vk), ...]；数字键额外注册小键盘变体。"""
    parts = [p.strip().upper() for p in combo.split("+") if p.strip()]
    mods = 0
    key = None
    for p in parts:
        if p in ("CTRL", "CONTROL"):
            mods |= MOD_CONTROL
        elif p == "ALT":
            mods |= MOD_ALT
        elif p == "SHIFT":
            mods |= MOD_SHIFT
        elif p in ("WIN", "LWIN", "RWIN"):
            mods |= MOD_WIN
        else:
            key = p
    if key is None:
        return []
    vk = keyname_to_vk(key)
    if vk is None:
        return []
    regs = [(1, mods, vk)]
    if key in "0123456789":
        regs.append((2, mods, 0x60 + int(key)))  # 小键盘对应键
    return regs


def register_combo(combo):
    regs = combo_to_regs(combo)
    if not regs:
        log_err(f"无法解析热键组合：{combo}")
        return []
    registered = []
    for (hid, mods, vk) in regs:
        if user32.RegisterHotKey(None, hid, mods, vk):
            registered.append(hid)
            log_info(f"已注册热键 id={hid} mods={mods:#06x} vk={vk:#04x} ({combo})")
        else:
            log_err(f"注册热键失败 combo={combo} id={hid} GetLastError={ctypes.GetLastError()}")
    return registered


def unregister_all(regs):
    for hid in regs:
        try:
            user32.UnregisterHotKey(None, hid)
        except Exception:
            pass


def hotkey_thread():
    """独立线程：注册全局热键 + 轮询消息 + 监听 hotkey.json 变化热重载。"""
    combo = load_hotkey_combo()
    regs = register_combo(combo)
    last_mtime = get_hotkey_mtime()
    log_info(f"初始热键：{combo}")
    msg = wintypes.MSG()
    while True:
        m = get_hotkey_mtime()
        if m and m != last_mtime:
            last_mtime = m
            new_combo = load_hotkey_combo()
            if new_combo != combo:
                unregister_all(regs)
                regs = register_combo(new_combo)
                combo = new_combo
                log_info(f"热键已切换为 {combo}")
        while user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, PM_REMOVE) != 0:
            if msg.message == WM_QUIT:
                unregister_all(regs)
                return
            if msg.message == WM_HOTKEY:
                try:
                    do_send()
                except Exception as e:
                    log_err(f"do_send 异常：{e}")
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
        time.sleep(0.05)


# ---------- 托盘菜单动作 ----------
def menu_execute(icon, item):
    threading.Thread(target=do_send, daemon=True).start()


def open_log(icon, item):
    try:
        os.startfile(LOG_FILE)
    except Exception as e:
        log_err(f"打开日志失败：{e}")


def open_inbox(icon, item):
    try:
        os.startfile(INBOX)
    except Exception as e:
        log_err(f"打开收件箱失败：{e}")


READER_SCRIPT = os.path.join(BASE_DIR, "clipthink_reader.pyw")
READER_URL = "http://127.0.0.1:8765/"


# ---------- 阅读器窗口位置与退出行为（用户偏好） ----------
def _screen_size():
    """返回主屏幕宽、高（像素）。"""
    user32 = ctypes.windll.user32
    return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)


def _reader_geometry(side="right"):
    """按「半屏贴边」计算阅读器窗口尺寸与位置。side ∈ {'left','right'}。"""
    sw, sh = _screen_size()
    w = sw // 2
    h = sh
    if side == "left":
        return w, h, 0, 0
    return w, h, w, 0


def _ask_choice(title, message, options, remember_default=True):
    """弹出单选对话框。options=[(label, value),...]，返回 (value, remember)。"""
    result = {"value": "", "remember": remember_default}
    ev = threading.Event()

    def _run():
        root = tk.Tk()
        root.title(title)
        root.attributes("-topmost", True)
        root.resizable(False, False)
        tk.Label(root, text=message, wraplength=360, justify="left").pack(padx=20, pady=(14, 8))
        var = tk.StringVar(value=result["value"])
        for label, value in options:
            tk.Radiobutton(root, text=label, variable=var, value=value, anchor="w").pack(fill="x", padx=20, pady=2)
        rem = tk.BooleanVar(value=remember_default)
        tk.Checkbutton(root, text="记住我的选择", variable=rem, anchor="w").pack(fill="x", padx=20, pady=(10, 0))

        def _ok():
            result["value"] = var.get()
            result["remember"] = rem.get()
            root.destroy()
            ev.set()

        def _cancel():
            root.destroy()
            ev.set()

        tk.Button(root, text="确定", command=_ok, width=12).pack(pady=16)
        root.protocol("WM_DELETE_WINDOW", _cancel)
        root.mainloop()

    threading.Thread(target=_run, daemon=True).start()
    ev.wait(timeout=60)
    return result["value"], result["remember"]


def _ask_yes_no_remember(title, message, default_yes=True, remember_default=True):
    """弹出带「记住选择」复选框的是/否对话框，返回 (yes, remember)。"""
    result = {"yes": default_yes, "remember": remember_default}
    ev = threading.Event()

    def _run():
        root = tk.Tk()
        root.title(title)
        root.attributes("-topmost", True)
        root.resizable(False, False)
        tk.Label(root, text=message, wraplength=360, justify="left").pack(padx=20, pady=(14, 8))
        yes_var = tk.BooleanVar(value=default_yes)
        rem_var = tk.BooleanVar(value=remember_default)
        tk.Checkbutton(root, text="同时关闭阅读器", variable=yes_var, anchor="w").pack(fill="x", padx=20, pady=2)
        tk.Checkbutton(root, text="记住我的选择", variable=rem_var, anchor="w").pack(fill="x", padx=20, pady=2)

        def _ok():
            result["yes"] = yes_var.get()
            result["remember"] = rem_var.get()
            root.destroy()
            ev.set()

        tk.Button(root, text="确定", command=_ok, width=12).pack(pady=16)
        root.protocol("WM_DELETE_WINDOW", _ok)
        root.mainloop()

    threading.Thread(target=_run, daemon=True).start()
    ev.wait(timeout=60)
    return result["yes"], result["remember"]


def _close_reader():
    """通过 .reader.lock 中的 PID 结束阅读器进程。"""
    reader_lock = os.path.join(BASE_DIR, ".reader.lock")
    if not os.path.exists(reader_lock):
        return
    try:
        pid = int(open(reader_lock, "r", encoding="utf-8").read().strip())
    except Exception:
        return
    if not _pid_alive(pid):
        return
    kernel32 = ctypes.windll.kernel32
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    h = kernel32.OpenProcess(0x0001, False, pid)  # PROCESS_TERMINATE
    if h:
        kernel32.TerminateProcess(h, 0)
        kernel32.CloseHandle(h)
        log_info(f"已结束阅读器进程 PID={pid}")


def _default_browser():
    """探测默认浏览器，返回 (exe_path, brand)；brand ∈ {chrome, edge, firefox, other}。
    失败返回 (None, None)。"""
    try:
        import winreg
        progid = None
        # 1) 取 UserChoice 的 ProgId（当前用户实际默认）
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\Shell\Associations\UrlAssociations\https\UserChoice",
            )
            progid, _ = winreg.QueryValueEx(key, "ProgId")
            winreg.CloseKey(key)
        except Exception:
            pass
        # 2) 从 ProgId 读 open 命令，提取 exe 路径
        exe = None
        if progid:
            try:
                key = winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, rf"{progid}\shell\open\command")
                cmd, _ = winreg.QueryValueEx(key, "")
                winreg.CloseKey(key)
                m = re.search(r'"([^"]+\.exe)"', cmd)
                if m and os.path.exists(m.group(1)):
                    exe = m.group(1)
            except Exception:
                exe = None
        # 3) 回退：遍历 StartMenuInternet 注册的浏览器
        if not exe or not os.path.exists(exe):
            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Clients\StartMenuInternet")
                i = 0
                while True:
                    name = winreg.EnumKey(key, i)
                    i += 1
                    try:
                        sub = winreg.OpenKey(key, rf"{name}\shell\open\command")
                        cmd, _ = winreg.QueryValueEx(sub, "")
                        winreg.CloseKey(sub)
                        m = re.search(r'"([^"]+\.exe)"', cmd)
                        if m and os.path.exists(m.group(1)):
                            exe = m.group(1)
                            break
                    except Exception:
                        continue
                winreg.CloseKey(key)
            except Exception:
                pass
        if not exe or not os.path.exists(exe):
            return None, None
        low = exe.lower()
        if "msedge" in low:
            brand = "edge"
        elif "chrome" in low:
            brand = "chrome"
        elif "firefox" in low:
            brand = "firefox"
        else:
            brand = "other"
        return exe, brand
    except Exception:
        return None, None


def _open_reader_browser():
    """用默认浏览器打开纯净应用窗口：Chrome/Edge 用 --app=<url>（无地址栏/标签栏），
    并按用户偏好占主屏幕半屏贴左/右；其它/探测失败降级为系统默认打开。"""
    try:
        exe, brand = _default_browser()
        cfg = _load_config()
        side = cfg.get("reader_side")
        if not side:
            chosen, remember = _ask_choice(
                "阅读器位置",
                "阅读器窗口默认放在屏幕哪一侧？\n（后续可在托盘右键「设置」中修改）",
                [("左侧", "left"), ("右侧", "right")],
                remember_default=True,
            )
            side = chosen if chosen else "right"
            if remember or True:  # 首次选择直接记住
                cfg["reader_side"] = side
                _save_config(cfg)
        w, h, x, y = _reader_geometry(side)
        if exe and brand in ("chrome", "edge"):
            subprocess.Popen(
                [exe, f"--app={READER_URL}", f"--window-size={w},{h}", f"--window-position={x},{y}"],
                creationflags=CREATE_NO_WINDOW,
            )
            log_info(f"已用 {brand} 纯净应用窗口打开阅读器：{exe}，位置={side} ({w}x{h}@{x},{y})")
            return True
        if exe and brand == "firefox":
            subprocess.Popen([exe, "--new-window", READER_URL], creationflags=CREATE_NO_WINDOW)
            log_info(f"已用 firefox 新窗口打开阅读器：{exe}")
            return True
    except Exception as e:
        log_err(f"探测/启动浏览器失败，回退默认打开：{e}")
    # 其它或探测失败：回退系统默认打开
    try:
        os.startfile(READER_URL)
        return True
    except Exception:
        try:
            import webbrowser
            webbrowser.open(READER_URL)
            return True
        except Exception as e:
            log_err(f"打开浏览器失败：{e}")
            return False


def open_reader(icon, item):
    try:
        if _port_listening(8765):
            if _open_reader_browser():
                log_info("阅读器已在运行，已打开浏览器")
            return
        pythonw = sys.executable
        if not pythonw or not os.path.exists(pythonw):
            pythonw = os.path.join(BASE_DIR, "python.exe")
        subprocess.Popen([pythonw, READER_SCRIPT], creationflags=CREATE_NO_WINDOW)
        # 轮询等待服务就绪，最多 5 秒
        for _ in range(50):
            if _port_listening(8765):
                break
            time.sleep(0.1)
        if _port_listening(8765):
            if _open_reader_browser():
                log_info("已启动/打开阅读器")
            else:
                show_toast("阅读器已启动，但无法打开浏览器，请手动访问 127.0.0.1:8765", kind="err")
        else:
            show_toast("阅读器服务未能启动，请查看日志", kind="err")
    except Exception as e:
        log_err(f"打开阅读器失败：{e}")
        threading.Thread(target=show_toast, args=("打开阅读器失败，请查看日志",), kwargs={"kind": "err"}, daemon=True).start()


def _port_listening(port):
    import socket
    s = socket.socket()
    s.settimeout(1)
    try:
        s.connect(("127.0.0.1", port))
        return True
    except Exception:
        return False
    finally:
        s.close()


def _find_node():
    n = shutil.which("node")
    if n and os.path.exists(n):
        return n
    for cand in (r"C:\Program Files\nodejs\node.exe",
                 r"C:\Users\user\.workbuddy\binaries\node\versions\22.22.2\node.exe"):
        if os.path.exists(cand):
            return cand
    return None


def ensure_serve():
    """确保 WorkBuddy 分析 serve 实例在运行（无鉴权，本地 8090）。发送端启动时被调用。"""
    if _port_listening(ANALYSIS_PORT):
        log_info(f"分析 serve 已在运行 (port {ANALYSIS_PORT})")
        return True
    if not os.path.exists(CODEBUDDY_CLI):
        log_err(f"未找到 codebuddy CLI：{CODEBUDDY_CLI}")
        return False
    env = os.environ.copy()
    env["CODEBUDDY_GATEWAY_AUTH"] = "none"
    env["CODEBUDDY_DISABLE_REQUEST_VALIDATION"] = "1"
    try:
        node_exe = _find_node()
        if not node_exe:
            log_err("未找到 node，无法启动分析 serve")
            return False
        subprocess.Popen(
            [node_exe, CODEBUDDY_CLI, "--serve", "--port", str(ANALYSIS_PORT),
             "--session-id", SERVE_SESSION, "-y"],
            env=env, creationflags=CREATE_NO_WINDOW,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        log_info(f"已启动分析 serve 实例 (port {ANALYSIS_PORT})")
        return True
    except Exception as e:
        log_err(f"启动分析 serve 失败：{e}")
        return False


def _submit_analysis():
    """向 serve 实例提交一次收件箱分析任务，返回 runId 或 None。"""
    payload = {
        "id": "tray-" + datetime.now().strftime("%Y%m%d_%H%M%S_%f"),
        "type": "message",
        "payload": {"text": ANALYSIS_PROMPT},
        "sessionId": ANALYSIS_SESSION_ID,
        "sender": {"id": "tray", "name": "托盘按钮"},
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        f"http://127.0.0.1:{ANALYSIS_PORT}/api/v1/runs",
        data=data,
        headers={
            "Content-Type": "application/json",
            # serve 的 X-Codebuddy-Run-Timeout 头以毫秒为单位（非秒）：180s -> 180000ms
            "X-Codebuddy-Run-Timeout": str(ANALYSIS_RUN_TIMEOUT * 1000),
        },
        method="POST",
    )
    resp = json.loads(urllib.request.urlopen(req, timeout=20).read().decode("utf-8"))
    return resp.get("data", {}).get("runId")


def _watch_run(run_id):
    """后台轮询分析任务状态，完成后弹提示。"""
    if not run_id:
        return
    url = f"http://127.0.0.1:{ANALYSIS_PORT}/api/v1/runs/{run_id}"
    done = False
    for _ in range(45):
        try:
            st = json.loads(urllib.request.urlopen(url, timeout=10).read().decode("utf-8"))
            if not st.get("data", {}).get("active", True):
                done = True
                break
        except Exception:
            pass
        time.sleep(6)
    if done:
        threading.Thread(target=show_toast, args=("分析完成，可在阅读器查看",),
                         kwargs={"dwell_ms": 2200}, daemon=True).start()


def _count_pending():
    """收件箱中还有多少 .md 没生成对应 .done（即待分析项）。"""
    try:
        files = os.listdir(INBOX)
    except Exception:
        return 0
    md = {f for f in files if f.endswith(".md")}
    done = {f for f in files if f.endswith(".md.done")}
    pending = md - {d[:-5] for d in done}  # x.md.done -> x.md
    return len(pending)


def auto_analyze():
    """每小时定时触发（由发送端后台定时器调用，尽量不弹打扰性提示）。
    仅当有待分析项时才真正提交，避免空跑与每小时弹窗。"""
    try:
        if _count_pending() == 0:
            log_info("定时分析：无待分析项，跳过")
            return
        if not ensure_serve():
            log_err("定时分析：分析服务不可用，跳过")
            return
        run_id = _submit_analysis()
        log_info(f"定时分析已提交 runId={run_id}")
        threading.Thread(target=_watch_run, args=(run_id,), daemon=True).start()
    except Exception as e:
        log_err(f"定时分析异常：{e}")


def _hourly_timer():
    """每小时触发一次收件箱分析；首次延迟 1 小时，纯后台、静默。"""
    while True:
        time.sleep(3600)
        auto_analyze()


def analyze_inbox(icon, item):
    """托盘菜单：分析收件箱。通过本地 serve 实例触发 WorkBuddy 立即分析。"""
    log_info("用户选择分析收件箱")
    if not ensure_serve():
        threading.Thread(target=show_toast, args=("分析服务不可用",),
                         kwargs={"kind": "err"}, daemon=True).start()
        return
    try:
        run_id = _submit_analysis()
        log_info(f"分析任务已提交 runId={run_id}")
        threading.Thread(target=_watch_run, args=(run_id,), daemon=True).start()
        threading.Thread(target=show_toast, args=("正在分析收件箱…",),
                         kwargs={"dwell_ms": 1500}, daemon=True).start()
    except Exception as e:
        log_err(f"提交分析任务失败：{e}")
        threading.Thread(target=show_toast, args=("分析提交失败",),
                         kwargs={"kind": "err"}, daemon=True).start()


def open_settings(icon, item):
    """托盘菜单：设置阅读器位置与退出行为。"""
    cfg = _load_config()
    current_side = cfg.get("reader_side", "right")
    chosen, _ = _ask_choice(
        "剪思盒设置",
        "阅读器窗口默认放在屏幕哪一侧？",
        [("左侧", "left"), ("右侧", "right")],
        remember_default=False,
    )
    if chosen:
        cfg["reader_side"] = chosen
    close_reader, _ = _ask_yes_no_remember(
        "剪思盒设置",
        "退出托盘时，是否同时关闭阅读器？",
        default_yes=cfg.get("close_reader_on_exit", True),
        remember_default=False,
    )
    cfg["close_reader_on_exit"] = close_reader
    cfg["asked_close_reader"] = True
    _save_config(cfg)
    threading.Thread(target=show_toast, args=(f"设置已保存：阅读器在{'左' if cfg['reader_side']=='left' else '右'}侧，退出{'关闭' if close_reader else '不关闭'}阅读器",),
                     kwargs={"dwell_ms": 2000}, daemon=True).start()


def quit_app(icon, item):
    log_info("用户选择退出")
    cfg = _load_config()
    close_reader = cfg.get("close_reader_on_exit")
    asked = cfg.get("asked_close_reader", False)
    if close_reader is None or not asked:
        yes, remember = _ask_yes_no_remember(
            "退出剪思盒",
            "退出托盘时，是否同时关闭阅读器？",
            default_yes=True,
            remember_default=True,
        )
        close_reader = yes
        if remember:
            cfg["close_reader_on_exit"] = close_reader
            cfg["asked_close_reader"] = True
            _save_config(cfg)
    if close_reader:
        _close_reader()
    try:
        icon.stop()
    except Exception:
        pass


# ---------- 命令文件监听（接收其它启动实例通过 IPC 转交的动作）----------
def _cmd_listener():
    """监听命令文件 .sender.cmd：桌面快捷方式带 --open-reader / --open-inbox 启动时，
    若主程序已在运行，重复实例会把动作写入此文件；本线程检测到即执行，并删除文件防重复触发。"""
    while True:
        try:
            if os.path.exists(CMD_FILE):
                with open(CMD_FILE, "r", encoding="utf-8") as cf:
                    action = cf.read().strip()
                try:
                    os.remove(CMD_FILE)
                except Exception:
                    pass
                if action == "--open-reader":
                    log_info("收到命令文件：打开阅读器")
                    threading.Thread(target=open_reader, args=(None, None), daemon=True).start()
                elif action == "--open-inbox":
                    log_info("收到命令文件：打开收件箱")
                    threading.Thread(target=open_inbox, args=(None, None), daemon=True).start()
        except Exception as e:
            log_err(f"命令监听异常：{e}")
        time.sleep(0.3)


# ---------- 主流程 ----------
def main():
    log_info("启动全局热键线程")
    t = threading.Thread(target=hotkey_thread, daemon=True)
    t.start()
    # 后台拉起分析 serve 实例（不阻塞托盘显示）
    threading.Thread(target=ensure_serve, daemon=True).start()
    # 每小时自动分析收件箱（静默；仅有待分析项时才真正提交）
    threading.Thread(target=_hourly_timer, daemon=True).start()
    # 监听桌面快捷方式通过命令文件转交的动作（主程序已在运行时，重复实例写入 .sender.cmd）
    threading.Thread(target=_cmd_listener, daemon=True).start()
    # 若本次是带动作参数启动（桌面快捷方式指向主程序），启动后执行对应动作
    if REQUESTED_ACTION == "--open-reader":
        threading.Thread(target=open_reader, args=(None, None), daemon=True).start()
    elif REQUESTED_ACTION == "--open-inbox":
        threading.Thread(target=open_inbox, args=(None, None), daemon=True).start()
    # 退出时清理命令文件
    atexit.register(lambda: os.path.exists(CMD_FILE) and os.remove(CMD_FILE))
    combo = load_hotkey_combo()
    icon = Icon(
        "ClipThink",
        make_icon(),
        f"剪思盒 - 运行中 ({combo})",
        Menu(
            MenuItem("立即执行（发送当前剪贴板）", menu_execute),
            MenuItem("分析收件箱", analyze_inbox),
            Menu.SEPARATOR,
            MenuItem("打开运行日志", open_log),
            MenuItem("打开收件箱", open_inbox),
            MenuItem("打开阅读器", open_reader),
            Menu.SEPARATOR,
            MenuItem("设置", open_settings),
            MenuItem("退出", quit_app),
        ),
    )
    log_info(f"托盘图标已显示，开始监听热键 {combo}")
    icon.run()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log_err(f"主流程异常：{e}")
        sys.exit(1)

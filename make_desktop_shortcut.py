# -*- coding: utf-8 -*-
"""在桌面创建唯一快捷方式「剪思盒.lnk」，指向主程序 clipthink_sender.pyw（不带动作参数）。
双击仅拉起托盘主程序（若已运行则聚焦已存在的托盘）；阅读器 / 收件箱在托盘右键菜单里点。
（单程序模型：桌面只保留一个入口图标，不再有独立的阅读器快捷方式。）"""
import os
import sys

try:
    from win32com.shell import shell, shellcon
    import pythoncom
except ImportError:
    sys.exit("NEED_PYWIN32")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHONW = r"C:\Users\user\.workbuddy\binaries\python\envs\shortcut\Scripts\pythonw.exe"
SENDER = os.path.join(BASE_DIR, "clipthink_sender.pyw")
desktop = os.path.join(os.environ["USERPROFILE"], "Desktop")
lnk = os.path.join(desktop, "剪思盒.lnk")

# 若已存在旧快捷方式，先删除（Explorer 可能占用，不删直接 Save 会拒绝访问）
if os.path.exists(lnk):
    try:
        os.remove(lnk)
    except Exception as e:
        print("warn: 删除旧快捷方式失败，尝试直接覆盖:", e)

pythoncom.CoInitialize()
shortcut = pythoncom.CoCreateInstance(
    shell.CLSID_ShellLink,
    None,
    pythoncom.CLSCTX_INPROC_SERVER,
    shell.IID_IShellLink,
)
shortcut.SetPath(PYTHONW)
shortcut.SetArguments(f'"{SENDER}"')
shortcut.SetWorkingDirectory(BASE_DIR)
shortcut.SetDescription("剪思盒 ClipThink - 双击启动（阅读器/收件箱在托盘右键菜单）")
shortcut.SetIconLocation(r"C:\Windows\System32\imageres.dll", 109)
persist = shortcut.QueryInterface(pythoncom.IID_IPersistFile)
persist.Save(lnk, 0)
print("OK:" + lnk)

# -*- coding: utf-8 -*-
"""在桌面创建「剪思盒 阅读器」快捷方式，指向 clipthink_reader.pyw（用 pythonw 静默运行）。"""
import os
import pythoncom
from win32com.shell import shell, shellcon
from win32com.client import Dispatch

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHONW = os.path.join(os.path.dirname(os.path.dirname(sys.executable)), "pythonw.exe") \
    if False else r"C:\Users\user\.workbuddy\binaries\python\envs\shortcut\Scripts\pythonw.exe"
READER = os.path.join(BASE_DIR, "clipthink_reader.pyw")
desktop = shell.SHGetFolderPath(0, shellcon.CSIDL_DESKTOP, None, 0)
lnk = os.path.join(desktop, "剪思盒阅读器.lnk")

if os.path.exists(lnk):
    os.remove(lnk)

shell_link = Dispatch("WScript.Shell").CreateShortcut(lnk)
shell_link.TargetPath = PYTHONW
shell_link.Arguments = f'"{READER}"'
shell_link.WorkingDirectory = BASE_DIR
shell_link.Description = "剪思盒 ClipThink"
shell_link.IconLocation = PYTHONW + ",0"
shell_link.Save()
print("桌面快捷方式已创建:", lnk)
print("Target:", PYTHONW)
print("Args:", READER)

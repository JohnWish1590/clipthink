# -*- coding: utf-8 -*-
"""在桌面创建「剪思盒 阅读器」快捷方式，指向主程序 clipthink_sender.pyw 并带 --open-reader 参数。
双击即调起托盘主程序（若未运行则启动并显示托盘图标），由主程序以纯净应用窗口打开阅读器。
（单程序模型：阅读器与收件箱都通过主程序入口动作触发，不再各自独立启动。）"""
import os
import pythoncom
from win32com.shell import shell, shellcon
from win32com.client import Dispatch

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHONW = r"C:\Users\user\.workbuddy\binaries\python\envs\shortcut\Scripts\pythonw.exe"
SENDER = os.path.join(BASE_DIR, "clipthink_sender.pyw")
desktop = shell.SHGetFolderPath(0, shellcon.CSIDL_DESKTOP, None, 0)
lnk = os.path.join(desktop, "剪思盒阅读器.lnk")

if os.path.exists(lnk):
    try:
        os.remove(lnk)
    except Exception as e:
        print("warn: 删除旧快捷方式失败，尝试直接覆盖:", e)

shell_link = Dispatch("WScript.Shell").CreateShortcut(lnk)
shell_link.TargetPath = PYTHONW
shell_link.Arguments = f'"{SENDER}" --open-reader'
shell_link.WorkingDirectory = BASE_DIR
shell_link.Description = "剪思盒 阅读器 - 双击打开阅读器"
shell_link.IconLocation = PYTHONW + ",0"
shell_link.Save()
print("桌面快捷方式已创建:", lnk)
print("Target:", PYTHONW)
print("Args:", SENDER, "--open-reader")

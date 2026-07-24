import os
from win32com.shell import shell, shellcon
import pythoncom

# 真正画托盘图标、提供「打开阅读器 / 打开收件箱」菜单的发送端
PYTHONW = r"C:\Users\user\.workbuddy\binaries\python\envs\shortcut\Scripts\pythonw.exe"
SENDER = r"C:\Users\user\ClipThink\clipthink_sender.pyw"

startup = os.path.join(os.environ["APPDATA"], r"Microsoft\Windows\Start Menu\Programs\Startup")
os.makedirs(startup, exist_ok=True)
lnk = os.path.join(startup, "clipthink_sender.lnk")

pythoncom.CoInitialize()
shortcut = pythoncom.CoCreateInstance(
    shell.CLSID_ShellLink,
    None,
    pythoncom.CLSCTX_INPROC_SERVER,
    shell.IID_IShellLink,
)
shortcut.SetPath(PYTHONW)
shortcut.SetArguments('"%s"' % SENDER)
shortcut.SetWorkingDirectory(r"C:\Users\user\ClipThink")
shortcut.SetDescription("剪思盒发送端（开机自启）")
shortcut.SetIconLocation(r"C:\Windows\System32\imageres.dll", 109)
persist = shortcut.QueryInterface(pythoncom.IID_IPersistFile)
persist.Save(lnk, 0)
print("OK:" + lnk)

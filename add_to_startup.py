import os
from win32com.shell import shell, shellcon
import pythoncom

ahk = r"C:\Users\user\ClipThink\clipthink_sender.ahk"
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
shortcut.SetPath(ahk)
shortcut.SetWorkingDirectory(r"C:\Users\user\ClipThink")
shortcut.SetDescription("剪思盒发送热键（开机自启）")
shortcut.SetIconLocation(r"C:\Windows\System32\imageres.dll", 109)
persist = shortcut.QueryInterface(pythoncom.IID_IPersistFile)
persist.Save(lnk, 0)
print("OK:" + lnk)

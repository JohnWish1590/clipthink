import os
import sys

try:
    from win32com.shell import shell, shellcon
    import pythoncom
except ImportError:
    sys.exit("NEED_PYWIN32")

inbox = r"C:\Users\user\ClipThinkInbox"
desktop = os.path.join(os.environ["USERPROFILE"], "Desktop")
lnk = os.path.join(desktop, "剪思盒.lnk")

pythoncom.CoInitialize()
shortcut = pythoncom.CoCreateInstance(
    shell.CLSID_ShellLink,
    None,
    pythoncom.CLSCTX_INPROC_SERVER,
    shell.IID_IShellLink,
)
shortcut.SetPath(inbox)
shortcut.SetDescription("剪思盒 - 双击查看待分析内容")
shortcut.SetIconLocation(r"C:\Windows\System32\imageres.dll", 109)
persist = shortcut.QueryInterface(pythoncom.IID_IPersistFile)
persist.Save(lnk, 0)
print("OK:" + lnk)

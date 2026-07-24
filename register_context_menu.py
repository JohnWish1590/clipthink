import winreg
import os

USER = os.environ.get("USERNAME", "user")
SENDER_DIR = r"C:\Users\%s\ClipThink" % USER
SCRIPT = os.path.join(SENDER_DIR, "send_to_clipthink.ps1")

key_path = r"Software\Classes\*\shell\SendToWorkBuddy"

key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE)
winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "发送到 WorkBuddy 分析")
winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, r"C:\Windows\System32\imageres.dll,109")

sub = winreg.CreateKeyEx(key, "command", 0, winreg.KEY_WRITE)
cmd = 'powershell.exe -WindowStyle Hidden -ExecutionPolicy Bypass -File "%s" "%%1"' % SCRIPT
winreg.SetValueEx(sub, "", 0, winreg.REG_SZ, cmd)

winreg.CloseKey(sub)
winreg.CloseKey(key)

print("OK: context menu registered")
print("command =", cmd)

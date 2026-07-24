import winreg

key_path = r"Software\Classes\*\shell\SendToClipThink"

try:
    winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path + r"\command")
    winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
    print("右键菜单已删除")
except FileNotFoundError:
    print("右键菜单本就不存在")

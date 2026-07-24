#Requires AutoHotkey v2.0
#SingleInstance Force
#Persistent

; 收件箱发送脚本路径（按当前用户名自动拼接）
ScriptPath := "C:\Users\" . A_UserName . "\ClipThink\send_to_clipthink.ps1"

; 托盘图标菜单
A_TrayMenu.Delete()
A_TrayMenu.Add("发送剪贴板到 剪思盒", (*) => SendClip())
A_TrayMenu.Add()
A_TrayMenu.Add("退出", (*) => ExitApp())

; 全局热键：Alt + 4  →  把当前剪贴板（文字或图片）发到 剪思盒
; 想换别的键，把下面这行的 !4 改成其它组合即可，例如：
;   #!w   = Win+Alt+W      ^!s = Ctrl+Alt+S      !w = Alt+W
!4::SendClip()

SendClip() {
    global ScriptPath
    Run('powershell.exe -WindowStyle Hidden -ExecutionPolicy Bypass -File "' ScriptPath '"')
    TrayTip("已发送到 剪思盒", "剪思盒 会自动开一个分析任务", 2)
}

' 启动 剪思盒 热键监听器（无黑窗口）
' 目标：Alt+4 触发复制内容到 剪思盒

Set WshShell = CreateObject("WScript.Shell")
WshShell.Run """C:\Users\user\.workbuddy\binaries\python\envs\shortcut\Scripts\pythonw.exe"" ""C:\Users\user\ClipThink\clipthink_sender.pyw""", 0, False
Set WshShell = Nothing

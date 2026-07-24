# 更新日志 / Changelog

本文件记录本项目的所有 **notable changes**（值得注意的变更）。

- 格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 规范。
- 版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)（SemVer）。
- 日期统一使用 ISO 8601 格式：`YYYY-MM-DD`。

---

## Release Notes（v1.0.2）

> 本小节为 GitHub Release **v1.0.2** 的正文，供发布时直接引用。

**剪思盒 ClipThink** v1.0.2 主要是 v1.0.1 品牌重命名的收尾补丁。

**本次更新**
- 右键上下文菜单（资源管理器对文件右键「发送到…」）注册表键 `SendToWorkBuddy` → `SendToClipThink`，显示文案改为「发送到 剪思盒 分析」。
- 同步更新卸载脚本键名，确保旧键可被正确移除、无残留。
- 清理 `clipthink_sender.ahk` / `clipthink_sender.vbs` 及 `make_reader_shortcut.py` 内的旧品牌注释。

**已验证**：本机重注册后新键生效、旧键消失；三个 Python 脚本 `py_compile` 通过。

**如何安装**：见仓库 README 的「部署与安装」章节。若已安装 v1.0.1，直接拉取最新代码并重新运行 `register_context_menu.py` 即可刷新右键菜单。

---

## Release Notes（v1.0.3）

> 本小节为 GitHub Release **v1.0.3** 的正文，供发布时直接引用。

**剪思盒 ClipThink** v1.0.3 修复「托盘图标不显示 / 点击桌面快捷方式无反应」的问题。

**本次更新**
- 修复开机自启指向错误：启动文件夹的 `clipthink_sender.lnk` 原先指向废弃的 `clipthink_sender.ahk`（仅含 Alt+4 热键，不会拉起带托盘菜单的发送端），现已改为直接以 `pythonw` 启动 `clipthink_sender.pyw`，开机后托盘图标与「打开阅读器 / 打开收件箱」菜单正常可用。
- 设置系统注册表 `TrayNotify\PromotedIcon1`，让托盘图标在通知区**常驻显示**，不再被 Windows 折叠进溢出区。

**已验证**：本机重启发送端后日志显示「托盘图标已显示」；自启快捷方式目标已确认指向 `clipthink_sender.pyw`；注册表项已生效。

**如何安装**：已安装的用户 `git pull` 后重新运行 `add_to_startup.py` 即可刷新自启项；托盘图标默认常驻，若仍在溢出区点击「^」即可看到。

---

## Release Notes（v1.0.4）

> 本小节为 GitHub Release **v1.0.4** 的正文，供发布时直接引用。

**剪思盒 ClipThink** v1.0.4 把「阅读器」与「收件箱」合并为单一托盘程序，并让阅读器以纯净应用窗口打开。

**本次更新**
- 单程序模型：桌面「剪思盒 / 剪思盒阅读器」两个快捷方式现在都带动作参数启动同一个托盘主程序 `clipthink_sender.pyw`。无论点哪个，托盘图标都会调出（已运行时由运行实例接管动作），状态一目了然。
- 阅读器纯净应用窗口：自动探测默认浏览器，Chrome / Edge 用 `--app=<url>` 打开无地址栏、无标签栏的独立窗口；其它浏览器降级为 `--new-window`；探测失败回退系统默认打开。不再塞进现有浏览器标签页。

**已验证**：三个脚本 `py_compile` 通过；桌面快捷方式目标已确认指向主程序并带正确参数；本机默认浏览器探测为 Chrome，`--app` 纯净窗口路径生效。

**如何安装**：已安装用户 `git pull` 后重新运行 `make_desktop_shortcut.py` 与 `make_reader_shortcut.py` 刷新桌面快捷方式即可；托盘图标逻辑不变。

---

## Release Notes（v1.0.5）

> 本小节为 GitHub Release **v1.0.5** 的正文，供发布时直接引用。

**剪思盒 ClipThink** v1.0.5 把桌面快捷方式合并为**唯一一个**「剪思盒」图标。

**本次更新**
- 桌面只保留一个快捷方式「剪思盒.lnk」，双击仅拉起托盘主程序（不再带 `--open-inbox` 之类的动作参数）；阅读器 / 收件箱改在托盘右键菜单里点。
- 删除独立的「剪思盒阅读器.lnk」及其生成脚本 `make_reader_shortcut.py`，合并为单一入口，桌面不再有两个图标。

**已验证**：三个脚本 `py_compile` 通过；桌面确认仅剩 `剪思盒.lnk` 一个 ClipThink 图标，目标为 `pythonw ...\clipthink_sender.pyw`（无动作参数）。

**如何安装**：已安装用户 `git pull` 后手动删除桌面旧的「剪思盒阅读器.lnk」，并重新运行 `make_desktop_shortcut.py` 刷新「剪思盒.lnk」即可；托盘图标逻辑不变。

---

## Release Notes（v1.0.6）

> 本小节为 GitHub Release **v1.0.6** 的正文，供发布时直接引用。

**剪思盒 ClipThink** v1.0.6 聚焦阅读器体验与桌面入口统一：双击桌面图标同时打开托盘 + 半屏贴边阅读器，托盘退出时可选择一起关闭阅读器，并换上用户设计的「CT」桌面图标。

**本次更新**
- 桌面快捷方式「剪思盒.lnk」改回带 `--open-reader` 参数：双击同时启动托盘主程序并打开阅读器，阅读器以 Chrome / Edge 纯净应用窗口占主屏幕 50% 宽度、100% 高度贴左/右显示。
- 首次打开阅读器时询问默认放在屏幕「左侧」还是「右侧」，选择后保存到 `clipthink.json`，后续按偏好自动贴边；托盘右键「设置」可随时修改。
- 托盘右键「退出」首次弹出确认：「是否同时关闭阅读器？」，默认勾选「记住我的选择」，后续直接按偏好执行。
- 阅读器列表卡片优化：删除按钮不再与时间重叠；时间字段由「分析时间」改为「发送/入箱时间」（读取文件名中的 `YYYYMMDD_HHMMSS` 时间戳）。
- 新增 `clipthink.ico` 桌面图标（多尺寸 16/32/48/64/128/256），风格为用户提供的「CT」铜线工艺图标；桌面快捷方式已指向新图标。

**已验证**：`clipthink_sender.pyw`、`clipthink_reader.pyw`、`make_desktop_shortcut.py` 三个脚本 `py_compile` 通过；桌面快捷方式目标已确认带 `--open-reader` 并指向 `clipthink.ico`。

**如何安装**：已安装用户 `git pull` 后重新运行 `make_desktop_shortcut.py` 刷新桌面快捷方式与图标即可；首次退出托盘与首次打开阅读器时会分别弹出偏好询问。

---

## Release Notes（v1.0.7）

> 本小节为 GitHub Release **v1.0.7** 的正文，供发布时直接引用。

**剪思盒 ClipThink** v1.0.7 修复阅读器窗口未真正顶格、选择对话框图标不统一、左右选项同时被选中的问题，并按用户提供的代码重新生成更清晰的「CT」矢量风格图标。

**本次更新**
- 阅读器窗口真正「顶格」：启动 Chrome / Edge 应用窗口后，通过 Windows API `FindWindowW` + `SetWindowPos` 按主显示器**工作区**（已扣除任务栏）精确贴边，左/右半屏各占 50% 宽度、100% 工作区高度，不再受浏览器边框影响。
- 修复选择对话框默认状态：首次询问阅读器位置时，单选按钮默认选中「右侧」，不再出现左右两个按钮同时被选中的视觉 bug。
- 图标全面统一：系统托盘图标、桌面快捷方式图标、阅读器网页 favicon、所有 tkinter 对话框图标，全部指向同一个 `clipthink.ico`。
- 重新生成桌面图标：按用户提供的裁剪/去背代码，从原始「CT」设计图生成带透明背景的多尺寸 ICO（16/32/48/64/128/256），桌面显示更清晰。

**已验证**：`clipthink_sender.pyw`、`clipthink_reader.pyw`、`make_desktop_shortcut.py` 三个脚本 `py_compile` 通过；桌面快捷方式目标已确认带 `--open-reader` 并指向新生成的 `clipthink.ico`。

**如何安装**：已安装用户 `git pull` 后重新运行 `make_desktop_shortcut.py` 刷新桌面快捷方式与图标即可；托盘发送端需要退出重开才能加载新图标与窗口贴边逻辑。

---

## Release Notes（v1.0.8）

> 本小节为 GitHub Release **v1.0.8** 的正文，供发布时直接引用。

**剪思盒 ClipThink** v1.0.8 进一步净化桌面图标，并修复首次退出确认对话框仍显示默认图标的问题。

**本次更新**
- 重新生成 `clipthink.ico` / `clipthink_icon.png`：只保留棕色 CT 线条本身，去掉原始截图中的白色圆角矩形底板与外围阴影，让桌面图标更紧凑、更贴近「铜线工艺」原设计。
- 修复 tkinter 对话框图标加载：新增 `_set_window_icon()` 统一封装 `iconbitmap` / `wm_iconbitmap` / `iconphoto` 三种回退方式，确保首次退出托盘时「是否同时关闭阅读器？」确认框正确显示剪思盒图标，不再回退到默认 feather 图标。

**已验证**：`clipthink_sender.pyw`、`clipthink_reader.pyw`、`make_desktop_shortcut.py` 三个脚本 `py_compile` 通过；桌面快捷方式目标已确认指向 `clipthink.ico`。

**如何安装**：已安装用户 `git pull` 后重新运行 `make_desktop_shortcut.py` 刷新桌面图标；托盘发送端需要退出重开才能加载新图标与对话框图标逻辑。

---

## [Unreleased]

## [1.0.8] - 2026-07-24

### Changed
- 重新生成 `clipthink.ico` / `clipthink_icon.png`：仅保留棕色 CT 线条，去除白色圆角底板与阴影。

### Fixed
- 首次退出托盘时的确认对话框可能仍显示默认 feather 图标；现通过 `_set_window_icon()` 多方式回退加载 `clipthink.ico`，确保剪思盒图标生效。

## [1.0.7] - 2026-07-24

### Fixed
- 阅读器窗口未真正顶格：改用 `SystemParametersInfo(SPI_GETWORKAREA)` 获取工作区，启动后用 `SetWindowPos` 把阅读器精确贴到左/右半屏。
- 首次询问阅读器位置时，单选按钮默认同时选中的视觉 bug；现在默认选中「右侧」。
- 系统托盘图标与 tkinter 对话框图标不统一；两者均使用 `clipthink.ico`。

### Changed
- 按用户提供的代码重新生成 `clipthink.ico` 与 `clipthink_icon.png`，去除白底、保留圆角卡片，尺寸更清晰。
- `reader.html` 新增 `<link rel="icon" href="/clipthink.ico">`，阅读器窗口/tab 也显示统一图标。
- `clipthink_reader.pyw` 增加 `/clipthink.ico` 路由，为阅读器页面提供 favicon。

## [1.0.6] - 2026-07-24

### Added
- 阅读器半屏贴边：Chrome / Edge 用 `--app=<url> --window-size=<w>,<h> --window-position=<x>,<y>` 打开占主屏幕 50% 宽、100% 高的纯净应用窗口。
- 首次打开阅读器时询问屏幕左侧/右侧偏好，保存到 `clipthink.json`；托盘菜单新增「设置」可修改偏好。
- 托盘「退出」首次询问是否同时关闭阅读器，保存偏好后后续直接执行。
- 新增 `clipthink.ico` 多尺寸桌面图标。

### Changed
- 桌面快捷方式「剪思盒.lnk」改为带 `--open-reader` 参数，双击同时打开托盘与阅读器。
- 阅读器列表卡片删除按钮移入标题行，不再与时间重叠。
- 阅读器列表时间由文件 `mtime` 改为文件名中的发送时间戳（`YYYYMMDD_HHMMSS`）。

## [1.0.5] - 2026-07-24

### Changed
- 桌面只保留一个快捷方式「剪思盒.lnk」，双击仅拉起托盘主程序（不带动作参数）；阅读器 / 收件箱改在托盘右键菜单里点。
- 删除独立的「剪思盒阅读器.lnk」及生成脚本 `make_reader_shortcut.py`，合并为单一入口。

### Notes
- `clipthink_sender.pyw` 的 `--open-reader` / `--open-inbox` 参数与命令文件 IPC 机制保留（供脚本或后续调用），桌面快捷方式不再使用。

## [1.0.4] - 2026-07-24

### Added
- 单程序模型：桌面快捷方式带 `--open-inbox` / `--open-reader` 参数启动同一托盘主程序；主程序已运行时重复实例通过命令文件 `.sender.cmd` 把动作转交给运行实例，保证托盘唯一且始终可见。
- 阅读器纯净应用窗口：探测默认浏览器，Chrome / Edge 用 `--app=<url>`（无地址栏/标签栏），其它浏览器降级 `--new-window`，失败回退系统默认打开。

### Changed
- `make_desktop_shortcut.py` / `make_reader_shortcut.py` 改为生成指向主程序并带动作参数的快捷方式。

## [1.0.3] - 2026-07-24

### Fixed
- 修复开机自启指向错误：`clipthink_sender.lnk` 由废弃的 `clipthink_sender.ahk` 改为直接启动 `clipthink_sender.pyw`，开机后托盘菜单（打开阅读器 / 打开收件箱）正常可用。

### Added
- 设置 `TrayNotify\PromotedIcon1` 注册表，使托盘图标在通知区常驻显示，不再被折叠进溢出区。

---

## [1.0.2] - 2026-07-23

### Fixed
- 右键上下文菜单注册表键 `SendToWorkBuddy` → `SendToClipThink`，显示文案「发送到 剪思盒 分析」（用户可见旧品牌收尾）。
- 卸载脚本键名同步，确保旧键可正确卸载、无残留。

### Changed
- 清理 `clipthink_sender.ahk` / `clipthink_sender.vbs` / `make_reader_shortcut.py` 内残留的旧品牌注释。

---

## Release Notes（v1.0.1）

> 本小节为 GitHub Release **v1.0.1** 的正文，供发布时直接引用。

**剪思盒 ClipThink** —— 一个常驻 Windows 系统托盘的剪贴板工具：一键把剪贴板里的文字 / 图片发到收件箱，由 WorkBuddy 自带的 AI 自动分析，并提供本地阅读器随时回看「原文 + 结论」、继续追问。

**本次更新**
- 产品正式更名为 **剪思盒 ClipThink**，统一托盘、阅读器与文档中的旧名；主程序重命名为 `clipthink_sender.pyw` / `clipthink_reader.pyw`，收件箱目录 `WorkBuddyInbox` → `ClipThinkInbox`。
- 修复托盘「打开阅读器」无响应的问题：消除浏览器在 HTTP 服务就绪前就连接的竞态，改用 `os.startfile` 打开默认浏览器，失败时给出可见提示。

**如何安装**：见仓库 README 的「部署与安装」章节（前置依赖与快速开始 3 步）。

**许可证**：本仓库为公开仓库，免费供个人使用（仅供个人学习与非商业用途）。

---

## [Unreleased]

## [1.0.1] - 2026-07-23

### Changed
- 产品更名为「剪思盒 ClipThink」；统一托盘、阅读器与文档中的旧名。
- 主程序重命名：`WorkBuddySender.pyw` → `clipthink_sender.pyw`、`WorkBuddyReader.pyw` → `clipthink_reader.pyw`。
- 收件箱目录 `WorkBuddyInbox` → `ClipThinkInbox`。

### Fixed
- 修复托盘「打开阅读器」无响应：消除浏览器在 HTTP 服务就绪前连接的竞态，改用 `os.startfile` 打开默认浏览器；失败时给出可见提示。

### Added
- README 新增「部署与安装」章节（前置依赖与快速开始）。

## [1.0.0] - 2026-07-22

### Added
- 初始发布。
- 全局热键发送剪贴板到收件箱。
- 每小时自动分析（亦可托盘右键即时触发）。
- 本地阅读器回看「原文 + 分析结果」。
- 继续讨论（追问）。
- 自定义热键。
- 单实例防多开。

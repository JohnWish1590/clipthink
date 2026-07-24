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

## [Unreleased]

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

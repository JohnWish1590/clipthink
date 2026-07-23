# 剪思盒 ClipThink（WorkBuddy 收件箱）功能说明

> 一份面向"会用电脑但不一定懂开发"的用户的功能说明文档。所有内容均以当前代码（`WorkBuddySender.pyw` / `WorkBuddyReader.pyw` / `reader.html`）为准。

---

## 一、项目概述

**一句话定位**：WorkBuddy 收件箱是一个常驻 Windows 系统托盘的小工具，让你用「一键全局热键」把剪贴板里的**文字或图片**快速发到 WorkBuddy，由 AI 自动做结构化分析，并提供一个本地网页阅读器随时回看「原文 + 分析结果」。

- **适用人群**：在微信 / 网页 / 研报里频繁看到值得深读的内容（尤其是金融投研场景），想"先收藏、后分析"、又不想反复手动粘贴到对话框的用户。
- **它能解决什么**：
  1. **收集快**：复制即按热键，0 延迟落盘，不打断当前操作。
  2. **分析自动**：每小时自动分析一次；也能在托盘右键即时触发。
  3. **回看方便**：本地阅读器左右两栏展示「你发的内容」和「AI 的分析结论」，支持继续追问。
  4. **后台干净**：无黑窗口、常驻托盘、单实例防多开、运行日志可查。

> 白话解释：它相当于给你的 WorkBuddy 装了一个"收件箱 + 自动分析师"。你只管往里丢素材，它定时帮你读、帮你分析，你随时来翻。

---

## 二、核心功能清单

| 功能点 | 说明 | 触发方式 |
|---|---|---|
| **全局热键发送剪贴板** | 按热键把当前剪贴板（文字或图片）写入收件箱。图片优先，其次文字。带去重，避免重复发同一条。 | 全局热键（默认 `ALT+4`，可自定义） |
| **托盘右键「立即执行」** | 等同热键，手动触发一次"发送当前剪贴板"。 | 系统托盘 → 右键菜单 |
| **托盘右键「分析收件箱」** | 立即让 WorkBuddy 分析收件箱里所有"未分析"的条目，分析完成后弹提示。 | 系统托盘 → 右键菜单 |
| **每小时自动分析** | 后台定时器每小时跑一次；仅当存在"未分析"条目时才真正提交，静默不弹窗。 | 自动（无需操作） |
| **系统托盘常驻** | 蓝紫渐变"对话气泡"图标常驻右下角，悬停显示「WorkBuddy 收件箱 - 运行中 (当前热键)」。 | 启动即常驻 |
| **鼠标旁轻量提示（toast）** | 发送成功/失败、分析完成等，在鼠标旁弹"已发送/分析完成"小卡片（绿=成功，红=失败），约 0.6–2.2 秒自动消失。 | 自动（随动作触发） |
| **本地网页阅读器** | 左右两栏：左=条目列表（是否已分析），右=原文 + 分析结果；支持 Markdown / 图片渲染、自动刷新。 | 托盘「打开阅读器」/ 浏览器访问 8765 |
| **继续讨论（追问）** | 在阅读器里针对某条写下问题 → 自动把"原文+之前分析+你的问题"写入收件箱并复制到剪贴板，再触发分析即可看到回复。 | 阅读器内「发到 WorkBuddy 讨论」 |
| **一键复制全文** | 把"原文 + 分析结果"复制进剪贴板，方便直接粘贴给 WorkBuddy。 | 阅读器内「复制全文」 |
| **清空 / 删除** | 可清空整个收件箱，或删除单条（连同关联图片）。均有二次确认。 | 阅读器内按钮 |
| **自定义全局热键** | 在阅读器「设置」里按下组合键即保存，或编辑 `hotkey.json`；发送端自动热重载，无需重启。 | 阅读器「设置」/ 编辑文件 |
| **单实例防多开** | 用原子锁文件保证同时只跑一个发送端、一个阅读器；重复启动自动退出，僵尸锁自动接管。 | 自动 |

---

## 三、系统架构

### 3.1 文件 / 模块职责

| 文件 / 模块 | 职责 |
|---|---|
| `WorkBuddySender.pyw`（主程序，发送端） | 全局热键监听（Windows 原生 `RegisterHotKey`）、系统托盘、剪贴板发送逻辑（`send_clipboard_direct`）、去重、轻量 toast、分析 serve 的拉起与提交（`ensure_serve` / `_submit_analysis` / `_watch_run`）、每小时定时分析（`_hourly_timer` / `auto_analyze`）、单实例锁（`.sender.lock`）、写 `log.txt`。 |
| `WorkBuddyReader.pyw`（阅读器后端） | 纯后台本地 HTTP 服务（端口 **8765**），无托盘。提供列表/条目/图片/热键读写/讨论/清空/删除等 API，读收件箱 `.md` / `.md.done` 并拆分"原文"与"分析结果"。单实例锁（`.reader.lock`）。 |
| `reader.html`（阅读器前端） | 本地网页界面（左右两栏 + 设置面板），通过 `fetch` 调用阅读器后端 API，渲染 Markdown、处理讨论/复制/清空/删除/自定义热键交互。 |
| `hotkey.json` | 当前热键组合配置（`{"combo": "ALT+4"}`），发送端与阅读器共用；改文件或阅读器保存即生效。 |
| `log.txt` | 发送端运行日志（启动、热键触发、发送成败、分析服务状态等），排查第一手资料。 |
| `send_clipboard.py` | **旧版备用发送脚本**，当前主流程已把发送逻辑内嵌到 `WorkBuddySender.pyw`，此文件不再被主流程调用，仅作备份保留。 |
| `send_to_workbuddy.ps1` | **旧版 PowerShell 发送脚本**，已被内嵌逻辑取代，不再被主流程使用。 |
| `register_context_menu.py` / `unregister_context_menu.py` | 用于在资源管理器右键菜单注册/卸载「发送到 WorkBuddy 分析」（文件级发送入口，独立于热键）。 |
| 其它 `*.py`（如 `add_to_startup.py`、`make_*_shortcut.py`、`fix_*.py`、`test_*.py`、`clean_inbox.py`、`update_all_shortcuts.py`） | 辅助/运维脚本：开机自启、生成桌面快捷方式、历史修复与自检。**正常使用无需关心**，详见第六节。 |

### 3.2 模块依赖与数据流（Mermaid）

```mermaid
flowchart LR
    subgraph 发送链路
        CLIP[剪贴板：文字 / 图片]
        HK[全局热键 ALT+4<br/>或 托盘"立即执行"]
        SEND[send_clipboard_direct]
        DEDUP{与最近内容<br/>重复?}
        INBOX[(收件箱<br/>WorkBuddyInbox)]
        CLIP --> HK --> SEND --> DEDUP
        DEDUP -- 否 --> INBOX
        DEDUP -- 是 --> TOAST1[弹"已发送过<br/>不重复"]
    end

    subgraph 分析链路
        TRAY[托盘"分析收件箱"<br/>或 每小时定时器]
        SERVE[ensure_serve<br/>node codebuddy --serve :8090]
        SUBMIT[POST /api/v1/runs<br/>X-Codebuddy-Run-Timeout: 180000]
        AGENT[codebuddy agent 遍历 .md]
        DONE[(同名 .md.done<br/>含 ## 分析结果)]
        TRAY --> SERVE --> SUBMIT --> AGENT
        INBOX -. 遍历未分析 .md .-> AGENT
        AGENT --> DONE
        DONE --> TOAST2[弹"分析完成"]
    end

    subgraph 阅读链路
        READER[WorkBuddyReader :8765]
        UI[reader.html 左右两栏]
        DONE --> READER --> UI
        UI -. 讨论/复制/清空/删除 .-> INBOX
    end
```

**一句话串起来**：你按热键 → 内容进收件箱 →（每小时 / 手动）WorkBuddy 把分析写进 `.md.done` → 本地阅读器读 `.done` 展示 → 你在阅读器里继续追问，又写回收件箱，形成闭环。

---

## 四、使用说明

### 4.1 安装 / 前置条件

- **必须**：已在本机安装 **WorkBuddy 桌面端**（分析能力依赖它自带的 `codebuddy` CLI，路径 `C:\Program Files\WorkBuddy\resources\app.asar.unpacked\cli\bin\codebuddy`）。
- **必须**：本机有 **Node.js**（发送端用 `node` 拉起 `codebuddy` 分析服务；程序会自动在 `PATH` 或 `C:\Program Files\nodejs\node.exe` 等位置查找）。
- **必须**：Python 运行环境（含 `pystray`、`Pillow`、`tkinter`；`tkinter` 为标准库）。发送端以 `pythonw.exe` 后台运行，无控制台窗口。
- 收件箱目录 `C:\Users\user\WorkBuddyInbox` 会在首次发送时自动创建。

### 4.2 启动方式

- **推荐**：双击 `WorkBuddySender.pyw`（或桌面「启动 WorkBuddy 收件箱」快捷方式）。
- 启动后：
  - 右下角系统托盘出现**蓝紫渐变对话气泡**图标；
  - 后台自动拉起分析服务（本地 8090）并启动每小时分析定时器；
  - 无任何黑窗口，常驻后台。
- 可选开机自启：运行 `add_to_startup.py` 可把发送端加入开机自启（具体是否当前已启用，取决于此前是否运行过）。

### 4.3 全局热键怎么用

1. 在微信 / 网页里 `Ctrl+C` 复制一段**文字**或一张**图片**；
2. 直接按 **`ALT+4`**（默认，可在阅读器「设置」里改）；
3. 鼠标旁闪现**绿色「已发送」**小卡片（约 0.6 秒消失）即成功；
4. 内容写入收件箱：文字 → `YYYYMMDD_HHMMSS.md`；图片 → 同名的 `.png` + 引用它的 `.md`。

> 小贴士：在微信 / 浏览器里"选中文字 → 右键"弹出的是应用自己的菜单，Windows 系统右键抓不到那段选中文字；所以**纯文字最顺手的做法是"复制后按热键"**。文件级发送可用资源管理器右键菜单「发送到 WorkBuddy 分析」（`register_context_menu.py` 注册）。

### 4.4 托盘菜单每一项说明

右键托盘气泡图标，菜单如下：

| 菜单项 | 作用 |
|---|---|
| **立即执行（发送当前剪贴板）** | 等同于按一次热键，把当前剪贴板内容发到收件箱。 |
| **分析收件箱** | 立即触发一次 WorkBuddy 分析（遍历未分析条目 → 写 `.md.done`），完成后弹"分析完成，可在阅读器查看"。若分析服务不可用则弹"分析服务不可用"。 |
| **打开运行日志** | 用默认程序打开 `log.txt`，排查问题用。 |
| **打开收件箱** | 打开资源管理器定位到 `C:\Users\user\WorkBuddyInbox`。 |
| **打开阅读器** | 启动阅读器后端（若未运行）并打开浏览器访问 `http://127.0.0.1:8765/`。 |
| **退出** | 关闭发送端（托盘图标消失，停止热键与分析定时器）。 |

### 4.5 阅读器用法

**打开方式**（任选其一）：
1. 托盘菜单 → **打开阅读器**；
2. 浏览器直接访问 `http://127.0.0.1:8765/`；
3. 双击桌面「WorkBuddy 阅读器」快捷方式（若存在）。

**界面说明**：
- 顶部提示：`每小时自动分析 · 右键托盘"分析收件箱"可即时触发`。
- **左栏（列表）**：每条一个卡片，带绿色（已分析）/ 灰色（未分析）圆点、`文字/图片` 标签、时间、内容摘要。点卡片在右栏查看；卡片右上「×」可删除该条（连同关联图片）。
- **右栏**：上方「你发送的内容」，下方「分析结果」。
  - 未分析时，分析区显示：`尚未分析。右键托盘点"分析收件箱"即可即时分析，或等每小时自动分析。`
  - 已分析时，显示 `## 分析结果` 内容（金融投研视角的中文结构化分析，≤250 字）。
- **继续讨论框**（文字条目，或已分析的图片条目会出现）：提示文案为
  > 想就这条跟 WorkBuddy 进一步聊？写下你的问题，点「发到 WorkBuddy 讨论」：会自动把原文+分析结果+你的问题复制进剪贴板，并写入收件箱；右键托盘点"分析收件箱"即可看到回复。

  点「**发到 WorkBuddy 讨论**」后：把"原文 + 之前分析 + 你的问题"写入收件箱（生成 `{时间戳}_discuss.md`）并复制到剪贴板，弹提示"已复制并写入收件箱，右键托盘点'分析收件箱'即可继续"。随后再触发分析即可看到针对你问题的回复。
- **复制全文**：把"原文 + 分析结果"复制进剪贴板。
- **刷新**：手动刷新列表与当前条目。
- **清空收件箱**：清空整个收件箱（带二次确认，不可撤销）。
- **设置**：见 4.6。
- 列表每 **5 秒**自动刷新；仅当某条"未分析→已分析"状态翻转时才重渲染，避免冲掉你正在写的讨论内容。
- 所有交互的轻提示（toast）从界面底部居中弹出，约 2.6 秒消失。

### 4.6 如何自定义热键

**方式 A（推荐，在阅读器里设）**：
1. 打开阅读器 → 点右上角「**设置**」；
2. 在弹出框里**点击输入框，然后直接按下**你想用的组合键（如 `Ctrl+Alt+4`、`F9`、`Alt+Shift+K`）；
3. 若没带修饰键（Ctrl/Alt/Shift/Win），框下会提示"会拦截正常输入，建议加修饰键"；
4. 点「保存」→ 提示"已保存：XXX（发送端运行即生效）"。发送端会**自动热重载**，无需重启。

**方式 B（直接编辑文件）**：
编辑 `WorkBuddySender\hotkey.json`，格式示例：

```json
{ "combo": "ALT+4" }
```

其它合法写法：`"CTRL+ALT+4"`、`"F9"`、`"ALT+SHIFT+K"`、`"WIN+Q"`。保存后发送端监测到文件变化即自动重新注册热键。

> 说明：`hotkey.json` 由发送端与阅读器共用。当前磁盘上的 `hotkey.json` 内容为 `ALT+Q`（即本机实际生效的是 `ALT+Q`）；代码内置默认值是 `ALT+4`，但**文件内容优先于默认值**。

---

## 五、配置项

| 配置项 | 位置（代码常量 / 文件） | 含义 | 是否可调 |
|---|---|---|---|
| `DEFAULT_HOTKEY` | `WorkBuddySender.pyw` | 热键默认值 `ALT+4`；仅当 `hotkey.json` 不存在/为空时生效。 | 改文件 `hotkey.json` 即可覆盖（推荐）。 |
| `HOTKEY_FILE` | `WorkBuddySender.pyw` | 热键配置文件 `hotkey.json`，发送端与阅读器共用。 | — |
| `INBOX` | `WorkBuddySender.pyw` / `WorkBuddyReader.pyw` | 收件箱目录 `C:\Users\user\WorkBuddyInbox`。 | 改代码常量（两处需一致）。 |
| `ANALYSIS_PORT` | `WorkBuddySender.pyw` | 分析服务（codebuddy serve）监听端口 **8090**。 | 改代码常量（需同步保证端口空闲）。 |
| `SERVE_SESSION` / `ANALYSIS_SESSION_ID` | `WorkBuddySender.pyw` | 分析会话标识，统一为 `inbox-analysis`（serve 实例与提交任务用同一会话）。 | 一般无需改。 |
| `ANALYSIS_RUN_TIMEOUT` | `WorkBuddySender.pyw` | 单次分析超时（秒），默认 **180**。注意：发送给 serve 的 `X-Codebuddy-Run-Timeout` 头以**毫秒**为单位，代码发送时自动 `×1000` → `180000` 毫秒。 | 可调（改后自动 `×1000`）。 |
| `CODEBUDDY_CLI` | `WorkBuddySender.pyw` | `codebuddy` CLI 路径（WorkBuddy 桌面端自带）。 | 若安装路径不同需改。 |
| `ANALYSIS_PROMPT` | `WorkBuddySender.pyw` | 分析提示词：要求 agent 遍历收件箱 `.md`（非 `.done`），用中文（金融投研视角，≤250 字）做结构化分析，在原文末尾追加 `## 分析结果`，写同名 `.md.done`（UTF-8 带 BOM），不删原文件、不创建其它文件。 | 高级用户可微调话术。 |
| `LOG_FILE` | `WorkBuddySender.pyw` | 运行日志 `log.txt` 路径。 | — |
| 阅读器端口 `PORT` | `WorkBuddyReader.pyw` | 阅读器 HTTP 服务端口 **8765**。 | 改代码常量。 |
| 分析仪环境变量 | `ensure_serve()` 内 | `CODEBUDDY_GATEWAY_AUTH=none`、`CODEBUDDY_DISABLE_REQUEST_VALIDATION=1`（本地无鉴权拉起 serve）。 | 一般无需改。 |

---

## 六、目录与文件清单（WorkBuddySender 目录）

> 日常使用只需关心前 6 个；其余为历史修复 / 运维脚本，可不动。

**核心文件**
- `WorkBuddySender.pyw` — 发送端主程序（热键 + 托盘 + 发送 + 分析调度 + 单实例锁 + 日志）。
- `WorkBuddyReader.pyw` — 阅读器后端（本地 HTTP 服务，端口 8765，无托盘）。
- `reader.html` — 阅读器前端界面。
- `hotkey.json` — 当前热键组合配置。
- `log.txt` — 发送端运行日志。
- `.sender.lock` / `.reader.lock` — 单实例原子锁文件（程序自动管理，勿手动删除）。

**旧版 / 备用脚本（非主流程）**
- `send_clipboard.py` — 旧版独立发送脚本，已被内嵌逻辑取代，仅备份。
- `send_to_workbuddy.ps1` — 旧版 PowerShell 发送脚本，已不再被主流程使用。
- `WorkBuddySender.ahk` / `WorkBuddySender.bat` / `WorkBuddySender.vbs` — 早期启动器，已废弃，请用 `.pyw` 直接启动。

**辅助 / 运维脚本（可选）**
- `add_to_startup.py` — 配置开机自启。
- `make_reader_shortcut.py` / `make_desktop_*.py` / `fix_desktop_lnk*.py` — 生成 / 修复桌面与阅读器快捷方式。
- `register_context_menu.py` / `unregister_context_menu.py` — 注册 / 卸载资源管理器右键菜单「发送到 WorkBuddy 分析」。
- `fix_*.py`、`update_all_shortcuts.py`、`clean_inbox.py`、`fix_encoding.py` — 历史修复与清理脚本。
- `test_send.py` / `test_reader_api.py` — 自检脚本。

**收件箱（独立目录）**
- `C:\Users\user\WorkBuddyInbox\` — 存放 `.md`（待分析/原文）、`.md.done`（已分析，含 `## 分析结果`）、`.png`/`.jpg`（图片）等。

---

## 七、已知限制与排查

### 7.1 分析与"未分析"在列表里可能显示两条
分析完成后，程序**保留原 `.md` 不动，另写一份同名 `.md.done`**（而非重命名）。阅读器按文件列出，因此同一条内容在左栏会出现两个卡片：原 `.md`（灰点"未分析"）和 `.md.done`（绿点"已分析"，含结论）。这是当前实现行为——看分析结论请点带绿点的那条。

### 7.2 端口 8090 被旧 serve 占用
若分析一直失败或弹"分析服务不可用"，可能是上次的分析服务（node serve）残留占着 8090：
- 查看 `log.txt` 是否有 `未找到 node` / `启动分析 serve 失败` 之类记录；
- 确认 8090 空闲：可用 `netstat -ano | findstr 8090` 查占用进程并结束；
- 正常情况发送端每次启动会先检测 8090 是否已监听，已监听则复用、不重复拉起。
- 若 `codebuddy` CLI 路径不对或 Node 未安装，`ensure_serve()` 会失败并记日志，分析功能不可用。

### 7.3 分析服务不存在 / node 找不到
- 日志关键字：`未找到 node，无法启动分析 serve`、`未找到 codebuddy CLI：...`。
- 排查：确认已安装 WorkBuddy 桌面端（提供 `codebuddy`）与 Node.js（加入 `PATH` 或位于 `C:\Program Files\nodejs\node.exe`）。程序用 `node` 拉起 `codebuddy`，**不能直接跑裸 `codebuddy`**（Windows 会报 WinError 193）。

### 7.4 分析超时（任务被秒杀）
- 单次分析超时由 `ANALYSIS_RUN_TIMEOUT`（秒）×1000 决定，作为 `X-Codebuddy-Run-Timeout` 头（毫秒）发送。若条目过多或分析很长，可适当调大该常量（改后自动换算为毫秒）。
- 若提交后 0.1 秒就被 `EXECUTION_ERROR: Task timed out` 杀死，通常是超时头未生效——当前代码已按 serve 要求写为小写 `b` 的 `X-Codebuddy-Run-Timeout` 并 `×1000`，正常情况下不会出现。

### 7.5 去重说明
- 发送时对**文字**（最近 60 条 `.md`/`.done` 正文）和**图片**（最近 60 张图片 MD5）做去重；与已有内容相同则跳过，弹"已发送过，不重复"。
- 若你确实想重复存同一条，可先改一点内容再发。

### 7.6 日志排查法
所有启动、热键触发、发送成败、分析服务状态都写进 `log.txt`：
- 打开方式：托盘「打开运行日志」，或直接打开 `C:\Users\user\WorkBuddySender\log.txt`。
- 遇到异常时，把对应时间段的日志内容提供出来，即可精准定位（例如 `发送异常`、`分析服务不可用`、`热键已切换为 XXX` 等）。

### 7.7 单实例
- 同时只跑一个发送端、一个阅读器。重复双击会被静默拒绝（原子锁 `.sender.lock` / `.reader.lock`）。
- 若上次异常退出残留了锁文件，程序会在下次启动时检测"锁中 PID 已死"并自动接管，一般无需手动清理。

### 7.8 退出
- 发送端：托盘「退出」。
- 阅读器：纯后台服务，关掉浏览器即可；如需彻底关闭阅读器后端，可在阅读器页面调用退出（或结束对应 `pythonw.exe` 进程）。

---

## 八、一句话总结（给不太懂技术的你）

复制东西 → 按 `ALT+4`（或阅读器里改的键）→ 进收件箱 → 每小时（或右键"分析收件箱"）自动出 AI 分析 → 打开阅读器看"原文 + 结论"，还能就某条继续追问。全程后台运行、有日志、防多开、可自定义热键。

---

## 九、关于与版权

- **名称**：剪思盒 (ClipThink)
- **版本**：1.0.0
- **作者**：微博@下一站澳门
- **源码**：https://github.com/JohnWish1590/clipthink
- © 2026 保留所有权利。
- 本扩展仅供个人学习使用，与 Workbuddy 官方无任何隶属或合作关系。Workbuddy 及相关标识归其各自权利人所有。

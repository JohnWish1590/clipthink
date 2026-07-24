# PRD：剪思盒 / ClipThink 品牌统一与 v1.0.0 发布（增量）

> 文档类型：增量 PRD（在已有可运行工具基础上的改名 + Bug 修复 + GitHub 文档/发布）
> 文档负责人：产品经理 许清楚
> 日期：2026-07-23
> 关联仓库：https://github.com/JohnWish1590/clipthink

---

## 0. 项目信息

| 项 | 内容 |
|---|---|
| 原始需求复述 | 将现有 Windows 托盘工具「WorkBuddy 收件箱」统一改名为「剪思盒 / ClipThink」；修复托盘菜单「打开阅读器」的 `NameError` 缺陷；补齐 GitHub 文档（README/CHANGELOG/Release Notes）；将仓库由 private 转为 public 并发布 v1.0.0。 |
| 项目名（新） | `clipthink`（snake_case 目录/文件前缀） |
| 语言 | 中文 |
| 技术栈（现状，不改） | Python（pyw 托盘 + 本地 HTTP 服务）+ HTML/JS 阅读器前端；依赖 pystray / Pillow / tkinter / pywin32 / Node.js / WorkBuddy 桌面端（codebuddy CLI） |

---

## 1. 产品定义（简述）

### Product Goals
1. **品牌一致**：用户在任何可见界面/文件/目录中看到的产品名统一为「剪思盒 / ClipThink」，去除旧「WorkBuddy 收件箱」字样。
2. **功能无损**：改名与发布过程不破坏热键发送、自动分析、阅读器回看等已有能力（含托盘「打开阅读器」）。
3. **可发布**：以公开、可复现的方式在 GitHub 发布 v1.0.0，降低非开发用户的上手门槛。

### User Stories
- 作为用户，我希望在托盘提示、阅读器标题、关于页看到的都是「剪思盒」，而不是旧的 WorkBuddy 名称。
- 作为用户，我希望右键托盘「打开阅读器」能正常打开网页，而不是毫无反应。
- 作为 GitHub 访客，我希望 README 顶部有清晰的「前置条件 / 安装 / 快速部署 / 启动 / 依赖」，能照着跑起来。
- 作为维护者，我希望有 CHANGELOG 与 Release Notes，便于追踪版本变更。

---

## 2. 改名需求（核心：新旧名称映射表）

### 2.1 命名决策（建议值，待确认见 §6）

| 维度 | 旧 | 新（建议） |
|---|---|---|
| 产品显示名 | WorkBuddy 收件箱 | **剪思盒 / ClipThink** |
| 项目目录 | `C:\Users\user\WorkBuddySender` | `C:\Users\user\ClipThink` |
| 发送端主程序 | `WorkBuddySender.pyw` | `clipthink_sender.pyw` |
| 阅读器后端 | `WorkBuddyReader.pyw` | `clipthink_reader.pyw` |
| 收件箱目录 | `C:\Users\user\WorkBuddyInbox` | `C:\Users\user\ClipThinkInbox` |

### 2.2 必改位置总表（按优先级）

#### P0（必须改，否则用户可见或功能断裂）

| # | 位置 | 旧值（节选） | 新值 | 文件/对象 |
|---|---|---|---|---|
| 1 | 阅读器 HTML `<title>` | `WorkBuddy 收件箱阅读器` | `剪思盒阅读器` | reader.html L6 |
| 2 | 阅读器页头 `<h1>` | `WorkBuddy 收件箱阅读器` | `剪思盒阅读器` | reader.html L132 |
| 3 | 托盘图标 tooltip | `WorkBuddy 收件箱 - 运行中 ({combo})` | `剪思盒 - 运行中 ({combo})` | WorkBuddySender.pyw L697 |
| 4 | 托盘图标内部名 `Icon(...)` | `Icon("WorkBuddySender", …)` | `Icon("ClipThink", …)` | WorkBuddySender.pyw L694 |
| 5 | 常量 `READER_SCRIPT` | `"WorkBuddyReader.pyw"` | `"clipthink_reader.pyw"` | WorkBuddySender.pyw L509（改名后须与实际文件名一致） |
| 6 | 常量 `INBOX`（发送端） | `C:\Users\user\WorkBuddyInbox` | `C:\Users\user\ClipThinkInbox` | WorkBuddySender.pyw L77 |
| 7 | 常量 `INBOX`（阅读器） | `…\WorkBuddyInbox` | `…\ClipThinkInbox` | WorkBuddyReader.pyw L70 |
| 8 | 分析提示词里的目录硬路径 | `C:\Users\user\WorkBuddyInbox` | `C:\Users\user\ClipThinkInbox` | WorkBuddySender.pyw L93（`ANALYSIS_PROMPT` 内） |
| 9 | 源码文件改名 | `WorkBuddySender.pyw` / `WorkBuddyReader.pyw` | `clipthink_sender.pyw` / `clipthink_reader.pyw` | 文件系统 + git mv |
| 10 | 项目目录改名 | `C:\Users\user\WorkBuddySender` | `C:\Users\user\ClipThink` | 文件系统 + 数据迁移 |
| 11 | 收件箱目录改名 + 数据迁移 | `C:\Users\user\WorkBuddyInbox` | `C:\Users\user\ClipThinkInbox`（保留已有 .md/.done/图片） | 文件系统 |
| 12 | 关于/版权块（名称） | `名称：剪思盒 (ClipThink)` | 维持（已正确） | reader.html L164 / README §九 |
| 13 | 关于/版权块（仓库链接） | `github.com/JohnWish1590/clipthink` | 维持（已正确） | reader.html L167 / README §九 |
| 14 | README 标题与全文 | `WorkBuddy 收件箱` 等 | `剪思盒 / ClipThink` | README.md 全文 |
| 15 | 功能架构图 SVG 文字标签 | `WorkBuddySender 功能架构与数据流`、`WorkBuddySender.pyw`、`WorkBuddyInbox/`、`<title>`/`WorkBuddySender …` | `ClipThink 功能架构与数据流`、`clipthink_sender.pyw`、`ClipThinkInbox/` 等 | 功能架构图.svg |

#### P1（应改：脚本/快捷方式/品牌声音）

| # | 位置 | 旧值 | 新值 | 文件 |
|---|---|---|---|---|
| 16 | 顶部文档注释 | `WorkBuddy 收件箱热键监听器…` | `剪思盒 热键监听器…` | clipthink_sender.pyw L1-9 |
| 17 | 阅读器顶部注释 | `WorkBuddy 收件箱阅读器 —— 纯后台 HTTP 服务` | `剪思盒阅读器 —— 纯后台 HTTP 服务` | clipthink_reader.pyw L1 |
| 18 | 分析提示词 persona | `你是 WorkBuddy 收件箱分析助手` | `你是 剪思盒（ClipThink）分析助手` | clipthink_sender.pyw L92 |
| 19 | 阅读器「继续讨论」文案（3 处） | `跟 WorkBuddy 进一步聊` / `发到 WorkBuddy 讨论` / `直接粘贴给 WorkBuddy` | 见 §6 决策（建议统一为「发到 剪思盒 分析」或保留指代底层引擎的「WorkBuddy」） | reader.html L153/310/315 |
| 20 | 桌面快捷方式「WorkBuddy 阅读器」 | 标题/描述/READER 路径 | `剪思盒 阅读器` + 指向 `clipthink_reader.pyw` | make_reader_shortcut.py L2/11/13/22 |
| 21 | 桌面快捷方式「WorkBuddy收件箱」 | `WorkBuddy收件箱.lnk` / 描述 | `剪思盒.lnk` + 指向 `ClipThinkInbox` | make_desktop_shortcut.py L10/12/22 |
| 22 | 「启动 WorkBuddy 收件箱」快捷方式（桌面+开机） | 路径/描述含 WorkBuddySender | `启动 剪思盒` + 指向 `clipthink_sender.pyw` | update_all_shortcuts.py L5-12；fix_all_shortcuts_pyw.py L4-22 |
| 23 | 开机自启脚本 | `…\WorkBuddySender\WorkBuddySender.ahk` 等 | `…\ClipThink\clipthink_sender.pyw`（或保持 .ahk 但同步改名） | add_to_startup.py L5/18/19 |
| 24 | 资源管理器右键菜单文案 | `发送到 WorkBuddy 分析` / `SendToWorkBuddy` 注册键 | `发送到 剪思盒 分析` / `SendToClipThink` | register_context_menu.py L8/11 |
| 25 | 旧启动器文件名 | `WorkBuddySender.ahk/.bat/.vbs`、`send_to_workbuddy.ps1` | 统一改为 `clipthink_sender.*` / `send_to_clipthink.ps1`（或确认弃用并删除） | 文件系统 |
| 26 | 其它 fix_*/make_*_shortcut.py 内硬编码路径/标题 | `C:\Users\user\WorkBuddySender`、WorkBuddy 字样 | 同步为 `ClipThink` | 全部辅助脚本 |

#### P2（可选：内部标识/装饰）

| # | 位置 | 旧值 | 新值 |
|---|---|---|---|
| 27 | logger 名 | `wb-sender` | `clipthink`（仅日志前缀，无用户可见影响） |
| 28 | 阅读器页头 logo 字母 | `W`（reader.html L131 `<div class="logo">W</div>`） | `剪` 或 `C`（视觉品牌，需设计确认，见 §6） |
| 29 | 内部交接文档 HANDOFF.md | 含旧名 | 同步（已被 .gitignore 忽略，低优先） |

### 2.3 明确「不修改」的项（事实性外部依赖，保持准确）

以下出现「WorkBuddy」是**对底层 AI 引擎的真实依赖描述**，不应改成产品名，否则会误导用户或破坏功能：

- README 中「依赖 **WorkBuddy 桌面端**（提供 `codebuddy` CLI）」及 `C:\Program Files\WorkBuddy\resources\app.asar.unpacked\cli\bin\codebuddy` 路径。
- 代码常量 `CODEBUDDY_CLI`（clipthink_sender.pyw L83）及其环境变量 `CODEBUDDY_GATEWAY_AUTH` / `CODEBUDDY_DISABLE_REQUEST_VALIDATION`。
- 关于/版权块中的法律免责：「本扩展仅供个人学习使用，与 Workbuddy 官方无任何隶属或合作关系。Workbuddy 及相关标识归其各自权利人所有。」（公开仓库必须保留）。
- 收件箱内的 `.workbuddy` 子目录（引擎会话产物，由 codebuddy 管理，不迁移/不重命名）。

> ⚠️ 改名逻辑边界：只改「本产品自己的名字」，**不要**把「调用 WorkBuddy 桌面端做分析」这个事实改掉。

---

## 3. Bug 修复需求：托盘「打开阅读器」

### 3.1 现象
右键托盘图标 → 点击「打开阅读器」→ 无反应；`log.txt` 报错：
`NameError: name 'subprocess' is not defined`。

### 3.2 根因（已定位）
- 当前源码 `clipthink_sender.pyw` 第 18 行**已存在** `import subprocess`，并在 `open_reader()`（启动阅读器）与 `ensure_serve()`（拉起分析服务）中正确使用。
- 报错来自**运行进程加载了陈旧的 `__pycache__` 字节码**（旧版源码当时 `import subprocess` 缺失/位置不当），且本次改源后 `.pyc` 因 mtime/校验未触发重编译，于是执行的是旧字节码。
- 目录 `C:\Users\user\WorkBuddySender\__pycache__\` 确实存在，印证此判断。

### 3.3 修复目标
- 点击「打开阅读器」能稳定启动阅读器后端（端口 8765，若已运行则仅开浏览器）并打开 `http://127.0.0.1:8765/`，`log.txt` 记录 `已启动/打开阅读器`，**不再出现 `NameError`**。

### 3.4 修复方案
1. **（关键）清理陈旧字节码**：删除 `C:\Users\user\WorkBuddySender\__pycache__\` 整个目录（含所有 `*.pyc`）；改名发布时因文件名变更天然失效，但仍需显式删除一次。
2. **（加固）导入位置**：确认 `import subprocess` 位于模块顶部 import 区（当前已满足），确保任何被调用函数执行前已就绪；无需逻辑改动。
3. **（验证）回归**：见 3.5 验收标准。

### 3.5 验收标准（Acceptance Criteria）
- [ ] 全新（已清 `__pycache__`）启动 `clipthink_sender.pyw`，托盘出现。
- [ ] 右键托盘 → 「打开阅读器」→ 浏览器打开 `http://127.0.0.1:8765/`，页面正常渲染。
- [ ] 若阅读器未运行，后端被拉起（端口 8765 监听）；若已运行，仅开浏览器、不重复拉起。
- [ ] `log.txt` 含 `已启动/打开阅读器`，且**全量搜索 `NameError` 为 0 命中**。
- [ ] 重复点击 3 次均正常（单实例：端口占用时只开浏览器）。

---

## 4. GitHub 文档规范需求

### 4.1 README 必须新增的章节（结构建议）
在 README 顶部或「一、项目概述」前新增 **「快速开始 / Quick Start」** 区块，至少包含：

1. **前置条件**：Windows 10/11；已装 WorkBuddy 桌面端（提供 `codebuddy` CLI）；已装 Node.js；已装 Python 3.11+。
2. **依赖说明**（明确列出）：
   - WorkBuddy 桌面端（分析引擎，`codebuddy` CLI 路径 `C:\Program Files\WorkBuddy\...`）
   - Node.js（用于 `node codebuddy --serve` 拉起本地分析服务）
   - Python 包：`pystray`、`Pillow`、`pywin32`（`win32com`，用于快捷方式/开机自启）；`tkinter` 为标准库
3. **安装步骤**：`git clone` → `cd clipthink` → `pip install -r requirements.txt`（需新增 `requirements.txt`：pystray / Pillow / pywin32）。
4. **快速部署**：运行 `pythonw clipthink_sender.pyw`；可选 `python add_to_startup.py` 开机自启；可选 `python register_context_menu.py` 注册右键菜单。
5. **启动方式**：双击 `clipthink_sender.pyw`（或桌面「启动 剪思盒」快捷方式）；托盘出现后按热键发送；浏览器访问 `http://127.0.0.1:8765/` 看阅读器。
6. 保留原有 9 章功能说明，并将其中所有 `WorkBuddy 收件箱` / `WorkBuddySender` / `WorkBuddyReader` / `WorkBuddyInbox` 按 §2 映射替换为新名。

> 注：现有 README 已有「4.1 安装/前置条件」「4.2 启动方式」，但分散且缺 `requirements.txt` 与「快速部署」。本次要求**前置、安装、快速部署、启动、依赖**五项在 README 中显式成章。

### 4.2 新增 `CHANGELOG.md`（Keep a Changelog 规范）
- 路径：仓库根 `CHANGELOG.md`
- 格式：基于 [Keep a Changelog 1.1.0](https://keepachangelog.com/zh-CN/1.1.0/)，遵循语义化版本。
- 草稿见附录 A。

### 4.3 新增 Release Notes（用于 GitHub Release v1.0.0）
- 作为 Release 描述正文，中文撰写，含：一句话定位、亮点、安装/快速开始、已知限制、免责声明。
- 草稿见附录 B。

### 4.4 其它文档动作
- 新增 `requirements.txt`（`pystray`、`Pillow`、`pywin32`）。
- 确认 `.gitignore` 已忽略 `log.txt`、`.sender.lock`、`.reader.lock`、`__pycache__/`、`HANDOFF.md`、旧脚本（当前已覆盖）。公开前再次确认**无密钥/令牌**被提交（`log.txt`、`.workbuddy` 均不应入库）。

---

## 5. 仓库公开需求

| 项 | 要求 |
|---|---|
| 可见性 | 由 **private → public** |
| Release | 创建 **v1.0.0**（tag `v1.0.0`），以附录 B 为 Release 描述 |
| 发布前检查 | 1) 全部改名落地且通过 §3.5；2) README/CHANGELOG/Release Notes 就绪；3) 无敏感文件入库；4) 免责声明保留 |
| 风险 | 公开后仓库名 `clipthink` 与「ClipThink」标识对外可见，需确认无商标冲突（低风险，个人学习项目已加免责） |

---

## 6. 待确认问题（Open Questions / 风险）

1. **新目录/文件名是否采用本 PRD 建议值？**
   `C:\Users\user\ClipThink`、`clipthink_sender.pyw`、`clipthink_reader.pyw`、`C:\Users\user\ClipThinkInbox`。若主理人想用其它命名（如 `ClipThinkSender`/`ClipThinkReader`），需同步调整 §2.1 与所有脚本常量。
2. **重命名目录/文件会破坏现有入口（高风险）：**
   - 桌面 3 个 `.lnk`：`WorkBuddy 阅读器.lnk`、`WorkBuddy收件箱.lnk`、`启动 WorkBuddy 收件箱.lnk`
   - 开机自启 `Startup\WorkBuddySender.lnk`
   - 资源管理器右键菜单注册表 `SendToWorkBuddy`
   - 上述均由 `add_to_startup.py` / `update_all_shortcuts.py` / `fix_all_shortcuts_*.py` / `register_context_menu.py` 生成，**改名后必须重新运行生成脚本（并先 unregister 旧右键菜单）**，否则入口全部失效。
   - 是否存在其它引用旧路径处（任务计划程序、其它快捷方式）？建议发布前全局搜索 `WorkBuddySender` / `WorkBuddyInbox`。
3. **收件箱数据迁移方式：** 改名 `WorkBuddyInbox → ClipThinkInbox` 时，已有 `.md`/`.md.done`/图片如何迁移（整目录复制/移动）？是否一并迁移 `.workbuddy` 会话子目录（建议不迁移，由引擎重建）？
4. **「继续讨论」文案里的 WorkBuddy 是否改产品名？** reader.html 中 `跟 WorkBuddy 进一步聊`/`发到 WorkBuddy 讨论`/`直接粘贴给 WorkBuddy` 实际指向底层分析引擎。建议二选一：(a) 保留「WorkBuddy」以如实表达「发到 WorkBuddy 分析」；(b) 统一为「发到 剪思盒 分析」。需主理人定夺。
5. **阅读器页头 logo 字母 `W` → 改什么？** 建议 `剪`（产品首字）或 `C`（ClipThink 首字母）；属视觉品牌决策。
6. **旧启动器（.ahk/.bat/.vbs/send_to_workbuddy.ps1）是否保留？** README 已标注废弃。建议随改名一并改为 `clipthink_sender.*` / `send_to_clipthink.ps1`，或直接删除并清理相关注册/快捷方式。
7. **`hotkey.json` 当前值为 `ALT+Q`**（非代码默认 `ALT+4`）。改名发布不改变热键，但需在 README/设置说明中写清「文件优先于默认值」，避免用户困惑。

---

## 7. 需求池（Requirements Pool）

**P0（Must）**
- 全部 §2.2 P0 项改名落地（界面/常量/文件/目录/README/SVG）。
- 修复 §3 托盘「打开阅读器」并满足 §3.5 验收。
- 收件箱数据从 `WorkBuddyInbox` 迁移到 `ClipThinkInbox` 且可用。
- 仓库转 public + 发布 v1.0.0。

**P1（Should）**
- §2.2 P1 全部脚本/快捷方式/右键菜单/分析 persona 同步改名并重新生成入口。
- README 新增「前置条件/安装/快速部署/启动/依赖」五章 + `requirements.txt`。
- 新增 `CHANGELOG.md` 与 Release Notes。

**P2（Nice to have）**
- logger 名、页头 logo 字母、HANDOFF.md 等内部/装饰项同步。
- 发布前全局搜索校验无残留旧名。

---

## 附录 A：CHANGELOG.md 草稿（Keep a Changelog）

```markdown
# Changelog

本文件记录本项目所有重要变更。
格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [1.0.0] - 2026-07-23

### Added
- 首次公开发布：GitHub 仓库由 private 转为 public。
- 产品品牌统一：原名「WorkBuddy 收件箱」正式更名为「剪思盒 / ClipThink」。

### Changed
- 重命名项目目录、源码文件（clipthink_sender.pyw / clipthink_reader.pyw）、
  收件箱目录（ClipThinkInbox）及全部用户可见文案。
- README 新增「前置条件 / 安装 / 快速部署 / 启动 / 依赖」章节，并补充 requirements.txt。

### Fixed
- 修复托盘菜单「打开阅读器」点击无反应的问题
  （根因：运行进程加载了陈旧的 __pycache__ 字节码导致
  `NameError: name 'subprocess' is not defined`；已清理字节码并加固导入）。

### Removed
- 弃用旧启动器 WorkBuddySender.ahk/.bat/.vbs、send_to_workbuddy.ps1
  （随改名一并清理或重命名）。
```

## 附录 B：Release Notes（v1.0.0）草稿

```markdown
# 剪思盒 ClipThink v1.0.0

常驻 Windows 系统托盘的小工具：一键全局热键把剪贴板里的文字/图片发送到「剪思盒」，
由 WorkBuddy 桌面端的 AI 自动做结构化分析，并提供本地网页阅读器随时回看
「原文 + 分析结果」，还能就某条继续追问。

## 亮点
- 全局热键一键收藏（默认 ALT+4，可自定义）
- 每小时自动分析 + 托盘手动即时触发
- 本地阅读器左右两栏：原文 / 分析结论，支持 Markdown 与图片
- 后台常驻、无黑窗、单实例防多开、运行日志可查

## 快速开始
1. 前置：Windows 10/11 + WorkBuddy 桌面端（提供 codebuddy CLI）+ Node.js + Python 3.11+
2. 安装依赖：`pip install -r requirements.txt`
3. 启动：`pythonw clipthink_sender.pyw`
4. 阅读器：浏览器访问 http://127.0.0.1:8765/

## 已知限制
- 分析与「未分析」在列表里会各显示一条（保留原 .md，另写同名 .md.done）。
- 分析依赖 WorkBuddy 桌面端，未安装则分析功能不可用。
- 重命名/迁移后请重新生成桌面与开机快捷方式、重新注册右键菜单。

## 免责声明
本扩展仅供个人学习使用，与 Workbuddy 官方无任何隶属或合作关系。
Workbuddy 及相关标识归其各自权利人所有。
```

---

> 文档结束。落地实现见开发任务拆解（架构师）/ 实施任务（开发）。

<!--
本文件是**手工维护**的 curated 参考，不由 scripts/build_dsh_skill.sh 生成（已在脚本的 KEEP 白名单内）。
内容原先挤在 SKILL.md 里，属「给维护者与评估者看」的元信息；迁出后 SKILL.md 只保留执行所需的操作指令。
-->

# 第 18 章 本技能的边界与维护

> **本文件用途**：两件不属于「开发 DSH 插件」本身、但会影响本技能可信度的事——
> ① **已知边界**：本技能不保证什么、哪些结论是快照、哪些坑是刻意保留的空白；
> ② **维护守则**：改本技能时必须遵守的分层、预算、核验与归一化规则。
> 读它的时机：评估本技能是否适合当前任务时；准备修改本技能时。

---

## 18.1 已知边界（诚实声明，不要复述给用户当结论）

**关于防过时机制**

- **探针必须能失败**，且**改探针后必须跑一次负向验证**。两处已修的假通过：bash 版空断言表报「全部成立」（现为 exit 3）、Python 版把文件当目录导致假 STALE。方法与脚本示例见 `00-version-gate.md` 第 9 节。
- **探针只覆盖它断言过的 56 条事实**，第二批 49 条在 `scripts/verify_absorbed_claims.py` 里（**两个核验入口，改基线要跑两个**）。两者都**不覆盖 V 级细节**；核验通过 ≠ 插件能跑通。
- 🔴 **判据缺陷与内容过时是两回事（2026-09-23 实测教训）**：本轮 4 条 STALE 里，**一条都不是文档写错了** —— 全是断言的**判据写法**有问题（整句锚定 / 邻近窗口过窄 / 逐字 import / 裸键正则过宽）。**看到 STALE 先问「是内容错了，还是判据错了」**，两者的修法相反：内容错要改文档，判据错要改断言。判别方法 = 拿**同一个判据**去跑**旧 tag 的检出**：若旧 tag 上也 STALE，则内容大概率没错，是判据挑剔了。
- 🔴 **邻近窗口（`[\s\S]{0,N}?`）是对排版敏感的判据**：上游在两条声明之间插入一段 JSDoc 就能让它失败（本轮 `U07`：实测字符距离 482，原窗口 400）。**能用两条独立断言表达的就不要写成一条跨行邻近式**（`U09`/`U10` 就是这样拆的）。
- **否定性断言必须配护栏模式**：只写「X 不存在」而不写「必然存在的 Y 命中」，在空语料/错路径下会**整表假通过**——本项目已实际发生两次。见 `api-claims.md` §6。
- references 里带行号的引用，**行号一定会漂移**；核验只能按符号名 grep。

**关于内容本身**

- **版本史是快照，不是流水账。** `13-version-history.md` 只列「会让现有代码/配置失效」的变更，每个区间还有几十到上百条新功能与内部重构**不在其中**。要全量请用第 6 节的命令自行生成。
- **DSH 没有 CHANGELOG，也不用 `BREAKING CHANGE:` 页脚**，但它**会用 `type(scope)!:` 标题标记**自报破坏性提交。所以准确说法是：「查变更日志」不成立，`--grep='!:'` 有效但覆盖不全，「`!:` + 源码级对比」并用才成立。
- 官方文档存在**两处内部矛盾**，本技能已选定立场，见 `11-glossary-and-provenance.md`。
- **UI 插槽清单曾被低估**：早期那张表由 `slots.(inject|register)('...')` 提取，**抓不到内建键**，因此既不全、也曾漏掉 `root`。权威清单用 `scripts/extract_slots.py` 复现。**凡「全部 / 仅 / 只有 N 个」这类完备性措辞，都必须能给出可复现的抽取命令与范围。**

**关于范围（有意不做的事）**

- **`ctx.webServer` 只在 Web 组合里存在**（它是一行补丁提供的服务，不是核心服务）。纯后端插件硬写 `inject = ['webServer']`，在 TUI / headless / 精简 profile 里会**永久 PENDING**；要跨 profile 可用就改用 `ctx.get('webServer')` 做可选分支，并在 README 写明前置要求。
- **托管插件包内的静态文件**：发布的 Web 组合里「回退席位」已被 `dsh-host-frontend-static` 认领，而该席位**只有一个所有者，第二次注册抛异常**——所以别指望用 `registerFallback` 抢整站；要托管自己的文件就用 `kind: 'prefix'` 的路由自己读文件应答。细节见 `14-inbound-http-and-timers.md` §17.1。
- **「发布一个 DSH skill（不是插件）」属本技能范围外**（本技能讲的是 DSH 插件，不是 skill 打包）。
- 本技能**不提供插件项目的自动一致性检查器**。同类方案带一个轻量校验脚本，但它把构建器绑死在特定打包约定（esbuild + `scripts/build.mjs`）上，本 skill 跟随的是另一套工程约定，照搬会误报。本技能把它要检查的项**收进了「交付前自检清单」**；日后若要脚本化，须按本技能自己的约定重写并做正反向验证。
- **`docs/plan.md` 是辅助产物，不是门禁依据。** 它记录「你当时为什么这么选」，不证明插件正确；正确性只由真实组合里的冒烟与验收证明。
- **同类方案的「完整可运行配方」不可默认信任。** 本轮调研的同名方案（`dsh-plugin-studio`）里，HTTP 路由 / 定时器 / 插槽注册 / `ctx.ui` 四处写法**逐条对源码核验后全部不成立**（属「不报错但永不生效」型）。清单见 `14-inbound-http-and-timers.md` §17.5。**结构可以借，代码必须核验。**

---

## 18.2 维护守则（防止本技能变形）

### 分层：什么内容放哪一层

| 层 | 放什么 | 判据 |
|---|---|---|
| `SKILL.md` | 流程 / 路由 / 红线 / 合同 / 验收 —— **执行任务时必须知道的** | 每次开发都要看吗？ |
| `references/` | 细节、逐字源码、坑点全表、边界与维护 | 只在特定情形才需要吗？ |
| `assets/` | 可直接复制/改名的产物（骨架、模板） | 会被写进用户项目吗？ |
| `scripts/` | 确定性、可重复执行、可**不读进上下文**就跑的代码 | 需要「执行」而非「阅读」吗？ |

**反例（本技能真发生过）**：版本闸门的详细机制、已知边界清单、维护守则都曾挤在 `SKILL.md` 里，使入口层有 18% 的篇幅在讲「本技能自己」，而不是在讲「怎么开发插件」。**入口层读起来像 README，就是分层失效的信号。**

### 每个资源都要有「加载条件」，否则等于没放

**分层只解决「放哪」，加载条件才解决「会不会被用」。** 一个放在 `references/` 里、却没人知道何时该读它的文件，等于不存在。

因此 `SKILL.md` 的资源索引是一张**加载路由表**，每行必须给出三件事：

| 列 | 含义 | 判据 |
|---|---|---|
| **触发条件** | 什么情形下才需要这个文件（含「什么时候**不**需要」） | 写不出触发条件 → 该内容应下沉或删除 |
| **读法** | 整读 / 定点（先 `grep` 定位再读那一节）/ 禁止整读 | 含上游素材的文件**不得标「整读」** |
| **成本** | 一次装载的上下文代价（低 / 中 / 高 / 极高） | 「极高」只允许配「禁止整读」 |

**两条硬规则**（由工作区侧的资源层审计器自动核对）：

1. **含上游素材的文件，读法不得是「整读」。** 否则读者会把素材段一起吞下去——素材是上游原文（性质不一：既有官方文档逐字摘录，也有调研期粗笔记），不是可以直接照做的整理稿。
2. **每个 `references/` `assets/` `scripts/` 下的文件都必须出现在路由表里。** 没有被引用到的资源是死文件。

**配套要求：大文件要在文件头自带导航块**，写明「多少行、不要整读、哪一段是整理稿、哪一段是上游素材、用什么 `grep` 定位」。导航块只写**可 `grep` 的标题锚点，不写行号**——行号会随文件演进而腐化，锚点不会。

### 硬预算

**`SKILL.md` ≤ 500 行**（2026-09-11 由 230 行上调；`scripts/check_refs.py` 之外的构建门禁见下）。上调的理由：入口层要承担能力面路由、冒烟判定、合同不变量、交付前自检与端到端示例——这五类内容**每次开发都会用到**，放在 `references/` 里会被反复跳过。**但 500 行是天花板，不是目标**：能下沉的仍然下沉。

> 本项目没有可用的自动行数门禁（原 `build_dsh_skill.sh` 已失效，见下），改动后请手动核对；工作区侧的 `scripts/_check_skill_merge.py --budget 500` 可复现该检查。

### 加内容前的三问

1. **每次开发都要看吗？** 否则下沉到 `references/`。
2. **是可核验的事实吗？** 是 → 登记 `api-claims.md` **并加进某个核验器的断言表**：核心骨架进 `dsh-api-probe.py/.sh`，专题事实进 `verify_absorbed_claims.py`。
3. **是否定结论（「没有 X」）吗？** 是 → **必须同时加一条 N 级反向断言 + 护栏模式**（护栏 = 一个在该作用域内必然命中的样本），否则它在空语料上会假通过。

### references 有三类文件（生成类 / 拆册派生 / 手工维护类）

| 类别 | 文件 | 能不能手工改 |
|---|---|---|
| **生成类** | `01`~`13` | ⚠️ **只允许定点编辑**（`Edit` 改指定的几行 / 插入一个导航块），**禁止整文件重写**：它们由构建脚本按源手册行号区间生成，整文件覆盖 = 丢掉所有历史上的手工加工。定点编辑是允许且必要的——例如插导航块、修标题编号歧义 |
| **生成类（拆册派生）** | `02b`、`02c`、`10a`~`10d` | 由 `02-templates.md` / `10-community-casebook.md` 按来源**逐行搬迁**拆出（2026-09-14）。正文是上游一手素材原文，**不是整理稿**；改动须同步总索引与 `SKILL.md` 路由表。它们**不参与**构建脚本的区间生成，但同样**禁止重写正文**——要改就在原文段上定点改。⚠️ **一处已知偏离**：`10b-casebook-tools.md` 已于 2026-09-15 / 09-16 因**许可整改**被定点改写两轮（清 AGPL 逐字转载 → 该来源整体移出引用集合），**不再是逐行搬迁**；这是**用户授权的许可合规改动**，动用的是「定点改」通道并留痕于该册 §1.2 的移除清单与 `13-version-history.md` §1.5 |
| **手工维护类** | `00`、`api-claims`、`14`、`15` | ✅ 可自由改写；**新增此类文件必须同步构建脚本的 `KEEP` 白名单**，否则下次构建会被当陈旧文件删掉 |

⚠️ **`build_dsh_skill.sh` 当前不可运行**（`$WS` 指向的工作区已不存在），且它一旦运行会**静默丢失**生成类文件里的手工追加内容（如 `00-version-gate.md` §9、`api-claims.md` §6/§7）。**不要「顺手修好」它**——要恢复这条流水线，必须先把手工内容折回源手册，或把脚本拆成「只跑门禁、不跑生成」。

### 资源引用归一化（守门脚本 `scripts/check_refs.py`）

本技能是**自包含**发布物：`references/` `assets/` `scripts/` 之外的路径在用户机器上都不存在。因此：

- **生成期素材只写代号**（「素材 B 坑 M1」），**不要**写成带路径或带扩展名的文件引用（形如 `plugin-research/notes/<素材代号>.md` 或 `notes/<素材代号>.md`）。对照表见 `11-glossary-and-provenance.md` §A.2。
- **不要写本机绝对路径**（会把作者机器的工作区路径带进发布物，既悬空又泄漏）。
- 指向 **DSH 上游**的路径（`packages/…`、`docs/…`、`apps/…`、`vendor/…`）是**合法**的——它们说的是「去目标 DSH 检出里找」，不是「在本技能里找」。
- 改完跑一次：`python scripts/check_refs.py .`（退出码 0 = 无问题引用）。

### 技能版本号约定（三段，与 DSH 的变更级别挂钩）

本技能自带一个三段版本号，**只有一个落点**：`SKILL.md` frontmatter 的 `version`。

> 🔴 **2026-09-12 更正（原文为「三处同改」）**：第三处原为 `skill-card.md` 的 Skill Version(s)。但 ClawHub 明确声明该文件**由平台生成、不可直接发布**——错误原文：`skill-card.md is generated by ClawHub and cannot be published directly.` ——故已把它移出发布目录，版本号随之收敛为**两处**。同批平台生成物 `_icon.png` / `_meta.json` **也已一并移出**，版本号随之收敛为**只有一个落点**：`SKILL.md` frontmatter。（判据的取证脚本与日志留在项目工作区，不随技能发布。）

它回答的是「**本技能自己改到了什么级别**」，**不用来**表示「本技能对应哪个 DSH 版本」——后者由**四处**精确记录（见下），且**四处必须同时改**：① `13-version-history.md` §1.5 的「技能版本 ↔ DSH 基线对照表」（**主表**）；② 本文件 **§18.2 的版本台账**（**镜像**）；③ `00-version-gate.md` §1 的基线行；④ 技能仓库里每个版本对应的 **commit + annotated git tag**（`v<技能版本>`，**注解内带 DSH 基线与基线 commit**）。一个 `1.0.4` 读不出对应的 DSH 版本，一个 `baseline_tag` 却可以；别让版本号去承担它承担不了的职责。

| 触发条件 | 改哪一段 | 例 |
|---|---|---|
| ① 官方发布了新 tag（**无论是否**引起内容变更）② 技能自身的缺陷被修复 | **第三段 +1** | `1.0.3 → 1.0.4` |
| DSH 出现**破坏性变更**（会让已有插件代码 / 配置失效；判定口径见 `13-version-history.md` §2） | **第二段 +1**，第三段归零 | `1.0.4 → 1.1.0` |
| DSH 发布**大版本**（第一段进位，如 `0.x → 1.x`） | **第一段 +1**，其余归零 | `1.4.2 → 2.0.0` |

**四条细则**：

1. **一轮更新只产出一个新版本号。** 同一轮里若同时命中多档（既发了新 tag、又含破坏性变更），**取最高的那一段**，低位归零。
2. **只增不减。** 本约定自 `1.0.3` 起生效，历史版本号不回改、不重排。
3. **版本号只有一个落点**：`SKILL.md` frontmatter 的 `version`。任何额外副本（无论放在哪个文件）都会与它漂移，且可能反过来阻断发布。
4. 每一轮更新都要在下面的台账**追加一行**。

**版本台账**（技能自身；与 DSH 版本史 `13-version-history.md` 是两份东西，别混）

> **权威主表在 `13-version-history.md` §1.5**（多两列：基线 commit、git 锚点）。此处是精简镜像，**两处必须同时改，不要只改一处**。

| 技能版本 | DSH 基线 | 基线 commit | 日期 | git 锚点 | 变更摘要 |
|---|---|---|---|---|---|
| `1.0.0` | `dsh-v0.1.5-rc.2` | `c291e7961a` | 2026-09-11 | `ba06186`（首提交） | 技能初始化 |
| `1.0.3` | `dsh-v0.1.5-rc.2` | `c291e7961a` | 2026-09-11 | `38d7bc0` | 吸收同类方案素材、重构 `SKILL.md`、修悬空引用（**已推送 GitHub**） |
| `1.0.4` | `dsh-v0.1.5-rc.2` | `c291e7961a` | 2026-09-12 | tag `v1.0.4` | 修 `assets/` 模板缺陷（补 `exports`、工具插件改为零构建可运行入口）；建立本版本约定；补「技能版本 ↔ DSH 基线」对照表 |
| `1.0.5` | `dsh-v0.1.5-rc.2` | `c291e7961a` | 2026-09-12 | tag `v1.0.5` | 补 `SKILL.md` frontmatter 的 `slug` / `displayName`（发布器硬要求）；澄清 `ownerId` 属 ClawHub 侧字段 |
| `1.0.6` | `dsh-v0.1.5-rc.2` | `c291e7961a` | 2026-09-12 | tag `v1.0.6` | 补 `summary`（官方教程的市场页简介位） |
| `1.0.7` | `dsh-v0.1.5-rc.2` | `c291e7961a` | 2026-09-12 | tag `v1.0.7` → commit `0301fd6` | 把三个平台生成物 `skill-card.md` / `_icon.png` / `_meta.json` 全部移出发布目录（ClawHub 明确拒收 `skill-card.md`）；版本号落点由「三处」收敛为**只有 `SKILL.md` 一处** |
| `1.0.8` | `dsh-v0.1.5-rc.2` | `c291e7961a` | 2026-09-13 | tag `v1.0.8` | 新增英文门面 `README.en.md`，并把 `README.md` 重写为「从入门到进阶」的完整安装与使用文档；「仓库专用文件」由 4 个增至 5 个，5 处排除清单同步 |
| `1.0.9` | `dsh-v0.1.5-rc.2` | `c291e7961a` | 2026-09-13 | tag `v1.0.9` | 按 ClawHub 安全审计修模板供应链缺陷（MCP 示例 pin 精确版本 + 补凭据作用域警告）；文件头注释改叙述式引用块；被命中的引用块叙述化 |
| `1.0.10` | `dsh-v0.1.5-rc.2` | `c291e7961a` | 2026-09-14 | tag `v1.0.10` | 资源层可装载性修复：`description` 1032→972；casebook 18 处跨方向重复编号加方向前缀消除检索歧义；9 个大引用文件插「本文件导航」块声明整理稿/素材边界；`SKILL.md` 资源索引重写为含「触发条件/读法/装载成本」的加载路由表；**拆册**——素材 A~D 拆 `10a`~`10d`、E/H 拆 `02b`/`02c`（逐行搬迁、零删除），`references/` 17→23 篇 |
| `1.0.11` | `dsh-v0.1.5-rc.2` | `c291e7961a` | 2026-09-15 | tag `v1.0.11` | **开源许可整改**：`10b` 文件头补许可警示块（修「警示在 A 文件、AGPL 代码在 B 文件」的错位）；`LICENSE` 声明段重写（补 DeepSeek 的 MIT 署名、13 个来源 × 许可 × 落点全表、修正 WeKnora 误标 `NOASSERTION`）；`12` 新增 §9 来源×许可×落点总表 + 两条判读纪律；`README` 双语同步；坑 O1 与模板二的机制类内容**改用官方 MIT 源码溯源**，OpenViking 逐字代码（91 行）改为结构要点 + 出处行号 |
| `1.0.12` | `dsh-v0.1.5-rc.2` | `c291e7961a` | 2026-09-15 | tag `v1.0.12` | **开源 NOTICE 合规补齐**（评审 `oss-fix-guide` P1~P9）：新建根目录 `NOTICE`（Apache-2.0 §4(d)，含 loopx NOTICE 逐字原文 + 13 来源声明，版权行 8/8 从上游正文逐字核取）；新建 `licenses/Apache-2.0.txt`（§4(a)）与 `licenses/MIT.txt`；`.gitattributes` 补 `NOTICE`/`licenses/*.txt` 的 `eol=lf`；`LICENSE` 末段改确定性表述并指向随包 `NOTICE`；`10b` §1.2 清掉 AGPL 逐字转载（英文原文 → 自撰机制描述 + 保留 `文件:行号`）；`README` 双语加第三方许可段；新增验证脚本 `scripts/check_oss_license.sh`（实跑 PASS）。**零删除** |
| `1.0.13` | `dsh-v0.1.5-rc.2` | `c291e7961a` | 2026-09-16 | tag `v1.0.13` → commit `c6af9d5` | 🔴 **引用集合收敛为 {MIT, Apache-2.0, BSD-3-Clause} + Apache-2.0 §4 义务补漏**：AGPL 来源整体移出引用集合（8 条私有实现类坑删除、教训提炼为 8 条自撰建议；坑 O1/O5 保留且出处换为官方 MIT 源码行号；模板二改以官方 `persona` 为载体；`10b` 2074→1931 行）；Apache-2.0 义务补漏——新增 **§0 变更声明（§4(b)，原先没有）**、补转载 **`loopx` 包级 NOTICE（§4(d)）**、**撤回无来源的 MemOS 版权行**、新增 `dsh-web` 逐包许可对照；`check_oss_license.sh` 豁免由「按文件」收紧为「**按显式移除标记**」；**BSD-3-Clause 纳入引用集合**（新增 `licenses/BSD-3-Clause.txt` 逐字取自上游、`NOTICE` 增 §2 BSD 节含无背书条款、声明文件清单 4→5）。**零删除、零 API 断言变更** |

| `1.1.0` | `dsh-v0.1.6-alpha.1` | `0a15e36e7f` | 2026-09-16 | tag `v1.1.0` | 🔴 **基线推进到 0.1.6-alpha.1**（首次吸收官方新 tag；该版含破坏性变更 → **第二段进位**）。① 基线四通道同步（`00-version-gate.md` §1 / `13` §1.5 / `15` §18.2 / commit + annotated tag），并修掉一处既有不一致（巡检状态记的是 tag commit `fb2c4b9e69`，而文档记的是当时检出的 master HEAD `c291e7961a`；本轮起两者统一为 tag commit）；② 探针断言表 **48 → 56 条**（新增 5 正向 `M33`~`M37` + 3 反向 `N06`~`N08`，并改写已失效的 `M11`），**双向实证**：旧 tag 检出 `holds=47 stale=7 skipped=2`（证明新增断言能失败）、新 tag `holds=56 stale=0`；③ 新增 `na:`（内容否定）模式并同步 `.sh` 版，另加断言表一致性校验器（本轮真的抓出两处漂移）；④ `13` 吸收该版全部破坏性变更：§2 新增区间行（PTC 整族改名 / E2B→SSH / `agent/session-start` 删除 / 加载器非事务化 / `tool-ralph` 默认关闭 / `permissionPresets` 与类型改名 / 新增 6 个服务）、**新增 §3.6「加载语义」**、§2.5 补上「本轮 `!:` 命中 0 条」的实测证据；⑤ `08-cheatsheet` 服务表与事件表按新版重取（删 `agent/session-start`、补 6 服务 + 2 事件、标注 `agent/created` 改为 serial）；⑥ `02-templates` / `02b` 的插槽计数改为 77/79/61；⑦ 按用户定调**剔除失效内容与「已失效/已移除」登记簿**（正式发布版只保留正确信息）；⑧ 同步引用仓库（fetch 到最新 + 删除已移出引用集合的 AGPL 仓库本地克隆） |
| `1.2.0` | `dsh-v0.1.6-alpha.2` | `ddefc45fbc` | 2026-09-18 | tag `v1.2.0` | 🔴 **基线推进到 0.1.6-alpha.2**（该版含破坏性变更 → **第二段进位**）。① 基线四通道同步（`00-version-gate.md` §1 / `13` §1.5 / `15` §18.2 / commit + annotated tag）；② **插槽改名 + 换语义**：`settings.plugin.item`（keyed）→ `plugins.item`（list，`id`/`order`/`label`），宿主移到新包 `ui-plugin-manager`，同批新增 `plugins.bundle.config` / `plugins.row.config`；`04` 的注册示例、插槽树、真实范本、AI 提示词同步改写；③ **官方包改名** `@deepseek-ai/cordis-plugin-hmr` → `@deepseek-ai/dsh-hmr`，同一 base 补丁行的 `disabled` / `root` 默认值也变了（`06` 坑 2 整节重写、`02b` 模板同步）；④ base 补丁新增 `plugin-manager` 两行；⑤ **CLI 安装实现搬包**（`apps/cli/src/plugin.ts` 163 → 25 行，逻辑入 `dsh-plugin-manager` 的 `operations.ts`），警告文案删掉结尾括注 —— `05` / `06` / `api-claims` 的引用与引文同步；⑥ **客户端产物契约扩展**（banner 按 chunk 生成、非入口带 `chunk` 字段、分块名 `client.<name>.js`、`require.async`）写入 `14 §17.3`；⑦ 第二批断言 **27 → 39 条**（新增 `B09`/`B10`/`B11`/`U06`/`U07`/`U08`/`P01`~`P05`/`X06`，改写已失效的 `B01`），负向自检 `39/39 STALE`；主探针 56 条对新基线 `holds=56 stale=0`；⑧ 插槽计数按新版重抽为 **81 / 84 / 约 66**（`02` / `02b` / `08` 三处同步）；⑨ ⚠️ **记录一处上游文档滞后**：`docs/cookbook/adding-a-settings-card.zh.md` 在本区间零改动、仍在教旧插槽名，已在 `04 §10.3` 显式标注 |

| `1.3.0` | `dsh-v0.1.7-rc.1` | `46a7f68b09` | 2026-09-23 | tag `v1.3.0` | 🔴 **基线推进到 0.1.7-rc.1**（区间 `ddefc45fbc..46a7f68b09`：**1617** 个提交 / **4** 个新 tag〔版本链 3 个台阶 `0.1.7-alpha.1` / `-alpha.2` / `-rc.1` + 旁线 `dsh-v0.1.5-rc.3` 本区间被后合并进主线〕；**破坏性证据四条 → 第二段进位**：唯一 `!:` 提交 `0dca00b425` 删 activity 平面 / `SESSION_FORMAT_VERSION` 3 → 4 / `installSection` + `SettingsScope` 移除 / base 键 `maxInlineBytes` → `maxInlineTokens`）。① 基线四通道同步（`00-version-gate.md` §1 / `13` §1.5 / `15` §18.2 / commit + annotated tag）；② **会话格式 `SESSION_FORMAT_VERSION` 3 → 4**（迁移包 `dsh-session-format-v3-to-v4`）→ `08` / `13 §3.4`；③ **插槽新增 17、移除 1**：新增 `conversation.header(.leading)` / `.input.activity` / `plugins.bundle.activation` / `plugins.detail.{actions,badge,section}` / `deliverables.{file.actions,review.file.actions}` / `settings.launcher` / `shell.leading` / `sidebar.right.tab.document.{action,actions,unpreviewable}` / `sidebar.workspaces.session.row.action` / `sidebar.workspaces.session.menu.item` / `settings.models.sign-in`；**移除 `conversation.session.header.leading`** → `04` / `08`，计数 81/84/约 66 → **121/123/约 86**（2026-09-23 修好抽取器漏抽后重抽）；④ **工具 DSL 新增 `deferLoading` 与 `projectContent`** → `02` / `03` / `08`；⑤ base 补丁新增 `config-editor` / `authorization` / `deepseek-account` 三行，配置键 `maxInlineBytes` → `maxInlineTokens`；⑥ 官方包增删（+20 / 移除改名 4）；⑦ 区间唯一 `!:` 提交删的是 **activity 平面**，而它在基线端与新版端**都不存在**（旁线先建后删）→ 登记进 `13 §2` 并补强 `§2.5` 的论证；⑧ 第二批断言 **39 → 49 条**（修 4 条判据缺陷型假 STALE：`B08`/`U07`/`P04`/`X04`；新增 `P06`/`P07`/`U09`/`U10`/`V01`/`X07`；**复核补记「设置机制重做」后再加 `U11`/`U12`/`X08`/`X09`**），自检 `49/49` + 正向 `49/49`；主探针 56 条 `holds=56 stale=0`；⑨ 四个脚本内的基线常量同步推进 |
| `1.3.1` | `dsh-v0.1.7-rc.1` | `46a7f68b09` | 2026-09-23 | tag `v1.3.1` | 🔴 **复核轮：修自身缺陷（基线未变 → 只动第三段）**。用户指令「审查内容执行」触发的对抗性复核，查出并修掉 5 项：① **首轮漏掉「上游自带开发 skill 与官方模板」整块面**（`dsh-agent-preset/skills/` 3 个 skill / 15 文件，旧基线无该目录）→ `02b` 末节 + `SKILL.md` 第 8 条 + **SOP §9 补两维**；② **`cordis_inspect what:"client"` 不是可执行工具名**（实为 `cordis_inspect_list` / `_query` / `_self`）→ `04` / `05`；③ **`plugin_manager` 工具未覆盖**；④ **插槽计数低估**（抽取器三处缺陷，修好后 **121 / 123 / 约 86**；delta **新增 17 / 移除 1**，**推翻 1.3.0 行的「净增 15」**）；⑤ **CLI `--dump-config-schema` 未记录 + dump 族变三方互斥** → `06` / `08`。**并纠正我自己的一处错误结论**（「上游无文档」实为搜错树，权威在 `apps/cli/reference/README.zh.md:57-58`） |

| `1.3.2` | `dsh-v0.1.7-rc.2` | `477b4f4205` | 2026-09-25 | tag `v1.3.2` | 🔴 **基线推进到 0.1.7-rc.2**（区间 `46a7f68b09..477b4f4205`：346 个提交 / 1 个新 tag；**本区间无破坏性变更 → 只动第三段**）。① 基线四通道同步（`00-version-gate.md` §1 / `13` §1.5 / `15` §18.2 / commit + annotated tag）；② **反向完备性：API 面零移除** —— 服务 / `defineTool` 工具名 / 事件名三类各用两条独立方法扫两端全集，**移除 0**；只有新增（服务 `schedule` / `shortcuts`、工具 `schedule_update`、事件 `deepseek-account/*` 3 个 + `schedule/changed`）；③ 插槽 **+3 / −0**（`shell.quota-notice`、`sidebar.session.row.hover`、`sidebar.session.row.leading`）→ 计数 121/123/约 86 → **124/126/约 89**，`slot-catalog.ts` 86 → **89**；④ base 补丁 `llm-deepseek` 行的**实现包**换成 `@deepseek-ai/dsh-llm-deepseek-api-key`（**`id` 不变 → 按 id 定位的补丁不受影响**；旧包仍在），新增 `llm-deepseek-account` 行；⑤ 官方包 +5 / 移除改名 0；⑥ 未变项逐条实测：`SESSION_FORMAT_VERSION`=4、配置键无变动、CLI 无新选项、包内 `skills/templates/examples` 清单两端相同、区间 `!:` 0 条；⑦ 修两处**既有**缺陷：`08` 服务表仍列着 rc.1 已移除的 `settingsScope`；`13 §1` 的 0.1.7 三行包数口径与其余 18 行不一致（307 实为两层数法）→ 统一 316/321 并写入口径命令；⑧ 断言数不变（主探针 56 条 stale=0；第二批 49 条 HOLDS 49）；⑨ 四个脚本内嵌基线常量同步推进 |
| `1.3.3` | `dsh-v0.2.0-rc.1` | `4878cdabd8` | 2026-09-29 | tag `v1.3.3` | 🔴 **基线推进到 0.2.0-rc.1**（区间 `477b4f4205..4878cdabd8`：**261** 个提交 / **1** 个新 tag；**本区间无破坏性变更 → 只动第三段**）。① 基线四通道同步（`00-version-gate.md` §1 / `13` §1.5 / `15` §18.2 / commit + annotated tag）；② **反向完备性：API 面零移除** —— 服务名（`extends Service`）移除 **0**、core 事件名增删 **0**；只有新增服务 `DesktopAnalytics`；③ **未变项逐条实测**：`SESSION_FORMAT_VERSION` 仍 **4**、`schema.ts`/`tools/index.ts` 的 blob hash 两端相同（DSL 契约无变动）、模型 ID 仍 `deepseek-flash`、CLI 无新增 `.option(`、插槽 **89 → 89**（计数维持 124/126/约 89）、`packages/AGENTS.md` 未变；④ 官方包 **+4 / 移除改名 0**（`dsh-otel`、`dsh-client-product-analytics`、`dsh-client-ui-settings-session-log`、`dsh-experimental-schedule-bundle`；包数 321 → 325）；⑤ base 补丁 +1 插件行（`otel`）+1 配置键（`maxRequestBytes`），`id:` 行集合两端相同；⑥ 🔴 **六维度之外的「结构性新增」**：上游自带 skill 树 `packages/preset/agent-preset/skills/` **15 → 17 文件 / 3 → 4 个 skill** —— 新增 skill `agent-experience` 与 `packages/preset/agent-preset/skills/cordis-plugin-development/references/user-actions.md`（「一个操作，两个调用者」：UI 动作与 agent 工具共用同一宿主服务方法；授权类动作只能给用户）→ `02b` / `SKILL.md` 同步；⑦ 断言数不变（主探针 56 条 stale=0；第二批 49 条 HOLDS 49）；⑧ **新登记一处既有工具缺陷（非本轮引入）**：`dsh-version-diff.sh` 把主工作树的**过期 HEAD** 当「未发布未来」，多输出一行**方向相反**的假区间 → 已在 `13 §2` 与本节标注「**只读第 1 行**」；⑨ 四个脚本内嵌基线常量同步推进（`dsh-api-probe.py`/`.sh`、`dsh-sync.sh`、`dsh-version-diff.sh`） |
| `1.3.4` | `dsh-v0.2.0-rc.1` | `4878cdabd8` | 2026-09-29 | tag `v1.3.4` | 🔴 **修自身缺陷 + 清过时内容**（**无新 tag、基线未变** → 只动第三段）。① 基线四通道同步（`00-version-gate.md` §1 / `13` §1.5 / `15` §18.2 / commit + annotated tag）；② **引用漂移清零**：新建**引用漂移检查器**（维护工具链脚本，不随技能发布；`--selftest` 7/7）扫 **195 个引用锚点** → 修 **4 处硬错 + 23 条规则**，复检**硬错 0**；③ **三个工具缺陷全修**：`check_repo_layout.py` 不再恒返回 0（已实证 `exit 1`）；`_audit_release_consistency.py` 旧基线改**动态推导**（`--selftest` 4/4）；`_audit_skill_vs_baseline.py` 修活死代码 `CTX_ALLOW_EXTRA`、F 段升级为**唯一硬判据**（`--selftest` 3/3）；④ 清过时内容：`08` 已移除服务行移出活表、`14` 陈旧编辑史注记、`发布准备清单` 加状态头、`scripts/` 清点清单刷新；⑤ 清点器**自指误报**与**自身名字写错**两处缺陷已修；⑥ 断言数与四脚本基线常量不变 |
| `1.3.5` | `dsh-v0.2.0-rc.2` | `639ed01539` | 2026-09-30 | tag `v1.3.5` | 🔴 **基线推进到 0.2.0-rc.2**（区间 `4878cdabd8..639ed01539`：**187** 个提交 / **1** 个新 tag / `!:` **0 条**；**本区间无破坏性变更 → 只动第三段**）。① 基线四通道同步（`00-version-gate.md` §1 / `13` §1.5 / `15` §18.2 / commit + annotated tag）；② **反向完备性：API 面零移除** —— 服务名 **126 → 126** / 事件名 **109 → 109** / `defineTool` 工具名 **55 → 55**，移除数**全为 0**（三类各用独立抽取交叉核对）；③ 插槽 **+1 / −0**：新增 `sidebar.right.tab.files.actions`（`list` / `scope: 'session'`，宿主 `ui-sidebar-files`，`packages/client/ui-sidebar-files/src/client/index.ts:34`）→ 计数 **124/126/约 89 → 125/127/约 90**，`slot-catalog.ts` **89 → 90**；④ **官方包 0 增 0 减**（`package.json` 计数 325 → 325、包名集合两端逐字相同）；base 补丁 blob `9c35ebf5` **两端相同**（`id:` 行与全部配置键零变动）；⑤ **未变项逐条实测**：`SESSION_FORMAT_VERSION` 仍 **4**、`schema.ts`（`5aea4f4f`）/ `tools/index.ts`（`ca89f370`）blob hash 两端相同（DSL 契约无变动）、模型 ID 仍 `deepseek-flash`、CLI 无新增 `.option(`、包内 `{skills,templates,examples}/` 清单 **18 → 18**；⑥ 🔴 **六维度之外的新增面：包内 `Config`**（本区间唯一有内容的一类改动）—— 全树「`Config` 键集合」两端 diff **+3 / −0**：`cordis-host-runner` 新增 `clientInspectTimeoutMs`（默认 `10000` ms，给 `cordis_inspect_*` 客户端查询设界 + 新增「网关无存活页面」预检）、`tool-ask-user` **首次带 `Config`**（`mode: 'legacy' / 'timed'` 默认 `legacy`、`timeout` 默认 `120` 秒）。⚠️ **两处都不在 base 补丁里** → `dsh-version-diff.sh` 的「配置键变动」维度（只扫 base 补丁）**看不见它们**，已登记为继「包内非代码资源」之后**同一类盲区的第二个落点**，并把「全树 `Config` 键集合 diff」列为常规第 7 维；两者**均非破坏性**（`ask_user_question` 工具名、`legacy` 模式参数面与 `ctx` 服务键未变；`timed` 模式新增的 `timeout` 参数 / `pending` 输出分支是**加法**且默认不出现）；⑦ 断言数**不变**（主探针 56 条 `holds=56 stale=0`；第二批 49 条 `HOLDS 49 / STALE 0`，负向自检 49/49）；⑧ 四个脚本内嵌基线常量同步推进（`dsh-api-probe.py`/`.sh` 的 `BASELINE_COMMIT`/`BASELINE_VER`、`dsh-sync.sh` 的 `skillBaseline`、`dsh-version-diff.sh` 的 `BASELINE`）；⑨ **顺手修掉一处既有腐化源**：`SKILL.md`「硬变化」段与 `13 §2.5` 原用「本轮 / 上一轮 / 上上轮」这类**每轮都要整体改写一遍**的相对说法 → 改为**按区间版本号标注** |

> `1.0.1` / `1.0.2` 没有独立提交记录（多档变更合并在 `1.0.3` 那一次提交里），故不单列。**不要为了凑连续性补造条目**——台账只登记能举证的版本。
> **基线 ≠ 技能版本。** `1.0.0`~`1.0.13` 各行的 DSH 基线全是 `dsh-v0.1.5-rc.2`，而技能版本一路走到 `1.0.13` —— 这不是漏更新：三段号进位有两类触发（官方发新 tag，**或**我们修了技能自身缺陷），那 13 次全属后者。**`1.1.0` 起两者第一次同时前进**（新 tag + 破坏性变更）。两个轴，唯一绑定处就是这两张表。

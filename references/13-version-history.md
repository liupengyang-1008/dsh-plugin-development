> **文件来源**：本文件由 DSH 插件开发手册套件整合生成。直接编辑会在下次整合时被覆盖，因此维护性改动记录在工作区源文档中。
> ⚠️ **例外**：§1.5「本 skill 版本 ↔ DSH 基线对照表」是**手工维护**章节（不来自上游手册）。它是本技能自身的版本台账，每次发布都会在此追加一行；若整文件被重新生成，这一节需要人工补回。

> **本文件用途**：按官方 tag 列出 DSH 的版本变化与破坏性变更；说明当目标版本高于本 skill 基线时，如何拉取最新源码并自行刷新这份表。
> **来源**：`deepseek-harness` 仓库 git 历史（**17 个 tag**，17,172 个提交），逐条机器核验。
> **快照警告**：本文件是**冻结快照**（基线 `dsh-v0.1.6-alpha.1` / commit `0a15e36e7f`，2026-09-15）。**下游 tag 一旦发布，本表就落后了**。
> **本 skill 版本 ↔ DSH 基线**：见 **§1.5**。本技能自己的三段版本号与官方基线是**两条独立的轴**，唯一绑定处就是那张表。
> **写代码前先核验**：`bash scripts/dsh-api-probe.sh <DSH 仓库路径>`；版本落后时按本文第 5 节刷新。
> **分级与核验规则**：`references/00-version-gate.md`、逐条登记 `references/api-claims.md`。

> **本文件导航 —— 共 387 行，不要整读。** 先 `grep` 定位小节，再只读需要的那一节。
> - **本文件全是整理稿**（无上游素材混杂），但它仍是基线快照——写代码前先过版本闸门。
> - 常用检索：`grep -n '^## '`（章节）、`grep -n '§1.5'`（技能版本↔基线对照表）

---

## 0. 先说结论（三句话）

1. **DSH 没有 CHANGELOG，也不用 `BREAKING CHANGE:` 页脚**（提交标题与正文里都搜不到 `BREAKING` 字样：各 0 条）。但它**会用 Conventional Commits 的 `type(scope)!:` 标题标记**自报破坏性提交。**两条路必须并用**：`git log --grep='!:'` 抓自报的（便宜但覆盖不全，见第 2.5 节），源码级机器化对比抓「影响插件作者却没标 `!`」的（见第 3 节）。
2. **API 名字长期稳定，但会「整族改名」**：探针的 48 条正向断言里，**基础 43 条**（S 级 6 + M 级 32 + L 级 5）在 0.1.5-rc.2 之前的 16 个 tag 上均为绿；**吸收 0.1.6-alpha.1 时新增的 5 条**（`M33`~`M37`）断言的是该版才出现的事实，**按设计**在更早的 tag 上必然 STALE（对旧 tag 检出跑一次即可自证：`holds=47 stale=7`）。真正的破坏性变更集中在**配置键、官方包名、模型 ID、数据格式版本、宿主方法废弃、加载语义**六类——前四类 `dsh-version-diff.sh` 能直接检出，后两类只能从决策记录（`.agents/notes/`）读。
3. 因此，「防过时」的正确姿势不是背 API 名，而是**盯住这几类 + 每次开工前跑一次探针 + `git log --grep='!:'` 补一路自报变更**。⚠️ 但**不要指望 `!:` 会替你报信**：本轮区间（800 个提交、含整族改名）的 `!:` 命中数是 **0**，见 §2.5。

---

## 1. tag 版本总表

口径说明（**重要，别误读**）：
- 「官方包数」= `packages/**/package.json` 文件数，**含测试夹具**，仅用于看增长趋势，不代表可用包数量。
- 「该版提交数」= 从上一个 tag 到本 tag 的提交数（`git rev-list --count`）。tag 之间不总是线性祖先关系，该数字为近似规模，**不要**当作精确工作量。
- 日期取 tag 创建时间。

| # | tag | 版本 | 日期 | commit | 官方包数 | 该版提交数 |
|---|---|---|---|---|---|---|
| 1 | `dsh-v0.1.0-rc.7` | 0.1.0-rc.7 | 2026-08-17 | `99f6f02fec` | 226 | — |
| 2 | `dsh-v0.1.0-rc.8` | 0.1.0-rc.8 | 2026-08-19 | `141eb6fef8` | 233 | 536 |
| 3 | `dsh-v0.1.1-rc.1` | 0.1.1-rc.1 | 2026-08-21 | `528c682e06` | 234 | 172 |
| 4 | `dsh-v0.1.1-rc.2` | 0.1.1-rc.2 | 2026-08-21 | `b150a551b8` | 234 | 35 |
| 5 | `dsh-v0.1.2-alpha.1` | 0.1.2-alpha.1 | 2026-08-28 | `cd5ef81481` | 254 | **1079** |
| 6 | `dsh-v0.1.2-alpha.2` | 0.1.2-alpha.2 | 2026-08-30 | `0a53fb55be` | 258 | 234 |
| 7 | `dsh-v0.1.2-alpha.3` | 0.1.2-alpha.3 | 2026-08-31 | `dd6322d604` | 257 | 117 |
| 8 | `dsh-v0.1.2-alpha.4` | 0.1.2-alpha.4 | 2026-09-01 | `4e84901e64` | 256 | 297 |
| 9 | `dsh-v0.1.2-alpha.5` | 0.1.2-alpha.5 | 2026-09-02 | `db6bdc3576` | 256 | 6 |
| 10 | `dsh-v0.1.2-rc.1` | 0.1.2-rc.1 | 2026-09-03 | `a66e470204` | 256 | 2 |
| 11 | `dsh-v0.1.3-alpha.1` | 0.1.3-alpha.1 | 2026-09-04 | `d347e70390` | 262 | 328 |
| 12 | `dsh-v0.1.3-alpha.2` | 0.1.3-alpha.2 | 2026-09-07 | `82a5fd61a7` | 265 | 316 |
| 13 | `dsh-v0.1.5-alpha.1` | 0.1.5-alpha.1 | 2026-09-08 | `5dda764ed3` | 272 | 563 |
| 14 | `dsh-v0.1.5-alpha.2` | 0.1.5-alpha.2 | 2026-09-09 | `b2e3b2a012` | 274 | 262 |
| 15 | `dsh-v0.1.5-rc.1` | 0.1.5-rc.1 | 2026-09-10 | `183f08e9c6` | 274 | 17 |
| 16 | `dsh-v0.1.5-rc.2` | **0.1.5-rc.2**（本 skill 基线） | 2026-09-10 | `fb2c4b9e69` | 274 | 4 |
| 17 | `dsh-v0.1.6-alpha.1` | **0.1.6-alpha.1**（本 skill 基线） | 2026-09-15 | `0a15e36e7f` | 290 | 800 |
| — | `master` HEAD（**1.0.x 期间**检出的树） | — | 2026-09-10 | `c291e7961a` | 275 | 139 |

> **为什么还留着下面那行 `master` HEAD**：技能 `1.0.0`~`1.0.13` 期间的核验对象是**当时检出的 master HEAD**（`c291e7961a`），而不是 tag 对象（`fb2c4b9e69`）；从 `1.1.0` 起核验对象改为**tag commit**（`0a15e36e7f`），两者一致。这是历史事实的保留，不是待办。

**从这张表该读出的三件事**：

- **节奏**：17 个 tag 跨 29 天，**平均 1.81 天一个 tag**；rc.2 与 rc.1 在同一天（间隔 4 个提交），而 `rc.2 → 0.1.6-alpha.1` 隔了 5 天、**800 个提交**（本周期第二大区间）。→ 任何写死的版本号都会很快过期。
- **版本号跳跃**：没有 `0.1.4`。`0.1.3-alpha.2` 之后直接是 `0.1.5-alpha.1`。→ **不要假设版本号连续**，也不要用「下一个应该是 0.1.4」这类推理。
- **规模**：`0.1.1-rc.2 → 0.1.2-alpha.1` 一个区间就有 1079 个提交，是本周期最大的变更潮（Code Mode 改名 PTC 就发生在其中）。→ 「一个大版本没有破坏性变更」是错误直觉。

---

## 1.5 本技能版本 ↔ DSH 基线对照表

> **为什么单独列一张表**：本技能自己的三段版本号**不表达**「对应哪个 DSH 版本」，只表达「我们自己改到了什么级别」（约定见 `15-skill-scope-and-maintenance.md` §18.2）。
> 「对应哪条 DSH 线」由此表 + **技能维护侧的巡检状态**（记录 `baseline_tag` / `baseline_commit`；该状态属维护工具链，不随本技能发布）共同记录。**两张表是两个轴，唯一的绑定处就是下面这张。**

口径：
- **DSH 基线** = 本轮更新所依据的官方 tag，等于本技能 `deepseek-harness` 检出的 HEAD（即上表最后一行 `master` HEAD）。
- **基线 commit** = 该 tag 指向的提交对象。
- **git 锚点** = 技能仓库里对应这次发布的提交 / tag。每个技能版本都打一个 **annotated tag**（`v<技能版本>`），**注解里带 DSH 基线与基线 commit** —— 所以 `git tag -n99` 本身就是一份可执行的对照表，不必只依赖本文档。

| 技能版本 | DSH 基线 tag | 基线 commit | 技能日期 | git 锚点 | 变更摘要 |
|---|---|---|---|---|---|
| `1.0.0` | `dsh-v0.1.5-rc.2` | `c291e7961a` | 2026-09-11 | `ba06186`（首提交） | 技能初始化 |
| `1.0.3` | `dsh-v0.1.5-rc.2` | `c291e7961a` | 2026-09-11 | `38d7bc0` | 吸收同类方案素材、重构 `SKILL.md`、修悬空引用（**已推送 GitHub**） |
| `1.0.4` | `dsh-v0.1.5-rc.2` | `c291e7961a` | 2026-09-12 | tag `v1.0.4` | 修 `assets/` 模板缺陷（补 `exports`、工具插件改零构建可运行入口）、建立三段版本号约定、补本对照表 |
| `1.0.5` | `dsh-v0.1.5-rc.2` | `c291e7961a` | 2026-09-12 | tag `v1.0.5` | 补 `SKILL.md` frontmatter 的 `slug` / `displayName`（发布器硬要求，缺则无法发布）；澄清 `_meta.json` 的 `ownerId` 属 ClawHub 侧字段 |
| `1.0.6` | `dsh-v0.1.5-rc.2` | `c291e7961a` | 2026-09-12 | tag `v1.0.6` | 补 `summary`（官方教程的市场页简介位）；确认本技能线上为 1.0.3，本次属版本更新 |
| `1.0.7` | `dsh-v0.1.5-rc.2` | `c291e7961a` | 2026-09-12 | tag `v1.0.7` → commit `0301fd6` | 把三个平台生成物 `skill-card.md` / `_icon.png` / `_meta.json` 全部移出发布目录（ClawHub 明确拒收 `skill-card.md`）；版本号落点由「三处」收敛为**只有 `SKILL.md` 一处** |
| `1.0.8` | `dsh-v0.1.5-rc.2` | `c291e7961a` | 2026-09-13 | tag `v1.0.8` | 新增英文门面 `README.en.md`，并把 `README.md` 重写为「从入门到进阶」的完整安装与使用文档；「仓库专用文件」由 4 个增至 5 个，5 处排除清单同步（含 `dist_consistency.py` 自检夹具覆盖新项） |
| `1.0.9` | `dsh-v0.1.5-rc.2` | `c291e7961a` | 2026-09-13 | tag `v1.0.9` | 按 ClawHub 安全审计修复模板供应链缺陷：MCP 示例改为**精确版本**（`npx … my-mcp-server` → `my-mcp-server@1.2.3`；`uvx` 主包 `ouroboros-ai[mcp]` → `==1.4.0`）并补凭据作用域警告；13 个 `references` 的文件头 HTML 注释改叙述式引用块；被静态扫描命中的引用块第三人称描述改叙述化；速查表凭据行去掉精确文件名 |
| `1.0.10` | `dsh-v0.1.5-rc.2` | `c291e7961a` | 2026-09-14 | tag `v1.0.10` | **资源层可装载性修复**（源自资源层规范评估）：① `description` 由 1032 裁到 **972** 字符，回到 1024 上限内；② `10-community-casebook.md` 的 **18 处跨方向重复编号**加方向前缀（`# 一、…` → `# A · 一、…`），消除「按编号检索跨来源误命中」；③ 9 个大引用文件插入「本文件导航」块，显式声明**整理稿段 / 上游素材段**的边界与 `grep` 定位配方；④ `SKILL.md` 资源索引重写为**含「触发条件 / 读法 / 装载成本」的加载路由表**，并新增「加载纪律」三条（含「禁止为保险通读」）；⑤ **拆册**（用户授权后执行）：素材 A~D 拆为 `10a`~`10d` 四个方向分册、E/H 拆为 `02b`/`02c`，正文逐行搬迁未改写，原文件名保留（`10-*` 转总索引、`02-*` 只留 T1~T12），**零删除**；`references/` 由 17 篇增至 **23 篇** |
| `1.0.11` | `dsh-v0.1.5-rc.2` | `c291e7961a` | 2026-09-15 | tag `v1.0.11` | **开源许可整改**（源自许可审计，三渠道已上架状态下的声明修复）：① `10b` 文件头新增**许可警示块**，逐条列明本册的 AGPL-3.0 / MIT 来源 —— 修补原「**警示在 A 文件、代码在 B 文件**」的错位（`AGPL` 字样原先只出现在 `LICENSE`/`README`/`12`，而实际落点 `10b` 内一次都没有）；② `LICENSE` 第三方声明段重写：补 **DeepSeek 的 MIT 版权署名**（官方逐字引用逾 500 行却零署名）、列出全部 **13 个来源 × 许可 × 落点**、明确「MIT-0 仅覆盖本技能原创内容」、修正 WeKnora 误标的 `NOASSERTION`；③ `12-community-plugins.md` 新增 **§9「来源 × 许可 × 落点」总表** + 两条判读纪律（**许可证只以 LICENSE 正文为准**；Apache-2.0 再分发需保留 NOTICE），并修正 WeKnora 许可；④ `README.md` / `README.en.md` 已知边界同步；⑤ **机制类内容改用官方 MIT 溯源**：坑 O1（persona `complete: true` 丢弃 prompt 段）出处由社区仓库改为官方 `packages/preset/persona/src/index.ts:42-43,52,67` + 官方单测 `system-prompt.spec.ts:380-385`；`10b` 模板二的 OpenViking 逐字代码（91 行）替换为**结构要点 + 出处行号**，并补官方 `persona` 插件（MIT，75 行）作为服务型插件范本。**零删除、零 API 断言变更** |
| `1.0.12` | `dsh-v0.1.5-rc.2` | `c291e7961a` | 2026-09-15 | tag `v1.0.12` | **开源 NOTICE 合规补齐**（源自评审「开源合规修复包」`oss-fix-guide`，P1~P9）：① **新建根目录 `NOTICE`**（133 行）—— 履行 Apache-2.0 **§4(d)**，含 `huangruiteng/loopx` NOTICE 的**逐字原文**、13 个来源的版权/归属声明，**所有版权行均从上游 LICENSE 正文逐字核取**（8/8 仓库实取，无一处凭印象填写）；② 新建 `licenses/Apache-2.0.txt`（§4(a)，Apache 官方全文 11,358 B）与 `licenses/MIT.txt`；③ `.gitattributes` 补 `NOTICE` 与 `licenses/*.txt` 的 `eol=lf`；④ `LICENSE` 末段改为**确定性表述** —— 删掉「Wherever practical」的余地、把「see each project's repository」改为指向**随包 `NOTICE`**、补上 §4(a)/§4(c)/MIT 三处落点；⑤ **`10b` §1.2 清掉 AGPL 逐字转载** —— 坑 O2~O10 的英文原文（文档段落 / 代码注释 / commit 正文）全部替换为**自撰机制描述**并保留 `文件:行号` 定位；「文档线索」原文照抄表替换为自撰机制表；顶部警示块措辞改确定性；⑥ `README.md` / `README.en.md` 新增第三方许可段；⑦ 新增 **§9 验证脚本** `scripts/check_oss_license.sh`（5 项检查，实跑 **PASS**）。**零删除、零 API 断言变更** |

| `1.0.13` | `dsh-v0.1.5-rc.2` | `c291e7961a` | 2026-09-16 | tag `v1.0.13` → commit `c6af9d5` | 🔴 **引用集合收敛为 {MIT, Apache-2.0, BSD-3-Clause} + Apache-2.0 §4 义务补漏**（用户定调：「保留 Apache-2.0 和 MIT 的引用，重整，保持合规前提下的最优实现」）。① **AGPL 来源整体移出**：`10b §1.2` 的社区记忆服务插件（**AGPL-3.0**）整节移出引用集合 —— 8 条私有实现类坑删除、其**通用教训提炼为 8 条自撰建议**保留（知识不丢、来源不再引用）；坑 **O1 / O5 保留**且权威出处换为**官方 MIT 源码行号**（`packages/llm/llm/src/types.ts:105`、`packages/acp/acp/src/updates.ts:82`、`packages/extensions/tool-cordis/src/api-catalog.ts:6111`）；模板二改以**官方 `persona`（MIT）**为载体；`10b` 目录树 / 坑位统计 / 来源索引同步（**2074 → 1931 行**）。② **Apache-2.0 §4 义务补漏（本轮最重要的实质修复）**：新增 **§0 变更声明**（**§4(b)**，原先完全没有）；补转载 **`loopx` 的包级 NOTICE**（**§4(d)** —— 原先只转载仓库根 NOTICE，而技能引用的恰是 `packages/dsh-loopx-plugin/` 内的源码）；**撤回一处无上游来源的版权行**（原写 MemOS「Copyright 2025 - Present MemTensor Research」，实测其 LICENSE 为标准 Apache 样板无版权行、仓库无根 `package.json`、README 亦无版权声明）；新增 `dsh-web` **逐包许可对照**（根 Apache-2.0，但 `packages/dsh-{community-plugins,doctor,plugin-manager}` 为 BSD-3-Clause、资源目录含 **CC BY-NC-SA 4.0**，且技能只引用前者）。③ **审计器收紧**：`check_oss_license.sh` 的 copyleft 豁免由「按文件」改为「**按显式移除标记**」，堵住「该册一向没问题就整册豁免」的静默漏检。④ 同步 `LICENSE` 来源表、`README` 双语、`12` §9 与风险条、`02` / `05` / `11`；⑤ **BSD-3-Clause 纳入引用集合**（用户确认「可以接受，按社区规范采用」）—— 新增 `licenses/BSD-3-Clause.txt`（**逐字取自上游** `zhu1090093659/dsh-web` → `packages/dsh-doctor/LICENSE`，1,521 B）、`NOTICE` 新增 **§2 BSD 3-Clause 节**（版权声明 + 无背书条款 clause 3）并把原 §2/§3/§4 顺延为 §3/§4/§5、`LICENSE` 增 BSD 义务段与「混合许可来源的逐包范围」说明、`check_oss_license.sh` 声明文件清单 4 → **5**、`.gitattributes` 的 `licenses/*.txt` 通配自动覆盖新文件。**零删除、零 API 断言变更** |

| `1.1.0` | `dsh-v0.1.6-alpha.1` | `0a15e36e7f` | 2026-09-16 | tag `v1.1.0` | 🔴 **基线推进到 0.1.6-alpha.1**（首次吸收官方新 tag；该版含破坏性变更 → **第二段进位**）。① 基线四通道同步并修掉一处既有不一致（巡检状态记 tag commit `fb2c4b9e69`、文档记当时检出的 master HEAD `c291e7961a` —— 自本轮起统一为 tag commit）；② 探针断言表 **48 → 56 条**（新增 5 正向 `M33`~`M37` + 3 反向 `N06`~`N08`，改写已失效的 `M11`），**双向实证**：旧 tag 检出 `holds=47 stale=7 skipped=2`、新 tag `holds=56 stale=0`；③ 新增 `na:`（内容否定）模式并同步 `.sh` 版，另加断言表一致性校验器；④ 本文件吸收该版全部破坏性变更（§1 新增 tag 行、§2 新增区间行、**新增 §3.6「加载语义」**、§2.5 补「本轮 `!:` 命中 0 条」实测）；⑤ `08-cheatsheet` 服务/事件表按新版重取；⑥ `02` / `02b` 插槽计数改为 77/79/61；⑦ 按用户定调**剔除失效内容与「已失效/已移除」登记簿**；⑧ 同步引用仓库并在本地删除已移出引用集合的 AGPL 仓库克隆 |

> `1.0.1` / `1.0.2` 无独立提交，不单列。**不要为了凑连续性补造条目** —— 本表只登记能举证的版本。

**怎么读「`1.0.0`~`1.0.13` 的基线一栏全是 `dsh-v0.1.5-rc.2`」**：这不是漏更新。那 13 次版本进位全都属于「修技能自身缺陷」那一档（三段号进位的两类触发之一），基线本就不动。**到 `1.1.0` 才第一次两者同时前进**（官方发新 tag + 该版含破坏性变更 → 第二段进位）。**不要用「技能版本变了，所以基线一定也变了」去推理。**

**新增一行时的动作**（与 `15-skill-scope-and-maintenance.md` §18.2 台账、`git tag -n99` 三处保持一致）：

在本技能仓库里，**一次发布 = 一次提交 + 一个 annotated tag**。tag 的注解必须写明这一版对应的 DSH 基线与基线 commit：

```bash
git tag -a "v1.0.4" -m "v1.0.4 | DSH baseline: dsh-v0.1.5-rc.2 (c291e7961a)"
git tag -n99 v1.0.4        # 复核注解确实带上了基线
```

这样即使本文档没跟上，`git tag -n99` 也能直接读出「技能版本 ↔ DSH 基线」的完整对照。

> **不要在本技能正文里写维护工具链的路径**（巡检状态文件、打包/同步脚本等在用户机器上都不存在）。正文只描述「有这样一份状态、记录了什么」，路径归维护侧文档。

---

## 2. 破坏性变更总表（按 tag 区间，插件作者视角）

**阅读方式**：左侧是你的起点版本，右侧是终点版本。只列**会让现有插件代码/配置失效**的项，不列新增功能。

| 区间 | 破坏性变更 | 证据 |
|---|---|---|
| rc.7 → rc.8 | 官方包移除：`dsh-client-schema-form`、`dsh-client-web-react`（新增 9 包，含 `dsh-client-ui-renderer`、`dsh-file-reference`） | 包名集合 diff |
| rc.8 → 0.1.1-rc.1 | 无破坏性项（新增 `dsh-authorization`） | 包名集合 diff |
| 0.1.1-rc.1 → rc.2 | 无包级变更；图像输入相关 4 条决策被取代（`blank-permission-default-refresh`、`image-dimension-admission-limit`、`request-image-payload-bound`、`direct-deepseek-vision-input` 被移除） | 决策记录 diff |
| **0.1.1-rc.2 → 0.1.2-alpha.1** | ① **Code Mode 改名 PTC**：配置值/插件名/事件名里的 `code`、`code-mode` → `ptc`（**`run_code` 工具名保留不变**）<br>② 官方包移除：`dsh-acp-demo`、`dsh-acp-snapshot`、`dsh-client-runtime`、`dsh-host-apiproxy`、`dsh-sdk-jsonrpc-demo`<br>③ base 补丁新增 8 个插件行（`storage`、`storage-json`、`storage-domain`、`session-projection-cache`、`session-log-deepseek`、`plugin-package-inventory-deepseek`、`deepseek-llm-api-extensions`、`web-fetch-http`）<br>④ 补丁新增 `disabled: true` 与 `patchReload` 语义<br>⑤ 另有 25 个官方包新增（含 `dsh-webhook`、`dsh-webhook-github`、`dsh-util-crypto`、`dsh-util-workspace-path`、`dsh-win32-process` 等）——新增不破坏兼容，此处仅说明本区间规模 | `git diff dsh-v0.1.1-rc.2 dsh-v0.1.2-alpha.1 -- packages/bundle/base/cordis.patch.yml`；`.agents/notes/archived/architecture/2026-08-25-rename-code-mode-to-ptc.md` |
| 0.1.2-alpha.1 → alpha.2 | **`JsonValue` 类型从 `@deepseek-ai/dsh-session` 迁到 `@deepseek-ai/dsh-util-values`**（包拆分）。直接 import 该类型会编译失败 | `git diff dsh-v0.1.2-alpha.1 dsh-v0.1.2-alpha.2 -- packages/core/tools/src/schema.ts`（1 行改动） |
| 0.1.2-alpha.2 → alpha.3 | 包移除：`dsh-agent-spine-demo`、`dsh-session-persistence-sqlite`；新增 `dsh-session-turn-outline` | 包名集合 diff |
| 0.1.2-alpha.3 → alpha.4 | ① **`dsh-tool-subagent-report` 整包移除**，base 补丁中对应行同时删除<br>② `dsh-code-runtime-python` → `dsh-experimental-code-runtime-python`（改名）<br>③ base 补丁 `tool-web` 的 `fetch: false` → `true`（行为默认值翻转） | 包名集合 diff + base 补丁插件行 diff |
| 0.1.2-alpha.4 → alpha.5 | 无包级变更；`schema.ts` / `cordis.patch.yml` 均未变 | 文件 hash 矩阵 |
| 0.1.2-alpha.5 → 0.1.2-rc.1 | 无包级变更 | 文件 hash 矩阵 |
| **0.1.2-rc.1 → 0.1.3-alpha.1** | ① **`SESSION_FORMAT_VERSION` 从 `0` 跳到 `2`** —— 旧 session 日志需经迁移链读取<br>② 首次出现格式迁移包族：`dsh-session-format`、`dsh-session-format-catalog`、`dsh-session-format-v0-to-v1`、`dsh-session-format-v1-to-v2`<br>③ 新增 `dsh-client-file-upload`、`dsh-http-proxy` | `git grep "SESSION_FORMAT_VERSION" <tag> -- packages/core/session/src/*.ts` |
| 0.1.3-alpha.1 → alpha.2 | ① **`tool-str-replace-editor` 插件行从 base 补丁移除**<br>② **配置键改名 `persona` → `personaPrefix`**<br>③ 另有配置键 `maxOutputChars` 被移除<br>④ `cordis.patch.yml` 结构改动 | base 补丁 diff（`- id: tool-str-replace-editor`、`- persona: ''` / `+ personaPrefix: ''`） |
| **0.1.3-alpha.2 → 0.1.5-alpha.1** | ① **`SESSION_FORMAT_VERSION` 从 `2` 升到 `3`**（新增 `dsh-session-format-v2-to-v3`）<br>② 新增侧边栏包族：`dsh-client-ui-sidebar-files`、`-sidebar-right`、`-sidebar-textpreview`、`dsh-client-ui-dockkit`<br>③ 新增 `dsh-client-resources`、`dsh-api-workspace-files` | 同上的 grep + 包名集合 diff |
| 0.1.5-alpha.1 → alpha.2 | ① 包改名：`dsh-client-ui-sidebar-textpreview` → `dsh-client-ui-sidebar-documentpreview`<br>② 新增 `dsh-chunked-list`、`dsh-tool-present` | 包名集合 diff |
| **0.1.5-alpha.2 → rc.1** | ① **模型 ID 改名：`deepseek-v4-flash` → `deepseek-flash`** —— 写死旧 ID 的配置会失效<br>② base 补丁 `cordis.patch.yml` 改动 | `git grep "^\s*model:" <tag> -- packages/bundle/base/cordis.patch.yml` |
| 0.1.5-rc.1 → rc.2 | 无包级变更 | 文件 hash 矩阵 |
| rc.2 → HEAD（`c291e7961a`，1.0.x 期间的检出树） | 新增 `dsh-remote-mock`；**交付 `Session.eventAt()` / `snapshotEvents()` / `ownEvents()` 正式废弃**（新调用被 lint 拒绝） | `.agents/notes/implemented/architecture/2026-09-09-deprecate-synchronous-session-event-reads.md` |
| **0.1.5-rc.2 → 0.1.6-alpha.1** | ① **执行能力整族改名（不留别名）**：服务 `ctx.codeRuntime` → `ctx.ptcRuntime`；包族 `dsh-code-runtime` / `-worker-thread` / `dsh-experimental-code-runtime-python` → `dsh-ptc-runtime` / `-node` / `dsh-experimental-ptc-runtime-python`；类型 `CodeRuntime` / `CodeSdkLanguage` / `CodeRun*` / `CodeBinding*` / `CodeJsonValue` → 对应的 `Ptc*`。**`run_code` 工具名与其 `code` 参数保留不变**<br>② **E2B 执行后端整体移除**：`dsh-e2b` / `dsh-fs-e2b` / `dsh-subprocess-e2b` 三包与 SDK 依赖被删；新增 **POSIX SSH 家族** `dsh-ssh` / `dsh-fs-ssh` / `dsh-subprocess-ssh` / `dsh-sandbox-ssh`（服务 `ctx.ssh`）<br>③ **事件 `agent/session-start` 被删除**；`agent/created` 由 `emit` 改为 **`serial`**（监听器被 `await`，抛错会让 agent 创建失败）；`agents` 服务新增 `announce(agent, source, signal)`，`register(agent)` 的返回值语义变化<br>④ **加载器不再事务化**：`EntryGroup.update()` 删掉重复 `id` 的校验、`EntryTree.await()` 不再拒绝失败的 fiber、应用失败**只写日志不回滚** —— 由此 `Loader.create()` 返回 **≠** 插件已激活<br>⑤ base 补丁：`workflow-worker-thread` 行拆成 `ptc-runtime` + `workflow-ptc`；新增 `image-offload`、`mcp-resources` 两行；**`tool-ralph` 改为 `disabled: true`**（默认不再发该工具；`ptc` preset 同时禁用 `workflow-ptc`）<br>⑥ 类型改名：`AssistantProvenance` → `AssistantProviderMetadata`、`SessionTitleModelProvenance` → `SessionTitleModelIdentity`、`ImageRequestPolicy` → `ImageRequestTarget`<br>⑦ `permissionPresets` 的 `selectFor()` 与类型 `KnobState` / `PermissionSelect` 移除，改为 `catalog()` / `registerAuto()`，并新增事件 `permission-presets/catalog-changed`；`sandbox.confine()` 与 `shell.start()` 改为异步<br>⑧ 新增能力面：服务 `ctx.browserUse` / `ctx.computerUse` / `ctx.mcpResources` / `ctx.terminalController` / `ctx.ssh`；事件 `compaction/summary-error`（waterfall）；`sessions.registerMessageProjection()` 与 `workspaceRegistry.unarchiveSession()` | `bash scripts/dsh-version-diff.sh <repo> --baseline dsh-v0.1.5-rc.2`；决策记录 `.agents/notes/implemented/{{simplification/2026-09-09-nontransactional-loader.md,architecture/2026-09-12-ptc-runtime-vocabulary.md,simplification/2026-09-11-remove-e2b-providers.md,architecture/2026-09-11-posix-ssh-runtime.md,simplification/2026-09-12-ralph-off-in-shipped-defaults.md}}` |

---

## 2.5 作者自报的破坏性变更（`type(scope)!:` 标记）—— 便宜，但覆盖不全

DSH 用 Conventional Commits，**作者自己认为破坏性的提交会在标题里带 `!`**。可以直接检索：

```bash
git -C <repo> log --oneline --grep='!:' <旧tag>..<新tag>
```

**基线前的 tag 链上只有这 7 条；本轮新增区间（`dsh-v0.1.5-rc.2 → dsh-v0.1.6-alpha.1`）再多 0 条：**

| 区间 | commit | 提交标题 |
|---|---|---|
| 0.1.1-rc.2 → 0.1.2-alpha.1 | `fd7f2065b2` | `refactor(apiproxy)!: remove settings and credentials RPCs` |
| 0.1.1-rc.2 → 0.1.2-alpha.1 | `6e4087626d` | `refactor(apiproxy)!: remove directory-picker RPCs` |
| 0.1.2-alpha.2 → alpha.3 | `4553c9d957` | `refactor(session)!: remove SQLite persistence backend` |
| 0.1.2-alpha.3 → alpha.4 | `27bf1039db` | `refactor(session)!: distinguish event seqs from log offsets` |
| 0.1.2-rc.1 → 0.1.3-alpha.1 | `f99b06eaed` | `feat(session)!: embed assistant streams in format v2` |
| 0.1.2-rc.1 → 0.1.3-alpha.1 | `d1521ea783` | `feat(session)!: add released format migration` |
| 0.1.2-rc.1 → 0.1.3-alpha.1 | `bec6805d6a` | `refactor(session-persistence)!: handle-based seam with a lifecycle-owned write path` |

用 `--all` 会多出 14 条（分布在 tag 祖先链之外的 master 与其他分支上），例如 `d4ccfbd80f refactor(cli)!: complete app-owned profile startup`、`f32aa54aeb feat(cli)!: make dsh run the headless entrypoint`。**评估某个区间的影响时用 `<旧tag>..<新tag>`；`--all` 只适合看仓库全貌。**

**本轮（0.1.5-rc.2 → 0.1.6-alpha.1，800 个提交）的实测结果：非 merge 提交里带 `!:` 的 —— 0 条。**

```bash
git -C <repo> log --oneline --no-merges --grep='!:' dsh-v0.1.5-rc.2..dsh-v0.1.6-alpha.1   # 输出为空
```

（唯一被 `--grep` 命中的是一条 merge 提交 —— 命中的是它的**正文**，不是标题。）而这一版恰恰包含
本周期最狠的一次改名：把整个执行能力族从 `code-runtime` 换成 `ptc-runtime`，**服务名、包名、类型名一起换、不留别名**。
承载它的提交标题是：

```
7c9bb5914c refactor(ptc): align runtime packages and services with PTC naming
```

它用的是 `refactor(ptc):` —— **没有 `!`**。这条实测把 §2.5 的论点从「推断」变成了「证据」：
**`!` 标记与「会不会打坏插件」之间没有可靠相关性，只靠它必然漏。**


### 为什么不能只依赖这条路

拿它和第 2 节的表对照，会发现**「带 `!`」与「真正会打坏插件」几乎不重合**：

| 第 2 节里杀伤力最大的几条 | 带 `!` 吗 |
|---|---|
| 配置键 `persona` → `personaPrefix` | ❌ |
| 模型 ID `deepseek-v4-flash` → `deepseek-flash` | ❌ |
| 官方包移除（`dsh-client-schema-form`、`dsh-tool-subagent-report` …） | ❌ |
| `dsh-code-runtime-python` 改名 | ❌ |
| `SESSION_FORMAT_VERSION` **0 → 2** | ✅（区间内有 3 条 `!` 提交） |
| `SESSION_FORMAT_VERSION` **2 → 3** | ❌（该区间一条 `!` 都没有） |

最后两行最能说明问题：**同一个维度，一次带了标记、一次没带。** 所以任何「只看 `!`」或「只看源码对比」的做法都会漏。

原因也直白：**`!` 是作者对自己那一层的判断**（「我改了 RPC 签名」），而**插件作者的痛点发生在配置层与包名层**（「我 `inject` 的那个包没了」）——两个视角不重合。

> ✅ **正确做法：两条都跑，取并集。** `--grep='!:'` 抓这 7 条自报的，`dsh-version-diff.sh` 抓六个维度（含配置键变动）。
> ⚠️ 另外注意：`git log --grep` 默认是**基本正则**，且匹配的是**子串**。要匹配 `type(scope)!:` 这种带 scope 的形式，用 `--grep='!:'` 最稳；写 `--grep='^refactor!'` 会漏掉 `refactor(cli)!:`（scope 在中间）。

---

## 3. 破坏性变更的高频维度（这才是要盯的地方）

按对插件作者的实际杀伤力排序。**前四类已被 `dsh-version-diff.sh` 做成自动检出**（官方包增删改名 / base 补丁插件行 / 配置键变动 / 模型 ID / 会话格式版本 / 文件 hash），第五类（宿主方法废弃）需读 `.agents/notes/` 下的决策记录。

**先说一个反直觉的观察**：本周期内改动最频繁的接口文件是 `packages/core/tools/src/index.ts`（`defineTool` 所在），16 个 tag 里**有 7 个区间改过它**；`packages/core/tools/src/schema.ts`（参数 DSL）只改过 1 次。但**这两个文件的导出符号名从头到尾没变**——变的是内部实现与类型细节。

所以两个方向都不能靠直觉：

- **别用「文件变了」推断「API 变了」**——要看 diff 才能确认。
- **也别用「API 名还在」推断「用法没变」**——名字稳定恰恰掩盖了语义变化（本周期最典型的例子就是 `persona` → `personaPrefix`，键名变了但没有任何符号消失）。

正确姿势：**符号存在性用探针批量核验，语义正确性用类型检查 + 真实运行验证（见 `05-pitfalls.md` 的坑 P2「手搓测试不算数」）。**

### 3.1 配置键改名（最难排查）

**症状**：插件装上了、`--dump-config` 里也有，但配置值不生效、或宿主启动报 schema 校验失败。

**已发生的实例**：
- `persona` → `personaPrefix`（0.1.3-alpha.2）
- 模型 ID `deepseek-v4-flash` → `deepseek-flash`（0.1.5-rc.1）

**为什么难查**：改的是**字符串值**，不是符号，所以编译不会报错，grep 类型定义也找不到。只有在运行期配置解析失败时才暴露。

**怎么防**：改任何 `config:` 里的键名前，先跑 `--dump-config` 看宿主自己用的名字；不要从旧文档或旧 issue 抄配置片段。

### 3.2 官方包改名/移除

**症状**：`import` 报「找不到模块」，或 `package.json` 依赖装不上。

**已发生的实例**（部分）：`dsh-client-runtime`、`dsh-host-apiproxy`、`dsh-tool-subagent-report`、`dsh-session-persistence-sqlite`、`dsh-agent-spine-demo`、`dsh-code-runtime-python`。

**规律**：官方倾向把还在试验中的包加上 `experimental-` 前缀（如 `dsh-experimental-ptc-runtime-python`），把 demo 类包直接删除。**别依赖名字里带 `demo` 或没有 `experimental-` 的试验性包。**

> ⚠️ 这条规律本轮再次应验，且**换名比加前缀更狠**：整个执行能力族从 `code-runtime` 改成 `ptc-runtime`（服务名 / 包名 / 类型名一起换、不留别名）。**所以「包名」和「服务名」都要当易变事实对待。**

### 3.3 模型 / 供应商 ID

**已发生的实例**：`deepseek-v4-flash` → `deepseek-flash`。

**规律**：模型 ID 会随供应商侧调整而变。**不要把模型 ID 写死在插件默认值里**，或者至少写进 `Config` 让用户可覆盖。

### 3.4 会话/持久化数据格式版本

**已发生的实例**：`SESSION_FORMAT_VERSION`：`0`（rc.7 ～ 0.1.2-rc.1）→ `2`（0.1.3-alpha.1）→ `3`（0.1.5-alpha.1 起）。

**为什么重要**：这是**已落盘用户数据**的兼容性问题。官方会配套发布 `dsh-session-format-v0-to-v1` 之类的迁移包，但**格式版本一旦前进就不会回退**（官方原文：`Never lower it on the development trunk`）。

**给插件的启示**：如果你的插件自己往 session 目录写数据，**必须自己带版本号**，别指望宿主替你迁移。

### 3.5 宿主方法废弃

**已发生的实例**：`Session.eventAt()`、`Session.snapshotEvents()`、`Session.ownEvents()` 被正式废弃（2026-09-09），官方立场是：

> 现有逻辑可以暂不迁移，但**禁止新调用**；也**禁止**新增暴露同样同步历史访问的别名或包装。

**怎么防**：跑 `pnpm exec tsc --noEmit` 或宿主的 lint；官方自带 `typescript/no-deprecated` 规则，废弃调用会带行级 waiver，你的新代码不该有 waiver。

### 3.6 加载语义（0.1.6-alpha.1 新出现的一类）

**症状**：插件「装上了」但没生效；日志里只有一条 `error`，进程不退出，`--dump-config` 里那行也还在。

**已发生的实例**：0.1.6-alpha.1 把 vendored loader 从**事务化**改回**非事务化**（决策记录
`.agents/notes/implemented/simplification/2026-09-09-nontransactional-loader.md`）：

- `EntryGroup.update()` 删掉了重复 `id` 的 `TypeError` 校验 —— 同 id 两行互相覆盖（后者胜），**不再报错**；
- `EntryTree.await()` 只等待、**不再拒绝**失败的 fiber；
- `Entry.update()` 失败**只写日志**：不恢复上一份配置、不删除失败的那一行。

**为什么难查**：它把「启动即崩」换成了「启动成功但你什么都没得到」——**错误从抛异常降级成一行日志**。
`Loader.create()` 返回也**不再**代表插件已激活。

**怎么防**：① 装完插件先 `--dump-config` 确认那行在树里，**再翻启动日志有没有 `error`**（别只看进程起没起来）；
② 自己的启动路径若依赖「某插件必须已激活」，**必须显式审计**，不能靠 `await` 的结果推断；
③ **不要再用重复 `id` 表达「覆盖」** —— 那已不是受支持的语义（要做覆盖请改 patch 行，不要写两行同 id）。



---

## 4. 历史大改名台账（早于首个 tag，已固化，但你可能撞见旧资料）

2026-08-11 官方做了一次**仓库级重命名**，理由是「发布前的窗口期让改名很便宜；留着弱名字会把偶然词汇变成兼容契约」。官方明确声明：

> **No alias, compatibility package, duplicate service key, dual event name, or fallback parser remains. The repository rejects the old name.**
> （不留别名、不留兼容包、不留双事件名、不留回退解析器。仓库拒绝旧名。）

**这就是为什么你在网上看到的旧教程会直接失效。** 摘录与插件作者最相关的部分：

| 旧名 | 新名 |
|---|---|
| `ctx.bash`、`@deepseek-ai/dsh-bash` | `ctx.shell`、`@deepseek-ai/dsh-shell` |
| `BASH_SETTINGS_NAMESPACE`、设置命名空间 `bash` | `SHELL_SETTINGS_NAMESPACE`、设置命名空间 `shell` |
| `@deepseek-ai/dsh-bash-env`、`ctx.bashEnv` | `@deepseek-ai/dsh-shell-env`、`ctx.shellEnv` |
| `packages/pty/`、`ctx.pty`、`PtyService` | `packages/terminal/`、`ctx.terminals`、`TerminalSessionService` |
| `@deepseek-ai/dsh-tool-pty` | `@deepseek-ai/dsh-tool-terminal` |
| `packages/tasks/`、`ctx.tasks`、`TaskService` | `packages/jobs/`、`ctx.jobs`、`JobRegistry` |
| 模型工具 `task_output` / `task_list` / `task_kill` | `job_output` / `job_list` / `job_kill` |
| `TaskView`、wire 帧 `session/tasks` | `JobView`、wire 帧 `session/jobs` |
| `@deepseek-ai/dsh-client-ui-task` | `@deepseek-ai/dsh-client-ui-jobs` |
| `@deepseek-ai/dsh-client-ui-slash` | `@deepseek-ai/dsh-client-ui-input-trigger` |
| `ctx.slash`、`SlashService`、`SlashController` | `ctx.inputTriggers`、`InputTriggerService`、`InputTriggerController` |
| `@deepseek-ai/dsh-agent-tool-mode`、插件 `tool-mode` | `@deepseek-ai/dsh-agent-tool-presentation`、插件 `tool-presentation` |
| `@deepseek-ai/dsh-permission`、`ctx.permission` | `@deepseek-ai/dsh-permission-presets`、`ctx.permissionPresets` |
| `@deepseek-ai/dsh-user-interaction`、`ctx.userInteraction` | `@deepseek-ai/dsh-user-questions`、`ctx.userQuestions` |
| `ToolRegistry` | `ToolRuntime` |
| `@deepseek-ai/dsh-workspace-context`、`context/workspace-context/` | `@deepseek-ai/dsh-agent-instructions`、`context/agent-instructions/` |
| Host `ctx.workspace` | Host `ctx.workspaceRegistry` |
| `ctx.telemetry`、抽象 `Telemetry` | `ctx.sessionTelemetry`、`SessionTelemetryBackend` |
| 事件 `telemetry/record` | `session-telemetry/record` |
| `@deepseek-ai/dsh-lsp-local` | `@deepseek-ai/dsh-lsp-stdio` |
| `@deepseek-ai/dsh-jsonrpc` | `@deepseek-ai/dsh-sdk-jsonrpc-server` |
| `@deepseek-ai/dsh-user-id`、`session/user-id/` | `@deepseek-ai/dsh-anonymous-user-id`、`identity/anonymous-user-id/` |
| `@deepseek-ai/dsh-type-meta`、`typert/type-meta/` | `@deepseek-ai/dsh-typert-protocol`、`typert/protocol/` |
| `TypeRT*` / `typeRT*` 标识符 | `Typert*` / `typert*` |

**注意 `ctx.workspace` 那条的特殊性**：Host 侧改成 `ctx.workspaceRegistry`，而 Client 侧 `ctx.workspaces` 保持不动——因为两者类型不兼容，但**声明合并到同一个 Cordis `Context` 接口**。这是「同名不同面」的经典陷阱，写插件时如果同时 import Host/Client 类型要特别小心。

**还有一条重要的「没改」清单**（别以为它们也改了）：`ask_user_question` 工具名、`@deepseek-ai/dsh-tool-ask-user`、`run_code`、`WorkspaceRegistry` 类名、`workspace.*` wire 名、`Bash`/`Pwsh`/`JSON-RPC`/`SQLite`/`JSONL`/`OpenTelemetry` 等机制限定词。

---

## 5. 当你的目标版本 > 本 skill 基线时：更新流程

这是本节要解决的问题——**不要凭记忆猜新版本改了什么**。

### 5.1 决策树

```
你的目标 DSH 版本 = 本 skill 基线（0.1.5-rc.2）？
├─ 是 → 直接用本 skill 的模板与速查表，跑一次探针确认即可。
└─ 否（更高、或你不确定）→ 走「拉源码 → 出差异 → 决定影响」
   ├─ 能联网 → 运行 scripts/dsh-sync.sh（见 5.3），把源码拉到 skill 目录内
   ├─ 不能联网 → 走 5.4「离线降级」
   └─ 拉取成功 → 运行 scripts/dsh-version-diff.sh 得到「相对基线的真实差异」
```

### 5.2 两条硬规则

1. **拉取前必须由开发者确认。** 首次克隆约 200 MB（`.git` 约 190 MB + 工作树）。脚本会先打印目标路径、预计体积、来源 URL，向你确认后才动手；`--yes` 可跳过交互。
2. **拉下来的源码是「引用源」，不是「依赖」。** 它只用于核验 API、查变更历史。**不要**在插件工程里 `import` 它，也不要在 skill 目录里 `pnpm install` 它。

### 5.3 标准更新流程（联网）

```bash
# 第 1 步：把源码拉进 skill 目录（首次会问你要不要继续）
bash ~/.workbuddy/skills/dsh-plugin-development/scripts/dsh-sync.sh

# 第 2 步：对拉下来的源码核验本 skill 的 56 条断言（48 正向 + 8 反向）
bash ~/.workbuddy/skills/dsh-plugin-development/scripts/dsh-api-probe.sh \
     ~/.workbuddy/skills/dsh-plugin-development/vendor/dsh-src

# 第 3 步：生成「基线 → 最新」的真实差异（新 tag、包增删、模型名、会话格式版本）
bash ~/.workbuddy/skills/dsh-plugin-development/scripts/dsh-version-diff.sh
```

第 3 步会输出一份 Markdown 片段。**把它贴到本文件第 2 节表格的末尾**，你就完成了一次「skill 自身的版本刷新」。

### 5.4 离线降级（拉不到源码时）

**允许继续工作，但必须遵守**：

1. 显式声明「以下 API 名未对当前版本核验」。
2. S 级骨架照给；M/V 级符号单独列成「**需你确认**」清单，不要混在正文里。
3. **禁止**把未核验事实写成肯定句。
4. 交付物带一行基线注释：`// DSH 插件 · 依 dsh-api-probe.sh 对 0a15e36e7f 核验通过`。
5. **绝不允许编造 API 名填补空白**——查不到就说查不到。

### 5.5 目录约定

```
~/.workbuddy/skills/dsh-plugin-development/
├── SKILL.md
├── references/          ← 知识快照
├── scripts/
│   ├── dsh-api-probe.sh      ← 核验 56 条断言（48 正向 + 8 反向）
│   ├── dsh-sync.sh           ← 从 GitHub 拉/更新源码
│   └── dsh-version-diff.sh   ← 出「基线 → 最新」差异
├── assets/              ← 可直接复制的骨架
└── vendor/
    ├── dsh-src/         ← ★ 拉下来的 DSH 源码（git 仓库，可增量 fetch）
    └── dsh-state.json   ← 同步状态：时间 / commit / tag / 探针结果
```

`vendor/dsh-src/` 是一个**真实的 git 仓库**，所以后续更新是增量的（`git fetch`），不会重复下载 200 MB。

---

## 6. 怎么自己复现这张表（不信任本文件时）

```bash
# 所有 tag（按时间序）
git for-each-ref --sort=creatordate --format='%(refname:short)|%(creatordate:iso-strict)|%(objectname:short)' refs/tags

# 每个 tag 的版本号
for t in $(git tag | sort -V); do printf "%-22s " "$t"; git show "$t:package.json" | grep -m1 '"version"'; done

# 会话格式版本历史
for t in $(git tag | sort -V) HEAD; do printf "%-22s " "$t"; \
  git grep -h "SESSION_FORMAT_VERSION *=" "$t" -- 'packages/core/session/src/*.ts'; done

# 模型 ID 历史
for t in $(git tag | sort -V) HEAD; do printf "%-22s " "$t"; \
  git grep -h "^\s*model:" "$t" -- 'packages/bundle/base/cordis.patch.yml' | tr -d ' '; done

# 官方包增删（逐区间）
#   见 scripts/dsh-version-diff.sh 的实现

# 配置面插件行增删（逐区间）
#   git grep -h -- "- id: " <tag> -- packages/bundle/base/cordis.patch.yml

# 作者自报的破坏性变更（注意：覆盖不全，只抓标题带 ! 的，见第 2.5 节）
git log --oneline --grep='!:' <旧tag>..<新tag>

# 配置键变动（base 补丁里的插件特有键名集合 —— 这是 persona→personaPrefix 那类改名的检出方式）
A=$(mktemp); B=$(mktemp)
for spec in "旧 <旧tag>" "新 <新tag>"; do
  set -- $spec
  git show "$2:packages/bundle/base/cordis.patch.yml" \
    | grep -oE '^[[:space:]]+[a-zA-Z_][a-zA-Z0-9_]*:' | tr -d ' :' \
    | grep -vxE 'name|config|id|disabled|plugin' | sort -u > "$A.$1"
done
comm -13 "$A.旧" "$A.新"   # 新增键
comm -23 "$A.旧" "$A.新"   # 移除 / 改名键
rm -f "$A.旧" "$A.新"
```

**矩阵化核验**（判断「哪个 tag 让哪条 API 断言翻转」）：

```bash
bash <skill>/scripts/dsh-tag-matrix.sh <DSH 仓库路径> out.tsv
```

该脚本对 16 个 tag + HEAD 逐条核验 30 条断言，输出 TSV 矩阵。**本文件第 2 节的结论就是用它 + 上述命令交叉验证得出的。**

---

## 7. 已知局限（诚实声明）

1. **「破坏性变更」不等于「全部变更」。** 本表只列会让现有代码/配置失效的项。每个区间还有几十到上百条新功能与内部重构，**不在此列**——需要全量时请用第 6 节的命令自行生成。
2. **包名集合的 diff 口径是 `packages/*/*/package.json`**，不含 `vendor/` 与 `native/`。vendor 目录的改名另见 `docs/rescope.md`（`cordis` → `@deepseek-ai/cordis` 等 9 个供应商包）。
3. **决策记录的「新增」包含目录迁移**（`proposed/` → `implemented/` → `archived/`），不全是新决策。我用 basename 比较以降低噪声，但仍可能高估。
4. **区间提交数不可当成工作量**：tag 之间不总是线性祖先关系。
5. **`HEAD` 行不是发布版本**，只是我拉取时的 master 快照（2026-09-10）。它比 `rc.2` 多 139 个提交，但**没有 tag，不保证稳定**。
6. **本文所有行号级引用都会漂移**；核验请按符号名 grep。
7. **官方文档存在两处内部矛盾**，本 skill 已选定立场，见 `11-glossary-and-provenance.md`。

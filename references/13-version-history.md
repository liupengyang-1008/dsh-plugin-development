<!-- 本文件由 DSH 插件开发手册套件整合生成，请勿手工编辑；改动请回到工作区源文档。 -->
<!-- ⚠️ 例外：§1.5「本 skill 版本 ↔ DSH 基线对照表」是**手工维护**章节（不来自上游手册）。
     它是本技能自身的版本台账，必须随每次发布同步追加一行；若整文件被重新生成，须人工补回本节。 -->

> **本文件用途**：按官方 tag 列出 DSH 的版本变化与破坏性变更；说明当目标版本高于本 skill 基线时，如何拉取最新源码并自行刷新这份表。
> **来源**：`deepseek-harness` 仓库 git 历史（16 个 tag，16,511 个提交），逐条机器核验。
> **快照警告**：本文件是**冻结快照**（基线 `v0.1.5-rc.2` / commit `c291e7961a`，2026-09-10）。**下游 tag 一旦发布，本表就落后了**。
> **本 skill 版本 ↔ DSH 基线**：见 **§1.5**。本技能自己的三段版本号与官方基线是**两条独立的轴**，唯一绑定处就是那张表。
> **写代码前先核验**：`bash scripts/dsh-api-probe.sh <DSH 仓库路径>`；版本落后时按本文第 5 节刷新。
> **分级与核验规则**：`references/00-version-gate.md`、逐条登记 `references/api-claims.md`。

---

## 0. 先说结论（三句话）

1. **DSH 没有 CHANGELOG，也不用 `BREAKING CHANGE:` 页脚**（提交标题与正文里都搜不到 `BREAKING` 字样：各 0 条）。但它**会用 Conventional Commits 的 `type(scope)!:` 标题标记**自报破坏性提交。**两条路必须并用**：`git log --grep='!:'` 抓自报的（便宜但覆盖不全，见第 2.5 节），源码级机器化对比抓「影响插件作者却没标 `!`」的（见第 3 节）。
2. **API 名字层面意外地稳定**：43 条正向 API 断言（S 级 6 + M 级 32 + L 级 5）在全部 16 个 tag 上均为绿。真正的破坏性变更发生在**配置键、官方包名、模型 ID、数据格式版本、宿主方法废弃**这五类——其中前四类 `dsh-version-diff.sh` 能直接检出，第五类只能从决策记录（`.agents/notes/`）读。
3. 因此，「防过时」的正确姿势不是背 API 名，而是**盯住这几类 + 每次开工前跑一次探针 + `git log --grep='!:'` 补一路自报变更**。

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
| — | `master` HEAD | — | 2026-09-10 | `c291e7961a` | 275 | 139 |

**从这张表该读出的三件事**：

- **节奏**：16 个 tag 跨 25 天，**平均 1.56 天一个 tag**；rc.2 与 rc.1 在同一天（间隔 4 个提交）。→ 任何写死的版本号都会很快过期。
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

> `1.0.1` / `1.0.2` 无独立提交，不单列。**不要为了凑连续性补造条目** —— 本表只登记能举证的版本。

**怎么读「基线一栏各行全是 `dsh-v0.1.5-rc.2`」**：这不是漏更新。技能版本从 `1.0.0` 走到 `1.0.8` 而 DSH 基线不动，本身就是「语义同步」这一裁定的直接结果 —— 三段号进位有两类触发（官方发新 tag，**或**我们修了技能自身缺陷），`1.0.4` 之后每次都属于后者。**不要用「技能版本变了，所以基线一定也变了」去推理。**

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
| rc.2 → HEAD | 新增 `dsh-remote-mock`；**交付 `Session.eventAt()` / `snapshotEvents()` / `ownEvents()` 正式废弃**（新调用被 lint 拒绝） | `.agents/notes/implemented/architecture/2026-09-09-deprecate-synchronous-session-event-reads.md` |

---

## 2.5 作者自报的破坏性变更（`type(scope)!:` 标记）—— 便宜，但覆盖不全

DSH 用 Conventional Commits，**作者自己认为破坏性的提交会在标题里带 `!`**。可以直接检索：

```bash
git -C <repo> log --oneline --grep='!:' <旧tag>..<新tag>
```

**基线前的 tag 链上，只有这 7 条：**

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

**规律**：官方倾向把还在试验中的包加上 `experimental-` 前缀（`dsh-experimental-code-runtime-python`），把 demo 类包直接删除。**别依赖名字里带 `demo` 或没有 `experimental-` 的试验性包。**

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

# 第 2 步：对拉下来的源码核验本 skill 的 48 条断言（43 正向 + 5 反向）
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
4. 交付物带一行基线注释：`// DSH 插件 · 依 dsh-api-probe.sh 对 c291e7961a 核验通过`。
5. **绝不允许编造 API 名填补空白**——查不到就说查不到。

### 5.5 目录约定

```
~/.workbuddy/skills/dsh-plugin-development/
├── SKILL.md
├── references/          ← 知识快照
├── scripts/
│   ├── dsh-api-probe.sh      ← 核验 48 条断言（43 正向 + 5 反向）
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

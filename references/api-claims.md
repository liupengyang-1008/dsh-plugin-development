<!-- 手工维护文件。与本文件对应的是 scripts/dsh-api-probe.sh 的断言表 —— 改这里也要改那里。 -->

# API 声明登记表（本 skill 依赖的易变事实）

> **用途**：本 skill 的每一条「关于 DSH 的断言」都登记在这里，标注易变性等级、基线写法、源码位置、核验方式。
> **基线**：commit `c291e7961a` / `0.1.5-rc.2`（2026-09-10）。
> **探针**：`scripts/dsh-api-probe.py`（首选，零 coreutils 依赖）与 `scripts/dsh-api-probe.sh`（备选）。
> **两份探针的断言表必须逐条一致**；被核验的断言数 = **48 条（43 正向 S/M/L + 5 反向 N）**。
> **核验结果（2026-09-11 实测，对基线同 commit 的仓库）**：`total=48 holds=48 stale=0`，`exit 0`。
> **怎么用**：写代码前按 ID 或等级检索；探针 `scripts/dsh-api-probe.sh` 会逐条核验 S / M / L / N 级。
> **四个维度**：S/M/V（易变性，越高越易变）+ **N（极性，否定性论断）**。N 级是本表唯一一类「语义反向」的条目，见第五节。
> **怎么维护**：探针报 STALE → 改本文件对应行 → 同步改探针断言表 → 重跑探针。见 `00-version-gate.md` 第 7 节。

⚠️ **「源码位置」里的行号只记录基线时刻的位置。行号必然漂移，核验时必须按符号名 grep，不要按行号找。**

---

## 一、S 级 · 结构性公理（可直接用）

| ID | 基线写法 / 结论 | 源码位置（基线时） | 核验方式 |
|---|---|---|---|
| S01 | **服务插件**用 default export 导出服务类；**函数式插件**具名导出 `name`/`inject`/`Config`/`apply`，**不得有 default export**。混用会让 Loader 丢弃函数式插件的命名空间 | `packages/AGENTS.md:5` | `grep -n "default-export" packages/AGENTS.md` |
| S02 | 上述规则的完整事故复盘在档 | `docs/postmortem/0001-acp-default-export-drops-inject.md` | 文件存在性 |
| S03 | 服务类继承形态：`class X extends Service`（`Service` 来自 cordis；也可继承领域基类，如 `export abstract class DirectoryPicker extends Service`） | `packages/host/directory-picker/src/index.ts:103` | `grep -rn "extends Service" packages` |
| S04 | **补丁行的书写顺序不影响加载顺序** —— 激活由「服务可用性」驱动 | `packages/bundle/base/cordis.patch.yml`（注释） | `grep -rn "Row order carries no load semantics" packages` |
| S05 | **纯配置组合包**的 `src/index.ts` 只是占位，不承载任何运行时 API | `packages/bundle/base/src/index.ts`（全文 9 行，仅 `export {}`） | `grep -n "export {}" packages/bundle/base/src/index.ts` |
| S06 | 官方 `base` 补丁是 `!!js` 用法的完整范本；**`!!js` 只在 `config:` 与 `disabled:` 内求值**，写在别处**静默失效**（不报错） | `packages/bundle/base/cordis.patch.yml` | `grep -rn "!!js" packages/bundle/base` |
| S07 | **`config` 是整段替换，不是深合并** —— 覆盖时必须重述整个 config | 同上（注释） | `grep -rn "replaces the targeted row" packages` |

---

## 二、M 级 · 接口名（**每次使用前必须核验**）

### 工具（Tools）

| ID | 基线写法 / 结论 | 源码位置（基线时） | 核验方式 |
|---|---|---|---|
| M01 | `defineTool` 从 `@deepseek-ai/dsh-tools` 具名导出 | `packages/core/tools/src/schema.ts` | `grep -rn "export function defineTool" packages` |
| M02 | **`parameters` 的必填写在属性级**：`ParameterPropertySpec = ValueSchemaSpec & { required?: true }`；参数 schema 的根是**隐式开放对象** | `packages/core/tools/src/schema.ts:96-106` | `grep -rn "ParameterPropertySpec" packages` |
| M03 | 属性级写错（值不是 `true`）时的报错文案：`.required must be true when present` | `packages/core/tools/src/schema.ts:292-295` | `grep -rn "required must be true when present" packages` |
| M04 | **裸 `ctx.tools.register` 走标准 JSON Schema，`required` 写在对象级且必须是字符串数组** —— 与 M02 规则相反，套错必报错 | `packages/core/tools/src/schema.ts` | `grep -rn "required must be an array of strings" packages` |
| M05 | `DefineToolOptions` 接口（`name`/`description`/`parameters`/`output{schema,render}`/`timeoutMs`/`isConcurrencySafe`/`execute`…） | `packages/core/tools/src/schema.ts:482-536` | `grep -rn "interface DefineToolOptions" packages` |
| M06 | 注册入口 `ctx.tools.register(...)`；是副作用，卸载时自动注销 | `packages/core/tools/src/schema.ts:570-571` | `grep -rn "tools.register(" packages` |
| M07 | 保留工具名 `run_code` 不可使用 | `docs/subsystems/tools.zh.md:500` 等 | `grep -rn "run_code" packages` |
| M08 | `timeoutMs` 必须是正有限数，否则报 `timeoutMs must be a positive finite number` | `packages/core/tools/src/schema.ts` | `grep -rn "timeoutMs must be a positive finite number" packages` |

### 命令 / 服务 / 插槽 / 事件

| ID | 基线写法 / 结论 | 源码位置（基线时） | 核验方式 |
|---|---|---|---|
| M09 | 命令注册：`ctx.commands.register({...})` | `packages/interaction/...`（`commands.register(` 全仓命中） | `grep -rn "commands.register(" packages` |
| M10 | 服务插件构造函数首行：`super(ctx, '服务名')` | 例 `packages/host/directory-picker-browse/src/index.ts:187` | `grep -rn "super(ctx, '" packages` |
| M11 | 取可选服务用 `ctx.get('名字')`（拓扑无关）；`ctx.x` 仅限已声明 `inject` 的服务 | 全仓 | `grep -rn "ctx.get(" packages` |
| M12 | 副作用回收：`ctx.effect(setup, label)`，setup 返回 disposer | 例 `packages/acp/acp/src/index.ts` | `grep -rn "ctx.effect(" packages` |
| M13 | waterfall 放行约定：`await next()` | 全仓 | `grep -rn "await next()" packages` |
| M14 | UI 插槽 API：`ctx.slots.inject(name, fn)` / `ctx.slots.register({name,...}, 组件)` | 例 `packages/client/ui-chat/src/client/contract/slots.ts` | `grep -rn "slots.\(inject\|register\)(" packages` |
| M15 | 高频插槽名（**基线枚举，非全集**）：`settings.section`、`conversation.view`、`tool.call.toolview` | `packages/bundle/base/cordis.patch.yml`、`packages/client/ui-chat/src/client/apply.ts`、`packages/client/ui-deliverables/src/client/index.ts` | 逐个 grep |
| M16 | Agent 流程事件（waterfall）：`agent/pre-step`（进入 step 前唯一的监听链）、`agent/request`（替换冻结调用配置，不能改消息）、`agent/turn-stopping` | 例 `packages/compaction/compaction-basic/src/index.ts`、`packages/core/agent/src/model-selection.ts` | 逐个 grep |
| M17 | 其它高频事件：`llm/stream`、`system-prompt/assemble`、`approval/request` | `packages/core/agent-loop/src/invariant.ts`、`packages/context/session-reference/src/index.ts`、`packages/api/remotes/src/remote-events.ts` | 逐个 grep |

### 清单 / 加载 / CLI / 路径

| ID | 基线写法 / 结论 | 源码位置（基线时） | 核验方式 |
|---|---|---|---|
| M18 | 组合包清单字段：`"dsh": {"bundle": {"patch": "./cordis.patch.yml"}}` | 各包 `package.json` | `grep -rn "dsh\.bundle" packages` |
| M19 | 缺清单字段时的警告：`declares no dsh.bundle` | `packages/boot/app-boot/src/profile.ts` | `grep -rn "declares no dsh.bundle" packages` |
| M20 | 补丁行 `id` 重复 → **启动即崩**：`TypeError: duplicate loader entry id: <id>` | `vendor/loader/src/config/group.ts:64` | `grep -rn "duplicate loader entry id" vendor` |
| M21 | 补丁内相对路径被**锚定到补丁文件所在目录** | `packages/boot/app-boot/src/index.ts`（`anchorInsertedPluginNames()`） | `grep -rn "anchorInsertedPluginNames" packages` |
| M22 | `dshHomePath()` 路径辅助函数（用于 `!!js` 内） | `packages/boot/app-boot/src/index.ts` | `grep -rn "dshHomePath" packages` |
| M23 | 环境变量 `DSH_HOME` | 全仓 | `grep -rn "DSH_HOME" packages` |
| M24 | 配置树导出开关 `--dump-config` | `apps/cli/README.md`、`packages/boot/app-boot/README.md` | `grep -rn -- "--dump-config" apps` |
| M25 | 插件安装 CLI：`dsh plugin --profile <名字> add <包>`（pnpm 转发器） | `apps/cli/src/plugin.ts` | `grep -rn "dsh plugin" apps` |
| M26 | 子进程凭据清洗：`SENSITIVE_ENV_PATTERN = /KEY\|PASSWORD\|SECRET\|TOKEN/i`，且删除所有 `DSH_*`。**要传的凭据必须在 `env:` 里显式列出** | `packages/subprocess/subprocess/src/index.ts` | `grep -rn "SENSITIVE_ENV_PATTERN" packages` |

---

## 三、V 级 · 实现细节（**故意不做断言**）

这些事实**变化最快**，写进代码会自己坏掉。探针不断言它们——因为一断言就会天天报假警，最后没人信任探针。

| 事实类型 | 基线时刻的值 | 为什么不断言 / 该怎么用 |
|---|---|---|
| 官方斜杠命令清单 | 基线时约 6 个（含 `/compact`、`/permission`、`/plan`、`/goal` 等） | **枚举会增长**。需要用就现场 `grep -rn "commands.register(" packages` 或看 `dsh` 的 `/help` |
| UI 插槽总数与全清单 | 基线时从源码提取到 40 个 | 数量会变。要用就用 M14 的方式现场枚举 |
| `$DSH_HOME` 默认值 | 基线时为 `~/.dsh` | 默认值可被改。要么读 `DSH_HOME` 环境变量，要么运行时确认 |
| profile 目录布局 | `$DSH_HOME/profiles/<名字>/`，已装插件在 `profiles/node_modules/` | 布局可能调整。用 `dsh plugin --profile <名字> ls` 现场确认 |
| 报错文案的细节措辞 | 见 M 级各条 | 只把**关键片段**当断言（如 `duplicate loader entry id`），**不要断言整句** |
| 源码行号 | 本文件记录的均为基线时刻位置 | **行号必然漂移。** 核验只按符号名 grep |
| 各字段默认值（`timeoutMs` 等） | — | 不要假设默认值，显式写出你要的值 |
| 包的内部文件布局 | 如 `src/index.ts`、`src/client/index.ts` | 新建插件时以官方同级包为参照，不要照抄记忆里的路径 |

---

## 四、L 级 · 仓库布局（探测用）

| ID | 结论 | 核验方式 |
|---|---|---|
| L01 | `packages/AGENTS.md` 是官方插件工程约定的入口 | 文件存在性 |
| L02 | `vendor/loader/src/` 是加载器与配置校验实现 | 文件存在性 |
| L03 | `apps/cli/src/plugin.ts` 是插件安装实现 | 文件存在性 |
| L04 | `packages/bundle/base/cordis.patch.yml` 是官方最完整的补丁范本 | 文件存在性 |
| L05 | 顶层布局：`packages/`、`vendor/`、`native/`、`apps/`、`docs/` | 目录存在性 |
| L06 | `docs/postmortem/` 存放事故复盘（0001~0004 已读） | 目录存在性 |
| L07 | `.agents/notes/` 存放设计决策与 bug 修复笔记（含中文版） | 目录存在性 —— **挖「为什么这么设计」的最佳去处** |

---

## 五、N 级 · 否定性论断（「没有 X」「不用 Y」）

**为什么单列一级**：本 skill 有相当一部分结论是**否定形式**的——「仓库没有 CHANGELOG」「提交不用 `BREAKING CHANGE:` 页脚」「不存在 TUI 前端包」。

它们同样会过时，而且**过时的方向是反的**：

- 正向断言过时的表现是「东西**消失**了」→ 探针搜不到 → STALE。
- 否定断言过时的表现是「东西**出现**了」→ 上面那套机制**完全抓不到**（搜不到反而被判定为成立）。

本 skill 曾因一条**错误的否定论断**（「DSH 不用 `!` 标记破坏性提交」——实际有 21 条）误导过整份文档，所以专门引入反向断言。**这是本表最容易被忽视的一类。**

### 5.1 已纳入探针自动核验（5 条）

> 语义与正向**相反**：**未命中 = HOLDS**（否定成立）；**命中 = STALE**（否定已被推翻）。
> 下表「若被推翻会看到什么」一列，写的就是探针要搜的证据。

| ID | 否定论断 | 若被推翻会看到什么（= 探针搜索的证据） | 探针模式 |
|---|---|---|---|
| N01 | 仓库**没有 CHANGELOG 文件** —— 变更史只在 git 与 `.agents/notes/` | 出现 `CHANGELOG*` 文件 | `nf:CHANGELOG*` |
| N02 | 提交**不使用 `BREAKING CHANGE:` 页脚**（只用 `type(scope)!:` 标题标记） | 任一提交的标题或正文含 `BREAKING CHANGE` | `nl:BREAKING CHANGE` |
| N03 | **不存在 `packages/ui/`**（TUI 前端包已归档） | 该目录重新出现 | `nd:ui`（scope=packages） |
| N04 | **版本号不连续**：不存在 `0.1.4` | 出现含 `0.1.4` 的 tag | `nt:0\.1\.4` |
| N05 | **不采用 changesets 发布流程**（无 `.changeset/`） | 出现 `.changeset/` 目录 | `nf:.changeset` |

新增一条 N 级断言的写法：在 `scripts/dsh-api-probe.sh` 的断言表里加一行，格式同其它行，模式用
`nf:`（文件名）/ `nd:`（目录）/ `nt:`（git tag）/ `nl:`（git log 提交信息），**payload 写「否定被推翻时会出现的证据」**。

### 5.2 只能人工复核（无法自动核验，附理由）

这些同样是「否定 / 行为」类结论，但**依赖 skill 之外的信息或运行时行为**，探针做不到。
**每次上游新版本时，5.1 由探针核对，5.2 需要人来判断** —— 这是本表唯一需要人工介入的部分。

| 论断 | 为什么不能自动 | 人工复核方式 |
|---|---|---|
| 官方文档**未列** UI 插槽全清单（40 个系从源码提取） | skill 内没有官方文档副本，且官方文档会更新 | 看 `<repo>/docs/` 是否新增插槽清单类文档 |
| 生态**没有官方插件市场**（发现机制是 GitHub topic `dsh-plugin`） | 生态事实，不在仓库内 | 查 GitHub 是否出现官方 marketplace 仓库 |
| 官方文档存在**两处内部矛盾** | 需人工阅读理解 | 重读 `11-glossary-and-provenance.md` 记录的矛盾点是否被官方修正 |
| `!!js` 写在 `config:`/`disabled:` 之外**静默失效（不报错）** | 运行时行为，静态搜不出来 | 写一个错位用例实跑一次 |
| 未声明 `inject` 就访问 `ctx.x` 会 **PENDING 或崩** | 同上 | 同上 |
| 补丁行 `id` 重复**启动即崩**（而非仅报错） | M11 只断言了报错文案，未断言行为 | 造一个重复 id 的补丁跑一次 |

---

## 六、探针自身的可信度（**不是关于 DSH 的断言，而是关于本 skill 的**）

探针报「全部成立」是一种**权力**——它会让使用者放心照抄。因此「不能失败的探针」比「没有探针」更危险。

### 6.1 已修正的三处假通过（本项目实际发生）

| # | 症状 | 根因 | 现状 |
|---|---|---|---|
| 1 | bash 版 `total=0` 却报「✅ 全部断言成立」并 `exit 0` | `CHECKS=$(cat <<'EOF'…)` 在缺 `cat` 的 shell 里静默展开为空 | 已改内联字符串 + 空表哨兵（`exit 3`） |
| 2 | Python 版 2 条假 STALE（样本明明存在） | `scope` 可指目录也可指**文件**，代码只按目录处理 | 遍历函数已支持单文件入口 |
| 3 | 本机 bash 报 37 条假 STALE | 该 bash 缺 `grep`/`head`/`find` | 改用纯 Python 探针；bash 版降为备选并在 SKILL.md 标注「本机勿用」 |

**共同模式**：失败形态不是报错，而是**静默给出一个看起来正常的答案**。三次都发生在「环境能力缺失」或「输入形态超出假设」时。

### 6.2 强制自检（每次改探针后必跑，步骤详见 `00-version-gate.md` 第 9 节）

| # | 场景 | 期望 |
|---|---|---|
| 1 | 正向：真实仓库 | `stale=0`，`exit 0` |
| 2 | 负向-路径：传 `C:\Windows` | `exit 2`，提示「看起来不是 DSH 仓库」 |
| 3 | 负向-断言：临时骨架中塞入 `CHANGELOG.md` + `packages/ui/` | `N01`/`N03` 报 STALE，`exit 1` |
| 4 | 空表：断言表置空 | `exit 3`，**不得**报成功 |

第 3 步是唯一能验证「否定性结论的兜底机制真的接上了」的手段，最容易被跳过。

### 6.3 断言表维护纪律

- `.py` 与 `.sh` 两份断言表**逐条一致**（等级 / 说明 / 模式 / 作用域全同），改一份必须同步另一份。
- 改断言前，**先用已知存在的样本验证正则本身**（`grep` 是 ERE，Python 是 `re`，转义不通用）。
- **V 级事实一律不许进断言表**。判据：这条事实明天变了，会让本 skill 的指引失效吗？不会 → 不进表。

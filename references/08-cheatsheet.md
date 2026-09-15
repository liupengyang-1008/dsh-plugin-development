> **文件来源**：本文件由 DSH 插件开发手册套件整合生成。直接编辑会在下次整合时被覆盖，因此维护性改动记录在工作区源文档中。

> **本文件用途**：速查卡，三部分：① 三种插件形态对照表（最容易搞混，放最前）② 完整 API 速查——服务名（inject 字符串）、事件名（含 waterfall 全套）、UI 插槽名、官方斜杠命令、CLI 命令、目录与路径、工具参数 DSL 类型（全部由源码 grep 提取，带实证来源列）③ 主手册的插件骨架、四类注册、真实范本清单、判断口诀，以及带 core/seam/bundle 角色的 ctx 键速查表。写代码时随手查这一份就够。
> **合成来源**：DSH插件开发实战补充-模板与踩坑.md（仅第六篇 6.5） + I-quickref.md + DSH插件开发指导手册.md（附录 A/B/C）
> **快照警告**：本文件是 DSH 插件知识的**冻结快照**（基线 `dsh-v0.1.6-alpha.1` / commit `0a15e36e7f`，2026-09-15），其中的**接口名级事实可能已过时**。
> **写代码前先核验**：`bash scripts/dsh-api-probe.sh <DSH 仓库路径>`（退出码 1 = 有 STALE，**不要直接照抄**）。
> **分级与核验规则**：`references/00-version-gate.md`、逐条登记 `references/api-claims.md`。
> **素材名约定**：正文里出现的 `Xxx-yyy.md`（如 `E-official-templates.md`、`B-tools-external.md`）是**生成时的源调研笔记名**，其内容在生成时已合并进本文件——**不是 skill 内的文件**，不必去别处找。

> **本文件导航 —— 共 430 行，不要整读。** 先 `grep` 定位小节，再只读需要的那一节。
> - **上游素材原文**：约 192 行（46%），起点：`I-quickref.md`（文件开头）。**不是本技能重写的整理稿**；性质不一——**有的是官方文档逐字摘录（属权威原文），有的是调研期粗笔记（仅备查）**。读某一段前，务必连带读**该段开头的取材说明**。
> - **其余部分 = 面向任务的整理稿**，可直接照做；但它同样是基线快照，写代码前先过版本闸门。
> - 常用检索：`grep -n '^## '`、`grep -n '^# I\.'`（档案起点）

---

<!-- ↓ 源：DSH插件开发实战补充-模板与踩坑.md 区间 1913-1924 -->

## 6.5 三种插件形态对照（**最容易搞混的一张表**）

| | 函数式插件 | 服务插件 | 组合包 |
|---|---|---|---|
| 导出 | `export const name/inject/Config` + `export function apply` | `export default class extends Service` | `export {}`（或什么都不导） |
| **不能有** | ❌ `export default` | ❌ `export function apply` | — |
| `package.json` 的 `dsh` | **无**（工具/命令类）或 `dsh.client`（UI 类） | 无 | `dsh.bundle.patch` |
| 干什么 | 注册工具/命令/监听事件/加 UI | 给别的插件提供能力 | 组装插件栈 |
| 典型范本 | `tool-ask-user` | `storage` | `bundle/base`、`ouroboros` |

---


---

<!-- ↓ 源：I-quickref.md （全文） -->

# I. 速查表 —— 服务 / 事件 / 插槽 / 命令 / 扩展点（全部实测）

> 来源：`deepseek-harness`（commit `0a15e36e7f`）。全部由源码 grep 提取，**不是文档复述**。
> 使用方法：写插件时先在这张表里找"我要挂到哪"。

---

## 1. 服务名（写 `inject` 用的字符串）

| 服务名 | 用途 | 实证来源 |
|---|---|---|
| `tools` | 工具注册表 | `interaction/tool-ask-user` |
| `commands` | 斜杠命令注册表 | `feedback/command-feedback` |
| `agents` | agent 注册表 | `context/time-context` |
| `sessions` | 会话存储 | `feedback/command-feedback` |
| `sessionProjections` | 会话投影 | `context/time-context` |
| `userQuestions` | 向用户提问的能力 | `interaction/tool-ask-user` |
| `settings` | 用户设置存储（宿主侧） | `client/ui-theme` |
| `slots` | UI 插槽注册表（客户端） | `client/ui-brand-official` |
| `locale` | 文案（客户端） | `client/ui-theme` |
| `remote` | 宿主↔客户端转发 | `client/ui-theme` |
| `settingsScope` | 客户端设置订阅 | `client/ui-theme` |
| `approval` | 审批分发服务 | `docs/subsystems/approval.zh.md` |
| `tokenMeter` | token 计量 | `docs/subsystems/compaction.zh.md` |
| `toolResultPruner` | 工具结果裁剪 | `docs/subsystems/compaction.zh.md` |
| `sessionQuery` | 会话全文检索 | `docs/subsystems/core.zh.md` |
| `ptcRuntime` | PTC 执行后端注册表（**0.1.6-alpha.1 起，原名 `codeRuntime`，无兼容别名**） | `packages/ptc-runtime/ptc-runtime/src/index.ts` |
| `ssh` | POSIX SSH 执行后端（0.1.6-alpha.1 新增，替代被移除的 `e2b`） | `packages/ssh/ssh/src/index.ts` |
| `browserUse` | 浏览器自动化后端注册（**只登记名字与 disposer**，不含浏览器对象/操作方法；同名二次注册必失败） | `packages/browser-use/browser-use/src/index.ts` |
| `computerUse` | 桌面自动化后端注册（同上，独立于 `browserUse`） | `packages/computer-use/computer-use/src/index.ts` |
| `mcpResources` | MCP 资源面：`register(server, provider)`，暴露「列资源 / 列模板 / 读 URI」三个共享工具 | `packages/mcp/mcp-resources/src/index.ts` |
| `terminalController` | 会话级终端进程的远程控制面（含 `webTerminals` 客户端侧） | `packages/api/terminal-controller/src/index.ts` |

> ⚠️ **服务名大小写敏感**（`sessionProjections` 不是 `session-projection`）。
> 💡 探测可选服务：`ctx.get('settings')`；**只有 `inject` 里声明过的**才能写 `ctx.settings`。

---

## 2. 事件名

### 2.1 生命周期 / 状态事件（`ctx.on('x', fn)` 监听，无返回值语义）

| 事件名 | 时机 |
|---|---|
| `agent/created` | agent 创建。**⚠️ 0.1.6-alpha.1 起由 `emit` 改为 `serial`** —— 监听器按序被 `await`，**抛错会让 agent 创建失败**；浏览器/桌面类后端就靠它做「会话创建前的启动等待」 |
| `agent/disposed` | agent 销毁 |
| `agent/status` | agent 状态变化 |
| `agent/turn-stopping` | 轮次即将结束（在最后一次 steering 排空之前） |
| `agent/error` | agent 出错 |
| `agent/assistant-stream` | 助手流式输出 |
| `session/created` / `session/disposed` | 会话生命周期 |
| `session/event` | 会话日志追加 |
| `session/fork` | 会话分叉 |
| `subagent/start` / `subagent/end` | 子 agent 生命周期 |
| `subagent/provider-added` / `subagent/provider-removed` | 子 agent provider 注册变化 |
| `tools/change` | 工具注册表变化 |
| `skills/change` | 技能变化 |
| `slots/changed` | **插槽变化**（UI） |
| `theme/change` | 主题变化（UI，**自定义事件范例**） |
| `locale/change` | 语言变化（UI） |
| `system-prompt/change` | system prompt 变化 |
| `goal/change` / `goal/changed` / `goal/activation-changed` | 目标状态 |
| `compaction/start` / `compaction/end` / `compaction/summary` / `compaction/prune` | 上下文压缩 |
| `llm/retry` / `llm/retry-started` | LLM 重试 |
| `llm/adapters-updated` | LLM 适配器变化 |
| `compaction/summary-error` | 摘要请求失败后的恢复（**waterfall**，0.1.6-alpha.1 新增） |
| `permission-presets/catalog-changed` | 可选权限预设目录变化（0.1.6-alpha.1 新增） |
| `session-telemetry/record` | 遥测（**脱敏 waterfall**） |
| `webserver/index-inject` | **往页面 HTML 注入**（UI 首屏，避免闪烁） |

### 2.2 ⭐ waterfall 事件 —— **Agent 会话流程的扩展点**（重要）

**语义**：`ctx.on('事件名', async (payload, next) => {...})`。
- 调 `await next()` → **保持原样**（继续走后面的监听器/默认逻辑）
- **返回替换值** → **改变流程**
- **不调 `next()` 就返回** → **短路**（官方原文用词：reject a proposed step）

| 事件名 | 能改什么（官方原文摘要） |
|---|---|
| **`agent/pre-step`** | **请求推导前唯一的 waterfall 监听器链**。可以**拒绝一个拟定的 step、或替换进入该 step 的消息**。`next()` 保持当前消息。payload：`{ agent, messages, turn, step, signal }` |
| **`agent/request`** | **替换冻结的调用配置**。`await next()` 拿到机器本会用的配置，返回替代品即可切换。在 assembly 与 `step/start` 之后、system prompt 与已接受用户批次提交之前运行。**此 waterfall 不能改消息** |
| `agent/request-error` | 失败请求的恢复（如触发重试） |
| `system-prompt/assemble` | 组装 system prompt |
| `llm/stream` | LLM 输出流 |
| `llm/discoverModels` / `llm/listProviders` / `llm/listConfigurableProviders` | 模型/提供商发现 |
| `approval/request` | 审批决策（第一个应答者占唯一决策槽，其余 `next()` 委托） |
| `session-telemetry/record` | 遥测记录（脱敏） |

> 🔥 **做"Agent 流程定制"就靠两个**：`agent/pre-step`（改消息/拦步骤）与 `agent/request`（改调用配置）。
> ⚠️ **官方硬规则**：waterfall 监听器**必须** `await next()` 或 `return next()`，否则会**静默吃掉**后续所有处理。

### 2.3 官方原文对 waterfall 的关键约束（逐字）

> `agent/pre-step`：
> ```
> Reject a proposed step or replace the messages that enter it. Calling `next()` preserves the current messages.
> ```

> `agent/request`：
> ```
> Replace the frozen call configuration. `await next()` yields the config the machine would use (agent options on the first request, the logged header afterwards); return a replacement to switch. On step admission, this runs after assembly and `step/start`, before the system prompt and accepted user batch are committed. Cancellation here or during subsequent `prepareCall()` resolution commits neither. The prepared call capability governs prompt admission. Model-visible content must use logged channels; this waterfall cannot mutate messages.
> ```

> `docs/subsystems/core.zh.md:345`（逐字）：
> ```
> `agent/pre-step` 是请求推导前唯一的 waterfall（瀑布式）监听器链。`agent/turn-stopping` 在轮次没有工具或 steering（中途引导）后续时运行，先于最后一次 steering 排空。
> ```

> `docs/subsystems/core.zh.md:306`（逐字）：
> ```
> [事件分类](../architecture.zh.md#events)负责 `agent/*` 生命周期、检查点与 waterfall（瀑布式事件）约定。轮次和步骤边界是持久会话事件，而不是 agent emit。
> ```

---

## 3. UI 插槽名（**最常用的几个**；权威全量约 **61** 个公开键 —— 对基线 `dsh-v0.1.6-alpha.1` 抽取：声明侧 77、并集 79、剔除 18 个测试专用键后约 61 个公开可用。用 `scripts/extract_slots.py` 复现）

**最常用的三个**：

| 插槽名 | 用途 |
|---|---|
| `settings.section` | **加一整段设置页** |
| `sidebar.right.tab.guide.entry` | 右侧栏「指引」页里的入口条目（0.1.6-alpha.1 新增） |
| `conversation.input.permission` | 输入区权限选择位（0.1.6-alpha.1 新增） |
| `settings.general.item` | **通用设置里加一行/一项** |
| `conversation.view` | 替换对话主视图（最激进） |
| `sidebar.brand.mark` / `sidebar.brand.name` | 侧栏品牌位（最小 UI 插件范例用的） |
| `tool.call.toolview` | 工具调用的自定义卡片 |

---

## 4. 官方内置斜杠命令

| 命令 | 来源包 |
|---|---|
| `/compact` | `packages/compaction/command-compact` |
| `/feedback` | `packages/feedback/command-feedback` |
| `/goal` | `packages/goal/command-goal` |
| `/permission` | `packages/interaction/permission-presets` |
| `/plan` | `packages/plan/plan-mode` |
| `/export` | `packages/session-query/session-log-export` |

---

## 5. CLI 命令速查（`apps/cli/src/args.ts` 原文）

```bash
dsh --profile web                          # 启动 web profile（= dsh web）
dsh --profile headless "跑一下测试"          # 单任务模式，答完即退
dsh --profile tui --patch ./extra.yml      # 启动并叠一层补丁
dsh --profile web --dump-config            # 打印组装后的完整配置树（调试神器）
dsh --profile web --dump-default-config    # 只打印 bundle 层
dsh --profile <名字> --from-default-profile web   # 从官方模板复制出新 profile
dsh plugin --profile web add <包>           # 装插件
dsh plugin --profile tui add <package>     # 官方帮助里的原文示例
```

**硬约束**：
- `--profile` 对 `plugin` 子命令是 **required**（省略直接报错）
- `web` = `--profile web` 的硬编码别名
- `desktop` profile 禁止手动操作（`error: profile "desktop" is managed exclusively by the Electron application`）
- `--dump-config` 与 `--dump-default-config` 互斥；`--dump-default-config` 不接受 `--patch`

---

## 6. 目录与路径速查

| 项 | 位置 |
|---|---|
| `$DSH_HOME` 默认 | `~/.dsh`（Windows：`C:\Users\<你>\.dsh`） |
| profile 目录 | `$DSH_HOME/profiles/<名字>/` |
| 已安装插件 | `$DSH_HOME/profiles/node_modules/` |
| **用户自己的补丁层** | `$DSH_HOME/profiles/<名字>/cordis.patch.yml` |
| 用户设置文档 | `$DSH_HOME/settings.yaml`（**热重载**） |
| 凭据存储 | `$DSH_HOME` 下的隐藏文件（由 DSH 自身管理；本技能只标注它在这个位置，不读取其内容） |
| 匿名用户 id | `$DSH_HOME/.anonymous-user-id`（删掉即重置） |

---

## 7. 工具参数 DSL 支持的类型（`schema.ts:411` 原文报错信息反推）

```
parameters.<字段>.type 允许：
  'string' | 'number' | 'integer' | 'boolean' | 'null' | 'array' | 'object' | 'json'
或者用 oneOf（但要 ≥2 个分支，且不能与 type 同时声明）
```

官方报错原文（`schema.ts:411`）：
```
${path}.type must be string/number/integer/boolean/null/array/object/json, or use oneOf
```

**必填写法**：`required: true`（**属性级**，走 `defineTool` 时）。写别的值会报（`schema.ts:293`）：
```
${path}.required must be true when present
```

---

<!-- ↓ 源：DSH插件开发指导手册.md 区间 2786-2976 -->

# 附录 A 速查卡（打印这张就够了）

## A.1 插件骨架

```ts
import type { Context } from '@deepseek-ai/cordis'

export const name = 'my-plugin'          // 可选，用于诊断
export const inject = ['tools']          // 需要哪些服务；不写就用不到 ctx.xxx
export const Config = /* schema */       // 可选，可配置插件才需要

export function apply(ctx: Context, config: Config) {
  // 在这里注册。注册即 effect，自动回收。
}
// ⚠️ 不要加 export default
```

## A.2 四类注册

```ts
// 1) 工具（给模型用）
ctx.tools.register(defineTool({ name, description, parameters, output, execute }))

// 2) 命令（给人用，/xxx）
ctx.commands.register({ name, description, input, handler })

// 3) 事件（听 / 截）
ctx.on('tools/result', (exec, result) => {})           // 只观察
ctx.on('tools/pre-execute', async (exec, next) => {}) // 拦截（必须 return next() 或决策对象）

// 4) UI 插槽（客户端半侧）
ctx.slots.inject('插槽名', () => ctx.slots.register({ name: '插槽名', id, order }, Component))
```

## A.3 必备命令

| 目的 | 命令 |
|---|---|
| 从源码启动 Web | `pnpm dsh web` |
| 带本地插件启动 | `pnpm dsh web --patch ./scratch-plugin/cordis.yml` |
| 看组合树 | `dsh --profile <name> --dump-config` |
| 装插件 | `dsh plugin --profile <name> add <包名/路径>` |
| 卸插件 | `dsh plugin --profile <name> remove <包名>` |
| 跑测试 | `pnpm run test` |
| 覆盖率门禁 | `pnpm run test:coverage` |
| 质量门禁 | `pnpm run constraints && pnpm run typecheck && pnpm run lint` |

## A.4 判断口诀

| 我要做的事 | 用什么 |
|---|---|
| 让模型能做某事 | 工具 `ctx.tools.register` |
| 让用户能做某事 | 命令 `ctx.commands.register` |
| 改/拦别人的行为 | 事件 `ctx.on`（waterfall） |
| 观察/审计 | 事件 `ctx.on`（emit） |
| 给别人复用我的能力 | 服务 `Service` 子类 |
| 在界面上显示 | 插槽 `ctx.slots.register` |
| 让用户改我的配置 | Config + 设置卡片 |
| 管理外部资源 | `ctx.effect(() => { ...; return () => 清理 })` |

## A.5 三条最容易忘的

1. ⚠️ 插件没反应 → 日志里找 `pending (waiting for service: ...)`
2. ⚠️ 函数插件**绝不能**有 `export default`
3. ⚠️ 未声明的服务用 `ctx.get('name')`，**不要** `ctx.name`

---

# 附录 B 真实范本清单（照着抄最快）

> 全部路径相对于仓库根。主文件行数为主 `src/index.ts` 的行数，「src 总量」为该包 `src/` 下所有 `.ts/.tsx` 行数之和。

## B.1 最小可运行（学习包骨架）

| 包 | 路径 | 主文件 | src 总量 | 用途 |
|---|---|---|---|---|
| `@deepseek-ai/dsh-brand` | `packages/util/brand` | 39 | 39 | 最小非 UI 包 |
| `@deepseek-ai/dsh-client-ui-brand-official` | `packages/client/ui-brand-official` | 7 | **49** | **最小 UI 插件**（首选范本） |
| `@deepseek-ai/dsh-subagent-spawn-in-process` | `packages/subagent/subagent-spawn-in-process` | 70 | 70 | 最小能力 Provider |
| `@deepseek-ai/dsh-agent-tool-presentation` | `packages/core/agent-tool-presentation` | 72 | 72 | 最小 `apply` + config |

## B.2 工具插件

| 包 | 路径 | 教什么 |
|---|---|---|
| `@deepseek-ai/dsh-tool-ask-user` | `packages/interaction/tool-ask-user` | **最小工具 + 对象输出 schema**（首选） |
| `@deepseek-ai/dsh-tool-todo` | `packages/todo/tool-todo` | 工具 + **必填** Config 字段 |
| `@deepseek-ai/dsh-tool-bash` | `packages/shell/tool-bash` | 工具 + Config + 卡片 + 审批升级（**进阶首选**） |
| `@deepseek-ai/dsh-tool-fs` | `packages/fs/tool-fs` | diff 卡片 |

## B.3 命令插件

| 包 | 路径 | 教什么 |
|---|---|---|
| `@deepseek-ai/dsh-command-compact` | `packages/compaction/command-compact` | **全生命周期最清晰的命令插件**（首选） |
| `@deepseek-ai/dsh-command-feedback` | `packages/feedback/command-feedback` | 命令 + 反馈通道 |
| `@deepseek-ai/dsh-command-goal` | `packages/goal/command-goal` | 命令 + 会话目标 |

## B.4 配置 / 设置

| 包 | 路径 | 教什么 |
|---|---|---|
| `@deepseek-ai/dsh-tool-terminal` | `packages/terminal/tool-terminal` | 数值范围校验（`.min/.max/.step`） |
| `@deepseek-ai/dsh-web-search-deepseek` | `packages/web/web-search-deepseek` | **Config 与设置卡 Host 半侧打通**（首选） |
| `@deepseek-ai/dsh-client-ui-theme` | `packages/client/ui-theme` | 长驻设置命名空间 + schema |

## B.5 UI 插件

| 包 | 路径 | 教什么 |
|---|---|---|
| `@deepseek-ai/dsh-client-ui-brand-official` | `packages/client/ui-brand-official` | **最小 UI 插件**（首选） |
| `@deepseek-ai/dsh-client-ui-plan` | `packages/client/ui-plan` | 单一功能 UI 插件 |
| `@deepseek-ai/dsh-client-ui-jobs` | `packages/client/ui-jobs` | 后台任务卡片 |
| `@deepseek-ai/dsh-client-ui-theme` | `packages/client/ui-theme` | UI + 设置行 + locale + store + CSS |
| `@deepseek-ai/dsh-client-ui-settings-plugins` | `packages/client/ui-settings-plugins` | **设置卡片宿主 + 4 张真实卡片**（首选） |
| `@deepseek-ai/dsh-client-ui-slots` | `packages/client/ui-slots` | 插槽注册表核心（非 React） |
| `@deepseek-ai/dsh-client-ui-renderer` | `packages/client/ui-renderer` | React 渲染器（唯一的 `useSyncExternalStore` 宿主） |
| `@deepseek-ai/dsh-client-modules` | `packages/client/modules` | `dsh.client` 扫描与 boot 图 |

## B.6 终端家族（capability seam 三角色标准范本）

| 包 | 路径 | 角色 |
|---|---|---|
| `@deepseek-ai/dsh-terminal` | `packages/terminal/terminal` | Service Definition（`ctx.terminals`） |
| `@deepseek-ai/dsh-terminal-bash` | `packages/terminal/terminal-bash` | Service Provider（PTY 后端） |
| `@deepseek-ai/dsh-tool-terminal` | `packages/terminal/tool-terminal` | Consumer（6 个工具） |

## B.7 新增包的整体模板

| 包 | 路径 | 说明 |
|---|---|---|
| `@deepseek-ai/dsh-tools` | `packages/core/tools` | 官方指定的 "copy from" 模板（`adding-a-package.zh.md:9-21`） |
| `@deepseek-ai/dsh-web-app` | `packages/bundle/web-app` | **客户端登记模板**（`dsh.bundle.patch` + 浏览器 roster） |

---

# 附录 C 核心服务名速查表

> **完整清单**：`docs/capability-seams.zh.md`（含每个服务的所属包、实现、消费方、配套插件）。官方明确要求**不要维护另一份静态清单**，以生成的区块为准。
> **角色**：`seam` = 可替换能力（有 Provider）；`core` = 主干服务；`bundle` = 由组合包提供的唯一实例。

## C.1 插件作者最常用的 12 个

| ctx 键 | 角色 | 用途 |
|---|---|---|
| `ctx.tools` | core | 工具注册表与受把关的执行流水线 |
| `ctx.commands` | core | 人类命令注册表 |
| `ctx.systemPrompt` | core | 系统提示词组装注册表 |
| `ctx.llm` | **seam** | LLM 适配器注册表 |
| `ctx.shell` | **seam** | Bash 执行器 |
| `ctx.fs` | **seam** | 文件系统提供方 |
| `ctx.subprocess` | **seam** | 子进程 |
| `ctx.terminals` | **seam** | 持久 PTY 会话注册表 |
| `ctx.settings` | **seam** | 用户设置 |
| `ctx.storage` | **seam** | 非会话存储枢纽 |
| `ctx.jobs` | **seam** | 后台作业注册表 |
| `ctx.approval` | **seam** | 审批 |

## C.2 会话与 agent 相关

| ctx 键 | 角色 | 用途 |
|---|---|---|
| `ctx.agents` | core | Agent 服务 |
| `ctx.agentLoop` | bundle | 唯一的具体循环插件 |
| `ctx.agentPresets` | core | 按会话的 agent 组合 |
| `ctx.sessions` | core | 内存会话存储 |
| `ctx.sessionPersistence` | **seam** | 持久会话持久化 |
| `ctx.sessionQuery` | **seam** | 会话读取、追踪、过滤与搜索 |
| `ctx.sessionProjections` | core | 会话投影单元 |
| `ctx.compaction` | **seam** | 压缩 |
| `ctx.skills` | **seam** | Skill 提供方注册表 |
| `ctx.subagents` | **seam** | Subagent 提供方与延续服务 |
| `ctx.userQuestions` | **seam** | 人类问答 |
| `ctx.workflowEngine` | **seam** | 工作流脚本引擎 |

## C.3 Web / UI 相关

| ctx 键 | 角色 | 用途 |
|---|---|---|
| `ctx.web` | **seam** | Web 访问提供方注册表 |
| `ctx.webServer` | core | HTTP 路由注册 |
| `ctx.clientModules` | core | 客户端插件图宿主 |
| `ctx.sandbox` | **seam** | 进程沙箱 |
| `ctx.credentials` | **seam** | 凭据 |
| `ctx.attachments` | **seam** | 持久二进制附件存储 |
| `ctx.webhookRuntime` | core | Webhook 规则运行时 |

**怎么选**：要「替换实现」→ 找 `seam` 行；要「新增能力」→ 自建三件套；要「消费」→ 直接 `inject` 已存在的服务。

---


---


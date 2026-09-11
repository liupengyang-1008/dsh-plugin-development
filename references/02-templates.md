<!-- 本文件由 DSH 插件开发手册套件整合生成，请勿手工编辑；改动请回到工作区源文档。 -->

> **本文件用途**：由易到难的 12 个可直接复制的插件模板（T1~T12），覆盖零代码组合包、补丁语法、工具、命令、配置、服务、UI、设置卡片、流程拦截、外部集成、工程骨架。后接【官方逐字源码附录】（7 类官方模板全文 + 40 个 UI 插槽名全清单 + 官方 AGENTS.md 硬约束）与【社区零代码组合包全文】。T3/T5/T6 与附录模板 3/4/5 是同一件事的两种粒度：正文给讲解与坑，附录给可逐字照抄的完整源码——两边都要看，冲突时以附录的官方源码为准。
> **合成来源**：DSH插件开发实战补充-模板与踩坑.md（第二篇） + E-official-templates.md + H-community-bundle.md
> **快照警告**：本文件是 DSH 插件知识的**冻结快照**（基线 `v0.1.5-rc.2` / commit `c291e7961a`，2026-09-10），其中的**接口名级事实可能已过时**。
> **写代码前先核验**：`bash scripts/dsh-api-probe.sh <DSH 仓库路径>`（退出码 1 = 有 STALE，**不要直接照抄**）。
> **分级与核验规则**：`references/00-version-gate.md`、逐条登记 `references/api-claims.md`。
> **素材名约定**：正文里出现的 `Xxx-yyy.md`（如 `E-official-templates.md`、`B-tools-external.md`）是**生成时的源调研笔记名**，其内容在生成时已合并进本文件——**不是 skill 内的文件**，不必去别处找。

---

<!-- ↓ 源：DSH插件开发实战补充-模板与踩坑.md 区间 64-1256 -->

# 第二篇 · 模板库（12 个，由易到难）

> 每个模板的结构：**它是干什么的 → 完整代码（逐字可抄）→ 逐行讲解 → 易错点 → 🤖 AI Agent 提示词**。
> 全部代码来自真实仓库，标注来源路径。

---

## T1 · 零代码组合包 ★（最小可用插件）

**它是什么**：整个插件只有 **3 个文件**，**不写一行 JavaScript**。靠一个 `cordis.patch.yml` 把现成能力挂进 DSH。
**来源**：`Q00/ouroboros → integrations/dsh-plugin/`（官方精选清单里**唯一**的纯配置零代码插件，约 5,805★）。它靠这一个补丁，给模型新增了 **35 个工具**。

### 1.1 目录结构（就这么多）

```
my-plugin/
├── package.json
├── cordis.patch.yml
└── README.md
```

### 1.2 `package.json`（逐字）

```json
{
  "name": "dsh-ouroboros",
  "version": "0.1.0",
  "description": "Mount Ouroboros (spec-first AI dev workflow engine) into DeepSeek Harness as native tools — type \"ooo interview\" or \"ooo auto\" in chat.",
  "type": "module",
  "license": "MIT",
  "repository": {
    "type": "git",
    "url": "git+https://github.com/Q00/ouroboros.git",
    "directory": "integrations/dsh-plugin"
  },
  "keywords": [
    "dsh-plugin",
    "deepseek-harness",
    "ouroboros",
    "mcp"
  ],
  "files": [
    "cordis.patch.yml",
    "README.md"
  ],
  "dsh": {
    "bundle": {
      "patch": "./cordis.patch.yml"
    }
  }
}
```

### 1.3 `cordis.patch.yml`（骨架；原文很长，此处保留结构最关键部分）

```yaml
# 注释可以写得很长 —— 对这个插件来说，注释就是它的"文档"
- insert:
    - id: mcp-ouroboros
      name: '@deepseek-ai/dsh-mcp-client'
      config:
        serverName: ouroboros
        transport: stdio
        command: uvx
        args:
          - --from
          - 'ouroboros-ai[mcp]'
          - --with
          - 'mcp==2.0.0'
          - ouroboros
          - mcp
          - serve
        env:
          OUROBOROS_LLM_BACKEND: !!js process.env.OUROBOROS_LLM_BACKEND ?? ''
          OUROBOROS_AGENT_RUNTIME: !!js process.env.OUROBOROS_AGENT_RUNTIME || 'host'
          DEEPSEEK_API_KEY: !!js process.env.DEEPSEEK_API_KEY ?? ''
        toolCallTimeoutMs: 1800000
        failOnStartupError: false
```

### 1.4 逐行讲解（4 个必抄点）

| 位置 | 为什么必须这样写 |
|---|---|
| `"type": "module"` | 必须 |
| `files` 里有 `cordis.patch.yml` | 🔥 **漏了它，发布后补丁文件不会进 npm 包，插件装上有警告、功能全无** |
| `dsh.bundle.patch` | 🔥 **少了它，`dsh plugin add` 会打那条 `declares no dsh.bundle` 警告，然后什么都不做** |
| 没有 `main`/`exports`/`dependencies` | 零代码包本来就没有 JS 入口 —— 这是它和普通包的显著差异 |

### 1.5 附带学到的 4 条硬知识（都来自原文注释）

1. **`!!js` 可以写在 `config:` 内部**（`env:` 里就用了）。
2. 🔥 **子进程环境会被"清洗"**：`@deepseek-ai/dsh-subprocess` 会把**凭据形状的名字**（正则 `/KEY|PASSWORD|SECRET|TOKEN/i`）**和所有 `DSH_*`** 从父环境里删掉。**你要传的凭据必须显式列在 `env:` 里**。
   原文：`hands mcp-client a scrubbed parent env with every credential-shaped name (/KEY|PASSWORD|SECRET|TOKEN/i) and every DSH_* name removed`
3. 🔥 **后面的层"替换"整段 `config`，不做深合并** —— 覆盖时必须**把整个 config 重述一遍**。
   原文：`restating the whole config, since a later layer replaces a row's config rather than deep-merging it`
4. **`failOnStartupError: false` = 软失败**：没装依赖的机器也能正常启动 DSH，其它插件照常工作。但**软失败不等于自动恢复**。
   原文：`Recovery is not guaranteed to be automatic — whether mcp-client retries at all depends on the dsh build`

### 1.6 安装

```bash
dsh plugin --profile web add ./my-plugin     # 本地目录
dsh plugin --profile web add dsh-my-plugin   # 已发布到 npm
```

### 1.7 ⚠️ 边界（诚实说清）

T1 **只能挂载别人已有的能力**（如 MCP server）。要给模型加**你自己写的新工具**，去 T3。

### 🤖 让 AI Agent 帮你做 T1

```
我要做一个 DSH 插件，它不做别的，只把 <外部工具/MCP server> 挂进 DSH。
请帮我写这个插件的三个文件：package.json、cordis.patch.yml、README.md。

要求：
1. package.json 必须有 "type":"module"、"files" 包含 cordis.patch.yml、
   "dsh":{"bundle":{"patch":"./cordis.patch.yml"}}。
2. cordis.patch.yml 用 "- insert:" 列表，具体怎么配 <外部工具> 请先查
   <外部工具的官方文档/GitHub>，不要猜参数名。
3. 所有需要传给子进程的凭据，必须在 config.env 里显式列出（用 !!js process.env.X ?? ''）。
4. 加 failOnStartupError: false，让依赖缺失时也能启动 DSH。

铁律：每个配置字段都要说出出处（文档链接或仓库文件路径）。查不到的字段不要编。
```

---

## T2 · 组合包与 `cordis.patch.yml` 语法详解 ★★

**它是什么**：把 T1 的补丁文件语法彻底讲清。官方自己最核心的包 `@deepseek-ai/dsh-base` 就是一个纯配置组合包。
**来源**：官方 `packages/bundle/base/`。

### 2.1 官方纯配置包的 `src/index.ts`（全文，就 9 行）

```ts
/**
 * @deepseek-ai/dsh-base — the shared dsh core as a profile bundle. The
 * package's substance is `cordis.patch.yml`, declared by the `dsh.bundle.patch`
 * manifest field and resolved by the profile composer through that field;
 * this module carries no runtime API.
 * @module @deepseek-ai/dsh-base
 */

export {}
```

> 官方注释说得很直白：**这个包的实质是 `cordis.patch.yml`，这个模块不承载任何运行时 API。**

### 2.2 补丁行的完整字段表

| 字段 | 必填 | 含义 |
|---|---|---|
| `id` | ✅ | 行标识。**后续层靠它覆盖该行**（逐行 last-write-wins）。**全局唯一**，重复会报 `duplicate loader entry id` 且**启动即崩** |
| `name` | ✅ | 包名。可以指向子路径，如 `@deepseek-ai/dsh-tool-subagent-control/list-agents`。**也可以写相对路径**（见 2.5） |
| `disabled` | ❌ | `true` 关闭该行；支持 `!!js` 表达式 |
| `config` | ❌ | 传给插件的配置对象。**覆盖时整段替换，不合并** |

### 2.3 `!!js` 内联表达式（官方原文用法）

```yaml
    - id: session-persistence-jsonl
      name: '@deepseek-ai/dsh-session-persistence-jsonl'
      config:
        root: !!js dshHomePath('sessions')

    - id: sandbox-policy
      name: '@deepseek-ai/dsh-sandbox-policy'
      config:
        mode: !!js process.env.DSH_PERMISSION_MODE ?? 'workspace-write'
        workspaceRoot: !!js process.cwd()

    # 🔥 跨平台标准写法：官方就这么处理 bash/pwsh 的平台差异
    - id: bash-sandbox
      name: '@deepseek-ai/dsh-bash-sandbox'
      disabled: !!js process.platform === 'win32'
      config:
        timeoutMs: 60000

    - id: pwsh-sandbox
      name: '@deepseek-ai/dsh-pwsh-sandbox'
      disabled: !!js process.platform !== 'win32'
```

**`!!js` 的求值范围（官方复盘 0002 的教训，必须记牢）**：

| 位置 | `!!js` 是否被求值 |
|---|---|
| `config:` 内部的任何值 | ✅ 会 |
| entry 的 `disabled:` | ✅ 会（当前版本） |
| **其它任何 entry 元数据**（如 `id`、`name`） | ❌ **不会**，必须写字面量 |

> ⚠️ 写在不会求值的位置**不报错**，只是**静默失效** —— 这是复盘 0002 整整一个事故的根因。

### 2.4 五条铁律（都有官方原文或复盘背书）

| # | 铁律 | 依据 |
|---|---|---|
| 1 | **行的书写顺序不影响加载顺序** —— 激活由「服务可用性」驱动，不是顺序 | 官方 base 补丁注释：`Row order carries no load semantics (activation is service-availability driven)` |
| 2 | `config` 是**整段替换**，不是深合并 | 同上：`A patch replaces the targeted row's whole config rather than merging into it` |
| 3 | `!!js` 的**可见范围**是「同一补丁内、它之前的行」 | `omdsh-dev/DSH-better-sidebar` 补丁注释：`only rows before this one are visible` |
| 4 | 同一个 `id` 重复 → **启动即崩**，且插件无法自愈 | 见 `第三篇 · 坑 P4` |
| 5 | 补丁文件**顶层是单个数组**（一个 `- insert:`），不要写成两个顶层值 | 见 `第三篇 · 坑 P3` |

### 2.5 相对路径 `name` 的真相（官方文档自相矛盾，以源码为准）

官方文档 `user/develop/basic/index.zh.md:56` 说插件路径「必须是绝对路径」。
但源码 `packages/boot/app-boot/src/index.ts` 的 `anchorInsertedPluginNames()` 明确把相对路径**锚定到补丁文件旁边**：

```ts
const base = dirname(resolve(file))
entry.name = pathToFileURL(resolve(base, entry.name)).href
```

**结论**：**写相对路径是可行的**（且有单元测试固定该行为）。但为了可移植，第三方插件建议用**包名**（`@scope/name`），而不是相对路径。

---

## T3 · 工具插件 · `defineTool`（让模型调用你的能力）★★

**它是什么**：给模型加一个可调用的工具。**这是"外部调用方向"的主力形态。**
**来源**：官方 `packages/interaction/tool-ask-user`（官方**最小**的工具插件，全包 101 行）。完整全文见 `plugin-research/notes/E-official-templates.md` 模板 3。

### 3.1 完整骨架（逐字，可直接抄）

```ts
import type { Context } from '@deepseek-ai/cordis'
import { defineTool } from '@deepseek-ai/dsh-tools'
import '@deepseek-ai/dsh-user-questions'

export const name = 'tool-ask-user'
export const inject = ['tools', 'userQuestions']

const description = 'Ask the user a concise question when you need confirmation, a choice, or missing information before proceeding. '
  + 'Send one or more questions, each with a stable id that will be echoed in the answer.'

export function apply(ctx: Context): void {
  ctx.tools.register(defineTool({
    name: 'ask_user_question',
    description,
    parameters: {
      questions: {
        type: 'array',
        required: true,
        description: 'Questions to ask the user before continuing.',
        items: {
          type: 'object',
          additionalProperties: true,
          properties: {
            id: { type: 'string', required: true, description: 'Stable id for this question; echoed in the answer.' },
            question: { type: 'string', required: true, description: 'The specific question to ask the user.' },
          },
        },
      },
    },
    output: {
      schema: {
        type: 'object',
        additionalProperties: false,
        properties: {
          answers: {
            type: 'array',
            required: true,
            items: {
              type: 'object',
              additionalProperties: false,
              properties: {
                id: { type: 'string', required: true },
                selected: { type: 'array', required: true, items: { type: 'string' } },
                custom: { type: 'string' },
              },
            },
          },
        },
      },
      render: (_args, value) => [{ type: 'text', text: JSON.stringify(value) }],
    },
    async execute(args, exec) {
      // 业务逻辑；exec.signal 是取消信号，exec.agent 是当前 agent
      const result = await ctx.userQuestions.ask({ /* ... */ signal: exec.signal })
      return { /* 返回值必须匹配 output.schema */ }
    },
  }))
}
```

### 3.2 🔥🔴 最重要的一课：`required` 有**两套写法**，混用必报错

DSH 有**两条**注册工具的路径，`required` 的位置**正好相反**：

| 注册方式 | `parameters` 是什么 | 必填怎么写 | 写错的后果 |
|---|---|---|---|
| **`defineTool({...})`**（官方自研插件全走这条，**新手推荐**） | **DSH 作者 DSL** | **属性级** `required: true` | 写对象级 `required: ['a']` → 报 `parameters.a.required must be true when present` |
| **裸 `ctx.tools.register({...})`**（社区插件常走） | **原始 JSON Schema** | **对象级** `required: ['a']` | 写属性级 `required: true` → 报 `required must be an array of strings` |

**证据（官方源码 `packages/core/tools/src/schema.ts`）**：

```ts
// 第 96-106 行
/** One implicit parameter-root property, optionally required. */
export type ParameterPropertySpec = ValueSchemaSpec & { required?: true }

/**
 * Tool parameter schema. The map itself is an implicit open object root;
 * requiredness remains a per-property `required: true` annotation.
 */
export type ParameterSchemaSpec = {
  [key: string]: ParameterPropertySpec
  [key: symbol]: never
}
```

```ts
// 第 570-571 行（defineTool 实现体内）
const parameters = parameterSchemaSpecToJsonSchema(options.parameters)
const outputSchema = valueSchemaSpecToJsonSchema(options.output.schema)
```

```ts
// 第 292-295 行（属性级 required 被收集成对象级数组）
if (Object.hasOwn(task.property, 'required') && task.property.required !== true) {
  authorError(`${task.path}.required must be true when present`)
}
if (Object.hasOwn(task.property, 'required') && task.property.required === true) task.required.push(task.key)
```

**三句话记住**：
1. 走 `defineTool` → `parameters` 的根是**隐式对象**，直接铺字段名，**不写** `type:'object'`/`properties` 包装。
2. 走 `defineTool` → 必填一律**属性级** `required: true`。
3. **`output.schema` 走 `defineTool` 时也是同一套 DSL**，同样用属性级 `required: true`；且它的**根节点不允许 `required`**。

> ⚠️ 这条之所以要单独强调：社区里有真实仓库（如 `yjh051108/dsh-routing-suite`）在注释里留下"血泪坑：属性级一律不允许 required 键"——那个结论**只对裸 `register` 路径成立**。照抄到 `defineTool` 上会直接报错。

### 3.3 `parameters` DSL 支持的类型

```
'string' | 'number' | 'integer' | 'boolean' | 'null' | 'array' | 'object' | 'json'
或者用 oneOf（需 ≥2 个分支，且不能与 type 同时声明）
```

官方报错原文（`schema.ts:411`）：
```
${path}.type must be string/number/integer/boolean/null/array/object/json, or use oneOf
```

### 3.4 字段速查

| 字段 | 说明 |
|---|---|
| `name` | 模型看到的工具名，下划线风格（`ask_user_question`） |
| `description` | **极重要**：模型靠它决定是否调用，要写"**什么时候用**" |
| `parameters.<x>.type` | 见 3.3 |
| `parameters.<x>.required` | `true`（属性级） |
| `parameters.<x>.description` | 逐字段描述，模型靠它填参 |
| `parameters.<x>.items` | 数组元素 schema |
| `parameters.<x>.properties` + `additionalProperties` | 对象字段 schema |
| `output.schema` | 返回值结构约束 |
| `output.render` | `(args, value) => [{type:'text', text}]`，渲染成模型可读内容 |
| `execute` | `async (args, exec) => result`；`exec.signal` 取消信号、`exec.agent` 当前 agent |
| `timeoutMs` | 可选，正有限数（写 0 或负数会抛 `timeoutMs must be a positive finite number`） |
| `isConcurrencySafe` | 可选，`() => true` 表示只读可并发 |

### 3.5 ⚠️ 三条易错点

1. **`output.schema` 必须描述返回值结构** —— 模型看到的是它。忘了写或写错，模型会困惑。
2. **`execute` 返回纯数据**（可序列化 JSON）。要逐字段把 `unknown` 收窄（`typeof x === 'string' ? x : ''`），别把 `undefined`/函数/类实例丢回去。
3. **权限与审批不在工具里声明**（主手册 4.7 已讲）。工具只管"能做什么"，"允不允许"由 sandbox/approval 服务管。

### 🤖 让 AI Agent 帮你做 T3

```
帮我写一个 DSH 工具插件，工具名 <tool_name>，它要做 <一句话功能>。

铁律（必须遵守，否则代码跑不起来）：
1. 用 defineTool()，从 '@deepseek-ai/dsh-tools' 导入。
2. 具名导出 name / inject / apply，绝对不要写 export default。
3. parameters 用 DSH 的 Schema DSL：
   - 根是隐式对象，直接写字段名，不要写 type:'object'/properties 包装
   - 必填写在属性级：{ type:'string', required: true, description:'...' }
4. output.schema 描述返回值结构，output.render 返回 [{type:'text', text}]。
5. execute 只返回纯数据，逐字段把 unknown 收窄。
6. inject 里写上你依赖的服务名。

请先告诉我：这个工具应该 inject 哪些服务？依据是什么（哪个官方包的 inject 里有类似服务）？
```

---

## T4 · 工具插件 · 手写 `ToolDefinition`（进阶备选）★★

**它是什么**：绕过 `defineTool`，直接手写 `ToolDefinition` 对象注册。社区插件常用这条路。
**来源**：`Tencent/WeKnora → packages/dsh-weknora/src/tools.ts`（腾讯开源，4 个只读工具，**最干净的社区范本**）。

### 4.1 写法对比（关键差异就一处）

```ts
// 路径 B：先构造 ToolDefinition 数组，再统一注册
const definitions: ToolDefinition[] = []

definitions.push({
  name: name('list_knowledge_bases'),
  description: '...',
  // ⚠️ 这里是【原始 JSON Schema】，不是 DSH DSL
  parameters: { type: 'object', properties: {}, additionalProperties: false },
  timeoutMs: config.requestTimeoutMs,
  isConcurrencySafe: () => true,
  output: {
    schema: {
      type: 'object',
      properties: {
        count: { type: 'integer' },
        knowledge_bases: {
          type: 'array',
          items: {
            type: 'object',
            properties: {
              id: { type: 'string' },
              name: { type: 'string' },
              description: { type: 'string' },
            },
            // ⚠️ 对象级 required 数组
            required: ['id', 'name', 'description'],
            additionalProperties: false,
          },
        },
      },
      required: ['count', 'knowledge_bases'],
      additionalProperties: false,
    },
    render: (_args, value) => { /* 返回文本块 */ },
  },
  async execute(_args, exec) {
    const bases = await client.listKnowledgeBases(exec.signal)
    return {
      count: bases.length,
      knowledge_bases: bases.map(kb => ({
        id: typeof kb.id === 'string' ? kb.id : '',
        // ...
      })),
    }
  },
})
```

带参数的例子（对象级 `required`）：

```ts
  parameters: {
    type: 'object',
    properties: {
      query: { type: 'string', description: 'Natural-language query; a full question retrieves better than keywords.' },
      knowledge_base_ids: { ...STRING_ARRAY, description: 'Restrict the search to these knowledge base ids.' },
      max_results: { type: 'integer', description: 'Maximum passages to return.' },
    },
    required: ['query'],
    additionalProperties: false,
  },
```

### 4.2 两条路怎么选

| | 路径 A `defineTool` | 路径 B 手写 `ToolDefinition` |
|---|---|---|
| 参数校验 | **自动**（`validateJsonSchemaValue`） | 自己保证 |
| 类型推导 | 有（`InferArgs<S>`） | 无 |
| 报错友好度 | 高 | 低 |
| 写法 | DSH DSL | 标准 JSON Schema |
| **推荐** | ✅ **新手一律走这条** | 想要零运行时依赖时才用（见 4.3） |

### 4.3 路径 B 唯一的真实优势：**零依赖**

WeKnora 的做法有一个值得学的技巧：它**不 import 任何 DSH 内部包**，而是手写一份"自己用到的接口"的类型镜像（`src/harness.ts`）。好处是：
- 不会撞上「官方装配不装 peers」的 `Cannot find package '@deepseek-ai/dsh-tools'` 报错（见坑 P18）；
- 不随 DSH 升级被迫重新发布；
- **代价**：DSH 大改字段时编译不报错，要靠 e2e 测试兜底。

---

## T5 · 命令插件（给人用的 `/斜杠命令`）★★

**来源**：官方 `packages/feedback/command-feedback`（提供 `/feedback` 命令）。

### 5.1 核心注册代码（逐字）

```ts
import { CommandDefinitionId } from '@deepseek-ai/dsh-commands/brand'
import type { CommandInvocation, CommandResult } from '@deepseek-ai/dsh-commands'

export const name = 'command-feedback'
export const inject = ['commands']

const USAGE = 'Usage: /feedback <text>'

function executeFeedbackCommand(invocation: CommandInvocation): CommandResult {
  if (invocation.rawInput.trim().length === 0) {
    return { kind: 'error', text: `Feedback text is required. ${USAGE}` }
  }
  recordFeedback(invocation.agent.session, { text: invocation.rawInput })
  return {
    kind: 'success',
    text: `Feedback recorded for session ${invocation.agent.session.id}`,
  }
}

export function apply(ctx: Context): void {
  ctx.commands.register({
    definitionId: CommandDefinitionId('@deepseek-ai/dsh-command-feedback'),
    name: 'feedback',
    description: 'Record feedback about this session',
    input: { hint: '<text>' },
    recordInput: false,
    handler: executeFeedbackCommand,
  })
}
```

### 5.2 参数速查

| 字段 | 值 | 说明 |
|---|---|---|
| `definitionId` | `CommandDefinitionId('@scope/pkg')` | 品牌化 id，**必须用 `CommandDefinitionId()` 包装** |
| `name` | `'feedback'` | 用户敲的 `/feedback` |
| `description` | `string` | 斜杠菜单里显示 |
| `input` | `{ hint: '<text>' }` | 输入提示 |
| `recordInput` | `false` | 是否把输入记进会话日志 |
| `handler` | `(inv) => CommandResult` | 返回值二选一 |

**`CommandResult` 两种形态**：`{ kind: 'success', text }` / `{ kind: 'error', text }`
**`CommandInvocation` 关键字段**：`invocation.rawInput`（用户原始输入）、`invocation.agent`（当前 agent，`agent.session` 是会话）。

### 5.3 命令 vs 工具

| | 命令 Command | 工具 Tool |
|---|---|---|
| 触发者 | **人**（敲 `/xxx`） | **模型**（自动决定调用） |
| 注册 API | `ctx.commands.register({...})` | `ctx.tools.register(defineTool({...}))` |
| 依赖服务 | `inject = ['commands']` | `inject = ['tools', ...]` |
| 典型用途 | 开关模式、导出、清空、反馈 | 读写文件、搜索、调外部 API |

### 5.4 官方内置的 6 个命令（可作范本）

`/compact`、`/feedback`、`/goal`、`/permission`、`/plan`、`/export`

---

## T6 · 可配置插件（让用户不改代码就能调参）★★

**来源**：官方 `packages/context/time-context`（schemastery 路线）+ `packages/plan/plan-mode`（手写校验路线）。

### 6.1 路线一：`export const Config = z.object({...})`（推荐给新手）

```ts
import z from '@deepseek-ai/schemastery'

/** The agent registry that owns pre-step processing. */
export const inject = ['agents', 'sessionProjections']

/** Request-preparation clock formatting and append scheduling. Invalid values fail plugin load. */
export interface Config {
  /** Fallback display zone when the open turn has no unique browser zone. Omit to use the process zone. */
  timeZone?: string
  /** Minimum milliseconds between durable injections in one session. Omit or set to 0 to inject at every eligible step. */
  refreshIntervalMs?: number
}

/** Schemastery validation for {@link Config}. */
export const Config: z<Config> = z.object({
  timeZone: z.string(),
  refreshIntervalMs: z.number(),
})
```

**机制（新手必须懂）**：
- 同一个名字 `Config` 既导出 **TypeScript 接口**，又导出**运行时校验器**（接口与值同名共存）。
- DSH 的加载器看到插件导出的 `Config`，就把它当作 schema，对 `cordis.patch.yml` 里该行的 `config:` 做校验。
- 校验失败 → **插件加载失败**（官方注释原文：`Invalid values fail plugin load.`）。

### 6.2 路线二：手写 `resolveConfig()`（想要"人话报错"时）

```ts
export interface PlanModeConfig {
  /** Guidance rendered as the `plan:policy` prompt section while plan mode is active. */
  section: string
}

export function resolveConfig(config: PlanModeConfig): PlanModeConfig {
  const section = (config as Partial<PlanModeConfig>).section
  // 校验：必须是字符串、非空、且不能有未知键
  throw new Error(`PlanModeConfig has unknown key(s) ${unknown.join(', ')} — config is { section }`)
}
```

> 🔥 这行报错是**教科书级范本**：说清"错在哪"+"期望是什么"。写自己的配置校验时照这个格式抄。

### 6.3 两路线取舍

| | `export const Config = z.object({...})` | 手写 `resolveConfig()` |
|---|---|---|
| 代码量 | 少 | 多 |
| 报错信息 | 库自动生成 | **可以写得非常人话** |
| 适用 | 新手首选 | 想"教会用户怎么配"的场景 |

---

## T7 · 服务插件（给别的插件提供能力）★★★

**来源**：官方 `packages/storage/storage/src/index.ts`（98 行，官方最小服务包）。

### 7.1 🔴 先记最重要的一条：服务插件与函数式插件**导出形式相反**

```ts
// ✅ 服务包：default export 服务类
export default MyService

// ✅ 函数式插件：具名导出 name/inject/apply，绝对没有 default export
export const name = '...'
export const inject = [...]
export function apply(ctx) { ... }
```

**混用会怎样**（官方复盘 0001，真实事故）：
- 官方原文：`service packages default-export their service class; function plugins named-export name / inject / Config / apply and have no default export. Mixing the forms makes the Loader discard the function plugin's namespace.`
- 事故现场：一个多余的 `export default apply` 让 Loader **丢弃了整个命名空间**（`inject`/`name`/`Config` 全丢），插件加载时崩在 `Internal error: cannot get property "agents" without inject`。**178 个绿灯单元测试、100% 行覆盖率，一个都没抓到。**

### 7.2 官方服务插件完整模板（逐字）

```ts
import { Context, Service } from '@deepseek-ai/cordis'

declare module '@deepseek-ai/cordis' {
  interface Context {
    storage: Storage        // ← 声明合并：让 ctx.storage 有类型
  }
}

export class Storage extends Service {
  readonly backend: BackendRegistry = new BackendRegistry()
  private readonly forms = new Map<keyof StorageForms, unknown>()

  constructor(ctx: Context) {
    super(ctx, 'storage')   // ← 服务名（ctx.storage）
  }

  mount<K extends keyof StorageForms>(form: K, facility: StorageForms[K]): () => void {
    if (this.forms.has(form)) {
      throw new StorageError('duplicate-mount', `storage form '${String(form)}' is already mounted`)
    }
    this.forms.set(form, facility)
    // 🔥 返回 disposer：卸载时清干净
    return () => {
      if (this.forms.get(form) === facility) {
        this.forms.delete(form)
      }
    }
  }
}

// Service packages default-export their service class and nothing else
// plugin-shaped (packages/AGENTS.md): mixing a default export with a
// function-plugin `apply` makes the Loader drop the plugin namespace.
export default Storage
```

**挂了之后在 `apply` 里启动它**：

```ts
export function apply(ctx: Context): void {
  ctx.plugin(SessionFeedbackService)   // ← 官方 command-feedback 的写法
}
```

### 7.3 社区的另一条路：函数式插件 + `ctx.provide`

**重要事实**：本次调研的社区插件（MemOS / loopx / archify / better-sidebar 等）**没有一个用 `extends Service`**。它们统一是：

```ts
export const name = 'my-plugin'
export const inject = ['...']
export function apply(ctx: Context, config: Config): void {
  // ① 发布一个服务
  ctx.provide('myServiceName', someValue)      // 官方 ThemeRuntime 的写法
  // 或 ctx.reflect.provide('myServiceName', someValue)   // loopx 的写法
  // ② 类只是普通 class，不继承任何基类
  // ③ 生命周期靠 ctx.effect 返回 disposer 接管
}
```

**两条路都真实存在**，选择建议：

| | `export default class extends Service`（官方） | 函数式 + `ctx.provide`（社区） |
|---|---|---|
| 适合 | 在官方 monorepo 里贡献、要做完整能力 seam | 第三方插件、单个服务 |
| 优点 | Loader 原生生命周期管理、`static inject` 声明 | 与函数式插件同构，好写 |
| 证据 | 官方 `packages/storage`、`packages/skill` | MemOS、loopx、archify |

### 🤖 让 AI Agent 帮你做 T7

```
我要写一个 DSH 服务插件，服务名 <xxx>，能力是 <一句话>。

请严格按官方 packages/storage/storage/src/index.ts 的形态写：
1. export class Xxx extends Service，constructor 里 super(ctx, '<服务名>')
2. declare module '@deepseek-ai/cordis' { interface Context { xxx: Xxx } }
3. 所有"注册型"方法必须返回 disposer，并且要有"陈旧 disposer 守卫"
4. 文件末尾 export default Xxx（服务包必须 default export）
5. 绝对不要在同一个文件里再写 export function apply

另外告诉我：装了这个服务之后，别人应该在 inject 数组里写什么字符串？
```

---

## T8 · 最小 UI 插件 + 插槽机制 ★★★

**来源**：官方 `packages/client/ui-brand-official`（全包 49 行，官方最小的 UI 插件）。
**完整原文见** `plugin-research/notes/E-official-templates.md` 模板 2。

### 8.1 一个 UI 插件 = 两个半侧

```
my-ui-plugin/
├── package.json
├── tsconfig.json          # extends tsconfig.base.client.json（注意是 client 版）
├── tsdown.config.ts
└── src/
    ├── index.ts           # 宿主半侧（node 侧）—— 可以是空的
    └── client/
        ├── index.ts       # 客户端半侧（浏览器侧）—— 真正的 UI 逻辑
        └── MyWidget.tsx   # React 组件
```

### 8.2 `package.json` 的四个关键点（逐字）

```json
{
  "exports": {
    ".": { "types": "./lib/types/index.d.ts", "default": "./lib/index.js" },
    "./client": { "types": "./lib/types/client/index.d.ts", "default": "./lib/client.js" },
    "./src/*": "./src/*",
    "./package.json": "./package.json"
  },
  "dsh": {
    "client": {
      "inject": [
        "@deepseek-ai/dsh-client-ui-renderer",
        "@deepseek-ai/dsh-client-ui-sidebar"
      ],
      "platform": "web"
    }
  },
  "files": ["lib/index.js", "lib/client.js", "lib/types/**/*.d.ts"]
}
```

| # | 关键点 | 漏了会怎样 |
|---|---|---|
| 1 | `exports["./client"]` 指向 `lib/client.js` | 🔥 **客户端半侧根本不会被加载** |
| 2 | `dsh.client.inject` 声明依赖的**包名**数组 | 组装失败 |
| 3 | `dsh.client.platform: "web"` | — |
| 4 | `files` 含 `lib/client.js` | 发布后 UI 半侧丢失 |

### 8.3 宿主半侧可以完全是空的（逐字）

```ts
/**
 * Official browser-brand plugin, node half. The empty apply gives Loader a
 * host-side row while the browser half ships through `exports["./client"]`.
 */

/** Host plugin body — this package contributes browser presentation only. */
export function apply(): void {}
```

> 🔑 **纯 UI 插件的宿主半侧空实现就够了** —— 这是标准形态，不是偷懒。

### 8.4 客户端半侧 + 插槽（逐字）

```ts
import type { Context as ClientContext } from '@deepseek-ai/cordis'
import type {} from '@deepseek-ai/dsh-client-ui-renderer/client'
import type {} from '@deepseek-ai/dsh-client-ui-sidebar/client'
import { OfficialBrandMark, OfficialBrandName } from './Brand.tsx'

/** Required service: the UI slot registry. */
export const inject = ['slots']

export function apply(ctx: ClientContext): void {
  ctx.slots.inject('sidebar.brand.mark', () =>
    ctx.slots.inject('sidebar.brand.name', function* () {
      yield ctx.slots.register({ name: 'sidebar.brand.mark' }, OfficialBrandMark)
      yield ctx.slots.register({ name: 'sidebar.brand.name' }, OfficialBrandName)
    }))
}
```

**三个必记点**：
1. `export const inject = ['slots']` —— 声明依赖 **slots 服务**。
2. `ctx.slots.inject('<插槽名>', () => ...)` —— 往插槽注入；**返回 disposer**。
3. `ctx.slots.register({ name: '<插槽名>' }, 组件)` —— 注册组件；**返回 disposer**。

> 🔥 **`inject` 的两层含义**（新手最容易混）：
> - `package.json` 的 `dsh.client.inject` 是**包级依赖**（字符串包名），决定加载顺序。
> - 代码里的 `export const inject = [...]` 是**服务级依赖**（服务名），决定 `apply` 何时被调用。

### 8.5 已知的 40 个官方插槽名（**最有用的三个先记住**）

| 插槽名 | 用途 |
|---|---|
| `settings.section` | 加一整段设置页 |
| `settings.general.item` | 通用设置里加一行/一项 |
| `conversation.view` | 替换对话主视图（最激进） |

> 完整 40 个见 `plugin-research/notes/E-official-templates.md` 的「官方全部 UI 插槽名」附录。

### 8.6 🔴 UI 插件的三条硬约束

1. **`dsh.client` 与 `exports["./client"]` 必须成对存在**。缺任一个，宿主报 `client package failed to compose`。
2. **浏览器半侧里 `@deepseek-ai/*` 只能写 `import type`**。要用值只用平台种子表允许的四个：`react` / `cordis` / `ui-slots` / `ui-primitives`。越界报：
   ```
   client-modules: require("...") missed the module table — not a platform seed word,
   not a materialized module, and no registered package factory
   ```
3. **不要 `import` 别人的实现**。跨插件协作走 **cordis 服务**（`ctx.slots`/`ctx.sessions`/`ctx.workspaces`）或**插槽**。

### 8.7 样式方案（事实，不猜测）

- **CSS Modules**：`import css from './X.module.css'`
- 全局语义 token 用 `--dsw-alias-*`（**明暗两套都要给**）
- **不要**假设能用 Tailwind

**官方为"只给了一个值"写的教学式报错（逐字，值得学）**：

```ts
throw new TypeError(
  `theme override "${name}" from "${source}" is a bare string — pass { light: ${JSON.stringify(value)}, dark: ${JSON.stringify(value)} } `
  + '(repeat the value when it is the same in both palettes); a single value goes illegible when the user switches color scheme',
)
```

### 🤖 让 AI Agent 帮你做 T8

```
我要给 DSH 的网页界面加一个 <位置描述> 上的 <控件描述>。

请按官方 packages/client/ui-brand-official 的形态写（这是官方最小的 UI 插件）：
1. package.json 必须有 exports["./client"] 和 dsh.client（inject 写包名数组、platform:"web"），
   files 必须含 lib/client.js。
2. 宿主半侧 src/index.ts 可以是 export function apply(): void {} 空实现。
3. 客户端半侧 src/client/index.ts：export const inject = ['slots']，
   用 ctx.slots.inject('<插槽名>', () => ctx.slots.register({ name: '<插槽名>' }, 组件))。
4. 组件用 React + CSS Modules；浏览器半侧里 @deepseek-ai/* 只能 import type。

请先回答：我应该用哪个插槽名？请从官方 40 个插槽名清单里选，并说明依据。
```

---

## T9 · 设置卡片（在设置界面里加一张卡）★★★

**来源**：官方 `packages/client/ui-theme`（它自己就是一个"主题设置"插件）。

### 9.1 `dsh.client` 要加 `immediately`

```json
  "dsh": {
    "client": {
      "inject": [
        "@deepseek-ai/dsh-client-connection",
        "@deepseek-ai/dsh-client-locale",
        "@deepseek-ai/dsh-client-ui-renderer",
        "@deepseek-ai/dsh-client-ui-settings",
        "@deepseek-ai/dsh-api-remotes"
      ],
      "platform": "web",
      "immediately": true
    }
  }
```

> `immediately: true` = **立刻加载**（不等别人按需触发）。设置类插件通常需要。

### 9.2 宿主半侧：注册一个"设置命名空间"（逐字）

```ts
function readSection(ctx: Context): { preference: ThemePreference; fontSize: number } {
  const fallback = { preference: DEFAULT_PREFERENCE, fontSize: DEFAULT_FONT_SIZE }
  const settings = ctx.get('settings')      // ← 探测可选服务，别写 ctx.settings
  if (settings === undefined) return fallback
  const section = settings.get(THEME_NAMESPACE) as ThemeSettings | undefined
  if (section === undefined) return fallback
  return section
}

export function apply(ctx: Context): void {
  // 等 settings 服务就绪后再注册（不要写成硬依赖）
  ctx.inject(['settings'], (settingsCtx) => {
    settingsCtx.settings.register(THEME_NAMESPACE, ThemeSettingsSchema)
  })
  // 往页面 HTML 注入首屏数据，避免闪烁
  ctx.on('webserver/index-inject', (table) => {
    const section = readSection(ctx)
    table.push(bootThemeInjection(section.preference, section.fontSize))
  })
}
```

| API | 用法 |
|---|---|
| `ctx.get('settings')` | **探测**可选服务是否存在（不阻塞加载） |
| `ctx.inject(['settings'], cb)` | 等服务就绪后再执行 `cb` |
| `settings.register(命名空间, Schema)` | 注册一个持久化的设置段 |
| `ctx.on('webserver/index-inject', ...)` | 往页面 HTML 注入行（首屏生效） |

### 9.3 客户端半侧：注册到设置插槽（逐字，关键部分）

```ts
export const inject = ['slots', 'locale', 'remote', 'settingsScope']

export function apply(ctx: ClientContext): void {
  const host = ctx.settingsScope.bind<ThemeSettings>({ namespace: THEME_SETTINGS_NAMESPACE })
  const theme = new ThemeRuntime(ctx, host)
  ctx.provide('theme', theme)

  ctx.effect(() => ctx.locale.register(SETTINGS_NS, { zh, en }), 'ui-theme: settings row dictionaries')

  const store = createAppearanceRowStore()
  let bound: BoundActions<typeof store> | undefined
  const sync = (snapshot: ThemeSnapshot): void => { bound?.sync(snapshot.preference, snapshot.revision) }
  ctx.on('theme/change', sync)

  const injected = (actions: BoundActions<typeof store>): AppearanceRowInjected => {
    bound = actions
    // 从 getter 重新同步，确保注册与首次渲染之间的改动不丢
    sync(theme.getTheme())
    return { setTheme: (id) => { theme.setTheme(id) } }
  }

  ctx.slots.inject('settings.general.item', () => ctx.slots.register({
    name: 'settings.general.item',
    id: 'appearance',
    order: 10,
    store,
    locale: SETTINGS_NS,
    inject: injected,
  }, AppearanceRow))
}
```

**`ctx.slots.register` 的完整参数**：

| 字段 | 说明 |
|---|---|
| `name` | 插槽名（`'settings.general.item'`） |
| `id` | 本注册项在该插槽内的唯一 id |
| `order` | 排序（数字小的在前） |
| `store` | 绑给组件的响应式 store（组件用 `useStore` 消费） |
| `locale` | 文案命名空间 |
| `inject` | 给组件注入"业务动作"的回调工厂 |

### 9.4 组件写法与 props 四件套（逐字）

```tsx
import type { PropsLocale, PropsRuntime, PropsStore } from '@deepseek-ai/dsh-client-ui-slots'
import css from './AppearanceRow.module.css'

/** Full component props: runtime share + store share + locale seat + injected face. */
export type AppearanceRowComponentProps =
  PropsRuntime<'settings.general.item'> & PropsStore<ReturnType<typeof createAppearanceRowStore>>
  & PropsLocale<'settings.theme'> & AppearanceRowInjected

export function AppearanceRow({ t, setTheme, useStore }: AppearanceRowComponentProps) {
  const preference = useStore(s => s.preference)
  return (
    <div className={css.group}>
      <div className={css.title}>{t('appearance.title')}</div>
      <button type="button" onClick={() => { setTheme('dark') }}>{t('appearance.dark')}</button>
    </div>
  )
}
```

**四件套**：`PropsRuntime<'插槽名'>` + `PropsStore<store 类型>` + `PropsLocale<'命名空间'>` + 自己的 `Injected` 面。

### 9.5 ⚠️ 两个真实事故（社区侧证据）

1. **把类实例的方法交给 React 当回调 → 必须 `.bind()`**
   官方 `SettingsScope` 的 `subscribe`/`getSnapshot` 是读 `this.store` 的原型方法，React 的 `useSyncExternalStore` 会当裸函数调用，`this` 变 `undefined`，第一次 `getSnapshot()` 就抛：
   ```
   TypeError: Cannot read properties of undefined (reading 'store')
       at getSnapshot (client.js:998)
   slot entry crashed in 'settings.section'
   ```
   **修复**：`settings.subscribe.bind(settings)`（官方用 `useMemo` 保持稳定身份）。
   **通用规则**：凡是把**类实例的方法**交给 React 当回调，一律 `.bind(instance)`。闭包 store（`createSnapshotStore` 之类）不用 bind。

2. **卡片整个不渲染** → 先看崩溃日志里带的**插槽名**（`slot entry crashed in 'settings.section'`），那是第一手线索。

---

## T10 · Agent 流程拦截（改 Agent 的行为）★★★★

**它是什么**：这是用户特别关心的"**Agent 会话流程设计**"能力。DSH 把 Agent 的每一步都做成了**可拦截的 waterfall 事件**。

### 10.1 核心概念：waterfall（瀑布式事件）

```ts
ctx.on('事件名', async (payload, next) => {
  // ① await next() → 保持原样（继续走后面的监听器）
  const original = await next()
  // ② 返回替换值 → 改变流程
  return modified
  // ③ 不调 next() 就 return → 短路（官方用词：reject）
})
```

> 🔴 **铁律**：waterfall 监听器**必须** `await next()` 或 `return next()`，否则会**静默吃掉**后续所有处理 —— 而且不报错。

### 10.2 两个最关键的拦截点

#### `agent/pre-step` —— **改消息 / 拦步骤**

官方逐字文档（`docs/subsystems/core.zh.md:1076`）：

> ```
> Reject a proposed step or replace the messages that enter it. Calling `next()` preserves the current messages.
> @param payload.agent - the agent proposing the step.
> @param payload.messages - messages removed from the inbox for this step.
> @param payload.turn - the turn that will own the step.
> @param payload.step - the step proposed by the loop.
> @param payload.signal - the current turn's cancellation signal.
> @mode waterfall
> ```

官方定位（`core.zh.md:345` 逐字）：
> `agent/pre-step` 是请求推导前**唯一**的 waterfall 监听器链。

#### `agent/request` —— **改调用配置**

官方逐字文档（`core.zh.md:1090` 附近）：
> Replace the frozen call configuration. `await next()` yields the config the machine would use (agent options on the first request, the logged header afterwards); return a replacement to switch. On step admission, this runs after assembly and `step/start`, before the system prompt and accepted user batch are committed. Cancellation here or during subsequent `prepareCall()` resolution commits neither. The prepared call capability governs prompt admission. **Model-visible content must use logged channels; this waterfall cannot mutate messages.**

### 10.3 其它可用的流程钩子

| 事件名 | 时机 / 能力 |
|---|---|
| `agent/turn-stopping` | 轮次即将结束（在最后一次 steering 排空之前） |
| `agent/request-error` | 失败请求的恢复（如触发重试） |
| `agent/assistant-stream` | 助手流式输出 |
| `llm/stream` | LLM 输出流拦截 |
| `system-prompt/assemble` | 组装 system prompt |
| `approval/request` | 审批决策（第一个应答者占唯一决策槽） |
| `compaction/*` | 上下文压缩的各阶段 |
| `tools/change` | 工具注册表变化 |

### 10.4 ⚠️ 社区真实事故：**用 system prompt 注入内容会被 persona 整段丢弃**

来自 `volcengine/OpenViking` 的坑（详见 `plugin-research/notes/B-tools-external.md` 坑 O1）：
**`agent preset` 的 persona 若声明了 `complete: true`，会丢弃其它插件贡献的 system prompt 段。**
→ 想往 system prompt 里加内容时，**先确认当前 persona 有没有 `complete: true`**。

### 🤖 让 AI Agent 帮你做 T10

```
我要拦截 DSH Agent 的 <某个环节>，做 <某件事>。

请先查阅官方仓库 docs/subsystems/core.zh.md 里这个事件的 waterfall 文档原文，
告诉我：
1. 这个事件的 payload 字段有哪些？每个字段什么含义？
2. 它是 waterfall 还是普通事件？我该不该 await next()？
3. 我的监听器返回什么类型？

然后再写代码。要求：
- 具名导出 name/inject/apply，不要 export default
- 所有注册都包 ctx.effect 并返回 disposer
- 铁律：waterfall 监听器必须 await next() 或 return next()，否则会静默吃掉后续处理
- 请在代码注释里写出你引用的官方文档路径
```

---

## T11 · 外部集成（HTTP / CLI / 协议）★★★

**两条路**：

| 路 | 做法 | 范本 | 什么时候用 |
|---|---|---|---|
| **零代码** | 对方已有 MCP server → 用 `@deepseek-ai/dsh-mcp-client` 挂 | **T1**（ouroboros） | **首选**，不写代码 |
| **写代码** | 自己写 `defineTool` 封装 HTTP/CLI | **T3/T4** | 对方没有 MCP，或需要特殊处理 |

### 11.1 从 ouroboros 学到的 3 条集成硬知识

1. 🔥 **子进程环境会被清洗**：凭据形状的名字（`/KEY|PASSWORD|SECRET|TOKEN/i`）和所有 `DSH_*` 会被移除。**要传的凭据必须显式列在 `config.env` 里**。
2. **长任务必须显式加大超时**：MCP 客户端默认 60s，长流程要写 `toolCallTimeoutMs: 1800000`。
3. **`failOnStartupError: false` 做软失败**：外部依赖没装好时，DSH 仍能正常启动。

### 11.2 社区踩过的外部调用坑（详见 `notes/B-tools-external.md`）

| 坑 | 教训 |
|---|---|
| 无 scope 的检索调用 → 模型收到不透明的 HTTP 400 | 错误信息要**给人/模型看得懂**，别只回状态码 |
| SSE 流被截断时把半截答案当完整答案 | 流式响应必须校验完整性 |
| dsh 会 scrub 掉继承环境里的"凭据形状"变量 | 同 11.1 第 1 条 |
| 工具结果用 camelCase 的 `isError`，插件只认 `is_error` | **字段名大小写**是跨系统集成的头号坑；以宿主的实际字段为准 |
| MCP 代理**自身超时**被当成"服务器不可达"上报 | 区分"我方超时"和"对方不可达" |
| Node 的 `fetch` 默认无视代理环境变量 | 需要代理时要显式配置 |
| 外部 provider 返回的 JSON 不符合声明的 schema | 收到外部数据必须**逐字段校验**，别直接透传 |

---

## T12 · 工程化骨架（完整规范的插件工程）★★★

### 12.1 官方标准目录（逐字，`docs/cookbook/adding-a-package.zh.md §1`）

```
packages/<group>/<pkg>/
  package.json     # copy from packages/core/tools, adjust name/description/deps
  tsconfig.json    # extends ../../../tsconfig.base.json, rootDir src,
                   # outDir lib/types, references: ../../../vendor/cosmokit,
                   # ../../../vendor/cordis (+ ../../../vendor/schemastery if
                   # you use Config, + ../../<group>/<dep> for each dsh dep)
  src/index.ts     # service default export or plugin (name/inject/apply/Config)
  README.md        # service API, events, extension points, design notes,
                   # + gated Model Experience context blocks or short form
                   # + the gated "Known Limitations and Deferred Work" section
```

> 🔑 那一行 `src/index.ts  # service default export or plugin (name/inject/apply/Config)` —— 官方一句话说清两种形态的选择。

### 12.2 第三方插件推荐目录（把官方约定搬到独立仓库）

```
my-dsh-plugin/
├── package.json
├── tsconfig.json
├── tsdown.config.ts          # 仅 UI 插件需要
├── cordis.patch.yml          # 仅组合包需要
├── README.md                 # 必须写：功能/前置要求/配置项/已知限制
├── src/
│   ├── index.ts              # 宿主半侧：apply()
│   ├── types.ts              # 只放类型，不放运行时代码
│   └── client/               # 仅 UI 插件
│       ├── index.ts
│       ├── Widget.tsx
│       └── Widget.module.css
└── tests/                    # 测试放这里，不是 src/__tests__/
    └── my-plugin.spec.ts
```

### 12.3 `package.json` 不变式（逐字）

> `private: true`，`version` 与根 `package.json` 一致，`type: module`，`main: "lib/index.js"`，`types: "lib/types/index.d.ts"`，`exports["."].types: "./lib/types/index.d.ts"`，`exports["."].default: "./lib/index.js"`，`@deepseek-ai/cordis` 同时出现在 peerDependencies 和 devDependencies 中（相同范围）。每个 dsh 对等依赖（peer dependency）都要在 devDependencies 中镜像。`@deepseek-ai/schemastery` 放在 `dependencies` 中（它是运行时校验器），与 agent-loop 保持一致。`files` 列表精确包含 `lib/index.js`、`lib/types/**/*.d.ts` …

### 12.4 相对导入必须写 `.ts` 后缀（逐字）

> 包内的相对导入在源码中使用显式 `.ts` 后缀（例如 `export * from './types.ts'`）。编译器在输出的 JS 中将其重写为 `.js`，在声明文件中保留显式 `.ts` 后缀。

> 💡 所以官方代码里全是 `from './types.ts'`、`from './Brand.tsx'` —— **这是官方要求，不是笔误**。

### 12.5 发布前自查

```bash
npx publint          # 检查 exports / files 是否配错（最有用的一条）
```

官方完整门禁清单见 `plugin-research/notes/J-official-conventions.md`。

### 12.6 命名别纠结：官方角色命名表（节选）

| 词 | 什么时候用 | **不该**用的时候 |
|---|---|---|
| `Registry` | 拥有一组动态具名注册 + 查询/重复项/优先级/生命周期 | 主要约定是分派、执行、取消 |
| `Store` | 拥有一组数据，提供 CRUD/snapshot/subscription | 校验状态机、裁决权限。**类里有 map ≠ store** |
| `Runtime` | 跑实时工作，跨调用拥有分派/取消/生命周期 | 只存记录、只返回目录 |
| `Policy` | 决定允许/选择/限制什么 | 执行该决定所允许的机制 |
| `Gateway` | 适配进程、网络、RPC 或 API 边界 | 只注册同进程服务 |
| `Provider` | 提供某项能力的一个实现（多实现加厂商限定词） | 表示能力定义或 provider registry |
| `Controller` | 接受命令/用户意图并改变领域状态 | 执行任意工作、拥有一组 provider |
| `Service` | 无法用以上更精确角色诚实描述的内聚领域服务 | **只因为继承了 Cordis `Service`** |

> 🔑 官方还规定：**单数 key 用于 engine/runtime/policy/controller/resolver/store/当前配置；复数 key 用于 registry/多具名成员的服务**。类的角色与 key 的单复数必须一致。

### 12.7 README 必须包含的两节（官方强制）

```
## Model Experience        # 这个插件对模型的请求上下文有什么影响（token / KV cache）
## Known Limitations and Deferred Work   # 诚实清单：已知限制与没做的事
```

> 💡 即使你不在官方仓库，**照抄这两节**会让你的插件 README 质量立刻上一个档次 —— 尤其"已知限制"这节，能极大减少用户的困惑。

---


---

<!-- ↓ 源：E-official-templates.md （全文） -->

# E. 官方自带插件 —— 七类可复用模板（原始素材）

> 来源：`D:/WorkBuddy/2026-09-11-11-58-02/deepseek-harness`（完整克隆，commit `c291e7961a`，`0.1.5-rc.2`）。
> 所有代码**逐字照抄**仓库原文，未改写。每个模板标注来源文件路径。
> 面向《DSH 插件开发实战手册》补充篇，读者为零软件工程经验新手。

---

## 0. 官方插件全景（实证数字）

| 事实 | 数值 | 取证命令 |
|---|---|---|
| 声明 `dsh` 清单的官方包 | **70** | `grep -rl '"dsh"\s*:' packages/*/*/package.json \| wc -l` |
| 其中 `packages/client/*`（UI 插件） | **46** | 同上，按目录分组统计 |
| `packages/bundle/*`（组合包） | 6 | |
| `packages/api/*`（宿主 RPC） | 5 | |
| `packages/experimental/*` | 4 | |
| `packages/session/*` | 3 | |
| `packages/subagent/*` | 2 | |
| `packages/extensions/*` | 2 | |

**`dsh` 字段只有两种形态**（去重后）：
- `{"bundle": {"patch": "./cordis.patch.yml"}}` ×10 —— 组合包（配置型插件）
- `{"client": {"inject": [...], "platform": "web", "immediately"?: true, "external"?: [...]}}` ×其余 —— 客户端（UI）插件

**官方包命名**：宿主侧 `@deepseek-ai/dsh-<域>-<名>`；客户端侧 `@deepseek-ai/dsh-client-<域>-<名>`。

**官方顶层分组（51 个域）**：
`acp api attachment boot bundle client code-runtime compaction context core credentials e2b experimental extensions feedback fs goal guard hooks host identity interaction jobs llm lsp mcp plan preset runtime-diagnostics sandbox schedule sdk session session-query settings shell skill spill storage subagent subprocess terminal test-support todo typert util web webhook workflow workspace`

---

## 模板 1 · 纯配置组合包（零代码插件）

**学习点**：插件可以**不写任何运行时代码**，只靠一个 YAML 补丁文件描述"要挂载哪些行"。

**来源**：`packages/bundle/base`（`src/index.ts` 仅 9 行）

### 1.1 `package.json`（关键字段）

```json
{
  "name": "@deepseek-ai/dsh-base",
  "version": "0.1.5-rc.2",
  "type": "module",
  "main": "lib/index.js",
  "types": "lib/types/index.d.ts",
  "exports": {
    ".": {
      "types": "./lib/types/index.d.ts",
      "default": "./lib/index.js"
    },
    "./cordis.patch.yml": "./cordis.patch.yml",
    "./src/*": "./src/*",
    "./package.json": "./package.json"
  },
  "files": [
    "lib/index.js",
    "cordis.patch.yml",
    "lib/types/**/*.d.ts"
  ],
  "license": "MIT",
  "dsh": {
    "bundle": {
      "patch": "./cordis.patch.yml"
    }
  }
}
```

> ⚠️ 注意 `files` 必须包含 `cordis.patch.yml`，否则发布到 npm 后补丁文件丢失，插件装上等于没装。同时 `exports` 里要有 `"./cordis.patch.yml": "./cordis.patch.yml"`。

### 1.2 `src/index.ts`（全文）

```ts
/**
 * @deepseek-ai/dsh-base — the shared dsh core as a profile bundle. The
 * package's substance is `cordis.patch.yml`, declared by the `dsh.bundle.patch`
 * manifest field and resolved by the profile composer through that field;
 * this module carries no runtime API.
 * @module @deepseek-ai/dsh-base
 */

export {}
```

### 1.3 `cordis.patch.yml` 语法（从 `packages/bundle/base/cordis.patch.yml` 提炼）

补丁文件用 **`insert:` 列表**，每行一个插件节点：

```yaml
- insert:
    - id: timer
      name: '@deepseek-ai/cordis-plugin-timer'

    - id: hmr
      name: '@deepseek-ai/cordis-plugin-hmr'
      disabled: true
      config:
        root: ['.']

    - id: agent-default-model
      name: '@deepseek-ai/dsh-agent-default-model'
      config:
        provider: deepseek-official
        model: deepseek-flash

    - id: session-title
      name: '@deepseek-ai/dsh-session-title'
      config:
        fallbackMaxWords: 5
        fallbackMaxBytes: 40
        maxTitleBytes: 80
```

**字段语义（原文注释 + 结构实证）**：

| 字段 | 含义 |
|---|---|
| `id` | 行标识。后续补丁层与用户的 `cordis.patch.yml` 靠它**覆盖**该行，**逐行 last-write-wins** |
| `name` | 包名（npm 包名，可指向子路径如 `@deepseek-ai/dsh-tool-subagent-control/list-agents`） |
| `disabled` | `true` 关闭该行；可用 `!!js` 表达式（见下） |
| `config` | 传给该插件的配置对象。**补丁替换整段 config，不做合并**（原文注释明确） |

**`!!js` 内联表达式**（原文出现，可直接抄）：

```yaml
    - id: session-persistence-jsonl
      name: '@deepseek-ai/dsh-session-persistence-jsonl'
      config:
        root: !!js dshHomePath('sessions')

    - id: sandbox-policy
      name: '@deepseek-ai/dsh-sandbox-policy'
      config:
        mode: !!js process.env.DSH_PERMISSION_MODE ?? 'workspace-write'
        workspaceRoot: !!js process.cwd()

    - id: bash-sandbox
      name: '@deepseek-ai/dsh-bash-sandbox'
      disabled: !!js process.platform === 'win32'
      config:
        timeoutMs: 60000
```

> 🔥 **跨平台写法必抄**：官方用 `disabled: !!js process.platform === 'win32'` 让 bash 工具只在非 Windows 启用、pwsh 工具只在 Windows 启用。这是处理平台差异的**官方姿势**。

**原文关键约束（逐字摘录，对写补丁极重要）**：

> A patch replaces the targeted row's whole `config` rather than merging into it, so a row whose value differs by mode does NOT live here: it belongs to each mode bundle, keeping any single row down to one bundle layer plus the user's.

> Row order carries no load semantics (activation is service-availability driven); the grouping is for readers.

**第二条极其关键**：**行的书写顺序不影响加载顺序**，激活由「服务可用性」驱动。这是新手最常见的误解（以为要按依赖顺序写）。

---

## 模板 2 · 最小 UI 插件（客户端半侧 + 插槽）

**学习点**：UI 插件 = 一个空的宿主半侧 + 一个客户端半侧。UI 通过**命名插槽（slot）**注入，不直接改别人的界面。

**来源**：`packages/client/ui-brand-official`（全包 49 行）

### 2.1 `package.json`（关键字段）

```json
{
  "name": "@deepseek-ai/dsh-client-ui-brand-official",
  "version": "0.1.5-rc.2",
  "type": "module",
  "main": "lib/index.js",
  "types": "lib/types/index.d.ts",
  "exports": {
    ".": {
      "types": "./lib/types/index.d.ts",
      "default": "./lib/index.js"
    },
    "./client": {
      "types": "./lib/types/client/index.d.ts",
      "default": "./lib/client.js"
    },
    "./src/*": "./src/*",
    "./package.json": "./package.json"
  },
  "dsh": {
    "client": {
      "inject": [
        "@deepseek-ai/dsh-client-ui-renderer",
        "@deepseek-ai/dsh-client-ui-sidebar"
      ],
      "platform": "web"
    }
  },
  "scripts": {
    "bundle": "tsdown",
    "watch": "tsdown --watch"
  },
  "license": "MIT",
  "peerDependencies": {
    "@deepseek-ai/cordis": "workspace:^"
  },
  "devDependencies": {
    "@deepseek-ai/dsh-client-ui-primitives": "workspace:^",
    "@deepseek-ai/dsh-client-ui-renderer": "workspace:^",
    "@deepseek-ai/dsh-client-ui-sidebar": "workspace:^",
    "@deepseek-ai/cordis": "workspace:^",
    "@testing-library/react": "^16.1.0",
    "@types/react": "~18.3.1",
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "files": [
    "lib/index.js",
    "lib/client.js",
    "lib/types/**/*.d.ts"
  ]
}
```

**四个必记点**：
1. `exports["./client"]` 指向客户端 bundle（`lib/client.js`）——**缺了它 UI 半侧不会被加载**。
2. `dsh.client.inject` 声明"我依赖哪些客户端插件"，值为**包名数组**。
3. `dsh.client.platform: "web"`。
4. `files` 必须含 `lib/client.js`。

### 2.2 宿主半侧 `src/index.ts`（全文）

```ts
/**
 * Official browser-brand plugin, node half. The empty apply gives Loader a
 * host-side row while the browser half ships through `exports["./client"]`.
 */

/** Host plugin body — this package contributes browser presentation only. */
export function apply(): void {}
```

> 宿主半侧**空实现**就够了 —— 这是纯 UI 插件的标准形态。

### 2.3 客户端半侧 `src/client/index.ts`（全文）

```ts
/** Official DeepSeek Harness occupants for the generic browser-brand slots. */
import type { Context as ClientContext } from '@deepseek-ai/cordis'
import type {} from '@deepseek-ai/dsh-client-ui-renderer/client'
import type {} from '@deepseek-ai/dsh-client-ui-sidebar/client'
import { OfficialBrandMark, OfficialBrandName } from './Brand.tsx'

/** Required service: the UI slot registry. */
export const inject = ['slots']

/**
 * Fill the sidebar brand slots as one declaration-aware registration set. The
 * conversation hero stays on its declaring package's animated fish fallback,
 * so the official build registers nothing there.
 * @param ctx - Client root context.
 */
export function apply(ctx: ClientContext): void {
  if (process.env.DSH_CLIENT_BUILD_PROFILE !== 'official') return
  ctx.slots.inject('sidebar.brand.mark', () =>
    ctx.slots.inject('sidebar.brand.name', function* () {
      yield ctx.slots.register({ name: 'sidebar.brand.mark' }, OfficialBrandMark)
      yield ctx.slots.register({ name: 'sidebar.brand.name' }, OfficialBrandName)
    }))
}
```

**三个必记点**：
1. `export const inject = ['slots']` —— 声明依赖 **slots 服务**（UI 插槽注册表）。
2. `ctx.slots.inject('<slot名>', () => ...)` —— 往某插槽注入；**返回 disposer**，用于卸载。
3. `ctx.slots.register({ name: '<slot名>' }, 组件)` —— 注册组件；**返回 disposer**。

> 🔥 **`inject` 的两层含义**（新手最容易混）：
> - `package.json` 的 `dsh.client.inject` 是**包级依赖**（字符串包名），决定加载顺序。
> - 代码里的 `export const inject = [...]` 是**服务级依赖**（服务名），决定 `apply` 何时被调用。
> 两者名字像、层级完全不同。

### 2.4 组件 `src/client/Brand.tsx`（全文）

```tsx
import { BrandWordmark, FishLogo } from '@deepseek-ai/dsh-client-ui-primitives'
import type { SidebarBrandMarkOwnerProps } from '@deepseek-ai/dsh-client-ui-sidebar/client'

/**
 * Render the official mark with the presentation requested by its host surface.
 * @param props - Host-supplied mark presentation.
 * @returns the official whale mark.
 */
export function OfficialBrandMark({ size }: SidebarBrandMarkOwnerProps) {
  return <FishLogo size={size} />
}

/**
 * Render the official name artwork without its independently slotted mark.
 * @returns the official name wordmark.
 */
export function OfficialBrandName() {
  return <BrandWordmark includeMark={false} />
}
```

> 前端框架 = **React 18 + TSX**（`react`/`react-dom` 为 `devDependencies`，由宿主提供）。

### 2.5 构建配置 `tsdown.config.ts`（全文）

```ts
import { clientBundle } from '../tsdown.client.ts'

export default clientBundle('@deepseek-ai/dsh-client-ui-brand-official', ['lib/types/index.js'])
```

### 2.6 `tsconfig.json`（全文）

```json
{
  "extends": "../../../tsconfig.base.client.json",
  "compilerOptions": {
    "rootDir": "src",
    "outDir": "lib/types"
  },
  "include": [
    "src"
  ],
  "references": [
    {
      "path": "../../../vendor/cordis"
    },
    {
      "path": "../ui-renderer"
    },
    {
      "path": "../ui-primitives"
    },
    {
      "path": "../ui-sidebar"
    },
    {
      "path": "../ui-slots"
    }
  ]
}
```

> ⚠️ `extends` 的是 **客户端专用** 基座 `tsconfig.base.client.json`（不是服务端的）。

---

## 模板 3 · 工具插件（`defineTool`）

**学习点**：给模型加一个可调用的工具。这是"外部调用/集成方向"的骨架。

**来源**：`packages/interaction/tool-ask-user`（全包 101 行，官方最小的工具插件）

### 3.1 `package.json` 关键字段

```json
{
  "name": "@deepseek-ai/dsh-tool-ask-user",
  "version": "0.1.5-rc.2",
  "type": "module",
  "main": "lib/index.js",
  "types": "lib/types/index.d.ts",
  "exports": {
    ".": {
      "types": "./lib/types/index.d.ts",
      "default": "./lib/index.js"
    },
    "./src/*": "./src/*",
    "./package.json": "./package.json"
  },
  "files": ["lib/index.js", "lib/types/**/*.d.ts"],
  "license": "MIT",
  "peerDependencies": {
    "@deepseek-ai/dsh-agent": "workspace:^",
    "@deepseek-ai/dsh-tools": "workspace:^",
    "@deepseek-ai/dsh-user-questions": "workspace:^",
    "@deepseek-ai/cordis": "workspace:^"
  }
}
```

> 💡 **工具插件没有 `dsh` 字段**！它靠"依赖被谁挂载"进入组合，不需要 `dsh.bundle` 或 `dsh.client`。这是和 UI 插件/组合包的**关键差异**。

### 3.2 `src/index.ts`（全文，逐字）

```ts
/**
 * Model-facing Consumer of the `ctx.userQuestions` capability seam.
 * The tool pauses until a UI provider returns a human answer, then feeds that
 * answer back into the agent loop as an ordinary tool result.
 *
 * @module @deepseek-ai/dsh-tool-ask-user
 */

import type { Context } from '@deepseek-ai/cordis'
import { defineTool } from '@deepseek-ai/dsh-tools'
import '@deepseek-ai/dsh-user-questions'

export const name = 'tool-ask-user'
export const inject = ['tools', 'userQuestions']

const description = 'Ask the user a concise question when you need confirmation, a choice, or missing information before proceeding. '
  + 'Send one or more questions, each with a stable id that will be echoed in the answer.'

export function apply(ctx: Context): void {
  ctx.tools.register(defineTool({
    name: 'ask_user_question',
    description,
    parameters: {
      questions: {
        type: 'array',
        required: true,
        description: 'Questions to ask the user before continuing.',
        items: {
          type: 'object',
          additionalProperties: true,
          properties: {
            id: { type: 'string', required: true, description: 'Stable id for this question; echoed in the answer.' },
            question: { type: 'string', required: true, description: 'The specific question to ask the user.' },
            header: {
              type: 'string',
              description: 'Optional short heading for the question, such as "Confirm" or "Choose Mode".',
            },
            options: {
              type: 'array',
              description: 'Optional choices to show the user. If you recommend one, put it first and append "(Recommended)" to that label.',
              items: {
                type: 'object',
                additionalProperties: true,
                properties: {
                  label: { type: 'string', required: true, description: 'Short user-facing option label.' },
                  description: { type: 'string', description: 'One sentence explaining the tradeoff or impact.' },
                },
              },
            },
            multi_select: {
              type: 'boolean',
              description: 'Whether the user may select more than one option. Defaults to false.',
            },
          },
        },
      },
    },
    output: {
      schema: {
        type: 'object',
        additionalProperties: false,
        properties: {
          answers: {
            type: 'array',
            required: true,
            items: {
              type: 'object',
              additionalProperties: false,
              properties: {
                id: { type: 'string', required: true },
                selected: { type: 'array', required: true, items: { type: 'string' } },
                custom: { type: 'string' },
              },
            },
          },
        },
      },
      render: (_args, value) => [{ type: 'text', text: JSON.stringify(value) }],
    },
    async execute(args, exec) {
      const result = await ctx.userQuestions.ask({
        questions: args.questions.map(question => ({
          id: question.id,
          question: question.question,
          ...question.header !== undefined ? { header: question.header } : {},
          ...question.options !== undefined ? { options: question.options } : {},
          ...question.multi_select !== undefined ? { multiSelect: question.multi_select } : {},
        })),
        ...exec.agent !== undefined ? { agent: exec.agent } : {},
        signal: exec.signal,
      })
      return {
        answers: result.answers.map(answer => ({
          id: answer.id,
          selected: [...answer.selected],
          ...answer.custom !== undefined ? { custom: answer.custom } : {},
        })),
      }
    },
  }))
}
```

### 3.3 `defineTool` 参数结构（速查表）

| 字段 | 类型/写法 | 说明 |
|---|---|---|
| `name` | `string` | 模型看到的工具名，下划线风格（`ask_user_question`） |
| `description` | `string` | **极重要**：模型靠它决定是否调用，要写"什么时候用" |
| `parameters` | 对象字面量（**不是** JSON Schema 顶层 `type/properties` 包装） | 直接写字段名 → `{type, required, description, items/properties}` |
| `parameters.<x>.type` | `'string' \| 'number' \| 'boolean' \| 'array' \| 'object'` | |
| `parameters.<x>.required` | `true` / 省略 | **`required` 写在字段里**，不是单独的 required 数组 |
| `parameters.<x>.description` | `string` | 逐字段描述，模型靠它填参 |
| `parameters.<x>.items` | 数组元素 schema | 数组用 `items` |
| `parameters.<x>.properties` | 对象字段 schema | 对象用 `properties` + `additionalProperties` |
| `output.schema` | JSON Schema | 返回值的结构约束 |
| `output.render` | `(args, value) => [{type:'text', text}]` | 渲染成模型可读内容 |
| `execute` | `async (args, exec) => result` | 业务逻辑；`exec.signal` 是取消信号，`exec.agent` 是当前 agent |

> 🔥 **与网上旧教程的关键差异**：`parameters` **不是**原始 JSON Schema（旧写法是 `parameters: {type:'object', properties:{...}, required:[...]}`）。新版是"字段名直接铺平 + `required` 内联"的 DSL。抄错会完全不工作。

---

## 模板 4 · 命令插件（`/斜杠命令`）

**来源**：`packages/feedback/command-feedback`

### 4.1 核心注册代码（逐字摘录）

```ts
import { CommandDefinitionId } from '@deepseek-ai/dsh-commands/brand'
import type { CommandInvocation, CommandResult } from '@deepseek-ai/dsh-commands'

export const name = 'command-feedback'
export const inject = ['commands']

const USAGE = 'Usage: /feedback <text>'

function executeFeedbackCommand(invocation: CommandInvocation): CommandResult {
  if (invocation.rawInput.trim().length === 0) {
    return { kind: 'error', text: `Feedback text is required. ${USAGE}` }
  }
  recordFeedback(invocation.agent.session, { text: invocation.rawInput })
  return {
    kind: 'success',
    text: `Feedback recorded for session ${invocation.agent.session.id}\nAnonymous user: ${getOrCreateAnonymousUserId()}.`,
  }
}

export function apply(ctx: Context): void {
  ctx.plugin(SessionFeedbackService)
  ctx.commands.register({
    definitionId: CommandDefinitionId('@deepseek-ai/dsh-command-feedback'),
    name: 'feedback',
    description: 'Record feedback about this session',
    input: { hint: '<text>' },
    recordInput: false,
    handler: executeFeedbackCommand,
  })
}
```

### 4.2 命令注册参数速查

| 字段 | 值 | 说明 |
|---|---|---|
| `definitionId` | `CommandDefinitionId('@scope/pkg')` | 品牌化 id，**必须用 `CommandDefinitionId()` 包装** |
| `name` | `'feedback'` | 用户在输入框敲的 `/feedback` |
| `description` | `string` | 斜杠菜单里显示 |
| `input` | `{ hint: '<text>' }` | 输入提示 |
| `recordInput` | `false` | 是否把输入记进会话日志 |
| `handler` | `(inv: CommandInvocation) => CommandResult` | 返回值二选一 |

**`CommandResult` 两种形态**：
- 成功：`{ kind: 'success', text: string }`
- 失败：`{ kind: 'error', text: string }`

**`CommandInvocation` 关键字段**：`invocation.rawInput`（用户原始输入）、`invocation.agent`（当前 agent，`agent.session` 是会话）。

### 4.3 「命令 vs 工具」怎么选

| | 命令 Command | 工具 Tool |
|---|---|---|
| 触发者 | **人**（敲 `/xxx`） | **模型**（自动决定调用） |
| 注册 API | `ctx.commands.register({...})` | `ctx.tools.register(defineTool({...}))` |
| 依赖服务 | `inject = ['commands']` | `inject = ['tools', ...]` |
| 典型用途 | 开关模式、导出、清空、反馈 | 读写文件、搜索、调外部 API |

---

## 模板 5 · 可配置插件（Config Schema）

**学习点**：让用户在 `cordis.patch.yml` 的 `config:` 里配置你的插件，并在加载时校验。

**来源**：`packages/context/time-context`

### 5.1 极简写法（推荐给新手）

```ts
import zd from '@deepseek-ai/schemastery'   // 注意：官方此文件里 import 名是 z（见下）

/** The agent registry that owns pre-step processing. */
export const inject = ['agents', 'sessionProjections']

/** Request-preparation clock formatting and append scheduling. Invalid values fail plugin load. */
export interface Config {
  /** Fallback display zone when the open turn has no unique browser zone. Omit to use the process zone. */
  timeZone?: string
  /** Minimum milliseconds between durable injections in one session. Omit or set to 0 to inject at every eligible step. */
  refreshIntervalMs?: number
}

/** Schemastery validation for {@link Config}. */
export const Config: z<Config> = z.object({
  timeZone: z.string(),
  refreshIntervalMs: z.number(),
})
```

> 原文 import 行逐字为：`import z from '@deepseek-ai/schemastery'`

**机制（关键，新手必须懂）**：
- 同一个名字 `Config` 既导出 **TypeScript 接口**，又导出**运行时校验器**（接口与值同名共存）。
- DSH 的加载器看到插件模块导出的 `Config`，就把它当作 schema，对 `cordis.patch.yml` 里该行的 `config:` 做校验。
- 校验失败 → **插件加载失败**（官方注释原文：`Invalid values fail plugin load.`）。

### 5.2 手写校验（另一条路，无 schema 依赖）

**来源**：`packages/plan/plan-mode`

```ts
/** Deployment-owned plan guidance. */
export interface PlanModeConfig {
  /** Guidance rendered as the `plan:policy` prompt section while plan mode is active. */
  section: string
}

export function resolveConfig(config: PlanModeConfig): PlanModeConfig {
  const section = (config as Partial<PlanModeConfig>).section
  // (原文随后校验：必须是字符串、非空、且不能有未知键)
  ...
  throw new Error(`PlanModeConfig has unknown key(s) ${unknown.join(', ')} — config is { section }`)
}
```

**两条路的取舍**：

| | `export const Config = z.object({...})` | 手写 `resolveConfig()` |
|---|---|---|
| 代码量 | 少 | 多 |
| 报错信息 | 库自动生成 | **可以写得非常人话** |
| 适用 | 新手首选 | 想要"教会用户怎么配"的场景 |

> 🔥 `resolveConfig` 抛出的 `PlanModeConfig has unknown key(s) ... — config is { section }` 是**教科书级错误信息**：说清错在哪、期望是什么。写自己的配置校验时照这个格式抄。

### 5.3 在 `cordis.patch.yml` 里消费配置

```yaml
    - id: plan-mode
      name: '@deepseek-ai/dsh-plan-mode'
      config:
        section: |
              You are in plan mode. Stay in plan mode until exit_plan_mode succeeds...
```

---

## 模板 6 · 设置卡片插件（在设置界面加一张卡）

**学习点**：UI 插件往 `settings.general.item` 这类插槽塞一个 React 组件，并通过宿主 settings 服务持久化。

**来源**：`packages/client/ui-theme`

### 6.1 `package.json` 的 `dsh.client`

```json
  "dsh": {
    "client": {
      "inject": [
        "@deepseek-ai/dsh-client-connection",
        "@deepseek-ai/dsh-client-locale",
        "@deepseek-ai/dsh-client-ui-renderer",
        "@deepseek-ai/dsh-client-ui-settings",
        "@deepseek-ai/dsh-api-remotes"
      ],
      "platform": "web",
      "immediately": true
    }
  }
```

> `immediately: true` = **立刻加载**（不等别人按需触发）。设置类插件通常需要。

### 6.2 宿主半侧注册"设置命名空间"（`src/index.ts` 摘录）

```ts
/** Read the registered theme section or the schema defaults without a settings provider. */
function readSection(ctx: Context): { preference: ThemePreference; fontSize: number } {
  const fallback = { preference: DEFAULT_PREFERENCE, fontSize: DEFAULT_FONT_SIZE }
  const settings = ctx.get('settings')
  if (settings === undefined) return fallback
  const section = settings.get(THEME_NAMESPACE) as ThemeSettings | undefined
  if (section === undefined) return fallback
  return section
}

export function apply(ctx: Context): void {
  ctx.inject(['settings'], (settingsCtx) => {
    settingsCtx.settings.register(THEME_NAMESPACE, ThemeSettingsSchema)
  })
  ctx.on('webserver/index-inject', (table) => {
    const section = readSection(ctx)
    table.push(bootThemeInjection(section.preference, section.fontSize))
  })
}
```

**必记点**：
- `ctx.get('settings')` —— **探测**可选服务是否存在（不阻塞加载）。
- `ctx.inject(['settings'], cb)` —— **等服务就绪后再执行** `cb`（不要写成硬依赖）。
- `settingsCtx.settings.register(命名空间, Schema)` —— 注册一个持久化的设置段。
- `ctx.on('webserver/index-inject', ...)` —— 往页面 HTML 注入行（首屏生效，避免闪烁）。

### 6.3 客户端半侧注册到设置插槽（`src/client/index.ts` 摘录）

```ts
/**
 * Required services: settings transport plus slots/locale for the Appearance
 * row. `remote` carries the forwarded settings invalidation that
 * `ctx.settingsScope.bind(spec)` subscribes to on this context.
 */
export const inject = ['slots', 'locale', 'remote', 'settingsScope']

export function apply(ctx: ClientContext): void {
  installThemeStyles(ctx)
  const host = ctx.settingsScope.bind<ThemeSettings>({ namespace: THEME_SETTINGS_NAMESPACE })
  const theme = new ThemeRuntime(ctx, host)
  ctx.provide('theme', theme)

  ctx.effect(() => ctx.locale.register(SETTINGS_NS, { zh, en }), 'ui-theme: settings row dictionaries')

  const store = createAppearanceRowStore()
  let bound: BoundActions<typeof store> | undefined
  const sync = (snapshot: ThemeSnapshot): void => {
    bound?.sync(snapshot.preference, snapshot.revision)
  }
  ctx.on('theme/change', sync)
  const injected = (actions: BoundActions<typeof store>): AppearanceRowInjected => {
    bound = actions
    // Re-sync from the getter so no event is lost between registration and
    // first render (the store's revision guard drops stale duplicates).
    sync(theme.getTheme())
    return {
      setTheme: (id) => { theme.setTheme(id) },
    }
  }
  ctx.slots.inject('settings.general.item', () => ctx.slots.register({
    name: 'settings.general.item',
    id: 'appearance',
    order: 10,
    store,
    locale: SETTINGS_NS,
    inject: injected,
  }, AppearanceRow))
}
```

**`ctx.slots.register` 的完整参数（UI 高级用法）**：

| 字段 | 说明 |
|---|---|
| `name` | 插槽名（`'settings.general.item'`） |
| `id` | 本注册项在该插槽内的唯一 id |
| `order` | 排序（数字小的在前；此处 10、11） |
| `store` | 绑给组件的响应式 store（`useStore` 消费） |
| `locale` | 文案命名空间 |
| `inject` | 给组件注入"业务动作"的回调工厂 |

### 6.4 组件写法（`src/client/AppearanceRow.tsx` 摘录）

```tsx
import type { PropsLocale, PropsRuntime, PropsStore } from '@deepseek-ai/dsh-client-ui-slots'
import type { createAppearanceRowStore } from './settings-store.ts'
import css from './AppearanceRow.module.css'

/** Full component props: runtime share + store share + locale seat + injected face. */
export type AppearanceRowComponentProps =
  PropsRuntime<'settings.general.item'> & PropsStore<ReturnType<typeof createAppearanceRowStore>>
  & PropsLocale<'settings.theme'> & AppearanceRowInjected

export function AppearanceRow({ t, setTheme, useStore }: AppearanceRowComponentProps) {
  const preference = useStore(s => s.preference)
  return (
    <div className={css.group}>
      <div className={css.title}>{t('appearance.title')}</div>
      <div className={css.cubeRow}>
        {CUBES.map(({ id, labelKey, Icon }) => (
          <button
            key={id}
            type="button"
            className={clsx(css.themeCube, preference === id && css.selected)}
            aria-pressed={preference === id}
            onClick={() => { setTheme(id) }}
          >
            <Icon />
            {t(labelKey)}
          </button>
        ))}
      </div>
    </div>
  )
}
```

**四件套 props（插槽组件的标准契约）**：
- `PropsRuntime<'插槽名'>` —— 运行时共享
- `PropsStore<store 类型>` —— 提供 `useStore` 选择器
- `PropsLocale<'命名空间'>` —— 提供 `t()` 翻译函数
- 自己的 `Injected` 面 —— 业务动作（如 `setTheme`）

**样式方案**：**CSS Modules**（`import css from './X.module.css'`）+ 全局语义 token（`--dsw-alias-*`）。官方不要求 Tailwind。

### 6.5 官方主题 token（可以直接用的语义变量）

**来源**：`packages/client/ui-theme/src/client/index.ts`

| Token | 用途 |
|---|---|
| `--dsw-alias-bg-base` | 应用基础背景 |
| `--dsw-alias-bg-layer-1` / `-layer-2` | 一/二级浮起表面 |
| `--dsw-alias-bg-overlay` | 浮层/气泡背景 |
| `--dsw-alias-border-l1` / `-l2` | 一/二级边框 |
| `--dsw-alias-brand-primary` | 品牌主色 |
| `--dsw-alias-label-primary` / `-secondary` | 主/次文字 |
| `--dsw-alias-state-error-primary` | 错误态 |
| `--dsw-alias-state-success-primary` | 成功态 |
| `--dsw-alias-state-warn-primary` | 警告态 |
| `--dsw-specific-sidebar-fill` | 侧栏底色 |

> 🔥 每个 token **都要求 light/dark 两个值**（原文：`requiresLightAndDark: true`）。只给一个值在切换配色时会变瞎——官方为此专门写了一段会抛错的校验（见下）。

**官方为"只给一个值"写的教学式报错（逐字，极好的错误信息范本）**：

```ts
      throw new TypeError(
        `theme override "${name}" from "${source}" is a bare string — pass { light: ${JSON.stringify(value)}, dark: ${JSON.stringify(value)} } `
        + '(repeat the value when it is the same in both palettes); a single value goes illegible when the user switches color scheme',
      )
```

---

## 模板 7 · 生命周期与副作用回收（`ctx.effect`）

**来源**：`packages/client/ui-theme/src/client/index.ts`

```ts
    if (this.media !== undefined) {
      const media = this.media
      const onChange = (): void => {
        if (this.preference !== 'system') return
        this.publish()
      }
      ctx.effect(() => {
        media.addEventListener('change', onChange)
        return () => { media.removeEventListener('change', onChange) }
      }, 'ui-theme: prefers-color-scheme listener')
    }
    ctx.effect(() => host.subscribe(() => { this.adopt() }), 'ui-theme: settings scope adoption')
```

**`ctx.effect(setup, label)` 规则**：
- `setup` 是函数，**返回一个清理函数**（disposer）。
- 第二个参数是**人类可读的标签**（官方每次都写，如 `'ui-theme: prefers-color-scheme listener'`）。
- 插件卸载 / HMR 重载时，DSH 自动调用清理函数 → **监听器、订阅、定时器不会泄漏**。

> 🔥 **新手第一号事故源**：加了事件监听/订阅却忘了返回清理函数 → 热更新后监听器叠加、界面越改越慢、事件触发多次。**凡是在插件里注册了外部资源，一律包进 `ctx.effect`。**

**注册类 API 一般自带 disposer**，不必再包 `ctx.effect`：

```ts
  register(definition: ThemeDefinition): () => void {
    ...
    return () => {
      if (!this.themes.some(t => t.id === definition.id)) return
      this.themes = this.themes.filter(t => t.id !== definition.id)
      ...
    }
  }
```

**官方注释原文（讲清了"为什么"）**：
> Disposing the theme backing the active preference resets the preference to the default so the UI never keeps tokens of an unregistered theme.

---

## 附：官方服务名速查（从各插件 `inject` 实证）

| 服务名（`inject` 里的字符串） | 用途 | 来源 |
|---|---|---|
| `tools` | 工具注册表 | `tool-ask-user` |
| `commands` | 斜杠命令注册表 | `command-feedback` |
| `userQuestions` | 向用户提问的能力 | `tool-ask-user` |
| `agents` | agent 注册表 | `time-context` |
| `sessionProjections` | 会话投影 | `time-context` |
| `settings` | 用户设置存储 | `ui-theme`（宿主） |
| `sessions` | 会话存储 | `command-feedback` |
| `slots` | UI 插槽注册表 | `ui-brand-official`、`ui-theme` |
| `locale` | 文案 | `ui-theme` |
| `remote` | 宿主↔客户端转发 | `ui-theme` |
| `settingsScope` | 客户端设置订阅 | `ui-theme` |

**宿主事件名（`ctx.on` 实证）**：`webserver/index-inject`（注入页面 HTML）、`theme/change`（自定义事件示例）。

**插槽名（实证）**：`sidebar.brand.mark`、`sidebar.brand.name`、`settings.general.item`。

---

## 附：官方全部 UI 插槽名（40 个，实测提取）

> 取证：`grep -rhoE "slots\.(inject|register)\(\s*'[^']+'" packages/*/*/src`（官方全仓）。**这份清单官方文档里没有**，靠源码提取。
> 用法：`ctx.slots.inject('<插槽名>', () => ctx.slots.register({ name: '<插槽名>' }, 组件))`

### 会话 / 对话区（conversation.*）

| 插槽名 | 位置 |
|---|---|
| `conversation.view` | 对话主视图（**最常用的整块替换点**） |
| `conversation.chat.node` | 聊天消息节点 |
| `conversation.chat.assistant-actions` | 助手消息的操作按钮区 |
| `conversation.composer` | 输入框整体 |
| `conversation.composer.dock` | 输入框停靠区 |
| `conversation.input.dock` | 输入区停靠 |
| `conversation.input.overlay` | 输入区浮层 |
| `conversation.input.attachments` | 输入区附件 |
| `conversation.input.model` | 输入区模型选择 |
| `conversation.input.plan` | 输入区计划 |
| `conversation.hero.workspace` | 空态主视觉 / 工作区 |
| `conversation.hero.workspace.directoryFlow` | 空态目录选择流 |
| `conversation.message.images` | 消息里的图片 |
| `conversation.trajectory.images` | 轨迹里的图片 |
| `conversation.session.header.corner` | 会话头部角落 |
| `conversation.session.header.utilities` | 会话头部工具区 |
| `conversation.approval.detail` | 审批详情 |

### 侧栏（sidebar.*）

| 插槽名 | 位置 |
|---|---|
| `sidebar` | 侧栏整体 |
| `sidebar.brand.mark` | 品牌图标（官方 `ui-brand-official` 用它） |
| `sidebar.brand.name` | 品牌文字（同上） |
| `sidebar.settings` | 侧栏设置入口 |
| `sidebar.workspaces` | 侧栏工作区列表 |
| `sidebar.workspaces.directoryFlow` | 侧栏目录选择流 |
| `sidebar.footer.action` | 侧栏底部动作 |
| `sidebar.right.pane.tab` | 右侧面板标签页 |
| `sidebar.right.pane.tab.title` | 右侧面板标签页标题 |
| `sidebar.right.tab.document` | 右侧文档标签 |

### 设置页（settings.*）

| 插槽名 | 位置 |
|---|---|
| `settings.section` | **设置页整段**（社区插件加设置页常注册这里） |
| `settings.general.item` | **通用设置里的一行/一项**（官方 `ui-theme` 用它） |
| `settings.header` | 设置页头部 |
| `settings.action` | 设置页动作区 |
| `settings.close` | 设置页关闭按钮位 |
| `settings.trigger` | 设置页触发入口 |
| `settings.onboarding` | 首次引导 |
| `settings.plugins.tab` | 插件标签页 |
| `settings.plugin.item` | 单个插件条目（插件管理器用） |

### 其他

| 插槽名 | 位置 |
|---|---|
| `main` | 主区域 |
| `rightbar` | 右侧栏 |
| `tool.call.toolview` | **工具调用的自定义视图**（工具插件想画专属卡片就用它） |
| `tool.call.images` | 工具调用里的图片 |

> 💡 **对新手最重要的三个**：`settings.section`（加设置页）、`settings.general.item`（加设置项）、`conversation.view`（整块替换对话视图，最激进）。

---

## 附：UI 插件的三条硬约束（实测 + 官方文档）

1. **`dsh.client` 与 `exports["./client"]` 必须成对存在**。缺任一个，客户端半侧不会被组装（宿主报 `client package failed to compose`）。
2. **浏览器半侧里 `@deepseek-ai/*` 只能写 `import type`**。要用值只用平台种子表允许的四个：`react` / `cordis` / `ui-slots` / `ui-primitives`。越界会报：
   `client-modules: require("...") missed the module table — not a platform seed word, not a materialized module, and no registered package factory`
3. **跨插件协作走服务或插槽，不要 `import` 别人的实现**（客户端 bundle 纯度门）。

---

## 附：官方 `packages/AGENTS.md` 对写插件的硬约束（原文摘录）

**来源**：`deepseek-harness/packages/AGENTS.md`（26 行，官方对"包/插件"的强制约定）。

### 前 3 条是新手必读（逐字）

> - **Plugin exports:** service packages default-export their service class; function plugins named-export `name` / `inject` / `Config` / `apply` and have no default export. Mixing the forms makes the Loader discard the function plugin's namespace ([postmortem](../docs/postmortem/0001-acp-default-export-drops-inject.md)).

> - **Optional services use `ctx.get(name)`.** Reserve `ctx.<name>` for declared injections; the property proxy is topology-sensitive, while strict `ctx.get` reads the global service store ([postmortem](../docs/postmortem/0001-acp-default-export-drops-inject.md)).

> - **Product-visible plugins require a non-unit REAL-composition test.** Hand-built `ctx.plugin(...)` suites are insufficient. Boot test-only `cordis.yml` through the Loader and app/process; mock only external services or nondeterministic inputs and assert model-visible, durable, or user-visible output. Keep opt-ins out of shipped defaults. [Policy](../docs/testing.md).

**翻译成人话**：

| 规则 | 一句话 |
|---|---|
| R-1 导出形态不能混 | **函数式插件** = 具名导出 `name`/`inject`/`Config`/`apply`，**绝不能有 default export**；**服务式插件** = default export 服务类。混用 → Loader **静默丢弃**你的命名空间（插件看起来装上了但不工作）。 |
| R-2 可选服务用 `ctx.get('x')` | 只有**声明过的**依赖才能写 `ctx.x`；探测"有没有"一律用 `ctx.get('x')`。 |
| R-3 面向用户可见的插件必须有真组合测试 | 只手搓 `ctx.plugin()` 不算；要真跑一遍 Loader + 应用，断言"模型可见 / 持久化 / 用户可见"的输出。 |

### 其余规则（对插件作者有约束力的）

> - **Initiator-owned private chains derive, then capture.** ... Keep `Agent` and `Session` explicit at lifecycle, session-log, service, authority, worker/process, persistence, and wire interfaces ...
> - **Represent one asynchronous operation with one lifecycle controller or transaction.** ... otherwise fold it while preserving rollback, callback containment, and quiescence.
> - **Design Service Definitions for all current Consumers.** Keep tool-schema, Loader, UI, transport, and provider-specific behavior in the Consumer or provider; do not let one Consumer dictate the service contract. Inverse smell: a public service method with one internal caller — pass a private capability closure instead.
> - **Require a current owner and need.** Tie each abstraction, state machine, option, defensive copy, and compatibility path to a current contract or production consumer ...
> - **Require evidence for public choices.** Configurability does not justify an unsupported default, public operation set, format, or imported external concept ...
> - **Write model-facing contracts from the model's perspective.** Prompts, tool schemas, results, and diagnostics contain only task-relevant concepts, not UI, transport, or implementation vocabulary.
> - **Enforce a decision in the operation that makes it.** Schema omission, prompt filtering, facades, wrappers, and listener order are not enforcement when direct or alternate callers can bypass them; test denial through the executor.
> - **Publish state only at its commit point.** Emit each notification and update derived state only after the operation succeeds ...
> - **Apply bounds to the complete result.** Enforce byte, token, item, and time limits where the complete emitted or retained value, including wrappers and metadata, is known ...
> - **Registry contributions prove disposal** through the HMR-safety test required by testing policy: **dispose the fiber and observe removal.**
> - **Specs run concurrently** in forked workers beside other gate processes. Own each acquired port, path, and child process through teardown; **a spec that passes only when run alone is a defect in the spec**.

### 命名与目录约定（逐字）

> - **Package tsconfig:** extends `tsconfig.base.json` (Client: `tsconfig.base.client.json`), sets `rootDir: src` and `outDir: lib/types`, references workspace dependencies ...
> - `src/types.ts` contains only types — no runtime code.
> - Tests live at package level under `tests/`, not `src/__tests__/`.
> - Update package README and JSDoc contracts in the same commit as behavior ...

**目录约定速查（可以直接照抄的结构）**：

```
my-plugin/
├── package.json
├── tsconfig.json          # extends tsconfig.base.json（客户端插件用 tsconfig.base.client.json）
├── tsdown.config.ts       # 只有客户端插件需要
├── cordis.patch.yml       # 只有组合包需要
├── README.md / README.zh.md
├── src/
│   ├── index.ts           # 宿主半侧：apply()
│   ├── types.ts           # 只放类型，不放运行时代码
│   └── client/            # 客户端半侧（UI 插件才有）
│       ├── index.ts       # apply(ctx) + inject
│       ├── Xxx.tsx
│       └── Xxx.module.css
└── tests/                 # 测试放这里，不是 src/__tests__/
    └── my-plugin.spec.ts
```

> ⚠️ `README.zh.md` / `README.i18n.yaml`：官方每个包都有中英双份 README + 一份 i18n 索引。第三方插件不强制，但**若想被官方精选清单收录，README 是硬门槛**。

---

<!-- ↓ 源：H-community-bundle.md （全文） -->

# H. 社区零代码组合包范本 —— `dsh-ouroboros`（原始素材）

> 来源：`plugin-research/src/Q00_ouroboros/integrations/dsh-plugin/`（仓库 `Q00/ouroboros`，约 5,805★）。
> 官方精选清单里**唯一一个"纯配置、零代码"插件**。**整个插件只有 3 个文件，没有一行 TypeScript。**
> 全部内容逐字照抄。

## 0. 为什么它是"最有教学价值"的范本

| 事实 | 说明 |
|---|---|
| 文件数 | **3**（`README.md` + `cordis.patch.yml` + `package.json`） |
| 源码 | **0 行** |
| 作用 | 把 Ouroboros（一个 Python 的 spec-first 开发工作流引擎）作为 MCP 工具挂进 dsh，给模型新增 **35 个工具** |
| 安装 | `dsh plugin --profile web add dsh-ouroboros` |

> 💡 **它证明了一件事：插件 ≠ 必须写代码。** 很多时候你想要的"集成外部工具"，只需要一个正确的 `cordis.patch.yml`。

---

## 1. 完整目录树（逐字）

```
./README.md
./cordis.patch.yml
./package.json
```

---

## 2. `package.json`（全文逐字）

```json
{
  "name": "dsh-ouroboros",
  "version": "0.1.0",
  "description": "Mount Ouroboros (spec-first AI dev workflow engine) into DeepSeek Harness as native tools — type \"ooo interview\" or \"ooo auto\" in chat.",
  "type": "module",
  "license": "MIT",
  "repository": {
    "type": "git",
    "url": "git+https://github.com/Q00/ouroboros.git",
    "directory": "integrations/dsh-plugin"
  },
  "homepage": "https://github.com/Q00/ouroboros/tree/main/integrations/dsh-plugin",
  "keywords": [
    "dsh-plugin",
    "deepseek-harness",
    "ouroboros",
    "mcp"
  ],
  "files": [
    "cordis.patch.yml",
    "README.md"
  ],
  "dsh": {
    "bundle": {
      "patch": "./cordis.patch.yml"
    }
  }
}
```

**四个必抄点**：
1. `"type": "module"` —— 必须。
2. `files` **只列了 `cordis.patch.yml` 和 `README.md`** —— 零代码包就这么短。**关键：patch 文件必须在 `files` 里，否则发布后它不会进 npm 包**。
3. `dsh.bundle.patch` —— 少了它，`dsh plugin add` 会打那条 `declares no dsh.bundle` 警告，装完不生效。
4. **没有 `main` / `exports` / `dependencies`** —— 因为没有任何 JS 入口。这是零代码包和普通包在 `package.json` 上的显著差异。

---

## 3. `cordis.patch.yml`（全文逐字，**最重要的模板**）

```yaml
# dsh-ouroboros — mounts Ouroboros as native MCP tools inside DeepSeek Harness.
#
# Ouroboros (https://github.com/Q00/ouroboros) is a spec-first AI dev workflow
# engine: Socratic interview -> Seed spec -> execute -> evaluate -> evolve.
# This bundle inserts one @deepseek-ai/dsh-mcp-client row that spawns
# `ouroboros mcp serve` over stdio, so every dsh agent gets tools named
# mcp__ouroboros__ouroboros_interview, mcp__ouroboros__ouroboros_auto, and 33
# others. Typing "ooo interview <goal>" or "ooo auto <goal>" in chat is enough
# for the model to find and call the matching tool on its own — no extra
# prompting needed (each tool carries its own description).
#
# Requirements: Python >= 3.12 and `uv` (https://astral.sh/uv) on PATH. No
# separate `pip install` step — uvx fetches and runs Ouroboros in an isolated
# environment on first launch.
#
# Configuration (env vars, read by the spawned `ouroboros mcp serve` process):
#   OUROBOROS_LLM_BACKEND   — LLM backend for interview/seed/QA. Unset uses
#                             your existing `ouroboros setup` default. `dsh`
#                             routes those calls back through DeepSeek Harness,
#                             but it is NOT a one-variable switch: Ouroboros
#                             spawns its own `dsh-acp-demo` child and fails
#                             closed (`invalid_config`) unless
#                             OUROBOROS_DSH_CONFIG_PATH names an absolute
#                             trusted Cordis composition. See the bundle README.
#   OUROBOROS_AGENT_RUNTIME — agent runtime backend for ooo run/ooo auto's
#                             execution step. Defaults to `host`: dsh has no
#                             installable execution CLI of its own, so by
#                             default the dsh model itself does the work —
#                             `execute_task` publishes a dispatch and dsh
#                             spawns its own subagent to service it
#                             (orchestrator/host_dispatch.py). Set this to an
#                             executable runtime (claude-cli, codex,
#                             opencode, ...) to have that CLI do the work
#                             instead.
#   OUROBOROS_DSH_CONFIG_PATH / OUROBOROS_DSH_CLI_PATH
#                           — the two prerequisites of the `dsh` LLM backend
#                             above: the absolute composition file, and the
#                             `dsh-acp-demo` bin when it is not on PATH.
#
# Override any field from your own profile's cordis.patch.yml by id (see the
# "Package and install a plugin" tutorial) — e.g. to pin a specific Ouroboros
# version, add local MCP servers back, or tighten toolCallTimeoutMs.
- insert:
    - id: mcp-ouroboros
      name: '@deepseek-ai/dsh-mcp-client'
      config:
        serverName: ouroboros
        transport: stdio
        command: uvx
        args:
          - --from
          - 'ouroboros-ai[mcp]'
          - --with
          - 'mcp==2.0.0'
          - ouroboros
          - mcp
          - serve
        # The child does NOT inherit the harness environment wholesale:
        # @deepseek-ai/dsh-subprocess hands mcp-client a scrubbed parent env
        # with every credential-shaped name (/KEY|PASSWORD|SECRET|TOKEN/i) and
        # every DSH_* name removed, precisely so harness credentials never leak
        # into a spawned process implicitly. This explicit layer merges *after*
        # that scrub, so any credential Ouroboros genuinely needs has to be
        # named here. It is deliberately a short allowlist covering the two
        # documented backends — not a wildcard passthrough. To forward another
        # (OPENAI_API_KEY, OPENROUTER_API_KEY, GOOGLE_API_KEY, ...), override
        # this row in your own profile's cordis.patch.yml with that one extra
        # name — restating the whole `config`, since a later layer replaces a
        # row's config rather than deep-merging it. Non-credential names
        # (PATH, HOME, the OUROBOROS_* selectors) survive the scrub on their
        # own; the OUROBOROS_* rows below are here to keep the contract
        # visible in one place.
        #
        # `?? ''` keeps every value a string (the row's schema is a string
        # dict). Ouroboros treats a blank credential as unset, so an unset host
        # variable stays effectively unset in the child. OUROBOROS_AGENT_RUNTIME
        # is the one exception: it falls back to the literal `'host'` rather
        # than `''`, because dsh has no installable execution CLI to fall back
        # to on its own — see the comment above.
        env:
          OUROBOROS_LLM_BACKEND: !!js process.env.OUROBOROS_LLM_BACKEND ?? ''
          OUROBOROS_AGENT_RUNTIME: !!js process.env.OUROBOROS_AGENT_RUNTIME || 'host'
          OUROBOROS_DSH_CONFIG_PATH: !!js process.env.OUROBOROS_DSH_CONFIG_PATH ?? ''
          OUROBOROS_DSH_CLI_PATH: !!js process.env.OUROBOROS_DSH_CLI_PATH ?? ''
          ANTHROPIC_API_KEY: !!js process.env.ANTHROPIC_API_KEY ?? ''
          DEEPSEEK_API_KEY: !!js process.env.DEEPSEEK_API_KEY ?? ''
        # ouroboros_auto runs a full interview -> Seed -> execute -> grade
        # pipeline synchronously when called without polling; give it real
        # headroom instead of dsh's 60s mcp-client default.
        toolCallTimeoutMs: 1800000
        # Soft-fail: a machine without `uv`/Ouroboros configured yet should
        # still boot dsh with every other plugin working, not crash outright.
        # Recovery is not guaranteed to be automatic — whether mcp-client
        # retries at all depends on the dsh build (the published rc has no
        # reconnect loop), and where it exists the attempt budget is bounded.
        # After fixing the cause, reload the plugin or restart dsh.
        failOnStartupError: false
```

---

## 4. 从这个文件里能学到的 8 条硬知识（逐条对应原文）

| # | 知识 | 原文依据 |
|---|---|---|
| 1 | 补丁文件**只写注释 + 一个 `- insert:` 列表**，注释可以写得很长（它就是这个插件的"文档"） | 整个文件 |
| 2 | 插一行就能给模型加 35 个工具（靠 `@deepseek-ai/dsh-mcp-client`） | 文件头注释：`so every dsh agent gets tools named mcp__ouroboros__ouroboros_interview, mcp__ouroboros__ouroboros_auto, and 33 others` |
| 3 | **`!!js` 可以写在 `config:` 内部**（`env:` 里就用了），与官方复盘 0002 一致 | `env:` 段落 |
| 4 | 🔥 **子进程环境会被"清洗"**：`@deepseek-ai/dsh-subprocess` 会把**凭据形状的名字**（正则 `/KEY\|PASSWORD\|SECRET\|TOKEN/i`）**和所有 `DSH_*`** 从父环境里删掉。**你要传的凭据必须显式列在 `env:` 里** | 注释原文：`hands mcp-client a scrubbed parent env with every credential-shaped name (/KEY|PASSWORD|SECRET|TOKEN/i) and every DSH_* name removed` |
| 5 | 🔥 **后面的层"替换"整段 `config`，不做深合并** —— 所以覆盖时必须**把整个 config 重述一遍** | 注释原文：`restating the whole config, since a later layer replaces a row's config rather than deep-merging it` |
| 6 | 用 `?? ''` 保持"值的类型是字符串"（该行的 schema 是 string dict），用 `\|\|` 提供真值回退 | 注释原文：`` `?? ''` keeps every value a string (the row's schema is a string dict) `` |
| 7 | 长任务要**显式加大超时**（默认 mcp-client 60s → 这里 1800000ms = 30 分钟） | 注释原文：`give it real headroom instead of dsh's 60s mcp-client default` |
| 8 | **加 `failOnStartupError: false` 实现"软失败"** —— 没装 uv 的机器也能正常启动 dsh，其它插件照常工作 | 注释原文：`a machine without uv/Ouroboros configured yet should still boot dsh with every other plugin working, not crash outright` |

> ⚠️ 第 8 条后半句也很重要：**软失败不是自动恢复**。原文：`Recovery is not guaranteed to be automatic — whether mcp-client retries at all depends on the dsh build (the published rc has no reconnect loop)`。

---

## 5. 可直接套用的最小零代码插件模板

```json
// package.json
{
  "name": "dsh-<你的插件名>",
  "version": "0.1.0",
  "description": "<一句话说明它给 dsh 加了什么>",
  "type": "module",
  "license": "MIT",
  "keywords": ["dsh-plugin", "deepseek-harness"],
  "files": ["cordis.patch.yml", "README.md"],
  "dsh": { "bundle": { "patch": "./cordis.patch.yml" } }
}
```

```yaml
# cordis.patch.yml
# <这里写清楚：这个插件做了什么、有什么前置要求、怎么配置>
- insert:
    - id: <行 id，全局唯一>
      name: '<要挂载的包名>'
      config:
        <该包要求的配置>
```

**装法**：
```bash
dsh plugin --profile web add ./你的插件目录     # 本地目录
dsh plugin --profile web add dsh-<你的插件名>   # 已发布到 npm
```

---

## 6. 这个范本的边界（诚实标注）

- 它**不能**给你加"自定义工具"（要写 `defineTool`），只能**挂载已存在的插件能力**（如 MCP 客户端）。想把外部能力变成 dsh 工具，有两条路：
  - **零代码**：对方已经有 MCP server → 用 `@deepseek-ai/dsh-mcp-client` 挂（本范本的路子）。
  - **写代码**：自己写 `defineTool`（见官方 `tool-ask-user` 模板）。
- 它的 `env` 里只放**名字**，不放**值** —— 值是运行时从宿主环境读的。**别把密钥硬编码进 `cordis.patch.yml`**（补丁文件会进 npm 包）。

---


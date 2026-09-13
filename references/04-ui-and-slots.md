> **文件来源**：本文件由 DSH 插件开发手册套件整合生成。直接编辑会在下次整合时被覆盖，因此维护性改动记录在工作区源文档中。

> **本文件用途**：UI 插件与设置卡片的完整实现：两个半侧结构、三个登记点、slot 插槽机制、React/TSX 技术栈约束、样式打包、开发期调试、三层配置解析模型。
> **合成来源**：DSH插件开发指导手册.md（第 9/10 章）
> **快照警告**：本文件是 DSH 插件知识的**冻结快照**（基线 `v0.1.5-rc.2` / commit `c291e7961a`，2026-09-10），其中的**接口名级事实可能已过时**。
> **写代码前先核验**：`bash scripts/dsh-api-probe.sh <DSH 仓库路径>`（退出码 1 = 有 STALE，**不要直接照抄**）。
> **分级与核验规则**：`references/00-version-gate.md`、逐条登记 `references/api-claims.md`。
> **素材名约定**：正文里出现的 `Xxx-yyy.md`（如 `E-official-templates.md`、`B-tools-external.md`）是**生成时的源调研笔记名**，其内容在生成时已合并进本文件——**不是 skill 内的文件**，不必去别处找。

---

<!-- ↓ 源：DSH插件开发指导手册.md 区间 1654-2138 -->

# 第 9 章 第七课｜UI 插件：在网页界面里长出你的东西

> **本课目标**：写一个在 DSH 网页界面里显示东西的插件。
> **难度**：这是全书最复杂的一章。核心难点是理解「一个包有两个半侧」。

## 9.1 核心概念：一个插件 = 两个半侧

官方原文（`docs/cookbook/adding-a-settings-card.zh.md:5-7`，逐字）：

> 两个半侧住在同一个包里——Host 半侧在 `src/`，浏览器半侧在 `src/client/`，以 `./client` 导出并用 `dsh.client` 声明。

```
你的插件包/
├── package.json          ← 声明 dsh.client + exports["./client"]
├── tsconfig.json         ← extends tsconfig.base.client.json
├── tsdown.config.ts      ← 用共享 preset
└── src/
    ├── index.ts          ← 【Host 半侧】运行在 Node 里（常常是空的）
    └── client/
        └── index.ts      ← 【浏览器半侧】真正跑在网页里的代码
        └── Something.tsx ← 你的 React 组件
```

**为什么要两个半侧？** 因为 DSH 是「后端 host + 前端 web」的架构。你的插件既要在 Node 里被加载（哪怕是空壳），又要在浏览器里运行 UI。

⚠️ **Host 半侧不能省**。官方（`packages/client/AGENTS.md:138,142`）：缺 node half 会让 Loader 无法 import 你的包。

**最小的 Host 半侧可以就这么点**（`packages/client/ui-brand-official/src/index.ts` 全文，逐字）：

```ts
/**
 * Official browser-brand plugin, node half. The empty apply gives Loader a
 * host-side row while the browser half ships through `exports["./client"]`.
 */

/** Host plugin body — this package contributes browser presentation only. */
export function apply(): void {}
```

💡 注意 `apply()` **连 ctx 参数都没有**。这是完全合法的——它只负责"占个位"，让 Loader 认为这个包被加载了。

## 9.2 `package.json` 模板（可直接抄）

来源：`packages/client/ui-brand-official/package.json`（逐字关键字段）

```json
{
  "name": "@deepseek-ai/dsh-client-ui-brand-official",
  "type": "module",
  "main": "lib/index.js",
  "types": "lib/types/index.d.ts",
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
  "files": [
    "lib/index.js",
    "lib/client.js",
    "lib/types/**/*.d.ts"
  ]
}
```

**三个必知字段**：

| 字段 | 含义 |
|---|---|
| `exports["./client"]` | 浏览器半侧的入口。**声明了 `dsh.client` 就必须有这个导出**（没有会抛错） |
| `dsh.client.platform` | **总是必填**，值为 `"web"` |
| `dsh.client.inject` | **信息性**的包名依赖边——**只用于 preflight 显示与 HMR diff，不决定激活顺序**。激活顺序由 Cordis fiber 等**服务**决定 |

来源：`packages/client/AGENTS.md:140`

`tsdown.config.ts`（`ui-brand-official/tsdown.config.ts`，逐字）：

```ts
import { clientBundle } from '../tsdown.client.ts'

export default clientBundle('@deepseek-ai/dsh-client-ui-brand-official', ['lib/types/index.js'])
```

> ⚠️ **这只在 DSH 仓库内可用**——`clientBundle()` 未对外发布。仓库外的第三方插件要自己复刻产物格式，见 §9.6 的校正块与 `14-inbound-http-and-timers.md` §17.3。

`tsconfig.json`（逐字）：

```json
{
  "extends": "../../../tsconfig.base.client.json",
  "compilerOptions": { "rootDir": "src", "outDir": "lib/types" },
  "include": ["src"],
  "references": [
    { "path": "../../../vendor/cordis" },
    { "path": "../ui-renderer" },
    { "path": "../ui-primitives" },
    { "path": "../ui-sidebar" },
    { "path": "../ui-slots" }
  ]
}
```

## 9.3 ⚠️ 再加 3 个登记点（漏一个就失败）

官方（`packages/client/AGENTS.md:139`）：客户端插件除了正常的包登记，还**必须**：

1. 在 `tsconfig.client.json` 的 `references` 里加你的包
2. 在 `packages/bundle/web-app/cordis.patch.yml` 里加一行
3. 在 `packages/bundle/web-app/package.json` 的依赖里加你的包

官方原文警告：

> 缺任一会在不同的更晚点失败。

**给新手的强烈建议**：直接让你的 Agent 抄一个现成的 client 包（如 `ui-brand-official`，src 总共 49 行），然后**逐项对照检查这 3 个登记点**。这是最容易漏、又最难排查的地方。

## 9.4 slots（插槽）：DSH 的 UI 扩展机制

### 9.4.1 设计原则

官方（`docs/subsystems/slots.zh.md:5`）：

> 功能插件**只**通过 `ctx.slots.register()` 贡献 UI，**绝不导入其他功能插件的组件**。

**唯一的注册 API**（`packages/client/AGENTS.md:11`）：

```ts
ctx.slots.register({ name, id?, key?, order?, children?, store?, inject? }, Component)
```

⚠️ 没有别的花哨接口：没有单独的 slot 定义调用、没有白名单对象、没有 helper。

### 9.4.2 两个正交维度：基数与作用域

来源：`docs/subsystems/slots.zh.md:46-58`（逐字表格）

| 维度 | 值 | 含义 |
|---|---|---|
| 基数 | `single` | 单个 cell，渲染当前 priority 胜者 |
| 基数 | `list` | cell 由必填 `id` 定址，先按 `order`、再按注册顺序排列 |
| 基数 | `keyed` | owner 传入 `entryKey`；匹配 cell 以该 key 对应的 props 渲染 |
| 基数 | `chain` | 每个 entry 提供纯 `select(owner)` 函数；按 priority 顺序第一个非 null 结果获选 |
| 作用域 | `root` | 一个 root 作用域组件和 store 实例 |
| 作用域 | `session-maybe` | 跟随当前选择，但没有 Session 时仍可渲染 |
| 作用域 | `session` | 要求可解析的 Session binding |

### 9.4.3 可用的插槽树（节选）

完整树见 `docs/subsystems/slots.zh.md:111-172`。以下是**最常用的部分**：

```text
root
├─ sidebar
│  ├─ sidebar.brand.mark
│  ├─ sidebar.brand.name
│  ├─ sidebar.panellist
│  ├─ sidebar.footer.action
│  └─ sidebar.settings
│     ├─ settings.section
│     │  ├─ settings.general.item
│     │  ├─ settings.models.provider-card
│     │  └─ settings.plugins.tab
│     │     └─ settings.plugin.item        ← 设置卡片（第 10 章）
├─ main
│  └─ main.conversation
│     ├─ conversation.session
│     │  └─ conversation.view
│     │     └─ conversation.chat.node
│     │        └─ tool.call.toolview       ← 工具卡片（第 8 章提到）
│     ├─ conversation.session.header.actions   ← 标题栏按钮（示例用这个）
│     └─ conversation.composer.bar
│        ├─ conversation.input.attachments
│        ├─ conversation.input.plan
│        └─ conversation.input.model
├─ rightbar
│  └─ rightbar.session
│     └─ sidebar.right.pane.tab
└─ shell.overlay
```

💡 运行中的 DSH 可以用 `cordis_inspect what:"client"` 查询**实时**的插槽树（`slots.zh.md:174`）。

### 9.4.4 最小可用示例：往标题栏加一个按钮

来源：`docs/subsystems/slots.zh.md:19-42`（逐字，原文标注 `tsx ignore-check`）

```tsx ignore-check
import type { Context } from '@deepseek-ai/cordis'
import type {} from '@deepseek-ai/dsh-client-ui-conversation/client'
import type {} from '@deepseek-ai/dsh-client-ui-session/client'
import type { PropsRuntime } from '@deepseek-ai/dsh-client-ui-slots'

type HeaderActionProps = PropsRuntime<'conversation.session.header.actions'>

function HeaderAction({ useSession }: HeaderActionProps) {
  const running = useSession(snapshot => snapshot.running)
  return <button disabled={running}>Review</button>
}

export const inject = ['slots']

export function apply(ctx: Context): void {
  ctx.slots.inject('conversation.session.header.actions', () =>
    ctx.slots.register({
      name: 'conversation.session.header.actions',
      id: 'review',
      order: 100,
    }, HeaderAction))
}
```

**逐点解释**：

| 代码 | 含义 |
|---|---|
| `import type {} from '...'` | 只引入**类型声明**（让插槽名和 props 有类型），**不引入运行时值** |
| `ctx.slots.inject(key, cb)` | 「等这个插槽被声明出来，再执行 cb」。owner 折叠时移除，重新声明后再跑，随你的 fiber 离开 |
| `ctx.slots.register({name, id, order}, Component)` | `id` 用于 `list` 基数；`order` 决定排序 |
| 组件签名 `{ useSession }` | 组件**不收到 `ctx`**！只收到框架给的几组 props |

⚠️ **注册进未声明的 slot 会在激活时报错**（`slots.zh.md:13-17`）。所以务必用 `ctx.slots.inject` 包一层，或者确认目标插槽一定存在。

### 9.4.5 组件能拿到什么（四个 share）

来源：`docs/subsystems/slots.zh.md:60-75`

| props 组 | 内容 |
|---|---|
| `PropsRuntime<K>` | owner 值与标准 scope 值 |
| `PropsRenderSlots<S>` | 获授权的子 slot 渲染器 |
| `PropsStore<H>` | 共享视图状态的 selector hook 与 mutation callback |
| `InjectFace<I>` | 私有数据、callback 与 observable hook |
| `PropsLocale<N>` | 国际化文案 |

**框架提供的 hook**：`useSessions`、`useSession`、`useProjection`、`useConversation`、`useInput`、`inputActions`、`useChat`、`useTrajectory`、`useWorkspaces`、`usePanelInfo`，以及按声明 store 生成的 `useStore` 和按 locale namespace 生成的 `t`。

⚠️ **硬规则**（`slots.zh.md:75`）：**组件绝不会收到 `ctx`**。这是刻意的设计——UI 组件不该直接摸服务，必须走声明的 props。

## 9.5 前端技术栈约束（写错会被门禁拦）

| 事实 | 来源 |
|---|---|
| **React 18**（`react: ^18.2.0`、`react-dom: ^18.2.0`） | `packages/client/ui-theme/package.json`、`apps/web/package.json` |
| **样式：CSS Modules + `clsx`**，用语义 token `--dsw-*` | `docs/web-styling.zh.md:16` |
| ⚠️ **不得添加组件库或 Tailwind** | `packages/client/AGENTS.md:111` |
| 不得写颜色字面量，要用 `--dsw-alias-*` 语义别名 | `docs/web-styling.zh.md:9,17` |
| 业务组件**不得**含订阅机制（无 `useSyncExternalStore`、无手写 subscribe） | `packages/client/AGENTS.md:24` |
| ⚠️ **跨插件的运行时值导入被门禁拒绝**，只能 `import type` | `packages/client/AGENTS.md:36` |

**最后一条最容易踩**：你想用别的插件的组件？**不行。** 只能通过 slots 组合，或者通过注入的 Cordis 服务协作。

## 9.6 样式与资源怎么打包

来源：`packages/client/tsdown.client.ts:1-8`

| 写法 | 打包行为 |
|---|---|
| `x.module.css` | 编译成**哈希类名** + 工厂执行时注入 `<style>` |
| `x.css?inline` | 编译后**文本**作为默认导出，供插件自己的生命周期 effect 使用 |
| `x.css` | 全局内联注入 |
| `?raw` 资源 | 内联成字符串（真实范例：`ui-sidebar-documentpreview` 内联 pdf.js worker） |

**结论**：**CSS 会被编进 `lib/client.js`**，不需要单独发布静态资源文件。`files` 里通常只列 `lib/index.js`、`lib/client.js`、`lib/types/**/*.d.ts`。

⚠️ **反直觉的事实（源码实证）**：动态 plugin bundle 是 **lazy-CJS factory**（`window.__ModuleLoader__.load({id, factory})`），**不是 ESM**。

> 🔧 **校正（2026-09-11）**：本节原先说「这是构建产物格式，你写代码时不用管」——**对仓库内开发成立，对仓库外开发不成立**。
> `clientBundle()` 这个共享 preset **没有对外发布**，官方原文（`adding-a-settings-card.zh.md:102`）写明「本仓库之外的包**得自行复刻同样的输出格式**」。
> 所以第三方 UI 插件作者**必须自己产出**这个格式：esbuild/rolldown 的 `format: 'cjs'` + `platform: 'browser'`，并自己拼那三行 banner/intro/footer。完整契约（含逐字三行与平台种子表 9 项）见 `14-inbound-http-and-timers.md` §17.3。

## 9.7 开发期调试 UI 插件

1. **客户端 HMR 需要单独跑 watcher**：源码实证 `apps/cli/reference/README.zh.md:81` —— 接收器始终挂载，但要单独运行 `pnpm run dev:web` 重建客户端 bundle 才会生效。
2. **不需要重新构建整个 Web 应用**：`adding-a-settings-card.zh.md:82` 原文——「只要 `cordis.yml` 挂载了插件，它就会出现在页面上——无需重新构建 Web 应用」。
3. 用 `cordis_inspect what:"client"` 看实时插槽树。

## 9.8 🤖 让 AI Agent 帮你做这一课

UI 插件最容易出错，**强烈建议先让 Agent 做一次"抄范本 + 登记"的热身**：

> 我要写一个 DSH 客户端（UI）插件，作用是**（描述，例如"在侧边栏底部加一个显示当前时间的按钮"）**。
> 请**分三步**做，每步做完等我确认：
>
> **第 1 步（选型）**：读 `docs/subsystems/slots.zh.md`，从插槽树里选一个合适的插槽，告诉我它的名称、基数（single/list/keyed）、scope，以及为什么选它。
>
> **第 2 步（抄范本）**：以 `packages/client/ui-brand-official/` 为范本，列出我需要的**全部文件清单**，以及**三个登记点**（`tsconfig.client.json` / `packages/bundle/web-app/cordis.patch.yml` / `packages/bundle/web-app/package.json`）分别要改什么。
>
> **第 3 步（写代码）**：写 Host 半侧（可以是空 `apply`）和浏览器半侧，组件用 React 18 + CSS Modules + `--dsw-*` token。
>
> 约束：**不允许**跨插件导入运行时值（只能 `import type`）；**不允许**引入组件库或 Tailwind；每个 API 标注仓库出处。

## 9.9 ✅ 第 9 章验收清单

- [ ] 我知道客户端插件必须有 Host 半侧 + 浏览器半侧
- [ ] `package.json` 里有 `exports["./client"]` 和 `dsh.client.platform = "web"`
- [ ] 三个登记点全部到位（用清单逐项勾）
- [ ] 我用的插槽名在 `slots.zh.md` 的插槽树里能找到
- [ ] 组件里**没有**用 `ctx`
- [ ] 没有跨插件导入运行时值、没有引入第三方 UI 库
- [ ] 在浏览器里真的看到了我的东西

---

# 第 10 章 第八课｜设置卡片：让用户在界面里配置你的插件

> **本课目标**：在 DSH 的「插件配置」页面里，给你的插件显示一张卡片，用户点点鼠标就能改配置。
> **前置**：需要先完成第 5 章（Config）和第 9 章（UI 插件）。

## 10.1 三层配置解析模型（必须先理解）

这是整个设置机制的地基。来源：`docs/subsystems/settings.zh.md:5`

```
① schema 默认值        ← 你在 Config 里写的 .default(...)
        ↓ 被覆盖
② 注册方 base          ← cordis.yml 里那一行的 config（第 5 章）
        ↓ 被覆盖
③ 用户在界面里改的部分  ← 用户在设置卡片里改的值，只写这一层
```

**核心机制**：`SettingsScope.update(patch)` 把稀疏 patch **只合并进"用户层"，绝不进 base 层**。

来源：`docs/subsystems/settings.zh.md:66-93`

## 10.2 Host 半侧：注册一个设置命名空间

来源：`docs/cookbook/adding-a-settings-card.zh.md:13-44`（逐字）

```ts
import type { Context } from '@deepseek-ai/cordis'
import type {} from '@deepseek-ai/dsh-settings'
import z from '@deepseek-ai/schemastery'

declare function assertReachable(endpoint: string | undefined): void
declare function rebuildFromSettings(config: Config): void

export const MY_PLUGIN_NS = 'my-plugin'

export interface Config {
  endpoint?: string
  retries?: number
}

export const Config: z<Config> = z.object({
  endpoint: z.string(),
  retries: z.number().step(1).min(0).default(3),
})

export function apply(ctx: Context, config: Config) {
  let source = () => config
  ctx.inject(['settings'], (settingsCtx) => {
    settingsCtx.settings.installSection(ctx, MY_PLUGIN_NS, Config, config, {
      // Constraints the schema cannot express refuse the write, not the next use.
      validate: value => void assertReachable(value.endpoint),
      setSource: (current) => { source = current },
      onChange: () => { rebuildFromSettings(source()) },
    })
  })
}
```

⚠️ 注意：这个片段里 `assertReachable` 和 `rebuildFromSettings` 是 `declare function`（**只有类型声明，没有实现**）——说明**这段代码不能直接复制运行**，你需要自己实现这两个函数。这是官方文档的省略，本手册如实指出。

**`installSection` 的精确签名**（`docs/subsystems/settings.zh.md:215`）：

```ts
installSection<
  const Namespace extends string,
  T,
>(
  owner: Context,
  ns: Namespace & SettingsNamespaceInput<Namespace>,
  schema: z<T>,
  entry: T,
  hooks: SettingsSectionHooks<T>,
): void
```

**两个 API 的选择**（关键区分）：

| API | 何时用 | 真实范例 |
|---|---|---|
| `installSection(owner, ns, schema, entry, hooks)` | 你有 `cordis.yml` 条目，要把 entry 当作 **base 层** | `packages/web/web-search-deepseek/src/index.ts:127-140` |
| `settings.register(ns, schema, options?)` | 纯卡片、自带命名空间，不需要 base 层 | `packages/client/ui-theme/src/index.ts:37-39` |

## 10.3 浏览器半侧：注册卡片

来源：`docs/cookbook/adding-a-settings-card.zh.md:52-70`（逐字，原文标注 `ts ignore-check`）

```ts ignore-check
import type { Context as ClientContext } from '@deepseek-ai/cordis'
// Type-only: the keyed slot's declaration. Cross-plugin collaboration goes
// through cordis services; a value import fails the client bundle-purity gate.
import type {} from '@deepseek-ai/dsh-client-ui-settings-plugins/client'

export const inject = ['slots', 'locale', 'connection', 'remote', 'settingsScope']

export function apply(ctx: ClientContext): void {
  const card = new MyPluginCardController(ctx.settingsScope.bind({ namespace: 'my-plugin' }))
  ctx.slots.inject('settings.plugin.item', () => ctx.slots.register({
    name: 'settings.plugin.item',
    key: 'my-plugin',
    locale: 'settings.myPlugin',
    inject: () => card.inject(),
  }, MyPluginCard),
  )
}
```

**`settings.plugin.item` 的声明**（源码 `packages/client/ui-settings-plugins/src/client/slot-contract.ts`，逐字）：

```ts
declare module '@deepseek-ai/dsh-client-ui-slots' {
  interface SlotMap {
    /** One plugin's card inside the plugin configuration section (see module JSDoc). */
    'settings.plugin.item': { kind: 'keyed'; scope: 'root'; owner: SettingsPluginItemOwnerProps }
  }
}
```

## 10.4 浏览器侧读写配置的 API

来源：`packages/client/ui-settings/src/client/settings-contract.ts:54-101`（逐字）

```ts
export interface SettingsScope<T> {
  getSnapshot(): SettingsScopeSnapshot<T>
  subscribe(listener: () => void): () => void
  mutate(ops: readonly SettingsPathOpView[], expectedRevision?: number): Promise<void>
  set(field: string, value: unknown): Promise<void>
  unset(field: string): Promise<void>
}
```

**三条必须知道的规则**：

1. **"字段是否被覆盖"看的是它有没有出现在 `user` 层，而不是它的值**（`adding-a-settings-card.zh.md:72`）。
2. **`set(field, value)` 存一个字段；`unset(field)` 把它清回组装层**（恢复默认）。
3. **⚠️ 每次写入都要带 `expectedRevision` 作栅栏**：不匹配的写入会被**拒绝**，从而不覆盖并发变更。官方原文（`adding-a-settings-card.zh.md:50`）：

> 每次写入都以读取时的 `revision` 作 `expectedRevision`，不匹配的写入被拒绝，不覆盖并发变更。

**对新手的意思**：不要把设置卡片做成"输入框一变就写"。要**读 → 改 → 带 revision 写**，失败就重新读一遍。

## 10.5 卡片什么时候才会显示

来源：`docs/cookbook/adding-a-settings-card.zh.md:74-78`

> **插件配置**标签页读 Host 服务了哪些命名空间并为每个派发一个 slot 键；Host 服务了某卡片的键才渲染，从未组装 Host 半侧的部署不会留下痕迹；卡片按注册顺序出现，keyed entry 不声明 `order`。

**翻译**：卡片显示的前提是 **Host 半侧真的注册了那个命名空间**。你只写浏览器半侧是没用的。

## 10.6 真实范本

| 范本 | 路径 | 教什么 |
|---|---|---|
| 插件配置卡片全套 | `packages/client/ui-settings-plugins/`（2208 行） | `settings.plugin.item` 卡片宿主 + 4 张真实卡片 |
| 设置行 + 主题服务 | `packages/client/ui-theme/`（890 行） | `settings.general.item` + locale + store + CSS 全套 |
| 卡片控制器写法 | `packages/client/ui-settings-plugins/src/client/bash-card-controller.ts:41-71` | 如何把 `SettingsScope` 包成表单 |
| Host 侧 schema | `packages/client/ui-theme/src/theme-settings.ts` | "配置项 = Cordis Config = schemastery schema" 同一份声明 |

## 10.7 🤖 让 AI Agent 帮你做这一课

> 我要给「（插件名）」加一张设置卡片，让用户能在界面里改 **（字段列表）**。
> 请：
> 1. 先讲清楚三层解析模型（schema 默认 / base / 用户层），并说明我的每个字段分别落在哪一层；
> 2. 写 Host 半侧：用 `installSection`（把我的 `cordis.yml` entry 作为 base 层）；
> 3. 写浏览器半侧：注册 `settings.plugin.item` 卡片；
> 4. 写卡片的读写逻辑：**必须**带 `expectedRevision` 做栅栏，并处理失败重读；
> 5. 告诉我怎么验证「用户改动真的落到了用户层」。
> 约束：不跨插件导入运行时值；字段"是否被覆盖"按是否出现在 user 层判断，不要用值比较。

## 10.8 ✅ 第 10 章验收清单

- [ ] 我能说清三层解析模型
- [ ] Host 半侧注册了命名空间，浏览器半侧注册了卡片
- [ ] 写设置时带了 `expectedRevision`
- [ ] 我知道卡片显示的前提是 Host 半侧注册了命名空间
- [ ] 我能在界面里改配置，并确认它生效了

---


---


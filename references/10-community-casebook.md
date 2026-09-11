<!-- 本文件由 DSH 插件开发手册套件整合生成，请勿手工编辑；改动请回到工作区源文档。 -->

> **本文件用途**：社区真实仓库的原始调研素材，按方向归档（UI / 工具与外部调用 / 服务与状态 / 宿主与组合包）。每条坑点与模板都标注了出处文件与行号。这是生成本手册的一手材料，比 05-pitfalls 更细但更粗糙——先读 05，需要追根究底时再查这里。体量大，不要通读，用 grep 按关键词检索。
> **合成来源**：A-ui-plugins.md + B-tools-external.md + C-services-state.md + D-host-bundle.md（原始调研笔记）
> **快照警告**：本文件是 DSH 插件知识的**冻结快照**（基线 `v0.1.5-rc.2` / commit `c291e7961a`，2026-09-10），其中的**接口名级事实可能已过时**。
> **写代码前先核验**：`bash scripts/dsh-api-probe.sh <DSH 仓库路径>`（退出码 1 = 有 STALE，**不要直接照抄**）。
> **分级与核验规则**：`references/00-version-gate.md`、逐条登记 `references/api-claims.md`。
> **素材名约定**：正文里出现的 `Xxx-yyy.md`（如 `E-official-templates.md`、`B-tools-external.md`）是**生成时的源调研笔记名**，其内容在生成时已合并进本文件——**不是 skill 内的文件**，不必去别处找。

---

<!-- ↓ 源：A-ui-plugins.md （全文） -->

﻿# A. DSH UI 插件方向 —— 真实踩坑记录 + 可复用骨架（原始素材）

> 面向《DSH 插件开发实战手册》。读者设定：**零软件工程经验的新手**。
> 每一条都标注来源：`仓库 + commit 短哈希 + 提交信息原文`，或 `仓库 + 文件路径`。
> 查不到的明确写 **「未找到」**，不编造。

---

## 0. 材料与方法（先读，决定你能从这个文件里信多少）

### 0.1 三个仓库的本地可用性（实测）

| 仓库 | commits | trees | **本地 blobs** |
|---|---|---|---|
| `zhu1090093659_dsh-web` | 2444 | 19098 | **365**（全部是 `.agents/notes/**` 笔记） |
| `omdsh-dev_DSH-better-sidebar` | 644 | 2044 | **0** |
| `dsh-market_dsh-market` | 491 | 1685 | **0** |

三仓均为 `--filter=blob:none --no-checkout` 部分克隆，工作区为空（`find . -type f -not -path './.git/*'` 返回 0）。
复现命令：

```bash
cd <repo>
git cat-file --batch-check --batch-all-objects | awk '$2=="blob"' | wc -l   # 本地 blob 数
git ls-tree -r HEAD                                                          # 全部路径+哈希（不需要 blob）
```

### 0.2 读文件内容的正确姿势

```bash
cd <repo>
GIT_NO_LAZY_FETCH=1 git show HEAD:<路径>
# 不加 GIT_NO_LAZY_FETCH=1 时会尝试联网 fetch，环境无网，报：
#   fatal: unable to access 'https://github.com/...': Could not connect to server
#   fatal: could not fetch <hash> from promisor remote
# 即使加了，blob 不在本地时仍报：fatal: bad object HEAD:<路径>
```

**结论（对写手册至关重要）：**

1. **本文件无法提供任何 `.ts` / `.tsx` / `package.json` / `cordis.patch.yml` 的源码逐字照抄** —— 这些 blob 不在本地，任务书里 `git show HEAD:<源码路径>` 会直接 `bad object`。凡涉及源码正文，本文件一律标注 **「未找到（blob 不可用）」**，只给出**路径与目录树**这两个确实可读到的事实。
2. 但 `dsh-web` 把 **245 篇 Agent Notes**（中文/英文成对）提交进了仓库，且这 365 个 blob 全部可用。这些 Notes 是**维护者自己写的 RFC/事故报告**，格式固定为 `## Problem` / `## Decision` / `## Alternatives considered` / `## Consequences` / `## Testing`，信息密度远高于源码注释，是本次最有价值的坑源。
3. `omdsh-dev_DSH-better-sidebar` 与 `dsh-market_dsh-market` 的提交信息**写得极长**（正文常含「诊断 / 根因 / 修复 / 测试」四段），弥补了 blob 缺失。
4. 三个仓库文件树完整，可读到：包边界、`exports` 相关文件是否存在、`src/{host,client,core}` 分层、`tests/` 命名等**结构性事实**。

### 0.3 本文件引用的 dsh-web 笔记

- Bug-fix 笔记：`.agents/notes/implemented/bug-fix/`（全仓 83 篇可读 / 该目录下 245 篇已实现笔记共存）
- Architecture 笔记：`.agents/notes/implemented/architecture/`（可读 18 篇）
- 权威规范：`packages/AGENTS.md`（**逐字可读**，见 §二 与 §三）
- 笔记写作规范：`.agents/notes/README.md`、`.agents/notes/AGENTS.md`

---

# 一、坑点清单：现象 → 根因 → 怎么修

> 记法：`[仓库] <commit 短哈希> <提交信息原文>`。
> 「提交信息原文」保留原始措辞（含中英混排、原文错别字）。

## 1.1 zhu1090093659_dsh-web（2444 commits，1032 次修复；坑矿最富）

### A 组：客户端半 / 宿主半通信与线协议

#### 坑 D1　客户端 bundle 硬 require `dsh-client-store`，宿主换 cohort 后整个家族客户端全不加载

- 来源：`dsh-web`　`.agents/notes/implemented/bug-fix/2026-08-28-client-store-dual-cohort-engine-shim.md`
  （笔记标题逐字：`Agent Note: dual-cohort client compatibility repair (store engine, injected faces)`）
- **现象**（笔记逐字）：
  ```
  failed to import loader entry 47c06ebb (@linxin666/dsh-client-ui-web-ui-settings):
  client-modules: require("@deepseek-ai/dsh-client-store") missed the module table —
  not a platform seed word, not a materialized module, and no registered package factory
  ```
  以及：task-board 条目永远停在 `pending (waiting for service: remote.agentPresets)`，启动审计报「一个条目未激活」。
- **根因**（笔记逐字）：
  1. 0.1.2-alpha.1 迁移把 `dsh-client-store` 变成「冻结平台模块」，共享客户端预设把它 external 化，于是每个重建的客户端 bundle 在求值期硬 require 它；但运行中的 0.1.1-rc.2 宿主没有这个包 —— `require` 落到模块表外。
  2. Typert-gateway 迁移把 `'remote.agentPresets'` 加进了客户端条目的**硬 inject 列表**；这个服务只在 0.1.2 宿主上注册，rc.2 宿主永远不满足 → 条目 pending。
- **修复**（笔记逐字要点）：
  - 不再 external `@deepseek-ai/dsh-client-store` 的 value import；预设把这类导入重定向到一个**生成 shim**，在 bundle 求值期通过 loader 注入的 `require` 解析引擎：**先试平台模块，再退到旧面 `@deepseek-ai/dsh-client-runtime/client`**。shim 的 specifier 用 `join('')` 拼，让静态解析器看不见，从而把 require 原样 emit 进 factory scope。
  - shim **只转发两个引擎共同的值面**：`notifySubscribers` 只在 cohort 包里存在，**绝不能再导出**——未来再 value import 它会以 missing-export 构建失败，而不是静默破坏 rc.2。
  - task-board 客户端：`remote.agentPresets` 从硬 inject 列表移除；改为**使用时探测**：注册了就用 `remote.agentPresets`，否则退到 `connection.api.agentPresets`（迁移前的 rc.2 面）。
  - 笔记明确否决「用 cordis 的软等待」：*"an inject wait either blocks activation (hard) or cannot express 'continue without it' (cordis inject has no optional flag here)"*。
- **给新手的教训**：宿主 SDK 大版本迁移时，**客户端 bundle 的 external/require 是最先炸的地方**；且 **inject 列表是硬门**，多写一个不存在的面（见市场坑 M1）或写少了都会挂。

#### 坑 D2　线协议参数形状与 descriptor 不一致，测试全绿但功能全死

- 来源：`dsh-web`　`.agents/notes/implemented/bug-fix/2026-08-28-descriptor-faithful-wire-contracts.md`
- **现象**（笔记逐字）：`session/list` 用 `{request}` 调用，但它的单参数在线上是 `_request`（task-board 结算循环死、手机会话列表死）；`directoryPicker/list` 发 `{request: body}`，但它声明的是一个扁平的可选 `path`（手机浏览死）；业务错误码从 `error.code` 读，但 `TypertRemoteFailure` 把它放在 `error.failure`（配对模型目录返回 502 而不是 409/422）；`CardForm.save()` 把「resolved 的 scope.mutate」当成成功，但 0.1.2 的 scope 在**拒绝后会先做一次恢复性 reload 再 resolve**（被拒绝的保存丢用户草稿）；git-graph 以为 `ISessions.create` 会导航，其实只有 `open()` 才选中（worktree 会话被隐形创建）；手机历史分页重复同一页，因为 `beforeSeq` 从不前进。
- **根因**：调用点把「自己以为的」线协议写进代码，**测试替身也带着同样的错误假设**，所以所有门禁全绿覆盖着静默损坏的路径。
- **修复**（笔记逐字要点）：新增 `invokeWireArgs()` helper 把 invoke 参数按 descriptor 的线布局键：`session/list -> { _request }`、`directoryPicker/list -> 扁平可选 path`、`agentPresets/list` 与 `session/modelCatalog -> {}`、**其余 -> `{ request }`**；测试 fake 也用同一套 descriptor 表，并像网关的 `assertExactArguments` 一样**拒绝多余/缺失的键**；BFF 从 `error.failure` 取业务失败，再退到 `error.code`，并把真实 wire code 映射（`settings-conflict -> 409`、`settings-rejected -> 422`）；`CardForm.save()` 保留单次原子 mutate，但**按「结算后的快照读回」判定**每次计划写入（set：用户层存有该值；unset：字段消失；一次 miss 即整批失败并保留草稿）。
- **给新手的教训**：DSH 的 RPC 参数形状不是「统一 `{request}`」，**要照 descriptor 表**；错误信息在 `error.failure` 不在 `error.code`；测试替身必须和线上同形，否则测试是自我安慰。

#### 坑 D3　把 `ctx.settings` 的 prototype 方法裸引用交给 `useSyncExternalStore`，设置区块首屏必崩

- 来源：`dsh-web`　`.agents/notes/implemented/bug-fix/2026-09-01-settings-scope-useSyncExternalStore-binding.md`
- **现象**（笔记逐字，含报错）：
  ```
  TypeError: Cannot read properties of undefined (reading 'store')
      at getSnapshot (client.js:998)        <- official dsh-client-ui-settings bundle
      at useSyncExternalStore (frontend bundle)
      at AutoSettingsPanel (AutoSettings.tsx:76)
  slot entry crashed in 'settings.section'
  ```
  每次安装，这个区块首次渲染就崩（v0.3.11 起）。
- **根因**：`AutoSettings.tsx` 把 `props.settings.subscribe` / `props.settings.getSnapshot` 当裸引用传给 `useSyncExternalStore`。settings prop 是官方 `SettingsScope` 实例，这两个方法**是读 `this.store` 的 prototype 方法**；React 以裸函数调用它们，`this` 是 `undefined`。
- **修复**：用 `useMemo` 绑定：`settings.subscribe.bind(settings)`（保持 hook 身份稳定；scope 对象每个条目身份稳定，不会引起重复订阅）。并**审计全仓所有 `useSyncExternalStore`**，确认只有 settings scope 是 prototype-方法面；补一个「故意用 prototype 方法 fake」的回归测试 + 一个断言「裸调用该 fake 会崩」的前提守卫。
- **给新手的教训**：`ctx.*` / service 上的方法是**带 `this` 的方法**；解构或当回调传出去前先 `bind`。这条和「`ctx.slots.register` 丢 this」（坑 C1）是**同一类事故**，在 DSH 里反复出现。

#### 坑 D4　`ctx.get('xxx')` vs `ctx.xxx`：直接属性读会抛 `cannot get property ... without inject`

- 来源：`omdsh-dev_DSH-better-sidebar` `c81de33`
- 提交信息原文：
  ```
  fix: @-reference button no-ops — read conversation via ctx.get, not the ctx property

  Cordis only grants property reads for services declared in the plugin's
  inject list; every other read throws "cannot get property X without inject"
  (the app's own plugins read 'conversation' through ctx.get for this reason).
  referenceInChat now resolves the conversation service lazily via
  ctx.get('conversation') and no-ops when absent.
  ```
- 来源：`omdsh-dev_DSH-better-sidebar` `197b10a`
- 提交信息原文（更完整，含死锁说明）：
  ```
  fix(sidebar): read betterSidebar via ctx.get() in all internal consumers

  ... the Cordis plugin loader registers the provided betterSidebar impl on a
  neighboring fiber that is not on the rendering fiber parent chain, so every
  direct ctx.betterSidebar read inside the plugin own tree throws

    cannot get property "betterSidebar" without inject

  and the panel dies inside RenderBoundary on page load ... declaring
  betterSidebar in the plugin own inject would deadlock the fiber (it
  waits for the service before running apply, but the service is only
  provided inside apply).

  ctx.get() resolves through the root reflect store and is unaffected by
  the fiber chain, so all 26 internal reads switch to it. External
  consumers keep using ctx.betterSidebar after injecting it, unchanged.
  ```
- **现象**：`@` 引用按钮点了没反应；侧栏面板加载即白屏。
- **根因**：cordis 只允许读 **inject 列表里声明过的**服务属性，其余一律抛错；而**自己 `ctx.provide()` 的服务又不能在 apply 前 inject**（会死锁）。
- **修复**：插件**内部**用 `ctx.get('服务名')`（走 root reflect store，不受 fiber 链影响），取不到就 no-op；**外部消费者**仍照常 `inject` 后 `ctx.服务名`。
- **给新手的教训**：这是 DSH 新手第一个必踩的坑。一句话记住：**自己 provide 的服务，自己读要用 `ctx.get()`；读别人的服务，先在 `inject` 里声明。**

### B 组：热更新 / HMR / 重新挂载

#### 坑 H1　HMR 原地替换 DOM 节点后，观察器挂在已分离节点上永久失效（底栏空白 / 输入框位移）

- 来源：`omdsh-dev_DSH-better-sidebar` `e8d0498`
- 提交信息原文（截断）：
  ```
  fix(drag): 中断/快速释放不再回滚，HMR 后中心列重定位兜底 (#247 #248) (#249)

  #248 HMR 后底栏空白/输入框位移：
  - #root 观察改为 childList+subtree：HMR 原地替换 centerCol 节点时
    childList-only 观察器不触发，ref/RO 挂在已分离节点上永久失效
  - locate 只在列节点身份变化时测量（同节点缩放交给 ResizeObserver），
    rAF 防抖避免流式渲染 mutation 突发强制布局
  - 列节点断开（isConnected=false）时丢弃引用，下次 tick 重新定位
  - 1.5s 兜底重定位 interval：任何 HMR teardown/setup 时序都能在数秒内
    收敛（style 属性字节相同、观察器尚未挂上等盲区全部覆盖）
  ```
- **现象**：改完前端热更新后，底部面板空白、输入框位置漂移。
- **根因**：HMR 会**原地替换** React 树里的 DOM 节点；`childList`-only 的 MutationObserver 对「同一父节点下子树被换」不敏感，`ref`/`ResizeObserver` 还挂在**已分离**的旧节点上，永久失效。
- **修复**：`childList+subtree` 观察；**只在列节点身份变化时**重新测量（同节点缩放交给 ResizeObserver）；`isConnected === false` 时丢弃引用，下个 tick 重新定位；加一个 1.5s 兜底重定位 interval 覆盖所有 HMR 时序盲区。
- **给新手的教训**：任何时候拿到 DOM 引用都要用 `node.isConnected` 兜底；**HMR 下没有「一直有效」的 DOM 引用**。

#### 坑 H2　构建期给产物打补丁不具持久性，任何别的构建路径都能让它复发

- 来源：`omdsh-dev_DSH-better-sidebar` `7eccc49`（revert）
- 提交信息原文：
  ```
  revert: 移除构建期 IME 守卫补丁 — 补丁打在产物上不具持久性

  taekchef 的 apply-ime-guard.mjs 在每次 build/prepare/bundle 后把守卫
  字符串注入 lib/client.js，但补丁对象是构建产物而非源码：
  - 裸 tsdown 重建 / 其他构建路径产出无守卫的 bundle（#562 复发根因）
  - 守卫逻辑游离于源码之外，难以测试与维护

  运行时方案（src/client/ime-guard.ts + tests/ime-guard.spec.ts）已在
  源码内实现同等守卫 ... 任何构建方式产物都自带守卫。
  ```
- **现象**：某个修复「明明提交了」，换个构建命令就复发。
- **根因**：补丁打在**产物**（`lib/client.js`）而不是源码；产物可被任意构建路径覆盖。
- **修复**：把逻辑搬进源码（`src/client/ime-guard.ts`）并带测试，删除构建期注入脚本。
- **给新手的教训**：**永远不要手动改 `lib/`、`dist/` 里的产物**。改源码，重新 build。

#### 坑 H3　「用完不清理」的全局副作用：卸载后样式/变量残留

- 来源：`omdsh-dev_DSH-better-sidebar` `9aeb046`
- 提交信息原文（截断）：
  ```
  fix: sidebar crash #31 — layout-push CSS-variable leak + per-tab error containment

  1. Layout-push leak (root cause): the layout-push effect wrote
     --dsh-sidebar-width/--dsh-sidebar-height on document.documentElement
     without a cleanup, so ANY unmount of the Sidebar (error-boundary swap,
     plugin disable, HMR) left the variables behind and layout.css kept
     squeezing #root with a stale margin — "the sidebar cannot be hidden"
     until a full reload. The effect now removes both properties on cleanup
     (the CSS fallback 0px restores the layout).

  2. Crash containment (UX): the root error boundary previously replaced the
     WHOLE sidebar — toggle cluster included — with an error strip on any tab
     crash. A new shared RenderBoundary (src/client/RenderBoundary.tsx) now
     scopes containment per tab ...
  ```
- **现象**：侧栏「关不掉」，必须整页刷新；任一个 tab 崩溃会把整个侧栏（连开关）换成错误条。
- **根因**：① 往 `document.documentElement` 写 CSS 变量却没 cleanup，卸载（错误边界切换 / 插件禁用 / HMR）后残留；② 错误边界粒度太粗。
- **修复**：effect cleanup 里 `removeProperty`；错误边界**按 tab 收敛**（`src/client/RenderBoundary.tsx`），用 `createElement` 渲染 descriptor 让顶层组件 throw 也能落进边界。
- **给新手的教训**：往 `html`/`body` 写 token/变量/属性，**必须成对写 cleanup**；否则用户唯一的自救方法是刷新页面。dsh-web 也有一条同源坑：skin 锁 `html,body` 的 `overflow` 后必须自己成对清理（见坑 S1）。
### C 组：插槽 slots

#### 坑 C1　把 `ctx.slots.register` 解构成裸函数调用，丢 `this` 后抛 `reading 'effect'`，且被空 catch 吞掉

- 来源：`dsh-web`　`.agents/notes/implemented/bug-fix/2026-08-26-dsh-perf-render-shadow-rework.md`
- **现象**（笔记逐字）：
  > **P1 assistant-step shadow never registered**: `registerAny = ctx.slots.register; registerAny(...)` strips the service instance (`this`), so `register` threw `Cannot read properties of undefined (reading 'effect')`. The original catch was empty, hiding the failure; the fiber chain proved the official `AssistantNodeView` always rendered.
- **根因**：① 解构丢 `this`；② **空的 catch 把失败藏了**（日志里什么都看不到）。
- **修复**（笔记逐字）：*"registration uses the lowest existing priority minus one to win the keyed cell, and the register call is bound to the slot service instance"*；并且 *"All three shadow/enable failure paths now log (warn) instead of swallowing silently, plus one per-page diagnostic line reporting the registered priority and the projected cell winner."*
- **给新手的教训**：**不要解构 `ctx.xxx` 上的方法**；**不要写空 catch**。

#### 坑 C2　直接 `slots.register` 会早于宿主的子插槽声明，抛 "not declared"

- 来源：`omdsh-dev_DSH-better-sidebar` `0f9af85`
- 提交信息原文（逐字）：
  ```
  fix: 聊天产出文件行拦截改用 slots.inject 延迟注册（issue #15）

  conversation.chat.turnTail 是宿主 ui-conversation 在 conversation.chat.node
  children 表中声明的子插槽，直接 slots.register 会早于声明而抛
  "not declared (a parent entry's children table must declare it)"，
  导致拦截注册失败回退默认 deliverables 行为并弹诊断条。

  改用 ctx.slots.inject 等待声明落账后再注册（与官方
  dsh-client-ui-deliverables 同款写法）：已声明则同步注册，未声明则
  在声明提交时注册，声明撤销自动卸载、重声明重新注册，fiber 卸载
  幂等清理。
  ```
- **现象**：往 `conversation.chat.turnTail` 注册拦截「注册了但没生效」，回退默认行为并弹诊断条。
- **根因**：该插槽是宿主的**子插槽**（父条目 `conversation.chat.node` 的 children 表里声明的），**声明时机晚于**你的 apply。
- **修复**：用 `ctx.slots.inject`（等声明后再注册；已声明则同步注册；声明撤销自动卸载；重声明重新注册；fiber 卸载幂等清理）。这正是官方 `dsh-client-ui-deliverables` 的写法。
- **给新手的教训**：**注册插槽先用 `slots.inject`，不要用 `slots.register` 硬怼**；DSH 里「注册了但没显示」九成是插槽名写错（要用宿主的**全名**如 `conversation.chat.turnTail`）或注册时机太早。

#### 坑 C3　keyed slot 的 `(key, priority)` 唯一性：两个插件都算 `-1` → 后 apply 的那个直接抛错

- 来源：`dsh-web`　`.agents/notes/implemented/bug-fix/2026-08-27-perf-shadow-priority-headroom.md`
- **现象**（笔记逐字）：
  > The keyed client slot `conversation.chat.node` enforces uniqueness per `(key, priority)` pair: registering an entry that collides on both throws, and the throwing plugin fails to apply ("keyed slot ... already has an entry ... registered by ...").
  > Loading the family bundle together with better-session therefore failed client boot: dsh-perf claimed `assistant-step` at `-1` first (registration order depends on apply order), and message-actions then threw on the same `(key, priority)`. Whichever order the two apply in, one of them dies while both compute or pin exactly `-1`.
- **根因**：`conversation.chat.node` 是 keyed slot，按 `(key, priority)` 去重；`dsh-perf` 用 `min(existing) - 1`（当时算出 `-1`），第三方 `@morlay/ui-conversation-message-actions@0.0.11` 硬编码 `-1`，两者撞车；**谁先 apply 谁活**，与顺序相关。
- **修复**（笔记逐字代码块，**逐字照抄**）：
  ```ts
  const SHADOW_PRIORITY_HEADROOM = 8
  const floor = (existing.length === 0 ? 0 : Math.min(...existing)) - 1 - SHADOW_PRIORITY_HEADROOM
  ```
  即从「紧贴最小值的 `-1`」改为「留 8 格安全带」：官方渲染器在 0 时影子落在 `-9`；若别人先在 `-1`，影子落到 `-10`。**顺序无关**。
- **给新手的教训**：往 keyed slot 注册时**不要用 `-1`、`0` 这类常见值**，留安全带；插槽投影规则（这里是「lowest renders」= 数值小的先渲染）要去宿主文档/官方包里确认。

#### 坑 C4　插槽宿主 DOM 结构变了（0.1.x 把 slot 包进 `[data-slot]`），靠 `nth-child` 的选择器全失效

- 来源：`omdsh-dev_DSH-better-sidebar` `0a07cff`
- 提交信息原文（逐字）：
  ```
  fix: 适配 DSH 0.1.x 的 [data-slot] DOM 结构，恢复 Session log 挤压与布局

  DSH 0.1.x 把 slot 宿主包进 [data-slot] 容器：
  #root > div[data-slot=root] > div.frame > div.centerCol
    > div[data-slot=conversation] > div.root[data-phase]
      > div[data-slot=conversation.session.header] > header

  旧选择器 #root > div > div:nth-child(2) 选中的是 data-slot=root 包装
  层的第 2 子元素（不存在，其唯一子元素是 frame），导致：
  - 折叠态 header 右 padding 挤压失效（Session log 胶囊被按钮簇盖住）
  - 底部面板纵向挤压 / 拖动过渡 / 减少动效全部失效
  - Sidebar.tsx 中间列定位器（#root > div 的 children[1]）失效，
    底部面板宽度测量回退为 0

  修复：全部改用 [data-slot] 语义锚点——
  - 中间列：#root > div[data-slot=root] > div > div:nth-child(2)
  - header：body[data-dsh-sidebar-collapsed]
    [data-slot=conversation.session.header] > header
  - Sidebar.tsx 定位器：#root [data-slot=conversation] 的 parentElement
    （= centerCol，探针实测确认）
  ```
- **现象**：升级宿主后，自己的定位/挤压样式**静默失效**（不报错，只是不对）。
- **根因**：宿主 0.1.x 给每个 slot 包了 `[data-slot=<插槽全名>]` 容器，改变了 DOM 层级；`nth-child` 这类位置选择器全部错位。
- **修复**：改用 `[data-slot="<插槽全名>"]` 语义锚点 + 属性锚点，而不是位置。
- **给新手的教训**：**不要用 `nth-child` 锚定宿主 DOM**；用 `[data-slot="..."]`、`[data-dsh-plugin]`、`[data-dsh-part]` 等语义属性（§三 有 dsh-web 的强制规范）。

#### 坑 C5　插槽 host 里「像自己」的 DOM 是别人的：宿主 slot 内已有官方组件，叠加成三层

- 来源：`dsh-web`　`.agents/notes/implemented/bug-fix/2026-08-24-wallpaper-exclusive-queue-dock-chrome.md`
- **现象**（笔记逐字）：
  > The native queue dock (the `data-queue-dock` element rendered by QueueDock in dsh-client-ui-conversation) stacks two boxes inside the conversation.input.dock slot: a root whose class contains `_dock` and therefore receives the skin input-card material, whose horizontal padding reads as a halo ring around the content, and an inner panel that paints its own near-opaque `--dsw-specific-tip` fill with a top-only border radius plus an ::after bottom highlight that reads as a bright seam above the composer card. With wallpaper-exclusive active the queued message renders as three visible layers instead of one.
- **根因**：`conversation.input.dock` 插槽里已经有官方组件自己的两层盒子；皮肤再叠一层材质，视觉上成了三层。注意：**官方组件的类名是带哈希前缀的**（如 `_dock`），且随版本变化。
- **修复**：用**属性锚点** `[data-queue-dock]`（而不是类名）收窄作用域；并明确否决「全局重映射 `--dsw-specific-tip`」（*"a global token remap would leak into unrelated consumers of that token"*）。
- **给新手的教训**：**不要用宿主组件的哈希类名做选择器**；用 `data-*` 属性或 `[class$="_xxx"]` 尾匹配（dsh-web 多处用 `[class$="_frame"]` / `[class$="_centerCol"]` 这种写法）。另注意：宿主 patch 里出现的 `[data-phase="active"]` 可能是**死代码**（该笔记原文：*"The `[data-phase="active"]` gate from the earlier round matched no shipped shell build and is removed as dead code"*）。
### D 组：样式 / 主题

#### 坑 S1　给 `#root` 加 `width: 100% !important` 直接顶死第三方侧栏

- 来源：`dsh-web`　`.agents/notes/implemented/bug-fix/2026-08-27-skin-center-root-width-lock.md`
- **现象**（笔记逐字）：
  > Skin Center 0.3.5 added viewport and root lock rules ... However, it placed `width: 100% !important;` on `[id="root"]`. This broke third-party sidebar plugins like `dsh-better-sidebar` (#1222), which resize `#root` via `#root { width: calc(100% - var(--dsh-sidebar-width, 0px)) }` ... the `!important` rule forced `#root` to remain at 100% width, causing the right sidebar panel to float over and obscure chat messages.
- **根因**：为了防外层滚动条，给 `#root` 上了 `width !important`，**把「别人要靠改 `#root` 宽度来推挤布局」这条契约踩死了**。
- **修复**：`width: 100% !important` → **`max-width: 100% !important`**；保留 `height/max-height/overflow/box-sizing`。
- **给新手的教训**：`!important` 在插件生态里是**跨插件事故**。要用就说清「我要锁的是什么、不锁什么」。

#### 坑 S2　CSS Modules 同名哈希撞车：8 个包都叫 `settings-card.module.css`，7 个的样式被去重守卫吃掉

- 来源：`dsh-web`　`.agents/notes/implemented/bug-fix/2026-09-02-css-module-style-tag-collision.md`
- **现象**（笔记逐字）：
  > In the deployed web GUI every family settings card except the first-processed one rendered as bare UA defaults: collapsed cards were fit-content inline buttons instead of full-width disclosure rows, and the pet / doctor / task-board / remote / describe-image / desktop-launcher fields had no styling at all, under every appearance skin.
- **根因**（笔记逐字）：
  1. 共享客户端预设（`shared/tsdown.client.ts`）用 `data-plugin-css = "<bundle id>/<basename>"` 给注入的样式表打 tag。聚合构建内联了 8 个包，每个都带自己的 `settings-card.module.css`，**8 个 tag id 相同**，幂等守卫让第一个 tag 压制了其余 7 个；而每个包的 class map 带**基于路径**的 CSS-modules 哈希 → 7 份 class map 指向从未注入的样式。
  2. `scripts/sync-shared.mjs` 的 `SETTINGS_CONSUMERS` 漏了 `dsh-perf`，它的卡壳副本漂移。
- **修复**：预设改用**完整 repo 相对文件 id** 作为 tag key（`<bundle id>/packages/<pkg>/src/client/<file>.module.css`），同名不同包的模块不再互相压制；`data-plugin`（卸载清理键）不变。并给 `sync-shared` 增加 `SETTINGS_CARD_ONLY_CONSUMERS` 分层。笔记明确否决替代方案：*"Content-hash dedupe of identical stylesheets: rejected — CSS-modules hashes derive from the file path, so identical copies still produce different class maps and cannot share one tag."*
- **给新手的教训**：多个插件被同一 bundle 内联时，**样式注入的去重键不能用文件名**；这也是「CSS Modules 哈希由路径决定」这一事实的实战后果。

#### 坑 S3　`backdrop-filter: blur()` 挂在根容器上，流式输出时 GPU/CPU 爆 80%

- 来源：`dsh-web`　`.agents/notes/implemented/bug-fix/2026-09-03-blue-fantasy-backdrop-filter-perf.md`
- **现象**（笔记逐字）：*"When using the Blue Fantasy skin with a background image ... during session task runs with continuous streaming token output, the GPU and CPU load reached over 80% (issue #1358)."*
- **根因**：`patches.css` 把 `backdrop-filter: blur(12px)` 挂在根视口容器 `.aionui-root` 上；**聊天气泡每追加一个 token 都触发整视口重绘 + 对壁纸做昂贵的高斯模糊重采样**。
- **修复**：把 `.aionui-root` 从 blur 规则里去掉，blur 只留在侧栏列；给侧栏列加 `contain: paint`，让聊天区的 DOM 变更不再让侧栏图层失效。笔记明确否决「去全局 blur」和「节流 React 流式更新」。
- **给新手的教训**：**`backdrop-filter` 永远不要挂在滚动/流式更新的容器上**；用 `contain: paint` 把重绘关在局部。

#### 坑 S4　暗色/亮色双方案：卡片故意保持深色，但亮色下没设文字色 → 深底深字看不见

- 来源：`dsh-web`　`.agents/notes/implemented/bug-fix/2026-08-24-maid-atelier-light-composer-contrast.md`
- **现象**（笔记逐字）：*"with the maid-atelier (Abyssal Maid Atelier) skin active in the light scheme, text typed into the conversation composer is unreadable."*
- **根因**：composer 卡片在**两种方案下都故意保持深蓝**；壳层通过卡片里一个高亮背板 div 画输入文字（textarea 用透明 `-webkit-text-fill-color` 叠在上面，只贡献光标和选区；`[data-input-mirror]` 是 `visibility:hidden` 的测量副本），而**亮色覆盖没设背板颜色** → 继承了亮色墨色 `#172347`，深蓝底 + 深蓝字。亮色光标 `#405a99`、placeholder `#4d5d7f` 同病。
- **修复**：把 composer 卡片当作「方案无关的深色面」，把背板/镜像文字 `#eef3fc`、光标 `#bcd2ff`、placeholder `#b6c2e0` 在两种方案下都钉死；删掉多余的 `body[data-ds-dark-theme]` 覆盖。skin 版本 bump 0.3.0→0.3.1。
- **给新手的教训**：暗色/亮色不是「只调背景色」；**只要有一处背景不随方案变，那里的文字色/光标色/placeholder 就都不能继承默认墨色**。

#### 坑 S5　token 误用：把品牌色当填充色 → 官方主题下黑底黑字/白底白字

- 来源：`dsh-web`　`packages/AGENTS.md`（**逐字可读**，原文引用）：
  > 填充主按钮一律用主按钮三件套（`--dsw-alias-button-primary-fill` / `--dsw-alias-button-primary-hover` / `--dsw-alias-label-primary-foreground`，明暗两组），不得把 `--dsw-alias-brand-primary` 当填充色（官方主题下它与前景同值，会出现黑底黑字/白底白字）
- **给新手的教训**：**颜色只用语义 token，不要用品牌色当填充**；这是被写进包级规范的血泪条款。

#### 坑 S6　skin 覆写 `--dsw-skin-scrim` 与背景显隐互相踩：拖动宠物/切模型把背景不透明度重置成 0

- 来源：`dsh-web`　`.agents/notes/implemented/bug-fix/2026-08-24-skin-background-scope-reset.md`
- **现象**（笔记逐字）：*"moving the whale pet or switching models can reset the Skin Center background occlusion to 0%."*
- **根因**：旧的 `skin-background` settings scope 在**任何 settings 文档变化**时都会发布一份 schema 解析后的 section，而 Skin Center v2 的 active-state 文档才是背景的权威存储。把「解析后的 section」当成完整替换，会让 schema 默认值 `backgroundOpacity: 0` 覆盖已持久化的值（如 100）。
- **修复**：把旧 scope 当成**带 revision 围栏的原始用户字段补丁**——没有 namespace revision 或 revision 相同的发布一律忽略；只读取 `snapshot.user`，过滤并归一化「已知且显式存储」的字段，合并进 v2 背景，**绝不用 schema 默认值替换缺失字段**。相关同源坑：`2026-08-26-skin-center-scrim-and-scope-guard.md`（*"removed all hardcoded scrim variable overwrites in `setBackgroundLayer`, keeping `--dsw-skin-scrim` under the sole authority of `BackgroundController`"*）。
- **给新手的教训**：**两个东西都想当「唯一事实源」时必然打架**。settings 的多源合并要按「显式用户字段」而不是「schema 解析结果」合并。

#### 坑 S7　解析 CSS 做审计时 at-rule 递归爆炸，skin 校验跑 ~126 秒

- 来源：`dsh-web`　`.agents/notes/implemented/bug-fix/2026-08-25-token-audit-at-rule-recursion.md`
- **现象**（笔记逐字）：*"`auditTokenContract` ... at-rule branch recursed with `visit(open + 1)` and no block boundary ... on nested at-rule chains (`@media` > `@supports` > `@container` > `@keyframes`, the shape a v1 CSS-modules bundle keeps after migration) the traversal became exponential — auditing the migrated orca-link patches.css took ~126 s and the `dsh-skin validate` / check gates hang on any such skin."*
- **根因**：递归没有 **block 边界**，每个 at-rule 都重扫剩余全部块 → 嵌套 at-rule 下指数级。
- **修复**：把 at-rule 递归限制到它自己的闭合花括号内：`visit(start, limit, ...)`，`limit` 封顶在外层 close。
- **给新手的教训**：解析 CSS（而不是直接交给浏览器）时，**嵌套结构必须有边界**；lightningcss 会产出嵌套 `@media`，这类输入是常态。

#### 坑 S8　宿主锁住 `html,body` 的 `overflow` / `height` 后，第三方布局推挤配套失效

- 来源：`dsh-web`　`.agents/notes/implemented/bug-fix/2026-08-26-viewport-scroll-lock-on-workspace-select.md`
- **现象**（笔记逐字）：*"When selecting or switching a workspace ... the page viewport scrolled downward unexpectedly. The top titlebar and sidebar top were displaced offscreen, `#root`'s bottom border moved to the middle of the viewport, and a large black void appeared at the bottom with a global window scrollbar."*
- **根因**：`html` / `body` 没有 `overflow: hidden`，而 `#root` 在某些皮肤下有 `border: 1px solid` 而没有 `box-sizing: border-box`，产生轻微溢出，浏览器 `focus()` / `scrollIntoView()` 把它滚到了底部。
- **修复**：`html, body` 锁 `height/width/overflow/margin/padding`；`[id="root"]` 锁 `box-sizing: border-box / height / max-height / overflow`（注意**用 max-width 不用 width**，见坑 S1）；`installShellRenderingAdapter()` 里调用 `doc.defaultView?.scrollTo?.(0, 0)` 复位已有滚动偏移；并修皮肤自己的 `box-sizing`。
- **给新手的教训**：**「锁视口」和「让别人推挤布局」是一对矛盾**；锁的时候只锁 `max-*`，把可变更的自由留给别人。
### E 组：插件启用/禁用 / 启停

#### 坑 P1　禁用「载体 bundle」只写了 insert 行的 `disabled: true`，它的顶层副作用行照样生效 → 启动断链

- 来源：`dsh-market_dsh-market` `263665c`
- 提交信息原文（逐字，截断）：
  ```
  fix: 禁用载体 bundle 时连同其 patch 副作用一起回滚 (#224) (#225)

  禁用一个"载体 bundle"（cordis.patch.yml 既 insert 自己的插件、又有顶层行
  修改其他插件的包）时，市场只往 user-patch 写 inserted 行的 disabled: true
  （#147 的结构归属），但 bundle 仍留在 dsh.profile.bundles，其副作用行
  （禁用官方后端 / 改其他插件 config）每次启动照样应用，导致启动断链。
  真实案例 dsh-postgres-backends：禁用后 session-persistence-jsonl 仍被禁、
  storage-domain 仍路由到已禁用的 postgres，sessionPersistence 无提供者。

  修复：toggle 检测到载体 bundle（carrierSideEffectIds = 全部 entry id 减去
  inserted id）时，禁用则把它移出 dsh.profile.bundles、启用则加回---
  bundle patch 整体不再应用，两类副作用同时消失。纯 insert 插件维持原 HMR
  快路径。载体 toggle 需要重启（bundles 为启动期读取）。
  ```
  以及同 PR 的第二段修正（**判据过宽**的教训）：
  ```
  fix: 载体判定收窄为"禁用其他插件"，修复 fixture-cross 重新启用失败 (#224)

  ... 首版 carrierSideEffectIds 把任何顶层副作用行都判为载体，而 e2e 的
  fixture-cross 只是改邻居 dshm-fixture-b 的 config（无 disabled），被误判后
  移出 dsh.profile.bundles，破坏了重新启用 ... 收窄判据：carrierDisableIds
  只识别顶层 `disabled: true` 行（禁用其他插件）。
  ```
- **给新手的教训**：**`cordis.patch.yml` 里「插自己」和「改别人」是两类行**：`- insert:`（自己）与顶层 `- id:`（改已有的别人）。禁用插件时**两类都要处理**，否则会留下幽灵副作用。

#### 坑 P2　把「最后一个 patch 行」删干净后，user patch 层变成纯注释，宿主直接拒启

- 来源：`dsh-market_dsh-market` `bb260cb`
- 提交信息原文（逐字）：
  ```
  fix: never leave the user patch layer without a top-level array

  Disable a plugin, then enable it again, and dsh refuses to start the profile:

    dsh: overlay .../cordis.patch.yml must be a top-level YAML array of
         loader patch entries

  Appending the first row comments the dsh template's `[]` placeholder out (it
  has to — appending after it would put two elements in one document), so
  removing the LAST row left a file of pure comments. yaml.load returns
  undefined for that, dsh's parsePatchList rejects anything that is not an
  array, and the profile will not boot at all. An emptied file has the same
  problem: yaml.load('') is undefined too, and one existing spec asserted
  exactly that empty result — it had encoded the bug as the expectation.
  ```
- **给新手的教训**：**动别人的 YAML 要保证「顶层永远是数组」**；同时注意「一个测试把 bug 编码成了期望」（把 bug 写进了断言）。

#### 坑 P3　装上市集后宿主起不来：ESM 具名导入一个已被删除的 export，任何兜底都来不及跑

- 来源：`dsh-market_dsh-market` `a99a205`
- 提交信息原文（逐字，截断）：
  ```
  fix: installing the market no longer stops dsh 0.1.2-alpha from booting (#437)

  dsh 0.1.2-alpha.2 reached npm today. With the market installed, the host
  does not start:

    SyntaxError: The requested module '@deepseek-ai/dsh-settings' does not
    provide an export named 'installSettingsSection'
    ... dsh exited 1

  0.1.2-alpha.1 deleted `installSettingsSection` and moved `settingsNamespace`
  to another package. src/settings.ts imported both by name.

  The distinction that matters is between a missing SERVICE and a missing
  EXPORT. This module was written for the first: its comment explains that the
  wiring rides a scoped fiber, so a host without a settings service simply
  never runs it. That is true, and `ctx.inject` still does exactly that. But an
  ESM named import of an export that no longer exists cannot degrade — it
  throws while the module is being evaluated, cordis records a failed entry,
  and the host exits 1. The graceful path never got a chance to run. A plugin
  must not be able to stop the host from starting.

  The service itself never changed. `settings.register(ns, schema, { base })`
  is identical in 0.1.0-rc.7 and 0.1.2-alpha.2; only the two convenience
  wrappers went away. So this inlines what the wrapper did ...
  ```
- **给新手的教训**：**「服务缺失」可以优雅降级；「ESM 具名导出缺失」是模块求值期就炸，会带着整个宿主 exit 1**。核心 SDK 只依赖**稳定的 service seam**，不要依赖便利包装函数。

#### 坑 P4　启动期隔离：一个坏插件会拖垮整个家族（甚至整个 `dsh web`）

- 来源：`dsh-web`　`.agents/notes/implemented/architecture/2026-09-01-aggregate-plugin-fault-isolation-shell.md`
- **现象**（笔记逐字）：*"The loader treats all rows as one transactional group (`EntryGroup.update` in the vendored cordis loader): any entry that fails to import or start rolls the whole group back, and the boot audit (`assertEntriesActivated` in `@deepseek-ai/dsh-app-boot`) then aborts the entire `dsh web` process. One broken plugin — an SDK drift, a bad release, a third-party import — took every plugin down"*
- **修复**：每个家族 insert 行的 `name` 改为聚合包的**按家族子路径导出** `@linxin666/dsh-web-all/<family>`，真包名放进 row config 的 `config.plugin`；shell（`packages/dsh-web-all/src/shell.ts`）在 start 时 import 真模块，导入失败/形状不可用/激活失败都被**捕获、记录**，shell 条目本身保持 ACTIVE。另加 `shared/host/run-guarded.ts` 把 fire-and-forget rejection 变成 logged error（因为宿主的 `installFailLoud` 会把**任何** unhandled rejection 变成整进程退出）。
- **给新手的教训**：宿主 loader 把一次 boot 里所有 row 当**一个事务组**；写插件要假设「我挂了不能连累别人」，并且**绝不允许 unhandled rejection 逃逸**（宿主会直接 exit）。

#### 坑 P5　菜单/开关状态与宿主不同步：宿主已禁用的插件，行里还让它显示可点开关

- 来源：`dsh-market_dsh-market` `a40d2d0`
  `fix: market row shows a disabled switch with a tooltip instead of a server-rejected toggle (#99)`
- 相关：`dsh-market_dsh-market` `334965a` `feat: universal plugin enable/disable, catalog-driven deprecation, and custom groups (#60, #11, #59) (#94)`
- **给新手的教训**：**宿主拒绝的开关不要让它「看起来能点」**；失败要显性化。

#### 坑 P6　改了开关要重启，但用户以为已生效

- 来源：`dsh-market_dsh-market` `53c0956` `fix: clear pending restart after successful hot mount (#75)`
- 相关：`dsh-market_dsh-market` `946d765` `fix: an update of a running plugin reads as "restart", not "live" (#172)`；`dsh-market_dsh-market` `a3e7141` `fix: a standing, dismissible restart notice for host-reported pending plugins (#146)`
- **给新手的教训**：**「已生效」和「待重启」必须区分得很清楚**，并在热挂载成功后清掉 pending 标记。

### F 组：构建 / 打包 / `exports` / client bundle

#### 坑 B1　声明了 `dsh.client.platform: "web"` 但 `package.json` 没导出 `./client` → 整个 profile 组合失败

- 来源：`dsh-web`　`.agents/notes/implemented/bug-fix/2026-08-26-dsh-perf-client-export.md`
- **现象**（笔记逐字）：
  > `dsh --profile web` fails before the Web UI starts with `client-modules: 1 client package failed to compose`: `@linxin666/dsh-perf` declares `dsh.client.platform: "web"` but its `package.json` does not export `./client`. The official client-modules loader resolves the declared browser half through `exports["./client"]`, so the missing subpath is treated as a plugin composition error even though `lib/client.js` already exists.
- **修复**：`packages/dsh-perf/package.json` 加标准客户端子路径：`"./client"` 的 types 指 `./lib/types/client/index.d.ts`，runtime 指 `./lib/client.js`；保留原 `dsh.client` 声明。笔记明确否决「用纯字符串 export」：*"the repository family convention uses the conditional object with a `types` entry, and the loader accepts that form directly."*
- **给新手的教训**：**`dsh.client` 声明与 `exports["./client"]` 必须配对**；只有其中一个，客户端半就不进引导清单。

#### 坑 B2　`dsh.client` 字段名写错（旧字段 `dshClient`）→ 浏览器根本不加载插件

- 来源：`omdsh-dev_DSH-better-sidebar` `53a9ced`
- 提交信息原文（逐字）：
  ```
  fix(client-modules): package.json 补 dsh.client 声明 — client 半未进引导清单的根因修复

  诊断（2026-08-11 重启后侧边栏不显示）：host 半正常（/sidebar/api 路由
  200），但页面 window.__DSH_BOOT__ 引导清单 30 个 client 插件中没有
  dsh-better-sidebar。client-modules 扫描器（packages/client/modules）读
  package.json 的 pkg.dsh.client 声明 + exports["./client"] 组合 bundle；
  插件只声明了旧字段 dshClient（dsH 新版本约定改为 dsh.client，工作正常的
  ui-genui 两者并存）。旧字段缺失 → 负判定缓存 → 无 client 入口 → 浏览器
  不加载侧边栏。

  修复：package.json 新增 "dsh": { "client": { inject, platform } }
  与 dshClient 并存（兼容新旧 dsh）
  ```
  相关：`omdsh-dev_DSH-better-sidebar` `7c792c2` `chore: 移除旧字段 dshClient — 只适配新 dsh 版本（dsh.client 声明）`
- **给新手的教训**：**`dsh.client`（点号），不是 `dshClient`**。验证方法（提交原文给的思路）：看页面 `window.__DSH_BOOT__` 的 client 插件清单里有没有你的包。

#### 坑 B3　`exports` 缺子路径别名（`./client/api`、`./client/service`）

- 来源：`omdsh-dev_DSH-better-sidebar` `39455ff`
  `docs+fix: exports 加 ./client/api 别名；catch-all+detect 纯嗅探规则；设计文档偏差记录`
- 相关：`omdsh-dev_DSH-better-sidebar` `291158a`
  `package.json: 加 ./client/service exports 子路径，version 0.4.0`
- **给新手的教训**：`exports` 是**白名单**；你要让外部 import 的每个子路径都得显式列出来（`.`, `./client`, `./client/service`, `./invariant`, `./src/*` 测试用）。

#### 坑 B4　客户端 bundle 不可复现 / 泄漏构建者绝对路径

- 来源：`dsh-market_dsh-market` `1391ada`
- 提交信息原文（逐字）：
  ```
  build: strip the builder's absolute path from the published client artifact (#121)

  client/client.js is committed AND published, so it must be byte-identical
  regardless of whose machine built it. tsdown names the CSS module's
  virtual chunk by absolute path, so the builder's checkout leaked into a
  region comment: main currently ships /Users/<me>/work/dsh-market/… to
  npm, and #99 arrived carrying D:\Github\… — every contributor's artifact
  diff churned on the path plus every hashed class name.

  normalize-client-banner now rewrites those virtual ids to a stable
  repo-relative form (Windows separators included, so a Windows build
  produces the same bytes) and fails the build if this builder's checkout
  path survives anywhere else.
  ```
- 相关：`dsh-market_dsh-market` `9f15747`：
  ```
  build: make the client bundle byte-reproducible (#171)

  ... The CSS module class map was a hole in that: tsdown emits its keys in an
  unstable order, so two consecutive builds of identical source differed by
  ~265 lines. ... Sorting the map fixes it. ... Four consecutive builds now
  produce identical sha256 for both client.js and client.js.map.
  ```
  以及 `8830b8b`：`chore: stop committing client.js.map, which is where the conflicts were (#533) (#539)`
- **给新手的教训**：客户端 bundle 若**提交进仓库或发布到 npm**，必须**可复现**（路径、CSS Modules class map 的 key 顺序都会被 tsdown 带进来）；否则每个人 `npm install` 都会拿到一个 diff，PR 之间在生成文件上冲突。

#### 坑 B5　聚合包把 8 个包的客户端内联成一个 2.5 MB 产物

- 来源：`dsh-web`　`.agents/notes/implemented/bug-fix/2026-09-02-aggregate-client-children-mount.md`
- 原文：*"`@linxin666/dsh-web-all`'s `lib/client.js` grows from ~14 KB to ~2.5 MB (the family's client code rides one artifact; the loader serves it as a single entry)."*
- 根因：客户端模块扫描器 `@deepseek-ai/dsh-client-modules` 是**从 loader 的 entries 组合浏览器 bundle 图**的；它**看不到 shell 的 apply 里创建的 cordis 子插件**，所以子插件的客户端 bundle 永远到不了浏览器。修法是让聚合的客户端 bundle**静态 import 每个子插件的 `./client`**（生成 `children.specifiers.json` / `children.generated.ts` / `children.modules.d.ts`），并 `mount-children.ts` 把每个子插件当**嵌套客户端插件**挂载。
- **给新手的教训**：**「宿主半能看到」≠「浏览器半能看到」**。客户端 bundle 的图只由 loader entries 决定；动态 create 的子插件必须显式带进客户端图。

#### 坑 B6　最近邻 `package.json` 规则：多一层子路径导出把扫描器引到错误的清单上

- 来源：`dsh-web`　`.agents/notes/implemented/architecture/2026-09-02-aggregate-family-row-display-names.md`
- **原文要点（逐字）**：*"A marker manifest (`src/shells/package.json`, built into `lib/shells/`) sits beside the re-export: the client module scanner resolves a row's module URL and walks up to the nearest package.json, and the marker (string `name`, `type: "module"`, no `dsh` field) stops that walk before it reaches the package root. Without it, every family row would resolve to the aggregate's own manifest and its `dsh.client` face — `reconcilePackage` then throws "resolves from multiple active Loader sources" ... `type: "module"` is required by the same nearest-manifest rule: without it Node parses the re-export as CJS."*
- **给新手的教训**：**客户端扫描器按「最近的 package.json」判定归属**。你若在包内再造一层子目录导出，务必放一个「标记清单」阻挡向上查找，并带 `type: "module"`。

#### 坑 B7　打包/构建杂项（同一类）

- 来源（提交信息原文）：
  - `dsh-web` `scripts/aggregate.mjs`：手写 YAML 子集扫描器，无 js-yaml 依赖（`2026-08-26-aggregate-harness-row-patches.md` 原文：*"Switch the generator's parser to a general YAML library: rejected — the repository has no js-yaml/yaml dependency, and the existing `parseManifest` already establishes the hand-rolled YAML-subset scanning style"*）
  - `omdsh-dev_DSH-better-sidebar` `61c9c55`：`fix(registry): registry 打包补上 mermaid 懒加载 chunk` —— **懒加载 chunk 要显式补进产物清单**
  - `omdsh-dev_DSH-better-sidebar` `4af8d31`：`fix: devDependency 改用 npm registry 版本，去掉本机 link 路径` —— **不可把本机 link 路径提交进清单**
  - `omdsh-dev_DSH-better-sidebar` `3d23ceb`：`fix(ci): pnpm 版本统一由 packageManager 字段供版，移除 action 显式 version 输入`
  - `dsh-web` `3a645bef`：`fix(pet): bound the frames2d warm pass behind a fetch pool` —— **预热/预取要有界**
  - `dsh-web` `2026-09-10-pet-frames2d-fetch-storm.md`（笔记，文件在但 blob 未本地）：**fetch 风暴**主题
- **给新手的教训**：懒加载/预取/生成物都要有**显式清单 + 一致性门禁**（`--check`）。

DSH_EOF_MARKER
### G 组：时序竞态

#### 坑 R1　启动竞态：host service 还没注册，首次轮询就报错（每次启动都打堆栈级 console.error）

- 来源：`dsh-web`　`.agents/notes/implemented/bug-fix/2026-08-28-task-board-roster-poll-boot-race.md`
- **现象**（笔记逐字）：*"the session tree activates `sessionController` only after its nine inject services resolve ... while `TaskBoardHostService.start()` fires the first roster poll immediately during plugin start. The first `session/list` therefore fails with the gateway's `service-unavailable` and every boot printed a stack-trace-level `console.error` ... even though the 5-second poll recovered on its next tick."*
- **修复**：`listRunning` 在网关报 `code: 'service-unavailable'` 时重试（5 次 × 2s 退避，可通过构造参数覆盖）；**只对这一个错误码重试**，其他错误保持单发语义；耗尽后只打一次同样的错误并返回 `{ known: false }`。笔记明确否决「按固定秒数延迟首轮」（*"a blind wait that still races on slow machines"*）和「inject 等 `sessionController`」（*"a hard wait pends the whole entry forever on hosts that never activate the service"*）。
- **给新手的教训**：**插件 start() 时别假设别人的 service 已就绪**；遇到 `service-unavailable` 要**有限重试**，不要硬 inject、也不要盲等固定时间。

#### 坑 R2　会话列表瞬时 `current = undefined` 把看板误关

- 来源：`dsh-web`　`.agents/notes/implemented/bug-fix/2026-08-26-task-board-navigation-jitter.md`
- **现象**（笔记逐字）：*"the session list snapshot momentarily emitted `current = undefined`. The controller's `onSessionsChanged()` checked `current !== this.lastCurrent` and immediately called `this.closeBoard()`, closing the task board on click."*
- **修复**：只在「两个有效且不同的 session id 之间导航」时才关：`this.lastCurrent !== undefined && current !== undefined && current !== this.lastCurrent`。同一天的后续笔记干脆**移除了隐式关闭**（`2026-08-26-task-board-implicit-close-removal.md`）：看板只由显式用户动作关闭。
- **给新手的教训**：**列表快照会瞬时缺字段**（子代理链初始化、视图挂载时都会）。不要用「值变了就关/就重置」；加 `undefined` 守卫，或干脆别隐式动作。

#### 坑 R3　DOM 被换掉后挂载点不 `isConnected`，返回按钮永久失效

- 来源：`dsh-web`　`.agents/notes/implemented/bug-fix/2026-08-27-task-board-return-button-and-remount-resilience.md`
- **现象**（笔记逐字）：
  > In DSH WebView2 desktop and web environments, clicking the "Return to session" (`返回会话`) button on top of the task board had no response and left the user stuck on the task board view.
- **根因**（笔记逐字）：
  - `BoardController.closeBoard()` had an early-return guard `if (!this.boardOpen) return`, preventing cleanup notification when internal state drifted or needed active attribute teardown.
  - `openSession()` in `controller.ts` navigated to the execution session but did not explicitly invoke `this.closeBoard()`.
  - `board-mount.tsx` had `if (container !== undefined) return;` which did not verify `container.isConnected`. When DSH React re-rendered or swapped the center conversation column, the container disconnected and could not self-heal/remount.
- **修复**：`closeBoard()` 无条件置 `boardOpen = false` 并 `notify()`；`openSession()` 先 `closeBoard()`；`ensure()` 检查 `container.isConnected`，断开则卸载旧 root、移除分离元素、重新挂到当前会话列。
- **给新手的教训**：**「容器已存在就直接 return」是错的**——必须检查 `isConnected`；幂等的 close/cleanup 不要加早退守卫。

#### 坑 R4　面板/布局「推挤」的变量在挂载期不持续有效，拖拽松手后闪一下全宽

- 来源：`omdsh-dev_DSH-better-sidebar` `5cc1a4b`
  `fix(layout): 推挤变量挂载期持续有效，拖拽松手后底边栏不再闪全宽 (#258) (#259)`
- 相关：`omdsh-dev_DSH-better-sidebar` `a2bb04b` `fix: 底栏宽度直测中间列，修复启动竞态下底栏跑到最左边`
- **给新手的教训**：**布局推挤类 CSS 变量要在挂载期持续有效**，不能「设置一次就完」；启动竞态下测量要落到真实列而不是默认值。

#### 坑 R5　子代理实时预览 O(N²) 请求风暴

- 来源：`omdsh-dev_DSH-better-sidebar` `6cea4bd`
- 提交信息原文（逐字，截断）：
  ```
  fix(subagent): 子代理页实时预览改为批量接口，避免 O(N²) history 请求风暴 (#298)
  ...
  旧实现中，每个 running 子代理卡片都独立轮询 subagents.history：
  - N 个 running 子代理 → 每 3 秒产生 N 次 subagents.history 请求；
  - 每次 subagents.history 都会在 host 侧触发一次完整的 listChildren 全量
    子代理目录枚举；
  - 子代理数量越多，服务端重复扫描越严重，近似 O(N²) 放大；
  - 请求超过 3 秒时，客户端还会 abort 旧请求并重发，进一步形成请求风暴。
  改动：① 新增 host 批量接口 POST /sidebar/api/subagents.live；② 客户端改
  为单轮询 + 单飞行请求（递归 setTimeout，慢请求不再被 abort/重发，页面隐藏
  或 root 变化时停止轮询并中止在途请求）；③ 解析器从事件尾部反向扫描、命中
  即停；④ UI 不变。
  ```
  后续 CR 修正（同 PR 第三段）还加了 **12 条消息窗口**：*"lastActivity 增加可选 maxMessages 参数：反向扫描按表面消息计数，窗口满后更老事件一律跳过；路由传 LIVE_WINDOW_MESSAGES = 12（导出常量）"* —— 否则长会话会显示陈旧 tool，且每次轮询反向扫描整个事件数组。
- **给新手的教训**：**列表页不要「每个卡片一个定时器」**；合并成一个轮询 + 单在途请求 + 隐藏页面停止 + 有界窗口。

#### 坑 R6　`getBoundingClientRect` 绝对定位法在皮肤/滚动/动态加载下必错

- 来源：`dsh-web`　`.agents/notes/implemented/bug-fix/2026-08-31-git-graph-branch-chip-hero-portal.md`
- **现象**（笔记逐字）：*"In blank sessions, the Git branch selector (`BranchChip`) detached and floated high above the conversation area / hero whale illustration rather than sitting in the row alongside `WorkspaceChip` and `AgentPresetSeat`."*
- **根因**（笔记逐字）：*"`BranchChip` calculated `top = rowRect.top - stackRect.top + ...` (coordinates relative to `div.wSkVaW_composerStack`) and applied `position: absolute; left: ${left}px; top: ${top}px` (`css.anchorHero`). However, `composerStack` and `heroWorkspaceRow` are `position: static` flex containers without an established containing block; the nearest positioned ancestor establishing a containing block was `div.wSkVaW_body` at the top of the conversation view (`y = 0`)."* → 相对 A 算坐标、相对 B 定位，偏几百像素。
- **修复**：不再算坐标，直接 `createPortal(chipNode, heroRow)` 把组件**门户**进官方 `heroWorkspaceRow` flex 容器；隐藏一个零尺寸占位留在 `conversation.input.dock`；`.anchorHero` 用 `display: inline-flex; align-items: center;`，**不用 `position: absolute`**，让 chip 成为原生 flex 子项，继承官方的 2px gap 与响应式流。
- **给新手的教训**：**要做「塞进宿主某一行」的效果，就 portal 进去，别用 `getBoundingClientRect` 算绝对坐标**（跨滚动、视口变化、动态加载、不同皮肤的 containing block 都会错）。

### H 组：跨平台（Windows / 换行符 / 大小写）

#### 坑 W1　`{...process.env}` 展开后 `Path` 与 `PATH` 并存，子进程丢失全部系统目录

- 来源：`dsh-web`　`.agents/notes/implemented/bug-fix/2026-09-04-desktop-child-env-path-normalization.md`（提交 `7d810121`）
- **现象**（笔记逐字）：*"Plugins relying on Windows DPAPI credential decryption (such as `dsh-chatgpt-subscription`) failed when calling `spawn('powershell.exe', ...)` with `Error: spawnSync powershell.exe ENOENT` ... Any external tools invoked by plugins (such as `codegraph`) failed to resolve"*
- **根因**（笔记逐字，含代码）：
  ```javascript
  const env = { ...process.env, DSH_HOME: home };
  const nodeBinDir = process.platform === 'win32' ? nodeHome : path.join(nodeHome, 'bin');
  env.PATH = nodeBinDir + path.delimiter + (env.PATH ?? '');
  ```
  *"On Windows, the operating system exposes the environment variable as `Path` (mixed-case) rather than `PATH`. When `process.env` (a case-insensitive Proxy in Node) is spread into a plain JavaScript object, the property is stored with its exact key `'Path'`. Because `env.PATH` was undefined before the assignment, `env.PATH` was set to *only* `nodeBinDir`. This left two distinct keys in the environment object: `Path` ... and `PATH` ... When Node.js and libuv serialized the environment block for `CreateProcessW`, `PATH` took precedence or collided, causing child processes to lose all standard Windows system directories (`C:\Windows\System32`, ...)."*
- **修复**：找 `process.env` 里 **PATH 的所有大小写变体**（`Path`/`PATH`…）→ 全删 → 只设一个规范化的 `env.PATH`。并把 `childEnv` 抽出到 `desktop/src/runtime.cjs` 以便单测。
- **给新手的教训**：**Windows 上是 `Path` 不是 `PATH`**；`{...process.env}` 会把这个大小写差异固化，之后写 `env.PATH` 等于**丢掉系统 PATH**。

#### 坑 W2　Windows 上只发 `.cmd` shim，`spawn` 不带 shell → ENOENT / EINVAL

- 来源：`dsh-market_dsh-market` `18abcd3`
- 提交信息原文（逐字）：
  ```
  fix: spawn pnpm/corepack/npm via a shell on Windows (#4)

  Windows only ships .cmd shims for these commands. Node spawn without a
  shell fails with ENOENT (bare name) or EINVAL (.cmd), so probePnpm and
  setup-pnpm always fail and the market UI stays blocked.

  Match dsh's plugin forwarder: shell: process.platform === "win32".
  ```
- 相关：`dsh-web` `404f0c4a` `fix(desktop): run pnpm install through a shell on windows`；`dsh-market_dsh-market` `237e8f5` `fix(cli): avoid Node DEP0190 shell+argv spawn on Windows (#80)`
- **给新手的教训**：**在 Windows 上 spawn `pnpm`/`npm`/`corepack` 要 `{ shell: true }`**（或直接找 `.cmd` 全路径）。

#### 坑 W3　CRLF 让注释剥离正则失效 → Windows 上写的 `cordis.patch.yml` 在**任何平台**都无法热挂载

- 来源：`dsh-market_dsh-market` `01b3c28`
- 提交信息原文（逐字）：
  ```
  fix: a Windows-authored bundle patch can be hot-mounted

  Running layer 3 on Windows turned up a real product bug, not a CI one: with
  CRLF line endings, parseSimplePatch refused a patch that is a plain insert
  list, so the market told the user to restart for a plugin it could have
  mounted immediately.

  The mechanism is a nasty little JS detail. Comments are stripped with
  `raw.replace(/#.*$/, '')`, and `\r` is a LINE TERMINATOR in JavaScript: `.`
  will not cross it, and `$` without /m anchors only at the very end of the
  string. So on `# comment\r` the pattern never matches, the comment survives,
  matches none of the row shapes, and hits the parser's `return null` — which
  the caller reports as "the bundle patch contains config/expression rows".

  The user-visible effect: any plugin whose cordis.patch.yml was authored on
  Windows could never hot-mount, on ANY platform, and always demanded a
  restart. Both parsers now split on /\r?\n/.
  ```
- **给新手的教训**：解析文本一定要 `split(/\r?\n/)`；**JS 里 `\r` 是行终止符**，`$`（无 `/m`）只匹配字符串末尾，`#.*$` 对 `# comment\r` 永不匹配。

#### 坑 W4　`import.meta.url` 与 `process.argv[1]` 的直接入口判断在 Windows 永远为 false（CLI 静默退出 0）

- 来源：`dsh-web`　`.agents/notes/implemented/bug-fix/2026-08-27-doctor-windows-supervisor-lifecycle.md`
- **现象**（笔记逐字）：*"src/cli.ts compared `import.meta.url === new URL(process.argv[1] ?? '', 'file:').href`. On Windows, drive letters in `process.argv[1]` (e.g. `C:\...`) produced malformed file URLs when constructed with `new URL(..., 'file:')`, causing the equality check to always evaluate to false. CLI commands exited silently with code 0 without executing main()."*
- 同笔记另两条 Windows 坑：
  - *"`service.ts` mistakenly imported path helpers from `node:path/posix`, corrupting Windows absolute paths."*
  - *"`runCommand` passed `{ shell: true }` on Windows, causing cmd.exe to break paths containing spaces (e.g. `DSH Doctor`) into multiple arguments and failing `schtasks /Create`"* —— **与坑 W2 相反**：这里 `shell: true` 反而害事（该传精确 argv 给 `schtasks.exe`）。
- **修复**：入口判断改为 `fileURLToPath(import.meta.url)` + `resolve(entryArg)`，Windows 下大小写不敏感归一；按目标平台选 `win32` 或 `posix` path 模块；`/TR` 目标路径加引号；去掉 `shell: true`。
- **给新手的教训**：**「要不要 shell」取决于具体可执行文件**——`.cmd` shim 要 shell，`.exe` 精确参数不要 shell；路径比较用 `fileURLToPath` + `resolve`，别手拼 `file:` URL。

#### 坑 W5　Windows 盘符路径解码多/少前导斜杠被拒

- 来源：`omdsh-dev_DSH-better-sidebar` `6b4fed1`
  `fix(html): Windows 盘符路径解码去掉前导斜杠，修复 html 预览被 isWithin 拒绝`
- 相关：`omdsh-dev_DSH-better-sidebar` `180b16d` `fix: 修复 WSL 会话 Linux 路径解析 (#399)`；`81ab0c5` `fix: cross-platform path handling and tests`；`db189e3` `feat: 统一路径处理——UNC/软链接分类/html 路由平台守卫`
- **给新手的教训**：路径要**统一入口归一化**（UNC、盘符、大小写、正/反斜杠、软链接），不要在几十处各写一遍解析。

#### 坑 W6　Windows 更新/解压/子进程/安装脚本杂项

- 来源（提交信息原文）：
  - `dsh-web` `36de9e36` `fix(desktop): extract runtime archives with windows-safe bsdtar`
  - `dsh-web` `00251900`：`fix(desktop): stage the windows cloudflared binary and self-heal wrong-arch ones` —— 原文要点：*"The payload's cloudflared postinstall only fetches the build machine's platform binary, so Windows installers shipped a macOS arm64 cloudflared"*
  - `dsh-market_dsh-market` `9f0ac8c` `fix: hide Windows child process consoles (#536)`（无正文）
  - `dsh-market_dsh-market` `33a5153` `fix: explain a Windows locked-file rename instead of showing pnpm's stack (#394)`
  - `dsh-market_dsh-market` `99ab687` `fix: honor Windows npm global prefix (#413)`
  - `omdsh-dev_DSH-better-sidebar` `9642e95` `fix: install.ps1 兼容 PowerShell 5.1（node -e 改临时文件，补 UTF-8 BOM）`
  - `omdsh-dev_DSH-better-sidebar` `d94465c` `fix: install.sh 变量加花括号（$WS_YML：→ ${WS_YML}），修复 macOS bash 3.2 下 unbound variable（#23）`
  - `omdsh-dev_DSH-better-sidebar` `71c5413` `fix(git): hide spawned git windows on Windows (#301)`
  - `omdsh-dev_DSH-better-sidebar` `7499383` `fix(terminal): resolve Windows custom shell executables (#487)`
  - `omdsh-dev_DSH-better-sidebar` `ac02598` `fix: preserve Windows explorer reveal selection`
  - `omdsh-dev_DSH-better-sidebar` `ddd3bed` `merge #47: fix PowerShell installer BOM parse and pnpm version check`
  - `omdsh-dev_DSH-better-sidebar` `24db20a` `test: make five suites Windows-runner clean`
- **给新手的教训**：Windows 相关坑**必须真机跑 CI**。市场那条说得很直白（`01b3c28`）：*"the whole suite was green on Linux and macOS throughout, and it would have kept hiding there."*

---

## 一-I 组：其它高频坑（跨主题，dsh-web 为主）

#### 坑 X1　z-index 层级：宿主的 shell.overlay 是 absolute inset:0 / z-index 20，插件面板默认被压在下面

- **来源**：zhu1090093659_dsh-web 08ea9de3 fix(aionui-panel): lift panel columns above shell.overlay layer (#195)；a36f60f6 fix(task-board): raise board container and modal z-index above panel overlays (#54)；40e15c77 fix(dsh-aionui-panel): keep panel frame chrome below the shell overlay layer (#234) (#259)
- **现象**：插件面板/看板/弹窗被宿主的 overlay 图层盖住，点不到、看不清；右下角区域尤其容易被盖。
- **根因**（提交原文）："The core AppFrame renders the shell.overlay slot as an absolute inset:0 layer at z-index 20 over the whole frame grid. With the aionui panel tracks appended as grid columns (4/5), right-edge overlay plugins painted on top of the Explorer / Preview content."
- **修复**：给插件自己的列/容器显式 z-index: 30 —— "above the overlay, below dialogs 1000+"，并沿用既有的 "tab-bar z-index 30 convention"；同时外壳 chrome 要低于 overlay（40e15c77），所以是分层而非一味抬高。
- **给新手的教训**：DSH 宿主自有一套 z-index 常量（shell.overlay = 20，对话框 = 1000+）。插件不要用 9999 一把梭，先在自己的层（20~30）里解决；抬得比对话框还高会盖住系统的确认框。

#### 坑 X2　不要把 React 拥有的 DOM 节点「搬家」——insertBefore / removeChild 锚点会失效

- **来源**：zhu1090093659_dsh-web baa711b4 perf(remote-web-ui): stop re-parenting the header actions and cut per-tick layout reads
- **现象**：把宿主已有的 React 节点搬到自己的容器里，界面上"看着没坏"，但后续 React 更新报错/错位；节点里的实时按钮（如后台任务徽标）变成点了没反应的死按钮。
- **根因**（提交原文）："The seated header actions were moved into the tabs row, which makes React's later insertBefore/removeChild anchors point at a node that is no longer a child of its recorded parent, and the background-task badge inside the node is a live React button a clone could not keep."
- **修复**：节点留在 React 原来的位置，改用「注入 CSS 把它移出文档流 + 用一个收敛的 transform 画到目标位置」，目标位置用 padding-right 预留被画上去的宽度。（同一提交还修了两个相邻坑：600ms 定时器每 tick 强制同步布局读取；以及靠匹配官方按钮文案来"下钻"选择器，在别的语言下永远不触发，改为结构化回退。）
- **给新手的教训**：宿主渲染出来的 DOM 属于 React。你可以改它的 class/样式，**不要改它的父子关系**。要"搬"就用视觉手段（CSS transform / position），不要用 DOM 手段。官方节点里的按钮可能是活的 React 组件，clone 出来的只是空壳。

#### 坑 X3　浏览器自动翻译会替换 React 底下的 text node，React 抛 NotFoundError，整段 UI 卸载变空白

- **来源**：dsh-market_dsh-market 43d5768 fix: a translated page can no longer blank the market (#293) (#513)；7133ed3 release 1.43.0: the blank market, and four failures that described themselves wrong
- **现象**：用户开了 Chrome/Edge 的整页翻译之后，市场面板**整块变空白**——连「导出日志」按钮都一起消失，所以从那个状态导出的日志永远是空的，导致这个 bug 在 #286 / #241 / #293 上挂了几个月、始终无法在身边复现。
- **根因**（提交原文）："Chrome and Edge translate by replacing text nodes underneath React; React then tries to remove a node its parent no longer has, throws NotFoundError, and the whole section unmounts."
- **修复**（逐条照抄要点）：
  1. 在市场根节点**以及 portal 宿主**上加 `translate="no"` 与 `notranslate`。**portal 宿主也必须加**，因为对话框和 lightbox 从那里渲染——"a translated dialog crashes React exactly the same way"。
  2. 只对自己子树生效："Scoped to this subtree: the host page around it still translates."
  3. 导出的日志里读 html 元素上 Chrome/Edge 留下的标记，写明"本页是否被浏览器翻译过"——"A fact, not a verdict — a translated page is not by itself a fault"，但这正是用户永远不会主动提供的线索。
- **代价**（作者自己写明）："The cost is that machine translation stops inside the market. That is a fair trade against a panel that cannot render at all, and the market ships its own 中文 and English rather than relying on the browser."
- **给新手的教训**：**任何挂在 React 树里的 DSH 插件，根节点都该加 `translate="no"` 与 `notranslate`**。这不是可选优化，是防止整块 UI 崩掉；凡有 portal 的（弹窗、右键菜单、浮层），portal 容器也要加。

#### 坑 X4　dsh.bundle.patch 型插件被当成普通插件写进 insert 行，loader 导入不存在的模块，dsh web 起不来

- **来源**：zhu1090093659_dsh-web d05bf033 fix(web-ui-all): expand external plugin bundles and restore better-session 0.0.11；63a8d3a7 fix(skins): drop dsh.bundle.patch from home-inserted skins (#381)；1e816872 feat(plugin-manager): strip duplicate-mount bundles entries after CLI mutations
- **现象**：`dsh web` 直接 boot 失败（宿主启动即崩，不是界面坏掉）。
- **根因**（提交原文）："@morlay/better-session ships as a profile bundle (dsh.bundle.patch), so writing its package name into an insert row made the loader import a module that does not exist and dsh web failed to boot."
- **修复**：聚合生成器 parsePatchBlocks **展开 bundle 行**——"accepts name-less harness patch rows (preserving extra lines such as disabled flags), insert ids stay namespaced, later bundle patches override earlier same-id rows, and external children are resolved from the aggregate package"；link-profile.mjs 把 bundle 子包也 link 到 profile 根，让 profile-root import 能解析。
- **反向坑**（63a8d3a7）：反过来，"Declaring dsh.bundle.patch lets reconcile put them back on dsh.profile.bundles and recreate duplicate loader entries."——一个已经被宿主层面插入的皮肤（`bundleWired: false`，由 dsh-skin 在 home 层插入），**不该**再声明 `dsh.bundle.patch`，否则 reconcile 会把它放回 `dsh.profile.bundles`、重建重复的 loader entries。
- **给新手的教训**：一个包**要么**是 `dsh.bundle.patch` 型（自己带 patch 文件、由 `bundles` 拉起），**要么**是被别人 `insert:` 的普通插件，不要两头都占。动完配置先 `dsh dump-config` 看**真实的 loader entries**，别只看自己的 package.json。

#### 坑 X5　异步 apply 里抛错，unhandled rejection 被宿主 installFailLoud 抓住，整个 dsh web 进程死掉

- **来源**：zhu1090093659_dsh-web ed3be967 fix(dsh-web-all): config-less self row mounts as a no-op; shell never throws；对照 8d4441ca fix(web-all): make degraded route a ref-counted singleton across shell entries (#1363)；4b25dd77 feat(aggregate): isolate per-plugin boot failures behind the dsh-web-all shell
- **现象**：一个配置形状不对的行（SELF 行用**空 config** 挂载本包）让 shell 抛错；抛错发生在 **async apply** 里，rejection 逃出 loader 生命周期变成 unhandled rejection，宿主 installFailLoud 直接把整个 `dsh web` 干掉——"the exact failure the shell exists to prevent"。
- **根因 + 修复要点**（逐条照抄）：
  - "a config-less row (self shape: `undefined` or `{}`) mounts as the original no-op compat behavior"
  - "a row WITH config but no plugin name no longer throws either: it records a degraded entry and returns."
  - "Loudness lives in the log and the degraded ledger, never in process death."
- **背景**（4b25dd77 原文）：宿主 loader 把整组行当成**一个事务组**（EntryGroup.update）——"any entry that fails to import or start rolls the whole group back, and the boot audit (assertEntriesActivated in @deepseek-ai/dsh-app-boot) then aborts the entire dsh web process." 所以家族把每条行包进 fault-isolation shell，一条坏插件只降级它自己，并提供 `GET /api/dsh-web-all/degraded` 路由报告降级台账。
- **给新手的教训**：DSH 宿主有 installFailLoud——**任何未处理的 promise rejection 都会终止整个 host 进程**。插件 apply() 里凡是异步的都要 try/catch；捕获后记日志 + 降级，绝不让 rejection 逃出去。测试要覆盖"启动失败"和"导入失败"两条路径（先例：`packages/dsh-web-all/tests/shell-isolation.spec.ts`）。

---

## 1.2　omdsh-dev_DSH-better-sidebar 分仓坑点汇总（第三方侧栏底座）

**仓库事实**：644 commits / 12 tags；根目录共 383 个文件。**0 个 blob 可用**（只读得到目录树 + 提交信息）。
技术栈：`package.json` / `pnpm-workspace.yaml` / `cordis.patch.yml` / `dsh.plugin.json`（根目录另有一份插件清单）/ `Makefile` / `eslint.config.js` / `playwright.config.ts`。
源码分区与 dsh-web 同一套约定：`src/`（host：agent-pty、bundle-route、browser-probe…）+ `src/client/`（browser：BrowserView.tsx、DiffTab.tsx、EditorHost.tsx…）。
最有价值的可读线索：`docs/plans/*.md`（50+ 篇设计文档，如 `2026-08-19-sidebar-injection-unified-host-design.md`、`2026-08-12-lazy-chunks-design.md`、`2026-08-14-terminal-font-design.md`、`2026-09-08-terminal-shell-config-hardening-design.md`）与 `docs/external-plugin-guide.md`（第三方注册新页面的官方指南）、`AGENTS.md`。
注意：这些 md 的 **blob 同样不可用**，只能从文件名与提交信息推断主题；正文无法逐字引用。

#### 坑 SB1　终端自定义字体栈不以通用族收尾，浏览器落到比例字体，整张网格崩掉

- **来源**：omdsh-dev_DSH-better-sidebar 0504e39 fix(terminal): 自定义字体解析失败时兜底到等宽，避免掉进比例字体毁掉网格
- **现象**（提交原文，含实测表）：macOS + Chrome 填 `Maple Mono NF CN` → DevTools Rendered Fonts 显示 **PingFang SC**，cell 12.09px @ 13px 字号（0.93em，等宽字体应为 0.6em），字符间距被撑开、字形变比例、Nerd Font 图标全消失。改成 `Maple Mono NF CN, monospace` → Rendered Fonts 变成 **Menlo**，恢复正常。
- **根因**：“字体栈若不以通用族收尾，浏览器解析不到任何具名字体时会落到**标准字体**（macOS 中文环境是 PingFang SC）——它是**比例字体**。xterm 用它的推进宽度量 cell，网格随即失真。” 并且“终端里跑的 shell 在 host 上，字体却由**浏览器所在机器**提供，两者不同机时（远程/容器化的 DSH）用户按 host 侧装的字体填名字必然解析失败。”
- **修复**：新增 `withMonospaceFallback()`，在 `resolveTerminalFont` 出口保证字体栈以通用族收尾；主题 token `--ds-font-family-code` 的值同样兜底。**不做字体嗅探**（设计文档把"字体合法性嗅探"列为非目标）；用户已写通用族则原样保留。
- **给新手的教训**：任何自定义字体栈都要以通用族（`monospace` / `sans-serif`）收尾，否则远端机器上一定落到比例字体。终端的字体来自**用户浏览器**，不是 host。

#### 坑 SB2　收起的面板用 transform 滑出屏幕，仍计入祖先滚动溢出区，整页可双向拖拽

- **来源**：omdsh-dev_DSH-better-sidebar ffcd695 fix(layout): 面板宿主裁剪视口边缘，收起的面板不再撑出文档双向滚动 (#277)
- **现象**：面板收起后整个页面可以左右/上下拖动。
- **根因**：“收起的面板以 `transform: translate(102%)` 滑出屏幕，但 transform 后的元素仍计入祖先滚动溢出区。”
- **修复**：面板宿主 `[data-dsh-panel-host]` 是视口尺寸的 `fixed` 容器，补上 `overflow: hidden`，裁剪点恰在视口边缘；开合滑入动画、内部滚动容器与 fixed 弹层均不受影响。e2e 增加回归断言：面板收起时文档 scrollWidth/Height 不得超出视口。
- **给新手的教训**：`transform` 移出可视区**不等于**移出溢出区。侧栏/抽屉类插件要在宿主容器上 `overflow: hidden`，并写一条"文档不产生滚动条"的 e2e 断言。

#### 坑 SB3　宿主 markdown 原语泄漏进文件预览：sticky 代码块 banner 钉在视口顶，TOC 浮层被压在它下面

- **来源**：omdsh-dev_DSH-better-sidebar a2a2690 fix(markdown): preview TOC dismiss-on-outside-click, popover z-index, code-block banner stickiness
- **现象**：预览里每个代码块的头像"浮动标题"一样钉在视口顶部，直到整块滚过去；TOC 目录面板被代码块 header 盖住；TOC 只能再点一次开关才关。
- **根因**：“DSH 的 `bannerWrap` 是 `position:sticky`（`top:0`，`z-index:6`）以便每条消息的代码块保留复制按钮。预览里每个 fence 共用同一个 `.editorMd` 滚动容器，banner 因此钉到视口顶。” 而 “`.tocBar` 是 `z-index:3`，低于代码 banner 的 6，所以目录面板画在 sticky fence header 下面。”
- **修复**：对预览里非 mermaid 的 fence 中和 stickiness（mermaid chrome 会替换 banner，用 `data-mermaid-processed` 排除）；TOC bar 抬到 `z-index:7`；给 TOC 加 `document` 级 `pointerdown` 监听做 outside-click 关闭（豁免按钮与面板本身）。
- **给新手的教训**：**宿主的组件按上下文做了 `position: sticky` / z-index，搬到别的滚动容器里语义就变了**。复用官方 markdown 原语时，要么中和它的定位，要么显式重排层级。

#### 坑 SB4　portal 出去的 fixed 弹窗，在它依附的编辑面离开视口后仍然存在

- **来源**：omdsh-dev_DSH-better-sidebar d258f3f fix(editor): dismiss the selection popup when its surface leaves the viewport (#425)
- **现象**：触发选区弹出层的编辑面已经不可见了，弹层还钉在屏幕上。
- **根因**：“侧栏让每个 tab 常驻挂载（切 tab 只设 `display:none`；收起面板是把整体 translate 出屏），所以 portal 的 `position:fixed` 按钮会活得比它的编辑面更久。”
- **修复**：抽出 `useSelectionPopup`，在按钮外任何 `mousedown`、Escape、`document` hidden、`window` blur，以及——关键——**用 `IntersectionObserver` 报告编辑面离开视口**时关闭。
- **给新手的教训**：portal 的浮层脱离了父级的显示状态。父面用 `display:none` / `transform` 隐藏时，浮层不会自动消失，必须显式监听（IntersectionObserver / visibilitychange / blur）。
- **来源**：omdsh-dev_DSH-better-sidebar c7d58c9 把 19 个非中英词典移进懒加载 chunk
- **现象**：核心 client bundle 体积过大（1.46MB）。
- **根因**（中文转述）：核心 client bundle 静态 import 了每一个第三语言词典（约 640KB 源码，差不多是 bundle 的一半），而大多数会话根本不会走这条路径：侧栏自己的翻译函数只查中英文加 better-locale override store，词典的唯一消费者是那个 store 的注册调用。
- **修复**：把词典挪进既有的 lazy-chunk 机制（单独打成一个懒加载 js，只在真的装了 better-locale 时按需取；用一个 generation counter 让异步注册在 effect 重跑或中途 dispose 时变得无关紧要）。chunk 落地前翻译函数继续走中英文链；store 在注册时 bump 自身 revision，词典到达后重渲染 chrome。**core client.js：1.46MB 降到 822KB，减少 44%**。词典 chunk 边界的 key-set 检查移到既有运行时测试（每个已发布词典必须与中文 key-set 相等）。
- **给新手的教训**：客户端 bundle 会被整包推给浏览器，**静态 import 就是全量下载**。翻译词典、图标集、大 JSON 一律走 lazy chunk；异步注册要配一个 generation counter 处理"还没到就卸载"。

#### 坑 SB6　桌面壳兼容硬编码在核心里会互相打架；正确做法是把壳适配下沉到用户空间

- **来源**：omdsh-dev_DSH-better-sidebar 50a8888 侧边栏桌面兼容三方案：自动检测（WCO 标准几何）、壳预设、自定义 CSS
- **现象**：为某个桌面壳（Electron 套壳）加的标题栏 offset，在另一个壳上就坏。
- **根因 + 决策**（提交原文，中文部分逐字）：提交原文写的是「核心只保留 Web 标准机制，壳专属适配全部下沉到用户空间（KISS）」，以及「核心 grep 无壳专属类名；为某壳做的兼容在另一壳会再坏——预设与自定义 CSS 是唯一出路（AGENTS.md §8 契约已更新）」。
- **修复**：`prefs` 新增 `titleBarScheme`（auto、preset、custom 三态，旧布尔 `titleBarCompat` 自动迁移）；`wco.ts` 用 `navigator.windowControlsOverlay` 做反应式几何（`geometrychange` 实时更新；`visible=false` 的幽灵 API 视为缺失）；`titlebar-strip.ts` 收敛出唯一 strip 取值链：WCO → `dsh-desktop-titlebar-inset` 契约参数 → 预设 → 手动 px → 0；移除 `desktop-env.ts` 里 win32 32px 硬编码；预设与自定义 CSS 通过 `data-dsh-preset-css`、`data-dsh-custom-css` 标签注入，并补稳定寻址面 `data-dsh-toggle-cluster`、`data-dsh-panel`；交互 chrome 统一 `-webkit-app-region: no-drag`。
- **给新手的教训**：**不要往核心里写"某壳"的类名或像素**。优先用 Web 标准 API（`navigator.windowControlsOverlay`）自动检测；检测不到就做成数据驱动的预设加用户可写 CSS，不要硬编码。

#### 坑 SB7　安装脚本的跨平台与内嵌 Node 版本细节

- **来源**：omdsh-dev_DSH-better-sidebar 9642e95 修 install.ps1 兼容 PowerShell 5.1（node -e 改临时文件，补 UTF-8 BOM）；d94465c 修 install.sh 变量加花括号，修复 macOS bash 3.2 下 unbound variable（#23）；ddd3bed 合并 #47 修 PowerShell 安装器 BOM 解析与 pnpm 版本检查
- **现象**：Windows 上安装脚本解析失败 / macOS 上安装脚本报 "unbound variable" / 中文输出乱码。
- **根因**：Windows PowerShell 5.1（`powershell.exe`，不是 `pwsh`）默认用非 UTF-8 读脚本；bash 3.2（macOS 自带）在 `set -u` 下对 `$VAR` 紧邻中文/标点时会做变量名扩展。
- **修复**：`.ps1` 补 UTF-8 BOM；避免 `node -e` 内联长脚本、改写成临时文件；`.sh` 里所有变量引用统一加花括号 `${VAR}`。
- **给新手的教训**：Windows 侧脚本要当 PowerShell 5.1（不是 7）来写，并保存成 **UTF-8 with BOM**；shell 脚本里变量一律写 `${VAR}`，别写 `$VAR` 后面紧跟其他字符。

#### 坑 SB8　"隐形齿轮"式的二级设置入口：可发现性不足，且容易踩到无边框按钮的可见性契约

- **来源**：omdsh-dev_DSH-better-sidebar 0fdf63b 侧边卡片设置页 UI/UX 现代化——卡片底部设置条替代隐形齿轮，协调双色启用态（#300）
- **现象**：插件设置卡片右下角 16px 的幽灵齿轮，用户找不到入口，以为这个插件没有设置页。
- **根因**：入口只有图标、没有文字标签、位置在角落，常态下几乎不可见。
- **修复**：把齿轮改成**卡片底缘全宽设置条**（hairline 分隔 + 齿轮图标 + 「功能设置」文字标签），常态可发现，hover 用品牌淡底加 brand 字色引导；**可见性条件与 `aria-label` 契约保持不变**（仅父级启用且声明 settings 时才出现）；动效纪律：全部过渡 ≤160ms 且只动颜色属性、`prefers-reduced-motion` 全覆盖。
- **给新手的教训**：给插件做设置页，**入口要有文字标签、要能被一眼看到**。改视觉时不要动 `aria-label` 和可见性条件——那是无障碍与逻辑契约。

---

## 1.3　dsh-market_dsh-market 分仓坑点汇总（设置页内的可视化插件市场）

**仓库事实**：491 commits / 12 tags；HEAD 树 213 个文件；**0 个 blob 可用**。
分层：`src/`（host：install.ts、patch.ts、hot.ts、profile.ts、restart.ts、routes.ts、settings.ts、pnpm-compat.ts、update-api-v1.ts…）+ `src/client/`（browser：MarketSection.tsx、SettingsCard.tsx、OperationsPanel.tsx、ErrorBoundary.tsx、Diagnostics.tsx、comments.ts、market-data.ts…）+ 预构建的 `client/client.js`（提交进仓库的 browser bundle）+ `cordis.patch.yml`。
测试结构值得新手照抄：`tests/` 平铺宿主单测 + `tests/client/*.client.spec.tsx`（浏览器半测）+ `tests/web/*.e2e.ts`（Playwright）+ **`tests/web/fixtures/fixture-a|b|carrier|clash|cross/`（每个都是含 `package.json` + `cordis.patch.yml` + `index.js` 的最小插件样例）** + `vitest.compat.config.ts`（真 pnpm 兼容车道）。
另注：根目录是 `package-lock.json`（npm），不是 pnpm lock —— 第三方独立插件不必强求 pnpm。

#### 坑 MK1　一个已删除的本地 .tgz 依赖会阻塞该 profile 的所有安装与卸载，而报错只给路径不给包名

- **来源**：dsh-market_dsh-market 7133ed3 release 1.43.0（#436，by @screamff）
- **现象**：一份"插件页面全坏"的报告；但实际是**安装/卸载全部失败**。
- **根因**（提交原文）："A plugin installed from a .tgz that has since been deleted blocks EVERY install and uninstall in the profile, because pnpm re-resolves all direct dependencies before any change." 用户看到的是 pnpm 原始的 ENOENT，**只给路径、不给包名**，读起来跟用户想做的事毫无关系。
- **修复**：抓出死掉的本地依赖并**点名那个包**；对照真实 pnpm 10 与 11 量化，并在 compat 车道里钉住。
- **给新手的教训**：报错信息要**点名用户能识别的对象**（插件名），不要透传包管理器的原始错误（只说路径）。另外：profile 里的**任何一条**直接依赖坏掉，都会让整条依赖操作失败——排查"我怎么装都装不上"时，先怀疑 profile 里已有的坏依赖。

#### 坑 MK2　原生 .node 插件无法 dlclose，卸载后报 "hot（刷新即可）" 是错的；Windows 上还会报 EPERM

- **来源**：dsh-market_dsh-market 7133ed3 release 1.43.0（#441，by @yandidan1）
- **现象**：卸载一个带 native addon 的插件后提示"刷新一下就够"，但刷新后仍然失败；Windows 上后续安装报 EPERM，且文案是写给**更新**场景的，让用户去禁用一个已经删掉的插件。
- **根因**（提交原文）："Node has no dlclose: once a `.node` is loaded the process holds it until it exits, so unmounting or even uninstalling the plugin does not free the file, and on Windows the next install fails renaming over it."
- **修复**：卸载对这类插件**明确说明**需要重启进程；EPERM 文案按场景区分安装/更新/卸载。
- **给新手的教训**：装了原生模块（`.node`）的插件，**热卸载是不成立的**，必须整进程重启。别把"刷新页面"当成万能解法。

#### 坑 MK3　pnpm 起不来时，用户看到的是 Node 的原始错误对象和一段 argv dump

- **来源**：dsh-market_dsh-market 7133ed3 release 1.43.0（#509 by @awslmowms；#502 by @Ztyss）
- **现象**：Ubuntu 上 spawn 直接被拒，界面显示 Node 的原始 error 对象 + argv dump；更新路径还谎称"回滚无法验证"——而 pnpm 根本没跑、什么都没写。
- **修复**：每种原因**配一条对应的修复指引**——EACCES、ENOENT，以及 Windows 的 exit 9009。
- **给新手的教训**：调用外部进程时，对**每个已知退出码/errno 写人话**，并且**没执行就别说"回滚失败"**。把 `err.code` 映射成用户能做的下一步动作。

#### 坑 MK4　「立即更新」看起来不像按钮——它用了宿主默认 variant，被塞在红色 12px 错误 banner 里

- **来源**：dsh-market_dsh-market 7133ed3 release 1.43.0（#410，由用户 @Dave-12138 在自己的截图里发现）
- **现象**：按钮一直都在，但用户找不到。
- **根因**："It was there the whole time, taking the host default variant inside a red 12px error banner."
- **修复**：给主操作显式使用主按钮三件套 token，让它在错误语境里仍是明确的按钮。
- **给新手的教训**：**不要把关键操作按钮放在错误 banner 里还依赖默认样式**。主按钮必须显式用 `--dsw-alias-button-primary-fill` 三件套（详见 §三）。

#### 坑 MK5　代理到不了 pnpm：catalog 能加载，安装却全部卡死

- **来源**：dsh-market_dsh-market 2c5a32b fix: a proxy reaches pnpm, a CRLF workspace file stays valid, and a long tag stops wrapping the row（#148 #161 #188 #232）
- **现象**：在有代理的网络里，市场自己的 catalog 拉得好好的，但每一次安装都卡住。
- **根因**（提交原文）："The market's own catalog fetches have gone through undici's EnvHttpProxyAgent since 1.14.0 … pnpm reads none of HTTPS_PROXY/http_proxy; it reads npm config, so a proxy reaches it only as npm_config_https_proxy / npm_config_proxy."
- **修复**：`spawnEnv()` 做翻译，**镜像 undici 自己的优先级**（小写覆盖大写，https 回退到 http）；`NO_PROXY` 也要转发；调用方已设置的 `npm_config_*` 永远优先，且**大小写不敏感**（因为 Windows 环境变量键就是大小写不敏感的）。
- **给新手的教训**：插件自己做 HTTP 和插件调用 pnpm，走的是**两套不同的代理配置**。给子进程传代理时，要同时写 `npm_config_https_proxy` / `npm_config_proxy`，并保留大小写两种拼写。

#### 坑 MK6　CRLF 的 pnpm-workspace.yaml 让 allowBuilds 块匹配失败、追加出第二个块 → 非法 YAML → 该 profile 所有安装失败

- **来源**：dsh-market_dsh-market 2c5a32b（#231 by @MichengAI）
- **现象**：Windows 上（或任何 `core.autocrlf=true` 的检出）该 profile 里**每一次**安装都失败。
- **根因**（提交原文）："The allowBuilds block pattern required a `\n` immediately after the key. A CRLF file … has `\r` there, so an EXISTING block was never found and a second one got appended. Two top-level allowBuilds keys is invalid YAML."
- **修复**：正则容忍 `\r`；**合并所有块**（而不是只处理第一个，这样可以修好已坏掉的文件，而不是静默撤销第二个块里的审批）；重写时保持文件自己的换行符，不留下混合换行。
- **给新手的教训**：**插件写用户的 YAML/JSON 配置时，正则必须容忍 `\r`**。改完要保持原文件换行风格；块匹配要用"合并"语义，不要用"找不到就再追加一个"。

#### 坑 MK7　行内唯一的可变长文案用了 nowrap + flex-shrink:0，把整个操作行挤下去

- **来源**：dsh-market_dsh-market 2c5a32b（#234 by @Ztyss）
- **现象**：`.metaTag`（本地开发 link）把 Uninstall 按钮挤到了单独一行。
- **根因**："`.metaTag` holds the row's only variable-length copy and was nowrap with flex-shrink:0, so the longest of them wrapped the whole action row."
- **修复**：文案这半边允许收缩/换行，按钮那半边保持可操作。
- **给新手的教训**：flex 行里**唯一可变长的那一段**不要用 `flex-shrink: 0` + `nowrap`，否则最长的数据会把按钮挤出去。可变长的给 `flex: 1; min-width: 0`，按钮给 `flex: none`。

#### 坑 MK8　插件自己的自动折叠，与 Chrome 的 scroll anchoring 互搏成无限抖动

- **来源**：dsh-market_dsh-market a56c5e9 fix: the category row stops fighting the scroll it triggered（#395 #403）；d590242 release 1.36.0
- **现象**：分类列表展开时滚动插件列表，画面**持续闪烁**。
- **根因**（提交原文）："Scroll anchoring picks a node below the viewport and rewrites scrollTop whenever content ABOVE it changes height, which is exactly what collapsing ~120px of category row does. So the browser undid the scroll that had caused the collapse, that put the viewport back above the sentinel, the row re-expanded, and the next scroll event started it again." 实测：*"one synthetic 8px/frame scroll drove scrollTop 8 → 134 → 24 inside 30ms while the row flipped 146px ↔ 26px; parking at scrollTop 20 with no further input was yanked straight back to 0."*
- **修复**：滚动容器上 `overflow-anchor: none`（*"With overflow-anchor:none … the same gesture collapses once and scrollTop stays where it was put."*）。放弃锚定在本列表没有代价——*"Every image it renders is sized in CSS (`.shot`, `.cardShot`, `.av`), so nothing above the viewport resizes on load."*
- **给新手的教训**：**当滚动本身会改变视口上方内容高度时，一定要关掉 `overflow-anchor`**，否则浏览器会"帮你"把滚动位置改回去，和你自己的逻辑打架成死循环。关闭的前提是：列表里没有"先占位后撑高"的图片。

#### 坑 MK9　每张卡片每次渲染都全量重扫 catalog：`O(cards × installed × catalog)`，占掉整个录制 28.4% 的 CPU

- **来源**：dsh-market_dsh-market 6ddc691 perf: stop rescanning the whole catalog once per card, per render（#262 #264）；b9323cc release 1.18.0
- **现象**："插件页面非常卡"，附了 Chrome trace。
- **根因**（提交原文）："`looseMatchCount` answers 'how many catalog entries could this installed dependency be?', which depends only on the catalog and the dependency name. It has nothing to do with the card being drawn. But it sat inside `matchInstalledName`, which runs once per installed dependency, which runs once per rendered card — so every render cost `cards × installed × catalog` with a full scan of ~1800 entries each time, allocating a fresh identity Set per entry along the way." CPU profile：*"looseMatches, 2918ms self time, 28.4% of the entire recording — the largest non-idle entry by a wide margin."*
- **修复**：按 **catalog 数组的 identity** 做 memo（重新拉取 catalog 自然拿到新 map，旧的变成可回收）；`entryIdentities` 按 entry 对象 memo（catalog entry 解析一次、之后不再 mutate）；`depIdentities` 移出扫描循环（原本每次调用重建约 1800 次）。实测：*"24 cards: 48.1ms → 1.8ms; 96 cards: 223.6ms → 0.8ms per render."*（线上 catalog 1800+，大约是实测的两倍。）
- **给新手的教训**：**渲染函数里任何"只跟数据有关、跟这一行无关"的计算，都要 memo**。看到三层嵌套循环 `cards × installed × catalog` 就是它在报警。用数组 identity 当 memo key。

#### 坑 MK10　把 `settingsScope` 写进模块级 `inject` 会让整个插件在旧宿主上不挂载

- **来源**：dsh-market_dsh-market 53ea53d feat: allowRestart is a switch on the settings page, not a YAML edit
- **背景**：市场要在 dsh 0.1.0-rc.7 开放的"插件配置页"上放一张设置卡（host 半在 `src/settings.ts` 注册命名空间，browser 半在 `src/client/SettingsCard.tsx` 出卡片）。
- **坑**（提交原文）："The browser side does need care, and takes it through a NESTED inject: naming `settingsScope` in the module-level `inject` would leave the whole plugin unmounted on rc.6 — trading the market's own page for a card that host cannot render. Nested, the card is simply absent there."
- **兼容性设计**（照抄）："Compatibility needs no version check on the Host side: `installSettingsSection` rides its own scoped fiber, so a dsh without a settings service never runs any of it and the composed entry stands."
- **另两条决策**：只暴露 `allowRestart`（`profile` 在挂载时决定、运行中换不了，提供了也是空承诺）；Desktop 分支根本不注册（那里由壳掌管进程生命周期，值被强制 false）。
- **给新手的教训**：**新 API 的依赖要放在"嵌套 inject"里，不要写进模块级 `inject`**。写进模块级意味着旧宿主上整个插件都不加载；嵌套注入则只是那张卡片不存在，插件本体照常工作。

#### 坑 MK11　插件不能通过通用卸载路径卸载自己：要独立路由、显式 confirm，且"热禁用"写下的行会活得更久

- **来源**：dsh-market_dsh-market b36f2ee feat: manage the market itself from its plugin-configuration card（#173）
- **要点**（提交原文逐条）：
  - 通用卸载路由**拒绝**卸载市场自己：*"a destructive action on the plugin serving the request should not be reachable as a stray `{ name: "dshmarket" }` on the ordinary path."* 需要单独的 `self-uninstall` 路由 + 显式 `confirm`，并走与重启相同的 loopback 门。
  - 已被 import 的模块**不会随文件消失**：*"an already-imported module does not vanish with its files, so the process keeps serving and the response completes; the profile boots clean afterwards. What DOES break is a refresh — the host 404s on the removed client bundle while the loader entry is still live … so the market disables its own entry after responding."*
  - "热禁用"写下的 `disabled: true` 行会**活过**这次操作：*"the market's hot-disable writes `disabled: true` rows into the profile's user patch layer, and those OUTLIVE …"* —— 所以设置页提供一个**默认关闭**的 cleanup 复选框来收拾它们。
- **给新手的教训**：插件**不要**给自己提供一条"普通路径就能触发"的自毁接口；要单独路由 + 显式确认。卸载/禁用后"刷新页面"必然 404（bundle 没了、loader entry 还在），要**在响应完成后先把自己的 entry 禁掉**。热禁用会在用户的 patch 层留下 `disabled: true` 行，考虑提供清理入口。

#### 坑 MK12　Windows 三连：CRLF 让热挂载失效、锁定文件改名被拒、重启给 PowerShell 一个 `.ps1` 被策略拒绝

- **来源**：dsh-market_dsh-market 01b3c28 fix: a Windows-authored bundle patch can be hot-mounted；33a5153 fix: explain a Windows locked-file rename instead of showing pnpm's stack（#394 #389）；d590242 release 1.36.0（#397 #398）
- **坑 12-a（CRLF + JS 的 `\r` 是行终止符）**（提交原文）：*"Comments are stripped with `raw.replace(/#.*$/, '')`, and `\r` is a LINE TERMINATOR in JavaScript: `.` will not cross it, and `$` without `/m` anchors only at the very end of the string. So on `# comment\r` the pattern never matches, the comment survives, matches none of the row shapes, and hits the parser's `return null` — which the caller reports as 'the bundle patch contains config/expression rows'."* 用户可见后果：*"any plugin whose `cordis.patch.yml` was authored on Windows could never hot-mount, on ANY platform, and always demanded a restart."* 修复：两个解析器都改成按 `/\r?\n/` 切分。**注意**：作者还写明 profile.ts 里"等价的那处改动是故意不覆盖的"，并**删掉了自己先写的那条测试**——因为那里的模式都是 `^` 锚定、注释行必以 `#` 开头，不剥离注释的结果完全相同；*"The test passed with and without the fix — it tested nothing."*
- **坑 12-b（Windows 锁定文件改名）**：pnpm 把新版本 stage 在同级 `<name>_tmp_<pid>_<n>` 目录再 rename 覆盖旧的，Windows 在目标下任何文件被打开时拒绝 rename。*"For an UPDATE the target is a plugin the running dsh has loaded — its own files are the ones held open. On POSIX this never comes up, because replacing an open file leaves the old inode alive for whoever still holds it."* 修复：报错点名插件、说明旧版本完好、给出两条出路（退出 harness 从命令行更新；或禁用插件→重启→更新），并点名杀毒软件/文件索引器。**故意不做自动重试**：*"the process that would retry is the one holding the handles, so a retry cannot win."*
- **坑 12-c（重启用 `dsh.ps1` 被 Restricted 执行策略拒）**：#397 报告 Windows 上点"立即重启"，宿主关掉后再也没回来。根因：*"The relaunch handed a bare `dsh` to a hidden PowerShell, PowerShell prefers `dsh.ps1`, and the default Restricted execution policy refuses it — after the old host has already exited. So the button did the destructive half of its job and not the other half, with no way back from inside the UI."* 修复：显式用 `dsh.cmd`（npm 同时安装、不受脚本策略管）。
- **给新手的教训**：Windows 上（1）一切按行切分都用 `/\r?\n/`，别用 `$`（JS 里 `\r` 是行终止符）；（2）文件被占用时的 rename 会失败，报错要说清"这个版本还在跑，先退出再更新"；（3）**重启/拉起子进程显式用 `.cmd`**，不要只给一个裸命令名让 PowerShell 去猜 `.ps1`。这些坑在 Linux/macOS 上 100% 不复现——*"the whole suite was green on Linux and macOS throughout, and it would have kept hiding there."*

---

# 二、插件骨架与可复用代码（含"能不能照抄"的诚实结论）

## 二.0　前置声明：源码 blob 不可用，因此**无法逐字照抄源码**

必须先把边界说清楚，否则这本手册会教错人。

三个仓库都是**部分克隆**（`--filter=blob:none --no-checkout`），本地只落了 commit/tree 对象，**blob（文件内容）在需要时才会 lazy fetch**。而当前环境没有网络，所以：

```text
$ git -C zhu1090093659_dsh-web show HEAD:packages/dsh-session-id/package.json
fatal: bad object HEAD:packages/dsh-session-id/package.json

$ GIT_NO_LAZY_FETCH=1 git -C zhu1090093659_dsh-web show HEAD:packages/dsh-session-id/src/index.ts
fatal: bad object HEAD:packages/dsh-session-id/src/index.ts
```

**实际 blob 计数**（`git cat-file --batch-check --batch-all-objects`）：

| 仓库 | commit | tag | tree | **可用 blob** | 说明 |
| --- | --- | --- | --- | --- | --- |
| zhu1090093659_dsh-web | 2444 | 15 | 19098 | **365** | 只有 `.agents/notes/**` 的笔记正文 + `packages/AGENTS.md` |
| omdsh-dev_DSH-better-sidebar | 644 | 12 | 2044 | **0** | 一个文件内容都读不到 |
| dsh-market_dsh-market | 491 | 12 | 1685 | **0** | 一个文件内容都读不到 |

**结论**：用户点名要"逐字照抄"的 `package.json` 全文、`src/index.ts`、客户端入口文件、`cordis.patch.yml`、调用 slots API 的代码、设置卡片代码、CSS——**在物理上拿不到**。本节不会伪造任何一行源码。

下面给出的是**确实读得到**的三类事实：

1. **权威契约文本**：`zhu1090093659_dsh-web` 的 `packages/AGENTS.md`（**逐字可读**，365 个可用 blob 之一）——它规定了包形态、分层、exports、样式、测试纪律。这是本节最有价值的部分。
2. **完整目录树**：`git ls-tree -r --name-only HEAD <路径>`（真实、完整），用来照抄"文件该放哪、叫什么名字"。
3. **确切的 API 名 / 字段名 / 报错字符串**：来自维护者笔记（`.agents/notes/**`，逐字可读）与提交信息。

凡用户要求"逐字照抄"而我拿不到的，一律写 **「未找到（blob 不可用）」**。

## 二.1　最小 UI 插件范本

### 二.1.1 判定方法（为什么不用 `wc -l`）

用户建议用 `find` + `wc -l` 找代码量最小的插件——但 blob 不可用，`wc -l` 无从下手。改用**文件数**做近似（`git ls-tree -r --name-only HEAD <包目录> | wc -l`），并在同等文件数下优先选"纯客户端 UI、无 host 逻辑"的包。

### 二.1.2 家族内文件数排行（越小越简单）

| 包 | 总文件数 | 其中 src 下 ts/tsx | 备注 |
| --- | --- | --- | --- |
| `packages/dsh-session-id` | **24** | 14 | **最小、最干净的纯客户端 UI 插件**，含 2 个测试 |
| `packages/dsh-model-capabilities` | 28 | 17 | 次小 |
| `packages/dsh-web-settings` | 34 | 25 | 含设置桥 |
| `packages/dsh-web-all` | 41 | 17 | 聚合载具，非普通插件 |
| `packages/dsh-usage` | 40 | 29 | |
| `packages/dsh-skill-explorer` | 48 | 36 | |
| `packages/dsh-session-archive` | 51 | 39 | 唯一把 "settings token 契约" 做进 UI 的包 |

### 二.1.3 范本 A（推荐）：`packages/dsh-session-id/` —— 家族内最小的纯客户端 UI 插件

**完整目录树（`git ls-tree -r --name-only HEAD packages/dsh-session-id/`，真实完整）**：

```text
packages/dsh-session-id/.gitignore
packages/dsh-session-id/AGENTS.md
packages/dsh-session-id/LICENSE
packages/dsh-session-id/README.i18n.yaml
packages/dsh-session-id/README.md
packages/dsh-session-id/README.zh.md
packages/dsh-session-id/cordis.patch.yml
packages/dsh-session-id/package.json
packages/dsh-session-id/src/client/SessionIdEntry.tsx
packages/dsh-session-id/src/client/SessionIdPanel.tsx
packages/dsh-session-id/src/client/css-modules.d.ts
packages/dsh-session-id/src/client/icons.tsx
packages/dsh-session-id/src/client/index.ts
packages/dsh-session-id/src/client/locales.ts
packages/dsh-session-id/src/client/semantic.ts
packages/dsh-session-id/src/client/session-id.module.css
packages/dsh-session-id/src/client/telemetry.ts
packages/dsh-session-id/src/index.ts
packages/dsh-session-id/src/invariant.ts
packages/dsh-session-id/tests/session-id-entry.spec.tsx
packages/dsh-session-id/tests/session-id-panel.spec.tsx
packages/dsh-session-id/tsconfig.build.json
packages/dsh-session-id/tsconfig.json
packages/dsh-session-id/tsdown.config.ts
packages/dsh-session-id/vitest.config.ts
```

**从这棵树能直接学到的事实（真实、可照抄的结构）**：

- 一个完整插件**必须有**：`package.json`、`cordis.patch.yml`、`src/index.ts`（host 半区，**可以为空函数**）、`tsconfig.json` + `tsconfig.build.json`、`tsdown.config.ts`、`vitest.config.ts`、`README.md` + `README.zh.md` + `README.i18n.yaml`（双语三件套）、`AGENTS.md`（包级规则）、`.gitignore`、`LICENSE`。
- 浏览器半区**全部**放 `src/client/`：入口 `index.ts`、组件 `*.tsx`、i18n `locales.ts`、语义属性 `semantic.ts`、遥测 `telemetry.ts`、CSS Modules `*.module.css`、以及 **`css-modules.d.ts`**（CSS Modules 的类型声明——没有它 TS 会报找不到 `*.module.css` 模块）。
- **`src/invariant.ts`**：本包特有的"不变量"声明（供 `exports["./invariant"]` 用；AGENTS.md 说"必要时"才提供）。
- 测试放 `tests/`，且是 `.spec.tsx`（用 vitest + 组件挂载）。

**`package.json` 全文：未找到（blob 不可用）。** 只能给出**必须包含的字段清单**，以及每个字段的**形状依据**：

| 字段 | 形状 | 依据（可读来源） |
| --- | --- | --- |
| `"type"` | `"module"` | `packages/AGENTS.md` 逐字："独立 cordis bundle 包：`"type": "module"`" |
| `"dsh"."bundle"."patch"` | `"./cordis.patch.yml"` | `packages/AGENTS.md` 逐字 |
| `"dsh"."client"."platform"` | `"web"` | `packages/AGENTS.md` 逐字（形态参照 `packages/dsh-task-board/`） |
| `"dsh"."client"."inject"` | 服务名数组 | 见 §二.2.3 与坑 D1 的车祸现场（`remote.agentPresets` 就在这个数组里） |
| `"exports"."."` | host 半区入口 | `packages/AGENTS.md` 逐字 |
| `"exports"["./client"]` | 浏览器半区入口（**条件对象**，含 `types` + 运行时） | dsh-web 笔记 `2026-08-26-dsh-perf-client-export.md` 专讲这个（坑 B1/B2） |
| `"exports"["./invariant"]` | 可选 | `packages/AGENTS.md` 逐字 |
| `"exports"["./src/*"]` | 测试引用的源码直出 | `packages/AGENTS.md` 逐字："`./src/*` 用于测试引用" |
| `"engines"."node"` | `"^22.19 || >=24"` | `packages/AGENTS.md` 逐字 |
| `"peerDependencies"` | 运行时注入的服务 | `packages/AGENTS.md` 逐字："peerDependencies 声明运行时注入的服务" |
| `"files"` | **未找到** | 三个仓库都读不到（dsh-web 的 AGENTS.md 未提 `files` 字段） |

**注意**：用户点名要的 `files`、`peerDependencies` 具体内容、`dsh` 字段的完整 JSON，**全部未找到（blob 不可用）**。`peerDependencies` 只能确定"**声明运行时注入的服务**"这一**语义**（AGENTS.md 逐字），具体依赖名无法给出。市场上有一条相关证据：`dsh-market` 的 `ddb66c9 fix(market): 移除公开版 cordis peer 并迁移类型基底到 @deepseek-ai/cordis` —— 说明第三方独立插件把 cordis 从 `peerDependencies` 移到类型基底也是实际情况，**不要照抄 dsh-web 家族的 peer 清单**。

### 二.1.4 范本 B：`scripts/plugin-template/` —— 仓库自带的官方脚手架（最小形态）

**完整目录树（真实完整）**：

```text
scripts/plugin-template/.gitignore
scripts/plugin-template/AGENTS.md
scripts/plugin-template/README.i18n.yaml
scripts/plugin-template/README.md
scripts/plugin-template/README.zh.md
scripts/plugin-template/cordis.patch.yml
scripts/plugin-template/package.json
scripts/plugin-template/src/client/index.ts
scripts/plugin-template/src/index.ts
scripts/plugin-template/tsconfig.build.json
scripts/plugin-template/tsconfig.json
scripts/plugin-template/tsdown.config.ts
```

**这是三个仓库里能找到的、文件数最少的 UI 插件骨架（12 个文件）**。它比 `dsh-session-id` 更小，因为它是模板：没有测试、没有 LICENSE、没有 locales/telemetry/invariant。

**新手应当照抄这个结构**：`src/index.ts`（host，可为空）+ `src/client/index.ts`（browser，写 UI）+ `package.json` + `cordis.patch.yml` + 两个 tsconfig + 一个 tsdown 配置 + 双语 README 三件套。

**同样：所有文件内容「未找到（blob 不可用）」。** 无法给出 `src/client/index.ts` 的实际写法。

### 二.1.5 第三方仓库里的最小插件样例（dsh-market 的测试 fixture）

如果想知道"一个能装进 profile 的插件包长什么样"，`dsh-market_dsh-market` 的测试目录里有**五个最小样例**，每个都只有三个文件：

```text
dsh-market_dsh-market/tests/web/fixtures/fixture-a/cordis.patch.yml
dsh-market_dsh-market/tests/web/fixtures/fixture-a/index.js
dsh-market_dsh-market/tests/web/fixtures/fixture-a/package.json
dsh-market_dsh-market/tests/web/fixtures/fixture-b/{cordis.patch.yml, index.js, package.json}
dsh-market_dsh-market/tests/web/fixtures/fixture-carrier/{cordis.patch.yml, package.json}       # 注意：没有 index.js
dsh-market_dsh-market/tests/web/fixtures/fixture-clash/{cordis.patch.yml, index.js, package.json}
dsh-market_dsh-market/tests/web/fixtures/fixture-cross/{cordis.patch.yml, index.js, package.json}
```

**能直接确认的事实**：一个最小的可安装插件 = `package.json` + `cordis.patch.yml` + 一个 JS 入口（`index.js`，说明**不必是 TypeScript**）；`fixture-carrier` 只有 `package.json` + `cordis.patch.yml` 没有 `index.js`，对应坑 X4 里"bundle 载体"的形态。**文件内容未找到（blob 不可用）。**

## 二.2　如何往 slots 塞 UI

**没有一行可照抄的 slots 调用代码（blob 不可用）。** 但笔记与提交里给了**确切的 API 名、参数形状和踩坑报错**，这些是真实读到的：

### 二.2.1 已知的 slots API 表面

- `ctx.slots` —— `packages/AGENTS.md` 逐字点名它是"跨插件协作的 cordis 服务"之一（原文："跨插件协作走 cordis 服务（`ctx.slots` / `ctx.sessions` / `ctx.workspaces`）或 slot，不走 value import"）。
- `ctx.slots.register(...)` / `ctx.slots.inject(...)` —— 见坑 C1/C2 的车祸现场笔记。
- **插槽名（slot name）是字符串**，宿主在 DOM 上以 `[data-slot="<插槽全名>"]` 暴露锚点 —— 见坑 C4。
- **keyed slot** 的优先级是二元组 `(key, priority)`，且有一个保留常量 `SHADOW_PRIORITY_HEADROOM = 8` —— 见坑 C3（笔记 `2026-08-27-perf-shadow-priority-headroom.md`，逐字可读）。

### 二.2.2 三条硬约束（都是真实报错换来的）

1. **`register` 必须保留 `this`**：解构 `const { register } = ctx.slots` 会丢 `this`，报 `TypeError: Cannot read properties of undefined (reading 'effect')`（坑 C1）。→ 写 `ctx.slots.register(...)`，不要解构。
2. **注册时机**：`ctx.slots.inject` 是延迟注册（坑 C2）——在依赖服务就绪后再挂 UI，不要假设 `apply()` 一开始就能注册。
3. **keyed slot 的 `(key, priority)` 必须唯一**，撞车会互相覆盖；官方组件用 `priority` 的保留区间，插件要留 headroom（坑 C3）。

### 二.2.3 客户端 inject 是硬约束，不是提示

`package.json` 的 `dsh.client.inject`（或客户端 entry 的 `inject` 数组）里写了某个服务名，宿主上**没有**这个服务，entry 会**永远 pending**，boot 报"一个 entry 未激活"。原文（笔记 `2026-08-28-client-store-dual-cohort-engine-shim.md`，逐字）：

```text
pending (waiting for service: remote.agentPresets)
```

**修复模式**（照抄思路）：把版本相关的服务**从硬 inject 里拿掉**，改成"使用时探测"：

- *"The preset roster is read at use time through whichever face the running host serves — `remote.agentPresets` when registered, else `connection.api.agentPresets` (the pre-migration rc.2 face)"*
- *"probing at use time is the same mechanism the bridge-fallback compat binder already uses"*
- 理由（原文）：*"an inject wait either blocks activation (hard) or cannot express 'continue without it' (cordis inject has no optional flag here)"* —— **cordis 没有"可选 inject"**，所以兼容写法只能在**使用时探测**。

## 二.3　如何在设置页加一张卡片

**调用代码：未找到（blob 不可用）。** 以下是确切读到的 API 名与两个真实车祸现场。

### 二.3.1 两端分工（dsh-market 的做法，提交 53ea53d 原文）

> "dsh 0.1.0-rc.7 opened the plugin configuration page to plugins outside its own repository: the Host serves every registered settings namespace, and the tab pairs a namespace with the card keyed to it. **Both halves ship here** — the namespace in `src/settings.ts`, the card in `src/client/SettingsCard.tsx`."

→ **host 半区**：`src/settings.ts` 注册一个 settings **namespace**。
→ **browser 半区**：`src/client/SettingsCard.tsx` 渲染 keyed 到该 namespace 的**卡片**。
→ **host 侧注册 API 确认为 `installSettingsSection`**（`packages/AGENTS.md` 逐字与提交 53ea53d 都点名）。

### 二.3.2 插槽名确认为 `settings.section`

笔记 `2026-09-01-settings-scope-useSyncExternalStore-binding.md` 里有一条真实的 slot 崩溃栈（逐字）：

```text
TypeError: Cannot read properties of undefined (reading 'store')
    at getSnapshot (client.js:998)        <- official dsh-client-ui-settings bundle
    at useSyncExternalStore (frontend bundle)
    at AutoSettingsPanel (AutoSettings.tsx:76)
slot entry crashed in 'settings.section'
```

→ **崩溃日志会带插槽名 `settings.section`**，这是排查"卡片没显示/卡片崩了"的第一手线索。

### 二.3.3 必须照抄的一条：拿到官方 `SettingsScope` 后要 **bind**

- 卡片组件收到的 `props.settings` 是官方的 `SettingsScope` **实例**，它的 `subscribe` / `getSnapshot` 是**读 `this.store` 的原型方法**。
- React 的 `useSyncExternalStore` 会把回调**当裸函数调用**，`this` 变成 `undefined`，第一次 `getSnapshot()` 就抛。
- **正确写法**（提交原文）：*"`AutoSettingsPanel` now binds both methods to the scope with `useMemo` (`settings.subscribe.bind(settings)`), keeping stable hook identities across renders (the scope object itself is identity-stable per entry, so no resubscribe churn)."*
- 维护者还做了全仓审计（doctor、market、pet、session-id、session-archive、ssh、usage）：*"all other stores are closure-based (`createSnapshotStore` instances or object literals with arrow methods) and are safe unbound; the settings scope was the only prototype-method surface passed as a callback."*
- **给新手的教训**：凡是把**类实例的方法**交给 React 当回调，一律 `.bind(instance)`。`createSnapshotStore` 之类闭包 store 不用 bind。

### 二.3.4 先例与契约

- 唯一把"settings token 契约"做进 UI 的家族包是 `packages/dsh-session-archive`（笔记 `2026-09-01-session-archive-token-contract-ui.md`）。
- 卡片上要放"主操作"时，**必须用主按钮三件套 token**（见 §二.5 与坑 MK4）。
- 设置卡片"长列表"要用内部滚动（提交 0fdf63b 原文：*"popupRows 内部滚动 max-height min(52vh,440px) + 细滚动条（`--dsw-alias-scrollbar-*` 令牌）"*），并且要处理 `prefers-reduced-motion`。

## 二.4　客户端插件如何拿宿主侧数据

**调用代码：未找到（blob 不可用）。** 但这一节的**接口表是逐字读到的**，可以直接当契约用。

### 二.4.1 `invokeWireArgs()` 参数形状表（逐字，来自笔记 `2026-08-28-descriptor-faithful-wire-contracts.md`）

网关方法的参数**不能随便包 `{ request }`**，每个方法的线上形状由 SDK 生成的 descriptor 表决定：

| 调用 | 线上参数形状 |
| --- | --- |
| `session/list` | `{ _request }`（**注意下划线**） |
| `directoryPicker/list` | 扁平的、可选的 path（**不是** `{ request: body }`） |
| `agentPresets/list` | `{}` |
| `session/modelCatalog` | `{}` |
| 其余一切 | `{ request }` |

实测翻车记录（逐字）：*"session/list was invoked with args `{request}` although its single parameter wires as `_request` (task-board settlement loop dead, phone session list dead); directoryPicker/list was sent `{request: body}` although it declares one flat optional path (phone browsing dead)"*。

网关侧有 `assertExactArguments` —— 多传/少传 key 会**直接报错**（原文：*"the fakes … reject extra/missing keys exactly like the gateway's `assertExactArguments`"*）。

**给新手的教训**：**不要凭直觉包 `{ request }`**。要么查 descriptor 表，要么照抄 `invokeWireArgs()` 这个 helper 的做法（按方法名分派），并且**让测试 fake 也用同一张表**——否则真机上一条路径静默死掉、测试全绿。

### 二.4.2 业务错误码在 `error.failure`，不在 `error.code`

- `TypertRemoteFailure` **把业务错误码挂在 `error.failure` 上**；`error.code` 不是它。
- 实测翻车：*"business error codes were read from `error.code` although `TypertRemoteFailure` carries them on `error.failure` (paired-model-catalog answered 502 instead of 409/422)"*。
- 正确映射（逐字）：*"`settings-conflict` -> 409, `settings-rejected` -> 422"*，**不要用 message 正则去猜**。
- 兼容写法：*"extracts business failures from `error.failure` before falling back to `error.code`"*。

### 二.4.3 `ctx.get()` 与 `ctx.<service>` 的区别（坑 D4）

- 在 host 半区，`ctx.get('service.name')` 与 `ctx.serviceName` 的语义差别是真实踩过的坑（见坑 D4）。
- **给新手的教训**：取服务用 `ctx.get(...)`（可判空、不触发注入约束），直接用 `ctx.xxx` 容易拿到 undefined 或踩 inject 约束。

### 二.4.4 客户端 store 引擎的确切导出名

笔记 `2026-08-28-client-store-dual-cohort-engine-shim.md` 逐字给出（两个 cohort 的契约完全相同）：

```text
createSnapshotStore / defineStore / shallowEqual
```

- 来源面：`@deepseek-ai/dsh-client-store`（0.1.2+ 的冻结平台模块）或 `@deepseek-ai/dsh-client-runtime/client`（rc.2 的 inject module 的 `./client` face）。
- **`notifySubscribers` 只在 cohort 包里有，绝不能 re-export**——*"a future value import of it fails the build with a missing-export error instead of silently breaking rc.2"*。
- 真实报错（逐字，非常重要，新手一定会遇到这个形状）：

```text
failed to import loader entry 47c06ebb (@linxin666/dsh-client-ui-web-ui-settings):
client-modules: require("@deepseek-ai/dsh-client-store") missed the module table —
not a platform seed word, not a materialized module, and no registered package factory
```

→ 遇到"missed the module table"就是**在浏览器 bundle 里 import 了一个平台没允许的包**（平台种子表见 §三与 `shared/web-platform.ts`）。

### 二.4.5 `stream()` 与 `invoke()` 是两种网关调用

- 网关有 `stream()`（流式）与 `invoke()`（一次性）两种；RPC 方法名与调用方式必须配对（见坑 D2）。
- 具体方法名清单**未找到**（blob 不可用）；只能从笔记确认"`stream()` vs `invoke()` 用错会静默拿不到数据"这一模式。

## 二.5　样式与主题怎么写（事实，不猜测）

### 二.5.1 官方契约原文（`zhu1090093659_dsh-web` 的 `packages/AGENTS.md`，逐字引用）

> - **样式**：CSS Modules（`*.module.css`）经 lightningcss 编译进 bundle；不引入
>   UI 框架样式库。填充主按钮一律用主按钮三件套
>   （`--dsw-alias-button-primary-fill` / `--dsw-alias-button-primary-hover` /
>   `--dsw-alias-label-primary-foreground`，明暗两组），不得把
>   `--dsw-alias-brand-primary` 当填充色（官方主题下它与前景同值，会出现
>   黑底黑字/白底白字），契约见
>   [skins/skin-center/contracts/primary-action-tokens-v1.md](skins/skin-center/contracts/primary-action-tokens-v1.md)。

**结论（可直接照抄的规范）**：

1. **样式方案就是 CSS Modules**：文件名 `*.module.css`，通过 `import styles from './x.module.css'` 用。**不是** CSS-in-JS，**不是** Tailwind，**不是** UI 框架样式库。
2. **编译器是 lightningcss**，产物打进浏览器 bundle。
3. **主按钮三件套 token**（明暗各一组，都要出）：
   - 填充：`--dsw-alias-button-primary-fill`
   - 悬停：`--dsw-alias-button-primary-hover`
   - 前景文字：`--dsw-alias-label-primary-foreground`
4. **禁止**：把 `--dsw-alias-brand-primary` 当填充色。**原因官方写明**：官方主题下它与前景同值，会造成"黑底黑字/白底白字"。
5. 需要 TypeScript 认识 `*.module.css`，就要有 `src/client/css-modules.d.ts`（`dsh-session-id` 树里有这个文件）。

### 二.5.2 其余在设计 token 与宿主契约里出现过、可确认存在的变量

从笔记与提交里读到的 token / 属性名（**都是真实字符串**）：

- 语义 token：`--dsw-alias-label-secondary`、`--dsw-alias-label-tertiary`、`--dsw-alias-state-error-primary`、`--dsw-alias-state-success-primary`、`--dsw-alias-brand-primary`、`--dsw-alias-scrollbar-*`、`--dsw-skin-scrim`
- 插件自有 token：`--dsh-sidebar-width`、`--dsh-composer-accessory-*`、`--ds-font-family-code`（终端字体，见坑 SB1）
- 语义属性（L2，`packages/AGENTS.md` 逐字）：插件根容器打 `data-dsh-plugin="<插件短名>"`；部件打**裸值** `data-dsh-part`（例如 `column`，**不是** `task-board-column`）；**不复用官方的 `data-plugin`**（它标注 style 标签归属，语义不同）。
- 宿主 DOM 锚点：`[data-slot="<插槽全名>"]`、`[data-dsh-plugin]`、`[class$="_xxx"]` 尾匹配（官方组件类名是哈希的，如 `_dock`）。

### 二.5.3 CSS Modules 注入机制（坑 S2 的真实机制，必须知道）

- 插件样式以 `<style data-plugin-css="...">` 标签注入，tag key 用于去重。
- **class map 的哈希由"文件路径"决定**——所以 8 个不同的包各自有一个同名 `settings-card.module.css` 时，去重会把其中 7 个吃掉（坑 S2 就是这么炸的）。
- 卸载清理用 `data-plugin` 键。

**给新手的教训**：CSS Modules 的类名要**按包命名空间化**（例如 `session-id.module.css` 而不是 `settings-card.module.css`），否则跨包同名会互相吞掉。

## 二.6　完整插件目录树

### 二.6.1 `packages/dsh-session-id/`（最小纯客户端 UI 插件）

见 §二.1.3（24 个文件，已给完整树）。

### 二.6.2 `packages/dsh-web-all/`（聚合载具，含"客户端要携带子插件"的架构）

```text
packages/dsh-web-all/aggregate.yml
packages/dsh-web-all/lib/shells/package.json
packages/dsh-web-all/package.json
packages/dsh-web-all/src/client/children.generated.ts
packages/dsh-web-all/src/client/children.modules.d.ts
packages/dsh-web-all/src/client/children.specifiers.json
packages/dsh-web-all/src/client/index.ts
packages/dsh-web-all/src/client/mount-children.ts
packages/dsh-web-all/src/degraded.ts
packages/dsh-web-all/src/index.ts
packages/dsh-web-all/src/rows.ts
packages/dsh-web-all/src/shell.ts
packages/dsh-web-all/src/shells/package.json
packages/dsh-web-all/src/shells/shell.ts
packages/dsh-web-all/src/state.ts
packages/dsh-web-all/src/shells/...   （tests 见下）
```
（注：`tests/` 下 6 个测试文件，含 `shell-isolation.spec.ts`、`client-children-mount.spec.ts`；`src/state.ts`、`src/degraded.ts`、`src/rows.ts` 是 shell 的台账/行生成。）

**这张树讲清了一件关键事**：客户端 bundle 图由 **loader entries** 决定，不是由 `import` 决定。所以聚合包必须：
1. 由生成器产出 `src/client/children.specifiers.json` / `children.generated.ts` / `children.modules.d.ts`；
2. 在 `src/client/mount-children.ts` 里**在浏览器侧把每个子插件的 `./client` 当作嵌套客户端插件挂载**；
3. 生成的 `./client` 产物是 **loader factory 文件**（*"they call `window.__ModuleLoader__.load` on evaluation"*），所以 tsdown 要把这些 specifier **alias 到子包的源码**，tsc 则读生成的 ambient 声明。
（全部依据笔记 `2026-09-02-aggregate-client-children-mount.md`，逐字可读；代价是 `lib/client.js` 从 ~14KB 涨到 ~2.5MB。）

### 二.6.3 `scripts/plugin-template/`（官方脚手架）

见 §二.1.4（12 个文件，已给完整树）。

### 二.6.4 三方仓库的目录树（用于对照"第三方插件长什么样"）

**`omdsh-dev_DSH-better-sidebar`（383 文件，根目录）**：`.editorconfig`、`.github/`、`.gitignore`、`AGENTS.md`、`LICENSE`、`Makefile`、`README.md`、`README_EN.md`、`cordis.patch.yml`、`dsh.plugin.json`、`docs/`（`external-plugin-guide.md` + `plans/` 50+ 篇 + `screenshots/`）、`eslint.config.js`、`package.json`、`playwright.config.ts`、`pnpm-lock.yaml`、`pnpm-workspace.yaml`、`scripts/`（`install.ps1`、`install.sh`、`check-consumer-types.sh`、`e2e-*.sh`、`package-registry.mjs`）、`src/`（host：`agent-opens.ts`、`agent-pty.ts`、`assistant-live.ts`、`browser-probe.ts`、`bundle-route.ts`…）+ `src/client/`（`BrowserView.tsx`、`DiffTab.tsx`、`EditorHost.tsx`…）。

**`dsh-market_dsh-market`（213 文件，根目录）**：`.gitattributes`、`.github/`、`IMPROVEMENT-PLAN.md`、`LICENSE`、`README.md`、`README.zh.md`、`TESTING.md`、`UPDATE-API-V1.md`、`assets/`、**`client/client.js`（提交进仓库的浏览器 bundle）**、`cordis.patch.yml`、`package.json`、**`package-lock.json`（npm，不是 pnpm）**、`scripts/`（`build-site.mjs`、`preflight.mjs`、`restart-smoke.mjs`、`smoke-spawn.mjs`、`validate-registry.mjs`…）、`site/`（静态站）、`src/`（host）+ `src/client/`（browser）、`tests/`（宿主单测）+ `tests/client/`（浏览器半测）+ `tests/web/`（Playwright e2e + 5 个 fixture 插件）、`tsdown.config.ts`、`tsconfig*.json`、`vitest*.config.ts`（3 个 vitest 配置：默认、compat、web）。

---

# 三、开发规范（只归纳三仓共识，并标注依据）

**归纳规则**：只有当**三个仓库都这么做**，或**多个提交在反复修同一个问题**时，才写成"规范"，并注明依据。单仓独有的约定会明确标注"（仅 dsh-web）"。

## 三.1　目录怎么放

**三仓共识（依据：三仓 HEAD 目录树都在 `git ls-tree -r --name-only HEAD` 里可见）**：

```text
<插件根>/
  package.json          # 三仓都有
  cordis.patch.yml      # 三仓都有
  tsconfig.json         # 三仓都有
  tsconfig.build.json   # 三仓都有
  tsdown.config.ts      # 三仓都有
  vitest.config.ts      # 三仓都有
  README.md             # 三仓都有
  AGENTS.md             # 三仓根目录都有
  LICENSE               # 三仓都有
  src/                  # host 半区（跑在 dsh host 进程）
  src/client/           # browser 半区（跑在 Web GUI）：*.tsx / *.module.css / index.ts
  tests/                # 三仓都有；dsh-web 用 *.spec.tsx、market 分 tests/ + tests/client/ + tests/web/
```

**三仓共识的三条**：

1. **`src/` = host，`src/client/` = browser**。三仓都严格这么分（dsh-web 的 `packages/AGENTS.md` 把它写成硬规则；sidebar 与 market 的树里也是 `src/**` 放 host、`src/client/**` 放 browser）。
2. **测试全部放 `tests/`**（三仓一致；market 进一步按宿主/浏览器/web e2e 分三个子目录，sidebar 有 `tests/e2e/`，并可带 `tests/fixtures/<名字>/{package.json,cordis.patch.yml,index.js}` 作为**最小插件 fixture**——sidebar 与 market 都这么做了）。
3. **一个插件包 = 一个独立可安装的 npm 包**，不是 monorepo 里的一个源文件夹（三仓一致）。

**仅 dsh-web 独有的约定（不要当通用规范）**：
- `src/core/`（两侧共享的纯逻辑，两个 program 都编译）——只有 dsh-web 的 `packages/AGENTS.md` 规定。
- `src/invariant.ts` + `exports["./invariant"]`——只有 dsh-web 用。
- `README.i18n.yaml`（双语配对一致性记录）——只有 dsh-web 的 `packages/AGENTS.md` 要求；market 只有 `README.md` + `README.zh.md`，sidebar 用 `README.md` + `README_EN.md`。
- 插件清单写在哪里**不统一**：dsh-web 与 market 写在 `package.json` 的 `dsh` 字段（AGENTS.md 与提交信息可证）；**sidebar 在根目录另放一份 `dsh.plugin.json`**。→ 新手册应以 `dsh` 字段为主（dsh-web 家族 + market 的做法），但要知道存在 `dsh.plugin.json` 形态。

## 三.2　命名怎么起

**多提交共同修正得出的规律**：

1. **CSS Module 文件名必须按包命名空间化**。依据：坑 S2（8 个包同名 `settings-card.module.css` 互相吞掉）+ 三仓实际命名（sidebar 用 `sidebar.module.css` / `SubagentView.module.css` / `changes.module.css`；market 用 `Market.module.css`；dsh-web 的 AGENTS.md 要求 `*.module.css`）。→ **文件名 = 模块名，不要用 `index.module.css` / `settings-card.module.css` 这种通用名。**
2. **语义属性用裸值**：`data-dsh-plugin="<短名>"` + `data-dsh-part="column"`（**不是** `task-board-column`）。依据：`packages/AGENTS.md` 逐字；且 dsh-web 的 `dsk-session-id/src/client/semantic.ts` 文件存在，说明这是每包一个文件的落地方式。
3. **host 侧服务名用点分命名空间**（如 `remote.agentPresets`、`settings.section`、`session.list`、`directoryPicker.list`）。依据：笔记与提交信息里出现的全部服务/方法名都是这个形状。
4. **patch 行 id 要带命名空间**：dsh-web 的聚合生成器把子插件行 id 统一改成 `web-ui-*`（剥掉子包 `ui-` 前缀）；market 也有一条 `fix(market): namespace market identifiers as dsh-web-ui-market`（d05bf033 附近）。依据：`packages/AGENTS.md` 逐字 + 提交 a7843022。→ **理由（逐字）**："与独立包安装共存，不再触发 loader 的 duplicate entry id"。
5. **测试文件与源码同名 + `.spec`**：三仓一致（`session-id-panel.spec.tsx` 对 `SessionIdPanel.tsx`；`agent-pty.spec.ts` 对 `agent-pty.ts`；`MarketSection.tsx` 对 `tests/client/market-section.client.spec.tsx`）。

## 三.3　类型怎么定义

**三仓共识**（依据：`packages/AGENTS.md` 逐字 + 三仓都有 `tsconfig.json` + `tsconfig.build.json`）：

1. **类型只来自官方 SDK 的 npm 包**，不指向任何 DSH 源码 checkout。原文（`packages/AGENTS.md` 逐字）："只基于官方 NPM SDK：类型来自 `@deepseek-ai/*` devDependencies（node_modules 解析）；peerDependencies 声明运行时注入的服务；**禁止 tsconfig 指向任何 DSH 源码 checkout**。"
2. **tsconfig 分层**：solution + host/client 各自 program（`tsconfig.json` + `tsconfig.build.json` + 有时还有 `tsconfig.client.json` / `tsconfig.tests.json`；market 就有 4 个 tsconfig）。
3. **CSS Modules 要有类型声明**：`src/client/css-modules.d.ts`（dsh-web 的 `dsh-session-id` 有此文件）；market 有 `src/client/globals.d.ts` 与 `src/client/primitives.d.ts`。→ **每个 browser 半区都要有 `.d.ts` 声明环境类型。**
4. **浏览器 bundle 的纯度门（仅 dsh-web，但建议照抄）**：`@deepseek-ai/*` **只能 type-only 导入**；值导入只允许平台种子表成员（react / cordis / ui-slots / ui-primitives，见 `shared/web-platform.ts`）；跨插件协作走 cordis 服务或 slot，不走 value import。依据：`packages/AGENTS.md` 逐字 + 坑 B1/B2 的真实报错。

## 三.4　错误怎么处理

**多提交反复修同一个问题累积出的规范（每条都有多次提交证据）**：

1. **绝不让 promise rejection 逃出去**。证据：坑 X5（`ed3be967`：config-less row 抛错 → unhandled rejection → `installFailLoud` 杀进程）+ 坑 P4（loader 事务组回滚）。→ 插件 `apply()` 的异步逻辑一律 `try/catch`，捕获后**记日志 + 降级**。
2. **报错要解释，不要透传**。证据（多条）：market 的 pnpm ENOENT 只说路径（MK1）、Windows 锁文件 rename 的 pnpm stack（MK12-b）、pnpm 起不来的 argv dump（MK3）、host boot 失败只给一个 entry hash（坑 B1）。→ 报错**点名用户能识别的对象**（插件名/服务名），并给出**下一步动作**。
3. **"能说出来"比"静默失败"重要**。证据：market 的 `ErrorBoundary.tsx`（browser 半区专门的错误边界文件）；dsh-web 的 degraded 台账 + `GET /api/dsh-web-all/degraded` 路由（坑 X5）；提交 `7c9b3941 feat(doctor): boot self-heal attributes the failing plugin row and quarantines it`。→ 崩溃/降级要有**出口**：错误边界、降级台账、日志。
4. **运行期依赖要"使用时探测"，不要写死在硬 inject 里**。证据：坑 D1（`dsh-client-store` 硬 require + `remote.agentPresets` 硬 inject 让 entry 永远 pending）+ 坑 MK10（`settingsScope` 写进模块级 inject 会让整个插件在旧宿主不挂载）。→ cordis **没有可选 inject**，兼容只能靠嵌套 inject / 使用时探测。

## 三.5　要不要写测试

**三仓共识：要，且是硬门禁。**

- 依据 1（`packages/AGENTS.md` 逐字）："每个包必须有 `vitest run` 可通过的测试（`pnpm test` 全仓门禁）。**行为变化必须带测试**；纯 UI 展示层的冒烟测试可放宽为轻量挂载断言。""`tests/` 放测试，**测试文件不得依赖 DSH 源码 checkout 的 fixture**。"
- 依据 2（三仓都有 `vitest.config.ts` 与 `tests/` 目录）。
- 依据 3（多提交反复修同一问题）：几乎每条坑的"修复"段落都带一句测试变化——`shell-isolation.spec.ts`（14→19 用例）、`mobile-adapt.spec.ts`（11 用例）、`md-toc` 单测、`client-children-mount.spec.ts`、`tests/auto-settings.spec.tsx`（对"故意原型方法 fake"渲染）、market 的 `vitest.compat.config.ts`（真 pnpm 兼容车道）。

**从提交里能提炼的两条测试纪律（都是真实教训）**：

1. **测试要让"契约漂移"直接红**。market 与 dsh-web 都用这招：*"the test fakes encode the same descriptor tables so drift fails the suite"*（坑 D2）；*"the fakes … reject extra/missing keys exactly like the gateway's `assertExactArguments`"*。→ **fake 要跟真实契约一样严格**，否则测试全绿、真机死掉。
2. **删掉"测不到东西"的测试**。market 的作者在 `01b3c28` 里逐字写道：*"The test passed with and without the fix — it tested nothing, which is the one thing…"*（他把这条没意义的测试删了）。→ **测试必须能失败**；一个在修复前后都通过的测试是负债。

## 三.6　一句话总结（写进手册的规范清单）

> 目录：`src/`（host）+ `src/client/`（browser）+ `tests/`；根目录必有 `package.json`、`cordis.patch.yml`、两个 tsconfig、`tsdown.config.ts`、`vitest.config.ts`、`README`（双语）、`AGENTS.md`、`LICENSE`。
> 命名：CSS Module 与 patch 行 id 都要带包命名空间；语义属性用 `data-dsh-plugin` + 裸值 `data-dsh-part`。
> 类型：只依赖官方 `@deepseek-ai/*` npm 类型；browser 半区要有 `.d.ts`；`@deepseek-ai/*` 在 browser 里只能 type-only。
> 错误：异步一律 try/catch，绝不放走 rejection；报错要点名对象 + 给下一步；要有错误边界与降级出口。
> 测试：每包必须有 vitest；行为变化必带测试；fake 要和真实契约一样严格；测不到东西的测试要删。

---

# 四、新手最容易卡住的 5 个点（每个一句可执行建议）

> 挑选依据：这 5 条在三个仓库里都留下了**反复出现的修复提交**，且都是"猜不到、必须踩过才知道"的类型。

### 1. 改完前端不生效，以为是 HMR，其实是 bundle 没重建 / 没配 `exports["./client"]`

现象：改了一行 UI，刷新页面没变化；或者 host 报 `1 client package failed to compose` / `failed to import loader entry <hash>`。
**可执行建议**：**先确认两件事，再怀疑 HMR**——(a) `package.json` 里 `dsh.client` 声明与 `exports["./client"]` **必须成对存在**（缺一个就 compose 失败，见坑 B1/B2）；(b) 用 `window.__DSH_BOOT__`（或 boot 日志里的 entry id）确认浏览器**真的加载了你的新 bundle**，而不是旧产物。**改了 bundle 层的任何东西，重启 `dsh web`；只改了被按需服务的 `lib/client.js`，刷新页面即可。**

### 2. 插槽注册了却没显示：不是插槽名写错，就是注册时机不对

现象：`ctx.slots.register` 调了，界面什么都没有；控制台可能只有一行被你自己 `catch` 吞掉的东西。
**可执行建议**：**三步排查**——(a) 写成 `ctx.slots.register(...)`，**绝不写成 `const { register } = ctx.slots`**（解构丢 `this`，报 `Cannot read properties of undefined (reading 'effect')`，见坑 C1）；(b) 用 `ctx.slots.inject` 做**延迟注册**，别在 `apply()` 一开始就注册（坑 C2）；(c) 在浏览器里 `document.querySelector('[data-slot="<你的插槽全名>"]')` 看锚点在不在——**不在就是插槽名错了，在就是渲染/优先级问题**（坑 C4）。另外：`catch(e) {}` 空捕获是这类 bug 的头号帮凶。

### 3. 主按钮变"黑底黑字/白底白字"或看不见

现象：按钮在浅色主题下文字和背景同色，或者按钮压根不像按钮。
**可执行建议**：**主按钮只用三件套 token，永远不要把 `--dsw-alias-brand-primary` 当填充色**——官方写明它在官方主题下与前景同值（见 §二.5.1 与坑 MK4）。三件套是 `--dsw-alias-button-primary-fill`（填充）、`--dsw-alias-button-primary-hover`（悬停）、`--dsw-alias-label-primary-foreground`（前景），**明暗两组都要给**。

### 4. 卸载/改开关后"刷新一下就好"——其实根本没生效

现象：卸载插件提示"hot，刷新即可"，刷新后还是坏的；或者改了启用开关，界面看着变了但功能没变。
**可执行建议**：**先问"这个动作天然是热生效的吗"**——(a) 带原生 `.node` 的插件**不能热卸载**，必须整进程重启（坑 MK2）；(b) 卸载后"刷新页面"**必然** 404（bundle 没了、loader entry 还在），要在响应完成后**先禁掉自己的 entry**（坑 MK11）；(c) 改完**明确告诉用户"已生效"还是"待重启"**（坑 P6），`dsh.bundle.patch` 层的改动一律待重启。

### 5. 在浏览器半区 import 了不该 import 的包，bundle 直接不加载

现象：控制台报 `client-modules: require("...") missed the module table — not a platform seed word, not a materialized module, and no registered package factory`。
**可执行建议**：**浏览器半区里 `@deepseek-ai/*` 只能写 `import type`**；要用值只允许**平台种子表**里的那 9 个 specifier（react 四件套 + `@deepseek-ai/cordis` + `dsh-client-store` + `dsh-client-ui-slots` + `dsh-client-ui-primitives` + `dsh-client-ui-dockkit`；权威来源 `packages/client/web/src/platform.ts:8-14`）。需要别的插件的功能时，**不要 `import` 它**，改用 **cordis 服务**（`ctx.slots` / `ctx.sessions` / `ctx.workspaces`）或插槽（见 §二.4.4 与 `packages/AGENTS.md` 的"浏览器 bundle 纯度门"）。

> 🔧 **校正（2026-09-11）**：本节原文写「只用平台种子表允许的**四个**（react / cordis / ui-slots / ui-primitives）」——那是**低估**，且写的是简写名而非真实 specifier。已按源码改为 9 个全名。见 `14-inbound-http-and-timers.md` §17.3。

---

# 附：本报告的素材边界（务必随报告一起读）

1. 三个仓库都是 `--filter=blob:none` 的部分克隆。dsh-web 有 365 个可用 blob（`.agents/notes/**` + `packages/AGENTS.md`），**sidebar 与 market 为 0**。因此：
   - 所有"坑"都来自**提交信息 + 维护者笔记 + 目录树**这三类**真实可读**证据，每条都标了 `仓库 + commit 短哈希`或`仓库 + 文件路径`。
   - 所有"照抄代码"需求中拿不到的部分，都明确标注 **未找到（blob 不可用）**，**没有一行虚构代码**。
2. dsh-web 的 `.agents/notes/**` 是本次最有价值的素材源：365 个 blob 全部可读，共 786 个笔记文件（含 zh 与 i18n 配对），形态是维护者自写的 RFC/事故报告，正文骨骼固定为 `## Problem` / `## Decision` / `## Alternatives considered` / `## Consequences` / `## Testing`，含真实报错字符串、根因、权衡与否决方案、验证步骤。
3. 若要补齐"逐字源码"，只有一条路：给能联网的环境，对三仓执行 `git fetch`（补 blob），或改用 `git clone`（不带 `--filter`）。在那之前，本报告是本任务能达到的**事实上限**。

---

<!-- ↓ 源：B-tools-external.md （全文） -->

# B · 外部调用 / 工具 / 协议集成方向 —— 踩坑原始素材与可抄模板

> 用途：《DSH 插件开发实战手册·补充篇》原始素材。读者定位：零软件工程经验。
> 调研对象（4 个仓库，均为 dsh 0.1.x 生态真实插件）：
> 1. `Tencent_WeKnora` → 包 `packages/dsh-weknora`（`@wxg-prc-cpg/dsh-weknora`）
> 2. `volcengine_OpenViking` → 包 `examples/dsh-memory-plugin`（`@openviking/dsh-memory-plugin`）
> 3. `liustack_modlens` → 包根即插件（`@liustack/modlens`，`dsh/` 目录为 dsh 半边）
> 4. `yjh051108_dsh-routing-suite` → `injector/`（`@dsh-external/dsh-super-injector`）+ `graded/`（`@dsh-external/dsh-graded-mode`）
>
> 素材来源标注规则：`仓库 + 文件路径` 或 `仓库 + commit 短哈希 + 提交信息原文`。
> 本次实际读到源码/文档文件约 **44 个**（其中 6 个为分段读取）。git 历史只有 commit 元数据、无 blob，
> 所有修复内容均来自 **commit message 正文**，未使用 `git show <hash>:<path>`。

---

# 一、挖坑记录（现象 → 根因 → 怎么修）

## 1.1 Tencent_WeKnora / `packages/dsh-weknora`

该包只有 4 个相关提交，但 `feat` 提交的正文里 **自带一份完整复盘**（多次 fix 被 squash 进同一提交）。
提交时序（`git log --oneline -- packages/dsh-weknora`）：

```
d75cf72f chore: prepare v0.8.0 release notes and version bump
c1b54df7 fix(dsh-weknora): show knowledge-base figures in plugin answers (#2829) (#2895)
a68bc532 docs: link dsh-weknora to its npm package page
5b140206 feat(dsh-weknora): DeepSeek Harness plugin exposing WeKnora retrieval tools (#2759)
```

### 坑 W1（最重要）：无 scope 的检索调用 → 模型收到不透明的 HTTP 400；mock 与真实 handler 不一致导致测试测不出

- **来源**：`Tencent_WeKnora + 5b140206 + feat(dsh-weknora): DeepSeek Harness plugin exposing WeKnora retrieval tools (#2759)`，正文小节原文：

  > `* fix(dsh-weknora): demand the retrieval scope WeKnora actually requires`
  > `WeKnora rejects a knowledge-search that names no knowledge base, document or tag. The search tool told the model the opposite — that the deployment would decide the scope when a call named none — so on a deployment with no configured default, which is what the quickstart's optional WEKNORA_KNOWLEDGE_BASE_IDS leaves behind, the model's first search failed with an opaque HTTP 400.`
  > `The mock backend answered unscoped retrievals where the real handler refuses them, which is why no test caught this. Align the mock with the handler, state the requirement in the description, and reject the call inside the plugin so the model gets a message naming the argument to supply instead of a transport error.`

- **现象**：按 README 快速开始（不设 `WEKNORA_KNOWLEDGE_BASE_IDS`）装好后，模型第一次调 `weknora_search` 报 `HTTP 400`，信息里没有任何“你缺哪个参数”的提示，模型无法自救。
- **根因**：① 服务端 `POST /knowledge-search` 要求请求体必须带 `knowledge_base_ids` / `knowledge_ids` / tag 之一；② 插件工具描述却写“不指定就由部署决定”；③ 单测用的 mock 后端比真实 Go handler 宽松，放过了无 scope 调用 → 测试全绿但线上必挂。
- **怎么修**（三层一起改）：
  1. **插件内主动拦截**，抛出点名参数的错，而不是让请求打到服务端拿 400。当前源码 `packages/dsh-weknora/src/tools.ts:340-343`：

     ```ts
     // Fail here rather than let WeKnora answer 400: the model can act on a
     // message naming the argument to supply, not on a transport error.
     if (knowledgeBaseIds.length === 0 && knowledgeIds.length === 0) {
       throw new Error(`${toolName}: this WeKnora credential can see no knowledge base, so there is `
         + 'nothing to search. Check the deployment\'s API key scope.')
     }
     ```
  2. **让 mock 与真实 handler 行为一致**（mock 也拒绝无 scope 检索）。
  3. **工具描述与行为对齐**，并把 scope 解析内置化。源码 `src/tools.ts:179-184` 的 `resolveScope`：

     ```ts
     const resolveScope = async (requested: string[], knowledgeIds: string[], signal: AbortSignal): Promise<string[]> => {
       if (requested.length > 0) return requested
       if (config.knowledgeBaseIds.length > 0) return config.knowledgeBaseIds
       if (knowledgeIds.length > 0) return []
       return await allKnowledgeBaseIds(signal)
     }
     ```
     以及 `src/tools.ts:168-178` 的“可见知识库全集只解析一次并缓存”：

     ```ts
     let everyId: Promise<string[]> | undefined
     const allKnowledgeBaseIds = async (signal: AbortSignal): Promise<string[]> => {
       everyId ??= client.listKnowledgeBases(signal).then(
         bases => bases.map(kb => typeof kb.id === 'string' ? kb.id : '').filter(id => id !== ''),
         (error: unknown) => { everyId = undefined; throw error },
       )
       return await everyId
     }
     ```
- **给手册的教训**：**错误信息本身就是模型可用性的接口**。外部 API 的 400/500 要翻译成“你该改哪个参数”的话；单测的假后端必须和真后端一样“凶”。

### 坑 W2：`resource://` handle 在 dsh 里渲染不了 → 引用配图全丢

- **来源**：`Tencent_WeKnora + c1b54df7 + fix(dsh-weknora): show knowledge-base figures in plugin answers (#2829) (#2895)`，正文原文：

  > `dsh cannot load resource:// handles, and the plugin previously dropped image_info, so Q&A returned text only. Default to public URLs and emit Markdown images so the harness can render cited figures.`
  > `Refs: https://github.com/Tencent/WeKnora/issues/2829`
  > 二次修订：`Passage text already carries Markdown figures after WeKnora rewrites resource:// handles. Drop the extra images arrays and clip restoration.`

- **现象**：`weknora_ask` 返回的答案/引用里图片全部消失，只剩文字（issue #2829）。
- **根因**：WeKnora 默认返回内部句柄 `resource://…`，dsh web UI 只认识 `https://` 的 Markdown 图片，不认识内部句柄；插件又主动丢弃了 `image_info`。
- **怎么修**：
  1. 配置默认改为 `resourceUrls: 'public'`（`src/config.ts:59-67` 的 DEFAULTS 与 `src/config.ts:152-155` 校验）。
  2. 通过查询参数要求服务端把 `resource://` 改写成可直接加载的 http(s) URL。`src/client.ts:132-143`：

     ```ts
     private resourceMode(): 'handle' | 'public' {
       return this.config.resourceUrls === 'public' && !this.publicModeBlocked ? 'public' : 'handle'
     }

     private url(path: string, query?: Record<string, string | number | undefined>): string {
       const url = new URL(`${this.config.baseUrl}${path}`)
       for (const [key, value] of Object.entries(query ?? {})) {
         if (value !== undefined) url.searchParams.set(key, String(value))
       }
       if (this.resourceMode() === 'public') url.searchParams.set('resource_urls', 'public')
       return url.toString()
     }
     ```
  3. 遇到受限 API Key（服务端 403）时**自动降级并记住**，不重复付代价。`src/client.ts:113-118 / 145-165`：

     ```ts
     /**
      * A knowledge-base-restricted API key rejects `resource_urls=public` with
      * 403. After the first such refusal this client stays on handle mode so
      * later calls do not pay the same round trip.
      */
     private publicModeBlocked = false
     ```
     ```ts
     private isPublicModeForbidden(error: unknown): boolean {
       return error instanceof WeknoraApiError
         && this.config.resourceUrls === 'public'
         && !this.publicModeBlocked
         && error.status === 403
         && error.message.includes('resource_urls=public')
     }
     ```
- **给手册的教训**：跨系统传递“资源引用”时，**必须确认接收端能直接消费的 URL 形态**；对“权限受限导致的降级”要做**一次性记忆**，不要每次调用都撞一次 403。

### 坑 W3：SSE 流被截断时，把半截答案当完整答案交给模型

- **来源**：`Tencent_WeKnora + 5b140206`，正文原文（在提交正文末尾）：

  > `Added error handling for incomplete responses in the client, ensuring that truncated streams are properly managed.`

- **现象**：`weknora_ask` 偶发返回半截答案，模型据此作答。
- **根因**：WeKnora 的 `text/event-stream` 以 `response_type: "complete"` 事件结尾；网络中断/超时后流提前结束，之前累积的 `answer` 文本已经拼了一半。
- **怎么修**：用 `completed` 标志；没有收到 `complete` 事件就**抛错而不是返回半截答案**。`src/client.ts:354-433` 关键片段：

  ```ts
  let completed = false
  // ... 在 consumeLine 内：
  //   case 'complete': completed = true; break
  //   case 'error':
  //     throw new WeknoraApiError(`POST ${path} streamed an error: ${event.content ?? 'unknown error'}`)
  // ...
  // WeKnora ends every answer with a `complete` event. Without it the stream was
  // cut short, and handing the model the partial text would present a truncated
  // answer as a whole one.
  if (!completed) {
    throw new WeknoraApiError(`POST ${path} ended before WeKnora completed the answer; `
      + `${answer.join('').length} character(s) had streamed`)
  }
  ```
  同时 `finally { await reader.cancel().catch(() => undefined) }` 保证读取器不泄漏。

### 坑 W4：CI 首次安装 dsh 约 15 分钟，超过 10 分钟 job 限额

- **来源**：
  - `Tencent_WeKnora + 4e25684b + ci(dsh-weknora): cache pinned dsh install to speed up e2e`：正文 `The e2e job spends ~15 minutes downloading @deepseek-ai/dsh on every run while the actual harness scenarios finish in seconds. Cache the install directory keyed by DSH_PINNED_SPEC and enable npm dependency caching.`
  - `Tencent_WeKnora + d4f4787f + ci(dsh-weknora): restore e2e timeout for cold dsh cache`：正文 `First-run npm install of @deepseek-ai/dsh still takes ~15 minutes; the 10-minute job limit cancelled the run before the cache could warm up.`
- **根因**：`dsh plugin add` 背后是 pnpm 安装整棵 harness 依赖树，冷缓存极慢。
- **怎么修**：给 e2e job 加缓存（key 用 `DSH_PINNED_SPEC`）+ 放宽超时；工作流里还配了**每周一 03:00 UTC 用 dsh@latest 跑一次漂移检测**（允许失败），用于提前发现 harness 破坏性变更。见 `.github/workflows/dsh-plugin.yml`（`DSH_PINNED_SPEC: "@deepseek-ai/dsh@0.1.0-rc.8"`、`schedule: cron: "0 3 * * 1"`）。

### 文档线索（WeKnora）

- `packages/dsh-weknora/README.md` 有 **Compatibility** 段，明确写“Verified against dsh `0.1.0-rc.8` and WeKnora `0.8.0`…this package deliberately has **no runtime dependencies** and hands `ctx.tools.register()` a plain object, so it does not pin any harness package version.”
- 同 README “Development” 段写明：`dsh needs a Node build with zstd support (Node ≥ 22.15 or ≥ 24)…and pnpm ≥ 10 on PATH`。
- 契约测试双端锁定：`test/fixtures/api-contract.json` 记录每一次 WeKnora 调用；`test/contract.test.mjs`（插件侧）与 `contract/contract_test.go`（服务端 Go 类型侧）**两端各自断言**，“so a rename on either side fails CI instead of a user's agent”。
- 在 WeKnora 仓库内 Grep `踩坑/gotcha/pitfall/known issue`，该包文档**未命中**（即该仓库未留下这几类关键词，但上面的 commit 正文已足够详细）。

---

## 1.2 volcengine_OpenViking / `examples/dsh-memory-plugin`（`@openviking/dsh-memory-plugin`）

该包 dsh 相关提交（`git log --oneline -- examples/dsh-memory-plugin`，节选）：

```
3841e6f2 fix(plugins): drain the dsh pending queue in-process so a transient write failure self-heals (#4779)
708dba60 feat(plugins): configurable regex input filters for recall queries and captured turns (#4858)
58bafa5b fix(codex): reuse shared recall compressor (#4445)
98f24e16 fix(plugins): treat camelCase isError as an error tool result (#4724)
f7c6e843 fix(memory-plugins): report client-side MCP proxy timeouts as -32004 instead of unreachable (#4741)
37ef554b refactor(plugins): converge the harness forks back onto the shared library (#4594)
1d89f8d4 feat(plugins): derive the workspace peer from git, and let a repository carry its own config (#4595)
cf18dfb4 fix(dsh-plugin): run profile and recall in parallel on pre-step (#4643)
66c16568 feat(dsh): prevent delegated sessions from contaminating user memory (#4382)
cf5cc308 fix(codex): avoid stale actor peer in MCP proxy (#4400)
3b1db208 fix(memory-plugin): setup wizard first-run path, proxy hint, config source reporting (#4387)
028d34a0 Revert "fix(dsh): launch MCP proxy with node command (#4263)" (#4343)
24185a08 fix(memory-plugin): stop the uri-guard from reading file content as a path (#4188) (#4233)
26aae04a fix(dsh): launch MCP proxy with node command (#4263)
5356ced5 fix(plugin): honor explicit recall context timeout (#4256)
187657bb fix(dsh): run MCP proxy as Node under Electron (#4272)
b02f6025 fix(dsh): prevent duplicate profile injection after re-seed (#4231)
a83b8171 feat(uri)!: remove uid-less current-user shorthand in favor of viking://~ (#4196)
daf5fb17 fix(dsh): support current release candidate peers (#4169)
c7044075 feat(dsh): serve tools over the shared stdio MCP proxy (#4157)
eb5aaf78 feat(mcp): consolidate recall into context search (#4075)
d7ab37c7 feat(plugins): add OpenViking memory for DSH (#3993)
```

> 注意：后几条（`187657bb`/`b02f6025`/`daf5fb17`/`3b1db208`/`cf5cc308`）的 commit message **只有标题、正文为空**；不得为其编造细节，只能引用标题。

### 坑 O1（最重要，且是“静默失效”类）：用 system prompt 注入记忆会被 persona 的 `complete: true` 整段丢弃

- **来源**：`volcengine_OpenViking + examples/dsh-memory-plugin/README.md`，原文（Design notes 小节）：

  > `Recall and profile context enter through the agent/pre-step waterfall as durable, source-attributed user messages (source: { kind: 'plugin', … }). They are deliberately **not** added to the system prompt: a DSH preset whose persona declares `complete: true` (the stock `minimal` preset does) restores that persona as the sole prompt section after assembly, silently discarding every other contribution — a system-prompt-based memory plugin loses its context under such presets with no error.`

- **现象**：记忆/画像注入“看起来装好了”，但在 `minimal` 这类 preset 下完全没有生效，且**没有任何报错**。
- **根因**：dsh 的 persona 若声明 `complete: true`，组装后会用 persona 段覆盖成“唯一 prompt 段”，其它 system prompt 贡献被静默丢弃。
- **怎么修**：走 `agent/pre-step` waterfall，把注入作为**持久、带来源归属的 user 消息**追加到本步，而不是塞进 system prompt。源码 `index.mjs:47-60`（注意 `prepend: true` 与 `await next()`）：

  ```js
  // prepend: downstream waterfall listeners run first, so this plugin sees
  // the final claimed batch and appends after every other contributor.
  // Profile + recall are independent after `next()`; run them concurrently so
  // the agent/pre-step waterfall (which currently gates user/message push in
  // dsh-agent-loop) spends less wall time (#4515).
  ctx.on("agent/pre-step", async ({ agent, messages, signal }, next) => {
    const decision = await next();
    if (skipMemory(agent.session)) return decision;
    if (decision.kind !== "enter" || signal.aborted) return decision;
    const [profile, recall] = await Promise.all([
      runtime.profileMessage(agent),
      runtime.recallMessage(agent, decision.messages),
    ]);
    if (signal.aborted) return decision;
    const additions = [profile, recall].filter(Boolean);
    return additions.length > 0
      ? { kind: "enter", messages: [...decision.messages, ...additions] }
      : decision;
  }, { prepend: true });
  ```
  消息用 dsh 自己的构造器生成，保证 identity/规范化与未来不变量（`runtime.mjs:406-417`）：

  ```js
  function pluginMessage(content, form) {
    // dsh's own constructor: identity, normalization, and any future Message
    // invariants come from the pinned peer instead of a hand-built object.
    return createUserMessage({
      content: [{ type: "text", text: content }],
      source: { kind: "plugin", plugin: OPENVIKING_PLUGIN_SOURCE, form },
    });
  }
  ```
- **给手册的教训**：**“没有报错的失效”是最危险的坑**。往 system prompt 塞内容前，先确认目标 preset 的 persona 是否 `complete: true`；插件注入优先走消息通道。

### 坑 O2：直连服务端 `/mcp` → `tools/list` 永不返回

- **来源**：`volcengine_OpenViking + examples/dsh-memory-plugin/README.md`，原文：

  > `Pointing the bridge straight at the server's `/mcp` endpoint does not work: with `stateless_http=True` the server still answers `GET /mcp` with an idle 200 SSE stream, and once the MCP SDK client opens that standalone stream it stops resolving POST responses, so `tools/list` never returns. The proxy owns the transport itself and is unaffected.`

- **现象**：MCP 桥接后模型看不到任何工具，`tools/list` 一直挂起。
- **根因**：`stateless_http=True` 的服务端对 `GET /mcp` 返回一个“空闲 200 SSE 流”，MCP SDK 客户端一旦打开这条独立流就不再解析 POST 响应。
- **怎么修**：改用**自建的 stdio 代理**（`servers/mcp-proxy.mjs`），由代理自己拥有传输层。`mcp.mjs:6-7 / 44-46`：

  ```js
  /** The same stdio proxy every other OpenViking memory integration starts. */
  export const PROXY_PATH = fileURLToPath(new URL("./servers/mcp-proxy.mjs", import.meta.url));
  ```
  ```js
  export function mountOpenVikingMcp(ctx, config) {
    return ctx.plugin(mcpClient, buildMcpConfig(config));
  }
  ```
  README 同时写明：`mcp.mjs` 挂载 `@deepseek-ai/dsh-mcp-client`，与其它 harness 的集成完全一致，**这样模型拿到的是服务端全量工具集，而不是手维护的子集**。
- **附带结论（安装方式）**：`dsh plugin` 转发给 profile 目录下的 pnpm，所以插件必须是**真实包**；`dsh plugin add ./examples/dsh-memory-plugin` 这种源码链接只有在那个 checkout 有自己的 `node_modules` 时才行，因为 Node 从**源树的 realpath** 解析 dsh peers，而不是从 profile。

### 坑 O3：dsh 会 scrub 掉继承环境里的“凭据形状”变量，子进程看不到 Cordis patch

- **来源**：`volcengine_OpenViking + examples/dsh-memory-plugin/mcp.mjs:9-17` 注释原文：

  > `The bundle's own credential resolution (`OPENVIKING_*` → `ovcli.conf` → `ov.conf`, plus anything set in the Cordis patch) is forwarded through the child environment: DSH scrubs credential-shaped names out of the inherited env, and the patch is invisible to a subprocess, so values the runtime already resolved have to be passed explicitly.`

- **现象**：MCP 代理子进程连不上服务端（凭据为空）。
- **根因**：dsh 把形如凭据的环境变量从**继承环境**里剔除；子进程又读不到 Cordis patch。
- **怎么修**：宿主在 `apply()` 里已解析好的值，**显式写进子进程 env**。`mcp.mjs:18-36`：

  ```js
  export function buildMcpConfig(config) {
    // In DSH Desktop, process.execPath is Electron's executable rather than a
    // standalone Node binary. This tells Electron to run the proxy script as
    // Node instead of attempting to launch a second Desktop instance.
    const env = { ELECTRON_RUN_AS_NODE: "1" };
    if (config.endpoint) env.OPENVIKING_URL = config.endpoint;
    if (config.apiKey) env.OPENVIKING_API_KEY = config.apiKey;
    if (config.account) env.OPENVIKING_ACCOUNT = config.account;
    if (config.user) env.OPENVIKING_USER = config.user;
    if (config.peerId) env.OPENVIKING_PEER_ID = config.peerId;
    return {
      transport: "stdio",
      serverName: MCP_SERVER_NAME,
      command: process.execPath,
      args: [PROXY_PATH],
      env,
      toolCallTimeoutMs: config.mcpToolCallTimeoutMs,
    };
  }
  ```

### 坑 O4：失败写入的 latch 只在会话初始化时重置 → 长驻进程卡死到重启

- **来源**：`volcengine_OpenViking + 3841e6f2 + fix(plugins): drain the dsh pending queue in-process so a transient write failure self-heals (#4779)`，正文原文：

  > `The dsh memory plugin latches capture and commit on the first retryable write failure (hasPendingWrites) and only reset the latch at session init, so the long-lived dsh process stayed stuck until restart.`
  > `Add a per-process single-flight drainer (default 60s, env OPENVIKING_PENDING_DRAIN_INTERVAL_MS) that follows the session-start flow: probe health, replay the queue without consuming retry budgets, then re-derive every session's latch from the queue. replayPending gains an optional consumeRetries flag (default true, byte-compatible): drainers release a failed claim back to its original filename instead of incrementing the retry count…`

- **现象**：网络抖一下之后，capture/commit **永久不工作**，直到重启 dsh。
- **根因**：第一次可重试写失败就置 `hasPendingWrites = true`（“锁存”），而这个锁只在 session init 时重置。
- **怎么修**：进程内**单飞 drainer**，默认 60s 一次，先探健康再回放队列，回放时**不消耗重试预算**。`runtime.mjs:344-388` 关键片段：

  ```js
  async drainTick() {
    if (this.drainRunning) return;
    this.drainRunning = true;
    try {
      const pending = await listPending();
      if (pending.length > 0) {
        const health = await this.client.healthResult();
        if (!health.ok) {
          if (this.drainHealth !== false) {
            this.log("drain_health_down", { status: health.status || 0 });
          }
          this.drainHealth = false;
        } else {
          if (this.drainHealth === false) {
            this.log("drain_health_restored", {});
          }
          this.drainHealth = true;
          await this.replayPendingQueue({ consumeRetries: false });
        }
      }
      for (const state of this.states.values()) {
        await this.refreshPendingState(state);
      }
    } finally {
      this.drainRunning = false;
    }
  }
  ```
  启动与清理都挂 `ctx.effect`，`index.mjs:24-31`：

  ```js
  // The pending-queue drainer is the in-process recovery path: without it a
  // single transient write failure latches capture/commit until the next dsh
  // restart. Started here so every session shares one single-flight drainer.
  runtime.startDrainer();
  ctx.effect(
    () => () => runtime.stopDrainer(),
    "openvikingMemory.stopDrainer()",
  );
  ```
  定时器 `unref()` 避免阻止进程退出（`runtime.mjs:386`：`this.drainTimer.unref?.();`）。
- **给手册的教训**：**“锁存式失败”是长驻进程的隐形炸弹**。任何 `failed = true` 的降级开关，都必须有一条自动恢复路径（这里是一条后台 drainer）。

### 坑 O5：DSH 工具结果用 camelCase 的 `isError`，插件只认 `is_error` → 失败的调用被记成“成功”

- **来源**：`volcengine_OpenViking + 98f24e16 + fix(plugins): treat camelCase isError as an error tool result (#4724)`，正文原文：

  > `DSH emits tool-result blocks with a camelCase isError field ({type:"tool-result", toolCallId, content, isError}), but the shared capture-utils toolStatus() only checks is_error / error / state.error. Failed results were therefore labeled tool_status=completed, while their error text still landed in tool_output. The mislabel does not mislead LLM memory extraction (verified end-to-end), but it does corrupt status-driven consumers: experience read lineage (experience_lineage.py), usage reporting, working-memory formatting, and rollout training artifacts.`
  > `Recognize block.isError alongside is_error.`

- **现象**：工具调用**失败了**，但捕获下来的 `tool_status` 是 `completed`（错误文本仍在 `tool_output`）。
- **根因**：dsh 的 tool-result 块字段是 camelCase `isError`，插件只检查了 snake_case `is_error`。
- **怎么修**：两个拼写都认。`shared/capture-utils.mjs:155-157`：

  ```js
  function toolStatus(block, kind) {
    // ...
    if (block?.is_error || block?.isError || block?.state?.isError || block?.error || block?.state?.error) return "error";
  ```
  同时把新测试登记进 CI 的 plugin-tests 列表（正文：`add examples/memory-plugin-shared/capture-utils.test.mjs to the pr.yml plugin-tests list (it was author-local only)`）。
- **给手册的教训**：读宿主回传的结构时，**字段命名的拼写变体（snake_case vs camelCase）是一类系统性坑**；判错只影响“统计/下游消费”，不会立刻报错，最难发现。

### 坑 O6：MCP 代理**自身超时**被当成“服务器不可达”上报

- **来源**：`volcengine_OpenViking + f7c6e843 + fix(memory-plugins): report client-side MCP proxy timeouts as -32004 instead of unreachable (#4741)`，正文原文：

  > `A request aborted by the proxy's own timeout budget fell into mapError()'s catch-all and surfaced as -32001 'check the URL / server reachable' even while the server was healthy and still computing — rerank-inclusive find/search legitimately runs tens of seconds past the default 15s budget, so every such call was mislabeled as an outage (#4739).`
  > `Branch on AbortError before the catch-all and return a dedicated -32004 naming the elapsed budget, the endpoint, and the OPENVIKING_TIMEOUT_MS knob; -32001 keeps its meaning of genuine connection failure. -32003 is already taken by the empty-response error, so timeouts use -32004.`

- **现象**：服务端健康、任务还在算，调用却报 `-32001 check the URL / server reachable`（误判为断连）。
- **根因**：代理自己的超时（默认 15s）抛 `AbortError`，落进了 catch-all 分支。
- **怎么修**：在 catch-all **之前**先判 `AbortError`，返回专用错误码 `-32004`，消息里点名“耗时预算 + 端点 + `OPENVIKING_TIMEOUT_MS` 旋钮”。`shared/mcp-proxy-core.mjs:295-309` 片段：

  ```js
  if (err && err.name === "AbortError") {
    // ... (rerank can run longer than the default budget). Keep -32001 for genuine
    return errorResponse(message.id, -32004,
      `OpenViking MCP request timed out after ${proxyConfig.timeoutMs}ms (${proxyConfig.mcpUrl}). The server may still be processing (rerank can be slow) — check /health or raise OPENVIKING_TIMEOUT_MS.`);
  }
  ```
- **给手册的教训**：**错误码要能区分“对方挂了”和“我们等太短”**，否则用户会去查一个根本没坏的服务。错误消息里要给出“调哪个环境变量可以放宽”。

### 坑 O7：URI guard 把“文件内容”当成“路径”扫 → 本地写入提到 viking:// 就被拒

- **来源**：`volcengine_OpenViking + 24185a08 + fix(memory-plugin): stop the uri-guard from reading file content as a path (#4188) (#4233)`，正文原文：

  > `findVikingUri() checked the path-like keys and then swept every remaining argument value, so a local write or edit whose CONTENT merely mentioned a viking URI was denied and no file was created:`
  > `  write { file_path: "/home/me/notes.md", content: "docs say viking://user/default/ is virtual" } -> deny`
  > `The sweep still runs — it is what catches an unusual or nested path key — but it now skips arguments that carry content rather than a location (content, new_string, old_string, file_text, ...). A URI in file_path, path, uri, an unknown nested path key, or a bash command still denies.`

- **现象**：本地 `write`/`edit` 的文件**正文里**只是提到了一句 `viking://…`，整次写入被 deny，文件没建出来。
- **根因**：guard 先查已知路径键，然后“扫剩余全部参数值”，把正文也扫了。
- **怎么修**：保留全扫（用于兜住奇怪/嵌套的路径键），但**按名字跳过内容类字段**。`shared/uri-guard.mjs:17-45` 原文：

  ```js
  // Arguments that carry file CONTENT rather than a location. The sweep below
  // looks past the known path keys so an unusual one (`paths`, a nested target)
  // is still caught, but text a tool is asked to WRITE is not a path: a local
  // `write` whose body merely mentions viking://user/default/ was denied, and no
  // file was created. Skipped by name at any depth.
  const DEFAULT_CONTENT_KEYS = [
    "content", "contents", "text", "body",
    "old_string", "oldString", "new_string", "newString",
    "old_str", "new_str", "file_text", "insert_line", "replacement",
  ];

  export function findVikingUri(args = {}, keys = DEFAULT_URI_KEYS, contentKeys = DEFAULT_CONTENT_KEYS) {
    if (!args || typeof args !== "object") return null;
    for (const key of keys) {
      const uri = findVikingUriInValue(args[key]);
      if (uri) return uri;
    }
    return findVikingUriInValue(args, new Set(contentKeys));
  }
  ```
  deny 时的提示消息也很讲究（`shared/uri-guard.mjs:69-78`）：

  ```js
  export function buildGuardMessage(uri, hint = {}) {
    const tool = hint.tool || "the OpenViking MCP tools";
    const example = typeof hint.example === "function" ? hint.example(uri) : hint.example;
    const lines = [
      "viking:// URIs are OpenViking virtual paths, not local filesystem paths.",
      `Use ${tool} instead.`,
    ];
    if (example) lines.push(`Example: ${example}`);
    return lines.join("\n");
  }
  ```
- **给手册的教训**：**“拦截器误伤”比“放行”更烦人**。做参数级校验时，先想清楚哪些字段是“位置”、哪些是“内容”；误拦时要给出“改用哪个工具 + 一个可抄的调用示例”。

### 坑 O8：Electron 桌面宿主下，`process.execPath` 不是 Node → 代理启不来（经历一次 revert）

- **来源（三条，按时间）**：
  - `volcengine_OpenViking + 187657bb + fix(dsh): run MCP proxy as Node under Electron (#4272)`（**正文为空**，仅标题）
  - `volcengine_OpenViking + 26aae04a + fix(dsh): launch MCP proxy with node command (#4263)`，正文 `Use a stable Node command for the DSH stdio MCP proxy so Electron desktop hosts do not try to spawn their own app binary as the proxy runtime.`
  - `volcengine_OpenViking + 028d34a0 + Revert "fix(dsh): launch MCP proxy with node command (#4263)" (#4343)`（**正文为空**，这是一次回滚——说明“换成固定 node 命令”的方案后来被撤了）
- **现象**：dsh 桌面版（Electron）里 MCP 代理起不来，Electron 把 `process.execPath` 当成自己的可执行文件，于是试图“再开一个桌面实例”。
- **根因**：Electron 下 `process.execPath` = Electron 二进制，不是独立 Node。
- **最终修法**（当前源码 `mcp.mjs:28-35`）：仍用 `process.execPath`，但**显式加 `ELECTRON_RUN_AS_NODE: "1"`** 让 Electron 以 Node 模式运行脚本：

  ```js
  return {
    transport: "stdio",
    serverName: MCP_SERVER_NAME,
    command: process.execPath,
    args: [PROXY_PATH],
    env,
    toolCallTimeoutMs: config.mcpToolCallTimeoutMs,
  };
  ```
- **给手册的教训**：桌面宿主里“`process.execPath` 是宿主而不是 Node”是常见陷阱；**`ELECTRON_RUN_AS_NODE=1` 是标准解法**。同时注意：这里有一次 `feat → revert` 的往复，说明**跨平台启动子进程的方案要按宿主类型分支，不能一把梭**。

### 坑 O9：re-seed 之后 profile 被重复注入

- **来源**：`volcengine_OpenViking + b02f6025 + fix(dsh): prevent duplicate profile injection after re-seed (#4231)`（**正文为空**，仅标题）。
- **现象/根因**：标题即结论——会话 re-seed 后 profile 被注入两次。修复方向（可从当前源码印证）：插件自己检查“本会话历史里是否已经有本插件的 instructions 消息”，有则不再注入。`runtime.mjs:419-435`：

  ```js
  function hasStartupProfile(agent) {
    const session = agent.session;
    const ownEvents = (session?.events || []).slice(session?.header?.seedLength ?? 0);
    const inHistory = ownEvents.some(event => (
      event?.type === "user/message" && isStartupProfile(event.data)
    ));
    if (inHistory) return true;
    return [agent.inbox?.nextTurn, agent.inbox?.nextStep].some(messages => (
      (messages || []).some(isStartupProfile)
    ));
  }

  function isStartupProfile(message) {
    return message?.source?.kind === "plugin"
      && message.source.plugin === OPENVIKING_PLUGIN_SOURCE
      && message.source.form === "instructions";
  }
  ```
- **给手册的教训**：任何“每会话只注入一次”的东西，都必须有**幂等判据**（这里靠 `source.kind/plugin/form` 三件套），并且要覆盖 `session.events` 与 “inbox 待发队列”两条路径。

### 坑 O10：`viking://user/<segment>` 有歧义 → 直接做成 breaking change

- **来源**：`volcengine_OpenViking + a83b8171 + feat(uri)!: remove uid-less current-user shorthand in favor of viking://~ (#4196)`（**正文很长、含大量迁移细节**），关键原文：

  > `viking://user/<segment> (memories/resources/skills/peers/privacy/sessions without a user id) was ambiguous with a user literally named after the segment, and a user actually named e.g. "memories" was unreachable for USER/ADMIN callers. Now that the viking://~ home alias (#4167) covers the same need unambiguously, the shorthand fails closed at the request boundary instead of expanding`
  > `BREAKING CHANGE: requests using the uid-less viking://user/<segment> spelling now fail with 400; use viking://~/<segment> or an explicit viking://user/{user_id}/<segment> URI.`

- **现象**：所有用旧写法的调用开始 400。
- **根因**：`viking://user/memories` 里 `memories` 既可能是“保留段”也可能是“一个真叫 memories 的用户”。
- **怎么修**：**fail closed**（拒绝并给出纠正提示），并**迁移仓库内所有第一方 emitter**；对存储里的历史写法做兼容归一化。README 顶部也加了醒目提示：

  > `**Requires an OpenViking server with `viking://~` home-alias support.** Recall targets the caller's own context space through `viking://~/memories` and `viking://~/skills`; the uid-less `viking://user/memories` shorthand is rejected by newer servers.`
- **给手册的教训**：URI / 路径里有“保留字 vs 真实名”的歧义时，**宁可在边界直接拒绝并给出正确写法**，也不要猜。

### 其它相关提交（只有标题，不展开）

- `cf5cc308 fix(codex): avoid stale actor peer in MCP proxy (#4400)`（标题；正文空）——代理里 actor peer 会变陈旧。
- `3b1db208 fix(memory-plugin): setup wizard first-run path, proxy hint, config source reporting (#4387)`（标题；正文空）。
- `5356ced5 fix(plugin): honor explicit recall context timeout (#4256)`，正文 `Let operator-configured recallContextTimeoutMs apply even when context recall skips rewrite and query expansion, so low-latency configs can still extend the request deadline explicitly.`（并且要求“把修复同步进共享源码，生成的插件副本才能保持一致”）。
- `708dba60 feat(plugins): configurable regex input filters for recall queries and captured turns (#4858)`（标题；正文在 `shared/input-filters.mjs` 可印证功能）。

### 文档线索（OpenViking，最关键的一份“逐条报错 → 排查”表）

`docs/zh/agent-integrations/17-dsh.md` 的「常见问题」表（原文照抄）：

| 现象 | 排查方向 |
|------|----------|
| 没有注入，也没有 OpenViking 工具 | `dsh --profile web --dump-config` 里应能看到 `openviking-memory`；重新运行安装器或 `dsh plugin --profile web add …` |
| 装到了错误的 profile | 安装器默认 `web`；用 `--dsh-profile <name>` 重新运行 |
| 安装时报 `ERESOLVE` | `@deepseek-ai/dsh-*` 各包预发布 tag 不同步；请精确安装 `@deepseek-ai/dsh@0.1.0-rc.6` |
| 安装时报包「不在 npm registry 中」 | pnpm 默认拒绝发布不满 24 小时的版本（`minimumReleaseAge`）。等一等，或把该精确版本加进 profile 的 `pnpm-workspace.yaml` 的 `minimumReleaseAgeExclude` |
| 召不回任何内容 | `curl http://localhost:1933/health`；检查端点配置，以及 prompt 是否长于最小查询长度（3 个字符） |
| OpenViking 返回 401 / 403 | 检查 `OPENVIKING_API_KEY`；可信模式部署还要检查 `OPENVIKING_ACCOUNT` 与 `OPENVIKING_USER` |
| 串入了其他项目的记忆 | 设置 `OPENVIKING_RECALL_PEER_SCOPE=actor` |
| 崩溃后没有 commit | commit 由 token 阈值和 teardown 触发；排队的写入会在下次会话开始时重放 |

README 另一处重要提示：`The bundle has no runtime npm dependencies.`（peerDependencies 由 DSH 自己安装；本包不额外加依赖）。以及 `PLUGIN_VERSION` 必须与 `package.json` 版本一致（`package.json` 的 `check:version` 脚本会校验）。

---

## 1.3 liustack_modlens / `@liustack/modlens`（包根即插件，`dsh/` 是 dsh 半边）

modlens 的 dsh 相关修复提交极多（`git log --oneline -i --grep='dsh'` 有 40+ 条）。挑与“工具 / 外部调用 / 协议集成”最相关的：

### 坑 M1（最重要，安装类）：`declares no dsh.bundle — installed as a plain dependency`

- **来源**：`liustack_modlens + docs/troubleshooting.zh-CN.md`（该条标题就是 dsh 的原话），正文原文：

  > `dsh profile 装到的是旧版 modlens。`dsh.bundle` 声明从 3.9.0 起才存在，而 pnpm 11 会扣住最近 24 小时内发布的版本（`minimumReleaseAge`，自 11.0 起默认开启。`pnpm config get` 不展示这一项的内置默认值，所以查它什么都不显示）。当带声明的版本全都落在这个窗口内时，pnpm 会静默回退到更旧的版本，而旧版本没有 bundle 声明，dsh 于是正确地把它当作普通依赖，一个工具都不会出现。`
  > ``@latest` 绕不开这一层，本页早先的说法是错的。冷静期先把候选版本过滤掉，dist-tag 才在剩下的里面解析，于是它直接落到了更旧的那个上。改成写死精确版本号，pnpm 会把它当作一次明确的指定，而不是一次解析：`
  > ```sh
  > npx -y @deepseek-ai/dsh plugin --profile <name> add @liustack/modlens@3.26.1
  > ```
  > `如果你自己设过 `minimumReleaseAge`，pnpm 会把这条策略视为严格模式，转而拒绝安装并报出版本与截止时间（`ERR_PNPM_NO_MATURE_MATCHING_VERSION`）。在同一个文件里放行这一个版本：`
  > ```yaml
  > minimumReleaseAgeExclude:
  >   - '@liustack/modlens@3.26.1'
  > ```

- **现象**：插件“装上了”，但一个工具都不出现；dsh 报 `declares no dsh.bundle — installed as a plain dependency`。
- **根因**：pnpm 11 的 24 小时冷静期 + 未点名版本号 → 静默回退到**没有 `dsh.bundle` 声明的旧版**。
- **怎么修**：**安装时写死精确版本号**（并同步更新时也用 `add @版本`，而非 `update`，因为 `update` 只在已记录的 caret 范围内挪动，2.7.1 永远进不了 3.x）。同文档还给出更严格的 `minimumReleaseAgeExclude` 例外写法。
- **给手册的教训**：**“装上了但没生效”** 优先查版本：包是否声明了 `dsh` 字段、装到的是不是被冷静期回退的旧版。`dsh plugin --profile <name> list` 可以看到实际装了什么。

### 坑 M2：工具名与宿主 `read_image` 撞名 → 宿主 scoped 层静默遮蔽插件全局层

- **来源**：`liustack_modlens + docs/troubleshooting.zh-CN.md`「dsh：模型看不到 read_image 工具」：

  > `插件注册的工具名是 `modlens_read_image`，不是 `read_image`。dsh 的工具注册表是分层的，scoped 层会遮蔽全局层：宿主的 `read_image` 挂在 agent preset 作用域、插件注册在全局层，两者根本不算重名，于是注册静默成功，模型解析到的仍是宿主那个，而它对纯文本模型直接拒绝（[#34](https://github.com/liustack/modlens/issues/34)）。用自己的名字就没有东西会遮蔽它，模型是通过工具 schema 找到它的，而 schema 每次请求都会送达，与叫什么名字无关。`
  > `如果模型仍然看不到，去 harness 日志里搜 `[modlens] ... registration skipped`。`

- **现象**：注册没报错，但模型看不到/解析到的是别人的同名工具。
- **根因**：dsh 工具注册表**分层**，scoped（agent preset）层遮蔽全局层；重名不是错误，是静默遮蔽。
- **怎么修**：**给自己的工具起一个专属名字**（`modlens_read_image`）。源码注释把结论写死（`dsh/index.js:296-314`）：

  ```js
  // A name of our own rather than the host's. dsh's registry is layered and
  // a scoped tool shadows a global one, so a host `read_image` mounted in the
  // agent-preset scope and ours registered globally are not a duplicate at
  // all: the registration succeeds, nothing throws, and the model still
  // resolves the host's (issue #34). ... `toolName` still pins whatever a host
  // prefers.
  const preferred = config.toolName || 'modlens_read_image'
  try {
    ctx.tools.register(readImageTool(preferred))
  } catch (error) {
    // Same-layer duplicate of the chosen name, or a preview-era surface
    // change: degrade loudly instead of taking the whole plugin down.
    console.error(`[modlens] ${preferred} registration skipped: ${error}`)
  }
  ```
- **给手册的教训**：**注册成功 ≠ 生效**。起名要避开宿主已有工具；注册用 `try/catch` 兜住并“响一声”（`console.error`），不要静默吞掉。

### 坑 M3：harness 小版本升级改了工具定义的必填字段 → `prepareCall` 派发缺失

- **来源**：`liustack_modlens + 9199c6c + fix(dsh): serve the prepareCall dispatch dsh 0.1.1 requires`（**正文为空**，仅标题）。可印证：插件工具定义里同时提供 `presentCall`，并在 `apply()` 里为宿主预留了工具名与 schema。
- **现象**：dsh 0.1.1 下工具派发失败。
- **根因**：harness 开发者预览期**会增改工具定义契约**（0.1.1 要求 `prepareCall` 派发）。
- **怎么修**：跟随新版提供所需字段。同时插件对“预览期表面变化”统一用 `try/catch` + “degrade loudly”（见 M2 代码）。
- **给手册的教训**：dsh 处于 developer preview，**工具定义契约会变**；插件要（a）不 import 宿主包，只交普通对象（WeKnora 与 modlens 都这么做），（b）注册失败要响。

### 坑 M4：dsh 0.1.0-rc.7 把 settings slot 变成 keyed → 卡片整块不渲染

- **来源**：`liustack_modlens + f0ab04f + fix(dsh): give the settings card the key and namespace rc.7 renders by`，正文原文：

  > `dsh 0.1.0-rc.7 changed the settings page twice over. The slot the card registers into became keyed, so registering without options.key throws, which is the console error both reports carry. And a card now renders only when its key matches a settings namespace the host serves, where the old page rendered every registered card.`
  > `So the fix is two-sided. The browser half keeps its id, which rc.6's list slot requires, and adds key: 'modlens', which rc.7's keyed slot requires; one client.js serves both versions. The host half registers a 'modlens' settings namespace so the key has something to match.`

- **现象**：设置页里插件卡片消失，控制台报 keyed-slot 错误（issues #61/#65）。
- **根因**：rc.7 起 slot 需要 `key`，且卡片必须匹配宿主提供的 settings namespace。
- **怎么修**：**双版本兼容**——保留 `id`（rc.6 列表槽需要），再加 `key`（rc.7 键控槽需要）；宿主侧注册一个同名空 namespace 让 key 有东西可匹配（`dsh/index.js:207-219`）：

  ```js
  if (config.settingsCard !== false && typeof ctx.inject === 'function') {
    ctx.inject(['settings'], (scope) => {
      try {
        const passThrough = (value) => ({ ...(value ?? {}) })
        passThrough.toJSON = () => ({
          uid: 0,
          refs: { 0: { type: 'object', meta: { default: {} }, dict: {} } },
        })
        scope.settings.register('modlens', passThrough, { base: {} })
      } catch (error) {
        console.error(`[modlens] settings namespace skipped: ${error}`)
      }
    })
  }
  ```
- **给手册的教训**：UI 槽位的“注册契约”也会随 harness 版本变；**同一份 client.js 同时满足新旧两版的必填字段**是最省事的兼容法。

### 坑 M5：dsh 0.1.2-rc.1 把 composer 换成 Lexical contenteditable → 粘贴转路径“静默失败”

- **来源**：`liustack_modlens + 4b76ed4 + fix(dsh): write paste-to-path into the Lexical composer (#100)`；`CHANGELOG.md` 第 5 行原文：

  > `**dsh paste-to-path writes into the Lexical composer ([#100]).** dsh 0.1.2-rc.1 replaced the composer textarea with a Lexical contenteditable div. The paste listener still uploaded the image, then insertText returned immediately because it only accepted TEXTAREA and INPUT, so the path never landed and the console stayed quiet. Paste-to-path now resolves a writable target (textarea, input, or [data-composer-input][contenteditable=true]) before taking the event, inserts with execCommand, and logs the path if that insert fails.`

- **现象**：图片上传成功，但输入框里没有出现路径，**控制台一声不响**。
- **根因**：`insertText` 只认 `TEXTAREA`/`INPUT`；新版 composer 是 Lexical 的 `contenteditable` div。
- **怎么修**：先解析“可写目标”，插入优先用 `execCommand('insertText')`，失败再退回原型 setter；内容可编辑 div 不适用 value setter，直接放弃并**打日志**。`dsh/client.js:35-87` 原文：

  ```js
  function isTextField(el) {
    return el && (el.tagName === 'TEXTAREA' || el.tagName === 'INPUT')
  }

  function isComposerEditable(el) {
    if (!el || typeof el.getAttribute !== 'function') return false
    if (el.getAttribute('data-composer-input') == null) return false
    return el.isContentEditable === true || el.contentEditable === 'true'
  }

  function isWritable(el) {
    return isTextField(el) || isComposerEditable(el)
  }

  function insertText(target, text) {
    if (!isWritable(target)) return false
    target.focus()
    // execCommand fires the input event React's controlled textarea needs;
    // the prototype-setter dance is the fallback for engines dropping it.
    var inserted = false
    try {
      inserted = document.execCommand('insertText', false, text)
    } catch {
      inserted = false
    }
    if (inserted) return true
    // Lexical's composer is a contenteditable div: it has no value
    // setter, and assigning innerHTML/textContent bypasses the editor.
    if (!isTextField(target)) return false
    try {
      var proto =
        target.tagName === 'TEXTAREA' ? window.HTMLTextAreaElement.prototype : window.HTMLInputElement.prototype
      var setter = Object.getOwnPropertyDescriptor(proto, 'value').set
      setter.call(target, target.value + text)
      target.dispatchEvent(new Event('input', { bubbles: true }))
      return true
    } catch {
      return false
    }
  }
  ```
  插入失败时明确打日志（`dsh/client.js:196-198`）：

  ```js
  if (!insertText(target, `${text} `)) {
    console.error(`[modlens] paste-to-path: could not insert into the composer (${text})`)
  }
  ```
- **给手册的教训**：浏览器端“往输入框里写字”**没有万能写法**，必须按元素类型分支；且**失败必须留下痕迹**（这里原来“console 一声不响”是最坑的部分）。

### 坑 M6：bundle loader 在等必需服务时调 `apply` → 读 `ctx.llm` 抛 “inactive context”

- **来源**：`liustack_modlens + dsh/index.js:145-160` 注释原文，并提到 issue #79：

  > `Bundle loaders can call apply while this outer context is still waiting for its required services. Reading ctx.llm here then throws "inactive context" before the first discovery sweep can register any lifecycle work (#79). Put the whole provider registry inside an injected child scope: Cordis starts it only while llm is active, and tears its listeners and registrations down with that service.`

- **现象**：加载期读可选服务直接抛 “inactive context”。
- **根因**：外层 context 还在等必需服务时 `apply` 已被调用。
- **怎么修**：把整块逻辑塞进 `ctx.inject([...], scope => ...)` 的**子作用域**，服务就绪才启动、服务下线就随之下线。`dsh/index.js:153-159`：

  ```js
  if (typeof ctx.inject === 'function') {
    ctx.inject(['llm'], (scope) => {
      return registerVisionProvider(scope, config, ownProviders, evidenceCache)
    })
  } else {
    registerVisionProvider(ctx, config, ownProviders, evidenceCache)
  }
  ```
  客户端侧同一模式（`dsh/client.js:1063-1105` 注释）：

  > `Reaching for an undeclared service throws in cordis, so each optional dependency rides a scoped ctx.inject of its own: the closure runs where the service exists and never runs where it does not… Listing it beside slots would be worse than useless: ctx.inject waits for every service named, so on a host that never provides locale the card would never register at all.`
- **给手册的教训**：**可选依赖要各自 `ctx.inject`，不要和必需依赖并列**；并列会让“一个可选服务缺席”把整块注册拖死。

### 坑 M7：包装路由丢上游状态 → 推理链（reasoning）成批丢失

- **来源（两条，都是 commit 正文原文）**：
  - `liustack_modlens + 83ab641 + fix(dsh): keep upstream replay state alive through the vision wrapper (#49)`：

    > `Reasoning blocks went missing on sessions routed through a (modlens vision) model… Measured by the reporter at ~57% of turns against a ~1% baseline on the same route… dsh strips an assistant message's adapter-private replayState whenever the provider recorded on that message belongs to a different adapter instance than the one about to run (LlmService.forAdapter, an identity comparison). This wrapper is a different instance by construction, so every turn it produced reached upstream with that state removed, and replayState is what carries reasoning continuity for these models.`
  - `liustack_modlens + c3e1f41 + fix(dsh): the vision wrapper inherits what its upstream route already had (#57)`：

    > `A user configured maxRetries 50 on their route and watched the (modlens vision) group retry twice, the harness default. The wrapper registers its own adapter, and its providerRetryPolicy() was hardcoded to return undefined. … It delegates now.`
    > `This is the second time the wrapper has been found dropping something the upstream had: #49 was the adapter-private replay state… so this went through all five methods the service calls on an adapter rather than fixing the one that was reported.`

- **现象**：走包装路由的会话里 reasoning 块丢失（报道者实测 ~57% vs 基线 ~1%）；`maxRetries` 等上游配置不生效。
- **根因**：包装器是**另一个 adapter 实例**，dsh 按“adapter 身份”比较，于是把 `replayState`（承载推理连续性）剥掉了；`providerRetryPolicy()` 又被硬编码返回 `undefined`。
- **怎么修**：包装器**把所有上游已有的东西都转发/委派**（五件事一次过，而不是只修被报道的那一件）。并明确“不复制 configurable-provider 目录”（配置仍归上游所有）。另有 `906d21a fix(dsh)!: a pinned default id encodes its upstream, like the sweep's`（**BREAKING CHANGE**：pinned 之外的默认 providerId 改为 `modlens-<upstream>`，旧会话需重选一次）。
- **给手册的教训**：**做“包装/代理层”时，宿主是按对象身份判等的**。凡是上游 adapter 提供的字段/方法，包装层都要显式转发；只修被投诉的那一个字段是治标不治本的（这里第二次才补全五处）。

### 坑 M8：Windows 下子进程弹黑框

- **来源**：`liustack_modlens + d7a2300 + fix(spawn): start every child through a wrapper that hides its console`，与 `dsh/spawnHidden.js` 全文：

  ```js
  // The only place this plugin starts a child process.
  //
  // The desktop app has no console of its own, so on Windows every child it
  // starts would be given one and shown its window: a black box per read
  // (issue #60). `windowsHide` suppresses that, defaults to false in Node, and is
  // ignored elsewhere.
  //
  // It lives in a file of its own, apart from its callers, so the rule can be
  // checked by looking at which files reach `child_process` at all rather than at
  // what each call passes. A call site cannot forget an option it never writes,
  // and writing the option after the caller's leaves nothing to override it.
  import { spawn } from 'node:child_process'

  export function spawnHidden(command, args, options) {
    return spawn(command, args, { ...options, windowsHide: true })
  }
  ```
- **根因**：Node 的 `windowsHide` 默认 false；桌面 App 每起一个子进程就闪一个黑框。
- **怎么修**：所有 spawn 收敛到**唯一一个包装函数**，并让 `windowsHide: true` 在**最后**合并（调用方无法覆盖）。文件独立，便于用“哪些文件 import 了 child_process”来审查。
- **给手册的教训**：Windows 下要加 `windowsHide: true`；并且**把跨平台差异封装到一个文件**，而不是靠每个调用点记得传。

### 坑 M9：Node 的 `fetch` 默认无视代理环境变量

- **来源**：`liustack_modlens + docs/troubleshooting.zh-CN.md`「fetch failed 或连接失败」原文：

  > `API 请求根本没离开这台机器。在要靠代理才能上网的网络里这是预期表现：Node 的 fetch 默认无视代理环境变量。你明确要求走代理后 modlens 才会遵循，两种写法任选：`
  > `HTTPS_PROXY=http://127.0.0.1:7890 modlens -i shot.png -p gemini-api   # env (NO_PROXY honored too)`
  > `modlens config set proxy http://127.0.0.1:7890                        # persistent, all API providers`
  > `modlens config set openai.proxy http://127.0.0.1:7890                 # one provider only`
  > `modlens config set openai.proxy ""                                    # 这个 provider 强制直连`
  > `provider 代理字段有三种状态。字段缺失表示继承共享配置或环境代理，空字符串表示直连，URL 表示只给该 provider 使用的代理。当外部 provider 需要共享代理，而内网端点必须直连时，这个区别很重要。`

- **现象**：`Could not connect to generativelanguage.googleapis.com (UND_ERR_CONNECT_TIMEOUT). The request never reached the network.`
- **根因**：Node 内建 fetch **不读** `HTTPS_PROXY` 等环境变量。
- **怎么修**：显式支持代理（env 或配置），并区分“缺省=继承 / 空串=直连 / URL=专用代理”三态。相关提交：`17b5373 fix: keep no-proxy API requests on same-sourced undici fetch`、`9d38558 fix(proxy): 支持 provider 直连与 DSH 代理设置`。
- **给手册的教训**：**“网络失败”先确认请求是否真的出了机器**；需要代理时必须显式配置（`undici`/`ProxyAgent`），别指望环境变量。

### 坑 M10：外部 provider 返回的 JSON 不符合声明的 schema

- **来源**：`liustack_modlens + docs/troubleshooting.zh-CN.md`「openai provider 的结果被拒绝」与 `docs/output-schema.md`：

  > 报错原文：`OpenAI-compatible API returned JSON that does not match the vision schema (wrong or missing: visual.notes, ...)`
  > `大多数 OpenAI 兼容网关在服务端什么都不强制，契约是以填好的 JSON 模板形式随提示词发过去的，能力弱一些的模型可能只答出一半，关掉思考时尤其明显。可以改成让网关自己强制执行：` `modlens config set openai.structuredOutput true`
  > `这会把契约以 response_format: json_schema 的严格形式发过去，schema 由 modlens 校验用的那份推导而来，没有需要手工同步的副本。默认关闭，因为不支持这个字段的网关会直接 400。`
  > （`docs/output-schema.md`）`Never null: a model with nothing to say there often writes one, and modlens drops the key before the result reaches you, so reading an optional field means checking whether it is there, not whether it is null.`
  > （同文档）`layout.regions[].type is a free string, not a closed list. Region kinds are an open set: a fixed enum rejected link on any web screenshot and search on a portal, and a rejected result fails the whole read over a descriptive label. The field's schema description names the common vocabulary as guidance.`

- **根因**：服务端不强制 schema；弱模型只答一半；模型爱用 `null` 填“无可说”；把描述性字段做成枚举会因“多一个合法值”而整体失败。
- **怎么修**：① 可选开关让支持 `response_format: json_schema` 的网关硬校验（默认关，因为不支持的网关会 400）；② 可选字段读“在不在”而不是“是不是 null”，`null` 直接丢键；③ **描述型字段用自由字符串 + description 引导**，不要用闭集 enum；④ 校验失败时**报出具体字段名**（`wrong or missing: visual.notes`）。
- **给手册的教训**：**模型的 JSON 输出要靠 schema 强约束 + 容错解析**；报错要能指出“哪个字段不对”。

### modlens 其它 dsh 提交（仅标题，未展开）

`0f29110 fix(dsh): a route that gains native vision says so, and says what to do`（拒绝包装自带视觉的模型时要给出人话解释）、`8962f59 fix(dsh): name a wrapped route after its upstream, and cover two untested paths`、`bfd6bbf fix(dsh): render settings card before agent discovery`、`8e711b7 fix(dsh): bind discovery to llm lifecycle`、`7546a6a fix(dsh): reuse repeated path-tool image reads`（同一图片重复读取要复用缓存）、`04e6ed1 fix(dsh): exclude vision-named ids and see through vendor prefixes`、`9085be4 fix(dsh): failed reads hold their bytes; the shared cache spares open walks`、`b95a021 fix(dsh): close paste store lifecycle gaps`、`314070c fix(dsh): canonicalise the store's parent, and never guess a paste's size`、`eccc8d2 fix(dsh): verify the paste store before trusting it, and keep the ledger honest`、`a2bb742 fix(dsh): collect pasted files instead of keeping them forever (#51)`、`c49d062 fix(dsh): require proof of ownership, not a borrowed name (#36)`、`f0c0f1e fix(dsh): follow dsh's interface language on the settings card`、`3ca7d59 fix(dsh): localize the card's load/save failure fallbacks`。

---

## 1.4 yjh051108_dsh-routing-suite / `injector`（`@dsh-external/dsh-super-injector`）+ `graded`（`@dsh-external/dsh-graded-mode`）

这个仓库的 git 只有 72 个提交，但 `injector/CHANGELOG.md` 与 `docs/SPEC.md` 把**每一条踩坑都写成了规范**。
以下坑优先选取“工具 / schema / 生命周期 / 跨平台”方向。

### 坑 R1：`parameters` 的 `required` 写法 —— **两条注册路径规则相反，必须分清** ⚠️⚠️

> ## 🔴 重要校正（2026-09-11，由主线核对官方源码后加）
>
> 本节原标题写的是「`parameters` 属性级不能有 `required` 键」——**这个结论只对一半，直接照抄会写错**。
> 官方仓库 `deepseek-harness` 源码（commit `c291e7961a`）实证：
>
> ```ts
> // packages/core/tools/src/schema.ts:570-571（defineTool 实现体内）
> const parameters = parameterSchemaSpecToJsonSchema(options.parameters)
> const outputSchema = valueSchemaSpecToJsonSchema(options.output.schema)
> ```
>
> ```ts
> // packages/core/tools/src/schema.ts:96-106
> /** One implicit parameter-root property, optionally required. */
> export type ParameterPropertySpec = ValueSchemaSpec & { required?: true }
>
> /**
>  * Tool parameter schema. The map itself is an implicit open object root;
>  * requiredness remains a per-property `required: true` annotation.
>  */
> export type ParameterSchemaSpec = {
>   [key: string]: ParameterPropertySpec
>   [key: symbol]: never
> }
> ```
>
> ```ts
> // packages/core/tools/src/schema.ts:290-303（属性级 required 的收集逻辑）
> if (task.kind === 'property') {
>   if (!isJsonSchemaRecord(task.property)) authorError(`${task.path} must be a value schema object`)
>   if (Object.hasOwn(task.property, 'required') && task.property.required !== true) {
>     authorError(`${task.path}.required must be true when present`)
>   }
>   if (Object.hasOwn(task.property, 'required') && task.property.required === true) task.required.push(task.key)
>   ...
> }
> ```
>
> ```ts
> // packages/core/tools/src/schema.ts:449-458（DSL → JSON Schema 的投影）
> export function parameterSchemaSpecToJsonSchema(spec: ParameterSchemaSpec): ParameterJsonSchema {
>   const compiled = compilePropertyMap(spec, 'parameters')
>   const schema: ParameterJsonSchema = {
>     type: 'object',
>     properties: compiled.properties,
>     ...(compiled.required === undefined ? {} : { required: compiled.required }),
>   }
>   assertSupportedJsonSchema(schema)
>   return schema
> }
> ```
>
> ### 结论：DSH 有**两条**写工具的参数路径，`required` 写法正好相反
>
> | 注册方式 | `parameters` 是什么 | 必填怎么写 | 写错的后果 |
> |---|---|---|---|
> | **`defineTool({...})`**（官方推荐，从 `@deepseek-ai/dsh-tools` 导入） | **DSH 作者 DSL**（`ParameterSchemaSpec`） | **属性级** `required: true` | 写对象级 `required: ['a']` → 报错 `parameters.a.required must be true when present` 或 `parameters.x is not supported by the value schema DSL` |
> | **裸 `ctx.tools.register({...})`** | **原始 JSON Schema**（`ToolDefinition.parameters`） | **对象级** `required: ['a']` | 写属性级 `required: true` → 被 `assertSupportedJsonSchema` 拒绝（`required must be an array of strings`） |
>
> 官方仓库自带的工具插件（如 `packages/interaction/tool-ask-user/src/index.ts`）**全部走 `defineTool`**，写法是**属性级**：
>
> ```ts
>     parameters: {
>       questions: {
>         type: 'array',
>         required: true,          // ← 属性级，DSH DSL 正确写法
>         description: 'Questions to ask the user before continuing.',
>         items: {
>           type: 'object',
>           additionalProperties: true,
>           properties: {
>             id: { type: 'string', required: true, description: '...' },
>             ...
> ```
>
> **`output.schema` 同理**：走 `defineTool` 时也是 DSH DSL，用**属性级** `required: true`（官方 `tool-ask-user` 的 `output.schema.properties.answers` 就是 `required: true`）；且官方源码里 `output.schema` 的**根节点不允许 `required`**（`compileValueSchema` 以 `allowRequired: false` 起步，`schema.ts:427`）。
>
> **本笔记下方所有来自社区仓库的"对象级 `required` 数组"例子**，都是**裸 `register` + 原始 JSON Schema** 路径的写法 —— 它们本身没错，但**不能拿去填 `defineTool` 的 `parameters`**。
>
> **给手册的最终教训**：先明确你走哪条路（新手一律推荐 `defineTool`），再决定 `required` 写在哪一级。**不要混用**。
>
> ---
>
> 以下为 Agent 原始调研内容，**请带着上述校正阅读**。

### 原来的分析（保留原貌，结论已被上方校正）

- **来源**：`yjh051108_dsh-routing-suite + graded/src/tools.js:12-19` 文件头注释原文（原话“血泪坑,勿改”）：

- **来源**：`yjh051108_dsh-routing-suite + graded/src/tools.js:12-19` 文件头注释原文（原话“血泪坑,勿改”）：

  > ```
  > Schema 形态约束（血泪坑,勿改）：
  >   register() 用 assertSupportedJsonSchema 直查 output.schema 原文,发给模型的
  >   parameters 经服务端 JSON Schema 严格校验——全都只认标准 raw 形态：
  >   对象级 required 数组,属性级一律不允许 required 键。
  > ```

- **现象**：工具注册被拒（或模型侧校验失败）。
- **根因**：dsh 的工具注册器用 `assertSupportedJsonSchema` **直接读 `output.schema` 原文**；且 `parameters` 会被服务端按**标准 JSON Schema** 严格校验。它只接受“对象级 `required` 数组”，**属性节点里不允许出现 `required` 键**。
- **怎么修**：全部使用**标准 raw JSON Schema**：
  - ✅ 正确（源码里到处如此，`graded/src/tools.js:35-45`）：

    ```js
    const outputSpec = {
      schema: {
        type: 'object', additionalProperties: false, required: ['ok', 'text'],
        properties: {
          ok: { type: 'boolean' },
          text: { type: 'string' },
          warnings: { type: 'array', items: { type: 'string' }, description: '软约束提示（如概念超限），非错误' },
        },
      },
      render: (_args, value) => TEXT(value.text + (value.warnings?.length ? `\n（提示：${value.warnings.join('；')}）` : '')),
    }
    ```
  - ✅ 嵌套对象的 required 也一律放“对象级”（`graded/src/tools.js:48-59` 的 `groupItemSchema`）：

    ```js
    const groupItemSchema = {
      type: 'object', additionalProperties: false, required: ['title', 'spec', 'accept', 'do', 'verify'],
      properties: {
        title: { type: 'string', description: '小类名（纯名词短语,不要重复大类词）' },
        concepts: { type: 'array', items: { type: 'string' }, description: '...' },
        // ...
        mode: { type: 'string', enum: ['correct', 'experience', 'research'], description: '...' },
      },
    }
    ```
  - ⚠️ **反例（不要抄）**：`injector/src/index.ts` 的骨架模板里出现过属性级 `required`（`injector/src/index.ts:176-178`）：

    ```ts
    parameters: {
      name: { type: 'string', required: true, description: '谁' },
    },
    ```
    这与 `tools.js` 文件头“属性级一律不允许 required 键”的结论**互相矛盾**；两处写法不同，说明该仓库自身也存在未统一的旧写法。**教学时以 `graded/src/tools.js` 的 `required` 数组写法为准**（更严格、且是该仓库“血泪坑”注释点名的那种）。
- **给手册的教训**：工具 schema 是**发给模型的严格 JSON Schema**，不是 TypeScript 类型。`required` 只写在对象节点上、值是字符串数组；属性节点里不要写 `required: true`。

### 坑 R2：资源“裸注册”（未挂 `ctx.effect`）→ 热重载报 `duplicate / already registered`

- **来源**：`yjh051108_dsh-routing-suite + injector/docs/SPEC.md` 规范 2.2 原文：

  > `**规范 2.2**：**所有资源注册挂 ctx.effect 即获得 dispose 自动清理**——这是 cordis 的契约。裸注册（绕过 effect）在 dispose 后残留（僵尸闭包根因）。注入器自身工具必须全部走 ctx.effect（已修），插件模板同样强制。`

  以及 `injector/CHANGELOG.md` [0.2.3]/[0.1.0] 的实测记录：

  > `**强制登记守卫**：reloadPackage 重建失败若报 duplicate / already registered → 判定未登记裸注册 → 明确报错（要求插件把资源注册挂 ctx.effect）+ 自动清理残留路由`

- **现象**：热重载后报 `duplicate` / `already registered`（如 `duplicate route`）；旧 fiber 的注册没被清掉。
- **根因**：插件用“裸注册”把工具/路由/监听挂上去，没挂 `ctx.effect` → dispose 后残留。
- **怎么修**：**一切注册都包在 `ctx.effect` 里**，并保留它返回的 disposer。`injector/src/index.ts:142-186` 的官方骨架（逐字）：

  ```ts
  export function apply(ctx: Context, config: Config): void {
    // 工具注册（ctx.effect：fiber dispose 自动注销）
    ctx.effect(() => ctx.tools.register(defineTool({
      name: '${pkgName.replace(/[^a-z0-9_]/gi, '_')}_hello',
      description: ${JSON.stringify(description || '示例工具')},
      parameters: {
        name: { type: 'string', required: true, description: '谁' },
      },
      output: {
        schema: { type: 'string' },
        render: (_args: unknown, value: unknown) => [{ type: 'text', text: String(value) }],
      },
      async execute(args: { name: string }) {
        return config.greeting + '，' + args.name + '！'
      },
    })), '${pkgName}: hello tool')
  ```
  `graded/src/index.js:358-367` 是“批量注册 + 显式 disposer”的更稳写法：

  ```js
  ctx.effect(() => {
    const disposers = []
    for (const def of [editPlanDefinition(deps), lockStageDefinition(deps), markTaskDefinition(deps), commitStarDefinition(), redteamVerdictDefinition(), reviseDoDefinition()]) {
      try {
        const d = ctx.tools.register(def)
        if (d) disposers.push(d)
      } catch (e) { console.warn('[graded] global tool register failed:', def.name, e?.message || e) }
    }
    return () => { for (const d of disposers) { try { d() } catch { /* 幂等 */ } } }
  }, 'graded-mode: global tools')
  ```
- **给手册的教训**：**注册必挂 `ctx.effect`**，否则热重载/卸载必留残留；注册多个工具时逐个 `try/catch`，一个坏工具不拖垮整组。

### 坑 R3：profile patch 顶层 `[]` + 盲目 append → YAML 双顶层值，解析必炸

- **来源**：`yjh051108_dsh-routing-suite + injector/docs/SPEC.md` 规范 3.1 与 `injector/src/index.ts:715-731` 注释原文：

  > `**规范 3.1**：**profile patch 永远是单一顶层数组**——`[]` 或 `- id:` 列表，**绝不混存**（双顶层值 = YAML 解析错误 = 装配全灭）。注入器写 patch 必须解析式追加（writePatch），这是配置方言的硬性契约。`
  > `官方 patch 初始是顶层 []（空数组）；盲 append "- id:" 会产生两个顶层 YAML 值 → 解析必炸。本函数：移除顶层 [] 再追加条目，保证文件始终单一顶层值（列表）。`

- **现象**：改过 patch 后 dsh 直接装配全灭（YAML 解析错误）。
- **根因**：官方生成的 patch 初值是顶层 `[]`；直接 append `- id: …` 就变成“数组 + 新条目”两个顶层值。
- **怎么修**：**解析式写入**——先扫描现有条目 id，去重、幂等，再移除顶层 `[]` 后追加。`injector/src/index.ts:731-762` 关键片段：

  ```ts
  function writePatch(appendText: string): boolean {
    // ...
    // 1. 收集 appendText 携带的 id
    const appendIds = [...appendText.matchAll(/^\s*- id:\s*([^\s#]+)/gm)].map((m) => m[1])
    // 2. 提取现有内容里所有条目块（含注释），按 id 归组
    const blocks = extractPatchBlocks(content)
    // ... 同 id 重复：只保留最后一条
    // 3. 幂等：appendIds 全部已存在 → 不写入
    if (appendIds.length > 0 && appendIds.every((id) => existing.has(id))) {
      return false
    }
    // 4. 重写：去重后的现有块 + 追加文本
    const cleanedTop = kept.join('').replace(/^\s*\[\]\s*$/m, '')
    writeFileSync(patchFile, cleanedTop + appendText, 'utf8')
    return true
  }
  ```
- **给手册的教训**：**别用字符串拼接改 YAML/JSON 配置文件**。要么整份解析后重新序列化，要么至少做 id 去重 + 顶层值归一。

### 坑 R4：`duplicate loader entry id` → 整个 plugin tree 加载失败（启动即崩），且插件无法自愈

- **来源**：`yjh051108_dsh-routing-suite + injector/src/index.ts:721-730` 注释原文：

  > ```
  > ═══ 幂等去重（2026-08-15 别人机器 duplicate loader entry id 教训）═══
  > 手动 patch / 重复安装 / 多路径写入都可能让同 id entry 出现两次——dsh
  > loader 装配遇同 id 直接抛 `duplicate loader entry id`，整个 plugin tree
  > 加载失败（启动即崩），且注入器自身无法自愈（鸡生蛋）。因此：
  >  1. 写入前扫描现有条目 id；若 appendText 的 id 已存在 → 不追加（幂等）；
  >  2. 对历史重复：重写文件时按 id 去重（保留最后一条，注释块保留）；
  >  3. heal/self-test 等触碰 patch 的路径全部走这里，杜绝盲 append。
  > ```

- **现象**：dsh 启动即崩，报 `duplicate loader entry id`。
- **根因**：同一个 `id` 的 entry 在 profile patch 里出现两次（手动改 / 重复安装 / 多路径写入）。
- **怎么修**：**写入前按 id 幂等去重**（见 R3 的 `writePatch`）。
- **给手册的教训**：插件行的 `id` 是**主键**；任何自动写入 patch 的代码都要先查重。

### 坑 R5：`homedir()` ≠ 真实 DSH_HOME → junction 建到错误 profile，loader 找不到包

- **来源**：`yjh051108_dsh-routing-suite + injector/src/index.ts:572-575` 注释原文：

  > ```
  > ⚠️ DSH_HOME 优先（实测踩坑）：部署的 web 进程 homedir 可能与 DSH_HOME 指向
  > 不同用户（如服务账户/另一用户 profile），homedir() 推导的路径会全部错位——
  > junction 建到错误 profile、loader 找不到包。DSH_HOME 环境变量才是权威。
  > ```
  > `const dshHome = process.env.DSH_HOME || join(homedir(), '.dsh')`

  同一修复也写进了 `injector/CHANGELOG.md` [0.3.3]：`**DSH_HOME 优先（homedir 错家）**：web 进程 homedir 与 DSH_HOME 不一致时（如服务账户/跨用户部署），registry/profileNodeModules/日志全错位…`

- **现象**：注入的插件“找不到”；写到了别的用户目录。
- **根因**：`os.homedir()` 推出的 `~/.dsh` 与真实的 `DSH_HOME` 不一致。
- **怎么修**：`process.env.DSH_HOME || join(homedir(), '.dsh')`，一切路径都由它派生。
- **给手册的教训**：**存盘/配置路径永远以 `DSH_HOME` 为准**，别硬编码 `~/.dsh`。graded 里的 `stateFile` 也遵循同一规则（`graded/src/index.js:34-39`）。

### 坑 R6：junction 路径被 tsx 模块缓存命中的旧模块 → 重载“静默失败”

- **来源**：`yjh051108_dsh-routing-suite + injector/src/index.ts:916-919` 注释原文：

  > ```
  > ⚠️ 必须 import realpath URL 而非 junction URL（实测踩坑）：tsx 按 URL
  > 缓存模块，junction 路径变化（如自检 tmpDir 迁移）后 junction URL 仍
  > 命中旧模块缓存，loadCache 不产生新 key → 匹配仍失败。realpath URL
  > 是全新 key，强制重新解析磁盘并填充缓存。
  > ```
  > 以及 `injector/CHANGELOG.md` [0.3.3]：`reloadPackage 磁盘降级改 import realpath URL（junction URL 会被 tsx 旧缓存命中，tmpDir 迁移后重载失效——实测 uid 不变）`

- **现象**：改了源码、重载了，但生效的还是旧代码（uid 不变）。
- **根因**：模块缓存按 URL 命中；junction 路径不变 → 命中旧缓存。
- **怎么修**：import **realpath** URL。`injector/src/index.ts:920-925`：

  ```ts
  const realLib = realpathSync(libPath)
  await ctx.loader.import(pathToFileURL(realLib).href, () => [])
  const real = realLib.replace(/\/g, '/')
  for (const u of loadCache.keys()) {
    if (typeof u === 'string' && decodeURIComponent(u).includes(real)) { entryUrl = u; break }
  }
  ```
- **给手册的教训**：做热重载时，**模块缓存按路径字符串命中**；走 realpath，且别忘 `decodeURIComponent`（非 ASCII 目录）与 `\` → `/`。

### 坑 R7：Windows 自带脚本宿主读不了带非 ASCII 注释的脚本 → 需 UTF-8 BOM


- **来源**：`yjh051108_dsh-routing-suite + 3f1b02e`（2026-09-03）提交信息原文：
  `fix(install): UTF-8 BOM so Windows PowerShell 5.1 parses non-ASCII comments (#16) (#87)`
- **现象**：Windows 自带的 Windows PowerShell 5.1 执行 `install-injector.ps1` 直接报语法错误（注释里的中文/中文标点被按 GBK/ANSI 解码，吃掉了引号或行尾）。
- **根因**：PS 5.1 默认按本地代码页（简体中文 Windows 是 GBK）读 `.ps1`，文件本身是无 BOM 的 UTF-8 → 中文注释乱码，某些字节序列被解释成引号导致解析失败。
- **怎么修**：把 `.ps1` 存成 **UTF-8 with BOM**（BOM 三个字节 `EF BB BF` 告诉 PS 5.1 用 UTF-8 读）。
- **给手册的教训**：给 Windows 用户发脚本时，**`.ps1` 必须带 BOM 存 UTF-8**；`.sh` 反过来要**去掉 BOM**（见 R8）。一份仓库同时装两种控制台脚本时最易踩。

### 坑 R8：`.sh` 被 CRLF 检出 → `set: pipefail: invalid option name`

- **来源**：`yjh051108_dsh-routing-suite + 5145152`（2026-09-03）提交信息原文：
  `fix: pin .sh to LF — CRLF breaks bash on Windows (#27)`，正文：
  > ```
  > With core.autocrlf=true on Windows, .sh scripts check out with CRLF line
  > endings; bash then reads "set -euo pipefail\r" and fails with
  > "set: pipefail: invalid option name" (seen when running
  > `bash scripts/build.sh` inside injector/). The repo blobs are LF — the
  > breakage is on the checkout side. Add .gitattributes (*.sh text eol=lf)
  > so .sh files stay LF regardless of autocrlf.
  > ```
- **现象**：Windows 上 `bash scripts/build.sh` 报 `set: pipefail: invalid option name`。
- **根因**：`core.autocrlf=true` 把 `.sh` 检出了 CRLF，首行 `set -euo pipefail` 末尾带了 `\r`，bash 把 `pipefail\r` 当成一个非法选项名。
- **怎么修**：仓库根加 `.gitattributes`：
  ```
  *.sh text eol=lf
  ```
  （注意：**子模块是独立仓库，各自都要自己的 `.gitattributes`**。）
- **给手册的教训**：Windows 上开发跨平台脚本，**第一时间加 `.gitattributes`**：`.sh` 强制 LF、`.ps1` 保持 CRLF/BOM、`.ts/.js/.json` 一般 `text eol=lf`。

### 坑 R9：`isHealthyLink` 把 pnpm 安装的**真实包目录**当“坏链接”删掉

- **来源**：`yjh051108_dsh-routing-suite + 1aa12ad`（2026-09-03）提交信息原文：
  `fix(injector): isHealthyLink 误删真实包目录 + 设置页 React 渲染契约 (#65)`，正文：
  > ```
  > * fix(injector): treat real (non-link) dirs as healthy in isHealthyLink
  >
  > - dev_inject_plugin: pnpm 安装的真实包目录被判为"坏链接"，被 rmSync 后替换为
  >   自指 junction--一次注入毁掉一个正常安装的包（Windows 实测）
  > - autoRestore link 自愈扫描对真实目录做无谓删除尝试；registry 包悬空警告
  >   对所有真实目录误报刷屏
  > - 真实（非链接）路径是包管理器管理的安装实体，不应进入链接校验/删除重建
  >   分支：一律视为健康
  > ```
- **现象**：执行一次“注入插件”，一个**本来好好装在 `node_modules` 里的包**被删了，换成了一个自己指向自己的 junction（自指链接），包直接废掉。
- **根因**：健康检查函数把“不是符号链接的真实目录”误判为“需要修复的坏链接”，走了 `rmSync` + 重建 junction 的分支。
- **怎么修**：判“链接健康”前先分类型——**真实（非链接）目录一律视为健康**，不进删除/重建分支。
- **给手册的教训**：任何“自动修复/自愈”逻辑，删除动作前必须**先用 `lstatSync` 判断它到底是不是链接**；`existsSync` 会跟随链接、对真实目录与悬空链接给出相反答案（见 R21）。

### 坑 R10：设置页塞普通对象 → React #130 + 整页空白

- **来源**：`yjh051108_dsh-routing-suite + 1aa12ad`（2026-09-03）提交信息原文（同上），正文：
  > ```
  > * fix(injector): settings page must use React render contract
  >
  > - 宿主 ui-settings 的 settings.section 槽期望 React 渲染函数（dsh-market 同款
  >   契约 register(descriptor, () => createElement(...))）
  > - 原 component: () => ({ render() {...} }) 普通对象在宿主渲染时抛 React #130
  >   （slot entry crashed in 'settings.section'）-> 设置页整页空白
  > - DOM 构建逻辑不变，仅改为 React 容器渲染；label「插件」与官方插件页重名，
  >   改为「插件管理」
  > ```
- **现象**：插件装上后，DSH 设置页**整页空白**，控制台 `slot entry crashed in 'settings.section'` + `React #130`（`React #130` = 返回了非合法 React 元素）。
- **根因**：`settings.section` 槽的渲染契约要的是**返回 React 元素**的函数，而插件返回了一个带 `render()` 方法的普通对象（以为要自己管 DOM）。
- **怎么修**：`register(descriptor, () => createElement(...))`，返回 React 元素；不要返回 `{ render() {} }` 这种对象。
- **给手册的教训**：UI 槽 = **React 世界**。插件的 `component` 必须返回 React 元素（JSX/`createElement`），不是自己写的 DOM 渲染器。契约可对照官方 `dsh-market` 同款写法。

### 坑 R11：同毫秒事件被“水位线”比较判成同一条 → 少推进一拍

- **来源**：`yjh051108_dsh-routing-suite + 39ee0a0`（2026-09-03）提交信息原文：
  `fix(stage): event-index watermark prevents same-millisecond double advance (#73) — port to v1.20 + sync unaliased baseline (carries sessionEvents from #85) (#86)`
- **现象**：快速连续两步（同一毫秒内）时，第二步被当成“已经处理过”。事件索引水位用**时间戳**做唯一标识，同毫秒两条事件时间戳相同 → 第二条被判为重复，双推进丢失（或反向：重复推进）。
- **根因**：用 `Date.now()`（毫秒）当事件的唯一键；毫秒内可以产生两条事件。
- **怎么修**：水位改**事件序号/索引**（单调递增整数），不用时间戳。
- **给手册的教训**：**永远不要用时间戳当唯一标识/去重键**；用数组下标或事件自带的单调 id。

### 坑 R12：agent preset 接管工具清单后，`bash` 变 `unknown tool`（注册表不匹配）

- **来源**：`yjh051108_dsh-routing-suite + 7ddeec3`（2026-09-03）提交信息原文：
  `fix(assembly): add tool-bash-posix row — POSIX bash registry mismatch (#66)`，正文：
  > ```
  > Agent presets take over the tool manifest, so the host (dsh-base) tool-bash
  > never enters a preset session: the bash claimed by STAGES stage 3 (verification)
  > fails with 'unknown tool' on macOS/Linux. Register it in the preset manifest;
  > win32 keeps using the gitbash group row (platform-mutually-exclusive, never
  > double-registered).
  > ```
- **现象**：进入某个 agent preset 会话后，提示模型用 `bash`，但模型报 `unknown tool: bash`；macOS/Linux 必现，Windows 反而正常。
- **根因**：preset **接管工具清单**（manifest）后，宿主 `dsh-base` 的 `tool-bash` 不再进入该会话；而清单里只声明了 `win32` 的 gitbash 组行，POSIX 侧没有对应行。
- **怎么修**：在 preset manifest 里补一行 POSIX 的 `tool-bash-posix`；`win32` 继续用 gitbash 组行（两者平台互斥，不会重复注册）。
- **给手册的教训**：**工具注册表是分层的**（全局层 / preset 层），preset 会整体接管工具面。写插件假设“宿主一定有某工具”就会踩空；跨平台工具名可能不同（`tool-bash` vs `tool-bash-posix`）。

### 坑 R13：`npm ci` 因引用了**未发布的包**而失败 → 锁到正式版 + 显式声明

- **来源**：`yjh051108_dsh-routing-suite + e3f00b2`（2026-09-03）提交信息原文：
  `merge: #76 fix(injector) unpin unpublished dsh-type-meta so npm ci works`，正文：
  > ```
  > - INSTALL.md：自源码构建真实经验文档（--legacy-peer-deps/分叉包重链）
  > - package-lock：rc 钉版→已发布正式版（cordis 4.0.1/cosmokit 1.8.2/TS 5.9.3）+ cordis-plugin-loader 声明
  > - package.json：devDependencies 声明 cordis-plugin-loader（锁对齐）
  > ```
- **现象**：`npm ci` 直接失败——`package-lock.json` 里钉了一个**从未发布到 registry** 的包版本（`dsh-type-meta`）。
- **根因**：锁文件里写着 registry 上不存在的版本；`npm ci` 严格按锁文件装，装不到即失败。另外 `cordis-plugin-loader` 被 `package-lock` 引用却没在 `package.json` 声明，锁与清单不一致。
- **怎么修**：把 rc 钉版改成**已发布的正式版**；`package.json` 里**显式声明**所有被锁引用的包；自源码构建的真实经验（`--legacy-peer-deps`、分叉包重链）写进 INSTALL.md。
- **给手册的教训**：**`package-lock` 引用的每个包都必须在 `package.json` 里声明**，且版本必须在 registry 真实存在；RC/未发布版本不要写进锁文件。

### 坑 R14：打包前没有先构建根 git 依赖 → 产物缺依赖

- **来源**：`yjh051108_dsh-routing-suite + a0122f3`（2026-09-03）提交信息原文：
  `fix: build root git dependency before packing (#81)`
- **现象**：`npm pack` / 发布出来的包在目标机装不上或缺文件。
- **根因**：根依赖是从 git 拉的（`git+...`），**打包时它还没被构建**，产物不完整。
- **怎么修**：在 `prepack`/`prepare` 阶段**先构建根 git 依赖再打包**。
- **给手册的教训**：`files` 白名单 + `prepare` 构建顺序要对齐：**先 build、再 pack**，`prepare` 里做构建（`npm install` 时也会跑）。

### 坑 R15：`registry.plugin` 第三参传错 → `getOuterStack is not a function`

- **来源**：`yjh051108_dsh-routing-suite + injector/CHANGELOG.md` [0.1.0] 修复段原文：
  > `getOuterStack is not a function`：`registry.plugin` 第三参必须是函数（`() => []`），双路径修正
- **现象**：插件加载时报 `getOuterStack is not a function`。
- **根因**：编程式注册插件时 `registry.plugin(plugin, config, ???)` 的**第三参必须是函数**（返回依赖/配置数组的工厂），传了数组或 undefined 就炸。
- **怎么修**：第三参传 `() => []`。
- **给手册的教训**：用 `loader.create` / `ctx.plugin` 做运行时注入时，**第三个参数是函数**：`() => []`。这是最隐蔽的签名坑之一。

### 坑 R16：Windows 装了 WSL 时，`bash` 探测抢先命中 WSL → 构建必挂

- **来源**：`yjh051108_dsh-routing-suite + injector/CHANGELOG.md` [0.3.3] 修复段原文：
  > **findBash 拒绝 WSL**：Windows 装 WSL 时 `System32\bash.exe` 抢先 PATH 命中，构建必挂
  > （"适用于 Linux 的 Windows 子系统没有已安装的分发版"）。修复：Git/PortableGit 路径优先，
  > PATH 探测结果含 wsl 标记即拒绝
- **现象**：Windows 上一跑构建就报 `适用于 Linux 的 Windows 子系统没有已安装的分发版`。
- **根因**：`System32\bash.exe` 是 WSL 的入口，在 PATH 探测里抢先命中；WSL 没装发行版就报错。
- **怎么修**：**Git / PortableGit 的 `bash.exe` 路径优先**；PATH 探测结果里含 `wsl` 标记（或路径在 `System32` 下）就拒绝。
- **给手册的教训**：Windows 上找 `bash`，**别只信 PATH**——显式优先 `Git\bin\bash.exe` / `PortableGit`，并排除 `System32\bash.exe`。

### 坑 R17：patch 块重写“粘连” → 顶格注释错挂到上一条目

- **来源**：`yjh051108_dsh-routing-suite + injector/CHANGELOG.md` [0.3.3] 修复段原文：
  > **writePatch/extractPatchBlocks 粘连 bug（patch 串位）**：条目块后的顶格注释被并入前一块，
  > 块间重写无换行 → 注释与下一 `- id:` 粘连成一行，`disabled: true` 错挂上一条目（实测：
  > 卸载自检插件后注入器行被禁用）。修复：每块保留行尾换行、顶格注释单独成块，块间 join 不再粘连
- **现象**：卸载某个插件后，**另一个不相干的插件行被 `disabled: true` 禁用了**（自检插件被卸载 → 注入器自己那行被禁掉，注入器死了）。
- **根因**：patch 文本被切成“块”再重写时，块与块 join 没有换行；上一块末尾的顶格注释和下一块的 `- id:` 粘成一行 → 把 `disabled: true` 挂到了错误的条目上。
- **怎么修**：每块**保留行尾换行**；顶格注释**单独成块**；块间 `join` 时确保不粘连。
- **给手册的教训**：程序化改写 YAML 时，**别用字符串拼接切块**；要么用 YAML 解析器，要么每块严格带换行、注释独立成块。这坑一次就毁掉一个插件的启用状态。

### 坑 R18：官方装配不装 peers → `Cannot find package '@deepseek-ai/dsh-tools'`

- **来源**：`yjh051108_dsh-routing-suite + injector/CHANGELOG.md` [0.3.3] 修复段原文：
  > **宿主自包含打包（issue #1 根治）**：tsdown 新增 host bundle，把 `@deepseek-ai/dsh-tools` /
  > schemastery 等运行时依赖打进 `lib/index.js`——官方装配（`dsh plugin add <目录>`，link: 依赖
  > 不装 peers）不再出现 `Cannot find package '@deepseek-ai/dsh-tools'`，任何装配路径均可加载
- **现象**：用官方 `dsh plugin add <目录>` 装插件，启动报 `Cannot find package '@deepseek-ai/dsh-tools'`。
- **根因**：插件把宿主包写在 `peerDependencies` 里，以为装配时装——但官方装配对 `link:` 依赖**不装 peers**，`node_modules` 里没有 `@deepseek-ai/dsh-tools`。
- **怎么修**：用 **tsdown/bundler 把运行时依赖打进产物**（host bundle），做到“自包含”，任何装配路径都能加载。
- **给手册的教训**：插件发布给新手时，**要么把宿主依赖打进 bundle，要么确保装配器会装 peers**；否则“我本地能跑，用户装了报 Cannot find package”。这与 WeKnora 的“零运行时依赖 + 结构化类型镜像”（见模板一）是同一问题的两种解法。

### 坑 R19：staging 工具转正后 `demote` 注销不掉 → 残留

- **来源**：`yjh051108_dsh-routing-suite + injector/CHANGELOG.md` [0.1.1] 修复段原文：
  > `dev_stage_demote` 无法注销已转正工具：`dev_stage_promote` 注册改挂 `ctx.effect` 并保存 disposer，demote 时真正从正式工具集注销（此前只删 staging 条目，正式注册残留）
- **现象**：把工具“转正”后又撤回，工具仍留在正式工具集里，撤不掉。
- **根因**：转正注册没挂 `ctx.effect`、没保存 disposer，demote 时只删了 staging 记录，正式注册还留着。
- **怎么修**：转正注册改挂 `ctx.effect` 拿 disposer，demote 时调 disposer 真正注销。
- **给手册的教训**：**任何注册都要拿 disposer**（`ctx.effect(() => ctx.tools.register(...))` 的返回值就是注销函数）；删除逻辑必须真调用它。这是“注册成对”的纪律。

### 坑 R20：清单文件被半截写入毒化自动恢复 → 原子写（tmp + rename）

- **来源**：`yjh051108_dsh-routing-suite + injector/CHANGELOG.md` [0.1.1] 修复段原文：
  > registry 原子写（tmp + rename）：中断不残留半截 JSON 毒化自动恢复
- **现象**：进程被杀在写清单中途，留下半截 JSON → 下次启动“自动恢复”读到坏 JSON 直接崩。
- **根因**：直接 `writeFileSync` 目标文件，写一半中断就损坏。
- **怎么修**：**先写临时文件（`.tmp`）再 `renameSync` 覆盖**（同目录 rename 原子）。
- **给手册的教训**：任何要“下次启动还能读”的 JSON/状态文件，都用 **tmp + rename** 原子写。

### 坑 R21：悬空 junction 用 `existsSync` 判存在返回 false → symlink EEXIST

- **来源**：`yjh051108_dsh-routing-suite + injector/CHANGELOG.md` [0.2.2] 修复段原文：
  > 注入 junction 悬空重建：`existsSync` 对悬空 junction 返回 false（跟随目标）导致 symlink EEXIST——改 `lstatSync` 判断链接存在 + `rmSync` 删除重建
- **现象**：重建一个**目标已消失的 junction** 时，报 `EEXIST`（说文件已存在），但代码以为它不存在。
- **根因**：`existsSync` 会**跟随链接**；链接指向的目标没了，它就返回 `false`，于是代码走“创建”分支 → 撞上那个实际仍存在的链接 → `EEXIST`。
- **怎么修**：用 **`lstatSync`** 判断“链接本身”是否存在（不跟随），存在就 `rmSync` 删掉再建。
- **给手册的教训**：判断“链接/悬空链接是否存在”一律用 **`lstatSync`**（`existsSync` 跟随链接，答案会误导你）。与 R9 是同一根因的两面。

### 坑 R22：热重载“静默失效”——缓存丢失后自我恢复

- **来源**：`yjh051108_dsh-routing-suite + injector/CHANGELOG.md` [0.2.3] 修复段原文：
  > **自重载链路断裂根治（P0）**：缓存无匹配不再 INFO 退出——降级从磁盘 URL 直接加载（junction/urlMatch 目录的 lib/index.js），`loader.import` 重新解析磁盘填充缓存后继续重载流程。此前缓存丢失（并行 build/自检交错 purge）会让自重载/热重载直接失效，只能人工 touch/重启；现链路自愈（实测：清空缓存 → 自重载直接从磁盘加载成功，审计 `cache-miss-healed`）
- **现象**：热重载/自重载**无声失效**——看着“成功”了，其实没重载；只能手动 touch 或重启。
- **根因**：缓存里找不到匹配项就 INFO 退出；而并行 build/自检会把缓存清掉（purge），于是匹配不到。
- **怎么修**：缓存无匹配时**降级为从磁盘 URL 直接 import**（`loader.import` 会重新解析磁盘、填充缓存），再继续重载流程；并打审计 `cache-miss-healed`。
- **给手册的教训**：热重载逻辑必须处理“**缓存 miss**”分支；**别在 catch/miss 路径静默 return**，否则表现为“重载没反应”。

### 坑 R23：坏 client 插件把整个 HARNESS 拖下水 → `Failed to load plugins`

- **来源**：`yjh051108_dsh-routing-suite + injector/CHANGELOG.md` [0.3.1] 修复段原文：
  > **autoRestore 恢复前 client 校验**：坏 client 插件（缺 inject）恢复时**跳过 + 审计**（此前恢复路径无校验——坏插件在 registry → 新会话启动 → client apply 失败 → 整个 HARNESS "Failed to load plugins"——用户被迫手动修）
  > **校验正则兼容单双引号**：用户手修的双引号 `inject = ["slots"]` 被误判为"缺 inject"的 bug
- **现象**：一个新会话一启动，整个 Harness 报 `Failed to load plugins`，全盘不可用，用户只能手动去删坏插件。
- **根因**：坏 client 插件（`client` 部分缺 `export const inject`）在 registry 里，新会话启动时它的 client `apply` 失败 → 整个插件加载失败。
- **怎么修**：**恢复/注入前对 client 骨架做校验**（检查编译产物 `lib/client.js` + 是否声明 `inject`），不合格就**跳过 + 审计**而非硬上；校验正则要兼容单引号 `inject = ['slots']` 与双引号 `inject = ["slots"]`。
- **给手册的教训**：**client 插件用了 `ctx.slots` 就必须 `export const inject = ['slots']`**，否则 `cannot get property 'slots' without inject`，严重时拖垮整个 Harness。自动恢复类逻辑一定要“先校验后执行”。

### 坑 R24：卸载“无匹配”的统计口径 → 假失败刷屏

- **来源**：`yjh051108_dsh-routing-suite + injector/CHANGELOG.md` [0.2.3] 修复段原文：
  > **uninject 统计口径（压测②）**：无匹配 = no-op 幂等，既不计 ✓ 也不计 ✗（此前：早期计 ✗ 产生 9✗ 假失败；后改计 ✓ 高估成功）
- **现象**：卸载一个本来就没装的插件，本该无操作，但统计里刷出 9 个 ✗（假失败），吓到用户。
- **根因**：幂等 no-op 被计成“失败”。
- **怎么修**：no-op 归为幂等，**既不计成功也不计失败**。
- **给手册的教训**：日志/统计里 **no-op 与 failure 要分开**，否则“本该静默的幂等操作”会制造一堆假错误。

### 坑 R25：同一引导被反复注入“淤积”

- **来源**：`yjh051108_dsh-routing-suite + graded/CHANGELOG.md` [0.0.1-rc1] 原文：
  > 注入淤积根治：focus 幂等键去 status（状态抖动不再重注同名引导）；执行端续轮 followup→steer + 同 turn 60ms 引导合并（消除 next-turn 堆积）
- **现象**：同一段引导在会话里越堆越多（next-turn 堆积），模型被重复提示干扰。
- **根因**：幂等键里带了易变的 `status`，状态一抖动就被判为“新的引导”而重注；续轮用 followup 又制造新堆积。
- **怎么修**：幂等键**不含易变 status**；同 turn 内的引导**合并（60ms 窗口）**；续轮语义从 followup 改 steer。
- **给手册的教训**：往会话里注入文本时，**幂等键只用稳定字段**；同一轮多次触发要**去抖合并**。

### 坑 R26：设置写与读路径不一致 → 设置“改了不生效”

- **来源**：`yjh051108_dsh-routing-suite + graded/CHANGELOG.md` [0.0.1-rc1] 原文：
  > 概念上限动态化：loadConceptLimit 读路径对齐设置 API（此前写读不一致致设置失效）——phaseL2/焦点注入/schema 描述全随设置（实测 8 全链断言）
- **现象**：用户在设置面板改了数值，实际行为不变（设置像没保存）。
- **根因**：**写入走一个路径，读取走另一个路径**，两边对不上。
- **怎么修**：读写共用同一 API/同一路径，并加“全链断言”测试（从设置写入一直验到注入与 schema 描述）。
- **给手册的教训**：设置项的**写与读必须同一来源**；给“设置生效”写一条端到端断言测试，否则这类 bug 极难发现。

### 坑 R27：设置面板闪退 → effect 一次挂载 + 回调 ref 化

- **来源**：`yjh051108_dsh-routing-suite + graded/CHANGELOG.md` [0.0.1-rc1] 原文：
  > **设置面板闪退修复**（effect 一次挂载+回调 ref 化）
- **现象**：一打开设置面板就闪退/白屏。
- **根因**：effect 反复挂载、回调闭包捕获了旧值（stale closure），重渲染时崩。
- **怎么修**：**effect 只挂载一次**（空依赖数组），**回调 ref 化**（用 ref 持有最新回调，避免闭包捕获旧值）。
- **给手册的教训**：React 面板里，**副作用 effect 用空依赖只挂一次**，事件回调**用 ref 存最新函数**，避免 stale closure 导致的闪退。

### 坑 R28：agent preset 的 persona `complete: true` 会丢弃其它 system prompt 贡献

（与 O1 同类，此处补充 routing-suite 侧证据）

- **来源**：`yjh051108_dsh-routing-suite + docs/SPEC.md` 关于 `system-prompt/assemble` 的「性能引导契约」段（[0.3.2] 新增第 6 节）：Waterfall 必须 `await next()`、`agent` 判空、晋升从持久日志推导、只裁剪本插件工具。
- **现象**：插件往 system prompt 里加了引导，但在某些 preset 会话里**完全不出现**。
- **根因**：persona 的 `complete: true` 表示“本 persona 独占 system prompt”，会**静默丢弃**其它贡献者。
- **怎么修**：插件侧无法强制，只能**用 `system-prompt/assemble` waterfall 观察实际产出**；文档层提醒“别对 `complete:true` persona 期望自己的 system prompt 生效”。
- **给手册的教训**：system prompt 有“独占 persona”概念；插件加 system prompt 后**要实测是否被吞**，别假设一定生效。

---

# 二、可抄代码模板

> 说明：以下代码**逐字照抄**自各仓库源码快照，路径为快照绝对路径。给新手时可直接复制。
> 四个模板按“从最简单到最复杂”排序：**模板一 = 只读工具插件（推荐新手第一个照抄）** → 模板二 = 有状态服务插件 → 模板三 = UI + bundle 双声明 → 模板四 = 运行时注入器（高级）。

## 模板一：WeKnora 只读工具插件（最干净的 `defineTool` 范本）

- **快照路径**：生成期素材 `Tencent_WeKnora/packages/dsh-weknora/`（不随本 skill 发布，见 `11-glossary-and-provenance.md` §A.2）
- **为什么适合新手**：**零运行时依赖**（`dependencies` 都不需要）、不碰 UI、不写 patch 复杂结构，4 个工具全是纯只读 HTTP 调用；类型用“结构化镜像”自包含，不 import 宿主内部包，**升级 DSH 不用改代码**。
- **目录树**（实际快照文件）：

  ```
  packages/dsh-weknora/
  ├── package.json          # dsh.bundle 声明 + 零 runtime 依赖（见下）
  ├── cordis.patch.yml      # bundle 装配补丁（把本插件插入 loader）
  ├── README.md             # 英文说明（含 Compatibility 段）
  ├── README_CN.md
  ├── src/
  │   ├── index.ts          # 插件入口：name / inject / apply（63 行量级）
  │   ├── tools.ts          # 4 个工具定义（563 行，最全的 defineTool 范本）
  │   ├── client.ts         # REST 客户端 + SSE 解析（433 行）
  │   ├── config.ts         # 手写 resolveConfig()（192 行）
  │   ├── harness.ts        # 结构化类型镜像（63 行，不依赖宿主包）
  │   └── render.ts         # 工具输出的文本渲染辅助（25 行）
  ├── test/
  │   └── fixtures/api-contract.json
  └── tsconfig.build.json / tsconfig.json
  ```

- **package.json 全文（逐字照抄）**：

  ```json
  {
    "name": "@wxg-prc-cpg/dsh-weknora",
    "version": "0.1.0",
    "publishConfig": {
      "access": "public",
      "registry": "https://registry.npmjs.org/"
    },
    "description": "WeKnora knowledge retrieval tools for DeepSeek Harness (dsh): semantic search, document reading and RAG/agent answers over your own knowledge bases.",
    "keywords": [
      "dsh",
      "dsh-plugin",
      "deepseek-harness",
      "cordis",
      "weknora",
      "rag",
      "retrieval",
      "knowledge-base"
    ],
    "license": "MIT",
    "author": "WeKnora",
    "homepage": "https://github.com/Tencent/WeKnora/tree/main/packages/dsh-weknora",
    "repository": {
      "type": "git",
      "url": "git+https://github.com/Tencent/WeKnora.git",
      "directory": "packages/dsh-weknora"
    },
    "bugs": {
      "url": "https://github.com/Tencent/WeKnora/issues"
    },
    "type": "module",
    "main": "./dist/index.js",
    "types": "./dist/index.d.ts",
    "exports": {
      ".": {
        "types": "./dist/index.d.ts",
        "default": "./dist/index.js"
      },
      "./package.json": "./package.json"
    },
    "files": [
      "dist",
      "cordis.patch.yml",
      "README.md",
      "README_CN.md"
    ],
    "engines": {
      "node": ">=20.11"
    },
    "scripts": {
      "build": "tsc -p tsconfig.build.json",
      "prepare": "npm run build",
      "typecheck": "tsc -p tsconfig.json --noEmit",
      "test": "npm run build && node --test \"test/*.test.mjs\"",
      "e2e": "node test/e2e/run-in-dsh.mjs"
    },
    "dsh": {
      "bundle": {
        "patch": "./cordis.patch.yml"
      }
    },
    "devDependencies": {
      "@types/node": "^22.13.0",
      "typescript": "^5.7.3"
    }
  }
  ```
  **逐字要点（新手必看）**：① `"type": "module"` 必须有；② `exports` 里 `types` 与 `default` 都要指到编译产物；③ `files` 白名单必须包含 `cordis.patch.yml`（否则发布后没有装配补丁）；④ `dsh.bundle.patch` 指向 patch 文件；⑤ **这里没有 `dependencies`**——因为它把宿主类型做成了本地镜像（见 `harness.ts`）。

- **插件入口 `src/index.ts` 全文（逐字照抄，新手抄这个骨架）**：

  ```ts
  /**
   * dsh-weknora: a DeepSeek Harness plugin that gives the agent retrieval,
   * document reading and composed answers from a WeKnora knowledge base.
   * @module dsh-weknora
   */

  import { WeknoraClient } from './client.ts'
  import { resolveConfig } from './config.ts'
  import type { HarnessContext } from './harness.ts'
  import { createTools } from './tools.ts'

  export const name = 'dsh-weknora'

  /** Cordis waits for the tool registry before applying this plugin. */
  export const inject = ['tools'] as const

  export type { Config } from './config.ts'
  export { ConfigError, normalizeBaseUrl, resolveConfig } from './config.ts'
  export { WeknoraApiError, WeknoraClient } from './client.ts'
  export { createTools } from './tools.ts'

  /**
   * Register the configured tools. Each registration is an effect, so unloading
   * or reconfiguring the plugin withdraws the tools without a restart.
   * @param ctx - the Cordis context, with `ctx.tools` injected.
   * @param config - the plugin's `config` row; validated here so a typo fails the load.
   */
  export function apply(ctx: HarnessContext, config: unknown): void {
    const resolved = resolveConfig(config as never)
    const client = new WeknoraClient(resolved)
    const registered: string[] = []
    for (const definition of createTools(client, resolved)) {
      ctx.tools.register(definition)
      registered.push(definition.name)
    }
    ctx.logger?.info(`dsh-weknora: registered ${registered.join(', ')} against ${resolved.baseUrl}`)
  }
  ```
  **要点**：`name` / `inject` / `apply` **三个具名导出**（没有 `export default`）；配置在 `apply` 里先 `resolveConfig` 校验，**拼错立刻加载失败**（比运行到一半才报错好）。

- **`src/harness.ts` 全文（逐字照抄）——这是“不依赖宿主包”的关键**：

  ```ts
  /**
   * Structural types for the slice of the DeepSeek Harness contract this plugin
   * uses. Declaring them here keeps the package free of runtime dependencies on
   * harness internals: the shipped code only ever hands `ctx.tools.register()` a
   * plain object, so a harness release that adds optional definition fields does
   * not require a republish of this plugin.
   *
   * The shapes mirror `@deepseek-ai/dsh-tools` (`ToolDefinition`) and
   * `@deepseek-ai/dsh-llm` (`ContentBlock`, `ToolSchema`) as of dsh 0.1.0-rc.8.
   */

  /** Supported subset of JSON Schema that the harness tool registry accepts. */
  export interface JsonSchemaNode {
    type?: 'object' | 'array' | 'string' | 'number' | 'integer' | 'boolean' | 'null'
    properties?: Record<string, JsonSchemaNode>
    required?: string[]
    additionalProperties?: boolean
    items?: JsonSchemaNode
    enum?: (string | number | boolean | null)[]
    const?: string | number | boolean | null
    description?: string
    title?: string
  }

  /** Model-facing content block returned by `output.render`. */
  export interface TextContentBlock {
    type: 'text'
    text: string
  }

  /** Execution context handed to a tool body. */
  export interface ToolRunContext {
    readonly signal: AbortSignal
  }

  /** One registered model-facing tool. */
  export interface ToolDefinition {
    readonly name: string
    readonly description: string
    readonly parameters: JsonSchemaNode
    readonly output: {
      readonly schema: JsonSchemaNode
      render(args: unknown, value: unknown): TextContentBlock[]
    }
    execute(args: unknown, exec: ToolRunContext): Promise<unknown>
    readonly timeoutMs?: number
    isConcurrencySafe?(args: unknown): boolean
  }

  /** The `ctx.tools` service seam. */
  export interface ToolRegistry {
    register(definition: ToolDefinition): () => void
  }

  /** The slice of the Cordis context this plugin injects. */
  export interface HarnessContext {
    readonly tools: ToolRegistry
    readonly logger?: {
      info(...args: unknown[]): void
      warn(...args: unknown[]): void
    }
  }
  ```
  **给新手的说明**：这段不是“抄 DSH 内部”，而是**手写一份自己用到的接口**。好处：插件不 `import` 宿主包 → 不会有 R18 的 `Cannot find package`，也不用随 DSH 升级重新发布。**代价**：类型是“结构性的”，DSH 大改字段时不会报错，要靠 e2e 测试兜底。

- **最小工具范本：`list_knowledge_bases` 全文（逐字照抄，约 52 行，新手第一个工具就抄它）**
  出处：`.../dsh-weknora/src/tools.ts` 第 188–243 行。

  ```ts
  definitions.push({
    name: name('list_knowledge_bases'),
    description: 'List the WeKnora knowledge bases this deployment can retrieve from, with their ids. '
      + `${name('search')} already spans them all, so reach for this only to report what is available or to `
      + 'narrow a later search to one of them.',
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
              required: ['id', 'name', 'description'],
              additionalProperties: false,
            },
          },
        },
        required: ['count', 'knowledge_bases'],
        additionalProperties: false,
      },
      render: (_args, value) => {
        const result = value as KnowledgeBasesValue
        if (result.count === 0) return text('No knowledge base is available to this WeKnora credential.')
        const lines = result.knowledge_bases.map(kb => {
          const description = kb.description === '' ? '' : ` — ${kb.name} (id: ${kb.id})${description}`
          return `- ${kb.name} (id: ${kb.id})${description}`
        })
        return text(`${result.count} knowledge base(s):\n${lines.join('\n')}`)
      },
    },
    async execute(_args, exec): Promise<KnowledgeBasesValue> {
      const bases = await client.listKnowledgeBases(exec.signal)
      return {
        count: bases.length,
        knowledge_bases: bases.map(kb => ({
          id: typeof kb.id === 'string' ? kb.id : '',
          name: typeof kb.name === 'string' ? kb.name : '',
          description: typeof kb.description === 'string' ? kb.description : '',
        })),
      }
    },
  })
  ```
  **逐字要点**：① `parameters` 是标准 JSON Schema，对象级 `required` 数组；这里无参就写 `{ type: 'object', properties: {}, additionalProperties: false }`；② **`output.schema` 必须描述返回值结构**（模型看到的是它），`render` 把它变成给人/模型看的文本块；③ `execute` 只返回**纯数据**，把 `unknown` 逐字段收窄（`typeof x === 'string' ? x : ''`），保证输出是可序列化 JSON；④ `isConcurrencySafe: () => true` 表示只读、可并发。

## 模板二：OpenViking 记忆服务插件（`ctx.provide` + 事件钩子）

- **快照路径**：生成期素材 `volcengine_OpenViking/examples/dsh-memory-plugin/`（不随本 skill 发布）
- **为什么值得看**：它是**“有状态服务型插件”**的标准形态——`inject` 多个服务、`ctx.provide('openvikingMemory', runtime)` 暴露一个运行时可被别的插件 `ctx.get('openvikingMemory')` 取用；用 `agent/pre-step` waterfall 往会话注入上下文；用 `session/event` 捕获事件；用 `tools/pre-execute` 做工具调用守卫。
- **插件形态**：**手写 JS（`.mjs`）**，不编译、不打包，天然自包含（避免 R18）。这与模板一的 TS 编译形态是两条路线，新手可对比。
- **目录树**（实际快照文件）：

  ```
  examples/dsh-memory-plugin/
  ├── package.json          # peerDependencies + overrides + dsh.bundle
  ├── cordis.patch.yml      # group + isolate 装配
  ├── index.mjs             # 入口：name / inject / apply + 事件钩子（80 行）
  ├── config.mjs            # 手写 resolveConfig（181 行）
  ├── runtime.mjs           # 服务主体：drainer / capture / recall（436 行）
  ├── client.mjs            # OpenViking HTTP 客户端
  ├── mcp.mjs               # 挂 MCP 服务（stdio 代理）
  ├── lifecycle.mjs         # 启动 profile 注入
  ├── uri-guard.mjs         # tools/pre-execute 守卫
  ├── skills.mjs            # 挂 skills 目录
  ├── shared/
  │   ├── retryable.mjs
  │   ├── uri-guard.mjs
  │   ├── capture-utils.mjs
  │   └── mcp-proxy-core.mjs
  ├── servers/
  └── skills/
  ```

- **package.json 关键段（逐字照抄）**：
  ```json
  {
    "name": "@openviking/dsh-memory-plugin",
    "version": "0.3.1",
    "type": "module",
    "main": "index.mjs",
    "exports": { ".": "./index.mjs" },
    "dsh": {
      "bundle": {
        "patch": "./cordis.patch.yml"
      }
    },
    "scripts": {
      "check": "for f in *.mjs shared/*.mjs; do node --check \"$f\" || exit 1; done && npm run check:version",
      "check:version": "node --input-type=module -e \"import {readFileSync} from 'node:fs'; const {PLUGIN_VERSION} = await import('./config.mjs'); const v = JSON.parse(readFileSync('package.json','utf8')).version; if (PLUGIN_VERSION !== v) throw new Error('PLUGIN_VERSION ' + PLUGIN_VERSION + ' does not match package.json version ' + v);\"",
      "test": "node --test *.test.mjs",
      "prepublishOnly": "npm run check && npm test"
    },
    "peerDependencies": {
      "@deepseek-ai/dsh-llm": ">=0.1.0-rc.6 <0.2.0",
      "@deepseek-ai/dsh-mcp-client": ">=0.1.0-rc.6 <0.2.0",
      "@deepseek-ai/dsh-skill-filesystem": ">=0.1.0-rc.6 <0.2.0"
    },
    "engines": {
      "node": "^22.19.0 || >=24"
    }
  }
  ```
  **要点**：① **`check:version` 脚本**——自动断言代码里的 `PLUGIN_VERSION` 与 `package.json` 的 `version` 一致（防“改了代码忘改版本”）；② peer 范围写成区间（`>=0.1.0-rc.6 <0.2.0`，别硬钉 rc 号，见 R13）；③ `files` 白名单要包含所有 `.mjs` 与 `cordis.patch.yml`。

- **入口 `index.mjs` 全文（逐字照抄）**：

  ```js
  import { OpenVikingClient } from "./client.mjs";
  import { resolveConfig } from "./config.mjs";
  import { injectStartupProfile } from "./lifecycle.mjs";
  import { mountOpenVikingMcp } from "./mcp.mjs";
  import { OpenVikingRuntime } from "./runtime.mjs";
  import { mountOpenVikingSkills } from "./skills.mjs";
  import { guardVikingUri } from "./uri-guard.mjs";

  export const name = "openviking-memory";
  export const inject = ["agents", "sessions", "tools"];

  export function apply(ctx, input = {}) {
    const config = resolveConfig(input);
    const client = new OpenVikingClient(config);
    const runtime = new OpenVikingRuntime(client, config, ctx.logger);
    const skipMemory = session => (
      config.skipSubagentSessions && session?.header?.origin === "subagent"
    );
    ctx.provide("openvikingMemory", runtime);
    ctx.effect(
      () => () => runtime.disposeAll(),
      "openvikingMemory.disposeAll()",
    );
    // The pending-queue drainer is the in-process recovery path: without it a
    // single transient write failure latches capture/commit until the next dsh
    // restart. Started here so every session shares one single-flight drainer.
    runtime.startDrainer();
    ctx.effect(
      () => () => runtime.stopDrainer(),
      "openvikingMemory.stopDrainer()",
    );

    ctx.on("agent/session-start", ({ agent }) => {
      if (skipMemory(agent.session)) return false;
      agent.ctx.effect(
        () => () => runtime.dispose(agent.session),
        "openvikingMemory.disposeSession()",
      );
      return injectStartupProfile(agent, runtime);
    });

    // prepend: downstream waterfall listeners run first, so this plugin sees
    // the final claimed batch and appends after every other contributor.
    // Profile + recall are independent after `next()`; run them concurrently so
    // the agent/pre-step waterfall (which currently gates user/message push in
    // dsh-agent-loop) spends less wall time (#4515).
    ctx.on("agent/pre-step", async ({ agent, messages, signal }, next) => {
      const decision = await next();
      if (skipMemory(agent.session)) return decision;
      if (decision.kind !== "enter" || signal.aborted) return decision;
      const [profile, recall] = await Promise.all([
        runtime.profileMessage(agent),
        runtime.recallMessage(agent, decision.messages),
      ]);
      if (signal.aborted) return decision;
      const additions = [profile, recall].filter(Boolean);
      return additions.length > 0
        ? { kind: "enter", messages: [...decision.messages, ...additions] }
        : decision;
    }, { prepend: true });

    ctx.on("session/event", (session, event) => {
      if (skipMemory(session)) return;
      runtime.capture(session, event);
      runtime.maybeCommit(session, event);
    });

    ctx.on("session/flush", async session => {
      if (skipMemory(session)) return;
      await runtime.flush(session);
    });

    ctx.on("tools/pre-execute", guardVikingUri);

    // Mounted last, and deliberately not awaited: the bridge's apply blocks on
    // its first tools/list, so a server that accepts the connection but never
    // answers would otherwise hold up every registration above it.
    mountOpenVikingMcp(ctx, config);
    mountOpenVikingSkills(ctx);
  }
  ```
  **逐字要点（每条都是踩坑后的写法）**：
  ① `ctx.provide("openvikingMemory", runtime)` 把服务暴露出去——别的插件能 `ctx.get('openvikingMemory')`。
  ② 资源注册**全部挂 `ctx.effect`**：`ctx.effect(() => () => runtime.disposeAll(), '标签')`，第二个参数是**给人看的标签**（dispose 时能对上是哪个资源）。这是 R19/R23 的根治写法。
  ③ `agent/pre-step` 用 **`{ prepend: true }`** + **先 `await next()` 再追加**：这样本插件是“最后说话的人”，追加在所有人之后（waterfall 顺序坑）。
  ④ `prepend: true` 时下游先跑，所以必须 `const decision = await next()` **拿到最终结果**再改，不能凭空造。
  ⑤ 每次都判 `signal.aborted`，`Promise.all` 并发跑 profile+recall（性能）。
  ⑥ `mountOpenVikingMcp` **故意不 await**：它的 `apply` 会阻塞在第一次 `tools/list` 上，一个“连上了但不回话”的服务器会卡住上面所有注册（见 O2）。

## 模板三：modlens 插件（`dsh.bundle` + `dsh.client` 双声明）

- **快照路径**：生成期素材 `liustack_modlens/`（不随本 skill 发布）
- **为什么值得看**：它是**“既有命令行、又有 DSH 插件、还有前端 UI 面板”**的复杂项目；`dsh` 字段**同时声明 bundle 与 client**；插件代码放在 `dsh/` 子目录、用 `exports` 映射，`bin` 仍是 CLI。
- **目录树（DSH 相关部分）**：

  ```
  liustack_modlens/
  ├── package.json          # dsh.bundle + dsh.client 双声明；exports 映射到 dsh/
  ├── cordis.patch.yml      # 插入 modlens 行
  ├── dsh/
  │   ├── index.js          # 插件主逻辑（后端，2199 行）
  │   ├── client.js         # 前端 UI 面板（51KB，client 入口）
  │   ├── vision-schema.json# 工具 output.schema（纯 JSON，见下）
  │   ├── spawnHidden.js    # Windows 隐藏子进程黑框（小而复用的范本）
  │   └── spawnHidden.d.ts
  ├── dist/                 # CLI 构建产物（bin 指向这里，与插件无关）
  ├── docs/
  │   └── troubleshooting.zh-CN.md   # 逐条报错排查（248 行）
  └── skills/modlens/       # 随插件分发的 skill
  ```

- **package.json 关键段（逐字照抄）**：
  ```json
  {
    "name": "@liustack/modlens",
    "version": "3.26.1",
    "type": "module",
    "bin": {
      "modlens": "./dist/main.js"
    },
    "files": [
      "dist",
      "docs",
      "skills/modlens/SKILL.md",
      "skills/modlens/scripts",
      "skills/modlens/references",
      "CHANGELOG.md",
      "SECURITY.md",
      "dsh",
      "cordis.patch.yml"
    ],
    "exports": {
      ".": "./dsh/index.js",
      "./dsh": "./dsh/index.js",
      "./package.json": "./package.json",
      "./client": "./dsh/client.js"
    },
    "dsh": {
      "bundle": {
        "patch": "./cordis.patch.yml"
      },
      "client": {
        "inject": [],
        "platform": "web",
        "immediately": true
      }
    }
  }
  ```
  **要点**：① `exports["."]` 指向插件入口 `./dsh/index.js`，`bin` 仍指向 CLI 的 `./dist/main.js`——**两种形态共存**；② `dsh.client.inject` 为空数组（本插件 UI 不依赖特定宿主服务），若用了 `ctx.slots` 必须写 `["@deepseek-ai/dsh-client-ui-slots"]` 之类（见 R23）；③ `platform: "web"`；④ `immediately: true` 表示 client 立即挂载。

- **`cordis.patch.yml` 全文（逐字照抄）**：
  ```yaml
  # dsh bundle layer: mount the modlens vision plugin (dsh/index.js via the
  # package root export; bin stays the CLI, nothing imports the root otherwise).
  - insert:
      - id: modlens
        name: '@liustack/modlens'
  ```
  **要点**：**顶层是单个数组**、`- insert:` 下再 `- id:`；entry 的 `id` 是主键（重复即崩，见 R4）；`name` 用 npm 包名，不用相对路径。

- **`dsh/spawnHidden.js` 全文（逐字照抄）——Windows “黑框”问题的通用小工具**：
  ```js
  // The only place this plugin starts a child process.
  //
  // The desktop app has no console of its own, so on Windows every child it
  // starts would be given one and shown its window: a black box per read
  // (issue #60). `windowsHide` suppresses that, defaults to false in Node, and is
  // ignored elsewhere.
  //
  // It lives in a file of its own, apart from its callers, so the rule can be
  // checked by looking at which files reach `child_process` at all rather than at
  // what each call passes. A call site cannot forget an option it never writes,
  // and writing the option after the caller's leaves nothing to override it.
  //
  // The core has its own copy in src/util/spawnHidden.ts. The duplication is on
  // purpose: this plugin ships as a unit and must not import from the CLI it
  // drives.
  import { spawn } from 'node:child_process'

  export function spawnHidden(command, args, options) {
    return spawn(command, args, { ...options, windowsHide: true })
  }
  ```
  **给手册的教训**：Windows 桌面上任何 `spawn`/`exec` 都要 `windowsHide: true`，否则**每次调用弹一个黑框**。把这件事**收进唯一一个函数**，别人就没法忘（见 M8）。

- **工具 `output.schema` 用独立 JSON 文件（逐字照抄一段）**：
  modlens 把输出的 JSON Schema 单独放 `dsh/vision-schema.json`，运行时读入。字段形态与 WeKnora 一致：对象级 `required` 数组、属性级只有 `type`/`description`/`items`/`properties`/`required`，**属性级不允许 `required: true`**（见 R1）。
  ```json
  {"type":"object","properties":{"summary":{"type":"string"},"ocr":{"type":"object","properties":{"full_text":{"type":"string"},"lines":{"type":"array","items":{"type":"object","properties":{"text":{"type":"string"},"language":{"type":"string"}},"required":["text"]}}},"required":["full_text","lines"]}},"required":["summary","ocr"]}
  ```
  （上面为便于阅读截取了 `summary`/`ocr` 两段；完整文件在 `.../dsh/vision-schema.json`。）

## 模板四：routing-suite 运行时注入器（bundle + client + 事件拦截 + 运行时注入）

- **快照路径**：生成期素材 `yjh051108_dsh-routing-suite/injector/`（不随本 skill 发布）
- **为什么值得看**：这是**高级形态全家桶**——`bundle` + `client` 双声明、`ctx.webServer.register` 起 HTTP API、`ctx.on('llm/stream')` 拦截模型路由、`ctx.slots.inject` 挂 UI 面板、并用 `loader.create` **运行时注入其它插件**。
- **它自带的“教学模板”**：仓库里有个 `dev_scaffold_plugin` 工具，会**生成新手骨架代码**。下面是它生成的两个骨架（逐字照抄），可直接当新手模板。

- **injector 的 package.json 关键段（逐字照抄）**：
  ```json
  {
    "name": "@dsh-external/dsh-super-injector",
    "version": "0.3.3",
    "type": "module",
    "main": "./lib/index.js",
    "types": "./lib/types/index.d.ts",
    "exports": {
      ".": {
        "types": "./lib/types/index.d.ts",
        "default": "./lib/index.js"
      },
      "./client": {
        "types": "./lib/types/client/index.d.ts",
        "default": "./lib/client.js"
      },
      "./package.json": "./package.json"
    },
    "files": [
      "lib",
      "cordis.patch.yml",
      "scripts/build.sh",
      "scripts/fix-patch.mjs",
      "scripts/prepare.mjs"
    ],
    "dsh": {
      "bundle": {
        "patch": "./cordis.patch.yml"
      },
      "client": {
        "inject": [
          "@deepseek-ai/dsh-client-runtime",
          "@deepseek-ai/dsh-client-ui-slots"
        ],
        "platform": "web"
      }
    },
    "peerDependencies": {
      "@deepseek-ai/dsh-tools": ">=0.0.1-rc <2",
      "cordis": ">=4.0.0-rc <5",
      "schemastery": "^3.18.0"
    }
  }
  ```
  **要点**：① 有 client 时，`exports` 要额外暴露 `./client`（指向编译出来的 `lib/client.js`）；② `type` 的 `types` 指到 `lib/types/...`；③ `peerDependencies` 用**范围**（`>=0.0.1-rc <2`）而非钉死（见 R13）；④ `files` 要带上构建脚本，否则从 tgz 装时没法构建。

- **生成器里的“工具包形态”骨架（逐字照抄，最短的完整插件）**：
  ```ts
  /**
   * ${pkgName} — 工具包形态（由 dev_scaffold_plugin 生成）。
   * 规范：资源注册必须挂 ctx.effect（热重载/卸载自动清理——注入器踩坑记录）。
   */
  import type { Context } from 'cordis'
  import { defineTool } from '@deepseek-ai/dsh-tools'
  import z from 'schemastery'

  export const name = ${JSON.stringify(pkgName)}
  export const inject = ['tools']

  export interface Config {
    greeting: string
  }

  export const Config = z.object({
    greeting: z.string().default('你好'),
  })

  export function apply(ctx: Context, config: Config): void {
    // 工具注册（ctx.effect：fiber dispose 自动注销）
    ctx.effect(() => ctx.tools.register(defineTool({
      name: '${pkgName}_hello',
      description: '示例工具',
      parameters: {
        name: { type: 'string', required: true, description: '谁' },
      },
      output: {
        schema: { type: 'string' },
        render: (_args, value) => [{ type: 'text', text: String(value) }],
      },
      async execute(args) {
        return config.greeting + '，' + args.name + '！'
      },
    })), '${pkgName}: hello tool')
  }
  ```
  **⚠️ 重要提醒（见坑 R1）**：这个官方骨架里 `parameters` 用了**属性级 `required: true`**（`name: { type: 'string', required: true }`），但 DSH 工具 schema 实际要求的是**对象级 `required` 数组**：
  ```ts
  parameters: {
    type: 'object',
    properties: { name: { type: 'string', description: '谁' } },
    required: ['name'],
    additionalProperties: false,
  },
  ```
  **🔴 本句已被 R1 顶部校正推翻**：走官方 `defineTool()` 时，**属性级 `required: true`（第一种写法）才是正确的**；第二种（对象级 `required` 数组）只适用于裸 `register` + 原始 JSON Schema。详见 R1 顶部「重要校正」。

- **“注册守卫”写法（逐字照抄）——冲突不崩、失败降级**：
  出处：`injector/src/index.ts` 第 2356–2366 行。

  ```ts
  // ⚠️ 必须挂 ctx.effect（自己的踩坑记录自己遵守）：裸注册在 fiber 卸载
  // （自重载 dispose/卸载）时不注销 → 残留工具闭包捕获旧 fiber 状态
  // （selfReloading 等）→ 新实例注册撞 duplicate 被跳过 → 跑的是「僵尸
  // 工具的僵尸闭包」（实测：锁永久卡死、新代码永不生效的根因）。
  function safeRegister(tool: any): void {
    try {
      ctx.effect(() => ctx.tools.register(tool), `dsh-super-injector: ${tool.name ?? 'tool'}`)
    } catch (e) {
      logger.warn('[super-injector] 跳过冲突工具注册: %s', e instanceof Error ? e.message : String(e))
    }
  }
  ```
  **要点**：① 注册一律包在 `ctx.effect` 里 + 带标签；② 用 `try/catch` 把“重名冲突”降级为 warn，**不让一个工具注册失败拖垮整个插件**。

- **拦截点 1：`llm/stream` waterfall（捕获/改写模型调用）**：

  ```ts
  // 观察面：捕获主模型路由（waterfall 必须 next() 委托）
  ctx.on('llm/stream', (options, next) => {
    lastRoute = { provider: options.provider, model: options.model }
    return next()
  })
  ```
  **要点**：waterfall 里**必须调用并返回 `next()`**，否则后续监听者和真正的 LLM 调用都被你“吃掉”。

- **拦截点 2：`ctx.webServer.register`（给插件开 HTTP API）**：
  出处：`injector/src/index.ts` 第 3281 行起。

  ```ts
  ctx.effect(() => ctx.webServer.register({
    kind: 'prefix',
    path: '/super-injector/api',
    handler: async (req: any, res: any) => {
      const send = (code: number, obj: unknown): void => {
        res.writeHead(code, { 'content-type': 'application/json; charset=utf-8' })
        res.end(JSON.stringify(obj))
      }
      try {
        const url = new URL(req.url ?? '/', 'http://localhost')
        const path = url.pathname.replace(/^\/super-injector\/api/, '') || '/'
        if (req.method === 'GET' && path === '/list') {
          const entries = readRegistry().map((e) => ({ ...e, active: hasActiveEntry(e.name) }))
          return send(200, { ok: true, entries, stats: opStats })
        }
      } catch (e) {
        send(500, { ok: false, error: String(e) })
      }
    },
  }))
  ```
  **要点**：① `kind: 'prefix'` + `path` 前缀路由；② 注册也挂 `ctx.effect`（热重载时路由自动摘，免 `duplicate route`）；③ 中文响应要写 `charset=utf-8`。

- **拦截点 3：`ctx.slots.inject` 挂 UI 面板（含两个必坑注释）**：
  出处：`SCAFFOLD_UI_CLIENT` 生成模板。

  ```ts
  /**
   * ${pkgName} — client 面板（conversation.view slot）。
   * 构建：npm run build:client（tsdown，产物 lib/client.js，ModuleLoader.load 注册）。
   * ⚠️ 两个必坑（2026-08 实测）：① apply 用 ctx.slots 必须 export const inject
   * = ['slots']（服务注入声明）；② register 必须带 name 字段（= slot 名，
   * 如 conversation.view）——缺 name 报 "slot undefined is not declared"。
   */
  import type { SlotsService } from '@deepseek-ai/dsh-client-ui-slots'

  type ClientContext = {
    slots: SlotsService
  }

  export const inject = ['slots']

  export function apply(ctx: ClientContext): void {
    ctx.effect(() => ctx.slots.inject('conversation.view', () =>
      ctx.slots.register({
        name: 'conversation.view',
        id: '${pkgName}-panel',
        label: () => ${JSON.stringify(pkgName)},
        component: () => ({
          render() {
            const el = document.createElement('div')
            el.textContent = ${JSON.stringify(pkgName)} + ' 面板'
            el.style.padding = '12px'
            el.style.fontFamily = 'monospace'
            return el
          },
        }),
      }),
    ), '${pkgName}: panel')
  }
  ```
  **要点**：① client 侧 `export const inject = ['slots']` **必须写**（否则 `cannot get property 'slots' without inject`，见 R23）；② `register` 的 `name` 字段 = slot 名，**缺了报 `slot undefined is not declared`**；③ `component` 形态随槽位不同：`conversation.view` 可用 `() => ({ render() {} })` 返回 DOM，而 **`settings.section` 必须返回 React 元素**（见 R10）。

---

# 三、该方向的开发规范（仅在多家共识时归纳）

> 归纳原则：下面每一条**至少两家独立仓库/文档**做法一致，且给出可核对的文件出处。只有一家这么做、或只是文档声称的，一律标“单一来源/未验证”，不当“规范”。

## 规范 1：函数式插件必须具名导出 `name` / `inject` / `apply`，**禁止 default export**

- **共识证据**：
  - WeKnora `src/index.ts`：`export const name = 'dsh-weknora'`、`export const inject = ['tools'] as const`、`export function apply(ctx, config)`（无 default）。
  - OpenViking `index.mjs`：`export const name = "openviking-memory"`、`export const inject = ["agents","sessions","tools"]`、`export function apply(ctx, input = {})`。
  - injector `SCAFFOLD_TOOLKIT`：`export const name = ...`、`export const inject = ['tools']`、`export function apply(...)`。
  - modlens `dsh/index.js`（grep 见 `export const name`/`apply`）。
- **要点**：`inject` 声明你依赖的服务（`tools`/`agents`/`sessions`/`llm`/`slots`/`timer`/`systemPrompt`…），Cordis **等这些服务就绪后才 apply**；用了某服务却没在 `inject` 声明，会报 `cannot get property 'X' without inject`（见 R23）。

## 规范 2：一切资源注册必须挂 `ctx.effect`，并保存 dispose

- **共识证据**：
  - injector `injector/CHANGELOG.md` [0.1.0]：明确要求“插件把资源注册挂 `ctx.effect`”，并把它写成**强制登记守卫**（发现裸注册即报错）。
  - OpenViking `index.mjs`：`ctx.provide`、`stopDrainer`、`disposeSession` 全部包 `ctx.effect`。
  - injector `SCAFFOLD_TOOLKIT`：注释“资源注册必须挂 ctx.effect（热重载/卸载自动清理）”。
  - WeKnora `index.ts` 注释：“Each registration is an effect, so unloading or reconfiguring the plugin withdraws the tools without a restart.”（`ctx.tools.register` 返回 disposer）。
- **要点**：裸注册（直接 `ctx.tools.register(x)` 不挂 effect）在热重载/卸载时**不注销**，导致 `duplicate`、僵尸闭包（见 R2/R19）。

## 规范 3：`package.json` 要有 `dsh.bundle.patch`，`files` 白名单必须含 patch 与产物

- **共识证据**：
  - WeKnora `dsh: { bundle: { patch: "./cordis.patch.yml" } }`；`files` 含 `dist`、`cordis.patch.yml`。
  - OpenViking 同上，`files` 含全部 `.mjs` 与 `cordis.patch.yml`。
  - modlens `dsh` 同时含 `bundle` 与 `client`；`files` 含 `dsh`、`cordis.patch.yml`。
  - injector `dsh` 同时含 `bundle` 与 `client`；`files` 含 `lib`、`cordis.patch.yml`、`scripts/*`。
- **要点**：漏了 `cordis.patch.yml` 进 `files` → 发布后用户装了但**没有装配补丁**；漏了构建脚本 → 从 tgz 装时建不了依赖（见 R14、[0.2.4]）。

## 规范 4：`cordis.patch.yml` 顶层是**单个数组**，entry 靠 `id` 唯一

- **共识证据**：
  - modlens：顶层 `- insert:` → `- id: modlens`。
  - injector 根 patch：顶层 `- insert:` → `- id: dsh-super-injector`。
  - injector `writePatch` 文档：坚持“顶层 `[]` 兼容 + 幂等”，杜绝“YAML 双顶层值”（见 R3/R4）。
- **要点**：`id` 是主键，**重复即启动崩**（`duplicate loader entry id`，见 R4）；**不要盲目 append** 到顶层，否则出现两个顶层数组（YAML 解析失败）。

## 规范 5：工具 schema 有两套写法 —— **先定路径，再定 `required` 位置**（⚠️ 原结论已按官方源码校正）

- **路径 A · `defineTool()`（官方自研插件全走这条）**：`parameters` / `output.schema` 是 **DSH 作者 DSL**，必填一律**属性级** `required: true`。
  - 证据：官方 `packages/interaction/tool-ask-user/src/index.ts`；官方 `packages/core/tools/src/schema.ts:570-571`（`parameterSchemaSpecToJsonSchema(options.parameters)`）。
- **路径 B · 手写 `ToolDefinition` 后 `register`（社区插件常走这条）**：`parameters` 是**原始 JSON Schema**，必填为**对象级** `required: ['a','b']`。
  - 证据：本次实测 `Tencent_WeKnora/packages/dsh-weknora/src/tools.ts:186` —— `const definitions: ToolDefinition[] = []`，随后 push 裸对象，`parameters: { type:'object', properties:{...}, required:['query'], additionalProperties:false }`（第 251-259 行）；`output.schema` 同理（第 194、211-216 行）。
- **共识证据（路径 B 内部）**：
  - WeKnora `tools.ts` 全部 4 个工具：`parameters` 与 `output.schema` 都是对象级 `required` 数组 + `additionalProperties:false`。
  - modlens `vision-schema.json`：对象级 `required` 数组，属性级只有 `type`/`description`/`properties`/`items`/`required`。
  - `graded/src/tools.js` 注释明确“属性级不允许 `required` 键”。**⚠️ 该注释只适用于路径 B；路径 A（`defineTool`）下属性级 `required: true` 才是正确写法（见 R1 顶部校正）。**
- **两条路径都能用，但绝不可混**。新手建议：**选路径 A（`defineTool`）**，因为它自带参数校验（`validateJsonSchemaValue`）、类型推导（`InferArgs<S>`）和更友好的报错。
- **不要**把路径 A 的 DSL 当成"标准 JSON Schema"来理解：它的根是**隐式开放对象**（直接铺属性名，不用写 `type:'object'`/`properties`），且作者**不允许**写对象级 `required` 数组（写了会报 `required must be true when present`）。

## 规范 6：`peerDependencies` 用版本**范围**；宿主依赖要么打进 bundle、要么完全不依赖

- **共识证据**：
  - injector：`"@deepseek-ai/dsh-tools": ">=0.0.1-rc <2"`、`"cordis": ">=4.0.0-rc <5"`；并用 tsdown host bundle 自包含（[0.3.3]，见 R18）。
  - OpenViking：`">=0.1.0-rc.6 <0.2.0"`。
  - WeKnora：**零 runtime 依赖**，类型自镜像。
- **要点**：钉死 rc 号会在 DSH 升级后报废（见 R13）；官方 `dsh plugin add <目录>` 对 `link:` 依赖**不装 peers**（见 R18）。

## 规范 7：waterfall 事件（`agent/pre-step`、`system-prompt/assemble`、`llm/stream`）必须 `await next()` / `return next()`

- **共识证据**：
  - OpenViking `index.mjs`：`agent/pre-step` 里 `const decision = await next()`，`llm/stream` 注释亦要求委托。
  - injector `SCAFFOLD_TOOLKIT` 与 `docs/SPEC.md` 第 6 节：“Waterfall 必须 `await next()`、`agent` 判空、晋升从持久日志推导、只裁剪本插件工具”。
- **要点**：不 `next()` = 吃掉后续所有监听者与真实调用；`{ prepend: true }` 表示“最后说话”，需先 `await next()` 拿最终结果再改。

## 规范 8：存盘/配置路径以 `DSH_HOME` 为准，别硬编码 `~/.dsh`

- **共识证据**：
  - injector [0.3.3]：“DSH_HOME 优先（homedir 错家）”，scaffold 模板同步（见 R5）。
  - injector `SCAFFOLD_DAEMON`：`const dshHome = process.env.DSH_HOME || join(homedir(), '.dsh')`。
  - `graded/src/index.js`：`stateFile` 同规则。
- **要点**：web 进程的 `homedir()` 与 `DSH_HOME` 可能不一致（服务账户/跨用户部署），硬编码会把文件写到错误位置。

## 规范 9（强共识）：工具 = `parameters`（输入 schema）+ `output.schema/render`（输出）+ `execute`（纯数据）

- **共识证据**：WeKnora 全部 4 个工具、modlens（`vision-schema.json` + `render`）、injector 全部 `dev_*` 工具，形态一致。
- **要点**：`execute` 只返回**可序列化的纯数据**；面向模型的文本在 `render` 里生成。

## 规范 10（两家，写法二选一）：配置校验用 schemastery `Config` 或手写 `resolveConfig`

- **共识证据**：
  - 用 schemastery：injector（`import z from 'schemastery'` + `export const Config = z.object({...})`）、injector scaffold。
  - 手写：WeKnora `config.ts` 的 `resolveConfig()`（收集所有错误一次性报）、OpenViking `config.mjs` 同理。
- **要点**：两种都行；关键是**在 `apply` 入口就校验**，拼错字段要“加载即失败”，别拖到运行中。

## 明确“**未找到共识**”的项（不要当规范写）

- 插件目录用 `src/`（TS 编译，WeKnora/injector）还是根目录 `.mjs`（OpenViking）还是 `dsh/`（modlens）——**三种并存，无共识**。
- 构建工具：WeKnora 用 `tsc`；injector/modlens 用 `tsdown`/`vite`——**无共识**。
- 是否要 client 面板：WeKnora/OpenViking 无 client，modlens/injector 有——**按需**。

---

# 四、新手最容易卡住的 5 个点（每条一句可执行建议）

1. **插件“装上了但没反应 / 工具找不到”** → 先查 `package.json` 有没有 `dsh.bundle.patch` 且 `files` 里带了 `cordis.patch.yml`，再查 patch 顶层是不是**单个数组**、`id` 有没有和别的 entry 重名。（依据：R3、R4、规范 3/4）
2. **`duplicate` / `already registered` / 热重载后跑旧代码** → 把所有注册（工具、路由、服务）**包进 `ctx.effect` 并保存返回值**，卸载时真调用它；不要“裸注册”。（依据：R2、R19、规范 2）
3. **工具一调用就报 schema 错 / 模型看不到工具** → `parameters` 用**对象级 `required` 数组 + `additionalProperties: false`**，别在属性里写 `required: true`；`output.schema` 必须完整描述 `execute` 的返回值。（依据：R1、规范 5/9）
4. **`cannot get property 'X' without inject` / 面板白屏** → 用了哪个服务就在插件里 `export const inject = ['X']`（UI 用 `ctx.slots` 就写 `['slots']`），`register` 记得带 `name` 字段；`settings.section` 的 `component` 必须**返回 React 元素**。（依据：R10、R23、模板四）
5. **本地能跑、发布/换机就崩** → `peerDependencies` 写**范围**不钉 rc 号；宿主依赖要么**打进 bundle**、要么像 WeKnora 一样用**结构化类型镜像做到零依赖**；路径一律以 `process.env.DSH_HOME || ~/.dsh` 派生。（依据：R5、R13、R18、规范 6/8）

---

# 五、附录：目录树汇总、坑位统计与来源索引

## 附录 A：四个仓库的完整目录树（实际快照）

### A1. WeKnora · `@wxg-prc-cpg/dsh-weknora`（工具插件，最干净）

```
packages/dsh-weknora/
├── .gitignore
├── README.md / README_CN.md
├── contract/contract_test.go
├── cordis.patch.yml
├── package.json / package-lock.json
├── src/
│   ├── client.ts        # REST + SSE
│   ├── config.ts        # 手写 resolveConfig
│   ├── harness.ts       # 结构化类型镜像（零依赖关键）
│   ├── index.ts         # name / inject / apply
│   ├── render.ts        # 文本渲染辅助
│   └── tools.ts         # 4 个 defineTool
├── test/
│   ├── client.test.mjs / config.test.mjs / contract.test.mjs / tools.test.mjs
│   ├── e2e/fake-model.mjs / e2e/run-in-dsh.mjs
│   ├── fixtures/api-contract.json
│   └── helpers/json-schema.mjs / helpers/mock-weknora.mjs
└── tsconfig.json / tsconfig.build.json
```

### A2. OpenViking · `@openviking/dsh-memory-plugin`（手写 .mjs 服务插件）

```
examples/dsh-memory-plugin/
├── README.md
├── cordis.patch.yml
├── package.json / package-lock.json
├── index.mjs            # 入口：provide + 事件钩子
├── config.mjs / client.mjs / runtime.mjs
├── capture.mjs / lifecycle.mjs / mcp.mjs / skills.mjs / uri-guard.mjs
├── servers/mcp-proxy.mjs
├── shared/
│   ├── capture-utils.mjs / credentials.mjs / debug-log.mjs
│   ├── input-filters.mjs / mcp-proxy-config.mjs / mcp-proxy-core.mjs
│   ├── pending-queue.mjs / profile-inject.mjs
│   ├── recall-compress-core.mjs / recall-core.mjs / retryable.mjs
│   ├── session-model.mjs / uri-guard.mjs
│   └── workspace-identity.mjs / workspace-peer.mjs
├── skills/openviking-memory/SKILL.md
└── *.test.mjs（index/config/runtime/mcp/capture/lifecycle/skills/uri-guard/live-recall/pending-queue/runtime-drain/bundle）
```

### A3. modlens · `@liustack/modlens`（bundle + client 双声明）

```
liustack_modlens/
├── package.json / cordis.patch.yml
├── dsh/
│   ├── index.js            # 后端插件（2199 行）
│   ├── client.js           # 前端 UI（client 入口，51KB）
│   ├── vision-schema.json  # output.schema（纯 JSON）
│   ├── spawnHidden.js / spawnHidden.d.ts
├── dist/                   # CLI 产物（bin）
├── docs/（含 troubleshooting.zh-CN.md 248 行、harness-setup.zh-CN.md、output-schema.md）
├── skills/modlens/...
├── assets/ / evals/ / scripts/
└── CHANGELOG.md / SECURITY.md / AGENTS.md
```

### A4. routing-suite · `@dsh-external/dsh-super-injector`（运行时注入器）

```
yjh051108_dsh-routing-suite/
├── package.json / cordis.patch.yml / install.ps1 / install.sh
├── .gitattributes / README.md / README.en.md / LICENSE
├── docs/FLATTEN-MIGRATION.md
├── test/root-package-prepare.test.mjs
├── scripts/install-injector.ps1
├── injector/            # 插件本体（bundle + client）
│   ├── package.json / cordis.patch.yml / CHANGELOG.md / INSTALL.md / README.md
│   ├── docs/SPEC.md
│   ├── src/index.ts（3323 行）/ src/client/index.ts（181 行）
│   ├── scripts/build.sh / prepare.mjs / fix-patch.mjs
│   └── lib/（构建产物：index.js / client.js / types/）
├── graded/             # 预设/工具示例（bundle 插件）
│   ├── package.json / cordis.patch.yml / dsh.plugin.json
│   ├── src/index.js / src/tools.js（521 行）/ src/inject-text.js / src/mode-state.js
│   └── lib/ / client/ / docs/ / tests/ / scripts/
└── preset/            # agent preset（不是插件！）
    ├── package.json / README.md / AGENTS.md / CHANGELOG.md
    ├── router-react/ / router-spec/ / router-standard/（*.mjs + preset.yml + agent.cordis.yml）
    └── router.test.mjs / router.integration.test.mjs
```

## 附录 B：四仓库坑位统计（本次实际挖到）

| 仓库 | 坑编号 | 数量 | 最主要的 3 个 |
|---|---|---|---|
| WeKnora | W1–W4 | 4 | W1 无 scope 检索不透明 400；W2 `resource://` 渲染 + 403 降级记忆；W3 SSE 截断当完整答案 |
| OpenViking | O1–O10 | 10 | O1 persona `complete:true` 吞 system prompt；O2 直连 `/mcp` 卡死 `tools/list`；O8 Electron `process.execPath` |
| modlens | M1–M10 | 10 | M1 缺 `dsh.bundle` + pnpm 冷静期；M2 工具名撞 scoped 层被遮蔽；M8 Windows 黑框 |
| routing-suite | R1–R28 | 28 | R1 属性级 `required` 不允许；R4 `duplicate loader entry id` 启动即崩；R18 官方装配不装 peers |

**总计 52 条**（WeKnora 4 + OpenViking 10 + modlens 10 + routing-suite 28）。

## 附录 C：本次实际读取的源码/文档文件（去重后清单，供复核）

- **WeKnora**：`package.json`、`src/index.ts`、`src/tools.ts`、`src/client.ts`、`src/config.ts`、`src/harness.ts`、`src/render.ts`、`cordis.patch.yml`、`README.md`、`test/fixtures/api-contract.json`、根 `.github/workflows/dsh-plugin.yml`（约 11 个）
- **OpenViking**：`package.json`、`index.mjs`、`config.mjs`、`runtime.mjs`、`mcp.mjs`、`lifecycle.mjs`、`uri-guard.mjs`、`shared/retryable.mjs`、`shared/uri-guard.mjs`、`shared/capture-utils.mjs`、`shared/mcp-proxy-core.mjs`、`cordis.patch.yml`、`README.md`、`docs/zh/agent-integrations/17-dsh.md`（约 14 个）
- **modlens**：`package.json`、`cordis.patch.yml`、`AGENTS.md`、`docs/troubleshooting.zh-CN.md`、`docs/harness-setup.zh-CN.md`、`docs/output-schema.md`、`CHANGELOG.md`、`dsh/index.js`、`dsh/client.js`、`dsh/spawnHidden.js`、`dsh/vision-schema.json`（约 11 个）
- **routing-suite**：`injector/package.json`、`injector/cordis.patch.yml`、`injector/src/index.ts`、`injector/src/client/index.ts`、`injector/docs/SPEC.md`、`injector/CHANGELOG.md`、`graded/package.json`、`graded/cordis.patch.yml`、`graded/dsh.plugin.json`、`graded/src/tools.js`、`graded/src/index.js`、`graded/CHANGELOG.md`、`package.json`、`cordis.patch.yml`（约 14 个）

**四仓库合计约 50 个文件**（另含 git 提交元数据查询若干次）。

## 附录 D：结论来源索引（按坑号反查）

- W1–W4 → `src/Tencent_WeKnora/packages/dsh-weknora/**`（tools.ts / client.ts / .github/workflows）
- O1–O10 → `src/volcengine_OpenViking/examples/dsh-memory-plugin/**` + `docs/zh/agent-integrations/17-dsh.md`
- M1–M10 → `src/liustack_modlens/**`（package.json / docs/troubleshooting.zh-CN.md / dsh/**）
- R1–R28 → `src/yjh051108_dsh-routing-suite/**`（injector/CHANGELOG.md、graded/CHANGELOG.md、injector/src/index.ts）+ `repos/yjh051108_dsh-routing-suite` git 提交元数据

> 备注：本次另有 git 历史查询（仅 commit 元数据、无 blob，故只用 `git log` 读提交信息，**未使用 `git show`**）。所有“提交信息原文”均来自 `repos/<仓库目录>/` 的 git 元数据。

---

<!-- ↓ 源：C-services-state.md （全文） -->

# C. 服务 / 记忆 / 状态内核 / 配置组合方向

> 调研员：Explore-1　｜　方向：服务式 / 记忆 / 状态内核 / 配置组合
> 读者定位：零软件工程经验的新手。本文只写**能从本地真实源码与 git 历史中核实**的内容。
> 素材根目录（生成期，**不随本 skill 发布**）：`<社区仓库快照>/src/`
> git 历史（生成期，仅 commit 元数据）：`<社区仓库快照>/repos/`
> 注意：本环境的 git 快照**只有 commit 元数据，没有文件 blob**；`git show <hash>:<path>` 与 `git show --stat` 会报 `could not fetch ... from promisor remote`。因此所有"改动文件清单"类信息无法获取，本文只引用 commit 的标题与正文。

---

## 0. 结论速览（先看这张表）

| 仓库 | 目录名 | 真实 DSH 插件位置 | 插件形态 | `dsh.bundle` | `dsh.client` | 有证据的坑数 |
|---|---|---|---|---|---|---|
| MemTensor/MemOS | `MemTensor_MemOS` | `apps/memos-local-plugin/`（DSH 适配器在 `adapters/deepseek-harness/`） | **函数式插件**：具名 `name`/`inject`/`Config`/`apply` | 有 `./adapters/deepseek-harness/cordis.patch.yml` | 无 | 7 |
| huangruiteng/loopx | `huangruiteng_loopx` | `packages/dsh-loopx-plugin/` | **函数式插件 ×3 行** + 一个纯 class 服务 `GoalBarService` | 有 `./cordis.patch.yml` | 有（`inject` 4 个客户端服务 + `platform: web`） | 7 |
| tt-a1i/archify | `tt-a1i_archify` | `integrations/deepseek-harness/` | **bundle-only**：`lib/index.js` 只是 `!!js` 里复用的路径解析助手，并不是被 Loader 加载的插件 | 有 `./cordis.patch.yml` | 无 | 5 |

### 0.1 必须先纠正一个流行误解：这三个仓库都**没有**使用「default export 服务类」写法

任务背景里提到"服务式插件 default export 服务类"。**在这三个仓库中我没有找到任何一处**：

- `grep -rn "extends Service"` → 0 命中；
- `grep -rn "export default"` → 只有 `src/client/css-modules.d.ts` 里的 `export default classes`（CSS 模块类型声明，与插件无关）；
- 三个仓库的插件入口**全部**是**具名函数式插件**：`export const name` + `export const inject` +（可选）`export const Config` + `export function apply(ctx, config)`。

因此本方向真正可抄的"服务"范本不是"继承 Service 的类"，而是三步：

1. **发布一个服务**：`ctx.reflect.provide('服务名', 值)`（loopx `init-command.ts:631`）；
2. **消费一个服务**：`ctx.get('名字')` / `inject: [...]`；
3. **类本身只是普通 class**：`GoalBarService implements GoalBarServiceHandle`，不继承任何基类（loopx `goalbar/service.ts:213`），生命周期靠 `apply()` 里的 `ctx.effect(..., '描述')` 返回 disposer 接管。

> 要"写一个自己的服务"，请把"具名导出 + inject + apply + ctx.effect 回收 + ctx.reflect.provide"当成模板；不要学着写 `export default class extends Service`——本批仓库里没有任何活例子能给你抄。

---
## 一、挖坑（现象 → 根因 → 怎么修）

> 每个坑都标注：**仓库 + commit 短哈希 + 提交信息原文**。凡 git 历史里查不到的，一律写"未找到"，不编造。

### 1.1 MemOS（`@memtensor/memos-local-plugin`，DSH 适配器 `adapters/deepseek-harness/`）

#### 坑 M1 ★★★：启动恢复没有超时，把关机流程扣成人质 10 分钟

- **仓库 + commit**：`MemTensor_MemOS` + `ecf1092`（2026-08-26）`fix(core): bound startup recovery wait in shutdown to 15s (#2252)`
- **提交正文原文（节选）**：
  > `core.shutdown()` awaited `startupRecoveryPromise` with **no timeout**. With a large dirty episode and a slow/flaky LLM, the startup-recovery reflect chain (up to 163 sequential LLM calls at ~2min each) can take minutes — holding shutdown hostage until the systemd kill timer fires.
  > Observed 15 Aug 2026 on a production bridge: SIGTERM at 08:00:23, daemon stuck mid-recovery, systemd `TimeoutStopSec=600` expired, SIGKILL at 08:10:23. A 10-minute stop-sigterm wedge from a single unguarded await.
- **现象**：发一个 `SIGTERM`（Ctrl+C / 进程管理器停止）后，进程卡在启动恢复流程里，10 分钟后被 systemd 强杀。
- **根因**：`shutdown()` 里 `await startupRecoveryPromise` 没有超时保护；启动恢复会串行发起最多 163 次 LLM 调用，慢/抖动的 LLM 让这个 await 变成无界等待。
- **修复（逐字）**：
  ```ts
  await withTimeout(startupRecoveryPromise, 15_000, "startup_recovery_shutdown_timeout");
  ```
  提交正文解释了"为什么 15 秒是安全的"：
  - 这个 await 最初是为 issue #1808 加的，防止 `init → shutdown` 太快导致 SQLite 在刷盘中途被关；15 秒仍足以覆盖"0–1 个 episode"的恢复（毫秒级完成）。
  - 恢复是**设计上可续跑**的：脏 episode 带 `rewardDirty.failedAttempts`，周期性的 10 分钟重打分（rescore）会重跑它们，因此超时后放行**不丢数据**。
  - 超时后 `handle.shutdown()` 摘掉订阅者，daemon 的 `process.exit(0)` 触发，残留 LLM 调用再也无法扣住进程。
- **给新手的教训**：**任何"等待后台任务"的 await 都必须包一层超时**；同时要能说清"超时后到底丢没丢数据"。

#### 坑 M2 ★★：Viewer 静态根目录解析，在"干净构建"里选错目录

- **仓库 + commit**：`MemTensor_MemOS` + `b41c899`（2026-08-16）`fix(plugin): resolve DSH Viewer assets in clean builds (#2257)`
- **提交正文原文（节选）**：
  > Fix the DSH Viewer static-root resolution exposed by the 2.0.16 release dry run. In a clean checkout, the test job runs before `prepack` builds `viewer/dist`; the previous existence-based fallback therefore selected `apps/viewer/dist` instead of the plugin-owned Viewer directory.
  > The resolver now identifies the package root through its stable `package.json` marker, so both source (`adapters/deepseek-harness`) and packed (`dist/adapters/deepseek-harness`) layouts resolve to `<package>/viewer/dist` even before Viewer assets are built. A regression test covers both clean layouts, including a package root itself named `dist`.
- **现象**：2.0.16 的 GitHub release dry run 失败；本地干净 checkout 下找不到正确的 Viewer 静态目录。
- **根因**：用"目录是否存在"（`existsSync`）来猜包根；但干净构建时 Viewer 产物 `viewer/dist` 还没生成，于是 fallback 选到了错误的 `apps/viewer/dist`。
- **修复**：改用稳定的 `package.json` 标记来识别包根，而不是猜存在性。对应源码即 §2.4 的 `resolveDeepSeekHarnessViewerStaticRoot()`：先试 `runtimeRoot/package.json`，否则上跳一层。
- **给新手的教训**：**不要用"某目录存不存在"当作路径推导依据**——它在 dev 能用、在 CI/打包后必坏。用版本稳定的锚点文件（这里是 `package.json`）。

#### 坑 M3 ★★：Viewer 端口被占用（EADDRINUSE）时，宿主快速重启会把插件搞崩

- **证据**：源码 `adapters/deepseek-harness/index.ts`（第 300–373 行）+ 该插件 `README.md`：`Quick Viewer restarts are self-healing. If viewerPort is still transiently busy, recall, capture, and tools become available immediately while the adapter retries the Viewer bind five times over about 5.75 seconds.`
- **现象**：DSH 快速重启时，旧进程的 Cordis 回收（disposal）还没走完，新进程绑同一个 `viewerPort` → `EADDRINUSE` → 整个插件启动失败。
- **根因**：一次性 `await startViewer()` 绑定，没有区分"**临时**占用（旧进程正在退出）"和"**永久**错误（端口被别的程序占用 / bindHost 非法）"。
- **修复**（源码原文，逐字）：
  ```ts
  export const DEEPSEEK_HARNESS_VIEWER_RETRY_DELAYS_MS = [
    250,
    500,
    1_000,
    2_000,
    2_000,
  ] as const;
  ```
  只对 `EADDRINUSE` 做 5 次退避自愈（合计约 5.75s）；永久错误 fail-open、不做无限重试。并且重试**可被 Cordis 的 abort 取消**——`startViewerRetryAttempt()` 专门处理"abort 赢得了 race，但延迟的 bind 稍后成功了"这种 late success，把它关掉，避免泄漏 listener 或产生未处理的 rejection：
  ```ts
  // Abort won the race. Consume either eventual outcome so a delayed bind
  // cannot leak a listener or produce an unhandled rejection after disposal.
  void pending.then(async (lateViewer) => {
    try {
      await lateViewer.close();
    } catch {
      /* best-effort cleanup after an uncancellable late listen */
    }
  }).catch(() => undefined);
  ```
- **给新手的教训**：重试要有上限、要能被取消；**"取消之后迟到的成功"必须主动清理**，否则就是内存/端口泄漏。

#### 坑 M4 ★：原生依赖 onnxruntime 在 macOS 上析构崩溃

- **证据**：该插件 `README.md`（引用了上游 issue）
- **现象**：本机 embedding（Transformers.js + ONNX Runtime）在推理结束后，宿主调用 `process.exit()` 时崩溃；DSH 的优雅退出路径恰好会这么做。
- **根因**：旧的 Transformers.js 3.x / ONNX Runtime 1.21 组合存在 known macOS destructor crash（microsoft/onnxruntime#24579），由上游 environment-lifetime 改动修复。
- **修复**：把 Transformers.js 钉在 `4.2.0`、onnxruntime-node 钉在 `1.24.3`。README 原文：`Do not downgrade this dependency in a DSH profile that uses local embeddings.`
- **给新手的教训**：**原生依赖（.node/.dll/.so）版本不能随手降**；升级平台时优先核对上游 issue。

#### 坑 M5 ★★：pnpm 11 默认拦截构建脚本，首次安装报 `ERR_PNPM_IGNORED_BUILDS`

- **证据**：该插件 `README.md`：`A first tarball or registry install can therefore stop with ERR_PNPM_IGNORED_BUILDS even though the adapter itself is prebuilt.`
- **现象**：首次从 tarball 或 npm registry 安装，卡在 `ERR_PNPM_IGNORED_BUILDS`，**即使 adapter 本体已经预编译**。
- **根因**：`better-sqlite3` / `sharp` / `onnxruntime-node` / `esbuild` 等依赖自带 install script，pnpm 11 出于安全默认 block，必须由 profile 所有者逐个批准。
- **修复**：`dsh plugin --profile web approve-builds` 逐项审查后批准；**不要** `approve-builds --all`，**不要**盲目复制 allowlist（README 明确写了 `do not use approve-builds --all or copy this allowlist blindly`）。实测策略示例：
  ```yaml
  # $DSH_HOME/profiles/web/pnpm-workspace.yaml
  allowBuilds:
    '@memtensor/memos-local-plugin': false
    better-sqlite3: true
    esbuild: true
    onnxruntime-node: true
    protobufjs: false
    sharp: true
  ```
- **给新手的教训**：安装脚本以**当前用户权限**运行，且在 agent 工具沙箱之外。只批准你信得过的依赖。

#### 坑 M6 ★★：DSH 辅助推理能力快照在 adapter 更新 / HMR 后过期

- **仓库 + commit**：`MemTensor_MemOS` + `db4717e`（2026-08-28）`fix(plugin): consolidate local runtime hardening (#2286)`
- **提交正文原文（节选）**：
  > resolves DeepSeek Harness auxiliary reasoning capability from exact model metadata, with per-route TTL caching, concurrent lookup coalescing, adapter-update invalidation, and registration-bound race fallback.
- **现象**：辅助 LLM 调用会请求"关掉推理（off）"，但 adapter 拓扑变化后旧的"该模型不支持 off"结论仍然生效（或反之），行为错乱。
- **根因**：能力结论被缓存后，没有跟随 DSH adapter 更新失效。
- **修复**：按 route 做 TTL 缓存 + 并发查询合并 + 监听 adapter 更新失效 + 绑定 registration 的 race fallback。源码对应：
  ```ts
  /** Refresh exact-model capability snapshots whenever DSH replaces an adapter. */
  export function registerDeepSeekHarnessHostLlmCapabilityInvalidation(
    ctx: Context,
    bridge: DeepSeekHarnessHostLlmBridge,
  ): () => void {
    return ctx.on("llm/adapters-updated", () => {
      bridge.invalidateModelCapabilities();
    });
  }
  ```
- **给新手的教训**：任何跨 HMR 存活的缓存，都必须挂一个失效钩子（`ctx.on(...)`）。

#### 坑 M7 ★：Hermes bridge 状态过期 / PID 被复用

- **仓库 + commit**：`MemTensor_MemOS` + `068a701`（2026-08-26）`fix(plugin): reconcile stale Hermes bridge status`；`9119efe`（2026-08-24）正文提到 `preserves the OpenClaw stale/recycled PID lock fix from #2099`
- **现象**：bridge 守护进程已经死了/被系统回收，插件仍认为它在跑；或 PID 被别的进程复用时误判。
- **根因**：状态文件（PID/status）与真实进程不同步。
- **修复**：主动 reconcile（对账）状态；对 PID 复用做防护。
- **给新手的教训**：**用 PID 文件判断"进程还活着"不可靠**，必须二次校验（启动时间 / 命令行 / 文件锁）。

---

### 1.2 loopx（`dsh-loopx-plugin`）

#### 坑 L1 ★★★：DSH 升级到 0.1.5 后 GoalBar"载体"失效

- **仓库 + commit**：`huangruiteng_loopx` + `04fc3879`（2026-09-11）`fix(dsh): restore GoalBar on DSH 0.1.5 (#4209)`
- **提交正文原文**：
  > * fix(dsh): support the 0.1.5 GoalBar carrier
  > * test(dsh): pin the 0.1.5 GoalBar regression
- **现象**：升级到 DSH 0.1.5 后，GoalBar（浏览器里的目标条）不再工作/不再显示。
- **根因**：DSH 的 **Connection RPC 载体（carrier）**在 0.1.5 变了。旧代码固定用 `/loopx` 通道；新版本要走 DSH 的 shared API 通道 `/api`，端点也更名。
- **修复**（源码 `src/client/index.tsx:44-47` + `src/client/rpc.ts`，逐字）：
  ```ts
  const rpc = createGoalBarRpc(
    ctx.connection.rpc,
    Reflect.has(ctx.connection, 'generation'),
  )
  ```
  ```ts
  const GOALBAR_CHANNEL = '/loopx'
  const GOALBAR_SHARED_API_CHANNEL = '/api'
  const GOALBAR_SHARED_API_ENDPOINT = 'loopx.goalbar'
  // ...
  const carrier = await caller.call(
    sharedApi ? GOALBAR_SHARED_API_CHANNEL : GOALBAR_CHANNEL,
    sharedApi ? GOALBAR_SHARED_API_ENDPOINT : endpoint,
    request,
    signal,
  )
  ```
  即：用**能力探测**（`Reflect.has(ctx.connection, 'generation')`）而不是"读版本号"来决定走哪条通道。
- **给新手的教训**：跨版本兼容要用**能力探测**，不要硬编码版本号判断；并且为老/新载体各留一条路。

#### 坑 L2 ★★：peer 依赖范围把"自己实测的预发布版本"排除在外

- **证据**：`packages/dsh-loopx-plugin/package.json` + `smoke/dsh-peer-range-smoke.mjs`（逐字）
  ```js
  for (const [name, range] of Object.entries(manifest.peerDependencies ?? {})) {
    if (!name.startsWith('@deepseek-ai/')) continue
    const testedVersion = manifest.devDependencies?.[name]
    assert(testedVersion, `missing tested version for official peer ${name}`)
    assert(
      supportsPrerelease(range, testedVersion),
      `${name} tested version ${testedVersion} is excluded by peer range ${range}`,
    )
  }
  ```
  其中 `supportsPrerelease` 会逐 `||` 分支检查预发布 `tuplePrefix`（`1.2.3-`）。
- **现象**：插件在实测过的 DSH 预发布版本上装不上 / peer 报警。
- **根因**：DSH 用大量预发布版本（`0.1.0-rc.7`、`0.1.1-rc.1` …），peer range 必须显式列出每个预发布分支，很容易漏。
- **修复/防御**：写一个小脚本，断言"devDependencies 里记录的实测版本"一定被 peer range 覆盖。
- **给新手的教训**：**预发布版本不遵循普通 semver 区间**，必须在 peer range 里逐条写清；用脚本自证，别靠肉眼。

#### 坑 L3 ★★：发版产物不可从 GitHub Release 安装

- **仓库 + commit**：
  - `huangruiteng_loopx` + `d6e4691b`（2026-09-01）`fix(dsh): make plugin release-installable (#3784)`
  - `98183980`（2026-09-03）`fix(dsh): require target-install compatible LoopX (#3890)`
  - `ac3fd88d`（2026-09-07）`fix(dsh): declare canonical plugin repository metadata`
- **现象**：从 GitHub Release 的 `.tgz` 安装失败；或安装成功但启动即坏。
- **根因**：包清单/入口（`exports`/`files`）或 `repository` 元数据不完整；且依赖的 LoopX 版本不满足"DSH 管理的 `pip --target` 安装后还能发现 workflow skill 文件"。
- **修复**：补齐 `exports`/`files`/`repository`；要求 `loopx>=0.5.4`。README 原文：`Although 0.5.3 carried the workflow-skill files, 0.5.4 is the first release that discovers them after the plugin's Linux pip --target managed-runtime install.`
- **给新手的教训**：**发布物要真的拿 tarball 装一遍**；"我本地能跑"不等于"装得上"。

#### 坑 L4 ★★：会话身份不唯一 → 绑定歧义，GoalBar 静默消失

- **仓库 + commit**：`huangruiteng_loopx` + `30a6e05e`（2026-09-08）`fix(dsh): derive unambiguous local session identities`
- **证据（源码）**：`src/goalbar/service.ts:41` `const AMBIGUOUS_LOG_CODE = 'dsh_loopx_goalbar_binding_ambiguous'`，以及 `capture()` / `captureIsCurrent()`（第 284–314 行）
- **现象**：某个 Session 匹配到多个绑定 → 行被隐藏、动作被拒。
- **根因**：会话身份派生不唯一（同一 sessionId 关联到多个 agent/session 引用）。
- **修复**：严格校验——`String(agent.id) === sessionId && String(session.id) === sessionId && agent.session === session`（**同一对象引用**）且 `agent.status ∈ {idle, running}` 且 `cwd` 非空；歧义时记 `binding_ambiguous` 并 **fail closed（隐藏）**。
- **给新手的教训**：**ID 相等不等于对象是同一个**；状态内核里要同时校验"ID 相等 + 引用相等 + 状态合法"。

#### 坑 L5 ★★：重复动作 / 双击 Start 触发两次可变变更

- **证据（源码）**：
  - 服务端 `src/goalbar/service.ts:584-591`：`if (this.activeAction !== undefined) return { kind: 'rejected', code: 'action_in_flight' }`
  - 客户端 `src/client/useGoalBar.ts:253`：`actionGuardRef.current = true`，注释写着 `This ref closes the pre-render/same-frame duplicate-click window.`
- **现象**：用户连点两下 `Start`，发起两次 LoopX 生命周期变更。
- **根因**：没有"进行中"闸门。
- **修复**：服务端用 `activeAction: ActionAdmission` 拒绝第二个请求；客户端用 `actionGuardRef` 关闭渲染前的同帧重复点击窗口，且**只有显式 Refresh（或 Session generation 切换）才解锁**（拒绝/结果不确定时故意保持锁）。
- **给新手的教训**：任何会改状态的按钮，**前端锁 + 后端锁都要有**。

#### 坑 L6 ★★：HMR / 同页插件重挂后 CSS 残留

- **证据（源码，逐字注释）**：`src/client/index.tsx:26-37`
  ```tsx
  // Client module exports are cached across a same-page plugin reapply, so CSS
  // installation must be an explicit, idempotent apply-time operation.
  ensurePluginStyle()

  // Register ownership immediately after installation, before any later apply
  // step can fail, so Cordis rollback and ordinary unload both remove the tag.
  ctx.effect(() => () => {
    if (typeof document === 'undefined') return
    for (const style of document.querySelectorAll('style[data-plugin]')) {
      if (style.getAttribute('data-plugin') === PACKAGE_ID) style.remove()
    }
  }, 'dsh-loopx-plugin CSS ownership')
  ```
- **现象**：热重载后样式重复叠加或丢失。
- **根因**：客户端模块导出在"同页插件重挂"之间被缓存；`apply` 会被再次调用。
- **修复**：安装要**幂等**；卸载要**在 apply 早期就登记所有权**（早于任何后续可能失败的步骤），这样 Cordis 回滚和普通卸载都会清理。
- **给新手的教训**：客户端 `apply` 可能被调用多次——一切副作用都必须幂等 + 可回收。

#### 坑 L7 ★：监听器 / 订阅忘记回收

- **证据（源码）**：`src/client/index.tsx:39-42` 用 `ctx.effect(() => ctx.locale.register(...))`；`subscribeConnectionReset: listener => ctx.on('connection/reset', listener)`；`driver.ts:1169` 与 `observer.ts:608` 都用 `ctx.effect(function* () { ... yield async () => { await dispose() } })`
- **现象**：HMR 或卸载后监听器叠加，事件触发多次，或老对象不被回收。
- **根因**：手动 `ctx.on` 若不在 `ctx.effect` 内，卸载时不会被自动清理。
- **修复**：所有注册都放进 `ctx.effect(...)`，并在生成器末尾 `yield` 一个清理函数。
- **给新手的教训**：**每一个 `ctx.on` / 注册调用都要有人负责回收**，首选 `ctx.effect`。

### 1.3 archify（`@tt-a1i/archify-dsh`）

#### 坑 A1 ★★★：用仓库根安装插件，必失败

- **证据**：`integrations/deepseek-harness/README.md`（逐字）
  > Do **not** use `dsh plugin add tt-a1i/archify`: the repository root is not a DSH package and has no bundle metadata (see [#341](https://github.com/tt-a1i/archify/issues/341)).
- **现象**：`dsh plugin add tt-a1i/archify` 失败。
- **根因**：DSH 包在**子目录** `integrations/deepseek-harness/`（`package.json` 里的 `repository.directory` 指向它）；仓库根没有 `dsh.bundle` 元数据。
- **修复**：只装发布好的 npm 包并锁死版本：`dsh plugin --profile web add @tt-a1i/archify-dsh@0.1.0`；或传本地 `.tgz`。
- **给新手的教训**：**monorepo 里插件常常不在仓库根**；安装前先确认哪个 `package.json` 里写了 `dsh.bundle`。

#### 坑 A2 ★★★：在 `!!js` 里把包根当字符串拼到 `baseUrl` 上

- **证据（源码，逐字注释）**：`integrations/deepseek-harness/cordis.patch.yml`
  ```yaml
  # Opt-in Archify filesystem Skill provider for DeepSeek Harness.
  # Resolves the packaged Skill root from the installed npm identity anchored at
  # the DSH profile (Loader baseUrl), never as a path concatenated onto baseUrl.
  - insert:
      - id: archify-skill-filesystem
        name: '@deepseek-ai/dsh-skill-filesystem'
        config:
          providerName: archify-plugin
          includeDefaultRoots: false
          bundledSkillDir: !!js process.getBuiltinModule('node:path').join(process.getBuiltinModule('node:path').dirname(process.getBuiltinModule('node:module').createRequire(baseUrl).resolve('@tt-a1i/archify-dsh/package.json')), 'skills')
  ```
- **现象**：`bundledSkillDir` 解析不到，skill 加载失败。
- **根因**：`baseUrl` 是 DSH profile 的模块解析锚点，不是一个"包目录"；直接字符串拼接会拼错。
- **修复**：用 `createRequire(baseUrl).resolve('<包名>/package.json')` 走 Node 模块解析，再取 `dirname`，最后 `join(..., 'skills')`。同一套逻辑在 `lib/index.js` 里有一份可测试的复制：
  ```js
  export function resolveArchifySkillRoot(profileBaseUrl) {
    if (!profileBaseUrl) {
      throw new Error('archify-dsh: missing DSH profile baseUrl for package resolution');
    }
    let manifestPath;
    try {
      manifestPath = createRequire(profileBaseUrl).resolve(`${PACKAGE_NAME}/package.json`);
    } catch (error) {
      throw new Error(
        `archify-dsh: cannot resolve ${PACKAGE_NAME}/package.json from the DSH profile`,
        { cause: error },
      );
    }
    return join(dirname(manifestPath), 'skills');
  }
  ```
  并且有测试断言解析失败要"响亮地抛错，而不是猜一个 root"（`test/adapter-security.test.mjs:24-28`）。
- **给新手的教训**：**要定位"已安装的包"，永远走模块解析（`createRequire().resolve`），不要拼路径。**

#### 坑 A3 ★★：Windows 上打包不可移植

- **仓库 + commit**：`tt-a1i_archify` + `fc6e8ac`（2026-08-14）`fix: make DSH packaging portable on Windows (#70)`
- **现象**：Windows 上打包/安装失败。
- **根因**：路径分隔符 / 行尾（CRLF）处理不统一。
- **修复**：规范化。同目录还留有 Linux/macOS/Windows 三平台跑的发布验收 CI（`README.md`：`Release CI runs this on Linux, macOS, and Windows.`）。
- **给新手的教训**：**路径一律用 `node:path` 处理，别手写 `/` 或 `\`。**

#### 坑 A4 ★★：从"工作区未提交的改动"打包，产物与发布不符

- **证据**：`README.md`（逐字）
  > The pack command reads adapter files and release metadata from the current adapter Git HEAD blob: commit those changes before packing; working-tree edits are not package inputs.
- **相关 commit**：`2ead014`（2026-09-08）`fix(dsh): prepare reproducible 0.2.0 adapter with current Skill snapshot (#345)`
- **现象**：本地打包出来的包，内容和已提交的版本不一致；发布不可复现。
- **根因**：打包脚本从 Git **HEAD blob** 取文件，而不是工作区文件。
- **修复**：先 commit 再 pack；发布用 tag + 记录的 Skill commit，"不是移动的分支"。
- **给新手的教训**：**先提交、再打包**；"打包源是 git 而不是磁盘"是很常见的设计。

#### 坑 A5 ★：shell 产生的文件不会自动进 Web 的 Produced Files

- **证据**：`README.md`「Produced Files limitation」（逐字）
  > Files created by shell commands do **not** automatically appear in the Web Produced Files strip. Ask the agent to return the **exact workspace paths** of the specification JSON and the HTML artifact, then open those files from the workspace.
- **现象**：工具生成了 JSON/HTML，但 Web UI 的"产出文件"条里看不到。
- **根因**：DSH 的 Produced Files 只跟踪它自己认识的文件，shell 命令产出的不算。
- **修复**：让 agent 返回精确的工作区绝对路径，用户自行打开。
- **给新手的教训**：**"文件生成了"和"UI 里看得到"是两件事**，要在提示词里显式要求返回路径。

### 1.4 未找到 / 明确不存在的坑

- **服务重复注册冲突**：三个仓库均未找到"同一服务被注册两次"的修复提交。
- **配置校验失败导致插件不加载**：无专门修复提交；MemOS 用 fail-open（见 §2.1）而非"不加载"，loopx 的 observer 用"配置不全就完全 off"（见 §2.2）。
- **`ctx.provide` 时机问题（服务冲突）**：无修复提交；loopx 反而**刻意**用 `ctx.reflect.provide` 在 boot 后才发布（见 §2.2）。
- 声明：以上写"未找到"，**不代表没有**，只代表在这三仓库的 commit 元数据里没查到。

---

## 二、可抄代码模板（逐字照抄，超长标 `…(略)`）

### 2.0 三个插件的完整目录树

#### 2.0.1 MemOS —— `apps/memos-local-plugin/`（全仓 673 个文件；DSH 入口在 `adapters/deepseek-harness/`）

```
apps/memos-local-plugin/
├── .gitignore
├── .npmignore
├── ARCHITECTURE.md
├── CHANGELOG.md
├── README.md
├── adapters/                      # 每个宿主一个适配器
│   ├── ALGORITHMS.md
│   ├── README.md
│   ├── deepseek-harness/          ← DSH 适配器（本次重点）
│   │   ├── README.md
│   │   ├── bridge.ts
│   │   ├── cordis.patch.yml       ← dsh.bundle.patch
│   │   ├── deadline.ts
│   │   ├── host-llm.ts
│   │   ├── index.ts               ← 插件入口（name/inject/Config/apply）
│   │   └── tools.ts               ← 6 个 memos_* 工具
│   ├── hermes/                    # Python provider + 安装脚本
│   └── openclaw/                  # index.ts / bridge.ts / tools.ts
├── agent-contract/                # 跨适配器共享的 DTO / 事件 / 错误 / JSON-RPC
├── bridge/                        # JSON-RPC bridge（DSH 不用；OpenClaw/Hermes 用）
├── bridge.cts
├── bridge.mts
├── core/                          # 记忆内核：capture/embedding/llm/memory/storage/config…
├── docs/
├── install.sh
├── openclaw.plugin.json
├── package-lock.json
├── package.json
├── pnpm-lock.yaml
├── scripts/
├── server/                        # 进程内 HTTP/SSE Viewer 后端
├── templates/                     # config.<agent>.yaml
├── tests/                         # 205 个文件（unit/integration/e2e/python 等）
├── tsconfig.build.json
├── tsconfig.json
├── tsconfig.viewer.json
├── viewer/                        # 64 个文件，Preact Viewer 前端
├── vite.config.ts
├── vitest.config.ts
└── website/
```

注：插件根另有 Windows 版安装脚本（与 `install.sh` 同名不同扩展名）。`adapters/deepseek-harness/` 只有 **7 个文件**，其余 660+ 是共享内核 / 测试 / Viewer。**新手只需盯住这 7 个文件的入口约定**。

#### 2.0.2 loopx —— `packages/dsh-loopx-plugin/`（全仓 51 个文件，`find ... | sort` 原始结果）

```
packages/dsh-loopx-plugin/
├── .gitignore
├── LICENSE
├── NOTICE
├── README.md
├── cordis.patch.yml
├── install.sh
├── package.json
├── pnpm-lock.yaml
├── pnpm-workspace.yaml
├── scripts/build.mjs
├── smoke/Dockerfile.clean
├── smoke/dsh-clean-docker-probe.mjs
├── smoke/dsh-clean-docker-smoke.sh
├── smoke/dsh-client-artifact-smoke.mjs
├── smoke/dsh-goalbar-runtime-smoke.mjs
├── smoke/dsh-peer-range-smoke.mjs
├── smoke/dsh-profile-smoke.mjs
├── src/cli.ts
├── src/client/LoopXGoalBar.tsx
├── src/client/css-modules.d.ts
├── src/client/goalbar.module.css
├── src/client/index.tsx
├── src/client/locale.ts
├── src/client/rpc.ts
├── src/client/useGoalBar.ts
├── src/driver.ts
├── src/goalbar/connection-rpc.ts
├── src/goalbar/events.ts
├── src/goalbar/protocol.ts
├── src/goalbar/read-model.ts
├── src/goalbar/service.ts
├── src/index.ts
├── src/init-command.ts
├── src/managed-runtime.ts
├── src/observer.ts
├── tests/admission-closeout.integration.spec.ts
├── tests/cli.spec.ts
├── tests/driver.spec.ts
├── tests/goalbar-client.spec.tsx
├── tests/goalbar-connection.spec.ts
├── tests/goalbar-protocol.spec.ts
├── tests/goalbar-read-model.spec.ts
├── tests/goalbar-service.spec.ts
├── tests/init-command.spec.ts
├── tests/observer.spec.ts
├── tsconfig.client.json
├── tsconfig.host.json
├── tsconfig.json
├── tsconfig.tests.json
├── tsdown.client.config.ts
└── tsdown.config.ts
```

#### 2.0.3 archify —— `integrations/deepseek-harness/`（全仓 21 个文件，`find ... | sort` 原始结果）

```
integrations/deepseek-harness/
├── .gitignore
├── README.md
├── cordis.patch.yml
├── lib/index.js
├── package.json
├── release.json
├── scripts/distribution-acceptance.mjs
├── scripts/pack.mjs
├── scripts/release-source.mjs
├── scripts/resolve-cli.mjs
├── scripts/transient-retry.mjs
├── test/adapter-security.test.mjs
├── test/adapter-staging.test.mjs
├── test/docs-contract.test.mjs
├── test/package-contract.test.mjs
├── test/probe-skills.mjs
├── test/probe-skills.test.mjs
├── test/resolve-cli.test.mjs
├── test/tarball-contract.test.mjs
├── test/transient-retry.test.mjs
└── test/zero-regression.test.mjs
```

⚠️ 注意：**这个目录里没有 `src/`，也没有客户端半侧**。它的 `lib/index.js` 不是被 Loader 加载的插件，而是给 `cordis.patch.yml` 的 `!!js` 表达式做同构的、可测试的路径解析助手（见坑 A2）。`dsh.bundle` 指向的 patch 里插入的是 DSH 自带的 `@deepseek-ai/dsh-skill-filesystem`。

### 2.1 archify `package.json`（全文）

```json
{
  "name": "@tt-a1i/archify-dsh",
  "version": "0.2.0",
  "description": "Opt-in DeepSeek Harness Skill-only bundle for the Archify architecture-diagram skill.",
  "license": "MIT",
  "type": "module",
  "main": "./lib/index.js",
  "exports": {
    ".": "./lib/index.js",
    "./package.json": "./package.json"
  },
  "files": [
    "lib",
    "cordis.patch.yml",
    "skills",
    "README.md",
    "LICENSE",
    "release.json"
  ],
  "keywords": [
    "dsh-plugin",
    "deepseek-harness",
    "agent-skill",
    "architecture-diagram"
  ],
  "engines": {
    "node": "^22.19.0 || >=24.0.0"
  },
  "repository": {
    "type": "git",
    "url": "git+https://github.com/tt-a1i/archify.git",
    "directory": "integrations/deepseek-harness"
  },
  "homepage": "https://github.com/tt-a1i/archify/tree/main/integrations/deepseek-harness",
  "bugs": "https://github.com/tt-a1i/archify/issues",
  "publishConfig": {
    "access": "public"
  },
  "dsh": {
    "bundle": {
      "patch": "./cordis.patch.yml"
    }
  }
}
```

### 2.2 MemOS `package.json`（全文；此处为前半段，后半段见 2.2b）

```json
{
  "name": "@memtensor/memos-local-plugin",
  "version": "2.0.16-beta.1",
  "description": "Reflect2Evolve memory plugin: layered L1/L2/L3 memory, reflection-weighted value backprop, cross-task policy induction, skill crystallization, and three-tier retrieval for OpenClaw, Hermes Agent, and DeepSeek Harness.",
  "type": "module",
  "main": "dist/core/index.js",
  "types": "dist/core/index.d.ts",
  "openclaw": {
    "id": "memos-local-plugin",
    "kind": "memory",
    "extensions": [
      "./dist/adapters/openclaw/index.js"
    ],
    "installDependencies": true
  },
  "dsh": {
    "bundle": {
      "patch": "./adapters/deepseek-harness/cordis.patch.yml"
    }
  },
  "files": [
    "dist",
    "telemetry.credentials.json",
    "openclaw.plugin.json",
    "bridge.cts",
    "bridge.mts",
    "bridge/**/*.ts",
    "core/**/*.ts",
    "core/storage/migrations/*.sql",
    "agent-contract/**/*.ts",
    "server/**/*.ts",
    "adapters/openclaw/**/*.ts",
    "adapters/openclaw/*.sh",
    "adapters/deepseek-harness/cordis.patch.yml",
    "adapters/hermes/*.sh",
    "adapters/hermes/plugin.yaml",
    "adapters/hermes/memos_provider/*.py",
    "templates/*.yaml",
    "templates/README.user.md",
    "viewer/dist",
    "scripts/postinstall.cjs",
    "scripts/sync-hermes-version.cjs",
    "install.sh",
    "...(安装脚本与其余 files 条目略)",
    "!**/ALGORITHMS.md",
    "!**/README.md",
    "adapters/deepseek-harness/README.md",
    "!**/__pycache__",
    "!**/*.pyc",
    "!**/.gitkeep",
    "!**/*.map",
    "!dist/tests",
    "!dist/tests/**"
  ],
  "scripts": {
    "build": "tsc -p tsconfig.build.json && node scripts/copy-runtime-assets.cjs",
    "build:viewer": "vite build --config vite.config.ts",
    "build:package": "npm run build && npm run build:viewer",
    "prepack": "npm run check:hermes-version && npm run build:package",
    "sync:hermes-version": "node scripts/sync-hermes-version.cjs",
    "check:hermes-version": "node scripts/sync-hermes-version.cjs --check",
    "release:validate": "npm run check:hermes-version && npm run lint && npm test",
    "dev": "tsc -p tsconfig.json --watch",
    "viewer:dev": "vite --config vite.config.ts",
    "bridge": "tsx bridge.cts",
    "bridge:daemon": "tsx bridge.cts --daemon",
    "test": "vitest run",
    "test:watch": "vitest",
    "test:unit": "vitest run tests/unit",
    "test:integration": "vitest run tests/integration",
    "test:e2e": "vitest run tests/e2e",
    "lint": "tsc -p tsconfig.json --noEmit",
    "postinstall": "node scripts/postinstall.cjs"
  },
  "keywords": [
    "memory",
    "agent",
    "reflect2evolve",
    "self-evolution",
    "skill-crystallization",
    "openclaw",
    "hermes",
    "deepseek-harness",
    "dsh-plugin"
  ],
  "license": "MIT",
  "engines": {
    "node": ">=20.0.0"
  },
```
  "dependencies": {
    "@huggingface/transformers": "4.2.0",
    "@preact/signals": "^2.9.0",
    "@sinclair/typebox": "^0.34.48",
    "better-sqlite3": "^12.10.0",
    "preact": "^10.29.1",
    "tsx": "^4.21.0",
    "uuid": "^10.0.0",
    "yaml": "^2.6.0"
  },
  "peerDependencies": {
    "@deepseek-ai/cordis": "^4.0.1",
    "@deepseek-ai/dsh-agent": ">=0.1.0-rc.5 <0.2.0",
    "@deepseek-ai/dsh-llm": ">=0.1.0-rc.5 <0.2.0",
    "@deepseek-ai/dsh-session": ">=0.1.0-rc.5 <0.2.0",
    "@deepseek-ai/dsh-system-prompt": ">=0.1.0-rc.5 <0.2.0",
    "@deepseek-ai/dsh-timeout": ">=0.1.0-rc.5 <0.2.0",
    "@deepseek-ai/dsh-tools": ">=0.1.0-rc.5 <0.2.0",
    "@deepseek-ai/schemastery": "^3.18.1"
  },
  "peerDependenciesMeta": {
    "@deepseek-ai/cordis": { "optional": true },
    "@deepseek-ai/dsh-agent": { "optional": true },
    "@deepseek-ai/dsh-llm": { "optional": true },
    "@deepseek-ai/dsh-session": { "optional": true },
    "@deepseek-ai/dsh-system-prompt": { "optional": true },
    "@deepseek-ai/dsh-timeout": { "optional": true },
    "@deepseek-ai/dsh-tools": { "optional": true },
    "@deepseek-ai/schemastery": { "optional": true }
  },
  "devDependencies": {
    "@deepseek-ai/cordis": "^4.0.1",
    "@deepseek-ai/dsh-agent": "0.1.0-rc.6",
    "@deepseek-ai/dsh-llm": "0.1.0-rc.6",
    "@deepseek-ai/dsh-session": "0.1.0-rc.6",
    "@deepseek-ai/dsh-system-prompt": "0.1.0-rc.6",
    "@deepseek-ai/dsh-timeout": "0.1.0-rc.6",
    "@deepseek-ai/dsh-tools": "0.1.0-rc.6",
    "@deepseek-ai/schemastery": "^3.18.1",
    "@preact/preset-vite": "^2.10.5",
    "@types/better-sqlite3": "^7.6.12",
    "@types/node": "^22.10.0",
    "@types/uuid": "^10.0.0",
    "typescript": "^5.7.0",
    "vite": "^5.4.10",
    "vitest": "^2.1.9"
  }
}
```

### 2.2b MemOS `cordis.patch.yml`（全文，逐字）

```yaml
- insert:
    - id: memos-local-memory
      name: '@memtensor/memos-local-plugin/dist/adapters/deepseek-harness/index.js'
      config:
        enabled: true
        profileId: default
        home: ''
        recallEnabled: true
        captureEnabled: true
        toolsEnabled: true
        hostLlmEnabled: true
        viewerEnabled: true
        viewerPort: 18801
        recallTimeoutMs: 3000
        contextMaxChars: 6000
        toolResultMaxChars: 1200
        failOnStartupError: false
```

要点：patch 里用的是**编译后**路径 `dist/adapters/deepseek-harness/index.js`（不是 `src`）；`name` 是包内相对导出，`config` 与插件 `Config` 的字段一一对应。

### 2.3 【核心范本·服务生命周期】MemOS DSH 适配器插件头 + Config（`adapters/deepseek-harness/index.ts`，逐字）

```ts
/** Native Cordis adapter for DeepSeek Harness. */

import type { Context } from "@deepseek-ai/cordis";
import type { PreStepDecision } from "@deepseek-ai/dsh-agent";
import { createUserMessage } from "@deepseek-ai/dsh-llm";
import type { Session, SessionEvent } from "@deepseek-ai/dsh-session";
import type {} from "@deepseek-ai/dsh-system-prompt";
import Schema from "@deepseek-ai/schemastery";
// …(其余 import 略)

export const name = DEEPSEEK_HARNESS_PLUGIN;
export const inject = ["systemPrompt", "tools", "llm"];
export const DEEPSEEK_HARNESS_VIEWER_PORT = 18_801;
export const DEEPSEEK_HARNESS_VIEWER_RETRY_DELAYS_MS = [
  250,
  500,
  1_000,
  2_000,
  2_000,
] as const;
export const DEEPSEEK_HARNESS_MAX_FOREGROUND_SEARCH_MS = 3_000;

export interface Config {
  enabled: boolean;
  profileId: string;
  home: string;
  recallEnabled: boolean;
  captureEnabled: boolean;
  toolsEnabled: boolean;
  hostLlmEnabled: boolean;
  viewerEnabled: boolean;
  viewerPort: number;
  recallTimeoutMs: number;
  contextMaxChars: number;
  toolResultMaxChars: number;
  failOnStartupError: boolean;
}

export const Config: Schema<Config> = Schema.object({
  enabled: Schema.boolean().default(true),
  profileId: Schema.string().default("default"),
  home: Schema.string().default(""),
  recallEnabled: Schema.boolean().default(true),
  captureEnabled: Schema.boolean().default(true),
  toolsEnabled: Schema.boolean().default(true),
  hostLlmEnabled: Schema.boolean().default(true),
  viewerEnabled: Schema.boolean().default(true),
  viewerPort: Schema.number().step(1).min(1).max(65_535).default(
    DEEPSEEK_HARNESS_VIEWER_PORT,
  ),
  recallTimeoutMs: Schema.number().min(100).default(3_000),
  contextMaxChars: Schema.number().min(256).default(6_000),
  toolResultMaxChars: Schema.number().min(128).default(1_200),
  failOnStartupError: Schema.boolean().default(false),
});
```

**可抄点**：
1. `name` / `inject` / `Config` **全部具名导出**，`inject` 是**字符串数组**，列出本插件要用到的 DSH 服务；
2. `interface Config` 与 `const Config: Schema<Config>` **同名共存**（TS 里接口与值可同名）；
3. `Schema.boolean().default(true)` 用 schemastery **给每个字段默认值**，并可用 `.min/.max/.step` 约束数值。

### 2.4 【核心范本·副作用回收】MemOS `apply()` 的"注册表 + 统一回滚 + 卸载 disposer"（逐字，中间略）

```ts
/** Bootstrap MemOS and register all lifecycle hooks as one Cordis plugin. */
export async function apply(
  ctx: Context,
  config: Config,
): Promise<() => Promise<void>> {
  if (!config.enabled) return async () => undefined;

  const configuredHome = defaultDeepSeekHarnessHome(config.home);

  let core: MemoryCore | undefined;
  let bridge: ReturnType<typeof createDeepSeekHarnessBridge> | undefined;
  let viewer: ServerHandle | undefined;
  let viewerRetryController: AbortController | undefined;
  let viewerRetryTask: Promise<void> | undefined;
  let disposing = false;
  const registrations: Array<() => void> = [];
  const unregisterAll = (): void => {
    for (const unregister of registrations.splice(0).reverse()) {
      try {
        unregister();
      } catch (error) {
        ctx.logger.warn(`memos-local-memory: registration rollback failed: ${String(error)}`);
      }
    }
  };
  try {
    // …(第 248–400 行：解析 home、loadConfig、建 hostLlmBridge、bootstrapMemoryCore、启动 Viewer 略)

    registrations.push(ctx.systemPrompt.section({
      name: "tool:memos-local-memory",
      order: 114,
      text: deepSeekHarnessMemoryGuidance(config.toolsEnabled),
    }));

    registrations.push(ctx.on("agent/pre-step", async (payload, next): Promise<PreStepDecision> => {
      return bridge!.beforeStep(
        payload as unknown as DshPreStepPayloadLike,
        next as unknown as () => Promise<DshPreStepDecisionLike>,
      ) as unknown as Promise<PreStepDecision>;
    }));

    registrations.push(ctx.on("session/event", (session: Session, event: SessionEvent): void => {
      bridge!.onSessionEvent(
        session as unknown as DshSessionLike,
        event as unknown as DshSessionEventLike,
      );
    }));

    registrations.push(ctx.on("session/disposed", (session: Session): void => {
      // Session disposal is intentionally detached from DSH's request path.
      // The bridge serializes close after this session's queued lifecycle work;
      // Cordis disposal remains the one place that drains all queues.
      void bridge!.closeSession(session as unknown as DshSessionLike).catch((error) => {
        ctx.logger.warn(
          `memos-local-memory: detached session cleanup failed: ${String(error)}`,
        );
      });
    }));

    if (config.toolsEnabled) {
      registrations.push(registerDeepSeekHarnessTools(ctx, {
        core,
        profileId: config.profileId,
        maxBodyChars: config.toolResultMaxChars,
        searchTimeoutMs: foregroundSearchTimeoutMs,
        currentEpisode: (session) => bridge!.currentEpisode(session),
        runWithLlmRoute: (route, operation) => routes.run(route, operation),
      }));
    }

    ctx.logger.info(
      `memos-local-memory: ready (home=${home.root}, recall=${String(config.recallEnabled)}, ` +
      // …(日志其余略)
    );
  } catch (error) {
    disposing = true;
    unregisterAll();
    viewerRetryController?.abort();
    if (viewerRetryTask) await viewerRetryTask;
    if (viewer) {
      try {
        await viewer.close();
      } catch {
        /* best-effort cleanup after failed bootstrap */
      }
    }
    if (bridge) await bridge.dispose();
    else if (core) await core.shutdown();
    const message = error instanceof Error ? error.message : String(error);
    ctx.logger.warn(`memos-local-memory: startup failed: ${message}`);
    if (config.failOnStartupError) throw error;
    return async () => undefined;
  }

  return async () => {
    disposing = true;
    unregisterAll();
    viewerRetryController?.abort();
    if (viewerRetryTask) await viewerRetryTask;
    if (viewer) {
      try {
        await viewer.close();
      } catch (error) {
        ctx.logger.warn(`memos-local-memory: viewer close failed: ${String(error)}`);
      }
    }
    await bridge!.dispose();
    ctx.logger.info("memos-local-memory: stopped");
  };
}
```

**可抄点（这是"服务/内存密级插件"的标准骨架）**：
1. `apply` 是 `async`，**返回一个卸载函数** `() => Promise<void>`；
2. 所有注册（`ctx.on` / `ctx.systemPrompt.section` / `ctx.tools.register` / 自定义 `register*`）的返回值都 `push` 进一个 `registrations` 数组，**每个注册函数都返回自己的 disposer**；
3. `unregisterAll()` **倒序** `splice(0).reverse()` 逐个调用，且**每个都 try/catch**（一个回滚失败不能挡住其余）；
4. `catch` 里做**全量回滚**（`unregisterAll` + abort 重试 + close viewer + dispose bridge / shutdown core），再按 `failOnStartupError` 决定"抛出"还是"返回空卸载函数、让宿主继续跑"；
5. `disposing` 标志位让"重试中迟到的成功"知道自己该收尾。

### 2.5 MemOS 工具模板：`parameters`（DSH DSL）与 `output.schema`（标准 JSON Schema）（逐字，节选）

```ts
/** Read-oriented MemOS tools exposed through DeepSeek Harness. */

import type { Context } from "@deepseek-ai/cordis";
import { defineTool, type JsonValue } from "@deepseek-ai/dsh-tools";
// …(import 略)

const JSON_OUTPUT = {
  schema: {
    type: "object" as const,
    additionalProperties: true,
    properties: {
      text: { type: "string" as const, required: true },
    },
  },
  render: (_args: unknown, value: Record<string, unknown>) => [{
    type: "text" as const,
    text: typeof value["text"] === "string"
      ? value["text"]
      : JSON.stringify(value),
  }],
} as const;

export function registerDeepSeekHarnessTools(
  ctx: Context,
  options: DeepSeekHarnessToolsOptions,
): () => void {
  const bodyCap = options.maxBodyChars;
  const searchTimeoutMs = options.searchTimeoutMs ?? 3_000;
  const now = options.now ?? (() => Date.now());
  const disposers: Array<() => void> = [];

  try {
    disposers.push(ctx.tools.register(defineTool({
      name: "memos_search",
      description:
        "Search long-term MemOS memory across prior traces, learned policies, world models, and skills. " +
        "Use this before claiming that earlier user context is unavailable.",
      parameters: {
        query: {
          type: "string",
          required: true,
          description: "A concise free-text memory query.",
        },
        maxResults: {
          type: "integer",
          description: "Maximum results per tier (1-50).",
        },
        tier1topK: { type: "integer", description: "Skill result limit (0-100)." },
        tier2topK: { type: "integer", description: "Trace/policy result limit (0-100)." },
        tier3topK: { type: "integer", description: "World-model result limit (0-100)." },
        sessionScope: {
          type: "boolean",
          description: "Restrict results to the current DSH session.",
        },
      },
      output: JSON_OUTPUT,
      isConcurrencySafe: () => true,
      async execute(args, exec) {
        const query = requireText(args.query, "query");
        // …(execute 主体略)
      },
    })));
    // …(其余 5 个工具同样 disposers.push(ctx.tools.register(defineTool({ ... }))) 略)
  } catch (error) {
    disposeAll(disposers);
    throw error;
  }

  return () => disposeAll(disposers);
}

function disposeAll(disposers: Array<() => void>): void {
  for (const dispose of disposers.splice(0).reverse()) dispose();
}
```

**可抄点 1 —— 两种 `required` 写法千万别混**（本手册的硬规则）：
- **`parameters` 用 DSH 自研 DSL**：必需参数写在**属性级** `required: true`（见上面 `query`）。
- **`output.schema` 用标准 JSON Schema**：对象级 `required: ['a','b']` 数组。
- 从源码可确认：`parameters.query.required: true`（属性级）、`output.schema.properties.text.required: true`（也是属性级，因为它走的是另一种渲染 DSL）；而标准 JSON Schema 对象级的 `required` 是**数组**，两者语法语义不同，**不可互相搬用**。

**可抄点 2 —— 工具注册的失败安全**：`register*` 函数内部维护 `disposers` 数组，整个注册包在 `try/catch` 里；任何一个工具注册失败就 `disposeAll` 已注册的、再把错误抛出去；成功则返回 `() => disposeAll(disposers)`。这与 §2.4 的 `registrations` 是**同一个模式**，只是作用域更小。

### 2.6 【最小范本·服务生命周期】loopx 包根 Host 插件（`src/index.ts` 全文，逐字，共 29 行）

```ts
import type { Context } from '@deepseek-ai/cordis'
import type { Agent } from '@deepseek-ai/dsh-agent'
import {
  registerGoalBarConnectionTransport,
} from './goalbar/connection-rpc.ts'
import { goalBarCoordinator } from './goalbar/events.ts'
import { createGoalBarService } from './goalbar/service.ts'
import { resolvePluginLoopXCommand } from './managed-runtime.ts'

export const name = 'dsh-loopx-plugin'
export const inject = ['agents', 'connection', 'loopxBootstrap']

/** Package-root Host plugin: one GoalBar service, never a second Driver. */
export function apply(ctx: Context): void {
  ctx.effect(() => {
    const service = createGoalBarService({
      getAgent: sessionId => ctx.agents.get(sessionId as Agent['id']),
      coordinator: goalBarCoordinator,
      resolveCommand: signal => resolvePluginLoopXCommand({ signal }),
      warn: message => { ctx.logger.warn(message) },
    })
    const disposeRpc = registerGoalBarConnectionTransport(ctx.connection, service)
    return async () => {
      await service.dispose()
      await disposeRpc()
    }
  }, 'dsh-loopx GoalBar Host service')
}
```

**为什么它是最佳"服务"起手范本**：
- 只有 `name` + `inject` + `apply` 三件套，**没有 Config**（loopx 这个包不读 Cordis config，见 §三）；
- `apply` 是**同步**的（`(): void`），所有异步初始化都封在 `ctx.effect` 的回调里；
- `ctx.effect(() => { ...; return async () => { await service.dispose(); await disposeRpc() } }, '描述')` —— **effect 回调返回 disposer**，Cordis 卸载时自动调用；
- `inject: ['agents', 'connection', 'loopxBootstrap']` 一眼看出依赖 3 个服务，其中 `loopxBootstrap` 是**自家**在其他行 `provide` 出来的。

### 2.7 【最小范本·条件关闭】loopx 影子观察者入口（`src/observer.ts` 末尾，逐字）

```ts
/** Cordis entrypoint. Partial configuration is the exact feature-off path. */
export function apply(ctx: Context): void {
  const config = resolveShadowObserverConfig()
  if (config === undefined) return
  registerShadowObserver(ctx, config)
}
```

```ts
/** Register only the session log's read-only publication hooks. */
export function registerShadowObserver(ctx: Context, config: ShadowObserverConfig): ShadowObserver {
  const observer = new ShadowObserver({
    config,
    warn: message => { ctx.logger.warn(message) },
  })
  ctx.effect(function* () {
    ctx.on('session/created', session => { observer.observeSessionCreated(session) })
    ctx.on('session/event', (session, event) => { observer.observeSessionEvent(session, event) })
    ctx.on('session/disposed', session => { observer.observeSessionDisposed(session) })
    yield async () => {
      await observer.dispose()
    }
  }, 'dsh-loopx shadow observer lifecycle')
  return observer
}
```

**可抄点**：
- **配置不全就彻底 off**：`if (config === undefined) return`——比"报错不加载"更友好，也不会留下半个插件；
- `ctx.effect(function* () { ...; yield async () => {...} })` 是**生成器写法**：`yield` 出来的函数就是 disposer，与返回函数的写法等价，适合"注册很多行 + 末尾统一清理"。

### 2.8 【核心范本·发布服务】loopx `init-command.ts` 的 `ctx.reflect.provide`（逐字）

```ts
/** Register the explicit repair command without changing LoopX readiness. */
export function registerLoopXInitCommand(
  ctx: Context,
  options: LoopXInitOptions = {},
): void {
  ctx.commands.register({
    name: 'loopx-init',
    description: 'install or upgrade LoopX and install the DSH LoopX skills',
    recordInput: false,
    async handler(invocation): Promise<CommandResult> {
      if (invocation.rawInput.trim().length > 0) {
        return { kind: 'error', text: 'Usage: /loopx-init' }
      }
      const warn = (message: string): void => { ctx.logger.warn(message) }
      queueFollowup(invocation.agent, startFollowup(), 'start', warn)
      try {
        const result = await initializeLoopX({ ...options, signal: invocation.signal })
        const commandResult = successResult(result)
        if (!invocation.signal.aborted) {
          queueFollowup(invocation.agent, successFollowup(result), 'complete', warn)
        }
        return commandResult
      } catch (error: unknown) {
        const commandResult = commandFailure(error)
        if (!cancelled(error, invocation.signal)) {
          queueFollowup(invocation.agent, failureFollowup(error), 'complete', warn)
        }
        return commandResult
      }
    },
  })
}
```

```ts
/**
 * Make the installed plugin ready before DSH finishes loading this row.
 *
 * Startup failures are isolated to LoopX: DSH still boots and the registered
 * command remains as an explicit retry surface. The awaited happy path keeps a
 * freshly installed profile from racing its first `skill.list` readback.
 */
export async function apply(ctx: Context, options: LoopXInitOptions = {}): Promise<void> {
  registerLoopXInitCommand(ctx, options)
  let status: LoopXBootstrapStatus
  try {
    await initializeLoopX(options)
    status = Object.freeze({ state: 'ready' })
  } catch (error: unknown) {
    status = bootstrapFailureStatus(error)
    try {
      ctx.logger.warn(automaticFailure(error))
    } catch {
      // Diagnostics must never turn an isolated LoopX bootstrap failure into a DSH startup failure.
    }
  }
  ctx.reflect.provide('loopxBootstrap', status)
}
```

**可抄点（怎么"提供"一个服务）**：
1. **服务名是字符串**：`ctx.reflect.provide('loopxBootstrap', status)`；别的行用 `inject: ['loopxBootstrap']` 或 `ctx.get('loopxBootstrap')` 消费；
2. **无论成功还是"安全失败"都要 provide**——否则依赖它的行（Web server / web runtime）会被一直挂起，DSH 的 Web URL 永远发不出来；
3. **失败降级成类型化的状态对象**（`{ state: 'failed', stage, causeKind }`），而不是抛异常；这样宿主可继续启动，`/loopx-init` 还能修复；
4. `Object.freeze(...)` 冻结状态，防止下游误改。

### 2.9 loopx 状态内核：`driver.ts` 的 `apply`（逐字，多监听 + 生成器清理）

```ts
export function apply(ctx: Context): void {
  const driver = new LoopXContinuationDriver({
    isLiveAgent: agent => ctx.agents.get(agent.id) === agent,
    resolveCommand: signal => resolvePluginLoopXCommand({ signal }),
    runDetached: operation => ctx.agents.withoutInitiator(operation),
    warn: message => { ctx.logger.warn(message) },
  })

  ctx.effect(function* () {
    const unregisterDriverBridge = goalBarCoordinator.registerDriverBridge(driver)
    ctx.on('agent/created', ({ agent }) => { driver.observeAgent(agent) })
    ctx.on('agent/disposed', ({ agent }) => {
      goalBarCoordinator.invalidateSession(agent.session)
      driver.onAgentDisposed(agent)
    })
    ctx.on('session/disposed', session => {
      goalBarCoordinator.invalidateSession(session)
    })
    ctx.on('agent/session-start', ({ agent }) => { driver.onSessionStart(agent) })
    ctx.on('agent/status', ({ agent, status }) => {
      if (status === 'idle' || status === 'running') {
        goalBarCoordinator.publishAgentStatus(agent.session, status)
      }
      driver.onAgentStatus(agent, status)
    })
    ctx.on('agent/inbox/inserted', ({ agent, message }) => driver.onInboxInserted(agent, message))
    ctx.on('agent/inbox/claimed', ({ agent, message }) => driver.onInboxClaimed(agent, message))
    ctx.on('agent/inbox/discarded', ({ agent, message }) => driver.onInboxDiscarded(agent, message))
    ctx.on('agent/error', ({ agent }) => { driver.onAgentError(agent) })
    ctx.on('agent/pre-step', ({ agent, messages, signal }, next) => (
      driver.onPreStep(agent, messages, signal, next)
    ))
    ctx.on('session/event', (session, event) => {
      if (event.type === 'step/end' || event.type === 'turn/end') {
        goalBarCoordinator.publishSessionCandidate(session, event)
      }
      const agent = ctx.agents.get(session.id)
      if (agent?.session === session) driver.onSessionEvent(agent, event)
    })
    for (const agent of ctx.agents.list()) driver.observeAgent(agent)
    yield async () => {
      unregisterDriverBridge()
      await driver.dispose()
    }
  }, 'dsh-loopx-driver lifecycle')
}
```

**可抄点**：
- **"全局一个 Driver，按会话激活"** 的状态内核模式：Driver 实例只建一次，把"DSh 的 agent 事件"翻译成 driver 内部状态；卸载时 `yield` 一个函数统一 `dispose()`；
- `ctx.agents.list()` 在 apply 时对**已存在**的 agent 补一遍 `observeAgent`，避免"插件比 agent 晚加载"时漏掉；
- `if (agent?.session === session)` 用**引用相等**确认事件属于当前 agent（呼应坑 L4）。

### 2.10 loopx 服务类骨架：不继承任何基类，自己管生命周期（`src/goalbar/service.ts` 节选，逐字）

```ts
export interface GoalBarServiceHandle {
  handle(
    request: GoalBarRequestV1,
    signal: AbortSignal,
  ): Promise<GoalBarResponseV1>
  dispose(): Promise<void>
}

export class GoalBarService implements GoalBarServiceHandle {
  private readonly disposal = new AbortController()
  private activeAction?: ActionAdmission | undefined
  private disposed = false

  constructor(options: GoalBarServiceOptions) {
    // …(字段赋值略)
  }

  async handle(
    request: GoalBarRequestV1,
    signal: AbortSignal,
  ): Promise<GoalBarResponseV1> {
    try {
      if (request.op === 'read') return await this.readResponse(request, signal)
      if (request.op === 'watch') return await this.watchResponse(request, signal)
      return await this.actionResponse(request, signal)
    } catch {
      return fixedGoalBarFailureResponseV1(request)
    }
  }

  async dispose(): Promise<void> {
    if (!this.disposed) {
      this.disposed = true
      this.disposal.abort()
      this.watchService.dispose()
    }
    await this.activeAction?.completion
  }
}

export function createGoalBarService(
  options: GoalBarServiceOptions,
): GoalBarService {
  return new GoalBarService(options)
}
```

**可抄点（"类式服务"的正确姿势）**：
1. **先定义 `interface XxxHandle`**（对外契约），`class` 只 `implements` 它——**不 extends Cordis 的 Service**；
2. 服务类自己持有一个 `AbortController` 作 `disposal`，`dispose()` **幂等**（`if (!this.disposed)`）；
3. `dispose()` 结束后 `await this.activeAction?.completion`，**等待进行中的动作收尾**，避免"卸载时还在改状态"；
4. 对外暴露一个 `createXxxService(options)` 工厂函数，而不是让调用方 `new`；
5. `handle()` 顶层 `try/catch`，任何意外都翻译成**类型化的失败响应**返回，而不是把异常抛给 RPC 边界。

### 2.11 loopx 客户端半侧入口（`src/client/index.tsx` 全文，逐字）

```tsx
import type { Context } from '@deepseek-ai/cordis'
import type { ConnectionHandle } from '@deepseek-ai/dsh-client-connection/client'
import type {} from '@deepseek-ai/dsh-client-locale/client'
import type {} from '@deepseek-ai/dsh-client-runtime/client'
import type {} from '@deepseek-ai/dsh-client-ui-conversation/client'

import { LoopXGoalBar } from './LoopXGoalBar.tsx'
import { ensurePluginStyle } from './goalbar.module.css'
import {
  GOALBAR_LOCALES,
  GOALBAR_LOCALE_NAMESPACE,
} from './locale.ts'
import { createGoalBarRpc } from './rpc.ts'

const PACKAGE_ID = 'dsh-loopx-plugin'

/** Cordis service names required before the materialized Client plugin applies. */
export const inject = ['connection', 'locale', 'slots'] as const

type GoalBarClientContext = Context & {
  readonly connection: ConnectionHandle
}

/** Register the exact-Session LoopX GoalBar contribution and its owned copy. */
export function apply(ctx: GoalBarClientContext): void {
  // Client module exports are cached across a same-page plugin reapply, so CSS
  // installation must be an explicit, idempotent apply-time operation.
  ensurePluginStyle()

  // Register ownership immediately after installation, before any later apply
  // step can fail, so Cordis rollback and ordinary unload both remove the tag.
  ctx.effect(() => () => {
    if (typeof document === 'undefined') return
    for (const style of document.querySelectorAll('style[data-plugin]')) {
      if (style.getAttribute('data-plugin') === PACKAGE_ID) style.remove()
    }
  }, 'dsh-loopx-plugin CSS ownership')

  ctx.effect(
    () => ctx.locale.register(GOALBAR_LOCALE_NAMESPACE, GOALBAR_LOCALES),
    'dsh-loopx-plugin GoalBar locale',
  )

  const rpc = createGoalBarRpc(
    ctx.connection.rpc,
    Reflect.has(ctx.connection, 'generation'),
  )
  ctx.slots.inject('conversation.input.dock', () => ctx.slots.register({
    name: 'conversation.input.dock',
    id: 'loopx-goal',
    order: 15,
    locale: GOALBAR_LOCALE_NAMESPACE,
    inject: sessionId => ({
      rpcSessionId: String(sessionId),
      rpc,
      subscribeConnectionReset: (listener: () => void) => (
        ctx.on('connection/reset', listener)
      ),
    }),
  }, LoopXGoalBar))
}
```

**可抄点（客户端半侧）**：
- 客户端入口同样是**具名** `inject` + `apply`，但 `inject` 是**客户端服务名**（`connection`/`locale`/`slots`），与宿主侧同名不同义；
- 通过 `ctx.slots.inject('conversation.input.dock', ...)` 往 DSH 对话输入区的 dock 里**插一个 React 组件**（`LoopXGoalBar`），用 `order` 控制排序；
- 组件的 `inject: sessionId => ({...})` 把**当前会话 id** 注入组件，同时把 `ctx.on` 的订阅能力传下去；
- 所有 `ctx.effect` 都带**第二个字符串参数**（用途描述），方便日志与排查。

### 2.12 loopx `cordis.patch.yml`（全文，逐字）

```yaml
# LoopX owns Goal, Todo, quota, and thread-binding authority.
- insert:
    # The package-root Host row is also the discovery anchor for dsh.client.
    - id: loopx-goalbar
      name: dsh-loopx-plugin

    - id: loopx-init-command
      name: dsh-loopx-plugin/init-command

    - id: loopx-driver
      name: dsh-loopx-plugin/driver

    # Loaded as its own default-off Cordis row. It has no Driver or Agent
    # injection and registers only session publication hooks when fully pinned.
    - id: loopx-shadow-observer
      name: dsh-loopx-plugin/observer

# The browser must not advertise readiness while first-run skill bootstrap is
# still in flight. A safe bootstrap failure also publishes the service, so DSH
# remains usable and /loopx-init can repair it.
- id: webserver
  name: '@deepseek-ai/dsh-host-webserver'
  inject: [webStartup, loopxBootstrap]

- id: web-runtime
  name: '@deepseek-ai/dsh-web-app'
  inject: [webStartup, loopxBootstrap]
```

**可抄点（patch 语法）**：
- `- insert:` 下面是一个**列表**，每行有 `id` 和 `name`；`name` 既可以是**包名**（`dsh-loopx-plugin`），也可以是**包的子导出**（`dsh-loopx-plugin/driver`、`dsh-loopx-plugin/observer`），与 `package.json` 的 `exports` 对应；
- 已存在的行（`webserver` / `web-runtime`）用**顶层** `- id/name/inject` 覆写，`inject` 列表里加上自家的 `loopxBootstrap`，从而把"Web 就绪"**挂到** LoopX 引导完成的边界上；
- 注释里点明了关键次序约束：依赖服务未 provide 前，被 inject 的行不会激活。

### 2.13 loopx `package.json`（全文；此处为前半段，后半段见 2.13b）

```json
{
  "name": "dsh-loopx-plugin",
  "version": "0.1.1-beta.5",
  "description": "One-step LoopX bootstrap, same-session driver, and local GoalBar for DeepSeek Harness",
  "type": "module",
  "main": "./lib/index.js",
  "types": "./lib/types/index.d.ts",
  "exports": {
    ".": {
      "types": "./lib/types/index.d.ts",
      "default": "./lib/index.js"
    },
    "./init-command": {
      "types": "./lib/types/init-command.d.ts",
      "default": "./lib/init-command.js"
    },
    "./driver": {
      "types": "./lib/types/driver.d.ts",
      "default": "./lib/driver.js"
    },
    "./observer": {
      "types": "./lib/types/observer.d.ts",
      "default": "./lib/observer.js"
    },
    "./client": {
      "types": "./lib/types/client/index.d.ts",
      "default": "./lib/client.js"
    },
    "./cordis.patch.yml": "./cordis.patch.yml",
    "./package.json": "./package.json"
  },
  "files": [
    "lib/*.js",
    "lib/types/**/*.d.ts",
    "cordis.patch.yml",
    "README.md",
    "LICENSE",
    "NOTICE"
  ],
  "engines": {
    "node": "^22.19.0 || >=24.0.0"
  },
  "scripts": {
    "build": "node scripts/build.mjs",
    "typecheck": "tsc -p tsconfig.host.json --noEmit && tsc -p tsconfig.client.json --noEmit && tsc -p tsconfig.tests.json",
    "test": "vitest run",
    "prepack": "pnpm build",
    "smoke:artifact": "node smoke/dsh-client-artifact-smoke.mjs",
    "smoke:peer-range": "node smoke/dsh-peer-range-smoke.mjs",
    "smoke:profile": "node smoke/dsh-profile-smoke.mjs",
    "smoke:runtime": "node smoke/dsh-goalbar-runtime-smoke.mjs",
    "smoke:docker": "bash smoke/dsh-clean-docker-smoke.sh"
  },
  "dsh": {
    "bundle": {
      "patch": "./cordis.patch.yml"
    },
    "client": {
      "inject": [
        "@deepseek-ai/dsh-client-connection",
        "@deepseek-ai/dsh-client-locale",
        "@deepseek-ai/dsh-client-runtime",
        "@deepseek-ai/dsh-client-ui-conversation"
      ],
      "platform": "web"
    }
  },
```
  "peerDependencies": {
    "@deepseek-ai/cordis": "^4.0.1",
    "@deepseek-ai/dsh": ">=0.1.0-rc.7 <0.1.1 || >=0.1.1-rc.1 <0.2.0-0",
    "@deepseek-ai/dsh-client-connection": ">=0.1.0-rc.7 <0.1.1 || >=0.1.1-rc.1 <0.2.0-0",
    "@deepseek-ai/dsh-client-locale": ">=0.1.0-rc.7 <0.1.1 || >=0.1.1-rc.1 <0.2.0-0",
    "@deepseek-ai/dsh-client-runtime": ">=0.1.0-rc.7 <0.1.1 || >=0.1.1-rc.1 <0.2.0-0",
    "@deepseek-ai/dsh-client-ui-conversation": ">=0.1.0-rc.7 <0.1.1 || >=0.1.1-rc.1 <0.2.0-0",
    "@deepseek-ai/dsh-client-ui-primitives": ">=0.1.0-rc.7 <0.1.1 || >=0.1.1-rc.1 <0.2.0-0",
    "@deepseek-ai/dsh-client-ui-slots": ">=0.1.0-rc.7 <0.1.1 || >=0.1.1-rc.1 <0.2.0-0",
    "react": "^18.2.0"
  },
  "peerDependenciesMeta": {
    "@deepseek-ai/cordis": { "optional": true },
    "@deepseek-ai/dsh": { "optional": true },
    "@deepseek-ai/dsh-client-connection": { "optional": true },
    "@deepseek-ai/dsh-client-locale": { "optional": true },
    "@deepseek-ai/dsh-client-runtime": { "optional": true },
    "@deepseek-ai/dsh-client-ui-conversation": { "optional": true },
    "@deepseek-ai/dsh-client-ui-primitives": { "optional": true },
    "@deepseek-ai/dsh-client-ui-slots": { "optional": true },
    "react": { "optional": true }
  },
  "devDependencies": {
    "@deepseek-ai/cordis": "4.0.1",
    "@deepseek-ai/dsh": "0.1.1-rc.2",
    "@deepseek-ai/dsh-agent": "0.1.1-rc.2",
    "@deepseek-ai/dsh-client-connection": "0.1.1-rc.2",
    "@deepseek-ai/dsh-client-locale": "0.1.1-rc.2",
    "@deepseek-ai/dsh-client-runtime": "0.1.1-rc.2",
    "@deepseek-ai/dsh-client-ui-conversation": "0.1.1-rc.2",
    "@deepseek-ai/dsh-client-ui-primitives": "0.1.1-rc.2",
    "@deepseek-ai/dsh-client-ui-slots": "0.1.1-rc.2",
    "@deepseek-ai/dsh-commands": "0.1.1-rc.2",
    "@deepseek-ai/dsh-llm": "0.1.1-rc.2",
    "@deepseek-ai/dsh-session": "0.1.1-rc.2",
    "@types/node": "^22.19.0",
    "@types/react": "~18.3.1",
    "@types/react-dom": "~18.3.1",
    "jsdom": "^26.1.0",
    "lightningcss": "1.33.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "tsdown": "0.22.2",
    "typescript": "^6.0.3",
    "vitest": "^4.1.8"
  },
  "repository": {
    "type": "git",
    "url": "git+https://github.com/huangruiteng/loopx.git",
    "directory": "packages/dsh-loopx-plugin"
  },
  "license": "Apache-2.0",
  "publishConfig": {
    "access": "public"
  }
}
```

**可抄点**：
- `dsh.client.inject` 列出**客户端模块名**（`@deepseek-ai/dsh-client-*`），`platform: "web"` 表示只在 Web 表面挂载；**这是与 MemOS/archify 的关键差异**：只有 loopx 同时声明了 `dsh.bundle` + `dsh.client`；
- `exports` 里为宿主多行（`./init-command`、`./driver`、`./observer`、`./client`）各开一个子导出，**patch 的 `name` 正好引用它们**；
- peer 全是 `optional: true` + `peerDependenciesMeta`，通过 `smoke:peer-range` 脚本自证"实测版本落在 peer 范围内"（坑 L2）。

### 2.14 【同类里最小的服务定义 / 插件入口】横向对比

| 角色 | 文件 | 行数 | 是否有 `apply` | 是否有 `inject` | 生命周期 |
|---|---|---|---|---|---|
| **最小"路径解析助手"**（严格说不是插件，但可当"入口模块"最小样板） | archify `integrations/deepseek-harness/lib/index.js` | 22 | 无 | 无 | 无 |
| **最小"服务生命周期"插件** | loopx `packages/dsh-loopx-plugin/src/index.ts` | 29 | 有 | 有（3 个） | `ctx.effect` 返回 async disposer |
| 中等"条件关闭"插件 | loopx `src/observer.ts` 的 `apply` | 6（apply 本体） | 有 | 无 | `if (config===undefined) return` |
| 大型"记忆服务"插件 | MemOS `adapters/deepseek-harness/index.ts` | 487 | 有（async） | 有（3 个） | `registrations[]` + 回滚 + 返回卸载函数 |

**结论：教学首选 loopx `src/index.ts`（29 行）作为"怎么写一个有生命周期的服务插件"的最小范本。**
它完整演示了：具名 `name`/`inject`、`ctx.effect` 建服务与 RPC、返回 disposer 卸载、以及"inject 一个自家 provide 的服务名"。想看"全量工程化"再升级到 MemOS 的 487 行版本。

**绝对最小的入口模块范本**（archify `lib/index.js` 全文，逐字，22 行）——注意它**没有 `apply`**，因为 archify 的 `cordis.patch.yml` 插入的是 DSH 内置 provider，这个文件只被测试直接 import：

```js
import { createRequire } from 'node:module';
import { dirname, join } from 'node:path';

export const name = 'archify-dsh';
export const PACKAGE_NAME = '@tt-a1i/archify-dsh';

export function resolveArchifySkillRoot(profileBaseUrl) {
  if (!profileBaseUrl) {
    throw new Error('archify-dsh: missing DSH profile baseUrl for package resolution');
  }
  let manifestPath;
  try {
    manifestPath = createRequire(profileBaseUrl).resolve(`${PACKAGE_NAME}/package.json`);
  } catch (error) {
    throw new Error(
      `archify-dsh: cannot resolve ${PACKAGE_NAME}/package.json from the DSH profile`,
      { cause: error },
    );
  }
  return join(dirname(manifestPath), 'skills');
}
```

**重要提醒**：archify 的 `package.json` 里 `"main": "./lib/index.js"`，但**patch 从未引用它**；Loader 加载的是 patch 里 `name: '@deepseek-ai/dsh-skill-filesystem'`。所以"包有 `main`/`exports`" ≠ "它会被当插件加载"，**真正的装配入口由 `cordis.patch.yml` 的 `name` 决定**。

---

## 三、该方向的开发规范（只在多家都这么做时才归纳）

> 每条规范都标注**依据**（哪几个仓库、哪几个文件）。只有"多家共识"才写"规范"；单家独有写"某仓库的做法"。

### 规范 1：插件入口一律**具名**导出 `name` / `inject` / `Config` / `apply`；**不要 default export**

- **依据（3/3 家）**：
  - MemOS：`adapters/deepseek-harness/index.ts` → `export const name`、`export const inject = ["systemPrompt","tools","llm"]`、`export const Config`、`export async function apply`；
  - loopx：`src/index.ts` / `src/driver.ts` / `src/observer.ts` / `src/init-command.ts` / `src/client/index.tsx` 全部具名 `name`/`inject`/`apply`；
  - archify：`lib/index.js` 也是具名 `name`。
- 补充：`grep -rn "export default"` 在三个仓库的插件代码里**只**命中一个与插件无关的 `css-modules.d.ts`。这与手册背景"绝不能有 default export（官方复盘 0001）"一致。

### 规范 2：生命周期/副作用统一用 `ctx.effect(...)` 或"注册函数返回 disposer + 数组统一回收"

- **依据（3/3 家）**：
  - loopx：`ctx.effect(() => {...; return async () => {...}}, '描述')`（`src/index.ts`）、`ctx.effect(function* () {...; yield async () => {...}}, '描述')`（`src/driver.ts`、`src/observer.ts`）、客户端同样 `ctx.effect(...)`（`src/client/index.tsx`）；
  - MemOS：`registrations.push(ctx.on(...))` + `unregisterAll()` 倒序回收（`adapters/deepseek-harness/index.ts`）；工具侧同样的 `disposers` 数组（`tools.ts`）；
  - archify：无副作用（README 明确"no background service / no telemetry / no install hooks"），是"零副作用"的另一种合规姿态。
- 描述字符串：loopx 所有 `ctx.effect` 都带第二个参数（用途），建议照抄这个习惯。

### 规范 3：发布服务的名字用**字符串**，消费方用 `inject: [...]` 或 `ctx.get('...')`

- **依据**：loopx `init-command.ts` 用 `ctx.reflect.provide('loopxBootstrap', status)`；同包 3 个插件用 `inject: ['agents','connection','loopxBootstrap']` 消费；patch 里 `inject: [webStartup, loopxBootstrap]`。
- **只有 1 家**做"provide + inject"，但它是本方向唯一的服务发布活例，建议作为该方向的样板。

### 规范 4：配置定义二选一，且都要有默认值

- **依据（2 家做法不同）**：
  - MemOS（DSH 插件层）：用 **schemastery** `export const Config: Schema<Config> = Schema.object({ ... .default(...) })`，且在 `interface Config` 里给类型（`adapters/deepseek-harness/index.ts`）；
  - MemOS（内核层 `core/config/schema.ts`）：用 **@sinclair/typebox** `Type.Object({...})`，并且"每个字段必须有 default，旧配置才能升级"（`core/config/README.md` 原文：`Adding fields: provide a default in defaults.ts (so old configs upgrade). Removing fields: log a warning at load time; don't crash.`）；
  - loopx：**完全不声明 `Config`**，配置走环境变量 + `resolve*Config()`（`src/observer.ts` 的 `resolveShadowObserverConfig()`），配置不完整就整体 off。
- 共识：**没有默认值 / 校验失败的路径必须有明确降级策略**（MemOS 缺失配置文件→用 defaults + 警告；loopx 配置不全→off）。

### 规范 5：`cordis.patch.yml` 用 `- insert:` 列表；`name` 指向"包名或包子导出"，与 `package.json` 的 `exports` 对齐

- **依据（3/3 家）**：三家都写 `dsh.bundle.patch`；loopx 的 patch `name` 直接用子导出（`dsh-loopx-plugin/driver` 等），并与其 `exports` 字段严格对应；MemOS 用**编译后**路径（`dist/adapters/deepseek-harness/index.js`）；archify 用 `!!js` 内联解析。
- 覆写已存在行时用**顶层** `- id/name/inject`（loopx 对 `webserver`/`web-runtime` 的做法）。
- 关于 `!!js`：只有 archify 用它（在插件 `config` 内），与手册背景"`!!js` 只在插件 config 与 entry 的 disabled 内被求值"一致。

### 规范 6：要写测试，且测试要覆盖"干净构建 / 打包产物"

- **依据（2/3 家做得很足）**：
  - MemOS：`tests/` 有 205 个文件，含 `deepseek-harness-*.test.ts` 6 个；提交 `b41c899` 明确"新增回归测试覆盖两种干净布局，包括包根本身名为 dist 的情况"；
  - archify：`test/` 10 个 `.test.mjs`，含 `package-contract.test.mjs`（断言必须有 `dsh.bundle.patch`、**不得**有 install 生命周期脚本、不得有 dependencies）、`tarball-contract.test.mjs`、`zero-regression.test.mjs`；
  - loopx：`tests/` 10 个 `*.spec.ts` + `smoke/` 5 个冒烟脚本（artifact/profile/runtime/docker/peer-range）。
- 共识：**测试要跑"打包后的产物"**，而不只是源码（呼应坑 A4/M2）。

### 规范 7：README 要写清"安装 / 升级 / 卸载 / 失败行为 / 已知限制 / 安全边界"，并诚实标注"非官方"

- **依据（3/3 家）**：
  - MemOS `adapters/deepseek-harness/README.md` 有 `Install` / `Uninstall` / `Failure behavior` / `Known limitations`(7 条) / `Privacy and security`，并给了**字段表**；
  - loopx `README.md` 有 `Install` / `Uninstall` / `Shadow observer` / 权限与隐私边界 / `Maintainer release and marketplace handoff`；
  - archify `README.md` 第一行就写 `This is **not** an official DeepSeek product and does not imply DeepSeek endorsement.`，并单列 `Security posture`。

### 规范 8（弱共识，仅供注意）：`inject` 是**数组**；`name` 用**包名或短横线命名**

- **依据（3/3 家的宿主侧入口）**：MemOS `inject = ["systemPrompt","tools","llm"]`；loopx `inject = ['agents','connection','loopxBootstrap']`；archify 无 inject（不适用）。客户端 loopx `inject = ['connection','locale','slots']`。
- 命名：包名 `dsh-loopx-plugin` / `@tt-a1i/archify-dsh`，插件 `name` 与之对应（`dsh-loopx-plugin`、`archify-dsh`）。

### 明确**没有**形成规范的点（提示手册不要写死）

- **是否用 `default export 服务类`**：3 家都没有 → 本方向**不要**把它写成规范，反而应写"本批真实仓库不使用该写法"。
- **是否继承某个 `Service` 基类**：0 家 → 类式服务（loopx `GoalBarService`）只是**普通 class + interface + AbortController 自管理**。
- **是否写 `Config`**：2/3 家写、1 家不写 → 不是硬性规范。

---

## 四、新手最容易卡住的 5 个点（附一句可执行建议）

> 全部来自上面的真实坑，按"对零经验者的致命程度"排序。

### 卡点 1：以为用了 `default export` 也没关系 —— 结果 `inject` 被静默丢弃

- **为什么致命**：官方复盘 0001 已确认 default export 会让 Loader 丢掉 `inject`；插件看似加载了，但服务依赖全没注入，行为诡异且不报错。新手最容易在 e2e 里写 `export default` 图省事。
- **建议**：入口**只写具名导出** `export const name` / `export const inject` / `export function apply`，提交前 `grep -n "export default"` 自查必须为空。

### 卡点 2：卸载/热重载时副作用没回收 —— 监听器叠加、样式重复、端口占用

- **为什么致命**：HMR 会**再次调用** `apply`；客户端模块导出还会被缓存（loopx 源码注释原话）。没回收就是"重载越多次越坏"，且常表现为"偶尔"。
- **建议**：**每写一个 `ctx.on`/注册调用，就立刻放进 `ctx.effect(...)`**（或 push 进数组并返回 disposer）；`apply` 里的副作用必须**幂等**。

### 卡点 3：任何"等后台任务"的 await 不设超时 —— 卸载/关整天卡死

- **为什么致命**：MemOS 真实事故：一个无超时的 `await` 让 `SIGTERM` 后卡 10 分钟被强杀（坑 M1）。新手不知道"后台 LLM 有 163 次串行调用"这种事。
- **建议**：**给每个等待后台工作的 await 都套 `withTimeout(promise, ms, "名字")`**，并在代码注释里写清"超时后丢不丢数据"。

### 卡点 4：路径靠"猜"或"拼" —— dev 能跑、打包/CI 必坏

- **为什么致命**：用 `existsSync` 猜包根（坑 M2）、把包名拼到 `baseUrl` 上（坑 A2）都会在干净构建或换机器时崩。新手无法复现"CI 才失败"。
- **建议**：**定位已安装的包一律用 `createRequire(锚点).resolve('<包名>/package.json')`**；路径拼接一律用 `node:path`，绝不用字符串手动拼 `/` 或 `\`。

### 卡点 5：把"能改状态的动作"当成普通函数 —— 双击/重复请求导致状态被改两次

- **为什么致命**：状态内核里 `Start`/`Pause` 这类动作真的会改权威数据；新手的按钮没有锁，连点两次就发起两次变更（坑 L5）。而且"拒绝/结果不确定"时如果解锁，用户会重复点，越点越乱。
- **建议**：**前端锁（`xxxGuardRef`）+ 后端锁（`activeAction`）双保险**；只有"显式刷新"或"会话切换"才解锁，拒绝与不确定结果**故意保持锁定**。

---

## 五、给手册写作的提醒（本方向特有）

1. **不要写"服务式插件用 default export 服务类"** —— 本批 3 个真实仓库**都不是**，会误导读者。可写"DSH 历史上存在该写法，但本批实战仓库统一用函数式具名导出 + `ctx.reflect.provide`"。若需引用 default export 服务类，需另找官方模板（不在本次素材内）。
2. **两种 `required` 的对照表一定要做成醒目小卡**：`parameters` 属性级 `required: true`（DSH DSL）vs `output.schema` 对象级 `required: ['a','b']`（标准 JSON Schema），不可混用。
3. **`!!js` 只出现在插件 config 内**：本批只有 archify 用它，且用于"解析已安装包路径"，是很好的正例。
4. **"行顺序不影响加载顺序"** 在 loopx 的 patch 里有旁证：`webserver`/`web-runtime` 靠 `inject: [..., loopxBootstrap]` 决定激活时机，而不是靠行序。

---

## 附：本文实际读取的源码/测试/文档文件清单（30 项）

1. `MemTensor_MemOS/apps/memos-local-plugin/adapters/deepseek-harness/index.ts`（全文 487 行）
2. `MemTensor_MemOS/apps/memos-local-plugin/adapters/deepseek-harness/tools.ts`（节选：头部 + 参数 DSL + 尾部回收）
3. `MemTensor_MemOS/apps/memos-local-plugin/adapters/deepseek-harness/host-llm.ts`（头部）
4. `MemTensor_MemOS/apps/memos-local-plugin/adapters/deepseek-harness/cordis.patch.yml`（全文）
5. `MemTensor_MemOS/apps/memos-local-plugin/adapters/deepseek-harness/README.md`（全文）
6. `MemTensor_MemOS/apps/memos-local-plugin/package.json`（全文）
7. `MemTensor_MemOS/apps/memos-local-plugin/CHANGELOG.md`（头部）
8. `MemTensor_MemOS/apps/memos-local-plugin/core/config/README.md`（全文）
9. `MemTensor_MemOS/apps/memos-local-plugin/core/config/schema.ts`（头部）
10. `MemTensor_MemOS/AGENTS.md`（grep）
11. `huangruiteng_loopx/packages/dsh-loopx-plugin/src/index.ts`（全文 29 行）
12. `huangruiteng_loopx/packages/dsh-loopx-plugin/src/driver.ts`（第 1130–1206 行）
13. `huangruiteng_loopx/packages/dsh-loopx-plugin/src/observer.ts`（第 585–624 行）
14. `huangruiteng_loopx/packages/dsh-loopx-plugin/src/init-command.ts`（第 530–632 行）
15. `huangruiteng_loopx/packages/dsh-loopx-plugin/src/goalbar/service.ts`（全文 745 行）
16. `huangruiteng_loopx/packages/dsh-loopx-plugin/src/client/index.tsx`（全文 61 行）
17. `huangruiteng_loopx/packages/dsh-loopx-plugin/src/client/rpc.ts`（全文）
18. `huangruiteng_loopx/packages/dsh-loopx-plugin/src/client/useGoalBar.ts`（全文 392 行）
19. `huangruiteng_loopx/packages/dsh-loopx-plugin/cordis.patch.yml`（全文）
20. `huangruiteng_loopx/packages/dsh-loopx-plugin/package.json`（全文）
21. `huangruiteng_loopx/packages/dsh-loopx-plugin/smoke/dsh-peer-range-smoke.mjs`（全文）
22. `huangruiteng_loopx/packages/dsh-loopx-plugin/README.md`（全文）
23. `huangruiteng_loopx/docs/plans/2026-08-20-dsh-native-skill-driver.md`（头部 130 行）
24. `huangruiteng_loopx/AGENTS.md`（grep）
25. `tt-a1i_archify/integrations/deepseek-harness/lib/index.js`（全文 22 行）
26. `tt-a1i_archify/integrations/deepseek-harness/cordis.patch.yml`（全文）
27. `tt-a1i_archify/integrations/deepseek-harness/package.json`（全文）
28. `tt-a1i_archify/integrations/deepseek-harness/README.md`（全文）
29. `tt-a1i_archify/integrations/deepseek-harness/test/package-contract.test.mjs`（头部）
30. `tt-a1i_archify/integrations/deepseek-harness/test/adapter-security.test.mjs`（全文）

（另：git 历史读取 3 个仓库的 `git log` / `git show -s`，共核实 20+ 条 commit 元数据。）

> 全文完。所有代码块逐字来自本地源码快照；所有坑均有 commit 哈希或源码行号佐证；查不到的已明确标注"未找到"。

---

<!-- ↓ 源：D-host-bundle.md （全文） -->

﻿# D. 宿主 / 桌面 / 组合 bundle / 工程规范化 —— 踩坑记录 + 可抄模板（原始素材）

> 调研对象（4 个仓库，源码快照 + git 历史均已在本地）：
> - `Q00_ouroboros` —— `dsh-ouroboros`（约 5800★），官方清单里唯一「纯配置、零代码」组合包
> - `anywhere-labs_dsh-desktop` —— `dsh-plugin-desktop`（约 25000★），桌面宿主插件
> - `xiaobright_dsh-anchored-standard` —— 126 文件的 preset 包（工程规范化方向）
> - `omdsh-dev_DSH-better-sidebar` —— 644 commits 的「可被第三方注册新页面」侧边栏底座
>
> 源码根（生成期，**不随本 skill 发布**）：`<社区仓库快照>/src/<仓库>/`
> git 根（生成期）：`<社区仓库快照>/repos/<仓库>/`
> 官方 DSH 源码（用于交叉验证机制）：`<DSH 检出>/`
>
> 规则：代码**逐字照抄**，超长标 `…(略)`；每个结论标注 `仓库 + 文件路径` 或 `仓库 + commit`；查不到写「未找到」，绝不编造。

---

## 0. 先给结论：本方向的「一句话真相」

| 真相 | 证据 |
|---|---|
| **组合包 = 一个 package.json + 一个 cordis.patch.yml + 一个 README，可以零行 JS 代码。** | `Q00_ouroboros/integrations/dsh-plugin/` 只有 3 个文件（`package.json` / `cordis.patch.yml` / `README.md`） |
| `package.json` 里声明 `"dsh": { "bundle": { "patch": "./cordis.patch.yml" } }`，profile 合成器就认。 | 官方 `packages/boot/app-boot/src/profile.ts:780-792`：`const declared = bundleManifest.dsh?.bundle?.patch`；`if (declared === undefined) throw ... declares no dsh.bundle` |
| patch 的相对路径 `name: ./xxx.mjs` **确实被锚到 patch 文件旁边**（官方文档口吻是「绝对路径」，源码实现允许相对）。 | 官方 `packages/boot/app-boot/src/index.ts` `anchorInsertedPluginNames()`：`const base = dirname(resolve(file))` → `entry.name = pathToFileURL(resolve(base, entry.name)).href` |
| `!!js` 由 Loader 针对每个 entry 的注入就绪 context 求值，因此 `!!js` 里能读到 `process.env`、`ctx.loader.entries()`。 | 官方 `packages/boot/app-boot/src/index.ts:220-225` 注释：`!!js` scalars become expression nodes the Loader interpolates against each entry's injection-ready context |
| 行顺序**不**决定加载顺序（激活由服务可用性驱动）；但**同一 patch 内 `!!js` 表达式的可见性**是「只看得见它之前的行」。 | `omdsh-dev_DSH-better-sidebar/cordis.patch.yml` 注释原文：`The loader evaluates it when this row is processed (entry-list order, only rows before this one are visible)` |
| 安装命令 `--profile` **必填**，省略直接报错。 | 官方 `apps/cli/src/args.ts:192` `.requiredOption('--profile <name>', ...)`；`Q00_ouroboros` commit `5258cb19` 原文：「`apps/cli/src/args.ts` declares `.requiredOption('--profile <name>')` on `dsh plugin`, so the root README's command errored out instead of installing」 |

---

# 一、踩坑记录（现象 → 根因 → 怎么修）

> 标注格式：`仓库 + commit 短哈希 + 提交信息原文`。凡提交 body 为空（只有标题）的，写明「body 为空」，不编造细节。

## 1. `Q00_ouroboros`（dsh-ouroboros）

### 坑 1.1　`dsh plugin add` 命令少了 `--profile` —— 照 README 抄会直接报错
- **仓库 + commit**：`Q00_ouroboros` + `5258cb19`（2026-08-17）
- **提交信息原文**：
  > `feat(integrations): add installable dsh plugin for Ouroboros (#2158)`
  > 正文：「**Install syntax.** `apps/cli/src/args.ts` declares `.requiredOption('--profile <name>')` on `dsh plugin`, so the root README's command errored out instead of installing. It now matches the bundle README and the verified command.」
- **现象**：照主 README 抄 `dsh plugin add ...`（漏 `--profile`），CLI 不安装，直接报 requires `--profile`。
- **根因**：`dsh plugin` 子命令声明了 `.requiredOption('--profile <name>')`，`--profile` 是强制项（源码 `apps/cli/src/args.ts:192` 佐证）。
- **修复**：所有安装命令补 `--profile <名字>`：``dsh plugin --profile <your-profile> add "github:Q00/ouroboros#main&path:integrations/dsh-plugin"``。

### 坑 1.2　凭据默认不会流进子进程（`/KEY|PASSWORD|SECRET|TOKEN/i` 被洗掉）
- **仓库 + commit**：`Q00_ouroboros` + `5258cb19`（同一条提交，review round 1 第 2 点）
- **提交信息原文（截断）**：
  > 「**Credential scrub.** `@deepseek-ai/dsh-subprocess` exports `SENSITIVE_ENV_PATTERN = /KEY|PASSWORD|SECRET|TOKEN/i` and …」
- **现象**：插件 `mcp-ouroboros` 行不给 `env` 时，被拉起的 `ouroboros mcp serve` 拿不到 `ANTHROPIC_API_KEY` / `DEEPSEEK_API_KEY`；工具能列出，第一次调用失败。
- **根因**：`@deepseek-ai/dsh-subprocess` 会把所有「凭据形状」的名字（`/KEY|PASSWORD|SECRET|TOKEN/i`）以及所有 `DSH_*` 名字从子进程环境里洗掉，「按设计不让 harness 凭据隐式泄漏」。
- **修复**：在插件行的 `config.env` 里**显式列白名单**（插件显式 env 层在 scrub **之后**合并）。参见模板 §二.1 的 `env:` 段。
- **同源踩坑**：**profile 里覆盖某行时，是整块替换该行的 `config`，不是深合并**。`Q00_ouroboros/docs/guides/deepseek-harness.md:66-70` 原文：「A later patch layer **replaces** a row's entire `config` rather than deep-merging it, so copy the bundle's `config` block and add your line to it.」→ 想加一个环境变量，必须把整段 `config` 抄过去再改，否则 timeout/args 全丢。

### 坑 1.3　「一条变量」其实不是一条变量：`dsh` LLM backend 需要绝对 composition 路径
- **仓库 + commit**：`Q00_ouroboros` + `9d58f4ab`（2026-08-17）；`a8f3cf89`（2026-08-20）
- **提交信息原文（`9d58f4ab`，截断）**：
  > 「dsh scrubs credential-shaped names (`/KEY|PASSWORD|SECRET|TOKEN/i`) from children by design and the explicit `env` layer merges after that scrub; a profile override replaces a row's whole `config` rather than deep-merging it; **a composition's plugin names resolve relative to the composition file's own directory**; and both `OUROBOROS_DSH_*` variables are on the project `.env` denylist…」
- **提交信息原文（`a8f3cf89`）**：
  > `fix(mcp): serve with an installed CLI when the SDK runtime is only inherited (#2164)`
  > 现象原文：`The MCP server cannot host the 'claude' SDK runtime in this process ...`（重复 3 次、0 个 Ouroboros 工具）
- **现象**：设了 `OUROBOROS_LLM_BACKEND=dsh`，第一次 interview/Seed/QA 调用失败，报 `invalid_config`；或机器继承 `runtime_backend: claude` 时反复报「cannot host the 'claude' SDK runtime」，且因为 `failOnStartupError: false`，dsh 照常启动、工具「静默消失」，错误看起来像噪音。
- **根因**：① `dsh` backend 会另起一个 `dsh-acp-demo` 子进程（不复用你正在聊的 dsh），它**必须**拿到一个 composition 文件才能加载，否则 fail closed；相对路径会被拒（会相对不可信的项目 cwd 解析）。② 被继承的 `claude` SDK runtime 无法在 MCP server 进程内托管。
- **修复**：① `OUROBOROS_DSH_CONFIG_PATH` 必须是**绝对路径**，且文件所在目录要能解析到 dsh 的 `node_modules`/workspace（composition 内的包名相对 composition 文件所在目录解析）。② 用可执行 runtime（`claude-cli` / `codex` / `opencode`，`a8f3cf89` 的偏好顺序是 `claude-cli` → `codex` → `opencode`），**但显式选择仍 fail**（`--runtime claude` 不替换）。
- **可抄教训**：`failOnStartupError: false` 让插件「静默消失」= 把错误变成噪音，新手会以为插件没生效。官方在 `cordis.patch.yml` 注释里明说：「Recovery is not guaranteed to be automatic … After fixing the cause, reload the plugin or restart dsh.」

### 坑 1.4　安装器自动装插件时的 profile 选择（无全局安装这回事）
- **仓库 + commit**：`Q00_ouroboros` + `3c8643f6`（2026-08-18）、`235487bb`（2026-08-18）
- **提交信息原文（`3c8643f6`，截断）**：
  > 「dsh keeps plugins per profile and `dsh plugin` requires `--profile`, so there is no global install to run. The installer therefore picks its targets: **`web`** … **Any other profile whose `package.json` already carries `dsh-ouroboros`** … **Nothing else.** Adding Ouroboros tools to someone's unrelated profile because an installer ran is not an upgrade.」
- **现象 / 根因**：**没有全局安装**；插件是「每个 profile 各装一份」。安装器若随便挑 profile，可能污染用户无关的 profile。
- **修复**：默认只装 `web`（`dsh web` 会脚手架出来的那个）；对已有 `dsh-ouroboros` 的 profile 才刷新。
- **平台相关**：`235487bb` 标题 `fix(install): preserve DSH profile names in recovery output (#2170)`，正文说用 Bash 参数展开替代 `basename` 命令替换以保留尾随换行，并处理了**空格 / 引号 / glob / 命令替换语法 / 分隔符 / 嵌入及尾随换行 / CR / ANSI 转义**这些「恶意 profile 名」。→ 教训：**profile 名和路径要当不可信输入处理**。

> ouroboros 仓库内 `fix(...)` 提交虽多（`1c968328`、`cd13da16`、`03714ba4` 等），但绝大多数是 Python 侧 agent 内核（seed/evidence/mcp），**与 dsh 插件装载无关**，故不计入本方向。dsh 方向有解释的坑就是上面 4 条（来源：`Q00_ouroboros` git log `--grep='dsh-plugin|integrations/dsh|dsh plugin|DeepSeek Harness'` + 全量 `fix` 扫描）。
---

## 2. `anywhere-labs_dsh-desktop`（dsh-plugin-desktop）

> 该仓库的提交多为 squash merge，**commit body 普遍为空，只有标题**。真正的「解释」全部写在 `.agents/notes/implemented/` 下的架构笔记里（中文 + 英文 + i18n.yaml，逐篇是「问题 / 决策 / 验证 / 备选 / 结果」五段式）。下面每条都用「笔记正文」当证据，标注笔记文件路径。

### 坑 2.1　打包后 profile 的符号链接进不了 `app.asar` → `ENOTDIR`
- **来源**：`anywhere-labs_dsh-desktop/.agents/notes/implemented/architecture/2026-08-15-packaged-profile-fallback.zh.md`
- **现象（原文）**：「打包后的 Electron 进程可以通过虚拟 `app.asar` 文件系统直接读取文件，但操作系统符号链接无法进入该虚拟归档。若把逻辑打包 manifest 作为安装锚点，就会生成在 Loader 激活 Web bundle 前以 `ENOTDIR` 失败的链接。」
- **根因**：Electron 能读 ASAR 虚拟路径，但 Node 经操作系统 symlink 访问 profile 依赖时，ASAR 路径不是真实目录。
- **修复**：Electron Builder 把 manifest / patch / node_modules 一起解包；Desktop Host 在 `healProfilesModuleFallback` 前把安装锚点从 `app.asar/package.json` 映射到 `app.asar.unpacked/package.json`；每次启动修复旧链接，且**不改**被选 profile 的 manifest/patch。打包前若缺物理 manifest 或 desktop 插件子路径则**签名前就失败**。

### 坑 2.2　打包 pnpm 的 PATH 只能给子进程 → Host 插件发现不到 package manager
- **来源**：`anywhere-labs_dsh-desktop/.agents/notes/implemented/architecture/2026-08-15-desktop-bundled-pnpm-runtime.zh.md`
- **现象（原文）**：「该终端拥有只属于其子进程的 `PATH`，因此 Cordis Host 插件与当前 desktop generation 启动的 subprocess 无法发现内置 package manager。调用 `pnpm` 的插件会在终端与应用运行时表现不一致。」
- **根因**：内置 pnpm 的命令目录只进了终端子进程的 PATH，没进 Electron main / Host 的 PATH。
- **修复**：Launcher 先跑账户 login shell 恢复 `PATH`（只从固定 allowlist 补 locale/工具链/pkg manager/venv），再把只含 `pnpm`（Windows 是 `pnpm.cmd`）的私有 runtime 目录**前置**到 Electron main 的 PATH。**明确拒绝**两种替代方案（原文）：「把完整终端 shim 目录加入 Host PATH」会覆盖每个插件里的 `node` 与 `dsh`；「在 Electron 进程中设置 Node-mode 与 ABI 变量」会让无关 Electron 子进程继承。
- **平台细节（可抄）**：`ELECTRON_RUN_AS_NODE` 只应存在于 pnpm subprocess tree，生成的 prelude 会在运行前**移除所有大小写形式**的该变量；Windows 上 batch 命令需要 `shell: true`，第三方插件若 `spawn('pnpm', { shell: false })` 无法执行 `pnpm.cmd`。

### 坑 2.3　renderer OOM 后主窗口空白，Host 还活着 → 需要「有界」自动恢复
- **来源**：`anywhere-labs_dsh-desktop/.agents/notes/implemented/architecture/2026-09-07-runtime-renderer-recovery.md`；commit `62171c601` `fix(desktop): automatically recover crashed renderers`、`5af1f8c16` `fix(desktop): recover blank and unresponsive runtime pages`（body 均为空）
- **现象（原文）**：「Issue #813 includes renderer exits reported as `oom` … A dead renderer therefore left the main window blank while the Host remained alive.」
- **根因**：所有 exit 都被转给「一次性启动健康门」，而该门在 healthy boot 之后正确忽略失败 —— 于是**运行时**没有任何恢复。
- **修复（关键数字，可抄）**：每次 shell generation 拥有一个恢复 controller，**3 次尝试**，延迟 **0 / 1 / 3 秒**；一次 reload 必须同时满足「页面加载完成」+「30 秒内健康的 client Loader 报告」才算恢复；**只有连续健康满 1 分钟才重置尝试计数**（防「crash→reload→healthy」循环绕过上限）。耗尽后才弹用户态提示，且**故意用 Electron 系统原生 message box**（原文：「recovery from a renderer OOM must not require another Chromium-rendered UI」）。兼容模式有 content + titlebar **两个** WebContents，两个都要 reload 且都要健康。

### 坑 2.4　启动资源的释放顺序散落在 3 条路径 → 引入单一 owner
- **来源**：`anywhere-labs_dsh-desktop/.agents/notes/implemented/architecture/2026-08-19-desktop-startup-resource-ownership.zh.md`
- **现象（原文）**：「一个 Desktop 进程会创建 Cordis Host、打包 pnpm PATH 安装，以及 Windows 上的打包 DSH PATH 安装 … `main.ts` 以前用互相独立的可变变量和重复清理代码表达它们的生命周期。普通 shutdown、fail-loud 清理和启动恢复分别实现了同一套释放协议的一部分。」
- **根因**：资源属于同一启动 generation，却没有单一 owner；调用方被迫知道释放顺序。
- **修复**：引入 `DesktopStartupGeneration`，接口只有 `id` / `bindHost(host)` / `own(release)` / `quiesceForRecovery()` / `release()`；`release()` 按**注册逆序**释放（即使某个回调失败也继续）；并发恢复共享同一个 Host disposal task。

### 坑 2.5　插件安装接口「文档说的和实现不一样」→ 身份可能分离
- **来源**：`anywhere-labs_dsh-desktop/.agents/notes/implemented/architecture/2026-08-19-desktop-plugin-install-lifecycle-ownership.zh.md`
- **现象（原文）**：「公开 `desktopPnpm` 文档要求插件管理器调用 `runPlugin(['add', ...])`，但 implementation 会拒绝 `add`，并要求未公开的 `runPluginInstall()` 方法。Market adapter 只能自行发现并复制这个隐藏 interface … 隐藏方法还把安装 argv 与 recovery metadata 分开接收。调用方理论上可以安装 package A，却让 WAL 记录 package B。」
- **根因**：安装 argv 与恢复日志（WAL）是两条独立入参，没有强制同一身份。
- **修复**：`installPlugin(request)` 成为唯一受支持的 `add` 路径，它同时拥有「强制的 `add` 命令 / 唯一精确 `packageName@packageVersion` 目标 / 安装前 profile 快照 + WAL / generation 级操作门 / 进程树完整退出 / 失败恢复 / 成功后图像封存」。**结论（原文）**：「插件作者不得使用 `run()` 或 `runPlugin()` 安装插件。」

### 坑 2.6　profile 选择不能存进「被选 profile 的 settings」
- **来源**：`anywhere-labs_dsh-desktop/.agents/notes/implemented/architecture/2026-08-15-desktop-profile-management.zh.md`
- **现象（原文）**：「Profile 选择发生在 Host Cordis 树及其 settings provider 创建之前，因此不能存放在被选 profile 的 settings namespace 中。若被选 profile 启动失败，在 renderer 与托盘都无法挂载时也必须能够恢复。」启动失败时不能无限重启 —— 「last-known-good generation 自身失败时仍会 **fail loud**，从而避免重启循环」。
- **根因**：循环依赖（被选 profile 能改 settings provider，而 profile 又必须在 provider 之前确定）。
- **修复**：选择状态放在 Electron user-data 下的**私有**带版本文档（`active` / `pending` / `lastKnownGood`），`0600` 临时文件 + 同目录原子 rename；只有 `app-boot` 完成且窗口加载成功后，才提升为 last-known-good。

### 坑 2.7　跨进程控制通道与端口占用
- **来源**：`anywhere-labs_dsh-desktop/.agents/notes/implemented/architecture/2026-09-10-beta-isolated-host.zh.md`；源码 `dsh-plugin-desktop/src/desktop-port.ts`、`src/webserver.ts`、`src/main.ts`
- **现象 / 设计**：Beta/稳定版把 Cordis Host 放进 Electron `utilityProcess` 隔离开（`startIsolatedDesktopHost`，源码 `src/host-process.ts` 用 `utilityProcess.fork(...)`）；私有控制通道**只**传原生操作和状态快照，函数留在原进程按回调 ID 调用。
- **端口**：默认从固定端口 `43120` 起（源码 `src/desktop-port.ts`：`DESKTOP_DEFAULT_WEB_PORT = 43_120`，`DESKTOP_WEB_PORT_RETRY_LIMIT = 32`），源码 `src/webserver.ts` 用 `code === 'EADDRINUSE'` 判定后顺延重试。
- **单实例**：`src/main.ts:384` `if (!app.requestSingleInstanceLock()) { ... }` —— 必须抢 Electron 单实例锁。
- **Host 崩溃处理**：`src/host-process.ts` 中 `child.once('exit', ...)`：「`DSH Host exited (${code}); restart the application to reconnect`」→ **Host 意外退出不自动重启、不重放请求**（笔记原文「Host 意外退出时报告错误，不自动重启或重放请求」）。退出流程：先请求正常清理（3s 超时）→ `child.kill()` → 限时等待退出（1s），无法确认终止则报错。
- **验证限制（诚实声明，可抄）**：「当前夹具未证明强制终止时任意插件后代进程的清理。」「未测量前不能宣称已改善 Windows 响应。」

> desktop 的 commit body 普遍为空，故 2.1–2.7 的「原文」均来自同名 `.agents/notes/...` 架构笔记，非 commit 正文。相关 commit 短哈希（标题，body 为空）：`62171c601`、`5af1f8c16`、`54af2fb1d`、`49aa95a30`、`6df4e5921`、`d93cd5de0`、`899d44bec`、`669557e8e`、`b30eea0d3`。
---

## 3. `xiaobright_dsh-anchored-standard`

> 这是一个 **preset（agent-plane composition）包**，不是普通混入宿主树的 bundle：它用 `agent.cordis.yml` + `preset.yml` 逐模式目录自包含。它的坑极适合教「跨平台 / 版本适配 / 发布前校验」。

### 坑 3.1　Windows 上 Git Bash 路径被 Node spawn 解释错 → 误导性 ENOENT
- **仓库 + commit**：`xiaobright_dsh-anchored-standard` + `babc933`（2026-08-17）
- **提交信息原文**：
  > `fix: normalize Git Bash workdir paths on Windows`
  > 「Node spawn treats `/e/foo` as `E:\e\foo`, so bash fails with a misleading ENOENT. Convert Git Bash drive paths and fall back to the session cwd when an explicit workdir is missing.」
- **现象**：Windows 上 `workdir: /e/foo` 被 Node 解释成 `E:\e\foo`，bash 报**误导性的 ENOENT**。
- **根因**：Node `spawn` 不认 Git Bash 的 `/e/...` 盘符写法。
- **修复**：转换 Git Bash drive path；显式 workdir 缺失时回退到 session cwd。

### 坑 3.2　硬编码 Git Bash 安装路径 → 换台机器就找不到 shell
- **仓库 + commit**：`xiaobright_dsh-anchored-standard` + `78b4cbd`（2026-08-17，正文提到手动 rebase PR #33）
- **提交信息原文（截断）**：
  > `fix(custom-bash): infer Git Bash path at runtime instead of hardcoding (PR #33, fixes #24)`
  > 「custom-bash.mjs resolution order: explicit bashPath > git install root > well-known Git-for-Windows roots (Program Files(/x86), per-user LOCALAPPDATA, scoop current) > plain bash on PATH; total discovery failure errors with guidance instead of falling back to a different shell … Hardcoded bashPath removed from ALL SIX mode compositions（PR 只改了 preset/ 的副本，`sync --check` 会拒）」
- **现象**：硬编码 `bashPath` 在别的机器上不存在。
- **根因**：只在一处改了，其余 5 个模式目录仍是旧副本。
- **修复**：运行时按优先级探测；**单源真相** `shared/custom-bash.mjs` + `npm run sync` 复制到每个模式目录；`sync --check` 拒绝不一致。

### 坑 3.3　`/bin/bash` 不存在的主机 → 「PTY shell exited during startup」
- **仓库 + commit**：`xiaobright_dsh-anchored-standard` + `efb01ca`（2026-08-17）
- **提交信息原文（截断）**：
  > `fix(persistent-shell): boot bash on hosts without /bin/bash (#44)`
  > 「官方 minimal preset 的 terminal-bash 行用插件默认 `shellPath /bin/bash`。On NixOS（及 bash 不在 /bin 的主机）该绝对路径不存在，PTY 子进程启动即退出，每次 bash 调用都失败 `PTY shell exited during startup`。」
- **修复（可抄的 `!!js` 表达式）**：
  ```yaml
  shellPath: !!js "process.getBuiltinModule?.('node:fs')?.existsSync('/bin/bash') ? '/bin/bash' : 'bash'"
  ```
  → 有 `/bin/bash` 就用它（行为不变），否则退回 PATH 查找的 `bash`。

### 坑 3.4　宿主 API 变了：`session.events` 数组 → `session.snapshotEvents()`
- **仓库 + commit**：`xiaobright_dsh-anchored-standard` + `751fd67`（2026-09-05）
- **提交信息原文**：
  > `fix: support session.snapshotEvents() in DSH presets`
  > 「DeepSeek Harness no longer exposes `session.events` as an array; presets should read session history via `session.snapshotEvents()` when available. Update all preset plugins and verify helpers to use `snapshotEvents()` with a fallback to the older `session.events` API for compatibility.」
- **修复**：所有 preset 插件改读 `snapshotEvents()`，**保留对旧 `session.events` 的 fallback**（保护旧宿主）。

### 坑 3.5　`dsh-persona` 0.1.3 把 `text:` 改成 `prefix:` → 旧 preset 静默失效
- **仓库 + commit**：`xiaobright_dsh-anchored-standard` + `51b38ef`（2026-09-08）
- **提交信息原文**：`fix: migrate persona rows from `text:` to `prefix:` for dsh-persona 0.1.3`（正文为空）
- **现象**：升级宿主后 persona 行不再生效。
- **根因**：`dsh-persona` 的配置字段从 `text:` 迁到 `prefix:`。
- **修复**：把 persona 行的 `text:` 改成 `prefix:`（本仓库 preset 里可见 `config: { prefix: You are a helpful software engineer assistant. }`）。

### 坑 3.6　重启后自动注入的 hint 用了**确定性 id** → 重复 id 打断历史装配
- **仓库 + commit**：`xiaobright_dsh-anchored-standard` + `b74543b`（2026-08-24）
- **提交信息原文（截断）**：
  > `fix(instruction-hint): make each injection id unique (fixes #76)`
  > 「The durable-scan dedup is prevention, not a guarantee: after a host restart the first `agent/pre-step` can run before `session.events` is materialized, see an empty list, and re-inject the hint. With the old deterministic id the duplicate collided with the first copy and stopped history assembly. Per-injection unique ids turn a past or future re-injection into a few wasted context tokens instead.」
- **现象**：注入的 hint 重复，**打断历史装配**（比多几个 token 严重得多）。
- **根因**：去重只是「预防」；宿主重启后首发 pre-step 可能在事件物化前跑，看到空列表 → 以**同一个确定性 id** 再注入一次 → id 撞车。
- **修复**：每次注入用唯一 id（代价只是多几个 context token）；并在 README 加排障说明：让受影响用户按 `source.kind == 'instruction-hint'` 去重旧坏日志。

### 坑 3.7　「用默认 preset 创建的会话」不发 `agent-preset/selected` → seeder 不跑
- **仓库 + commit**：`xiaobright_dsh-anchored-standard` + `24caabe`（2026-08-19）、`6733c10`（2026-08-21）
- **提交信息原文（`24caabe`，截断）**：
  > `fix(prefab): seed sessions created with the preset as default`
  > 「A session CREATED with the preset in its header (the default-preset path) never emits `agent-preset/selected` — the preset is composed at creation, not swapped — so the seeder never ran … Trigger seeding on the session's first permission/preset event too, and tolerate a not-yet-published agent on that path.」
  > （`6733c10` 补充：「re-read the agent after the skill registry await so an agent published during that window receives the seeded turn cursor」）
- **现象**：用「默认 preset」新建的会话从第 1 轮开始，而不是种子化的第 3 轮。
- **根因**：默认 preset 路径**不发** `agent-preset/selected` 事件，seeder 的触发条件没命中；且 await 期间 agent 可能尚未发布。
- **修复**：也在会话第一个 permission/preset 事件上触发 seeding，并容忍 agent 尚未发布（跳过 cursor 同步直到 agent 出现）。

### 坑 3.8　配置项校验：未知 config key 应在 apply 时拒绝
- **仓库 + commit**：`xiaobright_dsh-anchored-standard` + `4c52927`（2026-08-15）
- **提交信息原文**：`fix(tool-bootstrap): reject unknown config keys at apply time`
- **教训**：插件对 `config` 做**白名单校验**，未知 key 在 `apply` 时就抛错，而不是静默忽略（新手写错 key 时能立刻发现）。

### 坑 3.9　自包含纪律（工程规范化，来自测试而非 commit）
- **来源**：`xiaobright_dsh-anchored-standard/test/self-containment.test.mjs`
- **规则 1**：任何模式目录的 `agent.cordis.yml` **不得**引用目录外的插件（测试用正则找 `name: ../` 之类的上引用，发现即 fail）。
  > 原文：`test('no mode references plugins outside its own directory', ...)` → `must be self-contained`
- **规则 2**：`shared/` 是单源真相，各模式目录是**物化副本**，`sync --check` 必须过。
  > 原文：`test('materialized copies match shared/ sources (run: npm run sync)', ...)`
- **`package.json` scripts（可抄）**：
  ```json
  "scripts": {
    "sync": "node scripts/sync-modes.mjs",
    "test": "node --test",
    "check": "node scripts/sync-modes.mjs --check && node --test"
  }
  ```
---

## 4. `omdsh-dev_DSH-better-sidebar`（644 commits / 271 修复）

### 坑 4.1　「槽声明先到、服务后到」→ 按槽触发注册会**静默什么都不注册**
- **仓库 + commit**：`omdsh-dev_DSH-better-sidebar` + `aa1b994`（2026-09-09）
- **提交信息原文（截断）**：
  > `fix(native): register the plugin's tab types when the registry service arrives`
  > 「The native seat declares `sidebar.right.pane.tab` BEFORE it provides `sidebarRightTabs`, so driving the registration off the slot declaration read the service as missing and registered nothing — permanently, since a declaration never collapses. Observed on a real DSH profile (0.1.5-alpha.1, `dsh web` on the web profile): the plugin host and its other slot registrations mounted, the native guide page stayed empty, and a probe printed `sidebarRightTabs= undefined` at declaration time with the registry present three seconds later.」
- **现象**：真机 profile 上插件宿主 + 其他槽都挂上了，**原生指南页空**；探针显示声明时 `sidebarRightTabs= undefined`，3 秒后才出现。scratch lane 看不到，因为那里插件在原生包 provide 之后才激活。
- **根因**：**声明（declaration）≠ 服务就绪**；声明永远不会 collapse，所以按声明触发注册就永久错过服务。
- **修复**：`registerNativeSurface` 改为**等 SERVICE**（`ctx.inject`），服务出现/重现时重跑；per-body 槽注册仍走 `slots.inject`。回归测试 `tests/native-surface.spec.ts` 模拟「槽先触发、服务后到」。
- **可抄教训**：**依赖服务用 `ctx.inject([...], cb)` 驱动，别用槽声明时机。**

### 坑 4.2　双挂载 → 两个侧边栏 / `duplicate prefix route` / `duplicate loader entry id`
- **来源**：`omdsh-dev_DSH-better-sidebar/cordis.patch.yml` 注释 + `README.md` 常见问题表
- **现象（README 原文）**：「页面出现**两个侧边栏** | 双挂载。旧的手动挂载行：`~/.dsh/profiles/web/cordis.patch.yml` 还留着 `- insert: ... better-sidebar ...`，删掉那段（同 id 重复挂载 loader 会直接报 `duplicate loader entry id`）。」
- **根因**：bundle patch 通道 + 手动挂载行同时存在 = 挂两次（Node 半两个、两个侧边栏）。
- **修复**：
  - 切到 bundle 通道前**删掉** profile 里旧的手动挂载行；
  - 聚合包（如 `@linxin666/dsh-web-ui-all`）以**不同 id** 挂载本包时，插件自身 bundle patch 用 `!!js` **自动退让**（见 §二.5 的 `disabled: !!js` 表达式）；
  - 聚合包必须**排在 `dsh-better-sidebar` 之前**（注释原文：「the aggregate bundle must precede this one in `dsh.profile.bundles`」）；反向顺序是**已知限制**（`!!js` 只看得见它之前的行，且没有运行时单例守卫）。
  - 聚合双挂载的 boot 报错原文（注释）：「Two mounts register `/sidebar/api` twice and fail the whole plugin tree at boot (`"duplicate prefix route"`).」

### 坑 4.3　注册没包 `ctx.effect` → HMR/禁用后残留 → `already registered`
- **来源**：`omdsh-dev_DSH-better-sidebar/docs/external-plugin-guide.md` §3 / §9；源码 `src/client/service.ts:595-611`
- **源码原文（错误文案）**：
  ```ts
  throw new Error(`[dsh-better-sidebar] tab type "${descriptor.id}" already registered`)
  throw new Error(`[dsh-better-sidebar] file viewer "${descriptor.id}" already registered`)
  ```
- **现象（指南原文）**：「不包 effect，HMR / 插件禁用后注册残留，下次激活会抛 `"already registered"`。」
- **修复**：`ctx.effect(() => ctx.betterSidebar.registerTab({...}))`（disposer 由 Cordis fiber 在卸载时自动调用）；`inject = ['betterSidebar']` 让 Cordis 保证服务就绪后才激活你。

### 坑 4.4　id 撞车：`registerTab` / `registerFileViewer` 对重复 id 抛错
- **来源**：`docs/external-plugin-guide.md` §4.4
- **原文**：「你的 `id` 不可与上述重复，否则 `registerTab` 抛 `"tab type \"X\" already registered"`。」
- **修复**：**用包前缀**（`my-plugin:xxx`）。内置 7 tab id：`editor(10) / git(20) / subagent(30) / sidechat(35) / terminal(40) / browser(50) / diff(-1)`；内置 6 viewer：`image/pdf/markdown/html/code/binary-download`。

### 坑 4.5　自定义会话种子缺 fork 标记 → 子会话「继承父会话未领取的 inbox」→ 幽灵消息
- **仓库 + commit**：`omdsh-dev_DSH-better-sidebar` + `93ad87d`（2026-09-06）
- **提交信息原文（截断）**：
  > `fix(sidechat): stamp the seed with fork markers so the child inherits no pending inbox`
  > 「sidechat.start passed `seed` without `meta.isSeeded: true` + `inheritedEventCount`, so dsh-session treated the whole seed as the child's OWN events and the child's Inbox constructor replayed the parent's `agent/inbox/spliced` history … The first side prompt then claimed `[phantom, boundary, question]` — the stale parent message was sent to the model BEFORE the boundary and logged as a `user/message`.」
- **现象**：长长时侧边对话先把「之前那条 User msg」发出去（幽灵消息排在 boundary 之前最先发给模型）。
- **根因**：只给 seed 不标 `isSeeded`，宿主把整段 seed 当重放历史；子会话 inbox 折重放父会话的 `agent/inbox/spliced`。
- **修复**：传宿主 `session.fork` 同款标记对（`meta.isSeeded: true` + `inheritedEventCount`）；回归用**真实** `Session.create` + `Inbox` 双向跑。另注（AGENTS.md）：`Session.create` 的 header `version` 必须用 `SESSION_FORMAT_VERSION`（0.1.5 是 `3` 字面量），**勿钉 `0`**。

### 坑 4.6　宿主大版本适配：0.1.5-alpha.1 → alpha.2 → rc.1 每步都在改宿主契约
- **来源**：commit `ba01147`（alpha.1）、`0b6ac5d`（alpha.2）、`725b2f7`（rc.1）
- **`ba01147` 原文（截断）**：
  > - 「Live assistant stream (`assistant/chunk` is gone): 0.1.5 publishes in-flight model deltas as process-local `agent/assistant-stream` frames instead of durable `assistant/chunk` events …」
  > - 「Cold session reads (`persistence.inspect` is gone) … `open(id,'read') -> handle.read() -> close()`」
  > - 「drop the `remote.session.openWorkspacePath` interception … so the wrapper had no caller and would hijack the host's "open in app" gesture」
- **`0b6ac5d` 原文（截断）**：
  > - 「the native guide entry lost its `description` field …」
  > - 「global main panels replaced the `conversation` root slot with the keyed `main` slot (`main.conversation`)」
  > - 「Fixes a pre-existing fill bug … the native tab body host is a block scroller with a definite height, so tab roots that only declared `flex: 1` collapsed to content height and the side chat composer drifted off the pane bottom.」
- **`725b2f7` 原文（截断）**：
  > 「`SidebarRightGuideEntry.description` is back (optional). The native guide renders it only while it lists **at most 4 entries**; a longer list drops every description … the plugin contributes six guide entries, so the default composition is over the 4-entry limit and shows titles only.」
  > 「Restore caveat fixed in the lane: the settings route merges patches key-wise, so undoing a temporary `tabsEnabled` change by posting the original (empty) map leaves the disabled keys behind — the e2e restores every key it touched explicitly.」
- **可抄结论**：宿主每升一个小版本，**会话事件模型 / 文件打开漏斗 / 槽位 / 字段**都可能变；适配要「只对一条线做运行时兼容」，其余用户留在旧线（0.1.5-alpha.2 停在 `v0.19.0-alpha.1`，0.1.2-rc.1 停在 `v0.18.1`）。**字段回归 ≠ 兜底句回归**：宿主自己没有兜底句时，插件也**不发** `description` 字段（"通用句是噪音"）。

### 坑 4.7　`dsh-*` 传递 peer 与上游包自身 `dependencies` 丢失 → `Cannot find package 'anser'`
- **来源**：`omdsh-dev_DSH-better-sidebar/AGENTS.md` §3 第 9 条（原文很长，此处摘）
- **现象 1（原文）**：「`@deepseek-ai/dsh-subagent` 等 npm 包把 `dsh-attachment` 等 dsh-* 姊妹包全部声明为 peerDependencies … 其余 peer 在 pnpm 下会解析到树上残留的旧版——如 `dsh-attachment@0.1.1-rc.1` 缺 `admitPromptContent` 导出、`dsh-subagent` 产物 import 它时测试加载即崩。」
- **现象 2（原文）**：「`@deepseek-ai/dsh-client-ui-primitives@0.1.5-alpha.2` 的 manifest 不再声明任何 `dependencies`（alpha.1 声明了 19 个），但 `lib/*.js` 仍裸 import `anser` / `shiki` / `@shikijs/langs/*` / `mdast-util-*` / `micromark-*` / `katex` … vitest 一碰 primitives 就 `Cannot find package 'anser'`。」
- **根因**：宿主由预构建前端 bundle 满足依赖；**独立安装的 dev/test 树不会**。
- **修复**：把 dev 树实际触达的**全部** dsh-* 传递 peer 提升进 `devDependencies`（精确钉版）；上游丢的 `dependencies` 也要提升。**每次适配新 alpha 版本先跑 `pnpm peers check`**。rc.1 复评：「这组提升不得回退」。

### 坑 4.8　平台相关（Windows / WSL / 终端）
- **`7499383`**（2026-09-02）`fix(terminal): resolve Windows custom shell executables (#487)`（body 为空）—— Windows 自定义 shell 可执行文件解析。
- **`6d87747`**（2026-09-03）`fix(pty): contain node-pty's deferred Windows resize after pty exit`，原文（截断）：
  > 「node-pty's WindowsTerminal queues resize calls that arrive before the ConPTY control socket's first data flush (`_deferNoArgs`). If the pty exits before the flush, the deferred resize throws `'Cannot resize a pty that has already exited'` inside the socket's `'data'` handler — **uncatchable by any caller and fatal to the host process.** The Windows CI lane caught exactly this as an unhandled error while all 1233 tests passed.」
  > 修复：自己加一道 gate 把「首个输出前」的 resize 停住，输出 flush 后 `setImmediate` 重放；**Windows 才 arm，POSIX 保持原行为**（POSIX resize 是同步的）。
- **`180b16d`**（2026-08-29）`fix: 修复 WSL 会话 Linux 路径解析 (#399)`（body 为空）。
- **`8191951`**（2026-09-08）`fix(terminal): WS close reason 按 UTF-8 字节截断，避免超 123 字节抛错`，原文：
  > 「ws 用 `Buffer.byteLength` 校验 close reason 的 123 字节上限（`ws/lib/sender.js`），原 `slice(0, 100)` 按 UTF-16 code unit 截断，非 ASCII shell 名可达 316 字节（实测 200 个 CJK 字符），`ws.close()` 会抛 `RangeError` 顶掉原始错误。改为按字节截断且不切碎 code point。」
- **可抄结论**：**`slice()` 按 UTF-16 单位 ≠ 字节上限**；跨平台行为要按 `process.platform` 分叉并各自测。

### 坑 4.9　CI / 工程（Windows 车道暴露的假绿）
- **`c4c4d73`**（2026-09-03）`fix(ci): resolve consumer-type link targets to their physical path`，原文：
  > 「On the Windows lane the `@deepseek-ai/cordis` link produced `TS2307` even though the link was visibly created: under pnpm its target, `node_modules/@deepseek-ai/cordis`, is itself a junction into `.pnpm`, and a native symlink pointing AT that junction does not traverse for `tsc`. Resolve both link targets with node's native `realpath` first … and fail loudly with the link layer listed when a created link does not resolve to a package root.」
- **`2052d05`**（2026-09-02）`fix(e2e): 聚合 lane 按 mtime 取最新 tarball 并统一 DSH_CMD 缺省解析`，原文（截断）：
  > 「`e2e-aggregate-mount.sh` 选 tarball 用字典序 `ls | head -1`，仓库根堆积多个历史 tgz 时会把冒烟**挂到过期产物上** … 顺带修一个移植中暴露的边角：候选计数行在零候选时因 `pipefail+set -e` 静默退出，吞掉下一行的友好报错——补 `|| true`。」
- **`3d23ceb`**（2026-09-02）`fix(ci): pnpm 版本统一由 packageManager 字段供版，移除 action 显式 version 输入`（body 为空）。
- **可抄结论**：CI 要跑 **Windows 车道**；tarball 按 **mtime** 取最新；脚本要防 `set -e` 吞报错。

### 坑 4.10　原生 tab 的标题 / 图标
- **`4da2b43`**（2026-09-09）`fix(native): title a file tab by its own name, not the descriptor's`，原文：
  > 「The editor type serves both the files PAGE and every file RESOURCE; its native `title` callback ignored the address, so every opened file showed up in the strip as "Files" — indistinguishable tabs. Verified on a real profile: after opening `AGENTS.md` from the tree and a chat file link, the strip read ["文件", "文件", "文件"].」
- **`91de0e2`**（2026-09-09）`fix(native): give the "Files" guide row its glyph`，原文：
  > 「The guide renders `entry.icon`, and the `files` kind takeover registered without one — so after the editor type stopped contributing its own duplicate row (`b56ceec`), the single "Files" row was the only entry in the new-tab list with a blank icon slot.」
- **`b56ceec`**（2026-09-09）`fix(native): offer one "Files" row in the new-tab list`，原文：
  > 「The editor type's page identity IS the `files` kind takeover (same explorer, same title), so the guide/new-tab list showed two identical "Files" entries … The editor type now contributes no guide entry of its own; it stays registered as the file RESOURCE viewer.」
- **可抄结论**：`title` 回调要**读 address**（页面用 descriptor 标题、文件用文件名）；`icon` 不声明宿主补方块占位；**同一个页面身份只能有一条 guide 行**。

### 坑 4.11　过度遮蔽（secret redaction 误伤普通文件）
- **仓库 + commit**：`omdsh-dev_DSH-better-sidebar` + `0469319`（2026-09-06）
- **提交信息原文（截断）**：
  > `fix(redact): keep the credential heuristics off ordinary files`
  > 「Path layer: patterns now match with a right boundary (must not continue into `[a-z0-9]`) and list only store-plural forms (`credentials/secrets/passwords`, not `tokens`), so `tokenizer.ts` / `dev.environment.ts` / `style.keys.ts` / `api-tokens.md` are no longer masked whole while `.env.local` / `credentials.json` / `mytoken.yaml` still are. Content layer: drop the bare `key/auth/token/pass/bearer` field names — they label far more ordinary content (keyboard keys, CSS custom properties, lexical tokens) than secrets.」
- **可抄结论**：**安全启发式要加「右边界」+ 限定复数名词**，否则把 `tokenizer.ts` 这类普通文件整段遮蔽。

### 坑 4.12　README「常见问题」里记录的、用户最常撞的安装坑（可直接抄成手册）
- **来源**：`omdsh-dev_DSH-better-sidebar/README.md` 常见问题表（原文逐条）：
  | 现象 | 原因与解决 |
  |---|---|
  | 报 `Ignored build scripts` | pnpm 11 拦截构建脚本。在 profile 目录（`~/.dsh/profiles/web`）跑 `pnpm approve-builds --all`。 |
  | 报 `minimum release age` / 版本不足 24h | 装的版本发布不足 24 小时。等 24h 或重跑一次（pnpm 会自动补 `minimumReleaseAgeExclude`）。 |
  | 报「找不到 profile 目录」 | 先跑一次 `dsh web`，让它初始化 `~/.dsh/profiles/web`。 |
  | 页面出现**两个侧边栏** | 双挂载（见坑 4.2）。 |
  | Windows 下终端无法使用 | `node-pty` 依赖预编译二进制；当前 Node 版本没有对应产物时需装编译工具链（VS Build Tools）。 |
  | 终端提示「node-pty 加载失败」 | 在 `~/.dsh/profiles/web` 下 `pnpm approve-builds --all && pnpm rebuild node-pty`，完成后重启 DSH 并点重试。 |
  | 提示 `dsh: command not found` | 先安装 DSH；或 `npx -y --package @deepseek-ai/dsh dsh plugin --profile web add dsh-better-sidebar@latest`。 |
---

# 二、可逐字照抄的代码模板

## 二.1　ouroboros 的零代码组合包（**本次最重要的模板**）

**目录树**（3 个文件，零代码）：
```
Q00_ouroboros/integrations/dsh-plugin/
├── README.md
├── cordis.patch.yml
└── package.json
```

**`package.json` 全文**（来源：`Q00_ouroboros/integrations/dsh-plugin/package.json`）：
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

**`cordis.patch.yml` 全文**（来源：`Q00_ouroboros/integrations/dsh-plugin/cordis.patch.yml`；注释保留原文，正是新手最该读的部分）：
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

**分析（新手最需要的三点）**：
1. **挂了 1 行**：`- insert:` 列表里只有一条 `id: mcp-ouroboros`、`name: '@deepseek-ai/dsh-mcp-client'`。
2. **有 `!!js`**：全部在插件 **config** 内（`env` 段 6 个值）。**没有** `disabled` 字段。
3. **没有 `disabled`**：它是无条件挂载（不需要聚合退让逻辑）。
---

## 二.2　`dsh-desktop`：桌面宿主插件

**`dsh-plugin-desktop/package.json` 关键字段（逐字，其余依赖略）**（来源：`anywhere-labs_dsh-desktop/dsh-plugin-desktop/package.json`）：
```json
{
  "name": "dsh-plugin-desktop",
  "version": "2.0.9",
  "description": "DSH Desktop: an Electron shell composed as a DeepSeek Harness Cordis plugin",
  "type": "module",
  "main": "lib/main.js",
  "types": "lib/types/index.d.ts",
  "bin": {
    "dsh-desktop": "lib/bin.js",
    "dsh-plugin-desktop": "lib/bin.js"
  },
  "exports": {
    ".": { "types": "./lib/types/index.d.ts", "default": "./lib/index.js" },
    "./profile": { "types": "./lib/types/profile.d.ts", "default": "./lib/profile.js" },
    "./client": { "types": "./lib/types/client/index.d.ts", "default": "./lib/client.js" },
    "./webserver": { "types": "./lib/types/webserver.d.ts", "default": "./lib/webserver.js" },
    "./windows-pwsh-sandbox": { "types": "./lib/types/windows-pwsh-sandbox.d.ts", "default": "./lib/windows-pwsh-sandbox.js" },
    "./terminal": { "types": "./lib/types/terminal.d.ts", "default": "./lib/terminal.js" },
    "./pnpm": { "types": "./lib/types/pnpm.d.ts", "default": "./lib/pnpm.js" },
    "./profile-service": { "types": "./lib/types/profile-service.d.ts", "default": "./lib/profile-service.js" },
    "./desktop-plugins": { "types": "./lib/types/desktop-plugins.d.ts", "default": "./lib/desktop-plugins.js" },
    "./profiles": { "types": "./lib/types/profiles.d.ts", "default": "./lib/profiles.js" },
    "./diagnostics": { "types": "./lib/types/diagnostics.d.ts", "default": "./lib/diagnostics.js" },
    "./notifications": { "types": "./lib/types/notifications.d.ts", "default": "./lib/notifications.js" },
    "./updates": { "types": "./lib/types/updates.d.ts", "default": "./lib/updates.js" },
    "./package.json": "./package.json"
  },
  "files": [
    "build/app-icon.ico",
    "build/app-icon.png",
    "build/app-icon-mac.png",
    "build/tray-icon.svg",
    "build/tray-icon*.png",
    "cordis.patch.yml",
    "docs/**",
    "lib/**/*.js",
    "lib/**/*.map",
    "lib/native-ui/**",
    "lib/types/**/*.d.ts",
    "README.md",
    "README.zh.md",
    "README.i18n.yaml",
    "THIRD_PARTY_NOTICES.md"
  ],
  "dsh": {
    "client": {
      "inject": [
        "@deepseek-ai/dsh-api-remotes",
        "@deepseek-ai/dsh-client-connection",
        "@deepseek-ai/dsh-client-locale",
        "@deepseek-ai/dsh-client-ui-renderer",
        "@deepseek-ai/dsh-client-ui-settings",
        "@deepseek-ai/dsh-client-ui-theme"
      ],
      "platform": "web"
    },
    "bundle": {
      "patch": "./cordis.patch.yml"
    }
  },
  "scripts": { …(略，见下) },
  "dependencies": { …(略：129 个 @deepseek-ai/dsh-* 精确钉 0.1.5-rc.1 + 少量第三方) },
  "peerDependencies": { "electron": "43.3.0" },
  "devDependencies": { …(略) }
}
```
> **注意**：这个包**同时**有 `dsh.bundle`（宿主/桌面侧）**和** `dsh.client`（浏览器侧，`platform: "web"`）—— 它是「桌面宿主 + Web client 面」双面插件。

**`dsh-plugin-desktop/cordis.patch.yml` 全文**（来源同上）：
```yaml
# Desktop Host operations compose around the existing Web bundle. Compatibility
# mode keeps upstream ownership of the browser carrier and rendered UI.
- insert:
    - id: desktop-shell
      name: dsh-plugin-desktop
      config:
        mode: compatibility
    - id: desktop-terminal
      name: dsh-plugin-desktop/terminal
      disabled: !!js process.platform === 'linux'
    - id: desktop-diagnostics
      name: dsh-plugin-desktop/diagnostics
    - id: desktop-notifications
      name: dsh-plugin-desktop/notifications
    - id: desktop-pnpm
      name: dsh-plugin-desktop/pnpm
    - id: desktop-profiles
      name: dsh-plugin-desktop/profiles
    - id: desktop-updates
      name: dsh-plugin-desktop/updates

# A desktop launch has no terminal operator waiting for the Web readiness line.
- id: web-runtime
  config:
    openBrowser: false
    printUrl: false
    surfaceContext: true
    trustedHosts: []
```
> **教学价值**：这演示了 ① 一个组合包 `insert` **多行**；② `name` 用包**子路径**（`dsh-plugin-desktop/terminal`），行 `id` 与子路径**解耦**（`desktop-terminal`）；③ `disabled: !!js process.platform === 'linux'` 是官方认可的**跨平台**写法；④ 第二个顶层 patch 项**不带 `insert`**，只是 `id` 定位 + `config` 覆盖已有行（`web-runtime`）——这就是「override」形态。

**「怎么起一个 dsh 进程/会话」的关键代码**（Electron 用 `utilityProcess` 起独立 Host 子进程；来源：`dsh-plugin-desktop/src/host-process.ts`）：
```ts
/** Electron owns the child lifetime; the child owns the unchanged DSH Web server. */
export async function startIsolatedDesktopHost(options: IsolatedHostOptions): Promise<void> {
  const child = utilityProcess.fork(fileURLToPath(new URL('./host-process-entry.js', import.meta.url)), [], {
    serviceName: 'DSH Host', stdio: 'pipe', cwd: process.cwd(), env: { ...process.env },
  })
  // Keep normal Host logs in its own files; stderr includes bootstrap failures.
  child.stdout?.on('data', (data: Buffer) => { process.stdout.write(data) })
  child.stderr?.on('data', (data: Buffer) => { process.stderr.write(data) })
  const rpc = new HostRpc({
    send: message => child.postMessage(message),
    listen: receive => { child.on('message', receive); return () => { child.removeListener('message', receive) } },
  }, 120_000)
  const releaseNative = bindNativeRuntime(rpc, options.runtime)
  rpc.handle('certificate', () => options.prepareCertificate())
  rpc.handle('quit', ([code]) => { setImmediate(() => options.requestQuit(code)) })
  …
  child.once('exit', (code) => {
    exited = true
    rpc.close(`DSH Host exited (${code})`)
    resolveExit()
    if (!stopping && booted) options.onFailure(new Error(`DSH Host exited (${code}); restart the application to reconnect`))
  })
```
> 另见 `src/main.ts:384` `if (!app.requestSingleInstanceLock()) { ... }`（单实例锁）；`src/webserver.ts` 用 `EADDRINUSE` 判定后端重试；`src/desktop-port.ts` 端口策略 `43120` + 32 次顺延。

**桌面插件包目录树（2 层，来源：`dsh-plugin-desktop/src/`）**：
```
dsh-plugin-desktop/
├── package.json
├── cordis.patch.yml
├── tsconfig.json / tsconfig.client.json / tsconfig.native-ui.json / tsconfig.tests.json / tsconfig.tests.client.json
├── tsdown.config.ts / vite.native-ui.config.ts / vitest.config.ts
├── docs/            (plugin-services.md + .zh.md + compatibility-chrome-isolation.md + operation-reliability-matrix.yaml)
├── build/           (图标 assets)
├── scripts/         (打包/校验脚本：verify-runtime-closure、verify-loader-boot、verify-profile-boot、verify-licenses…)
├── tests/
└── src/
    ├── (约 130 个 .ts 根文件：main.ts / index.ts / bin.ts / host-process.ts / pnpm.ts / profile-manager.ts / safe-mode.ts / renderer-recovery.ts / startup-generation.ts …)
    ├── client/
    └── native-ui/   (compatibility-chrome / components / desktop-dialog / lib / profile-create / profile-selector / recovery / setup-wizard / shared)
```

**`scripts` 里可直接抄的发布门（来源：`dsh-plugin-desktop/package.json`）**：
```json
"verify:closure": "node --test scripts/runtime-closure.spec.mjs && node scripts/verify-runtime-closure.mjs",
"verify:cli": "node scripts/verify-cli-runtime.mjs",
"verify:loader": "node scripts/verify-loader-boot.mjs",
"verify:profile": "node scripts/verify-profile-boot.mjs",
"verify:licenses": "node scripts/verify-licenses.mjs",
"prepack": "yarn run check",
"check": "yarn run build && yarn run typecheck && yarn run test && yarn run verify:closure && yarn run verify:cli && yarn run verify:loader && yarn run verify:profile && yarn run verify:aa && yarn run verify:licenses && yarn run verify:operations"
```
> 教学点：`prepack` 挂钩 `check` → **`npm pack` / `npm publish` 前自动跑全套校验**。
---

## 二.3　`anchored-standard`：完整包结构 + 构建/校验配置

**`package.json` 全文**（来源：`xiaobright_dsh-anchored-standard/package.json`）：
```json
{
  "name": "dsh-anchored-standard",
  "version": "0.1.0",
  "private": true,
  "description": "Two-phase DeepSeek Harness preset: Minimal-aligned bootstrap, then full Standard tools",
  "type": "module",
  "license": "MIT",
  "engines": {
    "node": ">=22.19.0"
  },
  "scripts": {
    "sync": "node scripts/sync-modes.mjs",
    "test": "node --test",
    "check": "node scripts/sync-modes.mjs --check && node --test"
  }
}
```
> **注意**：它是 **preset 包**（`private: true`，不发 npm），没有 `dsh` 字段；用目录结构 + `agent.cordis.yml` 表达。

**完整目录树（来源：`xiaobright_dsh-anchored-standard/`，126 文件）**：
```
dsh-anchored-standard/
├── package.json  README.md  README.zh-CN.md  LICENSE  NOTICE  ACKNOWLEDGEMENTS.md  FAREWELL.md
├── .gitattributes  .gitignore  .github/workflows/test.yml
├── scripts/sync-modes.mjs          # 单源真相 → 各模式目录的物化同步器（--check 模式）
├── shared/                         # 单源真相（15 个 .mjs）
│   ├── anchor-turn.mjs  compaction-epoch.mjs  context-gate.mjs  cot-drip.mjs
│   ├── custom-bash.mjs  deliberation-gate.mjs  dev-tool-search.mjs  instruction-hint.mjs
│   ├── skill-search.mjs  think-phase.mjs  tool-bootstrap.mjs  toolchoice-adapter.mjs
│   └── wire-think.mjs  zero-tool-bootstrap.mjs
├── test/                           # 20 个 node:test 用例
│   ├── self-containment.test.mjs   # 守护「目录自包含」+「副本与 shared 一致」
│   └── (anchor-turn / context-gate / custom-bash / instruction-hint / snapshot-events-compat …)
├── verify/                         # 一次性无头复现 runner
│   ├── run-verify.mjs  verify-runner.mjs  first-assistant-canceller.mjs
├── preset/                         # 7 个可独立复制安装的模式目录：
├── prefab/                         #   每个目录都含 agent.cordis.yml + preset.yml + 若干 .mjs
├── zero-anchored-standard/
├── whoami-standard/
├── eternal-minimal/
├── wire-think-standard/
└── combo-anchored/
```

**`preset/preset.yml`（模式元数据，可抄）**：
```yaml
name: Anchored Standard (experimental)
description: Bootstrap with the Minimal preset's real tool pair (persistent bash + str_replace_editor) and no auto-injected workspace or skill context, then expose the full Standard catalog after the first durable tool call or reply.
order: 5
```

**`preset/agent.cordis.yml` 的「insert 行」形态（节选，逐字）**——注意这里用**顶层数组 + `- id:` 行**（preset 组合格式），与 bundle 的 `- insert:` 不同：
```yaml
- id: context-gate
  name: ./context-gate.mjs
  config:
    promoteOn: either
    includeSubagents: true
    allowKinds: [skill-invocation]

- id: tool-pwsh
  name: '@deepseek-ai/dsh-tool-pwsh'
  disabled: !!js process.platform !== 'win32'

- id: persistent-shell
  name: cordis:group
  group: true
  disabled: !!js process.platform === 'win32'
  isolate:
    terminals: true
  config:
    - id: pty
      name: '@deepseek-ai/dsh-terminal'
    - id: terminal-bash
      name: '@deepseek-ai/dsh-terminal-bash'
      config:
        shellPath: !!js "process.getBuiltinModule?.('node:fs')?.existsSync('/bin/bash') ? '/bin/bash' : 'bash'"
        timeoutMs: 300000
```
> 可抄知识点：① `name: ./xxx.mjs` 相对路径（锚到 patch 文件旁，源码机理见 §0）；② `name: cordis:group` + `group: true` + `config:` 是数组 = **嵌套组**；③ `isolate:` 声明 realm；④ `disabled: !!js process.platform === 'win32'` 跨平台分叉；⑤ 一个 `!!js` 表达式里用 `process.getBuiltinModule?.('node:fs')`（更安全的 Node API 探测）。

**`check` 脚本与自包含测试全文**（来源：`xiaobright_dsh-anchored-standard/test/self-containment.test.mjs`）：
```js
const MODE_DIRS = [
  'preset', 'prefab', 'zero-anchored-standard', 'whoami-standard',
  'eternal-minimal', 'wire-think-standard', 'combo-anchored',
]

test('no mode references plugins outside its own directory', () => {
  for (const dir of MODE_DIRS) {
    const yml = readFileSync(join(root, dir, 'agent.cordis.yml'), 'utf8')
    const upward = [...yml.matchAll(/^[ \t]*name:[ \t]*\.\.\/\S+/gm)]
    assert.deepEqual(upward.map((m) => m[0].trim()), [], `${dir}/agent.cordis.yml must be self-contained`)
  }
})

test('materialized copies match shared/ sources (run: npm run sync)', () => {
  const result = spawnSync(process.execPath, [join(root, 'scripts', 'sync-modes.mjs'), '--check'], { encoding: 'utf8' })
  assert.equal(result.status, 0, `sync --check failed:\n${result.stdout}${result.stderr}`)
})
```
---

## 二.4　`better-sidebar` 的扩展点（暴露给第三方的注册 API）

**服务提供点（源码）**：`omdsh-dev_DSH-better-sidebar/src/client/index.tsx` 在 `apply()` 开头执行 `ctx.provide('betterSidebar', service)`；消费插件在 `inject` 里声明 `'betterSidebar'`。

**注册 API（函数名 + 签名，逐字，来源：`docs/external-plugin-guide.md` §7）**：
```ts
interface BetterSidebarService {
  /** 注册 tab 类型；返回 disposer */
  registerTab(descriptor: TabDescriptor): () => void
  /** 注册文件预览器；返回 disposer */
  registerFileViewer(descriptor: FileViewerDescriptor): () => void
  /** 当前已注册的 tab 描述符快照（同步，供 useSyncExternalStore 用；含被设置页禁用的类型） */
  getTabs(): readonly TabDescriptor[]
  /** 当前已注册的 file viewer 描述符快照（含被设置页禁用的 viewer） */
  getFileViewers(): readonly FileViewerDescriptor[]
  /** 按 id 查 tab 描述符 */
  getTab(id: string): TabDescriptor | undefined
  /** 某个 tab 类型是否在 Side card 设置中启用 */
  isTabEnabled(id: string): boolean
  /** 某个 file viewer 是否在 Side card 设置中启用 */
  isViewerEnabled(id: string): boolean
  /** 按 path 匹配 file viewer（priority 降序单趟：detect → exts；跳过硬禁用 viewer） */
  matchFileViewer(path: string, head?: Uint8Array): FileViewerDescriptor | undefined
  /** 打开一个 tab（+ 菜单和外部触发都用它；走 descriptor.dedupeKey 去重） */
  openTab(seed: OpenTabSeed, scope?: SessionScope): void
  /** 关闭一个 tab（未知 id 严格 no-op） */
  closeTab(tabId: string, scope?: SessionScope): void
  /** 订阅注册表变化（register/dispose 时触发） */
  subscribe(listener: () => void): () => void
  /** 插件版本（如 '0.17.1'；与 package.json 同步，测试守护） */
  readonly version: string
  /** 能力清单（只增不删）：'badge' | 'tabLifecycle' | 'updateTab' | 'openFile' | 'targetedOpen' |
   *  'stateSubscription' | 'tabMeta' | 'pluginSettings' | 'urlTarget' | 'settingSelect' */
  readonly features: readonly string[]
  /** 当前快照：激活 sessionId + 其状态 + prefs */
  getSnapshot(): SidebarSnapshot
  /** 订阅快照变化（会话切换/状态变更/prefs 写入）；返回 disposer */
  subscribeState(listener: () => void): () => void
  /** 更新一个已打开 tab 的显示字段（title/path/meta）；tab 不存在时 no-op */
  updateTab(tabId: string, patch: { title?: string; path?: string; meta?: unknown }): void
  /** 激活一个已打开的 tab（触发 descriptor.onActivate；未知 id 严格 no-op） */
  activateTab(tabId: string, scope?: SessionScope): void
  /** 在 scope.sessionId 的侧边栏编辑器打开一个文件 */
  openFile(scope: SessionScope, path: string, title?: string): void
}
```

**消费方最小骨架（逐字，来源：`docs/external-plugin-guide.md` §3 / §13）**：
```ts
// my-plugin/src/client/index.ts
import type {} from 'dsh-better-sidebar'          // 触发 ctx.betterSidebar 类型合并
import type { Context } from '@deepseek-ai/cordis'

export const inject = ['betterSidebar', 'slots']   // 声明服务依赖（slots 可选，按需）

export function apply(ctx: Context): void {
  // 注册一个 sidebar tab：ctx.effect 包裹 → 卸载时自动撤销注册（HMR-safe）
  ctx.effect(() =>
    ctx.betterSidebar.registerTab({
      id: 'my-plugin:db',
      title: () => 'Database',
      icon: <DbIcon />,
      order: 50,
      component: ({ scope }) => <DbView sessionId={scope.sessionId} />,
    })
  )

  // 注册一个文件预览器
  ctx.effect(() =>
    ctx.betterSidebar.registerFileViewer({
      id: 'my-plugin:csv',
      exts: ['csv'],
      fetchStrategy: 'custom',
      load: async (path, scope) => parseCsv(await fetchCsvBytes(scope, path)),
      component: ({ customData, path }) => <CsvGrid data={customData} path={path} />,
    })
  )
}
```

**`TabDescriptor` 完整字段（逐字，来源：§4.1；节选关键）**：
```ts
interface TabDescriptor {
  id: string                    // 唯一 id；也是 SidebarTab.type 的值。建议带包前缀：'my-plugin:db'
  title: string | (() => string)
  description?: string | (() => string)   // 一行说明；宿主只在 guide 条目 ≤ 4 条时渲染
  icon?: ReactNode | ((size: number) => ReactNode)
  order?: number                // + 菜单排序（升序）；默认 100
  hidden?: boolean              // 从 + 菜单隐藏
  available?: (ctx: Context, scope: SessionScope, state: SidebarState) => boolean
  single?: boolean              // ≡ dedupeKey: () => id
  dedupeKey?: (tab: SidebarTab) => string | undefined  // 必须纯函数：每次 open 求值两次
  createTab?: (state: SidebarState) => { tab: SidebarTab; patch?: Partial<SidebarState> } | null
  urlTarget?: (url: URL) => boolean
  settings?: SidebarSettingsDeclaration      // { toggles?, pluginToggles?, render? }
  badge?: (ctx, scope, state) => string | number | null | undefined
  onOpen?: (tab: SidebarTab, scope: SessionScope) => void
  onActivate?: (tab: SidebarTab, scope: SessionScope) => void
  onClose?: (tab: SidebarTab, scope: SessionScope) => void
  component: (props: TabComponentProps) => ReactNode
}
```

**消费方 `package.json` 声明（逐字，来源：§2.2 / §13）**：
```jsonc
{
  "name": "my-plugin",
  "version": "0.1.0",
  "main": "lib/index.js",
  "exports": {
    ".": { "types": "./lib/types/index.d.ts", "default": "./lib/index.js" },
    "./client": { "types": "./lib/types/client/index.d.ts", "default": "./lib/client.js" }
  },
  "peerDependencies": {
    "@deepseek-ai/cordis": "^4.0.1",
    "dsh-better-sidebar": "workspace:*",
    "react": "^18.2.0"
  },
  "peerDependenciesMeta": {
    "dsh-better-sidebar": { "optional": true }
  }
}
```
> 关键：`dsh-better-sidebar` 必须是 **peerDependency**（不是 dependency，避免两份实例），且 `optional: true`（未装时你的插件照常加载）。

**能力的版本优雅降级（逐字，来源：§7）**：
```ts
if (ctx.betterSidebar.features.includes('badge')) {
  // 使用 TabDescriptor.badge
}
if (ctx.betterSidebar.version >= '0.12.0') { /* 字符串比较即可：minor 只增 */ }
```

**`better-sidebar` 自己的 `package.json` 关键字段（逐字，来源：`omdsh-dev_DSH-better-sidebar/package.json`）**：
```json
{
  "name": "dsh-better-sidebar",
  "version": "0.19.0",
  "type": "module",
  "main": "lib/index.js",
  "types": "lib/types/index.d.ts",
  "exports": {
    ".": { "types": "./lib/types/index.d.ts", "default": "./lib/index.js" },
    "./invariant": { "types": "./lib/types/invariant.d.ts", "default": "./lib/invariant.js" },
    "./client": { "types": "./lib/types/client/index.d.ts", "default": "./lib/client.js" },
    "./client/service": { "types": "./lib/types/client/service.d.ts", "default": "./lib/client.js" },
    "./client/api": { "types": "./lib/types/client/service.d.ts", "default": "./lib/client.js" },
    "./src/*": "./src/*",
    "./package.json": "./package.json"
  },
  "dsh": {
    "bundle": { "patch": "./cordis.patch.yml" },
    "client": {
      "inject": [
        "@deepseek-ai/dsh-client-locale",
        "@deepseek-ai/dsh-client-ui-slots",
        "@deepseek-ai/dsh-client-ui-conversation",
        "@deepseek-ai/dsh-client-ui-sidebar-right",
        "@deepseek-ai/dsh-client-modules"
      ],
      "platform": "web"
    }
  },
  "files": [
    "lib/index.js", "lib/invariant.js", "lib/client.js", "lib/client-registry.js",
    "lib/client-terminal.js", "lib/client-editor.js", "lib/client-mermaid.js",
    "lib/types/**/*.d.ts", "src", "scripts/install.sh", "scripts/install.ps1",
    "cordis.patch.yml", "README.md", "README_EN.md", "LICENSE"
  ],
  "scripts": {
    "build": "node -e \"require('node:fs').rmSync('lib',{recursive:true,force:true})\" && tsc -p tsconfig.build.json && tsdown",
    "prepublishOnly": "pnpm build",
    "test": "vitest run",
    "test:mount": "bash scripts/e2e-mount.sh",
    "check:consumer-types": "bash scripts/check-consumer-types.sh"
  },
  "peerDependenciesMeta": {
    "@huanlin/dsh-plugin-better-locale": { "optional": true },
    "@deepseek-ai/dsh-client-ui-sidebar-right": { "optional": true }
  }
}
```
> **注意 `files` 里必须带 `cordis.patch.yml`**（否则装上了不生效 —— 这是「漏带 patch 文件」的标准反例警戒点）。
---

## 二.5　`better-sidebar` 的退让表达式（`disabled: !!js`）—— 聚合包双挂载守卫

**`cordis.patch.yml` 全文**（来源：`omdsh-dev_DSH-better-sidebar/cordis.patch.yml`；长注释是「为什么这么写」的教材）：
```yaml
# dsh-better-sidebar bundle patch
#
# This file is the `dsh.bundle.patch` layer of the published npm package: when
# the plugin is installed through the official CLI —
#
#   dsh plugin --profile <name> add dsh-better-sidebar@<version>
#
# — the command reconciles `dsh.profile.bundles` against installed packages
# and, seeing this declaration, appends `dsh-better-sidebar` to the bundle
# stack. The profile boot then merges THIS patch (a single `insert` of the
# plugin row) exactly like the manual cordis.patch.yml mount line used
# before. No profile file edits needed — one command installs and mounts.
#
# If the profile still carries the old manual mount line in its own
# cordis.patch.yml, remove it before switching to the bundle channel to
# avoid double-mounting (two Node halves, two sidebars).
#
# To choose the terminal shell, add `config.shell` to the inserted plugin
# row (or to the profile's manual cordis.patch.yml mount line). When omitted,
# the host keeps resolving $SHELL / the login shell / powershell.exe.
# `config.shellArgs` optionally supplies explicit startup arguments; when
# non-empty they replace the automatic POSIX `-l` login flag:
#
#   - insert:
#       - id: better-sidebar
#         name: 'dsh-better-sidebar'
#         config:
#           shell: /bin/zsh
#           shellArgs:
#             - --noprofile
#             - --no-rc
#
# Aggregate double-mount guard: aggregate bundles (e.g. @linxin666/dsh-web-ui-all)
# may already mount this package under their own entry id (e.g.
# `web-ui-better-sidebar`). Two mounts register /sidebar/api twice and fail the
# whole plugin tree at boot ("duplicate prefix route"). The `!!js` disabled
# expression backs THIS row off when another *enabled* entry already mounts
# `dsh-better-sidebar`; the aggregate instance then owns the sidebar. The
# loader evaluates it when this row is processed (entry-list order, only rows
# before this one are visible), so the aggregate bundle must precede this one
# in `dsh.profile.bundles` — the standard install order, since `dsh plugin add`
# appends new bundles last. The reverse order (this bundle before the
# aggregate) is a known limitation: the guard cannot see rows that come after
# it, and no runtime singleton guard is added. Same-id manual duplicates still
# fail loudly at the loader as before.
- insert:
    - id: better-sidebar
      name: 'dsh-better-sidebar'
      disabled: !!js "[...ctx.loader.entries()].some((e) => e.options.name === 'dsh-better-sidebar' && e.options.id !== 'better-sidebar' && !e.disabled)"
```
> **这是本手册唯一一处 `disabled` 内使用 `!!js` 的真实生产范例**，且注释把「为什么行顺序重要」讲透了。

---

## 二.6　同类里代码量最小的组合包范本

**结论：`Q00_ouroboros/integrations/dsh-plugin/`（3 个文件，0 行 JS，1 个 `insert` 行）** 是本次四个仓库里、也是全仓清单里最小的「组合包」。

- 路径：生成期素材 `Q00_ouroboros/integrations/dsh-plugin/`（不随本 skill 发布）
- 文件：`package.json`（声明 `dsh.bundle.patch`）+ `cordis.patch.yml`（1 行 insert）+ `README.md`
- 对比：`better-sidebar` 组合包（同为零 JS bundle 层）也在用 `cordis.patch.yml`，但它的包里有完整 TS 源码 + 构建链；`dsh-desktop` 的组合包挂了 7 行并带 130 个源码文件。
- **推荐作为手册「第一个例子」**：把 ouroboros 的 `package.json` + `cordis.patch.yml` 直接当「最小可用组合包」模板（把 `name` 换成你的目标行、`config` 换成你的参数即可）。
- 全仓横向印证：本次扫描到 13 个仓库里共 20 个 `package.json` 声明了 `dsh.bundle`（含测试 fixture），最小的是 ouroboros 这一份。

---

# 三、本方向的开发规范（多家共识才叫「规范」）

> 说明：本节只把**至少两个仓库都这么做**的做法上升为「规范」，并在每条后面写清**依据**。只被单一仓库采用的做法标为「个别做法」，新手不必强行照抄。所有结论均来自本次读到的四个仓库源码 + 官方 DSH 源码交叉核对。

## 三.1 组合包（bundle）的规范

| 规范 | 依据（多家共识） | 说明 |
|---|---|---|
| 在 `package.json` 用 `dsh.bundle.patch` 指向**包根目录**的 `cordis.patch.yml` | ouroboros、dsh-desktop、better-sidebar 三家全中 | 值写成 `"./cordis.patch.yml"`，官方 `profile.ts` 会 `dirname(resolve(file)) + patch` 解析出补丁路径 |
| 补丁文件放在**包根目录**，不放 `src/` 里 | ouroboros、dsh-desktop、better-sidebar 三家全中 | 放 `src/` 里会因为 `files`/发布路径不对而在安装后丢失 |
| `files` 数组**必须**显式列出 `cordis.patch.yml` | 三家都在 `files` 里显式列了 `cordis.patch.yml` | 漏了它 → 包能装上、`dsh` 却读不到补丁 → **插件静默不生效**（详见 # 四 卡点 2） |
| 补丁用 `- insert:` 列表挂载插件行 | 三家一致 | 每行至少 `id` + `name`（`name` 是 npm 包名） |
| 覆盖已有行时用「带 `id`、不带 `insert`」的 override 形态 | dsh-desktop 明确使用（7 行 insert + 1 个 override）；官方复盘 0002 亦印证 | override **整块替换** `config`，不是深合并 → 只写要改的字段会丢掉其余字段 |
| `!!js` 只出现在 plugin `config` 的值里，或 entry 的 `disabled` 里 | 官方源码交叉印证 + ouroboros（config 内 6 处）+ better-sidebar（disabled 1 处） | 放在其它字段不会被求值，等于写了个死字符串 |
| 跨平台行为差异用 `disabled: !!js` 表达 | better-sidebar（聚合包双挂载守卫）为唯一真实范例；官方文档为此设计 | 求值上下文是「该 entry 被处理时的 injection-ready context」，**只能看到排在它之前**的行 |
| 可能启动失败的插件写 `failOnStartupError: false`（软失败） | ouroboros（`config.failOnStartupError: false`） | 缺依赖/缺 CLI 时不让整棵插件树崩，而是让该行降级 |
| 组合包里**零 JS** 是可行的、且是推荐起点 | ouroboros（0 行 JS） | 「组合包」本质是配置清单，不写运行时代码；需要逻辑才升级为 `dsh.client`/工具插件 |

## 三.2 包与发布（npm 工程）规范

| 规范 | 依据 | 说明 |
|---|---|---|
| 包名用 `dsh-<名>` 或 `dsh-plugin-<名>` | ouroboros(`dsh-ouroboros`)、dsh-desktop(`dsh-plugin-desktop`)、better-sidebar(`dsh-better-sidebar`) | 便于在 `dsh.profile.bundles` 里识别与社区检索 |
| `exports` 用 `{ "types": ..., "default": ... }` 双键 | dsh-desktop、better-sidebar 明确如此 | 只写 `default` 或只写 `main` 会让 `publint`/TS 解析告警 |
| **必须**导出 `"./package.json": "./package.json"` | dsh-desktop、better-sidebar 都显式导出 | 官方加载器/工具链会读包内 `package.json`（读 `dsh` 字段）；不导出会在部分解析模式下报 `ERR_PACKAGE_PATH_NOT_EXPORTED` |
| 所有 `@deepseek-ai/dsh-*` 依赖放 `peerDependencies` | better-sidebar 把它注入的 5 个 `dsh-client-*` 全放 peer | 避免同一套 host 被装出多份实例（多份实例会导致服务注册冲突，见 # 四 卡点 5） |
| 宿主/常驻服务类依赖放 `peerDependencies` 且标 `optional: true` | dsh-desktop 对宿主侧包如此处理 | 运行期由宿主提供，插件不自带 |
| 依赖的 `dsh-*` 包若只用于开发，提升进 `devDependencies` | anchored-standard、better-sidebar 都这么做 | 用 `pnpm peers check` 校验 peer 是否齐全 |

## 三.3 校验与测试规范（工程规范化方向的核心）

| 规范 | 依据 | 说明 |
|---|---|---|
| 提供统一 `check` 脚本 = build + typecheck + test + **真机挂载冒烟** | anchored-standard(`check`)、better-sidebar(`test:mount`)、dsh-desktop(`verify:closure/cli/loader/profile/licenses`) | 只跑单测不跑「真挂载」是新手最常漏的一环：单测全绿、装上却崩 |
| `prepack` / `prepublishOnly` 里跑 `check` | anchored-standard 明确把校验挂到发布钩子 | 防止没构建/没过检的包被发布 |
| 提供一致性门（`sync --check` 之类） | anchored-standard（`test/self-containment.test.mjs` 校验包内自包含） | 保证「仓库里的声明」和「发布产物」一致，不会出现补丁漏带 |
| 跨平台要有独立 CI 车道（Windows/Linux/macOS） | anchored-standard、better-sidebar 的坑都集中在平台差异（`/bin/bash`、大小写、CRLF） | 只在 Linux 跑 CI 会漏掉 Windows 全部路径/换行坑 |
| 回归测试必须能对「未修复代码」失败 | better-sidebar 的 271 个修复大多带回归测试 | 否则测试只是装饰，改坏了也发现不了 |
| 用 `publint` 校验发布形态 | 社区通行 + 各仓库 `exports` 写法一致 | 报 `exports` 键缺失、`main`/`types` 不匹配等 |

## 三.4 README / 文档规范

| 规范 | 依据 | 说明 |
|---|---|---|
| README 必备段落：定位（一句话）+ 安装命令（含 `--profile`）+ Requirements + 配置表 + FAQ + 来源目录 | ouroboros、dsh-desktop、anchored-standard、better-sidebar 全中 | 新手照着「安装命令」那一段逐字抄就能装上 |
| 安装命令必须写全 `dsh plugin --profile <名字> add <包名>` | 四家全中；官方 `args.ts` 里 `--profile` 是 `.requiredOption` | 省略 `--profile` 直接报错退出（详见 # 四 卡点 1） |
| 提供第三方扩展文档（若插件暴露扩展点） | better-sidebar(`docs/external-plugin-guide.md`) 为范本 | 有扩展点的插件，文档里要给出「函数名 + 签名 + 可抄示例」 |
| 双语（中/英）README | anchored-standard(`README.zh-CN.md`)、better-sidebar 均提供 | 面向中文新手建议至少提供中文版 |
| 在补丁注释里写清「为什么」 | ouroboros、better-sidebar 的 `cordis.patch.yml` 顶部都有大段注释 | 注释不是可选项：它解释了 id 选择、顺序敏感、如何覆盖 |

## 三.5 个别做法（不作为规范，仅记录）

- anchored-standard 的 `preset/agent.cordis.yml + preset.yml`（agent-plane 组合）是它自己的架构选择，不是所有插件都需要。
- dsh-desktop 用 `utilityProcess.fork` 起宿主进程，属于「桌面宿主」特有做法，普通插件不涉及。
- `isolate:` realm / `cordis:group` / `group: true` 只在需要服务隔离时使用，本次四个仓库里仅个别用到。

## 三.6 一句话总纲

> **组合包 = 一个 `package.json`（声明 `dsh.bundle.patch` + `files` 带上补丁）+ 一个 `cordis.patch.yml`（insert 若干行）；不写一行 JS 就能发布一个插件。所有工程规范（`exports`、`peerDependencies`、`check`、跨平台 CI）都是为了让这个组合包在别人机器上「装上就能跑」。**

---

# 四、新手最容易卡住的 5 个点（每点一句可执行建议）

> 排序按「新手实际撞上的概率 × 排查难度」从高到低。每条都附**现象 + 报错/原文 + 最省事的修法**。

## 卡点 1：安装命令漏了 `--profile`

- **一句话建议：任何 `dsh plugin` 安装/移除命令，都写全 `dsh plugin --profile <你的profile名> add <包名>`，`--profile` 永远不能省。**
- **现象**：照着某些 README 写 `dsh plugin add dsh-better-sidebar`，命令直接退出、什么都没装。
- **报错原文**：CLI 打出 `error: required option '--profile <name>' not specified`（官方 `apps/cli/src/args.ts` 里它是 `.requiredOption`，不是可选参数）。
- **根因**：DSH 是多 profile 设计，插件必须装进某个 profile 才有意义；CLI 用「必填参数」强制你指定。
- **正确写法**（逐字抄，把 `<名字>` 换掉）：
  ```
  dsh plugin --profile default add dsh-better-sidebar
  ```
- **备注**：`--profile` 的值要和 `dsh.profile.name` 一致；不确定就先用 `dsh profile list` 看有哪些。

## 卡点 2：`files` 漏了 `cordis.patch.yml` —— 包装上了、插件却「静默不生效」

- **一句话建议：发布前先跑 `npm pack --dry-run`，在文件清单里亲眼确认 `cordis.patch.yml` 在里面。**
- **现象**：`dsh plugin --profile default add 你的包` 成功；`package.json` 的 `dsh.profile.bundles` 也加上了包名；重启 DSH 后插件**完全没有任何效果**，也**没有任何报错**。这是最折磨人的「无声失败」。
- **根因**：`files` 是一份**白名单**。如果你写了 `"files": ["lib", "README.md"]` 却漏了 `cordis.patch.yml`，npm 打包时就把补丁文件排除在发布物之外。安装后 `dsh.bundle.patch` 指向 `./cordis.patch.yml` 这个**不存在的文件**，加载器读不到补丁行，于是跳过——不报错，只是不生效。
- **修法**（逐字改 `package.json`）：
  ```json
  "files": [
    "cordis.patch.yml",
    "README.md",
    "lib"
  ]
  ```
- **自检**：`npm pack --dry-run 2>&1 | grep cordis.patch.yml` 有输出才算过。

## 卡点 3：双挂载 —— 两个侧边栏 / 启动报 `duplicate prefix route`

- **一句话建议：从「手动挂载行」切换到「bundle 安装」时，先删掉 profile 里原有的手动 mount 行，再执行 `dsh plugin add`。**
- **现象**：界面上出现**两个侧边栏**（或两套同功能面板）；或启动直接失败，报 `duplicate prefix route`，整棵插件树起不来。
- **根因**：同一个插件被挂了两次。旧的手动 `insert` 行还在 profile 的 `cordis.patch.yml` 里，新装的 bundle 又插了一行 → 两个 Node 半边、两条 `/sidebar/api` 路由，路由前缀重复就报 `duplicate prefix route`。
- **修法**：
  1. 打开 profile 的 `cordis.patch.yml`，删掉手动的插件行；
  2. 只保留 bundle 那一行；
  3. 若无法删（被聚合包带上），用插件自带的 `disabled: !!js` 守卫退让（见 二.5 的 better-sidebar 范例）。
- **顺序敏感**：`!!js` 守卫**只能看到排在它之前**的行，所以聚合包必须在被退让的插件之前；`dsh plugin add` 默认把新 bundle 追加到最后，正是这个顺序。

## 卡点 4：子进程拿不到 API Key（凭据 scrub）+ profile 覆盖整块替换 `config`

- **一句话建议：别把密钥写进插件 `config`；子进程默认拿不到 `*KEY/*TOKEN/*SECRET/*PASSWORD` 和 `DSH_*` 环境变量，要用就自己显式透传。**
- **现象 A**：插件里 spawn 的子进程拿不到 `MY_API_KEY` / `DEEPSEEK_API_KEY`，请求 401。
- **根因 A**：`@deepseek-ai/dsh-subprocess` 在起子进程前会按 `SENSITIVE_ENV_PATTERN = /KEY|PASSWORD|SECRET|TOKEN/i` 以及 `DSH_*` 前缀**清洗环境变量**，防止把宿主的密钥泄露给第三方子进程。名字里带 `KEY`/`TOKEN`/`SECRET`/`PASSWORD` 的变量会被删掉。
- **修法 A**：给这类变量起一个不含敏感词的名字（如 `OUROBOROS_DSH_CONFIG_PATH`），或由插件在**自己的**配置里显式读取后再传给子进程。
- **现象 B**：profile 里覆盖某个插件行后，插件的其它配置「莫名其妙没了」。
- **根因 B**：override 形态（带 `id`、不带 `insert`）是**整块替换** `config`，**不是深合并**。只写 `config: { timeout: 1000 }` 会把原来的 `failOnStartupError` 等字段全部丢掉。
- **修法 B**：override 时**把要保留的字段一起写全**。

## 卡点 5：服务注册没包 `ctx.effect` / id 撞车 → `already registered`

- **一句话建议：每一次服务注册（`ctx.provide()` 等）都写进 `ctx.effect(() => { ...; return () => { /* 清理 */ } })`，并用全局唯一 id。**
- **现象**：热重载或二次挂载时报 `already registered`；或卸载后服务没清干净，重启出现「幽灵服务」。
- **根因**：把 `ctx.provide('xxx', ...)` 直接写在 `apply` 顶层，插件卸载/热重载时旧实例没有被清理，再次挂载就重复注册同名服务。
- **修法**（骨架，逐字可抄）：
  ```ts
  export const name = 'my-plugin'
  export const inject = ['sidebar']
  export function apply(ctx: Context) {
    ctx.effect(() => {
      const dispose = ctx.sidebar.register({ /* ... */ })
      return () => dispose()   // 卸载时一定要调
    })
  }
  ```
- **补充**：多个插件注册同一 id（例：两个插件都想占 `better-sidebar` 这个 id）也会报错；id 命名带上你的包名前缀最安全。

---

# 附、本次实际读取清单（可复核）

> 说明：以下均为**实际打开读过正文**的文件（不是目录列举）。四个仓库的 git 历史只含 commit 元数据（无文件 blob），故修复提交的「解释」来自 commit message 与其指向的 `.agents/notes` 文档，无法用 `git show <hash>:<path>` 取旧文件。

## 1. `Q00_ouroboros`（dsh-ouroboros）
- `src/Q00_ouroboros/integrations/dsh-plugin/package.json`（全文）
- `src/Q00_ouroboros/integrations/dsh-plugin/cordis.patch.yml`（全文，含顶部大段注释）
- `src/Q00_ouroboros/integrations/dsh-plugin/README.md`（全文）
- `src/Q00_ouroboros/README.md`（全文）
- `src/Q00_ouroboros/docs/guides/deepseek-harness.md`（全文）
- git 日志：`repos/Q00_ouroboros/`（commit 元数据）

## 2. `anywhere-labs_dsh-desktop`（dsh-plugin-desktop）
- `src/anywhere-labs_dsh-desktop/dsh-plugin-desktop/package.json`（全文）
- `src/anywhere-labs_dsh-desktop/dsh-plugin-desktop/cordis.patch.yml`（全文）
- `src/anywhere-labs_dsh-desktop/dsh-plugin-desktop/README.md`（全文）
- `src/anywhere-labs_dsh-desktop/dsh-plugin-desktop/src/host-process.ts`（全文）
- `src/anywhere-labs_dsh-desktop/dsh-plugin-desktop/src/pnpm.ts`（全文）
- `src/anywhere-labs_dsh-desktop/dsh-plugin-desktop/src/desktop-port.ts`（全文）
- `src/anywhere-labs_dsh-desktop/dsh-plugin-desktop/src/index.ts`（全文）
- `.agents/notes/implemented/architecture/` 下 7 篇中文设计说明：
  `packaged-profile-fallback`、`bundled-pnpm-runtime`、`profile-management`、`beta-isolated-host`、`runtime-renderer-recovery`、`startup-resource-ownership`、`plugin-install-lifecycle-ownership`
- git 日志：`repos/anywhere-labs_dsh-desktop/`（commit 元数据；多数 commit body 为空，解释在 `.agents/notes`）

## 3. `xiaobright_dsh-anchored-standard`
- `src/xiaobright_dsh-anchored-standard/package.json`（全文）
- `src/xiaobright_dsh-anchored-standard/README.zh-CN.md`（全文）
- `src/xiaobright_dsh-anchored-standard/preset/agent.cordis.yml`（全文/节选）
- `src/xiaobright_dsh-anchored-standard/preset/preset.yml`（全文）
- `src/xiaobright_dsh-anchored-standard/combo-anchored/preset.yml`（全文）
- `src/xiaobright_dsh-anchored-standard/test/self-containment.test.mjs`（全文）
- 完整 126 文件目录树（列举 + 关键文件阅读）
- git 日志：`repos/xiaobright_dsh-anchored-standard/`（commit 元数据）

## 4. `omdsh-dev_DSH-better-sidebar`
- `src/omdsh-dev_DSH-better-sidebar/package.json`（全文）
- `src/omdsh-dev_DSH-better-sidebar/cordis.patch.yml`（全文）
- `src/omdsh-dev_DSH-better-sidebar/dsh.plugin.json`（全文）
- `src/omdsh-dev_DSH-better-sidebar/AGENTS.md`（全文）
- `src/omdsh-dev_DSH-better-sidebar/README.md`（全文）
- `src/omdsh-dev_DSH-better-sidebar/docs/external-plugin-guide.md`（全文）
- `src/omdsh-dev_DSH-better-sidebar/src/client/service.ts`（全文）
- git 日志：`repos/omdsh-dev_DSH-better-sidebar/`（644 commits，其中 271 条修复类；逐条读 message 提炼）

## 5. 官方 DSH 源码（用于交叉验证机制）
- `deepseek-harness/packages/boot/app-boot/src/index.ts`（`!!js` 求值作用域、`anchorInsertedPluginNames()` 相对路径锚定）
- `deepseek-harness/packages/boot/app-boot/src/profile.ts`（`dsh.bundle.patch` 的读取与解析逻辑）
- `deepseek-harness/apps/cli/src/args.ts`（`--profile` 为 `.requiredOption`）

**合计：4 个目标仓库共约 34 个源码/文档文件实际读取全文或大段正文 + 官方 DSH 3 个源文件 + 4 份 git 日志（commit 元数据）。**

---


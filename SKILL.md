---
name: dsh-plugin-development
slug: dsh-plugin-development
displayName: DSH Plugin Development
summary: Develop DSH (DeepSeek Harness) / Cordis plugins end to end — plugin forms, templates, an API cookbook, catalogued pitfalls, packaging and publishing, plus a mandatory version gate for the pre-stable upstream.
description: A development-time skill for building plugins on DSH (DeepSeek Harness) / Cordis. It is not itself an installable DSH plugin; it is the tooling that guides a developer or AI agent through creating, debugging, packaging, and publishing one. This skill should be used when the user asks to develop a DSH plugin, write or modify a cordis plugin, add a tool, slash command, config schema, service, UI slot or HTTP route to DSH, run a periodic task inside a plugin, fix a plugin that fails to load or stays in PENDING, or package a plugin bundle for installation or distribution. It covers the plugin forms and the official engineering conventions, with 12 templates, 23 catalogued pitfalls, and copy-ready prompts for AI-agent pair development. Because DSH is pre-stable and ships breaking changes on a short cadence, it also ships a mandatory version gate to answer before writing any DSH code, a probe that re-verifies its own API and negative claims against a live source checkout, and a per-tag history of upstream breaking changes.
version: 1.0.7
license: MIT-0
agent_created: true
metadata:
  openclaw:
    emoji: "🔌"
    homepage: https://github.com/liupengyang-1008/dsh-plugin-development
    requires: { anyBins: [python3, python] }
---

# DSH 插件开发

把「DSH 插件」从选型做到发布：选形态 → 写代码 → 排错 → 打包 → 发布。入口只放**执行时必需**的东西（闸门 / 选型 / 路由 / 工作流 / 红线 / 合同 / 验收），细节一律在 `references/`，按需读取，不要一次全读。

> **定位：这是一个「用来开发 DSH 插件的技能」，它本身不是能装进 DSH 的插件。** 它不会被 `dsh plugin add` 安装，也不进入任何 DSH profile；**本技能产出的那个 `dsh.bundle` 包才是能装进 DSH 的东西**。找现成插件请去社区插件市场（`references/12-community-plugins.md`）。
> 已知边界与维护守则见 `references/15-skill-scope-and-maintenance.md`（此处不重复）。

## 何时使用

- 用户要求开发 / 修改 / 调试 / 打包 / 发布 DSH（DeepSeek Harness）插件
- 出现这些词：DSH 插件、cordis 插件、`cordis.patch.yml`、`dsh.bundle`、`defineTool`、`ctx.slots`、`ctx.tools.register`、PENDING
- 用户要求审查现有 DSH 插件代码、判断该用哪种插件形态
- 用户问「为什么我的插件装上了但没反应」
- 用户报这些症状：**插件不生效 / slot 崩溃 / 服务注入失败 / 改了代码不生效 / 样式被冲掉**

**不适用**：要的是「装进 DSH 就能直接用的现成插件」——本技能不提供任何运行时能力、也不负责插件分发。

## 第 0 步（强制，不可跳过）· 版本闸门

**references 是某一时刻的快照，会腐化。** DSH 处于 rc 阶段（基线 `v0.1.5-rc.2` / commit `c291e7961a`，2026-09-10），tag 间隔中位数约 1.1 天、出现过破坏性变更。**所以不要承诺「不过时」，要保证「过时会响」。**

**① 权威顺序（源码永远压过本技能）**

```
1. 当前 DSH 源码                    ← 唯一权威
2. 探针脚本对当前源码的核验结果      ← 可执行的证据
3. 本技能的 references（快照）       ← 脚手架，不是权威
4. 模型记忆 / 常识                   ← 禁止作为唯一依据
```

**② 三问**：① 我在对哪个版本写代码？（拿不到就**先要版本**，不知道版本不得断言 API）② 我要用的 API 属于 S/M/V 哪一级？③ 我能核验吗？（不能 → 走降级规则）

**③ 跑探针**（两个版本，优先 Python 版）

```bash
python <skill>/scripts/dsh-api-probe.py <DSH 仓库路径>    # 推荐：零 coreutils 依赖，Windows 最稳
bash   <skill>/scripts/dsh-api-probe.sh <DSH 仓库路径>    # 备选：仅当 shell 有完整 coreutils
# 0 = 断言全部成立    1 = 有 STALE（不要照抄）
# 2 = 仓库路径不对    3 = 断言表为空（结果无效）
```

> ⚠️ shell 缺 `cat`/`grep`/`dirname` 时，bash 版会报几十条**假 STALE**。拿不准就用 Python 版；两者不一致以 Python 版为准。
> **S/M/V**：问「这条事实明天变了，我的代码会崩吗？」——会崩 → M/V，必须核验；不会崩 → S，可直接用。
> **降级规则**（拿不到源码时）：① 显式声明「以下 API 未对当前版本核验」；② S 级骨架照给，M/V 级符号单列成「需你确认」；③ 禁止把未核验事实写成肯定句。**绝不编造 API 名填补空白。**
> **目标版本高于基线时**不要猜：`dsh-sync.sh` 拉源码（先经确认）→ 探针核验 → `dsh-version-diff.sh` 出差异。
> 完整机制（腐化推导、三级全表、五种核验手段、网络不可达时的降级路径）见 `references/00-version-gate.md`。

## 三条基础纪律

1. **引用任何字段名 / 事件名 / 服务名 / 插槽名前，先查 `references/08-cheatsheet.md` 或 `references/api-claims.md`。** 查不到就 grep 源码，**不要凭印象写**。
2. **代码跑通前不要声称完成。**「装上了」不等于「生效了」——必须看到实际输出或界面变化。
3. 每条结论尽量附出处（文件路径 + 行号）。

## 决策流程

### 第 1 步 · 选形态（选错形态 = 后面全部返工）

| 形态 | 何时选 | 必须这样写 | 禁止 |
|---|---|---|---|
| **函数式插件** | 绝大多数情况：加工具 / 命令 / 事件监听 | 具名导出 `name` / `inject` / `Config` / `apply` | **绝对不能有 `export default`**（会被当成服务类解析而失败） |
| **服务插件** | 要给**别的插件**提供能力，让别人 `inject` 你 | `export default class extends Service`，构造函数首行 `super(ctx, '服务名')` | 写成普通函数导出 |
| **组合包 bundle** | 只是把已有插件装到一起，纯配置 | 只需 `package.json` + `cordis.patch.yml`，声明 `"dsh": {"bundle": {"patch": "./cordis.patch.yml"}}` | 不要写 JS / TS，不要有 `src/` |

> **UI 插件是函数式插件的特例**，不是第四种形态——它只是多了一个「浏览器半侧」和若干登记点。判定流程见 `references/01-mental-model.md`。

### 第 2 步 · 按需求路由到模板

用户不会说「T3」或 `defineTool`，他说的是人话。**照抄用户的说法**在左列定位，再往右走：

| 用户这么说 | 模板 | 形态 | 注册在哪 | 怎么算跑通（冒烟判定） |
|---|---|---|---|---|
| 「把某个现成能力 / MCP server 挂进来」 | **T1** | 组合包 | `cordis.patch.yml`（零代码） | `--dump-config` 里出现 insert 行 |
| 「改一下某个现成插件的行为」 | **T2** | 组合包 + 覆盖层 | 同上 + 补丁字段 | 同上，且被改的行为确实变了 |
| 「让模型会用某个能力」「加个工具」 | **T3**（首选）/ **T4** | 函数式插件 | 宿主半侧 `ctx.tools.register(defineTool({...}))` | 真实会话里模型调用它并拿到结果 |
| 「加个 /命令」 | **T5** | 函数式插件 | `ctx.commands.register({...})` | 敲一次 `/命令`，有返回 |
| 「让用户能调参 / 改配置」 | **T6** | 函数式插件 | `export const Config` | 改配置后行为变化；非法配置被拒 |
| 「给别的插件提供能力」「当基础设施」 | **T7** | 服务插件 | `extends Service` / `ctx.provide` | 另一个插件能 `inject` 并调用成功 |
| 「网页界面上加个东西」 | **T8** | 函数式插件 + 浏览器半侧 | `ctx.slots.inject(key, () => ctx.slots.register({...}, 组件))` | 界面出现你的东西，无 slot 崩溃 |
| 「设置界面里加一张卡」 | **T9** | 同上 | 设置命名空间 + `settings.*` 插槽 | 卡片可见、改动生效 |
| 「管住 Agent / 拦消息 / 改请求 / 加提示词」 | **T10** | 函数式插件 | `agent/pre-step`、`agent/request`（waterfall） | 跑一次会话，行为确实被改 |
| 「接一个外部系统（HTTP / CLI / 协议）」 | **T11**（零代码优先 → **T1**） | 函数式插件 或 组合包 | 工具 + 事件钩子 | 真调一次外部系统，拿到真数据 |
| 「暴露一个接口给外面调」「加个健康检查」 | — | 函数式插件 | `ctx.webServer.register({kind, path, handler})` | `curl` 真打一次，看到 200 与预期响应体 |
| 「每天定时跑」「周期任务」 | — | 函数式插件 | `ctx.interval(cb, delay)`（**不是** `ctx.setInterval`） | 等一个周期，看到任务真的跑了 |
| 「建一个规范的完整工程 / 准备发布」 | **T12** | 工程骨架 | 全套约定 | 门禁脚本通过 + 真 profile 安装成功 |
| 「托管静态文件」「发布一个 DSH skill」 | ⚠️ 范围外 | — | — | 见 `references/15-skill-scope-and-maintenance.md` |

**没在表里？** 先按「实现位置」归属——改宿主行为 = 工具/命令/服务/事件；改界面 = 插槽；只是组装 = 补丁。归属清楚后照最近的模板改。
带 `—` 的两行（入站 HTTP / 定时任务）没有独立模板，完整写法见 `references/14-inbound-http-and-timers.md`；更细的路由展开见 `references/01-mental-model.md` §1.1 与 `references/08-cheatsheet.md` A.4，**冲突时以 references 的逐字源码为准**。

### 第 3 步 · 按难度阶梯选模板

**不要从最难的开始。** 先做能跑通的最小闭环，再逐级加复杂度：零代码组合包（T1/T2，低）→ 斜杠命令（T5，低）→ 工具插件（T3/T4，中）→ 可配置插件（T6，中）→ 服务插件（T7，中高）→ UI 与设置卡片（T8/T9，高）→ Agent 流程拦截（T10，高）→ 外部集成 / 完整工程骨架（T11/T12，高）。

12 个模板的完整代码、官方 7 类模板的逐字源码、常用 UI 插槽名速查（**节选，非全清单**），都在 `references/02-templates.md`。

## 标准工作流

按顺序执行，每一步都能独立验证。**不要跳步**，也不要在上一阶段未确认时抢跑下一阶段。

| # | 阶段 | 做什么 | 完成标志（未达到不得进入下一步） | 读哪个文件 |
|---|---|---|---|---|
| **0** | **版本闸门** | **强制**：答三问 + 跑探针 | 探针退出码 0；或已显式声明哪些 API 未核验 | `00-version-gate.md` |
| 1 | 选型 | 判定三种形态之一 + 路由到模板 | 形态与模板编号都写下来了，且**没有 `export default`** | `01-mental-model.md` → `02-templates.md` |
| 2 | 环境 | 版本对照、`DSH_HOME` 位置、从源码跑起来 | `dsh --profile <名字> --dump-config` 能打出组合树 | `06-workflow.md` ① |
| 3 | 最小闭环 | 先做一个能加载、能看到的空插件 | **装进真 profile 后有可见结果**（哪怕只是一条命令返回） | `02-templates.md`（T1 或 T3） |
| 4 | 冒烟 | 给每个能力面立起冒烟点并跑通 | 对照本文件「冒烟与验收」的判定表，逐项为真 | 本文件「冒烟与验收」 |
| 5 | 写功能 | 按 API 写工具 / 命令 / 配置 / 服务 | `inject` 覆盖全部用到的服务；需清理的副作用在 `ctx.effect()` 内 | `03-api-cookbook.md` |
| 6 | UI（如需） | 两个半侧 + **三个登记点** + 插槽 | 界面出现你的东西，且控制台无 slot 崩溃 | `04-ui-and-slots.md` |
| 7 | 调试 | `--dump-config` 查组合树；PENDING 审计查注入失败；HMR 免重启 | 没有 PENDING 条目、没有静默失败 | `06-workflow.md` ④ |
| 8 | 打包 | 组合包结构、`package.json`、patch 引用、分发方式对比 | **合同不变量 5 条全过** | `06-workflow.md` ③ |
| 9 | 安装验证 | `dsh plugin --profile <名字> add <包>`（`--profile` 必填） | 从**最终分发源**重装后仍通过冒烟 | `06-workflow.md` ② |
| 10 | 工程化 | 命名、README 强制节、测试、门禁、提交规范 | 过 `07-conventions.md` 的门禁清单 | `07-conventions.md` |

**决策门的回退规则**（失败先分类，别一律推倒重来）：

- **合同级 / 形态级错误**（导出形式、`inject`、patch 声明、client 声明、名称三处不一致）→ **回第 1~2 步重新选型**。在错形态上打补丁只会越补越乱。
- **业务级错误**（逻辑、返回值、样式、报错信息）→ 留在第 5~7 步**原地修**。

**环境降级**：本机没有 Node / pnpm 时，仍要产出**等价的完整文件**，并在 `docs/plan.md` 里**显式标注跳过了哪些可执行验证**。不许把「跳过」写成「通过」。

## 冒烟与验收

**原则：每个能力面，先配一个「一眼能看出真假」的冒烟点，再写业务。** 新建插件时先立起三件套：**一条命令**（总能成功、输出可辨认）+ **一个真实调用**（工具/集成类要让模型真调一次，看它拿到真数据）+ **一个可见标记**（UI 类要在界面上一眼能看到）。

| 能力面 | 冒烟通过 = |
|---|---|
| 组合包 / 补丁 | `--dump-config` 里出现你的行，且改配置确实生效 |
| 命令 | 敲一次 `/命令`，有返回 |
| 工具 | 真实会话里模型调用它，拿到预期结果 |
| 服务 | 另一个插件 `inject` 后能调用成功 |
| 事件 / 拦截 | 触发一次事件，行为确实随之改变（不是静默无响应） |
| HTTP 路由 | `curl` 真打一次你注册的 `{kind, path}`，看到 200 与预期响应体 |
| 定时任务 | 等过至少一个周期，看到任务真的执行 |
| UI / 设置卡片 | 组件可见可交互，控制台无 `slot entry crashed`、无重复 React 报错 |
| 配置 | 改配置后行为变化；给非法值能被明确拒绝 |

⚠️ **三条反假通过的纪律**：① 必须在**真实组合**（真 profile、真加载）里验，本地另一份配置跑通不算；② 验收要指向**用户实际访问的那个 URL / 那个 profile**；③ 部分成功不能当成功返回——操作了一半要如实报错。

### 改完代码怎么生效（改错地方 = 白改）

| 改了什么 | 怎么生效 |
|---|---|
| profile / home 下 `cordis.patch.yml` 里的 `config` | **自动热替换**（框架卸载旧实例、加载新实例） |
| `--patch` 指定的 overlay 文件 | **不会**被热重载——改它必须重启进程 |
| 插件代码（`src/`） | 默认**必须重启**；想免重启要先开启 HMR（默认 `disabled: true`，且依赖 timer 插件，缺了会永久 PENDING） |
| 浏览器半侧（client） | 重新构建 → 重新安装 / 更新插件 → 刷新页面（client bundle 按 id 缓存） |

> 任何时候都**只改 `src/`，不要手改 `lib/`**——`lib/` 是构建产物，手改会在下次构建被覆盖。

## 合同不变量（写 `package.json` / patch / client 前必看）

DSH 里最常见的「我明明装了啊」有五种成因，全部落在这 5 条上：

1. `package.json`：`type: "module"`、`main: "lib/index.js"`；`exports["."]` 与 `exports["./package.json"]` **必备**。
2. 组合包形态再加：`dsh.bundle.patch` 指向 `./cordis.patch.yml`，且 `exports["./cordis.patch.yml"]` 与 `files` **都要有**。
   ⚠️ 少了 `dsh.bundle.patch`，`dsh plugin add` 只打一条 `declares no dsh.bundle` 警告然后**什么都不做**——新手第一大坑。
3. UI 形态再加：`dsh.client.platform: "web"` 与 `exports["./client"]` **必须成对存在**，缺一个客户端半侧根本不组装。
4. **名称三处一致（铁律）**：`package.json#name` = patch 的 insert `id` / `name` = 客户端 ModuleLoader `id`。
5. **禁止声明 `@deepseek-ai/*` 依赖**（DSH profile 已提供）；客户端 bundle 里 `react`、`react/jsx-runtime`、`react-dom`、`react-dom/client` **必须 external**（打进第二份 React 会导致 hooks 直接崩）。

逐字对照表、官方不变式原文、各形态 `files` 清单见 `07-conventions.md` 与 `08-cheatsheet.md`；客户端 bundle 的产物格式契约见 `14-inbound-http-and-timers.md` §17.3。

## 写代码前必读的八条红线

每条都来自官方事故复盘或社区真实提交，**违反任何一条都会被用户打回**：

1. **绝不写 `export default`** —— 函数式插件的头号杀手。
2. **可选服务一律用 `ctx.get('x')`，不用 `ctx.x`** —— 后者仅限已声明 `inject` 的服务；未声明就访问会 PENDING 或直接崩。
3. **手搓测试不算数** —— 必须用真实组合（真 profile、真加载）验证，不能只调函数单测。
4. **`!!js` 表达式只在 `config:` 与 `disabled:` 内求值** —— 写错位置会被当普通字符串。
5. **快照刷新 ≠ 正确性验证** —— 更新快照只是让测试通过，不代表行为正确。
6. **验收要指向「用户实际访问的那个 URL / 那个 profile」** —— 本地另一份配置跑通不算。
7. **别用 shell `&` 起后台进程** —— 用工具自己的后台机制，否则进程会随会话退出被杀。
8. **部分成功不能当成功返回** —— 操作了一半要如实报错，不能返回 success。

### 最容易写错的一处（`required` 有两条路径，规则相反）

这是本套手册调研中**发现并纠正的真实错误**：

- **`defineTool` 路径（DSH 自有 DSL）**：`required` 写在**属性级**，值为字面量 `true`。
  ```ts
  parameters: {
    questions: { type: 'array', required: true, description: '...' },  // ← 属性级
  }
  ```
- **裸 `ctx.tools.register` 路径（标准 JSON Schema）**：`required` 写在**对象级**，值为字符串数组 `required: ['a', 'b']`。

**两条路径规则相反，套错就静默失效。** 完整源码证据见 `05-pitfalls.md` 的坑 P7。

## 排查顺序

> **只问局部问题**（如「为什么我的 slot 崩溃」）时**不要重跑全流程**——直接按症状定位，改完只重跑受影响的验证。

1. 插件装上了但**完全没反应** → `06-workflow.md` 第 ④ 部分（`--dump-config` + PENDING 审计）
2. 报错信息看不懂 → `05-pitfalls.md` 的「报错信息 / 现象对照表」
3. 已知症状检索 → `05-pitfalls.md`（23 条坑，按症状编号 P1~P22b）
4. 追根究底（原始社区提交、行号级出处）→ `10-community-casebook.md`

## 端到端示例（一次完整的装配）

需求：「做一个插件，能敲一条命令查当前时间，也让模型能调用它。」

| 步 | 做什么 | 结果 |
|---|---|---|
| 0 | 版本闸门：确认目标版本 + 跑探针 | 探针退出码 0 |
| 1 | 选型：要「给人用」又要「给模型用」→ 都是**函数式插件** | 不是服务插件、不是组合包 |
| 2 | 路由：T5（命令）+ T3（工具） | 两者可以并存于同一个 `apply` |
| 3 | 最小闭环：先只写命令，让它能加载、能敲 | `export const inject = ['commands']` + `apply` 内注册 |
| 4 | 冒烟：装进真 profile，敲一次命令 | 有返回 = 链路通了 |
| 5 | 加第二个能力：工具走 `ctx.tools.register(defineTool({...}))`，`inject` 补 `'tools'` | 两个能力共用一个 `apply` |
| 6 | 可选：加 `export const Config`，让用户能调时区 | 改配置后行为变化 |
| 7 | 打包 → 安装 → **从最终分发源重装验收** | `dsh plugin --profile <名字> add <包>` |
| 8 | 留痕：把上述决策与验证结果写进 `docs/plan.md` | 可回放、可交接 |

⚠️ **合并多个模板时只有两条规则**：**`inject` 取并集**；**需要清理的副作用包进 `ctx.effect()` 并返回 disposer**（普通注册本身即 effect、会自动回收——见 `01-mental-model.md` §3.6，但显式 `effect` 更稳）。

## 交付前自检清单

逐项打勾；**打不了勾的项就是还没做完**。

- [ ] 形态选对了（函数式 / 服务 / 组合包），且**没有任何 `export default`**
- [ ] 版本闸门已过：三问答完 + 探针退出码 0（或已按降级规则声明未核验项）
- [ ] `inject` 覆盖所有用到的服务；可选服务走 `ctx.get('x')`
- [ ] 需要清理的副作用在 `ctx.effect()` 内并返回 disposer
- [ ] **合同不变量 5 条**全部满足（含名称三处一致）
- [ ] 每个能力面都有冒烟点，且**在真 profile 里**看到了实际输出 / 界面变化
- [ ] 没有手改 `lib/`（改的是 `src/`，且跑过构建）
- [ ] 打包产物齐全（`files` 含 patch 与 client；有静态资源也含）
- [ ] 失败路径试过：给坏输入 / 缺服务时报错能指向原因，而不是静默成功
- [ ] `docs/plan.md` 已按实际决策勾选完成（模板：`assets/plan-template.md`）

## 与 AI Agent 结对开发

用户常让 Agent 代写插件代码。此时：给 Agent 的提示词模板见 `09-agent-pairing.md`（两套来源共 10 个可直接复制的模板）；要求 Agent **每次附出处**（文件 + 行号），无出处不予采纳；交付后按 `07-conventions.md` 的门禁清单验收。

## 资源索引

### `references/`（按主题组织，共 17 篇：编号 `00`~`15` + `api-claims`）

| 文件 | 何时读 |
|---|---|
| `references/00-version-gate.md` | **写任何 DSH 代码前**；探针报 STALE 后；讨论「会不会过时」时 |
| `references/api-claims.md` | 想知道「这条事实属于 S/M/V/N 哪一级、该怎么核验」时 |
| `references/01-mental-model.md` | 开始任何插件前；搞不清形态 / profile / 组合包加载机制 / 该选哪个模板时 |
| `references/02-templates.md` | 要抄代码时。12 个模板（T1~T12）+ 官方 7 类模板逐字源码 + 常用 UI 插槽名速查（节选）+ 社区零代码组合包全文 |
| `references/03-api-cookbook.md` | 写工具 / 配置 / 命令 / 事件 / 服务 / 终端功能时 |
| `references/04-ui-and-slots.md` | 做 UI 插件或设置卡片时 |
| `references/05-pitfalls.md` | **写代码前通读；出问题时检索**。23 条坑 + 症状速查表 + 报错对照表 + 官方 4 篇事故复盘全文 |
| `references/06-workflow.md` | 环境准备 / 安装与 CLI 机制 / 打包分发 / 调试排错——四部分顺序阅读 |
| `references/07-conventions.md` | 想做得像官方包一样规范时（官方约定 + 命名/测试/门禁 + 版本兼容军规） |
| `references/08-cheatsheet.md` | **随手查**：三形态对照表 + 服务名/事件名/插槽名/命令/CLI/路径/参数 DSL 全表 |
| `references/09-agent-pairing.md` | 与 Agent 结对开发（10 个提示词模板 + 十条红线） |
| `references/10-community-casebook.md` | 追根究底：原始社区素材、行号级出处（6.6k 行，**最后再读**，用 grep 检索而非整读） |
| `references/11-glossary-and-provenance.md` | 查术语、来源、素材代号对照（§A.2）、已知边界与官方文档矛盾 |
| `references/12-community-plugins.md` | 选型参考、找可借鉴的社区高星插件 |
| `references/13-version-history.md` | **目标版本高于基线时必读**；查 tag 版本史、破坏性变更、更新流程 |
| `references/14-inbound-http-and-timers.md` | 要暴露 HTTP 接口 / 写定时任务 / 搞清客户端产物格式时 |
| `references/15-skill-scope-and-maintenance.md` | 评估本技能是否适用、或要修改本技能时（已知边界 + 维护守则） |

### `assets/`（可直接复制 / 改名）

- `assets/minimal-bundle/` —— 零代码组合包（T1 形态，0 行 JS）
- `assets/minimal-tool-plugin/` —— 最小工具插件（T3 形态，`defineTool` + 参数 Schema）
- `assets/plan-template.md` —— 决策留痕模板（复制到插件项目的 `docs/plan.md`）

### `scripts/`（确定性工具，用法与退出码见脚本头部注释）

| 脚本 | 作用 | 关键点 |
|---|---|---|
| `dsh-api-probe.py <仓库路径>` | **防过时探针（首选）**：核验 43 条正向 + 5 条反向断言 | 退出码 0/1/2/3；纯标准库、零外部命令依赖 |
| `dsh-api-probe.sh <仓库路径>` | 同上的 bash 版（断言表须与 .py 版同步） | 依赖 coreutils；**缺 `grep` 会报假 STALE** |
| `verify_absorbed_claims.py <仓库路径>` | **第二批断言核验器**：27 条（入站 HTTP / 定时器 / 客户端产物 / 插槽 / 防编造否定） | 先跑 `--selftest` 证明它能失败 |
| `extract_slots.py <仓库路径> <skill目录>` | 从源码抽取**权威插槽清单**并与本技能声明比对 | 写「插槽名」前用它，不要凭表抄 |
| `check_refs.py <skill目录>` | **资源引用一致性**：悬空引用 / 生成期素材路径 / 本机绝对路径 | 退出码 0 = 全部可在技能内解析 |
| `dsh-sync.sh` | 把 DSH 源码拉进技能目录（`vendor/dsh-src/`） | 首次约 200 MB，**必须先经开发者确认**；**绝不执行 pnpm install** |
| `dsh-version-diff.sh <仓库路径>` | 出「基线 → 最新」差异，六维度 + 作者自报的 `!:` 提交 | 需要本地是 git 仓库；输出可追加到 `13-version-history.md` |
| `dsh-tag-matrix.sh <仓库路径> [out.tsv]` | 历史矩阵复核：对全部 tag 逐条核验 API 面 | 只在质疑「API 名是否稳定」这类**历史结论**时用 |

**大文件检索**（`references/` 单文件最大 6.6k 行，优先检索而非整读）：

```bash
grep -rn "ctx.slots.inject" references/ | head -30        # 某 API 名出现在哪
grep -n -A 40 "^### 坑 P7" references/05-pitfalls.md      # 某个坑的全文（按编号）
```

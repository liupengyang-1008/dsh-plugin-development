# DSH 插件开发技能 · `dsh-plugin-development`

> **这是一个「用来开发 DSH 插件的技能」，它本身不是能装进 DSH 的插件。**
> 它不会被 `dsh plugin add` 安装，也不进入任何 DSH profile；**它帮你产出的那个 `dsh.bundle` 包，才是能装进 DSH 的东西。**

**中文** · [English](README.en.md)

一套给开发者与 AI Agent 用的 DSH 插件工程能力：**选形态 → 写代码 → 排错 → 打包 → 发布**，全链路都有可直接复制的模板、可执行的校验脚本，以及一份「过时会响」的版本闸门。

[技能市场](https://skillhub.cn/skills/dsh-plugin-development) · [GitHub](https://github.com/liupengyang-1008/dsh-plugin-development) · 许可 MIT-0

---

## 目录

- [0. 30 秒看懂](#0-30-秒看懂)
- [1. 安装](#1-安装)
- [2. 第一次使用：零学习成本](#2-第一次使用零学习成本)
- [3. 由浅入深：四个难度阶梯](#3-由浅入深四个难度阶梯)
- [4. 它里面装了什么](#4-它里面装了什么)
- [5. 为什么它不承诺「不过时」](#5-为什么它不承诺不过时)
- [6. 出问题了去哪儿查](#6-出问题了去哪儿查)
- [7. 与 AI Agent 结对开发](#7-与-ai-agent-结对开发)
- [8. 常见问题](#8-常见问题)
- [9. 基线、已知边界与许可](#9-基线已知边界与许可)

---

## 0. 30 秒看懂

| 问题 | 答案 |
|---|---|
| **这是什么** | 一套写给 AI Agent 的 DSH 插件开发手册 + 一包可执行的校验工具 |
| **谁用** | 装了 DSH、想给它写插件的人；以及替人写插件的 AI Agent |
| **怎么用** | **对它说话**——不是敲命令行工具。加载后它指导 Agent 完成开发全流程 |
| **它给你什么** | 12 个可复制模板 · 23 条踩坑 · 8 个校验脚本 · 1 套防过时版本闸门 · 10 个结对提示词 |
| **它不给你什么** | ❌ 现成的可装插件（那是它帮你**做**的东西）❌ DSH 运行时依赖 |
| **前提** | 目标机器上有 DSH（DeepSeek Harness）源码或安装、有 Python 3 或 bash |

### 一句话判断它适不适用

> 用户说的是「**给我写/改/修/打包一个 DSH 插件**」→ 适用。
> 用户说的是「**给我一个装进 DSH 就能用的现成插件**」→ **不适用**，去社区插件市场（见 `references/12-community-plugins.md`）。

---

## 1. 安装

### 方式一 · 从技能市场装（推荐）

```bash
skillhub install dsh-plugin-development --namespace user_9d594bab
```

技能会落在客户端的 skills 目录下，例如 `~/.workbuddy/skills/dsh-plugin-development/`。

> 本技能在 **SkillHub**（<https://skillhub.cn/skills/dsh-plugin-development>）与 **ClawHub**（搜索 `dsh-plugin-development`）上均有发布。两个渠道的版本可能不同步，以技能内 `SKILL.md` 的 `version` 为准。

### 方式二 · 手动放置（从 GitHub 或 zip）

```bash
git clone https://github.com/liupengyang-1008/dsh-plugin-development.git
```

然后把整个目录放到客户端的 skills 目录下：

```
macOS / Linux :  ~/.workbuddy/skills/dsh-plugin-development/
Windows       :  C:\Users\<你的用户名>\.workbuddy\skills\dsh-plugin-development\
```

或用发布包 `dist/dsh-plugin-development.zip` 解压到同一位置。

### 装完怎么确认

目录里应当是这套结构（`SKILL.md` + 三个资源目录）：

```
SKILL.md          ← 入口层：闸门 / 选型 / 流程 / 红线 / 验收
references/       ← 17 篇专题文档，按需读取
scripts/          ← 8 个确定性校验工具
assets/           ← 可直接复制改名的工程骨架
```

**功能验证**：向 AI 提一个 DSH 插件相关的问题（例如「帮我判断这个插件该用哪种形态」）。如果回答里出现「**第 0 步 · 版本闸门**」、模板编号（`T1`~`T12`）或「冒烟判定」这类概念，说明技能已被加载。

---

## 2. 第一次使用：零学习成本

**这个技能的最佳用法是不要读文档，直接对它说人话。**

> 「帮我写一个 DSH 插件：在会话里加一条 `/hello` 命令，再让模型能用上一个查时间的能力。」

Agent 会自动走完：**选形态 → 路由到模板 → 写最小闭环 → 立冒烟点 → 验证 → 打包**。你不需要知道「T3」「defineTool」这些词——技能里有一张「用户这么说 → 模板 → 形态 → 注册在哪 → 怎么算跑通」的路由表，负责把你的话翻译成技术动作。

它会先做一件事，而且**不允许跳过**：

```bash
# 第 0 步 · 版本闸门：核验本技能记录的事实，是否还符合你手上的 DSH 版本
python scripts/dsh-api-probe.py <你的 DSH 仓库路径>
# 0 = 断言全部成立（43 正向 + 5 反向 = 48）
# 1 = 有 STALE —— 某条事实已过时，不要照抄模板
# 2 = 那不是 DSH 仓库（防对着错目录得出错误结论）
# 3 = 断言表为空 —— 什么都没核验，结果无效
```

**为什么必须先跑它**：DSH 处于 rc 阶段，tag 间隔中位数约 1.1 天，出现过破坏性变更。本技能的文档是某一时刻的快照，源码永远压过它。

---

## 3. 由浅入深：四个难度阶梯

不要从最难的开始。**先做能跑通的最小闭环，再逐级加复杂度。**

### Level 1 · 零代码组合包 —— 不写一行 JavaScript

**什么时候用**：只是把已有能力组装到一起。典型需求是「把某个 MCP server 挂进 DSH」「改一下某个现成插件的行为」。

**要点**：全部行为由 `cordis.patch.yml` 描述，没有 `src/`，没有 JS 入口。骨架在 `assets/minimal-bundle/`。

三个文件里，`package.json` 有一行是新手第一大坑：

```jsonc
{
  "name": "dsh-my-bundle",
  "type": "module",
  "files": ["cordis.patch.yml", "README.md"],
  "exports": {
    "./cordis.patch.yml": "./cordis.patch.yml",
    "./package.json": "./package.json"
  },
  "dsh": {
    "bundle": {
      "patch": "./cordis.patch.yml"   // ← 少了它，dsh plugin add 只打一条警告然后什么都不做
    }
  }
}
```

补丁文件顶层是**单个数组**，每行 `id` 必须全局唯一：

```yaml
- insert:
    - id: mcp-my-capability
      name: '@deepseek-ai/dsh-mcp-client'
      config:
        serverName: my-capability
        transport: stdio
        command: npx
        args: [-y, my-mcp-server]
        # 子进程环境会被清洗掉 *KEY|PASSWORD|SECRET|TOKEN* 与所有 DSH_* 变量，
        # 要传的凭据必须在这里显式列出
        MY_API_KEY: !!js process.env.MY_API_KEY ?? ''
```

**安装与验证**（`--profile` 是必填参数，不是可选项）：

```bash
dsh plugin --profile <profile 名> add ./minimal-bundle     # 安装
dsh plugin --profile <profile 名> ls                       # 确认已登记
dsh --dump-config                                          # 不启动就能看组装结果
```

> **冒烟通过 =** `--dump-config` 里出现你的那行，并且改配置确实生效。

---

### Level 2 · 加一个工具 —— 最典型的函数式插件

**什么时候用**：「让模型会用某个能力」。骨架在 `assets/minimal-tool-plugin/`（纯 JS，零构建，开箱可装）。

```js
import { defineTool } from '@deepseek-ai/dsh-tools'

export const name = 'dsh-tool-greet'
export const inject = ['tools']        // 不写它，ctx.tools 就是 undefined，插件直接报错

/** @param {import('@deepseek-ai/cordis').Context} ctx */
export function apply(ctx) {
  ctx.tools.register(defineTool({
    name: 'greet',
    description: 'Greet someone by name. Use this when ...',
    parameters: {
      name: { type: 'string', required: true, description: 'The name to greet.' }
    },
    output: {
      schema: { type: 'string' },
      render: (_args, value) => [{ type: 'text', text: value }]
    },
    async execute(args) {
      return `Hello, ${args.name}!`
    }
  }))
}

// ⚠️ 绝对不要写 export default —— 会被 Loader 当成「服务类」解析，
//    进而丢弃函数插件的命名空间。这是函数式插件的头号杀手。
```

**这里有一个最容易写错的地方**，两条路径的规则**相反**：

| 路径 | `required` 写在哪 | 值 |
|---|---|---|
| `defineTool`（DSH 自有 DSL） | **属性级** | 字面量 `true` |
| 裸 `ctx.tools.register`（标准 JSON Schema） | **对象级** | 字符串数组 `['name']` |

套错就静默失效，不报错。

> **冒烟通过 =** 在**真实会话**里让模型调用它，拿到预期结果。「装上了」不等于「生效了」。

---

### Level 3 · 加命令、加配置 —— 让它可调参

**斜杠命令**（T5）：

```js
export const inject = ['commands']

export function apply(ctx) {
  ctx.commands.register({
    name: 'hello',
    description: 'Say hello',
    async run(args) { return `Hello, ${args || 'world'}!` }
  })
}
```

**用户可调配置**（T6）：导出 `Config`，改配置后行为变化、非法值被明确拒绝。

**同时加多个能力面只有两条规则**：`inject` 取**并集**；需要清理的副作用包进 `ctx.effect()` 并返回 disposer。

---

### Level 4 · 服务、界面、拦截、定时、HTTP —— 进入深水区

| 你要做的 | 形态 | 注册点 | 冒烟通过 = |
|---|---|---|---|
| 给别的插件提供能力 | **服务插件** | `export default class extends Service`，构造函数首行 `super(ctx, '服务名')` | 另一个插件能 `inject` 并调用成功 |
| 网页界面上加东西 | 函数式 + 浏览器半侧 | `ctx.slots.inject(key, () => ctx.slots.register(opts, 组件))` | 界面出现你的东西，控制台无 `slot entry crashed` |
| 设置界面里加卡片 | 同上 | 设置命名空间 + `settings.*` 插槽 | 卡片可见、改动生效 |
| 拦消息 / 改请求 / 加提示词 | 函数式插件 | `agent/pre-step`、`agent/request`（waterfall） | 跑一次会话，行为确实被改 |
| 暴露 HTTP 接口 | 函数式插件 | `ctx.webServer.register({kind, path, handler})` | `curl` 真打一次，看到 200 |
| 定时 / 周期任务 | 函数式插件 | `ctx.interval(cb, delay)`（**不是** `ctx.setInterval`） | 等过一个周期，任务真的跑了 |

> **服务插件是唯一允许（且必须）写 `export default` 的形态**——它和函数式插件是两种东西，别混。
> 完整签名、客户端产物契约、反面教材见 `references/14-inbound-http-and-timers.md`；界面细节见 `references/04-ui-and-slots.md`。

**到了这一级，请务必通读 `references/05-pitfalls.md` 的 23 条坑**——它们全部来自官方事故复盘或社区真实提交，每条都对应一次真实的失败。

---

### 难度阶梯速查

```
低  ├─ T1/T2  零代码组合包          不写 JS，只描述组装
    ├─ T5     斜杠命令              一个 register 调用
中  ├─ T3/T4  工具插件              defineTool + 参数 Schema
    ├─ T6     可配置插件            export const Config
    ├─ T7     服务插件              extends Service
高  ├─ T8/T9  UI 与设置卡片         双半侧 + 三个登记点
    ├─ T10    Agent 流程拦截        waterfall 事件
    └─ T11/T12 外部集成 / 完整工程  全套工程约定 + 门禁
```

---

## 4. 它里面装了什么

| 位置 | 内容 | 什么时候读 |
|---|---|---|
| `SKILL.md` | 入口层（≤500 行）：版本闸门、形态选型、路由表、10 步工作流、冒烟判定、合同不变量 5 条、八条红线、自检清单 | 每次开发，**整体加载** |
| `references/` | **17 篇**专题：`00` 版本闸门 · `api-claims` 事实分级 · `01` 心智模型 · `02` 12 个模板 · `03` API 手册 · `04` UI 与插槽 · `05` 23 条坑 · `06` 工作流 · `07` 工程约定 · `08` 速查表 · `09` 结对提示词 · `10` 社区案例库 · `11` 术语与来源 · `12` 社区插件 · `13` 版本史 · `14` HTTP 与定时器 · `15` 边界与维护 | **按需读取**，不要一次全读 |
| `scripts/` | **8 个**确定性工具：防过时探针（py/sh 双版本）· 第二批断言核验器 · 插槽权威抽取 · 引用一致性守门 · 上游同步 · 版本差异 · 历史矩阵 | 见 [第 5 节](#5-为什么它不承诺不过时) |
| `assets/` | **8 件**可直接复制：零代码组合包骨架 · 最小工具插件骨架 · 决策留痕模板 | 动手时直接抄 |

**大文件用检索、不要整读**（单文件最大 6.6k 行）：

```bash
grep -rn "ctx.slots.inject" references/ | head -30      # 某 API 名出现在哪
grep -n -A 40 "^### 坑 P7" references/05-pitfalls.md    # 某个坑的全文（按编号）
```

---

## 5. 为什么它不承诺「不过时」

DSH 处于 pre-stable / rc 阶段，**tag 间隔中位数约 1.1 天**，并且出现过破坏性变更。任何写死 DSH API 的文档**都会**腐化——这是结构性的，不是谁疏忽。

所以本技能不承诺「不过时」，只承诺一件事：**过时会响。**

| 机制 | 作用 |
|---|---|
| **第 0 步 · 版本闸门（强制）** | 写任何 DSH 代码前先答三问 + 跑探针；拿不到源码时按降级规则显式声明「本条未核验」 |
| **事实分级 S / M / V** | 一句话判断法：*这条事实明天变了，我的代码会崩吗？* 会崩 → 必须核验；不会崩 → 可直接用 |
| `dsh-api-probe.py` | 对**实时源码**重验 **48 条断言**（43 正向 + 5 反向） |
| `verify_absorbed_claims.py` | 第二批 **27 条**（入站 HTTP / 定时器 / 客户端产物 / 插槽 / **防编造的否定断言**） |
| `extract_slots.py` | 从源码抽取**权威插槽清单**并与技能声明双向 diff——写插槽名前用它，不要凭表抄 |
| `check_refs.py` | 证明技能里引用的每个路径都能在技能内解析，且没有指向作者机器的绝对路径 |

> **一个不能失败的校验器，比没有校验器更危险。**
> 本项目在开发期查出了 **4 次「假通过」**——什么都没核验，却报告「全部成立」。因此：探针有退出码 `3`（断言表为空）；否定断言必须带**护栏模式**（必须同时命中一个必然存在的样本）；每个核验器都自带 `--selftest`，必须先证明它**能失败**，它的「通过」才可信。
> 方法论常驻于 `references/00-version-gate.md` §9 与 `references/api-claims.md` §6。

---

## 6. 出问题了去哪儿查

| 症状 | 先去哪 |
|---|---|
| 插件装上了但**完全没反应** | `references/06-workflow.md` ④：`--dump-config` 查组合树 + PENDING 审计 |
| 报错信息看不懂 | `references/05-pitfalls.md` 的「报错信息 / 现象对照表」 |
| 已知症状检索 | `references/05-pitfalls.md`（23 条坑，编号 P1~P22b） |
| 改了代码不生效 | `SKILL.md` 的「改完代码怎么生效」表——**只改 `src/`，永远不要手改 `lib/`** |
| 界面崩了 / slot 报错 | `references/04-ui-and-slots.md` |
| 想追到原始社区提交与行号级出处 | `references/10-community-casebook.md` |

> **「我明明装了啊」的五大成因**，全部落在 `SKILL.md` 的**合同不变量 5 条**上：缺 `dsh.bundle.patch`、`type`/`main`/`exports` 不全、UI 半侧声明不成对、名称三处不一致（`package.json#name` = patch 的 `id` = 客户端 `ModuleLoader.id`）、误把 `react` 打进 bundle。
> 打包前对照这 5 条逐项打勾，能省掉大部分返工。

---

## 7. 与 AI Agent 结对开发

这个技能本来就是为「Agent 替人写插件」设计的。

- 直接给 Agent 的提示词模板：`references/09-agent-pairing.md`（**10 个**可直接复制的模板）
- **要求 Agent 每次附出处（文件 + 行号），无出处不予采纳。** 这条比提示词本身更重要——它会挡掉绝大部分凭空编造的 API
- 交付后按 `references/07-conventions.md` 的门禁清单验收

---

## 8. 常见问题

**Q：这是 DSH 插件吗？我 `dsh plugin add` 装它为什么没反应？**
不是。它是**开发期技能**，装在你的 AI 客户端 skills 目录，不是 DSH profile。你用它**产出**的那个 `dsh.bundle` 才是 DSH 插件。

**Q：我能只用它的一部分吗（比如只要模板）？**
可以。`assets/` 下的两个骨架是独立的、可直接复制的工程；`references/02-templates.md` 的 12 个模板也可以单独抄。但**模板是脚手架不是权威**——抄之前先跑一次探针确认它依赖的 API 还在。

**Q：没有 DSH 源码，能用吗？**
能，但要走**降级规则**：显式声明「以下 API 未对当前版本核验」，S 级骨架照给，M/V 级符号单列成「需你确认」。**技能从不编造 API 名去填补空白。**

**Q：目标版本比技能基线新怎么办？**
不要猜。`scripts/dsh-sync.sh` 拉源码（需确认，首次约 200 MB，**绝不执行 pnpm install**）→ 跑探针 → `scripts/dsh-version-diff.sh` 出「基线 → 最新」差异，看六个破坏性变更高频维度。

**Q：为什么文档里有些数字（17 篇 / 23 条 / 48 条）看起来像在自我强调？**
因为这些数字是**可复现的**：项目规矩是写「全部 / 仅 / 只有 N 个」必须附抽取命令与范围。历史上这条规矩已经拦下过 3 次措辞与事实不符。

---

## 9. 基线、已知边界与许可

### 事实基线

| 项 | 值 |
|---|---|
| DSH 基线 | tag `dsh-v0.1.5-rc.2` / commit `c291e7961a` / 2026-09-10 |
| 上游仓库 | [deepseek-ai/deepseek-harness](https://github.com/deepseek-ai/deepseek-harness) |
| 技能版本 | 见 `SKILL.md` frontmatter 的 `version`（**唯一落点**） |
| 版本 ↔ 基线对照 | `references/13-version-history.md` §1.5 |

> 技能版本号**不表示**「对应哪个 DSH 版本」，只表示「本技能自己改到了什么级别」。两条独立的轴，绑定处就是上面那张对照表。

### 已知边界（诚实声明）

- 探针只覆盖它断言的 48 条事实，**不覆盖 `V` 级实现细节**。探针全绿 ≠ 你的插件能跑。
- 文档里引用的**行号会漂移**，请按符号名核验，不要按行号。
- 版本史只登记「会让已有代码 / 配置失效」的变更，它**不是 changelog**。
- `references/10-community-casebook.md` 与 `12-community-plugins.md` 引用了社区仓库代码片段，**授权混杂**（含 AGPL-3.0 与 NOASSERTION），复用前请自行复核。
- 本技能**不提供**「托管静态文件」与「发布 DSH skill」两类能力面，属有意保留的空白，理由见 `references/15-skill-scope-and-maintenance.md`。

### 许可

**MIT-0** —— 见 [LICENSE](LICENSE)。

第三方衍生内容的授权提示见 LICENSE 文件末尾。

---
name: dsh-plugin-development
description: A development-time skill for building plugins on DSH (DeepSeek Harness) / Cordis — it is not itself an installable DSH plugin, but the tooling that guides a developer or AI agent through creating, debugging, packaging, and publishing one. This skill should be used whenever the user asks to develop a DSH plugin, write or modify a cordis plugin, add a tool / slash command / config schema / service / UI slot to DSH, fix a plugin that fails to load or stays in PENDING, or package a plugin bundle for installation or distribution. It covers the full difficulty ladder — zero-code bundles, patch syntax, defineTool tools, commands, configurable plugins, services, React UI plugins, settings cards, and agent-flow interception — plus 23 catalogued pitfalls, official engineering conventions, and copy-ready prompts for AI-agent pair development. Because DSH is pre-stable and changes frequently, it also ships a per-tag version history of upstream breaking changes, a probe script that verifies the skill's own API claims (including negative claims such as "there is no CHANGELOG") against the live source checkout, a sync script that pulls the upstream source into the skill directory after developer confirmation so the history can be refreshed, and a mandatory version gate that must be answered before writing any DSH code.
license: MIT-0
agent_created: true
---

# DSH 插件开发

> **定位：这是一个「用来开发 DSH 插件的技能」，它本身不是能装进 DSH 的插件。**
> 它服务于在 DSH（DeepSeek Harness，基于 Cordis 的「一切皆插件」宿主）上做二次开发的开发者与 AI Agent——帮你选形态、写代码、排错、打包、发布。它自己**不会被 `dsh plugin add` 安装**，也不进入任何 DSH profile。
> 别混淆：**本技能产出的那个 `dsh.bundle` 包（你写出来的插件），才是能装进 DSH 的东西。**

把「DSH 插件」从选型做到发布。本技能是《DSH 插件开发指导手册》与《实战补充：模板库·踩坑百科》的整合入口：**本文件只放流程与路由，细节全部在 `references/`**，按需读取，不要一次全读。

## 何时使用

- 用户要求开发 / 修改 / 调试 / 打包 / 发布 DSH（DeepSeek Harness）插件
- 出现这些词：DSH 插件、cordis 插件、`cordis.patch.yml`、`dsh.bundle`、`defineTool`、`ctx.slots`、`ctx.tools.register`、PENDING
- 用户要求审查现有 DSH 插件代码、判断该用哪种插件形态
- 用户问「为什么我的插件装上了但没反应」

**不适用**：你要的是「装进 DSH 就能直接用的现成插件」。本技能不提供任何运行时能力、也不负责插件分发——找现成插件请去社区插件市场（见 `references/12-community-plugins.md`）。

## 第 0 步（强制，不可跳过）· 版本闸门

**本 skill 的 references 是某一时刻的快照，会腐化。** DSH 处于 rc 阶段（基线 `v0.1.5-rc.2` / commit `c291e7961a`，2026-09-10），tag 间隔中位数约 1.1 天、出现过破坏性变更。

**所以不要承诺「不过时」，要保证「过时会响」。** 写任何 DSH 代码前，先过这道闸门。

**① 权威顺序（源码永远压过本 skill）**

```
1. 当前 DSH 源码                    ← 唯一权威
2. 探针脚本对当前源码的核验结果      ← 可执行的证据
3. 本 skill 的 references（快照）    ← 脚手架，不是权威
4. 模型记忆 / 常识                   ← 禁止作为唯一依据
```

**② 三问**：① 我在对哪个版本写代码？（拿不到就**先要版本**，不知道版本不得断言 API）② 我要用的 API 属于 S/M/V 哪一级？③ 我能核验吗？（不能 → 走降级规则，**没有第三条路**）

**③ 跑探针**（两个版本，**优先用 Python 版**）

```bash
python <skill>/scripts/dsh-api-probe.py <DSH 仓库路径>    # ← 推荐：零 coreutils 依赖，Windows 最稳
bash   <skill>/scripts/dsh-api-probe.sh <DSH 仓库路径>    # 备选：仅当 shell 有完整 coreutils 时
# 0 = 断言全部成立（43 条正向 + 5 条反向）
# 1 = 有 STALE —— 模板可能过时，或某条否定结论已被推翻。**不要照抄**
# 2 = 仓库路径不对（防止对着错目录跑出假结论）
# 3 = 断言表为空 —— 未核验任何事实，结果无效（缺 coreutils 的典型症状）
```

> ⚠️ **bash 版在本机不可用**：`C:\Program Files\Git\bin\bash.exe` 缺 `cat`/`grep`/`head`/`find`，
> bash 版会因缺 `grep` 报出**几十条假 STALE**。本机请一律用 Python 版。
> 另：环境缺 `dirname` 时 WorkBuddy 自带的 `bash` 完全不可用。

> **S/M/V 怎么分**：问「这条事实明天变了，我的代码会崩吗？」——**会崩 → M/V，必须核验**；不会崩 → S，可直接用。
> **降级规则**（拿不到源码时）：允许继续，但必须 ① 显式声明「以下 API 未对当前版本核验」；② S 级骨架照给，M/V 级符号单独列成「需你确认」清单；③ 禁止把未核验事实写成肯定句。**绝不编造 API 名填补空白。**
> **目标版本高于基线时**：不要去猜。`dsh-sync.sh` 拉源码（先经你确认）→ `dsh-api-probe.sh` 核验 → `dsh-version-diff.sh` 出「基线 → 最新」差异。
> **手上已有任意一份 DSH 仓库时**，直接指给探针即可，无需联网。

📖 完整机制（腐化推导、易变性三级全表、五种核验手段、降级四条、探针维护流程、拉取纪律、网络不可达时的三条降级路径）**见 `references/00-version-gate.md`**。本节只保留「不做就会出错」的部分。

## 另外三条基础纪律

1. **引用任何字段名、事件名、服务名、插槽名前，先查 `references/08-cheatsheet.md` 或 `references/api-claims.md`。** 查不到就 grep 源码，**不要凭印象写**。
2. **代码跑通前不要声称完成。** 「装上了」不等于「生效了」——必须看到实际输出或界面变化。
3. 每条结论尽量附出处（文件路径 + 行号）。用户明确要求「无出处不采纳」。

## 第一步：选形态（选错形态 = 后面全部返工）

写入代码前先做一次判定，三种形态互斥且写法不同：

| 形态 | 何时选 | 必须这样写 | 禁止 |
|---|---|---|---|
| **函数式插件** | 绝大多数情况：加工具 / 加命令 / 加事件监听 | 具名导出 `name` / `inject` / `Config` / `apply` | **绝对不能有 `export default`**（有 default 会被当成服务类解析而失败） |
| **服务插件** | 你要给**别的插件**提供能力，让别人 `inject` 你 | `export default class extends Service`，构造函数首行 `super(ctx, '服务名')` | 写成普通函数导出 |
| **组合包 bundle** | 只是把已有插件装到一起，纯配置 | 只需 `package.json` + `cordis.patch.yml`，`package.json` 里声明 `"dsh": {"bundle": {"patch": "./cordis.patch.yml"}}` | 不要写 JS / TS，不要有 `src/` |

> **UI 插件是函数式插件的特例**，不是第四种形态——它只是多了一个「浏览器半侧」和若干登记点。

判定流程与完整心智模型见 `references/01-mental-model.md`。

## 第二步：按难度阶梯选模板

**不要从最难的开始。** 先做能跑通的最小闭环，再逐级加复杂度：

| 阶梯 | 模板 | 难度 |
|---|---|---|
| 1. 零代码组合包（两个配置文件、0 行 JS） | T1 / T2 | 低 |
| 2. 斜杠命令（给人用的 `/命令`） | T5 | 低 |
| 3. 工具插件（让模型调用你的能力，`defineTool`） | T3 / T4 | 中 |
| 4. 可配置插件（用户不改代码就能调参） | T6 | 中 |
| 5. 服务插件（给别的插件提供能力） | T7 | 中高 |
| 6. UI 插件与设置卡片（React） | T8 / T9 | 高 |
| 7. Agent 流程拦截（`waterfall` 事件） | T10 | 高 |
| 8. 外部集成 / 完整工程骨架 | T11 / T12 | 高 |

12 个模板的完整代码、官方 7 类模板的逐字源码、**40 个官方 UI 插槽名全清单**，全部在 `references/02-templates.md`——该文件已把「12 个实战模板」与「官方逐字源码附录」合并到一处，不必再找第二个文件。

## 标准工作流

按顺序执行，每一步都能独立验证。**不要跳步**。

| # | 阶段 | 做什么 | 读哪个文件 |
|---|---|---|---|
| **0** | **版本闸门** | **强制**：答三问 + 跑探针。不可跳过 | `00-version-gate.md` |
| 1 | 选型 | 判定三种形态之一 + 选模板 | `01-mental-model.md` → `02-templates.md` |
| 2 | 环境 | 版本对照、`DSH_HOME` 位置、从源码跑起来 | `06-workflow.md` ① |
| 3 | 最小闭环 | 先做一个能加载、能看到的空插件 | `02-templates.md`（T1 或 T3） |
| 4 | 写功能 | 按 API 写工具 / 命令 / 配置 / 服务 | `03-api-cookbook.md` |
| 5 | UI（如需） | 两个半侧 + **三个登记点** + 插槽 | `04-ui-and-slots.md` |
| 6 | 调试 | `--dump-config` 查组合树；PENDING 审计查注入失败；HMR 免重启 | `06-workflow.md` ④ |
| 7 | 打包 | 组合包结构、`package.json`、patch 引用、分发方式对比 | `06-workflow.md` ③ |
| 8 | 安装验证 | `dsh plugin --profile <名字> add <包>`（`--profile` 必填） | `06-workflow.md` ② |
| 9 | 工程化 | 命名、README 强制节、测试、门禁、提交规范 | `07-conventions.md` |

## 写代码前必读的八条红线

以下每条都来自官方事故复盘或社区真实提交，**违反任何一条都会被用户打回**：

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

## 出问题时的排查顺序

1. 插件装上了但**完全没反应** → 读 `06-workflow.md` 第 ④ 部分（`--dump-config` + PENDING 审计）
2. 报错信息看不懂 → 查 `05-pitfalls.md` 里的「报错信息 / 现象对照表」
3. 已知症状检索 → `05-pitfalls.md`（23 条坑，按症状编号 P1~P22b）
4. 需要追根究底（原始社区提交、行号级出处）→ `10-community-casebook.md`

## 与 AI Agent 结对开发

用户常让 Agent 代写插件代码。此时：

- 给 Agent 的提示词模板见 `09-agent-pairing.md`（两套来源共 10 个模板，可直接复制改用）。
- 要求 Agent **每次附出处**（文件 + 行号），无出处不予采纳。
- Agent 交付后按 `07-conventions.md` 的门禁清单验收。

## 参考文件路由表

`references/` 按**主题**组织（不是按来源手册拆），共 15 个文件。每个 reference 的文件头都标了「合成来源」，写明它由哪几份素材合成——**不必在多个同名文件之间猜该读哪个**。

| 文件 | 何时读 |
|---|---|
| `references/00-version-gate.md` | **写任何 DSH 代码前**；探针报 STALE 后；讨论「会不会过时」时 |
| `references/api-claims.md` | 想知道「这条事实属于 S/M/V/N 哪一级、该怎么核验」时 |
| `references/01-mental-model.md` | 开始任何插件前；搞不清形态 / profile / 组合包加载机制 / 该选哪个模板时 |
| `references/02-templates.md` | 要抄代码时。含 12 个模板（T1~T12）+ 官方 7 类模板逐字源码 + 40 个 UI 插槽名全清单 + 社区零代码组合包全文 |
| `references/03-api-cookbook.md` | 写工具 / 配置 / 命令 / 事件 / 服务 / 终端功能时 |
| `references/04-ui-and-slots.md` | 做 UI 插件或设置卡片时 |
| `references/05-pitfalls.md` | **写代码前通读；出问题时检索**。含 23 条坑 + 症状速查表 + 报错对照表 + 官方 4 篇事故复盘全文与八红线 |
| `references/06-workflow.md` | 环境准备 / 安装与 CLI 机制 / 打包分发 / 调试排错——四部分顺序阅读 |
| `references/07-conventions.md` | 想做得像官方包一样规范时（官方约定 + 命名/测试/门禁 + 版本兼容军规） |
| `references/08-cheatsheet.md` | **随手查**：三形态对照表 + 服务名/事件名/插槽名/命令/CLI/路径/参数 DSL 全表 + 骨架与范本清单 |
| `references/09-agent-pairing.md` | 与 Agent 结对开发（10 个可直接复制的提示词模板 + 十条红线） |
| `references/10-community-casebook.md` | 追根究底：原始社区素材、行号级出处（6.6k 行，**最后再读**，用 grep 检索而非整读） |
| `references/11-glossary-and-provenance.md` | 查术语、来源、**已知边界与官方文档矛盾** |
| `references/12-community-plugins.md` | 选型参考、找可借鉴的社区高星插件 |
| `references/13-version-history.md` | **目标版本高于基线时必读**；查 tag 版本史、破坏性变更、更新流程 |

## 大文件检索（避免整文件读入）

`references/` 单文件最大 6.6k 行，**优先用检索而不是整读**：

```bash
grep -rn "ctx.slots.inject" references/ | head -30        # 某 API 名出现在哪
grep -n -A 40 "^### 坑 P7" references/05-pitfalls.md      # 某个坑的全文（按编号）
grep -n -A 120 "^## T3 " references/02-templates.md       # 某个模板
grep -n -B 3 -A 10 "duplicate" references/05-pitfalls.md  # 报错反查成因
```

## 内置工具

`assets/` 下有最小可运行骨架，复制后改名字即可：

- `assets/minimal-bundle/` —— 零代码组合包（T1 形态，0 行 JS）
- `assets/minimal-tool-plugin/` —— 最小工具插件（T3 形态，`defineTool` + 参数 Schema）

`scripts/` 下有五个确定性工具（用法与退出码见脚本头部注释）：

| 脚本 | 作用 | 关键点 |
|---|---|---|
| `dsh-api-probe.py <仓库路径>` | **防过时探针（首选）**：核验 43 条正向 + 5 条反向断言 | 退出码 0/1/2/3；纯标准库、零外部命令依赖，Windows 最稳 |
| `dsh-api-probe.sh <仓库路径>` | 同上的 bash 版（断言表须与 .py 版同步） | 依赖 coreutils；**本机缺 `grep` 会报假 STALE，勿用** |
| `dsh-sync.sh` | **把 DSH 源码拉进 skill 目录**（`vendor/dsh-src/`） | 首次约 200 MB，**必须先经开发者确认**；之后增量更新。**绝不执行 pnpm install** |
| `dsh-version-diff.sh <仓库路径>` | **出「基线 → 最新」差异**，六个维度 + 作者自报的 `!:` 提交 | 需要本地是 git 仓库；输出可直接追加到 `13-version-history.md` 第 2 节 |
| `dsh-tag-matrix.sh <仓库路径> [out.tsv]` | **历史矩阵复核**：对全部 tag 逐条核验 API 面，输出 TSV | 只在质疑「API 名是否稳定」这类**历史结论**时用；需要完整 tag 历史 |

## 已知边界（诚实声明，不要复述给用户当结论）

- **探针必须能失败**，且**改探针后必须跑一次负向验证**。两处已修的假通过：bash 版空断言表报「全部成立」（现为 exit 3）、Python 版把文件当目录导致假 STALE。方法与脚本示例见 `00-version-gate.md` 第 9 节。
- 探针只覆盖它断言过的 48 条事实，**不覆盖 V 级细节**；探针通过 ≠ 插件能跑通。
- references 里带行号的引用，**行号一定会漂移**；核验只能按符号名 grep。
- 官方文档存在**两处内部矛盾**，本 skill 已选定立场，见 `11-glossary-and-provenance.md`。
- 部分 UI 插槽清单是从源码提取的（官方文档未列），可信但需以源码为准。
- **版本史是快照，不是流水账。** `13-version-history.md` 只列「会让现有代码/配置失效」的变更，每个区间还有几十到上百条新功能与内部重构**不在其中**。要全量请用第 6 节的命令自行生成。
- **DSH 没有 CHANGELOG，也不用 `BREAKING CHANGE:` 页脚**，但它**会用 `type(scope)!:` 标题标记**自报破坏性提交。所以准确说法是：「查变更日志」不成立，`--grep='!:'` 有效但覆盖不全，「`!:` + 源码级对比」并用才成立。

## 维护本 skill（防止它变形）

skill 的价值在于**分层**：SKILL.md 只放「每次都要知道」的（流程 / 选型 / 红线 / 路由），其余一律下沉 `references/`。
加内容前自问三句：**每次开发都要看吗？**（否则下沉）· **是可核验的事实吗？**（是 → 登记 `api-claims.md` + 加进探针断言表）· **是否定结论（「没有 X」）吗？**（是 → **必须**同时加一条 N 级反向断言，否则它坏了没人知道）

**硬预算：本文件 ≤ 230 行**，`build_dsh_skill.sh` 会门禁检查。超限说明有内容放错层了——找出来下沉，**不要放宽预算**。

> ⚠️ 踩过的坑：用正则做「搜不到 → 所以不存在」的判断前，**必须先用已知存在的样本验证正则本身**。本 skill 曾因正则漏写 `scope` 得出「DSH 不用 `!` 标记」的错误结论，并据此删掉了原本正确的内容。**命中不了 → 结论无效，不是事实为空。**

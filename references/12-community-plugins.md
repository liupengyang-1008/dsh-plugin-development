> **文件来源**：本文件由 DSH 插件开发手册套件整合生成。直接编辑会在下次整合时被覆盖，因此维护性改动记录在工作区源文档中。

> **本文件用途**：社区中被广泛使用的高星 DSH 插件清单，用于选型参考与'抄作业'对象筛选。
> **合成来源**：DSH社区高星插件清单.md
> **快照警告**：本文件是 DSH 插件知识的**冻结快照**（基线 `v0.1.5-rc.2` / commit `c291e7961a`，2026-09-10），其中的**接口名级事实可能已过时**。
> **写代码前先核验**：`bash scripts/dsh-api-probe.sh <DSH 仓库路径>`（退出码 1 = 有 STALE，**不要直接照抄**）。
> **分级与核验规则**：`references/00-version-gate.md`、逐条登记 `references/api-claims.md`。
> **素材名约定**：正文里出现的 `Xxx-yyy.md`（如 `E-official-templates.md`、`B-tools-external.md`）是**生成时的源调研笔记名**，其内容在生成时已合并进本文件——**不是 skill 内的文件**，不必去别处找。

---

<!-- ↓ 源：DSH社区高星插件清单.md 区间 1-300 -->

# DSH 社区高星插件清单（≥5000 ⭐ 实证版）

> 调研时间：2026-09-11 12:45 CST
> 数据源：GitHub Search API + `awesome-dsh-plugin` 官方精选清单 + 逐仓库 manifest 实测
> 目标：筛出可作**开发模板**的高星插件，并剔除"看着像但不是插件"的仓库

---

## 0. 结论先行（三条硬事实）

| # | 结论 | 置信度 |
|---|---|---|
| 1 | DSH 生态**确实繁荣**：官方精选清单收录 **3,408 个**插件（`awesome-dsh-plugin.com/count.json` 实时计数），分 23 个类目 | **A 级**（官方 badge 接口） |
| 2 | 但 **star ≥ 5000 的真插件只有 11 个**。高星区间被两类"非插件"占据：**harness 本体**、**蹭 topic 的大型无关项目** | **A 级**（逐个拉 `package.json` 验证 `dsh.bundle` 清单） |
| 3 | **真正"原生 DSH 插件"的主力在 1,000–4,000 ⭐ 区间**（约 46 个）。若目标是学插件写法，这一档比 ≥5000 档更有参考价值 | **B 级**（同上，抽样验证） |

**一句话**：你问"star 超过 5000 的插件"——答案是**有，但只有 11 个，且其中大部分是"把已有大产品接进 DSH"的重量级集成**，不是典型的插件写法范本。原生插件写法的最佳范本在 3000–4000 星档。

---

## 1. 判定方法（可复现，非主观印象）

生态**没有官方插件市场**（我此前已实证），发现机制是 GitHub topic `dsh-plugin`。而官方精选清单明确写了收录门槛：

> "A plugin is listed because it follows the official protocol — **it declares a `dsh.bundle` manifest and installs with `dsh plugin add`**"

所以我用了**四步硬筛**，每步都可复现：

| 步骤 | 动作 | 目的 |
|---|---|---|
| ① | GitHub Search：`topic:dsh-plugin stars:>5000` | 拿到 **27 个**高星候选 |
| ② | 拉取候选的 `awesome-dsh-plugin` 精选条目 | 交叉验证是否在册 |
| ③ | 拉取每个候选的**完整文件树**（`git/trees?recursive=1`），定位所有 `package.json` | 解决"插件藏在子目录"问题 |
| ④ | 逐个读取 `package.json`，检查是否存在 **`dsh.bundle`** 字段 | **决定性判据**：只有声明了才能被 `dsh plugin add` 安装 |

> ⚠️ **第③步是关键**。很多高星仓库的插件不在根目录，而在子目录里。例如 `Tencent/WeKnora` 的插件在 `packages/dsh-weknora/`，`archify` 的在 `integrations/deepseek-harness/`。只看根 `package.json` 会全部误判为"不是插件"——我第一次探测就踩了这个坑。

---

## 2. 清单 A：≥5000 ⭐ 且**已实证 `dsh.bundle`** 的真插件（11 个）

按 star 降序，全部经 `package.json → dsh.bundle` 字段实测确认：

| # | 仓库 | ⭐ | 语言 | 插件包名 | 插件路径 | 类型 | 授权 |
|---|---|---|---|---|---|---|---|
| 1 | [nexu-io/open-design](https://github.com/nexu-io/open-design) | **95,472** | TS | `@open-design/dsh-runtime` | `packages/dsh-runtime` | Web/设计集成 | Apache-2.0 |
| 2 | [tt-a1i/archify](https://github.com/tt-a1i/archify) | **57,636** | JS | `@tt-a1i/archify-dsh` | `integrations/deepseek-harness` | 工具+图表渲染 | MIT |
| 3 | [reactive-resume/app](https://github.com/reactive-resume/app) | **42,448** | TS | `dsh-plugin-reactive-resume` | `packages/dsh-plugin` | Web UI | MIT |
| 4 | [volcengine/OpenViking](https://github.com/volcengine/OpenViking) | **36,559** | Python | `@openviking/dsh-memory-plugin` | `examples/dsh-memory-plugin` | 记忆服务 | AGPL-3.0 |
| 5 | [anywhere-labs/dsh-desktop](https://github.com/anywhere-labs/dsh-desktop) | **25,403** | TS | `dsh-plugin-desktop` | `dsh-plugin-desktop` | 桌面宿主 | MIT |
| 6 | [Tencent/WeKnora](https://github.com/Tencent/WeKnora) | **22,166** | Go | `@wxg-prc-cpg/dsh-weknora` | `packages/dsh-weknora` | 工具插件 | 见仓库 |
| 7 | [MemTensor/MemOS](https://github.com/MemTensor/MemOS) | **11,277** | TS | `@memtensor/memos-local-plugin` | `apps/memos-local-plugin` | 记忆 | Apache-2.0 |
| 8 | [zhu1090093659/dsh-web](https://github.com/zhu1090093659/dsh-web) | **7,358** | TS | **10+ 个原生 UI 插件** | `packages/*` | UI 插件集 | Apache-2.0 |
| 9 | [yjh051108/dsh-routing-suite](https://github.com/yjh051108/dsh-routing-suite) | **7,162** | JS | `@dsh-external/dsh-super-injector` | 根目录 + `injector/` | 运行时注入 | MIT |
| 10 | [Q00/ouroboros](https://github.com/Q00/ouroboros) | **5,805** | Python | `dsh-ouroboros` | `integrations/dsh-plugin` | **纯配置 Bundle** | MIT |
| 11 | [huangruiteng/loopx](https://github.com/huangruiteng/loopx) | **5,785** | Python | `dsh-loopx-plugin` | `packages/dsh-loopx-plugin` | 状态内核 | Apache-2.0 |

### 各插件的官方描述（摘自精选清单原文）

- **open-design** — 本地优先的桌面设计应用，把编码 Agent 变成设计引擎（原型 / landing page / dashboard / 幻灯片）
- **archify** — 从代码库或系统描述生成经验证的、自包含交互式架构图 / 时序图 / 数据流图
- **OpenViking** — `pre-step 自动召回 + profile 注入`、会话捕获、`viking://` URI 守卫、recall/write 记忆工具
- **dsh-desktop** — "万物皆插件，桌面本身也是插件"，轻量桌面端
- **WeKnora** — ⭐ **4 个只读工具**挂在 WeKnora 知识库上：列知识库 / 混合检索 / 按序重组文档分块 / 带引用的 RAG 或 ReAct 回答
- **dsh-web** — 任务看板、Git 图谱、侧栏、远程移动 UI、宠物、实时 token 统计、皮肤中心（**同一 monorepo 内 10+ 个独立插件**）
- **dsh-routing-suite** — 先装运行时注入器，再装任务感知的推理模式路由预设
- **ouroboros** — ⭐ **纯配置 Bundle**，通过 DSH 的 MCP 客户端挂载，暴露 36 个访谈/执行/评估/演化工具
- **loopx** — 长周期 Agent 的 provider 中立本地优先状态内核，维护 Goal/Todo/gate/evidence/quota/recovery/handoff 状态

---

## 3. 清单 B：**高星但经实证"不是 DSH 插件"**（避免你踩坑）

这 16 个仓库带着 `dsh-plugin` topic、star 都很高，但**文件树里不存在任何 `dsh.bundle` 清单**，无法用 `dsh plugin add` 安装：

| 仓库 | ⭐ | 实测结果 | 它其实是什么 |
|---|---|---|---|
| deepseek-ai/deepseek-harness | 219,477 | 无 `dsh.bundle`（它是**宿主本体**） | harness 本身 |
| ruvnet/ruflo | 72,014 | 根 pkg 无 `dsh` 字段 | 独立的 agent meta-harness |
| freestylefly/awesome-gpt-image-2 | 31,016 | 无 `dsh.bundle` | 提示词案例库 |
| Molunerfinn/PicGo | 27,169 | 无 `dsh.bundle` | 图床工具（蹭 topic 曝光） |
| nocobase/nocobase | 24,150 | 无 `dsh.bundle` | 低代码平台（蹭 topic 曝光） |
| titanwings/distilly | 24,607 | 仓库无 `package.json` | Skill 蒸馏工具 |
| Nagi-ovo/voyager | 20,030 | 无 `dsh.bundle` | 浏览器扩展 |
| awesome-dsh-plugin/awesome-dsh-plugin | 15,239 | 它是**清单本身** | 精选列表（B 端入口） |
| walkinglabs/learn-harness-engineering | 15,069 | 无 `dsh.bundle` | 教学项目 |
| EverMind-AI/EverOS | 12,870 | 无 `dsh.bundle` | 记忆层产品 |
| YaoApp/yao | 7,923 | 仓库无 `package.json` | Agent 工作台 |
| plastic-labs/honcho | 7,110 | 有 `harness-plugin-core/` 但无 `dsh.bundle` | 记忆库（未按 DSH 协议打包） |
| anbeime/skill | 6,516 | 无 `dsh.bundle` | Skill 商店聚合 |
| ZSeven-W/openpencil | 5,900 | 无 `dsh.bundle` | 矢量设计工具 |
| esengine/DeepSeek-Reasonix | 35,493 | 无包清单 | 独立终端 coding agent |
| Devin-AXIS/iPolloWork | 5,752 | 无 `dsh.bundle` | 桌面应用 |

> ⚠️ `awesome-dsh-plugin`（15,239⭐）虽不是插件，但**是本次调研最有价值的入口**——3,408 个插件全在这份清单里，且每条都验证过协议合规。

---

## 4. 清单 C：1,000–4,000 ⭐ 区间 —— **原生插件主力**（学习价值更高）

这一档才是"典型 DSH 插件"的真实形态：单一仓库 = 一个插件，代码面可控，直接可抄。

| 仓库 | ⭐ | 插件包名 | 类型 | 为什么值得学 |
|---|---|---|---|---|
| [crafter-station/petdex](https://github.com/crafter-station/petdex) | 4,076 | — | 动画/UI | 跨多个 agent 复用的 UI 插件 |
| [liustack/modlens](https://github.com/liustack/modlens) | 3,941 | `@liustack/modlens` | **视觉/多模态** | 有 `dsh.client`，声明 `platform: web` + `immediately` |
| [xiaobright/dsh-anchored-standard](https://github.com/xiaobright/dsh-anchored-standard) | 3,818 | — | **Preset/组合** | 两阶段 preset 写法（bootstrap → 全量工具） |
| [dsh-market/dsh-market](https://github.com/dsh-market/dsh-market) | 3,625 | `dshmarket` | **插件市场** | 官方清单推荐的市场；装法 `dsh plugin --profile web add dshmarket` |
| [omdsh-dev/DSH-better-sidebar](https://github.com/omdsh-dev/DSH-better-sidebar) | 3,507 | `dsh-better-sidebar` | **UI 扩展底座** | ⭐ 开放的侧边栏底座，第三方可注册新页面 |
| [ccch1mneyyy/dsh-TUI](https://github.com/ccch1mneyyy/dsh-TUI) | 2,951 | `@deepseek-harness-tui/dsh-tui` | **终端 TUI** | 官方公众号收录的 TUI 补位插件 |
| [dsh-tauri-desk/deepseek-harness-desktop](https://github.com/dsh-tauri-desk/deepseek-harness-desktop) | 1,907 | — | 桌面 | Tauri 桌面版，5MB 安装包 |

---

## 5. 学习模板推荐矩阵（对应《DSH 插件开发指导手册》章节）

按"想学什么"选范本，不要只看 star：

| 想学 | 首选范本 | 对应手册章节 | 理由 |
|---|---|---|---|
| **工具插件（最基础）** | ⭐ **Tencent/WeKnora → `packages/dsh-weknora`** | 第 4 章 `defineTool` | 4 个只读工具，职责单一，无 UI 复杂度，**最干净的入门范本** |
| **纯配置、不写代码** | ⭐ **Q00/ouroboros → `integrations/dsh-plugin`** | 第 5 章 Config | config-only bundle，只需写 `cordis.patch.yml`，验证"插件≠必须写代码" |
| **UI 插件 / slots** | ⭐ **zhu1090093659/dsh-web → `packages/*`** | 第 9、10 章 | 一个仓库塞 10+ 个原生 UI 插件，风格统一，可横向对比 |
| **第三方扩展点设计** | ⭐ **omdsh-dev/DSH-better-sidebar** | 第 9 章 slots | 侧边栏底座，演示"如何给别人留插槽" |
| **设置页里的市场** | **dsh-market/dsh-market** | 第 10 章设置卡片 | 官方清单推荐，含客户端半侧 + 服务端半侧完整样例 |
| **把已有产品接成插件** | **nexu-io/open-design**（95k） | 第 11 章打包 | 重量级集成，看大项目如何切出插件边界 |
| **本地服务接入（Memory）** | **volcengine/OpenViking** | 第 4、7 章 | `pre-step` 钩子 + 记忆工具 + URI 守卫，看服务型插件全貌 |
| **多插件 monorepo 组织** | **zhu1090093659/dsh-web** | 第 14 章工程规范 | 同仓管理 10+ 插件，看 workspace / 命名 / 发布流水线 |

---

## 6. 安装命令（清单实测）

官方清单里反复出现的安装形态：

```sh
# 通用形态（--profile 是必填，省略会报错）
dsh plugin --profile web add <npm包名>

# 实例（清单原文）
dsh plugin --profile web add dshmarket
dsh plugin --profile web add dsh-find-plugin
```

> ⚠️ 各插件的**确切 npm 包名**以各自 README 为准——上表里的"插件包名"是仓库内 `package.json` 的 `name` 字段，不一定等于发布到 npm 后的名字。

---

## 7. 数据与复现

本次调研的原始数据与脚本都落在**生成期工作区**内（**不随本 skill 发布**）：

```
<工作区>\
├── scripts\
│   ├── parse_dsh_plugins.py     # 解析 GitHub 搜索结果
│   ├── filter_dsh_eco.py        # 按生态 topic 过滤
│   ├── parse_awesome.py         # 解析 3,431 条精选清单
│   ├── crossref.py              # 交叉验证精选清单
│   ├── probe_manifest.py        # 根目录 manifest 探测
│   ├── probe_tree.py            # ⭐ 文件树级 manifest 精确定位
│   ├── extract_desc.py          # 提取官方描述
│   └── dump_table.py            # 导出元数据表
└── scripts\data\
    ├── awesome-dsh-plugin-README.md   # 官方清单原文（980KB / 3,621 行）
    ├── awesome_entries.json           # 解析后 3,431 条
    ├── tree_probe.json                # 文件树探测结果
    └── manifest_probe.json            # manifest 探测结果
```

原始检索命令：`https://api.github.com/search/repositories?q=topic:dsh-plugin+stars:>5000&sort=stars&order=desc`

---

## 8. 风险与边界提示

| # | 提示 |
|---|---|
| ⚠️ 1 | **star 数不等于插件质量**。≥5000 档里 16/27 是蹭 topic 的无关仓库；反过来说，生态里被广泛使用的插件（如 `dsh-find-plugin`、各类主题包）star 只有几百 |
| ⚠️ 2 | **生态极年轻**。清单里创建的插件绝大多数是 2026-08 之后建的（不到一个月）。star 数还在快速变动，本清单会很快过时 |
| ⚠️ 3 | **授权混杂**。OpenViking 是 **AGPL-3.0**（传染性），WeKnora 授权为 `NOASSERTION`。想抄代码进自己项目前**务必核对 license** |
| ⚠️ 4 | **topic 会被滥用**。任何仓库都能自己加 `dsh-plugin` topic。判据永远是**看它有没有 `dsh.bundle`**，不是看 topic |
| ⚠️ 5 | 本清单基线为 **2026-09-11**，DSH 版本 `0.1.5-rc.2`（commit `c291e7961a`）。项目处于 pre-stable，插件 API 可能破坏性变更 |

---


# DSH Plugin Development · `dsh-plugin-development`

> **This is a development-time skill for building DSH plugins — it is not itself an installable DSH plugin.**
> It is not installed by `dsh plugin add` and it does not enter any DSH profile. **The `dsh.bundle` package it helps you produce is what actually gets installed.**

[中文](README.md) · **English**

An engineering skillset for developers and AI agents building plugins on **DSH (DeepSeek Harness)** — the Cordis-based host whose design principle is "everything is a plugin". It covers the whole path: **choose a plugin form → write code → debug → package → publish**, with copy-ready templates, executable verification scripts, and a version gate whose job is to make staleness *loud*.

[SkillHub](https://skillhub.cn/skills/dsh-plugin-development) · [GitHub](https://github.com/liupengyang-1008/dsh-plugin-development) · License MIT-0

---

## Contents

- [0. The 30-second version](#0-the-30-second-version)
- [1. Installation](#1-installation)
- [2. First use: zero learning curve](#2-first-use-zero-learning-curve)
- [3. Four levels, easy to hard](#3-four-levels-easy-to-hard)
- [4. What is inside](#4-what-is-inside)
- [5. Why it does not promise to stay current](#5-why-it-does-not-promise-to-stay-current)
- [6. When something breaks](#6-when-something-breaks)
- [7. Pairing with an AI agent](#7-pairing-with-an-ai-agent)
- [8. FAQ](#8-faq)
- [9. Baseline, known limits, license](#9-baseline-known-limits-license)

---

## 0. The 30-second version

| Question | Answer |
|---|---|
| **What is it** | A DSH plugin development handbook written for AI agents, plus a bundle of executable verification tools |
| **Who is it for** | People who have DSH installed and want to write plugins for it; and the AI agents writing those plugins on their behalf |
| **How do I use it** | **You talk to it** — there is no CLI to drive. Once loaded, it steers the agent through the whole development flow |
| **Where it goes** | Into your **AI client's** skills directory. It follows the open **Agent Skills** format and is **not tied to any one client** — Claude Code / Codex / Cursor / Gemini CLI / Copilot / OpenClaw / WorkBuddy and more |
| **What you get** | 12 copy-ready templates · 23 catalogued pitfalls · 8 verification scripts · 1 anti-staleness version gate · 10 agent prompt templates |
| **What you do not get** | ❌ A ready-made installable plugin (that is what it helps you *build*) ❌ A DSH runtime dependency |
| **What your environment needs** | ① An AI client that can load `SKILL.md` ② A shell (`python3` or `bash`) ③ Optional: a DSH checkout, used to verify APIs — without it the skill falls back to its explicit degradation rule |

### Does it apply to your task?

> "**Write / modify / fix / package a DSH plugin for me**" → applies.
> "**Give me a ready-made plugin I can drop into DSH**" → does **not** apply; go to the community plugin market instead (see `references/12-community-plugins.md`).

---

## 1. Installation

### 1.1 One portable skill, tied to no single client

This skill uses the open **Agent Skills** format: a directory containing `SKILL.md` (required) plus `references/`, `scripts/` and `assets/`. The format was originally developed by Anthropic, released as an open standard, and is now implemented by a large number of AI clients.

**The only test that matters:**

> If your agent can load a `SKILL.md`, it can use this skill.

It depends on **no client-specific capability** — only on two things: the agent can read files, and it can run shell commands. Confirmed to work with (non-exhaustive):

**Claude Code** · **OpenAI Codex** · **Cursor** · **Gemini CLI** · **GitHub Copilot** · **Windsurf** · **OpenCode** · **Kiro** · **OpenClaw** · **WorkBuddy** · and any other client implementing the standard.

> ⚠️ **Do not confuse the two layers**: this skill installs into **your AI client**; the `dsh.bundle` package it helps you produce is what installs into **DSH**. **DSH is its target platform, not its host.**

### 1.2 Install (pick one of three)

#### Option A · The client's own skill-install command (least effort)

| Client | Command |
|---|---|
| **OpenClaw · from Git (recommended, gets the newest)** | `openclaw skills install git:liupengyang-1008/dsh-plugin-development@main` |
| **OpenClaw · from a local directory** | `openclaw skills install ./dsh-plugin-development --as dsh-plugin-development` |
| **OpenClaw · from ClawHub** | `openclaw skills install @liupengyang-1008/dsh-plugin-development` |
| **OpenClaw · update** | `openclaw skills update --all` (workspace) / `--all --global` |
| **skillhub.cn** | `skillhub install dsh-plugin-development --namespace user_9d594bab` |
| **Claude Code / Codex / others** | These currently rely on placing the directory in a skills path — use Option B |

> OpenClaw installs into the **current workspace's** `skills/` by default; add `--global` to install into `~/.openclaw/skills/`, visible to all local agents.
> **Version note**: ClawHub / SkillHub releases may lag GitHub. **`version` in the skill's `SKILL.md` is authoritative**; for the newest build, install from Git via Option B.

#### Option B · Place it from the Git repo (most portable — works with any client)

```bash
git clone https://github.com/liupengyang-1008/dsh-plugin-development.git
```

Then move the whole directory into a skills path your client scans. Default paths for reference:

| Client | User scope (all projects) | Project scope (current project only) |
|---|---|---|
| **WorkBuddy** | `~/.workbuddy/skills/` | — |
| **Claude Code** | `~/.claude/skills/` | `.claude/skills/` |
| **OpenAI Codex** | `~/.agents/skills/` (some versions: `~/.codex/skills/`) | `.agents/skills/` (or `.codex/skills/`) |
| **OpenClaw** | `~/.openclaw/skills/` | `<workspace>/skills/` |
| **Cursor** | `~/.cursor/skills/` | `.cursor/skills/` |
| **Gemini CLI** | `~/.gemini/skills/` | `.gemini/skills/` |
| **GitHub Copilot** | `~/.copilot/skills/` | `.github/skills/` |
| **Windsurf** | `~/.codeium/windsurf/skills/` | `.windsurf/skills/` |
| **OpenCode** | `~/.config/opencode/skills/` | `.opencode/skills/` |
| **Kiro** | `~/.kiro/skills/` | `.kiro/skills/` |

On Windows, replace `~` with `C:\Users\<your-user>\`.

> 🔎 **Not sure about the path? Do not guess — ask your agent:**
> "Where is your skills directory?"
> That is the most reliable method: paths move between versions, and the agent knows where it loads skills from.

> ⚠️ **Keep the directory named `dsh-plugin-development`.** The Agent Skills spec requires the frontmatter `name` to match the parent directory name (this skill uses `dsh-plugin-development` for both). **Renaming the directory makes the skill fail to load.**

#### Option C · Unpack the release archive

Unzip `dsh-plugin-development.zip` into any of the paths above, yielding `<skills dir>/dsh-plugin-development/`.

### 1.3 Sharing one copy across clients? Symlink, do not duplicate

Duplicated copies drift apart. **Keep one canonical copy and symlink it into each client:**

```bash
# canonical copy
git clone https://github.com/liupengyang-1008/dsh-plugin-development.git ~/skills-src/dsh-plugin-development

# link it into every client you use
ln -s ~/skills-src/dsh-plugin-development ~/.claude/skills/dsh-plugin-development
ln -s ~/skills-src/dsh-plugin-development ~/.agents/skills/dsh-plugin-development
ln -s ~/skills-src/dsh-plugin-development ~/.openclaw/skills/dsh-plugin-development
```

Updating is then a single command:

```bash
git -C ~/skills-src/dsh-plugin-development pull
```

> Some clients apply path-containment checks to symlinked skills (the resolved realpath of `SKILL.md` must stay inside the skill directory). This skill is a **plain directory tree** that never steps outside itself, so it is unaffected.
> OpenClaw explicitly supports both `git:` installs and symlinked skill folders.

### 1.4 Verifying the install

The directory should look like this (`SKILL.md` plus three resource folders):

```
SKILL.md          ← entry layer: gate / form selection / workflow / red lines / acceptance
references/       ← 17 topic documents, read on demand
scripts/          ← 8 deterministic verification tools
assets/           ← engineering skeletons you can copy and rename
```

**Structural self-check** (needs no client):

```bash
python scripts/check_refs.py .        # reference integrity: expect exit 0
```

**Functional check**: ask your AI a DSH plugin question (e.g. "which plugin form should this use?"). If the reply mentions the **"Step 0 · version gate"**, a template ID (`T1`–`T12`), or a "smoke criterion", the skill loaded successfully.

> Skill loading is **progressive**: at startup the agent reads only the `name` + `description` from `SKILL.md` (~100 tokens), loads the body only when the task matches, and reads `references/` or `scripts/` only when a step actually needs them. Installing many skills therefore does not blow up the context window.

---

## 2. First use: zero learning curve

**The best way to use this skill is not to read the docs — just talk to it in plain language.**

> "Write me a DSH plugin that adds a `/hello` command, and lets the model call a capability that returns the current time."

The agent will walk: **choose form → route to a template → build the smallest working loop → set up a smoke point → verify → package**. You never need to know the words "T3" or `defineTool` — the skill ships a router table that maps *what the user says* → template → form → registration point → smoke criterion.

It will do one thing first, and **skipping it is not allowed**:

```bash
# Step 0 · version gate: re-verify the facts this skill records against YOUR DSH version
python scripts/dsh-api-probe.py <PATH_TO_DSH_CHECKOUT>
# 0 = all assertions hold (43 positive + 5 negative = 48)
# 1 = something is STALE — do not copy the templates blindly
# 2 = that path is not a DSH checkout (guards against conclusions from the wrong directory)
# 3 = assertion table is empty — nothing was verified, the result is not valid
```

**Why it must run first**: DSH is at release-candidate stage, with a median tag interval of about 1.1 days and a history of breaking changes. This skill's documents are a snapshot of one moment. **Upstream source always outranks them.**

---

## 3. Four levels, easy to hard

Do not start with the hardest one. **Get the smallest working loop running first, then add complexity one level at a time.**

### Level 1 · Zero-code bundle — not a single line of JavaScript

**Use when** you are only assembling existing capabilities: "mount this MCP server into DSH", "change how an existing plugin behaves".

All behaviour is described by `cordis.patch.yml`. No `src/`, no JS entry. Skeleton: `assets/minimal-bundle/`.

Of the three files, one line in `package.json` is the single biggest beginner trap:

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
      "patch": "./cordis.patch.yml"   // ← without this, `dsh plugin add` prints one warning and does nothing
    }
  }
}
```

The patch file's top level is a **single array**, and every line needs a globally unique `id`:

```yaml
- insert:
    - id: mcp-my-capability
      name: '@deepseek-ai/dsh-mcp-client'
      config:
        serverName: my-capability
        transport: stdio
        command: npx
        args: [-y, my-mcp-server]
        # The child process env is scrubbed: anything matching *KEY|PASSWORD|SECRET|TOKEN*
        # and every DSH_* variable is removed. Credentials must be listed explicitly here.
        MY_API_KEY: !!js process.env.MY_API_KEY ?? ''
```

**Install and verify** (`--profile` is required, not optional):

```bash
dsh plugin --profile <profile> add ./minimal-bundle     # install
dsh plugin --profile <profile> ls                       # confirm it is registered
dsh --dump-config                                       # inspect the composed tree without starting
```

> **Smoke passes when** your line shows up in `--dump-config` *and* changing the config actually changes behaviour.

---

### Level 2 · Add a tool — the canonical function plugin

**Use when** you want the model to be able to call something. Skeleton: `assets/minimal-tool-plugin/` (plain JS, zero build, installable as-is).

```js
import { defineTool } from '@deepseek-ai/dsh-tools'

export const name = 'dsh-tool-greet'
export const inject = ['tools']        // without it ctx.tools is undefined and the plugin throws

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

// ⚠️ NEVER write `export default` — the loader parses it as a *service class*
//    and silently discards the function plugin's namespace. This is the #1 killer.
```

**The most commonly mis-written detail** — two paths, opposite rules:

| Path | Where `required` goes | Value |
|---|---|---|
| `defineTool` (DSH's own DSL) | **property level** | literal `true` |
| bare `ctx.tools.register` (standard JSON Schema) | **object level** | string array `['name']` |

Mix them up and it fails silently, with no error.

> **Smoke passes when** a real session makes the model call it and return the expected result. "It installed" is not "it works".

---

### Level 3 · Commands and config — make it tunable

**Slash command** (T5):

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

**User-adjustable config** (T6): export `Config`; behaviour changes when config changes, and invalid values are rejected explicitly.

**Combining several capability faces takes only two rules**: take the **union** of `inject`; wrap anything that needs cleanup in `ctx.effect()` and return a disposer.

---

### Level 4 · Services, UI, interception, timers, HTTP — the deep end

| What you want | Form | Registration point | Smoke passes when |
|---|---|---|---|
| Provide capability to *other* plugins | **service plugin** | `export default class extends Service`, first line of the constructor `super(ctx, 'name')` | another plugin can `inject` it and call successfully |
| Add something to the web UI | function plugin + browser half | `ctx.slots.inject(key, () => ctx.slots.register(opts, Component))` | it appears in the UI, console shows no `slot entry crashed` |
| Add a settings card | same | settings namespace + `settings.*` slots | the card is visible and edits take effect |
| Intercept messages / requests / prompts | function plugin | `agent/pre-step`, `agent/request` (waterfall) | run a session and the behaviour actually changes |
| Expose an HTTP route | function plugin | `ctx.webServer.register({kind, path, handler})` | `curl` it for real and get a 200 |
| Periodic task | function plugin | `ctx.interval(cb, delay)` (**not** `ctx.setInterval`) | wait one period and the task really ran |

> **The service plugin is the only form that may — and must — use `export default`.** It is a different animal from the function plugin; do not mix them.
> Full signatures, the client artifact contract and an anti-pattern list are in `references/14-inbound-http-and-timers.md`; UI details in `references/04-ui-and-slots.md`.

**At this level, read all 23 pitfalls in `references/05-pitfalls.md`.** Every one of them comes from an official postmortem or a real community submission, and each maps to an actual failure.

---

### Difficulty ladder at a glance

```
low   ├─ T1/T2   zero-code bundle          no JS, pure description of the assembly
      ├─ T5      slash command             one register call
mid   ├─ T3/T4   tool plugin               defineTool + parameter schema
      ├─ T6      configurable plugin       export const Config
      ├─ T7      service plugin            extends Service
high  ├─ T8/T9   UI and settings cards     two halves + three registration points
      ├─ T10     agent-flow interception   waterfall events
      └─ T11/T12 external integration / full project skeleton with gates
```

---

### ⚠️ Before you copy a template: three security constraints

The templates are **copy-ready skeletons**. The examples that mount an external MCP server or an external process **download and execute an external package when DSH starts** — the only place in this skill with real security weight. Three rules when you copy them:

| # | Constraint | Why |
|---|---|---|
| 1 | **Pin an exact version** (`pkg@1.2.3`) — never `pkg`, `latest`, `^1`, `~1.x` | A floating spec means "whatever is on the registry right now runs on every start". **The code can change after you reviewed it** — a compromised upstream, a malicious new release, or a name-squatting package lands directly on your machine |
| 2 | **Forward only the one credential the integration needs, and use a low-quota, revocable key** | The downloaded child process runs with the **same privileges as DSH**: it can read and write files, make network requests, and read **every** credential listed in `env:` |
| 3 | **Split "download" from "execute" into two steps** | Install explicitly and review the resolved dependency tree first, then point the patch at a local executable — so what actually runs is determinate before it runs |

> These three come from a real security audit of this skill (ClawHub scanners). **Nothing else in the skill carries this risk**: it contains no runtime logic of its own, reads no credentials, and transmits no data.

---

## 4. What is inside

| Location | Contents | When to read |
|---|---|---|
| `SKILL.md` | Entry layer (≤500 lines): version gate, form selection, router table, 10-step workflow, smoke criteria, 5 contract invariants, 8 red lines, pre-delivery checklist | Every session — **loaded whole** |
| `references/` | **17** topic documents: `00` version gate · `api-claims` fact grading · `01` mental model · `02` 12 templates · `03` API cookbook · `04` UI & slots · `05` 23 pitfalls · `06` workflow · `07` conventions · `08` cheatsheet · `09` agent pairing · `10` community casebook · `11` glossary & provenance · `12` community plugins · `13` version history · `14` HTTP & timers · `15` scope & maintenance | **On demand** — do not read them all at once |
| `scripts/` | **8** deterministic tools: anti-staleness probe (python + bash) · second assertion set · authoritative slot extraction · reference-integrity guard · upstream sync · version diff · historical matrix | See [section 5](#5-why-it-does-not-promise-to-stay-current) |
| `assets/` | **8** copy-ready files: zero-code bundle skeleton · minimal tool plugin skeleton · decision-log template | Copy them directly when you start building |

**Search large files, do not read them whole** (the largest is 6.6k lines):

```bash
grep -rn "ctx.slots.inject" references/ | head -30      # where does an API name appear
grep -n -A 40 "^### 坑 P7" references/05-pitfalls.md    # full text of one pitfall, by ID
```

---

## 5. Why it does not promise to stay current

DSH is pre-stable / rc, with a **median tag interval of about 1.1 days**, and it has shipped breaking changes. Any document that hardcodes DSH APIs **will** rot — that is structural, not negligence.

So this skill does not promise to stay current. It promises one thing: **staleness will be loud.**

| Mechanism | What it does |
|---|---|
| **Step 0 · version gate (mandatory)** | Answer three questions and run the probe before writing any DSH code; with no source available, declare explicitly which facts are unverified |
| **Fact grading S / M / V** | One-line test: *if this fact changed tomorrow, would my code break?* Yes → verify it. No → use it as-is |
| `dsh-api-probe.py` | Re-verifies **48 assertions** (43 positive + 5 negative) against a **live** source checkout |
| `verify_absorbed_claims.py` | A second set of **27** (inbound HTTP, timers, client artifact format, slots, plus **negative assertions that keep fabricated API names out**) |
| `extract_slots.py` | Extracts the **authoritative slot list** from source and diffs it against the skill's claims — use it before writing any slot name, never copy from a table |
| `check_refs.py` | Proves every path cited in the skill resolves inside the skill, with no absolute paths pointing at the author's machine |

> **A checker that cannot fail is more dangerous than no checker.**
> This project found **4 separate "silent false passes"** during development — cases where nothing was verified but "all assertions hold" was reported. Hence: the probe has exit code `3` for an empty assertion table; negative assertions must carry a **guard pattern** (they must also hit a sample that certainly exists); and every verifier ships a `--selftest` so it must first prove it **can** fail before its "pass" means anything.
> The methodology lives in `references/00-version-gate.md` §9 and `references/api-claims.md` §6.

---

## 6. When something breaks

| Symptom | Go here |
|---|---|
| Plugin installed but **does nothing at all** | `references/06-workflow.md` ④ — `--dump-config` for the composed tree plus a PENDING audit |
| The error message makes no sense | the "error message / symptom lookup" table in `references/05-pitfalls.md` |
| Looking up a known symptom | `references/05-pitfalls.md` (23 pitfalls, IDs P1–P22b) |
| Code changes have no effect | the "how changes take effect" table in `SKILL.md` — **edit `src/` only, never hand-edit `lib/`** |
| UI crashed / slot errors | `references/04-ui-and-slots.md` |
| Want line-level provenance back to the original submission | `references/10-community-casebook.md` (index) → the `10a`~`10d` per-direction volumes |

> **"But I installed it!"** has five root causes, all captured by the **5 contract invariants** in `SKILL.md`: missing `dsh.bundle.patch`; incomplete `type`/`main`/`exports`; unpaired UI-half declarations; a name that is not identical in all three places (`package.json#name` = the patch's `id` = the client `ModuleLoader.id`); and shipping a second copy of `react` inside the bundle.
> Ticking those five off before packaging eliminates most rework.

---

## 7. Pairing with an AI agent

This skill was designed for the case where an agent writes the plugin for you.

- Prompt templates to hand straight to an agent: `references/09-agent-pairing.md` (**10** copy-ready templates)
- **Require the agent to cite a source (file + line) for every claim; accept nothing without one.** This rule matters more than the prompts themselves — it blocks the overwhelming majority of invented APIs
- On delivery, run the gate checklist in `references/07-conventions.md`

---

## 8. FAQ

**Q: Is this a DSH plugin? Why does `dsh plugin add` do nothing with it?**
It is not. It is a **development-time skill** that lives in your AI client's skills directory, not in a DSH profile. The `dsh.bundle` package it helps you produce is the DSH plugin.

**Q: Can I use just part of it (say, only the templates)?**
Yes. The two skeletons under `assets/` are standalone, copy-ready projects, and the 12 templates in `references/02-templates.md` can be used on their own. But **a template is a scaffold, not an authority** — run the probe before copying, to confirm the APIs it depends on still exist.

**Q: Can I use it without a DSH checkout?**
Yes, via the **degradation rule**: state explicitly that the following APIs are unverified; give the S-level skeleton as-is; and list M/V-level symbols separately as "confirm these yourself". **The skill never invents an API name to fill a gap.**

**Q: What if my target DSH version is newer than the skill's baseline?**
Do not guess. `scripts/dsh-sync.sh` pulls the source (needs confirmation, ~200 MB on first run, and it **never** runs `pnpm install`) → run the probe → `scripts/dsh-version-diff.sh` produces a "baseline → latest" report across the six dimensions where breaking changes cluster.

**Q: Why do the docs keep quoting numbers (17 / 23 / 48)?**
Because those numbers are **reproducible**. The project rule is that any statement of the form "all / only / exactly N" must come with the extraction command and scope. That rule has already caught 3 cases of prose contradicting fact.

---

## 9. Baseline, known limits, license

### Fact baseline

| Item | Value |
|---|---|
| DSH baseline | tag `dsh-v0.1.5-rc.2` / commit `c291e7961a` / 2026-09-10 |
| Upstream | [deepseek-ai/deepseek-harness](https://github.com/deepseek-ai/deepseek-harness) |
| Skill version | `version` in `SKILL.md` frontmatter (**the single source of truth**) |
| Version ↔ baseline table | `references/13-version-history.md` §1.5 |

> The skill version does **not** say "which DSH version this corresponds to" — only "how far we have changed this skill". Two independent axes; the table above is the only place they are bound together.

### Known limits (stated honestly)

- The probe only covers the 48 facts it asserts. **It does not cover `V`-level implementation details.** A green probe does not mean your plugin runs.
- Line numbers cited in `references/` **will drift**. Verify by symbol name, not by line.
- The version history lists only changes that break existing code or configuration. **It is not a changelog.**
- `references/10a-casebook-ui.md` through `10d-casebook-host-bundle.md`, plus `12-community-plugins.md`, quote community repositories under **mixed licenses** (including AGPL-3.0 and NOASSERTION). Review before reusing any code from them.
- The skill deliberately does **not** cover "hosting static files" or "publishing a DSH skill". Rationale in `references/15-skill-scope-and-maintenance.md`.

### License

**MIT-0** — see [LICENSE](LICENSE).

Third-party attribution notes are at the end of the LICENSE file.

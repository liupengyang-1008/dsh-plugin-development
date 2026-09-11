# DSH Plugin Development

> **This is a development-time skill for building DSH plugins — it is not itself an installable DSH plugin.**

A skill for developers and AI agents who build plugins on **DSH (DeepSeek Harness)**, the Cordis-based host whose design principle is "everything is a plugin". It walks you through choosing a plugin form, writing code that actually loads, debugging what will not activate, packaging, and publishing.

It is **not** a DSH runtime dependency. It does not install into any DSH profile. The `dsh.bundle` package that it helps you produce is what actually gets installed.

## What it covers

| Area | Contents |
|---|---|
| Plugin forms | Function plugin / service plugin / zero-code bundle — and why mixing them fails |
| Routing | A user-language → template → form → registration point → smoke-criterion router, so "add a tool" lands on T3 without reading the templates first |
| Templates | 12 practice templates (T1–T12) + verbatim official sources + a curated UI slot quick-reference |
| APIs | `defineTool`, parameter DSL, `ctx.tools.register`, commands, config schemas, services, events, slots |
| Inbound HTTP & timers | `ctx.webServer.register({kind, path, handler})`, `ctx.interval` / `ctx.timeout`, and the client bundle's lazy-CJS artifact contract (with a "looks plausible, verified wrong" anti-pattern list) |
| UI | React plugin halves, three registration points, settings cards |
| Agent flow | `waterfall` interception, `agent/pre-step`, `agent/request` |
| Verification | Smoke-first delivery discipline: one command / one real call / one visible marker, plus a per-capability pass table |
| Contracts | The five `package.json` / patch / client invariants behind most "installed but does nothing" failures |
| Pitfalls | 23 catalogued pitfalls + symptom index + error-message lookup table + 4 official postmortems |
| Engineering | Naming, README requirements, testing, gates, commit conventions |
| AI pairing | 10 copy-ready prompt templates for agent-assisted development |

## Anti-staleness design

DSH is at release-candidate stage and ships breaking changes on a short cadence (median tag interval ≈ 1.1 days). Any document that hardcodes DSH APIs **will** rot. This skill therefore does not promise to stay current — **it promises to make staleness loud**:

- **Mandatory version gate** — three questions plus a probe run, answered *before* any DSH code is written (`references/00-version-gate.md`).
- **Claims register** — every fact graded by volatility: `S` structural axiom / `M` interface name / `V` implementation detail / `N` negative claim (`references/api-claims.md`).
- **Probe** — `scripts/dsh-api-probe.py` re-verifies **48 assertions** (43 positive + 5 negative) against a live source checkout.

```bash
python scripts/dsh-api-probe.py <DSH_CHECKOUT>
# 0 = all assertions hold (43 positive + 5 negative)
# 1 = something is STALE — a template may be outdated, or a negative claim was overturned
# 2 = that path is not a DSH checkout (guards against false conclusions from the wrong directory)
# 3 = assertion table is empty — nothing was verified, the result is not valid
```

- **Second assertion set** — `scripts/verify_absorbed_claims.py` re-verifies 27 further facts (inbound HTTP, timers, client artifact format, slot registration, plus negative claims that keep fabricated API names out). It ships a `--selftest` that runs the same table against an empty corpus and requires **all 27 to go STALE**, because a table made of "X does not exist" assertions otherwise passes on nothing at all.
- **Reference integrity** — `scripts/check_refs.py` proves every path cited anywhere in the skill either resolves inside the skill or points at the DSH upstream checkout. Generation-time research material is cited by code ("material B, pit M1") rather than as a file path, so nothing points at files a user will never have.
- **Sync + diff** — `scripts/dsh-sync.sh` pulls upstream source into `vendor/dsh-src/` after explicit developer confirmation (≈200 MB on first run, never runs `pnpm install`); `scripts/dsh-version-diff.sh` produces a "baseline → latest" change report.

> **A probe that cannot fail is more dangerous than no probe.** Exit code `3` exists because an empty assertion table once reported "all assertions hold". The probe's own reliability rules, the two false-pass defects found and fixed, and the mandatory self-check are documented in `references/00-version-gate.md` §9 and `references/api-claims.md` §6.

## Installation

This skill follows the SkillHub / ClawHub package layout. Once published there, install it through your client. For local use, place the directory under your skills folder:

```
~/.workbuddy/skills/dsh-plugin-development/
```

## Repository layout

```
SKILL.md                    entry layer — routing, workflow, smoke criteria, contracts, red lines (≤ 500 lines)
skill-card.md               marketplace listing card (fixed 10-section format)
references/
  00-version-gate.md        mandatory step 0: anti-staleness protocol + probe self-reliability
  api-claims.md             claims register: every fact graded S/M/V/N with its verification method
  01-mental-model.md        plugin forms, profiles, bundle loading
  02-templates.md           12 templates + official source + 40 slot names
  03-api-cookbook.md        tools, config, commands, events, services, terminals
  04-ui-and-slots.md        UI plugins and settings cards
  05-pitfalls.md            23 pitfalls + symptom index + error table + official postmortems
  06-workflow.md            environment, CLI, packaging, debugging
  07-conventions.md         official engineering conventions and gates
  08-cheatsheet.md          quick-reference tables
  09-agent-pairing.md       AI-agent prompts for pair development
  10-community-casebook.md  raw community material with line-level provenance (6.6k lines — grep, don't read)
  11-glossary-and-provenance.md  glossary, sources, and known limits
  12-community-plugins.md   community high-star plugin survey
  13-version-history.md     per-tag upstream version history and breaking changes
  14-inbound-http-and-timers.md  curated: webServer routes, timers, client artifact format
  15-skill-scope-and-maintenance.md  curated: known limits + maintenance rules
scripts/
  dsh-api-probe.py          anti-staleness probe (preferred; stdlib only)
  dsh-api-probe.sh          same probe, bash version
  verify_absorbed_claims.py second assertion set (27 checks) + --selftest
  extract_slots.py          authoritative UI slot-key extraction and diff
  check_refs.py             resource-reference integrity (dangling / out-of-skill / local paths)
  dsh-sync.sh               pull upstream source into the skill directory
  dsh-version-diff.sh       baseline → latest change report
  dsh-tag-matrix.sh         cross-tag historical assertion matrix
assets/
  minimal-bundle/           smallest working zero-code bundle
  minimal-tool-plugin/      smallest working tool plugin
  plan-template.md          decision log template (copy into your plugin's docs/plan.md)
```

## Baselined against

- DSH `v0.1.5-rc.2` / commit `c291e7961a` (2026-09-10)
- Upstream: [deepseek-ai/deepseek-harness](https://github.com/deepseek-ai/deepseek-harness)

## Known limits

- The probe only covers the 48 facts it asserts. **It does not cover `V`-level details**, and a passing probe does not mean your plugin runs.
- Line numbers cited in `references/` will drift. Verify by symbol name, not by line.
- The version history lists only changes that break existing code or configuration. It is not a changelog.
- `references/10-community-casebook.md` and `12-community-plugins.md` quote community repositories under mixed licenses (OpenViking is AGPL-3.0; WeKnora is NOASSERTION). Review before reusing code from them.

## License

MIT-0 — see [LICENSE](LICENSE).

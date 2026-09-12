## Description: <br>
A development-time skill for building plugins on DSH (DeepSeek Harness), the Cordis-based host whose design principle is "everything is a plugin". It is not itself an installable DSH plugin — it is the tooling that guides a developer or AI agent through choosing a plugin form, writing code that loads, debugging what will not activate, packaging, and publishing. It covers zero-code bundles, `cordis.patch.yml` syntax, `defineTool` tools, slash commands, configuration schemas, service plugins, React UI plugins, settings cards, and agent-flow interception. It also routes a plain-language feature request to the right template, registration point and smoke criterion; enforces a smoke-first delivery discipline with per-stage gates; pins the five package / patch / client invariants behind most "installed but does nothing" failures; covers inbound HTTP route registration, timer tasks and the browser-half artifact format with source-verified signatures; and keeps a decision log in the plugin's own `docs/plan.md`. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[liupengyang-1008](https://github.com/liupengyang-1008) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
Plugin authors and AI-agent users use this skill to pick the right plugin form, scaffold a DSH plugin that actually loads, wire up tools / slash commands / configuration / services / UI slots, diagnose a plugin that installs but never activates, and package a bundle for installation or distribution. It additionally ships a user-language-to-template router, a per-capability smoke-verification table, the five packaging invariants to check before delivery, and a decision-log template so a build can be replayed and handed over. It is a development-time aid and a source of guidance only: it is not a DSH runtime dependency, it does not install into any DSH profile, and the bundles it helps you produce are what actually get installed. Because DSH is at release-candidate stage and ships breaking changes on a short cadence, the skill also refuses to go silently stale: it carries a per-tag ledger of upstream breaking changes, a probe script that re-verifies its own API and negative claims against a live source checkout, and a mandatory version gate that must be answered before any DSH code is written. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: The bundled probe, diff, and sync scripts execute shell code and read a local DSH source checkout; the sync script can download roughly 200 MB of upstream source from GitHub into the skill directory. <br>
Mitigation: Run the scripts only against a checkout you control, keep the sync step behind explicit developer confirmation, and treat fetched upstream source as read-only reference material. <br>
Risk: DSH is pre-stable and changes frequently, so the bundled templates, API tables, and version history are point-in-time snapshots that can yield outdated or non-loading plugin code when copied blindly. <br>
Mitigation: Answer the mandatory version gate first, run the probe against the target checkout, and stop to re-verify whenever the probe reports STALE instead of copying a snapshot through. <br>
Risk: Generated scaffolding and bundle installation write files and configuration into the user's DSH profile, changing runtime state. <br>
Mitigation: Review generated files and the `cordis.patch.yml` diff before installing, confirm activation in the real target profile rather than a scratch one, and remove the profile layer if the plugin fails to activate. <br>

## Reference(s): <br>
- [DSH upstream repository](https://github.com/deepseek-ai/deepseek-harness) <br>
- [Version gate and anti-staleness protocol](references/00-version-gate.md) <br>
- [API claims register (S/M/V/N levels)](references/api-claims.md) <br>
- [Mental model and plugin forms](references/01-mental-model.md) <br>
- [Template library (12 templates + official sources)](references/02-templates.md) <br>
- [API cookbook](references/03-api-cookbook.md) <br>
- [UI plugins and slots](references/04-ui-and-slots.md) <br>
- [Pitfall encyclopedia (23 pitfalls)](references/05-pitfalls.md) <br>
- [Workflow, packaging, and debugging](references/06-workflow.md) <br>
- [Engineering conventions](references/07-conventions.md) <br>
- [Cheatsheet and full API tables](references/08-cheatsheet.md) <br>
- [AI-agent pair development prompts](references/09-agent-pairing.md) <br>
- [Community casebook](references/10-community-casebook.md) <br>
- [Glossary, provenance, and known limits](references/11-glossary-and-provenance.md) <br>
- [Community plugin list by stars](references/12-community-plugins.md) <br>
- [Version history and breaking changes](references/13-version-history.md) <br>
- [Inbound HTTP routes, timers, and client artifact format](references/14-inbound-http-and-timers.md) <br>
- [Skill scope, known limits, and maintenance rules](references/15-skill-scope-and-maintenance.md) <br>

## Skill Output: <br>
**Output Type(s):** [Guidance, Code, Configuration, Shell commands, Markdown] <br>
**Output Format:** [Markdown guidance with inline TypeScript plugin sources, YAML `cordis.patch.yml` snippets, JSON manifests, and shell commands] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Produces copy-ready plugin scaffolds, `package.json` and patch manifests, probe and version-diff command output, and tabular change reports; generated files must be verified in a real DSH profile before being treated as working.] <br>

## Skill Version(s): <br>
1.0.6 (source: skill package) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>

#!/usr/bin/env python3
"""校验 skill 内部所有「指向文件」的引用都能在本 skill 内解析。

为什么需要它：skill 是**自包含**发布物（`references/` `assets/` `scripts/` 之外的路径
在用户机器上都不存在）。一旦正文里留下生成期的素材路径（如 `plugin-research/notes/…`）
或本机绝对路径，引用就会指向空气，且**不会报错**——属于本项目的典型「静默失效」。

分类规则（避免把 DSH 上游路径误判为悬空）：
  OK-内   `references/` `assets/` `scripts/` 下且文件真实存在
  OK-外   形如 `packages/…` `apps/…` `docs/…` `vendor/…` `src/…` `.agents/…`
          —— 这些是 **DSH 上游仓库**里的路径，本 skill 只做引用说明，属合法
  ❌ 素材  `plugin-research/…`、`notes/X.md`、裸 `A~J-*.md` —— 生成期调研素材，不在 skill 内
  ❌ 绝对  盘符开头的本机绝对路径（既悬空又泄漏本机路径）
  ❌ 悬空  以 `references/` `assets/` `scripts/` 开头但文件不存在

用法：python scripts/check_refs.py <skill目录> [日志路径]
退出码：0 = 无问题；1 = 存在问题；2 = 前置错误
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

SCAN_SUFFIXES = {".md", ".py", ".sh", ".json", ".yml", ".yaml"}
SKIP_DIRS = {"vendor", "__pycache__", ".git"}

# 以这些前缀开头的路径属于 DSH 上游仓库，不是本 skill 的文件
UPSTREAM_PREFIXES = (
    "packages/", "apps/", "docs/", "vendor/", "src/", ".agents/", "native/", "scripts/gen-",
)

TICKED = re.compile(r"`([^`\n]{2,160})`")
# 盘符绝对路径。两处收紧，都是为了排除「看着像路径、其实是模式/表格」的文本：
#   ① 负向后顾：排除 URL 里的 `s://`（来自 https:）
#   ② 正向前瞻：分隔符后必须紧跟**路径首字符**（字母/数字/_/./$/~/<）
#      —— 否则断言表里的字段分隔符 `g:\-\-dump-config` 会被误判成 G 盘路径
ABS_WIN = re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:[/\\](?=[A-Za-z0-9_.$~<{])[^\s`）)、，,]*")

# 正则/通配片段守卫：含这些元字符的「盘符形状」文本是模式而非路径（如 `d:\s*([^\s#]+`）
REGEX_META = ("*", "[", "]", "(", ")", "+", "?", "|", "^")

# 文档里用于举例的盘符路径：**通用的、与任何人的机器无关**的示例，
# 不视为「本机路径泄漏」。除此之外的任何盘符路径都会被判为 ❌本机。
# （刻意不写作者自己的工作区路径——那既会泄漏，对第三方用户也是错的判据。）
DOC_EXAMPLE_PATHS = (
    "C:\\Windows",
    "C:/Windows",
    "E:\\e\\foo",
    "E:/e/foo",
)
# 占位/示例路径（含尖括号占位符或省略号）——属正常的文档写法，不算缺陷
PLACEHOLDER = re.compile(r"[<{…]|\.\.\.")

# 本 skill 自己只发布 .py / .sh；`scripts/*.ts|*.mjs|*.js` 一律是 DSH 上游或社区仓库的脚本
OWN_SCRIPT_SUFFIX = (".py", ".sh")


def is_pathish(s: str) -> bool:
    if " " in s.strip() or "\n" in s:
        return False
    if s.startswith(("http://", "https://", "npm:", "github:", "dsh:", "git+")):
        return False
    if "/" not in s and "\\" not in s:
        return False
    return bool(re.search(r"\.(md|py|sh|json|yml|yaml|ts|tsx|mjs|js|txt|png)$", s))


def classify(ref: str, skill: Path) -> tuple[str, str]:
    rel = ref.lstrip("./").replace("\\", "/")
    # ① 占位/模板形态优先：含 <…> {…} … 的一律视为「示例」，不是可解析的路径。
    #    这一条必须排在最前——否则「不要写成 plugin-research/notes/<素材>.md」这类
    #    **规则示例文本**会被当成真实引用而自指误报。
    if PLACEHOLDER.search(ref):
        return "示例", "含占位符，属正常文档写法"
    if rel.startswith(UPSTREAM_PREFIXES):
        return "OK-外", ""
    if rel.startswith("plugin-research/") or rel.startswith("notes/"):
        return "❌素材", "生成期调研素材，不在 skill 内"
    if re.match(r"^[A-J]-[a-z][a-z-]*\.md$", rel):
        return "❌素材", "生成期调研笔记名，不在 skill 内"
    if re.match(r"^[A-Za-z]:[/\\]", ref):
        return "❌本机", "本机绝对路径（悬空 + 泄漏本机路径）"
    # scripts/*.ts|*.mjs|*.js 不是本 skill 的脚本（我们只发布 .py/.sh）
    if rel.startswith("scripts/") and not rel.endswith(OWN_SCRIPT_SUFFIX):
        return "OK-外", ""
    for root in ("references", "assets", "scripts"):
        if rel.startswith(root + "/"):
            return ("OK-内", "") if (skill / rel).exists() else ("❌悬空", f"{rel} 不存在")
    # 裸文件名：只在本 skill 内找同名文件
    if (skill / rel).exists():
        return "OK-内", ""
    return "忽略", ""


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: check_refs.py <skill_dir> [log]")
        return 2
    skill = Path(sys.argv[1]).resolve()
    if not (skill / "SKILL.md").exists():
        print(f"FATAL: {skill} 下没有 SKILL.md")
        return 2
    log = Path(sys.argv[2]) if len(sys.argv) > 2 else Path.cwd() / "_refs_report.txt"

    # 排除本脚本自身：它必须写下 `notes/X.md`、盘符路径等**模式字面量**作为判据，
    # 那是规则定义而不是资源引用（否则会自指误报）。
    me = Path(__file__).resolve()
    files = [
        p
        for p in skill.rglob("*")
        if p.is_file()
        and p.suffix in SCAN_SUFFIXES
        and not any(d in p.parts for d in SKIP_DIRS)
        and p.resolve() != me
    ]

    buckets: dict[str, list[tuple[str, int, str, str]]] = {}
    for p in sorted(files):
        rel_file = p.relative_to(skill).as_posix()
        for i, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            for ref in TICKED.findall(line):
                if not is_pathish(ref):
                    continue
                kind, why = classify(ref, skill)
                if kind == "忽略":
                    continue
                buckets.setdefault(kind, []).append((rel_file, i, ref, why))
            for ref in ABS_WIN.findall(line):
                if ref.lstrip("./").startswith(UPSTREAM_PREFIXES):
                    continue
                is_regex = any(m in ref for m in REGEX_META)
                is_example = (
                    is_regex
                    or PLACEHOLDER.search(ref)
                    or any(ref.startswith(p) for p in DOC_EXAMPLE_PATHS)
                )
                kind = "示例" if is_example else "❌本机"
                if is_example:
                    why = "正则片段或占位示例，非路径"
                else:
                    why = "本机绝对路径（悬空 + 泄漏本机路径）"
                buckets.setdefault(kind, []).append((rel_file, i, ref.rstrip("。；;,)'\""), why))

    out: list[str] = []
    out.append("=" * 78)
    out.append(f" skill 资源引用一致性校验   {skill}")
    out.append("=" * 78)
    out.append(f" 扫描文件数：{len(files)}（后缀 {', '.join(sorted(SCAN_SUFFIXES))}）")
    out.append("")

    total_bad = 0
    for kind in ("❌素材", "❌本机", "❌悬空", "示例", "OK-外", "OK-内"):
        rows = buckets.get(kind, [])
        if kind.startswith("❌"):
            total_bad += len(rows)
        out.append(f"─ {kind}  {len(rows)} 处 ─")
        if kind == "OK-内" and rows:
            out.append("  （数量多，只列前 12 条）")
            rows = rows[:12]
        for rel_file, i, ref, why in rows:
            mark = f"   ← {why}" if why and kind.startswith("❌") else ""
            out.append(f"    {rel_file}:{i}  {ref}{mark}")
        if not rows:
            out.append("    （无）")
        out.append("")

    # 缺失文件清单（去重，便于按清单处理）
    missing = sorted({ref for k in ("❌素材", "❌悬空", "❌本机") for _, _, ref, _ in buckets.get(k, [])})
    out.append("─ 缺失引用清单（去重）─")
    if missing:
        for ref in missing:
            out.append(f"    {ref}")
    else:
        out.append("    （无）")
    out.append("")
    out.append(f"结论：{'✅ 全部引用均可在 skill 内解析或指向 DSH 上游' if total_bad == 0 else f'❌ {total_bad} 处问题引用'}")

    log.write_text("\n".join(out) + "\n", encoding="utf-8")
    return 0 if total_bad == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

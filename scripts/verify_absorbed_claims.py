#!/usr/bin/env python3
"""核验「本轮从同类方案吸收进来的事实」是否对目标 DSH 源码真实成立。

背景：本项目规定「任何校验器都必须先证明它能失败」（见
references/00-version-gate.md §9、api-claims.md §6）。所以本脚本自带两种模式：

  正向：对真实 DSH 仓库跑断言表，期望全部 HOLDS。
  负向自检：对一个**故意造错的空仓库**跑同一张断言表，期望全部 STALE。
            —— 若负向自检里仍有 HOLDS，说明断言写得太松（假通过），脚本本身不可信。

用法：
  python scripts/verify_absorbed_claims.py <DSH仓库路径> [日志路径]
  python scripts/verify_absorbed_claims.py --selftest [日志路径]
"""

from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

# (id, 级别, 说明, 相对路径, 模式, 期望)  —— 期望 'has' = 必须命中；'not' = 必须不命中
CHECKS: list[tuple[str, str, str, str, str, str]] = [
    # ── 17.1 入站 HTTP 路由 ────────────────────────────────────────────────
    ("H01", "M", "webServer.register 接收单个 WebRoute 对象并返回 disposer",
     "docs/subsystems/web-server.zh.md", r"register\(route: WebRoute\): \(\) => void", "has"),
    ("H02", "S", "WebRoute 结构 = {kind, path, handler(req,res)}",
     "packages/host/webserver/src/index.ts", r"type WebRouteKind = 'exact' \| 'prefix'", "has"),
    ("H03", "S", "WebRoute.handler 拥有 ServerResponse（无 JSON 便捷层）",
     "packages/host/webserver/src/index.ts",
     r"handler: \(req: IncomingMessage, res: ServerResponse\) => void \| Promise<void>", "has"),
    ("H04", "M", "webServer 由 Web 组合的一行补丁提供（不是核心服务）",
     "packages/bundle/web-app/cordis.patch.yml",
     r"- id: webserver[\s\S]{0,80}@deepseek-ai/dsh-host-webserver", "has"),
    ("H05", "M", "回退席位只有一个所有者，第二次注册抛异常",
     "docs/subsystems/web-server.zh.md", r"席位只有一个所有者，第二次注册会抛出异常", "has"),

    # ── 17.2 定时器 ───────────────────────────────────────────────────────
    ("T01", "S", "ctx.interval(cb, delay) 返回 disposer（不是 Node Timeout）",
     "vendor/timer/README.md", r"`ctx\.interval\(callback, delay\)` \| Run repeatedly and return a disposer", "has"),
    ("T02", "S", "timer handle 绑在 fiber 上，插件卸载自动清",
     "vendor/timer/README.md", r"cleared\s+automatically when the plugin that created them is disposed", "has"),
    ("T03", "M", "ctx.setTimeout/setInterval 仅为 deprecated 别名",
     "vendor/timer/README.md", r"are kept as deprecated aliases", "has"),
    ("T04", "M", "timer 由 base 层插件行提供（缺失会 PENDING）",
     "packages/bundle/base/cordis.patch.yml",
     r"- id: timer[\s\S]{0,80}@deepseek-ai/cordis-plugin-timer", "has"),

    # ── 17.3 浏览器半侧产物格式 ───────────────────────────────────────────
    ("B01", "S", "客户端 bundle 是 lazy-CJS factory：banner 按 chunk 生成，非入口分块多带 chunk 字段",
     "packages/client/tsdown.client.ts",
     r"banner: \(chunk\) => \{[\s\S]{0,240}?window\.__ModuleLoader__\.load\(\{ id: \$\{JSON\.stringify\(id\)\}, \$\{chunk\.isEntry", "has"),
    ("B02", "S", "intro 建立 CJS 的 module/exports 外壳",
     "packages/client/tsdown.client.ts",
     r"intro: 'var module = \{ exports: \{\} \}; var exports = module\.exports;'", "has"),
    ("B03", "S", "footer 返回 module.exports 并收口",
     "packages/client/tsdown.client.ts", r"footer: 'return module\.exports; \} \}\);'", "has"),
    ("B04", "M", "class 产物路径固定为 lib/client.js",
     "packages/client/tsdown.client.ts", r"entryFileNames: 'client\.js'", "has"),
    ("B05", "M", "platform 模块种子表 = 9 个 specifier（react 四件套 + cordis + store + ui-slots + ui-primitives + ui-dockkit）",
     "packages/client/web/src/platform.ts",
     r"export const PLATFORM_MODULES = \[[\s\S]{0,400}?\] as const", "has"),
    ("B06", "M", "PRELOADED_CLIENT_EXTERNALS 当前为空数组",
     "packages/client/web/src/platform.ts",
     r"export const PRELOADED_CLIENT_EXTERNALS = \[\s*\] as const", "has"),
    ("B07", "M", "跨插件值导入被纯度门禁拒绝（只允许 type-only）",
     "packages/client/tsdown.client.ts", r"client bundle purity:", "has"),
    ("B08", "M", "官方明确：没有已发布的客户端预设，仓库外需自行复刻输出格式",
     "docs/cookbook/adding-a-settings-card.zh.md",
     r"没有已发布的预设暴露该包，因此本仓库之外的包得自行复刻同样的输出格式", "has"),
    ("B09", "M", "非入口客户端分块命名为 client.<name>.js（入口固定 client.js）",
     "packages/client/tsdown.client.ts", r"chunkFileNames: 'client\.\[name\]\.js'", "has"),
    ("B10", "M", "包内动态分块改走 require.async（CJS 外壳下的异步加载）",
     "packages/client/tsdown.client.ts",
     r"require\.async\(\$\{JSON\.stringify\(specifier\)\}\)", "has"),
    ("B11", "M", "clientBundle 支持按产物文件名选法务/署名文本（clientBanner）",
     "packages/client/tsdown.client.ts",
     r"readonly clientBanner\?: \(fileName: string\) => string \| undefined", "has"),

    # ── 17.4 插槽真实签名 ────────────────────────────────────────────────
    ("U01", "M", "slots.register(options, component) —— 组件是第二个参数",
     "packages/client/ui-slots/src/index.ts",
     r"register\(options: ErasedOptions, component: unknown\): \(\) => void", "has"),
    ("U02", "M", "向未声明 slot 注册会抛具体错误",
     "packages/client/ui-slots/src/index.ts",
     r'is not declared \(a parent entry\'s children table must declare it\)', "has"),
    ("U03", "M", "slots.inject(key, callback) 由 ui-renderer 提供",
     "packages/client/ui-renderer/src/client/registry.ts",
     r"inject\(key: keyof SlotMap & string, callback: \(\) => SlotInjectionEffect\): \(\) => void", "has"),
    ("U04", "S", "root 是内建插槽键（kind single / scope root）",
     "packages/client/ui-renderer/src/client/registry.ts",
     r"'root': \{ kind: 'single'; scope: 'root'; owner: RootOwnerProps \}", "has"),
    ("U05", "M", "ui-layout 是可禁用的补丁行 id（根布局替换法）",
     "packages/bundle/web-app/cordis.patch.yml",
     r"- id: ui-layout[\s\S]{0,80}@deepseek-ai/dsh-client-ui-layout", "has"),
    ("U06", "M", "插件配置插槽更名为 plugins.item，且为 list 语义（id/order，非 keyed）",
     "packages/client/ui-plugin-manager/src/client/slot-contract.ts",
     r"'plugins\.item': \{ kind: 'list'; scope: 'root'", "has"),
    ("U07", "M", "新增 plugins.bundle.config / plugins.row.config 两个 keyed 配置插槽",
     "packages/client/ui-plugin-manager/src/client/slot-contract.ts",
     r"'plugins\.bundle\.config': \{ kind: 'keyed'; scope: 'root'[\s\S]{0,400}?'plugins\.row\.config': \{ kind: 'keyed'; scope: 'root'",
     "has"),
    ("U08", "M", "配置插槽的组件收 view: 'summary' | 'page' 两态",
     "packages/client/ui-plugin-manager/src/client/slot-contract.ts",
     r"readonly view: 'summary' \| 'page'", "has"),

    # ── 17.5 推进基线 0.1.6-alpha.2 时吸收的破坏性事实 ────────────────────
    ("P01", "M", "base 补丁的 hmr 行改用 @deepseek-ai/dsh-hmr（旧名 cordis-plugin-hmr 已不再是模块名）",
     "packages/bundle/base/cordis.patch.yml",
     r"- id: hmr[\s\S]{0,120}?@deepseek-ai/dsh-hmr", "has"),
    ("P02", "M", "官方 README 明写改动范围：只换模块名，hmr 服务键与事件名不变",
     "packages/boot/hmr/README.zh.md",
     r"已有配置将模块名 `@deepseek-ai/cordis-plugin-hmr` 替换为 `@deepseek-ai/dsh-hmr`", "has"),
    ("P03", "M", "base 补丁新增 plugin-manager / tool-plugin-manager 两行",
     "packages/bundle/base/cordis.patch.yml",
     r"- id: tool-plugin-manager[\s\S]{0,200}?- id: plugin-manager", "has"),
    ("P04", "M", "CLI 插件安装改为转发给 @deepseek-ai/dsh-plugin-manager/operations",
     "apps/cli/src/plugin.ts",
     r"import \{ runPluginCommand \} from '@deepseek-ai/dsh-plugin-manager/operations'", "has"),
    ("P05", "M", "bundle 对账（含「未声明 dsh.bundle」警告）实现位于 plugin-manager 包",
     "packages/boot/plugin-manager/src/operations.ts",
     r"declares no dsh\.bundle — installed as a plain dependency, not a profile layer", "has"),

    # ── 反面教材：这些「编造名」在源码中必须不存在（未命中 = HOLDS）───────
    ("X01", "N", "不存在名为 ui 的服务（同类方案 ctx.ui.request 属编造）",
     "packages", r"provide\(\s*'ui'\s*,", "not"),
    ("X02", "N", "不存在裸 settings 插槽键（只有 settings.* 形式）",
     "packages", r"['\"]settings['\"]\s*:\s*\{\s*kind:", "not"),
    ("X03", "N", "不存在裸 status 插槽键",
     "packages", r"['\"]status['\"]\s*:\s*\{\s*kind:", "not"),
    ("X04", "N", "不存在裸 workspace 插槽键",
     "packages", r"['\"]workspace['\"]\s*:\s*\{\s*kind:", "not"),
    ("X05", "N", "webServer.register 不接受 router 回调（无 router.get/post 路由对象）",
     "packages", r"webServer\.register\(\s*\(router\)", "not"),
    ("X06", "N", "settings.plugin.item 不再作为插槽被声明（已整体改名为 plugins.item）",
     "packages", r"['\"]settings\.plugin\.item['\"]\s*:\s*\{\s*kind:", "not"),
]

TEXT_SUFFIXES = {".ts", ".tsx", ".md", ".yml", ".yaml", ".json", ".js", ".mjs"}

# 否定性断言（expect='not'）的护栏：必须先证明「扫描面确实读到了语料」。
# 否则在空仓库/错路径上，所有「X 不存在」都会假通过 —— 这正是
# references/00-version-gate.md §9「一个不能失败的探针比没有探针更危险」的同一类失败。
# (检查 id) -> (相对路径, 该作用域内**必然存在**的护栏模式)
NEGATIVE_GUARDS: dict[str, tuple[str, str]] = {
    "X01": ("packages", r"provide\(\s*['\"]"),
    "X02": ("packages", r"['\"]conversation\.view['\"]\s*:\s*\{\s*kind:"),
    "X03": ("packages", r"['\"]conversation\.view['\"]\s*:\s*\{\s*kind:"),
    "X04": ("packages", r"['\"]conversation\.view['\"]\s*:\s*\{\s*kind:"),
    "X05": ("packages", r"webServer\.register\("),
    "X06": ("packages/client/ui-plugin-manager/src/client/slot-contract.ts",
            r"'plugins\.item': \{ kind: 'list'"),
}


def gather(root: Path, rel: str) -> str:
    """把 rel 指向的文件（或目录下所有文本文件）读成一个大字符串。"""
    target = root / rel
    if target.is_file():
        try:
            return target.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return ""
    if not target.is_dir():
        return ""
    parts: list[str] = []
    for p in target.rglob("*"):
        if not p.is_file() or p.suffix not in TEXT_SUFFIXES:
            continue
        if "/node_modules/" in p.as_posix() or "/dist/" in p.as_posix():
            continue
        try:
            parts.append(p.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
    return "\n".join(parts)


def run(root: Path) -> list[tuple[str, str, str, str, bool]]:
    """返回 [(id, level, desc, path, ok)]。"""
    results = []
    cache: dict[str, str] = {}
    for cid, level, desc, rel, pattern, expect in CHECKS:
        if rel not in cache:
            cache[rel] = gather(root, rel)
        text = cache[rel]
        hit = re.search(pattern, text) is not None
        if expect == "has":
            ok = hit
        else:
            # 否定性断言：既要「没命中」，也要「护栏命中」（证明语料真的读到了）
            guard_rel, guard_pat = NEGATIVE_GUARDS[cid]
            if guard_rel not in cache:
                cache[guard_rel] = gather(root, guard_rel)
            guard_ok = re.search(guard_pat, cache[guard_rel]) is not None
            ok = (not hit) and guard_ok
        results.append((cid, level, desc, rel, ok))
    return results


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    selftest = "--selftest" in sys.argv
    # 默认写到**当前工作目录**，不写进 skill 目录（skill 目录可能只读，且不应被运行时产物污染）
    default_log = Path.cwd() / "_absorbed_claims.log"
    log = Path(args[1]) if len(args) > 1 else default_log

    out: list[str] = []
    lines_ok = True

    if selftest:
        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp)
            (fake / "packages").mkdir()
            (fake / "packages" / "nothing.ts").write_text("export {}\n", encoding="utf-8")
            res = run(fake)
            stales = [r for r in res if not r[4]]
            holds = [r for r in res if r[4]]
            out.append("=== 负向自检（对故意造错的空仓库跑同一张断言表）===")
            out.append(f"  总断言 {len(res)}  期望 STALE {len(res)}  实际 STALE {len(stales)}  HOLDS {len(holds)}")
            for cid, _lvl, _d, _p, ok in holds:
                out.append(f"  🔴 假通过: {cid} 在空仓库上也 HOLDS —— 断言过松，脚本不可信")
            lines_ok = len(holds) == 0
            out.append(f"  判定: {'PASS —— 断言表确实能失败' if lines_ok else 'FAIL —— 存在假通过'}")
    else:
        if not args:
            print("usage: verify_absorbed_claims.py <DSH_repo> | --selftest [log]")
            return 2
        repo = Path(args[0]).resolve()
        if not repo.is_dir():
            print(f"ERROR: 不是目录: {repo}")
            return 2
        res = run(repo)
        holds = [r for r in res if r[4]]
        stales = [r for r in res if not r[4]]
        out.append(f"=== 正向核验 ===  repo = {repo}")
        out.append(f"  总断言 {len(res)}  HOLDS {len(holds)}  STALE {len(stales)}")
        out.append("")
        for cid, lvl, desc, rel, ok in res:
            mark = "HOLDS" if ok else "STALE"
            out.append(f"  {mark}  {cid}  [{lvl}] {desc}")
            if not ok:
                out.append(f"          ← 未在 {rel} 中命中预期模式")
        out.append("")
        lines_ok = len(stales) == 0
        out.append(f"  判定: {'PASS —— 吸收的事实对当前源码全部成立' if lines_ok else f'FAIL —— {len(stales)} 条不成立，不要照抄相关文档'}")

    log.write_text("\n".join(out) + "\n", encoding="utf-8")
    return 0 if lines_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

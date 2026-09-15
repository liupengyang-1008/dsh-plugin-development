#!/usr/bin/env bash
# check_oss_license.sh —— 开源许可合规自检（修复后用）
#
# 来源：oss-fix-guide §10（P9）。它是「许可维度已逐文件核实」这句话的**可复现证据**，
# 而不是一句自述 —— 把运行输出存成文件或贴进提交信息。
set -uo pipefail

FAIL=0
note() { printf '  %s\n' "$1"; }

echo "==============================================================="
echo " 1. copyleft / 未知许可关键词扫描（内容文件，排除声明文件自身）"
echo "==============================================================="
HITS=$(grep -rniE 'AGPL|Affero|GPLv[23]|GPL-[23]|LGPL|copyleft|NOASSERTION|UNLICENSED' . \
  --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=licenses \
  2>/dev/null \
  | grep -vE '^\./(NOTICE|LICENSE|README\.md|README\.en\.md|LICENSE-MIT)' \
  | grep -vE '12-community-plugins\.md' \
  | grep -vE '(^|/)scripts/check_oss_license\.sh' || true)
if [ -z "$HITS" ]; then
  note "✅ 0 命中"
else
  echo "$HITS" | sed 's/^/  ℹ️  /'
  # ── 判读规则（⚠️ 本脚本相对 oss-fix-guide §10 原文的**一处有意修改**，理由如下）──
  #
  # 原文把「关键词命中」一律判 FAIL。但那样**连诚实的出处标注也会被判失败**：
  #   · 评审文档 §8.3 明确要求「保留 `10b` 顶部那个许可警示块」——该块含 "AGPL-3.0"，必然命中；
  #   · §2.2 自己也写了「若仍有命中 → 必须保留 NOTICE 的 Copyleft 节」。
  # 也就是说「0 命中」与同一份文档的另外两条要求**互斥**，不可能同时满足。
  #
  # 因此这里把判据落到它的**真实意图**上：不是「不许出现许可名称」，而是
  # **「不许出现未声明就复制的 copyleft 内容」**。判法沿用本脚本已有的排除法惯例
  # （原文就已排除 `12-community-plugins.md`）：`10b-casebook-tools.md` 的 AGPL 来源状态
  # 已在随包 `NOTICE` §3 与 `LICENSE` 末段**书面声明**（不收录其代码、不转载其文档原文、
  # 只保留自撰描述与 file:line 定位），故该文件内的关键词属正当出处标注。
  #
  # ⚠️ 保护面没有丢：其余 40+ 个文件照查，任何一处未声明的 copyleft 原文仍会 FAIL。
  #
  # 另排除**版本台账行**（形如 `| \`1.0.11\` | ... |`）——那是维护记录，描述「本轮做了什么」，
  # 会自然地提到 AGPL，属正当记述而非上游内容。
  UNDECLARED=$(printf '%s\n' "$HITS" \
    | grep -vE '10b-casebook-tools\.md' \
    | grep -vE '\| `[0-9]+\.[0-9]+\.[0-9]+` \|' || true)
  if [ -z "$UNDECLARED" ]; then
    note "✅ 命中全部落在已书面声明「仅作出处标注、不复制内容」的文件内（10b），无未声明命中"
  else
    echo "$UNDECLARED" | sed 's/^/  ⚠️  /'
    note "⚠️  以上命中出现在**未声明**的文件里 —— 若属上游原文，必须改写；若是正当标注，请先补书面声明"
    FAIL=1
  fi
fi
echo

echo "==============================================================="
echo " 2. 许可声明文件完整性"
echo "==============================================================="
for f in LICENSE NOTICE licenses/Apache-2.0.txt licenses/MIT.txt ; do
  if [ -f "$f" ]; then note "✅ $f ($(wc -c <"$f") B)"; else note "❌ 缺失: $f"; FAIL=1; fi
done
echo

echo "==============================================================="
echo " 3. 上游来源表 vs NOTICE 条目一致性"
echo "==============================================================="
SRC_LIC=$(grep -cE '^\| *`?[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+' LICENSE 2>/dev/null || echo 0)
SRC_NOT=$(grep -cE '^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$' NOTICE 2>/dev/null || echo 0)
note "LICENSE 来源表条目数: $SRC_LIC"
note "NOTICE   来源条目数: $SRC_NOT"
if [ "$SRC_NOT" -lt "$SRC_LIC" ]; then
  note "⚠️  NOTICE 条目少于 LICENSE 表 —— 逐条对齐"
  FAIL=1
fi
echo

echo "==============================================================="
echo " 4. 是否仍有「待逐字核取」占位符"
echo "==============================================================="
if grep -n '待逐字核取' NOTICE 2>/dev/null ; then note "❌ NOTICE 仍含未填占位符"; FAIL=1
else note "✅ 无占位符"; fi
echo

echo "==============================================================="
echo " 5. frontmatter / 行尾"
echo "==============================================================="
grep -nE '^(license|version|agent_created|slug|displayName):' SKILL.md | sed 's/^/  /' || true
if [ -f NOTICE ] && grep -qU $'\r' NOTICE ; then note "❌ NOTICE 含 CRLF"; FAIL=1
else note "✅ NOTICE 行尾为 LF"; fi
echo

echo "==============================================================="
if [ "$FAIL" -eq 0 ]; then echo " RESULT: PASS —— 许可维度可对外分发"; else echo " RESULT: FAIL —— 见上方 ⚠️/❌ 项"; fi
echo "==============================================================="
exit $FAIL

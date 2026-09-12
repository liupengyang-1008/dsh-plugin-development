# dsh-my-bundle

零代码组合包骨架（T1 形态）。**不包含任何 JavaScript** —— 全部行为由 `cordis.patch.yml` 描述。

## 复制后要改的地方

| 文件 | 改什么 |
|---|---|
| `package.json` | `name`、`version`、`description`、`keywords`，以及补上 `repository` |
| `cordis.patch.yml` | 换成你真正要挂载的能力（示例行删掉） |
| `README.md` | 这份说明 |

## 五条容易致命的规则

1. **`dsh.bundle.patch` 不能少。** 少了它，`dsh plugin add` 会打一条 `declares no dsh.bundle` 警告，然后**什么都不做** —— 这是新手最常见的「我明明装了啊」。
2. **`files` 里必须包含 `cordis.patch.yml`。** 漏了它，发布后补丁文件不会进 npm 包，装上有警告、功能全无。
3. **`exports` 要显式声明 `'./cordis.patch.yml'` 与 `'./package.json'`。** 本包是零代码组合包，**没有 JS 入口，所以不要加 `'.'`**（没有可指向的文件）。官方 6 个 bundle 包全部带 `'.'`、`'./cordis.patch.yml'`、`'./package.json'`，部分还有 `'./src/*'`；组合包取与本包实际路径相符的那两个即可，与官方约定保持一致。
4. **`id` 全局唯一。** 重复会报 `duplicate loader entry id` 且**启动即崩**。
5. **`config` 是整段替换，不是深合并。** 后续层覆盖某一行时，必须把整个 `config` 重述一遍。

## 安装

```bash
# 本地目录
dsh plugin --profile <profile 名> add ./minimal-bundle

# 已发布到 npm
dsh plugin --profile <profile 名> add dsh-my-bundle
```

`--profile` 是**必填**参数。

## 验证

```bash
dsh plugin --profile <profile 名> ls
dsh --dump-config          # 打印组装后的配置树，不启动就能检查补丁是否生效
```

## 参考

- 完整模板与逐行讲解：`references/02-templates.md` 的 T1、T2
- 补丁语法与 `!!js` 求值范围：同上 T2
- 踩坑百科：`references/05-pitfalls.md`
- 真实范本：`Q00/ouroboros → integrations/dsh-plugin/`（官方精选清单里唯一的纯配置零代码插件）

# dsh-tool-greet

最小工具插件骨架（T3 形态）。给模型注册一个可调用的工具。

## 目录结构

```
minimal-tool-plugin/
├── package.json
├── cordis.patch.yml
├── README.md
└── src/
    └── index.ts        # 开发期写这里
```

交付时 `package.json` 的 `main` 指向 `index.js` —— 即 `src/index.ts` 的编译产物（纯 JS 手写则把文件直接命名为 `index.js`）。

## 开发期：用 overlay 挂载（不用先打包）

在 profile 目录旁边建 `cordis.yml`：

```yaml
- insert:
    - id: dsh-tool-greet
      name: './src/index.ts'
```

`name` 支持相对路径、绝对路径、npm 包名三种。相对路径会被**锚定到补丁文件所在目录**（源码 `packages/boot/app-boot/src/index.ts` 的 `anchorInsertedPluginNames()` 行为，且有单测固定）。

启动并确认工具已注册：

```bash
dsh --dump-config        # 看组装后的配置树
```

然后在会话里让模型调用 `greet`。**必须看到实际输出**才算跑通 —— 「装上了」不等于「生效了」。

## 交付期：按包名安装

```bash
dsh plugin --profile <profile 名> add .
# 或已发布到 npm
dsh plugin --profile <profile 名> add dsh-tool-greet
```

## 四条必须遵守的规则

1. **不要写 `export default`。** 函数式插件用命名导出 `name` / `inject` / `apply`；有 default 会被当成服务类解析，命名空间被丢弃。
2. **`inject` 里要写 `'tools'`。** 否则 `ctx.tools` 是 `undefined`，插件直接报错。可选服务不要写在 `inject`，用 `ctx.get('x')`。
3. **`parameters` 的 `required` 写在属性级**（`required: true`）。这是 `defineTool` 的 DSH 自有 DSL；裸 `ctx.tools.register` 才是对象级 `required: ['a']`。两条路径规则相反，套错会静默失效或直接报错。
4. **`dsh.bundle.patch` 和 `files` 都不能漏。** 前者漏了 `dsh plugin add` 只打警告不生效；后者漏了补丁文件不会进 npm 包。

## 验证清单

- [ ] `dsh --dump-config` 里能看到这一行
- [ ] 插件没有停在 PENDING（PENDING = 注入的服务没到位）
- [ ] 模型能实际调用工具并拿到正确输出
- [ ] 卸载后工具消失（`ctx.tools.register` 是副作用，不需要手动清理）

## 参考

- 完整字段表与两条注册路径对比：`references/03-api-cookbook.md`
- 模板库 T3 / T4：`references/02-templates.md`
- 官方最小范本逐字源码：`references/02-templates.md` 附录 E（官方模板 3）
- 出问题先查：`references/05-pitfalls.md`、`references/06-workflow.md` 第 ④ 部分（调试与排错）

# Margin · 文档协作模板

打开 `index.html` 即可阅读和批注。正文已经嵌入 HTML；用户不需要先导入 Markdown。

单文件 HTML 内含样式、脚本、Markdown 解析器和净化器。无需服务、安装或网络。目录中的其他文件供 agent 生成后续版本使用。

## 用户怎么用

1. 打开 `index.html`，在左侧切换文档。
2. 选中同一段内的一段文字，点击“批注所选文字”。也可直接点击“＋ 批注”给整篇文档留意见。
3. 点击“＋ 备忘”记录待办，可选日期；日期用于页面内的到期提示，不会后台推送。
4. 在“编辑正文”中修改 Markdown，并保存。正文版本自动增加，原批注继续保留。
5. 用“当前署名”区分用户和不同 agent 的消息；回复可以标记为 Rebuttal 或结论。这里的署名是消息元数据，不代表连接了在线 agent，也不做身份认证。
6. 点击“导出交接包”，把下载的 JSON 发给 agent。正文、引用、备忘、讨论和处理状态都在其中。
7. Agent 可以生成新版 HTML；也可以只提供回复 JSON，通过“载入回复”合并。完整交接包也可在同一工作区恢复，但会替换当前内容，界面提供确认与导出备份。

浏览器本地保存用于恢复同一浏览器中的工作。跨设备、移动文件或清理浏览器前，请导出 JSON。未发送的回复不属于已保存讨论。首次打开新版 HTML 时，优先展示新版内嵌数据；旧本地草稿会保留在“恢复草稿”入口，不会静默覆盖新版。

## Agent 如何生成真实文档

Python 3 即可，无第三方 Python 依赖。首次生成新工作区：

```bash
python3 build.py --new --title "项目设计评审" \
  --docs /path/to/taskplan.md /path/to/findings.md /path/to/specs.md /path/to/standards.md \
  --output /path/to/review.html
```

`--new` 创建全新的工作区，不包含示例文档。Markdown 文件名应唯一；它们会成为稳定的 `source` 标识。

用户返回交接包后，先阅读其中最新正文和讨论，再更新：

```bash
python3 build.py --workspace /path/to/handoff.json \
  --docs /path/to/specs.md \
  --output /path/to/review-v2.html
```

只提供需要替换的 Markdown 文件。相同 `source` 的文档保留 ID，内容发生变化时增加 `revision`；其他文档和所有讨论保持原样。请确保文件内容基于交接包中的最新正文，避免用旧文件覆盖用户编辑。

Agent 也可以直接编辑交接包，再生成：

```bash
python3 build.py --workspace /path/to/revised-workspace.json --output review-v2.html
```

直接编辑交接包时：保留工作区 `id`、文档 `id`、讨论 `id` 和已有消息 `id`；正文变化增加 `revision`；新回复追加到对应讨论的 `messages`，不要改写用户已有发言。`build.py` 会增加页面 `generation`，以区分新 HTML 与浏览器里的旧草稿。

## JSON 交接约定

### 完整交接包：`agent-docs-workspace` v1

顶层字段：

| 字段 | 含义 |
| --- | --- |
| `format` / `version` | `agent-docs-workspace` / `1` |
| `id` / `title` | 工作区稳定 ID 与显示名称 |
| `generation` | HTML 生成版本，正整数 |
| `documents` | 文档数组 |
| `threads` | 批注、备忘及其消息数组 |
| `appliedChangeIds` | 已处理修改建议的 ID，用于防止重复导入 |

文档结构：

```json
{
  "id": "doc-spec",
  "source": "spec.md",
  "title": "交互规格",
  "kind": "SPEC",
  "revision": 1,
  "markdown": "# 标题\n\n正文"
}
```

讨论结构：

```json
{
  "id": "thread-unique-id",
  "documentId": "doc-spec",
  "kind": "comment",
  "status": "open",
  "dueDate": "",
  "anchor": {
    "quote": "引用的原文",
    "before": "引用之前的邻近文字",
    "after": "引用之后的邻近文字",
    "revision": 1
  },
  "messages": [
    {
      "id": "message-unique-id",
      "author": "Reviewer",
      "role": "agent",
      "intent": "rebuttal",
      "body": "具体的意见与依据",
      "createdAt": "2026-10-03T03:00:00Z"
    }
  ]
}
```

- `kind`：`comment` 或 `memo`。
- `status`：`open` 或 `resolved`。
- `dueDate`：空字符串或 `YYYY-MM-DD`。仅显示到期状态。
- `anchor`：段落引用对象，或 `null`（整篇讨论、备忘）。引用需是渲染后可见文字。
- `role`：`human` 或 `agent`。
- `intent`：`comment`、`rebuttal` 或 `decision`。
- `createdAt`：ISO 时间字符串。
- 消息 ID 在整个工作区中唯一。无法唯一定位引用时，保留原文引用并提示，不任意迁移。

### 增量回复：`agent-docs-feedback` v1

查看 `reply.example.json`，可直接在示例页面中载入。

```json
{
  "format": "agent-docs-feedback",
  "version": 1,
  "workspaceId": "与交接包的 id 相同",
  "replies": [
    {
      "id": "新的稳定消息 ID",
      "threadId": "要回复的讨论 ID",
      "author": "Reviewer",
      "role": "agent",
      "intent": "rebuttal",
      "body": "回复内容",
      "createdAt": "2026-10-03T03:00:00Z"
    }
  ],
  "threads": [],
  "changes": [
    {
      "id": "新的稳定修改 ID",
      "documentId": "目标文档 ID",
      "baseRevision": 1,
      "author": "Planner",
      "summary": "修改原因",
      "markdown": "修改后的完整正文"
    }
  ]
}
```

`replies`、`threads`、`changes` 均可省略。`threads` 用于新增讨论，结构与完整交接包中的讨论相同。若要回复已有讨论，使用 `replies`。

载入前页面展示摘要，确认后合并。消息和修改 ID 用于去重；相同消息 ID 携带不同内容会被拒绝。`baseRevision` 与当前文档版本一致时才更新正文；版本冲突时，建议全文保存为一条待处理讨论，原正文保留。冲突建议被视为已处理；修订后请使用新的修改 ID 和当前 `baseRevision`。

## 模板文件

- `index.html`：可直接分享的单文件成品，包含示例正文。
- `template.html`：HTML/CSS/JavaScript 模板。
- `workspace.json`：示例工作区数据。
- `build.py`：将数据和模板组合成单文件 HTML，可装入真实 Markdown 文档。
- `.vendor.js`：随 HTML 一起内嵌的 Markdown 解析和净化代码，生成时需要保留。
- `reply.example.json`：示例 agent 回复。
- `THIRD_PARTY_LICENSES.txt`：内嵌第三方库许可证。

Markdown 支持标题、段落、列表、任务列表、引用、表格、链接和代码块。原始 HTML 只保留文本排版所需的安全标签；脚本、样式、图片与嵌入内容不会执行或加载。正文使用 Markdown 编辑；讨论消息作为纯文本保存。

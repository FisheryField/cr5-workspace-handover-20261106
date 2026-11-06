# 开发任务：AI 长篇小说写作插件（结构化记忆 + 上下文装配）

> 把本文件完整交给实现方 AI。文中"你"指实现方 AI，"用户"指把本文件交给你的人。
> 本文件是规格书，不是建议书。标注【硬性】的条目不得自行改动；标注【可商量】的条目可以提出替代方案，但要先说明理由再动手。

---

## 0. 你的任务

用 Python 实现一个 CLI 工具，帮助作者用大模型写长篇小说（10 万字以上），核心解决一个问题：

**模型写到第 40 章时，忘记了第 3 章埋的伏笔。因为聊天记录被截断了。**

解决方式不是"把更多历史塞进上下文"，而是把记忆从对话记录里独立出来，做成**结构化、可检索、大小恒定**的数据层，每章重新装配一次上下文。

---

## 1. 核心设计原则（先理解，再写码）

### 1.1 三层分离

| 层 | 角色 | 是否进 prompt | 增长速度 |
|---|---|---|---|
| 事实层 | 事件流，append-only，唯一真相 | 不直接进 | 线性增长 |
| 状态层 | 由事实层投影出的"当前状态" | 全量进 | **恒定** |
| 上下文层 | 每次生成时临时装配 | — | **恒定** |

**关键：进 prompt 的东西永远恒定在 6k token 以内，与已写章节数无关。**

### 1.2 事件溯源（event sourcing）

- 真源 = `timeline.jsonl`，只追加，永不修改、永不删除。
- `state.json` 是 `timeline.jsonl` 的**投影**（fold），可随时删除并从事件流重建。
- 模型永远不直接改写 `state.json`，它只产出**增量**（delta），由程序合并。
- 理由：模型原地改文件会静默篡改早期设定且不可回溯。改成增量后，模型的错误变成**可见的追加**，不是**静默的覆盖**。

### 1.3 抽取与生成分离

- 生成正文：一次调用。
- 从正文抽取 delta：**另一次**调用，用便宜模型即可。
- 抽取失败不得阻塞写作流程，但要记录到 `pending/` 等人工处理。

### 1.4 检索优先查表，不优先向量

小说的检索需求 90% 是"某角色最近发生了什么"和"某条伏笔的编号"，这两类用**倒排索引 + 编号精确匹配**即可，零算法、可解释、可单测。向量检索只作为第三类（语义模糊查询）的兜底，v1 不实现。

---

## 2. 【硬性】约束清单

实现时以下各条不得违反：

1. **不得原地改写事实**。`timeline.jsonl` 只允许 `>>` 追加，任何写操作前校验文件长度只增不减。
2. **不得让模型重写整个文件**。所有模型输出都是受限 schema 的增量。
3. **不得使用数据库作为真源**。真源必须是纯文本/JSON 文件，便于 `git diff`、人工编辑、版本回滚。SQLite 只能作为可选的索引缓存，且必须能从文件完全重建。
4. **不得使用递归摘要**（把摘要再摘要）。摘要只从原文抽取，或只做增量追加。
5. **上下文构建必须有硬预算**，超出即按优先级裁剪，且函数返回实际用量。
6. **所有记录必须带章号 `ch`**，且上下文装配时必须过滤掉 `ch >= 当前章` 的所有内容（防剧透/防幻觉）。
7. **人物/地点/物品一律用稳定 ID**，不得用名字当主键。名字和称号走别名表。
8. **v1 不引入向量数据库**、不引入多 agent 编排、不做 GUI。
9. **测试必须能在无网络、无 API key 的情况下全绿**（提供 mock 模式）。
10. **依赖最小化**：Python 3.11+ 标准库为主，最多额外允许 `jsonschema`、`httpx`。不得引入 web 框架、ORM、向量库。

---

## 3. 目录结构

```
novel/
  config.toml
  canon/
    world.md                 # 世界规则/体系/地理，人工维护，几乎不变
    style.md                 # 文风样本 300 字，人工维护
    characters/
      lin_yan.md             # 一个人物一个文件，文件名 = 稳定 ID
    places/
      warehouse.md
    aliases.json             # 别名 → ID 映射
    threads.jsonl            # 伏笔台账，append-only
  outline/
    ch012.md                 # 本章细纲，人工写
  timeline.jsonl             # 事件流，append-only
  state.json                 # 投影产物（可删可重建）
  index.json                 # 倒排索引（可删可重建）
  delta/
    ch012.json               # 每章抽取结果
  archive/
    ch012.md                 # 每章正文原文，只读
  pending/
    ch012.json               # 抽取失败/待人工确认
  logs/
```

---

## 4. 数据模型（精确 schema）

### 4.1 `timeline.jsonl`

一行一条记录，UTF-8，不允许换行。字段：

```json
{"seq": 1203, "ch": 12, "kind": "event", "who": ["lin_yan"], "what": "在仓库发现老周的怀表停在3:40", "where": "warehouse", "when_story": "D+3 傍晚", "quote": "怀表的指针停在三点四十。", "confidence": 0.95}
```

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `seq` | int | 是 | 全局单调递增，合并时分配 |
| `ch` | int | 是 | 来源章节号 |
| `kind` | enum | 是 | `event` / `fact` / `thread_open` / `thread_close` / `entity` / `retcon` |
| `who` | string[] | 视 kind | 涉及的实体 ID |
| `what` | string | 是 | 一句话事实，不超过 60 字 |
| `where` | string | 否 | 地点 ID |
| `when_story` | string | 否 | 故事内时间，自由文本 |
| `quote` | string | 否 | 原文佐证句，抽取时必填 |
| `confidence` | float | 是 | 0–1，低于 0.6 进入待确认 |

`retcon` 是唯一的"修正"手段：不删除旧记录，而是追加一条声明"此前的 X 作废，改为 Y"，字段含 `targets: [seq...]`。

### 4.2 `delta/chNNN.json`

模型抽取的唯一产物：

```json
{
  "ch": 12,
  "summary": "不超过200字，只记事实不记文笔",
  "events": [
    {"who": ["lin_yan"], "what": "发现怀表停在3:40", "where": "warehouse", "quote": "怀表的指针停在三点四十。"}
  ],
  "threads_open": [
    {"id": "F017", "desc": "仓库墙上的划痕", "planned_close_ch": 20}
  ],
  "threads_close": ["F009"],
  "entities": [
    {"id": "shen_yuan", "new_aliases": ["沈姑娘"]}
  ],
  "knowledge_changes": [
    {"who": "lin_yan", "learned": "货单是假的", "still_unaware": "老周已叛"}
  ],
  "state_patch": {
    "story_time": "D+3 傍晚",
    "location": "warehouse",
    "present": ["lin_yan", "lao_zhou"],
    "injuries": {"lin_yan": {"desc": "左臂受伤", "expires_ch": 14}},
    "items": {"bronze_key": {"holder": "shen_yuan"}}
  },
  "contradictions": [
    {"with_seq": 804, "desc": "第7章说钥匙在林砚手里"}
  ],
  "uncertain": ["墙上划痕的来历未交代"]
}
```

### 4.3 `state.json`（投影产物）

```json
{
  "as_of_ch": 12,
  "story_time": "D+3 傍晚",
  "location": "warehouse",
  "present": ["lin_yan", "lao_zhou"],
  "knowledge": {
    "lin_yan": {"knows": ["货单是假的"], "unaware_of": ["老周已叛"]}
  },
  "chars": {
    "lin_yan": {"injuries": [{"desc": "左臂受伤", "expires_ch": 14}], "items": [], "last_seen_ch": 12}
  },
  "items": {"bronze_key": {"holder": "shen_yuan"}},
  "open_threads": [{"id": "F017", "desc": "仓库墙上的划痕", "opened_ch": 12, "planned_close_ch": 20}],
  "suspense": "仓库外那把火是谁放的",
  "next_must": []
}
```

投影函数 `project_state(records, as_of_ch=None) -> dict`：

- 按 `seq` 升序 fold。
- 只处理 `ch <= as_of_ch` 的记录。
- 处理 `retcon`：被指向的 seq 视为无效。
- 处理 `thread_close`：从 `open_threads` 移除。
- 处理 `expires_ch`：`as_of_ch > expires_ch` 的伤病自动移除。
- **必须幂等**：`project(project 的输入) == project 一次的结果`。

### 4.4 伏笔 `canon/threads.jsonl`

```json
{"id": "F017", "opened_ch": 12, "desc": "仓库墙上的划痕", "planned_close_ch": 20, "status": "open"}
```

ID 格式 `F` + 三位数字，全局唯一、只增不减。`status` 由投影与 delta 共同决定，不在文件里手写状态。

### 4.5 人物 `canon/characters/<id>.md`

人工可读的 Markdown，含固定小节：

```markdown
# 林砚
- id: lin_yan
- 别名: 小砚, 砚哥
- 外貌: ...
- 口癖: 说话前先"啧"一声
- 动机: 查清父亲死因
- 禁忌: 不提母亲
- 说话样本:
  > "啧。这单子有问题。"
```

`aliases.json` 由这些文件自动汇总生成，**同一别名不得映射到两个 ID**，冲突时报错。

---

## 5. 核心模块

### 5.1 `build_context(ch, query=None, budget=6000) -> (prompt, usage)`

按固定顺序渲染，每段有独立配额。**配额之和必须 ≤ budget**，实际渲染后再做一次总裁剪。

| 顺序 | 段落 | 配额(tokens) | 优先级 | 内容 |
|---|---|---|---|---|
| 1 | 截止声明 | 60 | P0 | "你只知道第 N-1 章为止的事" |
| 2 | 文风样本 | 350 | P0 | `style.md` |
| 3 | 世界规则 | 500 | P0 | `world.md`，超长则只取"硬性规则"小节 |
| 4 | 当前状态 | 800 | P0 | `state.json` 渲染成自然语言 |
| 5 | 本章出场人物 | 800 | P1 | 按 `present` 取人物卡，只取外貌/口癖/动机/样本 |
| 6 | 待回收伏笔 | 400 | P1 | `open_threads` 中 `planned_close_ch <= ch` 或最近 3 章内开启的 |
| 7 | 本章细纲 | 500 | P1 | `outline/chNNN.md` |
| 8 | 上一章结尾原文 | 800 | P2 | `archive/ch(N-1).md` 末尾约 600 字 |
| 9 | 检索到的历史事件 | 1000 | P2 | 见 5.3 |
| 10 | 输出格式要求 | 300 | P2 | 字数、不要解释等 |

- 裁剪顺序：P2 → P1 → P0，同级内先砍旧的。
- 返回 `usage`：每段实际 token 数与总量。
- token 计数用可插拔函数 `count_tokens(text)`，默认实现：`CJK 字符数 + 其他字符数/3.5`，允许用户替换为真实 tokenizer。
- **断言**：任意输入下 `usage.total <= budget`，否则抛异常。

### 5.2 `ingest(ch, delta, dry_run=False)`

1. 校验 delta schema。
2. 校验引用完整性：`threads_close` 的 id 必须已在 `open`；`who` 里的 ID 必须存在于 `characters/` 或本次 `entities`。
3. 分配 `seq`，把 events / thread_* / knowledge_changes 展开成 timeline 记录，追加。
4. 追加前记录文件字节长度，追加后校验"只增不减"。
5. 重建 `state.json` 与 `index.json`。
6. 返回 `contradictions` 列表。有冲突时**仍然写入**（append-only），但以非零退出码提示人工裁决。
7. `dry_run=True` 时只打印将追加的行，不落盘。

### 5.3 检索层（v1，无向量）

```python
def query_entity(entity_id, last_n=5) -> list[record]      # 倒排索引命中，按 ch 倒序取前 n
def query_thread(thread_id) -> dict                        # 编号精确匹配
def query_recent(ch, window=2) -> list[record]             # 最近 window 章所有事件
def query_keyword(kw, limit=10) -> list[record]            # 简单子串/分词匹配
```

`index.json` 结构：

```json
{"entities": {"lin_yan": [3, 5, 7, 12]}, "threads": {"F017": [12]}, "places": {"warehouse": [12]}}
```

从 `timeline.jsonl` 全量重建，不做增量维护（章节数在千级以内，重建耗时 < 100ms，简单优于快）。

`build_context` 的默认检索策略：
`query_recent(ch, 2)` + `query_entity(present 中的主角, 3)` + `query_thread(到期伏笔)`，去重后按配额裁剪。

### 5.4 矛盾检测 `check(ch)`

只做**可机械判定**的四类，其余交人工：

1. 同一 `(who, what)` 重复追加且 `what` 语义相反 → 报可疑（用关键词表：`不是/没有/拒绝/失败` 对 `是/有/答应/成功`）。
2. `threads_close` 引用了未开启的伏笔。
3. 别名冲突。
4. 时间倒流：`when_story` 若为 `D+n` 格式，新记录 n 小于上一条。

不做语义级矛盾检测（那是 v2 的事，容易误报）。

---

## 6. CLI 契约

```
novel init --title "..." --dir ./novel
novel context --ch 13 [--budget 6000] [--out prompt.txt] [--query "怀表"]
novel ingest --ch 13 --delta delta/ch013.json [--dry-run]
novel project [--as-of 13]          # 重建 state.json / index.json
novel check --ch 13                 # 输出冲突报告，退出码非 0 表示有问题
novel query entity lin_yan --last 5
novel query thread F017
novel stats                         # 总章数、总字数、token 用量趋势、未回收伏笔数
novel extract --ch 13 --mock        # 调模型从 archive/ch013.md 抽 delta
novel write --ch 13 --mock          # 调模型生成正文（需先 context）
novel selftest                      # 跑内置自检
```

`--mock` 走本地固定响应，不联网。

配置 `config.toml`：

```toml
[model]
provider = "openai-compatible"
base_url = "https://api.example.com/v1"
model = "your-model"
api_key_env = "NOVEL_API_KEY"
cheap_model = "your-cheap-model"

[context]
budget = 6000
style_tokens = 350
world_tokens = 500
state_tokens = 800
char_tokens = 800
thread_tokens = 400
outline_tokens = 500
prev_tail_tokens = 800
retrieval_tokens = 1000
```

---

## 7. 插件内置的提示词模板

把以下三段写进 `prompts/` 目录，用 `{占位符}` 填充。**它们本身也是交付物，措辞不要随意改写。**

### 7.1 `prompts/write.md` — 生成正文

```
你是长篇小说《{title}》的作者。现在只写第 {ch} 章正文。

【铁律】
1. 只能使用下方【设定】【状态】【人物】【伏笔】中明确给出的事实。不得引入未列出的设定、能力、人物关系。
2. 你不知道第 {ch} 章之后的任何事。严禁暗示、伏笔式预告或"后文中"式表述。
3. 角色的行动必须符合【信息差】：角色只能依据自己"已知"的信息行动。不要让角色说出他不该知道的事。
4. 不要解释你的写法，不要加小标题，不要写"本章完"。直接输出正文。

【截止声明】
故事进行到第 {prev_ch} 章结束时的状态如下。

【设定】
{world}

【文风样本】
{style}

【状态】
{state}

【本章出场人物】
{characters}

【待推进伏笔】
{threads}

【上一章结尾原文】
{prev_tail}

【历史片段（可能相关，不一定用）】
{retrieved}

【本章要求】
{outline}

字数：{min_words}–{max_words} 字。
```

### 7.2 `prompts/extract.md` — 抽取 delta

```
你是小说数据抽取器。读下面这一章正文，输出一个 JSON 对象。只输出 JSON，不要 markdown 代码块，不要任何解释。

【JSON schema】
{schema}

【抽取规则】
1. 只记录正文中**明确写出**的事实。不推断、不补充、不润色。
2. 每条 event 必须附 quote，quote 必须是正文原句的连续子串（≤40 字）。
3. who 只能从给定 ID 列表中选择：{id_list}。不得新造 ID。
4. 正文中出现新人物时，在 entities 里给出建议 ID（小写下划线）和别名。
5. 无法确定的内容放进 uncertain，不要猜。
6. 如果某条事实与【已有事实】冲突，写进 contradictions，**不要自行调和**。
7. summary 只记事实，不记文笔评价，≤200 字。

【已有事实（最近 {n} 条）】
{recent_facts}

【当前未回收伏笔】
{open_threads}

【第 {ch} 章正文】
{text}
```

### 7.3 `prompts/verify.md` — 一致性校验

```
对照【状态】与【本章正文】，只回答四个问题，输出 JSON：

{
  "who_learned_what": [{"who": "id", "learned": "..."}],
  "state_changed": ["..."],
  "threads_touched": [{"id": "F017", "action": "open|advance|close"}],
  "contradictions": [{"with": "第N章/seq", "desc": "..."}]
}

只报告正文中确实发生的事。没有就返回空数组。

【状态】
{state}

【本章正文】
{text}
```

---

## 8. 【硬性】验收标准

实现完成后必须全部通过，逐条给出测试证据：

| # | 测试 | 判据 |
|---|---|---|
| 1 | 投影幂等 | `project()` 连跑两次，`state.json` 字节级相同 |
| 2 | 投影可重建 | 删除 `state.json` 与 `index.json` 后 `project`，与原文件一致 |
| 3 | 时间旅行 | `project(as_of=5)` 不含任何 `ch>5` 的记录 |
| 4 | 预算硬约束 | 构造 200 章数据，任意章 `build_context` 的 `usage.total <= budget` |
| 5 | 防剧透 | 上下文渲染结果中不出现 `ch >= 当前章` 的任何 event 文本 |
| 6 | 只增不减 | 篡改 `timeline.jsonl` 中间某行后 `ingest` 必须报错拒绝 |
| 7 | 引用完整性 | `threads_close` 引用未开启的 ID 时 `ingest` 报错 |
| 8 | 别名冲突 | 两个人物登记同一别名时 `project` 报错 |
| 9 | 冲突可见 | 写入矛盾事件后 `check` 退出码非 0 且列出冲突 |
| 10 | 离线可测 | `pytest` 在无网络、无 API key 环境下全绿 |
| 11 | 端到端 | mock 模式下跑 10 章：write → extract → ingest → check 全链路无人工干预 |
| 12 | 常量上下文 | 第 10 章与第 200 章的 `usage.total` 差值 ≤ 5% |

测试放在 `tests/`，用 pytest。示例数据放 `fixtures/`，至少造 20 章的合成数据用于测试 3/4/5/12。

---

## 9. 里程碑（按顺序做，每个里程碑结束先跑测试再汇报）

**M0 — 骨架与只读链路（约半天）**
目录初始化、schema 定义、`init` / `project` / `context` 三个命令、投影函数、上下文装配、测试 1–5、12。

**M1 — 写入链路**
`ingest`、`check`、`extract`（含 mock）、测试 6–9。

**M2 — 检索与闭环**
`index.json` 重建、四个 query 函数、`stats`、端到端 mock 跑 10 章、测试 10–11。

**M3 — 打磨**
错误信息可读性、`--dry-run` 完善、README（面向作者，不是面向开发者）、一个 20 章示例数据集。

每个里程碑结束输出：做了什么、测试结果、遗留问题、下一步。不要等全部做完再汇报。

---

## 10. 明确不做（v1）

- 不做向量检索 / embedding（v2 再说，且必须是可选插件）
- 不做多 agent 编排（大纲 agent、审稿 agent 等）
- 不做 Web UI / 桌面 GUI
- 不做自动发布、格式导出
- 不做语义级矛盾检测
- 不做"自动改写前文"，只做 append
- 不用数据库做主存储

---

## 11. 交付物

1. 可运行的 Python 包，`pip install -e .` 后 `novel --help` 可用。
2. `tests/` 全绿，附一段 `pytest -q` 的原始输出。
3. `README.md`：面向作者的使用说明，含"写第 13 章的完整 5 步流程"。
4. `docs/design.md`：1500 字以内，说明为什么用事件溯源、为什么不用向量、上下文预算怎么分配。
5. `fixtures/demo/`：20 章合成数据集，能直接 `novel context --ch 21` 看到效果。

---

## 12. 工作方式要求

- 遇到规格未覆盖的细节，自行选择最保守（最不容易丢数据）的方案，并在汇报里列出来，不要停下来提问。
- 任何可能破坏已有数据的功能，默认 `--dry-run`，必须显式加 `--force` 才落盘。
- 代码注释和文档用中文；变量名、函数名用英文。
- 每个公开函数写 docstring，说明输入、输出、副作用。
- 不要为了"优雅"引入抽象层。这个工具的规模在 800–1500 行，超过 2000 行说明设计复杂了。

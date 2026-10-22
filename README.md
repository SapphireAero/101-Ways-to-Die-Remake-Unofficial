# 101 Ways to Die Remake Unofficial

基于 Ren’Py 8.5.0 的数据驱动叙事运行时。JSON 描述场景事件、条件分支、文本段落与媒体控制，Ren’Py 脚本负责调度事件并接入原生对话、历史、存读档和回退机制。

## 作者的话
去年年底偶然在硬盘里寻觅到这个游戏，无愧为三大毒电波。
基于renpy8.5.0进行了重置，算是一次学习，把游戏进行了重置，没有开源素材但是开源了代码。
release提供PC（Windows/Linux），Mac，Android，IOS的完整重置版本

## 运行环境与目录

使用 Ren’Py 8.5.0 SDK 打开项目并启动。保留标准 `game/` 目录结构；存档目录由 `config.save_directory` 指定，当前为 `101RemakePublicDemo-v1`。

```text
game/
  original_data.rpy                 数据加载、文本解析、两级路线解释器
  original_reader.rpy               事件执行与 Ren’Py 脚本入口
  original_supplemental_routes.rpy  子场景调用栈与阶段状态
  original_story_support.rpy        段落对齐、事件合并、对话标识
  original_presentation.rpy         等待与文本窗口控制
  original_audio.rpy                音频通道、预览与加载恢复
  original_gallery_progress.rpy     鉴赏进度
  original_gallery_ui.rpy           鉴赏与回放界面
  language.rpy                     语言切换与缓存失效
  screens.rpy / original_ui.rpy     对话、历史、菜单和设置
  demo_dialogue_lines.rpy           预生成的原生对话语句
  demo/data/                       JSON 数据与翻译表
  demo/cg/                         几何占位图
  gui/ / tl/                       通用界面资源与界面翻译
LICENSES/                          第三方许可证
```

## 执行模型

运行时分为根路线和场景内部两个层级：根路线选择接下来调用哪个场景，场景解释器负责场景内的事件分组与条件范围。

```text
start → original_script_reader
          ├─ original_route_begin()：初始化根路线
          ├─ 调用 catalog.prologue 指定的序章
          └─ 循环
               original_route_next(state)
                 → original_scenario_file_reader
                     → 加载并合并场景事件
                     → original_scenario_route_begin(events, route)
                     → 按事件组执行文本、选择、图片、控制与子调用
                     → 返回最后一次选择结果
                 → original_route_apply_choice(state, result)
```

根路线没有场景调用时，入口转入 `original_linear_script_reader`，按 `pure_script.txt` 的非空文本行顺序执行，并读取行级背景和选项表。

### 路线状态与分支

`original_route_*` 和 `original_scenario_route_*` 都使用 `begin → next → apply_choice` 协议。根路线操作场景调用列表，场景解释器操作按偏移分组的事件列表。

| 状态字段 | 含义 |
| --- | --- |
| `calls` / `groups` | 排序后的场景调用或事件组 |
| `conditions` | 以选择位置为键的条件节点 |
| `frames` | 当前有效的偏移范围栈 |
| `pending` | 已取出、尚未应用选择结果的调用或事件组 |
| `done` | 所有范围处理完毕的标记 |

每个范围帧包含：

```python
{"cursor": 起始位置, "end": 当前范围终点, "ceiling": 可延伸的终点}
```

范围采用左闭右开区间 `[cursor, end)`。`next` 在栈顶范围中查找下一个位置，前移游标并设置 `pending`；再次调用 `next` 会返回同一待处理项，直到 `apply_choice` 清除它。

遇到条件节点时，解释器将父帧游标移到共同继续位置 `group_end`，再压入所选分支的范围。分支耗尽后弹栈，恢复父帧并继续执行。嵌套分支需要越过当前词法范围时，通过 `ceiling` 保留可继续执行的边界。事件组中的事件按合并后的顺序执行，同一偏移不会拆成多个独立分组。

### 子场景调用

`call` 事件通过 `original_scenario_push_call()` 保存父场景现场，包括场景名、事件列表、路线状态、事件组、组内索引、最后选项和当前阶段。子场景返回后，`original_scenario_pop_call(result)` 恢复这些字段。

子场景返回非 `None` 的选择结果时，该结果会写回父场景的最后选择与当前组选择；没有产生选择时，保留父场景原来的结果。

`original_auxiliary_progress` 保存本轮流程的阶段计数。场景进入时取阶段快照，带 `stage` 字段的调用只在阶段相等时执行。场景完成后的计数上限由 `catalog.json` 的 `auxiliary_limits` 定义。

## 数据接口

数据入口在 `original_data.rpy` 中定义：

```python
ORIGINAL_DATA_DIRECTORY = "demo/data"
```

文件通过 `renpy.file()` 加载。事件和路线加载器将场景名转为大写，因此数据表中的场景键应使用统一的大写名称。演示中的 `.FOB` 后缀仅作为场景标识，仓库不包含原作 FOB 文件。

| 文件（相对于数据目录） | 职责 |
| --- | --- |
| `catalog.json` | 序章、CG、场景、结局及媒体映射 |
| `route_flow_draft.json` | 根路线调用与分支范围 |
| `scenario_events.json` | 场景事件序列 |
| `scenario_routes.json` | 场景内部条件范围 |
| `scenario_dialogue.json` | 物理文本事件到显示段落的映射 |
| `scenario_visual.json` | 背景与图片事件 |
| `scenario_control.json` | 等待、窗口显示和关闭事件 |
| `scenario_audio.json` | 音乐与音效事件 |
| `translations/schinese.json` | 默认中文的事件文本与选项映射 |
| `translations/japanese.json` | 日文覆盖表；没有覆盖时使用源事件文本 |
| `pure_script.txt` | 线性读取模式的文本 |
| `background_events.json`、`choice_events.json` | 线性读取模式的行级事件 |

### 资源目录表

`catalog.json` 的主要字段如下：

| 字段 | 约定 |
| --- | --- |
| `prologue` | 序章场景 ID |
| `cg` | `[名称, 资源路径, 来源说明]` 三元组列表；当前相册从路径中筛选 `/cg/` 或 `/cg_r18/` |
| `scenes`、`endings` | 含 `scenario`、`title` 的目录项；结局项可提供 `movie` |
| `auxiliary_limits` | 场景 ID 到阶段计数上限的映射 |
| `bgm`、`se` | 数字字符串 ID 到音频路径的映射，加载时将键转换为整数 |
| `opening_movie` | 可选的开场视频路径 |

所有资源路径均相对于 `game/`。当前目录表只引用演示内容。

### 事件格式

事件具有稳定的 `id`、十六进制字符串 `offset` 和事件类型 `type`。场景中的事件以场景 ID 分组：

```json
{
  "DEMO_A.FOB": [
    {
      "id": "DEMO_A.FOB:0x10:text:0",
      "offset": "0x10",
      "type": "text",
      "text": "青いルートを選びました。"
    }
  ]
}
```

| `type` | 主要字段与执行行为 |
| --- | --- |
| `text` | `text`；解析当前语言后调用对应的原生对话标签 |
| `choice` | `options`；显示选项，记录从 0 开始的选项索引 |
| `background` | `image`、可选 `transition`；切换图片并记录鉴赏进度 |
| `call` | `scenario`、可选 `stage`；保存现场并调用子场景 |
| `jump` | `target`；将场景范围栈重置为目标偏移到当前最大 `ceiling` 的范围 |
| `branch` | `value`、`target`；最后选择不等于 `value` 时执行跳转 |
| `audio` | `command` 及对应的音轨、音效、通道参数 |
| `control` | `command` 及等待时长等参数 |

`jump` 和 `branch` 的 `target` 使用整数偏移。`id` 同时用于翻译、段落对齐与事件定位；调整文本内容时应保留原 ID，新增事件应分配新 ID。

### 根路线与场景条件

根路线将调用位置与选择结果关联。以下为演示中使用的两分支结构：

```json
{
  "scenario_calls": [
    {"offset": 10, "scenario": "DEMO_CHOICE.FOB"},
    {"offset": 20, "scenario": "DEMO_A.FOB"},
    {"offset": 30, "scenario": "DEMO_B.FOB"},
    {"offset": 40, "scenario": "DEMO_END.FOB"}
  ],
  "conditions": [{
    "source_call_offset": "0xa",
    "option_count": 2,
    "branch_group": {"metadata_end": "0x28"},
    "branches": [
      {"range": ["0x14", "0x1e"]},
      {"range": ["0x1e", "0x28"]}
    ]
  }],
  "root_end": 50
}
```

选择 0 时执行 `[20, 30)`，选择 1 时执行 `[30, 40)`，之后都从偏移 40 继续。`scenario_calls.offset` 和 `root_end` 使用整数；`source_call_offset`、`metadata_end` 和 `range` 端点按十六进制字符串解析。

`scenario_routes.json` 则按场景 ID 保存 `conditions` 列表。每个条件使用整数 `choice_offset`、`option_count`、`group_end`，分支使用整数 `start`、`end`，分支数应与 `option_count` 一致。

### 事件合并顺序

场景加载时先按段落表对齐文本，再合并图片、音频和控制事件：

1. 带 `anchor` 的事件按目标事件 ID 插入，`position` 使用 `before` 或 `after`；同一锚点内按 `control_index` 排序，缺省值为 `-1`。
2. 没有锚点的事件直接加入序列。
3. 合并结果按十六进制偏移稳定排序，再交给场景解释器分组。

当 `scenario_visual.json` 为某场景提供了条目时，基础事件列表中的 `background` 会被该条目替代。锚点描述的是合并时的相对顺序，最终执行顺序仍受偏移排序约束。

## 对话标识与语言解析

### 显示段落与原生语句

`scenario_dialogue.json` 通过 `ids` 将物理文本事件映射到显示段落。组内事件共用 `dialogue_group`，读取器只在首事件显示一次；多事件段落使用 `首事件ID:paragraph:1` 作为 `dialogue_key`。

对话标签命名规则为：

```python
"original_line_" + sha256(key.encode("utf-8")).hexdigest()[:24]
```

单事件默认使用事件 ID；线性文本使用 `file:文件名:行索引`。预生成的标签包含独立的原生 `say` 语句：

```renpy
label original_line_标识:
    narrator "[original_dynamic_text()]"
    return
```

修改事件、段落分组或线性文本后，需要同步维护 `game/demo_dialogue_lines.rpy`。每个显示段落都应具有按上述规则命名的独立标签；已有段落保持原标识，新增段落添加对应标签，合并或拆分段落时同步调整映射。

标签为 Ren’Py 的已读记录提供稳定语句位置；文本值在显示时解析。对话框高度则通过字符宽度和行数估算，在默认文本框高度与屏幕可用高度之间调整。

### 语言与历史记录

| Ren’Py 语言值 | JSON 语言键 | 文本来源 |
| --- | --- | --- |
| `None` | `schinese` | 中文覆盖表，缺省时回退到源文本 |
| `japanese` | `japanese` | 日文覆盖表，缺省时回退到源文本 |

事件缓存保留源文本。`original_localize_event()` 根据稳定事件 ID 获取当前语言的 `text` 或 `options`；选项覆盖表的长度必须与源选项一致。

`original_dialogue_context` 保存事件或文件行的来源信息。历史回调将该来源附加到历史条目，随后由对话屏幕和历史屏幕重新解析，使语言切换能作用于当前行与历史内容。

`OriginalLanguageAction` 调用 `original_set_language()`：先强制切换 Ren’Py 语言，再清空场景、文本和翻译表缓存，最后重启当前交互。界面字符串使用 `tl/japanese/` 下的 Ren’Py 翻译文件，事件正文使用 JSON 翻译表。

## 状态与鉴赏进度

| 状态 | 存储与用途 |
| --- | --- |
| `original_route_state`、`original_scenario_state` | Ren’Py store 中的路线游标、分支帧和待处理项 |
| `original_scenario_call_stack` | 父场景现场栈 |
| `original_auxiliary_progress` | 当前流程的阶段计数，新流程开始时重置 |
| `original_choice_history` | 已选择的事件或文本行、选项索引及显示文本 |
| `persistent.original_completed_scenarios` | 跨存档的场景完成集合，持久化数据合并时取集合并集 |
| Ren’Py 图片已见记录 | CG 观看状态，按资源路径记录 |

场景执行到末尾且含有文本事件时写入完成集合；仅作出路线选择不会直接解锁场景。CG 在剧情实际切换到对应图片时记录，相册绘制不写入观看状态。回放期间通过 `original_gallery_replay_mode` 和 `_in_replay` 阻止新增 CG 与场景完成记录。

## 音频与呈现控制

音效使用 `original_se_0` 至 `original_se_2` 三个非循环通道，音乐预览使用独立的 `original_music_preview` 通道。进入预览时暂停剧情音乐，退出时停止预览并恢复剧情音乐。

音频指令包括 `PlayCD`、`StopCD`、`StopCD2`、`SePlay`、`SePlayEx`、`SeWait`、`SeStop`、`SeStopFade` 和 `SeStopAll`。音轨与音效 ID 由目录表映射；兼容逻辑将音轨 13 视为停止音乐。

呈现指令由 `original_presentation_execute()` 处理：`WaitTime` 将 `ticks` 按 60 Hz 转为秒，`WaitKey` 等待输入，`TextOn` 恢复自动文本窗口，窗口开关指令控制显示与转场。恢复状态时跳过等待。视频入口在 `renpy.loadable(path)` 为真时调用 `renpy.movie_cutscene(path)`。

## 资源与扩展

新增内容需要同步更新资源目录表、事件数据和对话标签。`.gitignore` 排除运行缓存、存档、原作数据目录、音视频及发行文件；调整公开的资源类型时，应同步维护忽略规则和许可说明。

仓库只提供通用界面资源、字体、演示文本和几何图形，不含原作剧情及视听素材。完整工程接入需自行适配数据入口、资源映射、剧情规则与菜单。

## 许可

项目代码改动、演示文本和几何图形采用 [MIT 许可](LICENSE)。Ren’Py 模板、通用界面资源和字体保留各自许可，见 [第三方组件说明](THIRD_PARTY_NOTICES.md)。原作游戏内容不在本项目许可范围内。

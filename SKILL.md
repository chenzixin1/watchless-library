---
name: watchless-library
description: 将视频链接或本地视频文件转换为固定风格的“边看边读”学习网站，并把新课程持续追加到同一目录。用于“把视频做成学习站”“像 agent-learning 那样整理”“把新视频加入学习库”等请求。Skill 已内置 Watchless、video-use、站点模板、入库脚本和示例课程，可完成转录、语义分段、关键帧、图文笔记、视频联动与目录更新。
description_zh: 视频转固定风格学习网站并持续入库
description_en: Turn videos into a cumulative watch-and-read learning site
disable: false
agent_created: true
---

# Watchless Library

将输入视频处理成固定风格学习站：左侧视频与章节，右侧图文笔记；播放时自动跟随，点击段落跳回对应时刻，自动保存学习进度。

保持站点外壳稳定。新增视频时只生成课程数据、媒体文件并更新目录，不为单个课程修改模板。

## Bundled resources

- `dependencies/watchless/`：转录、路由、语义分段、关键帧与图文笔记流水线
- `dependencies/video-use/`：转录打包与局部时间线检查工具
- `assets/site-template/`：固定站点模板
- `scripts/setup_runtime.py`：创建隔离 Python 环境并安装依赖
- `scripts/run_watchless.py`：调用仓库内置 Watchless
- `scripts/init_site.py`：初始化或刷新站点外壳
- `scripts/ingest.py`：把 Watchless 项目写入学习站并更新目录
- `scripts/doctor.py`：检查依赖、数据与示例站点
- `site/`：已包含一门课程的可运行站点实例

## Workflow

### 1. 定位 Skill 根目录

以当前 `SKILL.md` 所在目录为 `SKILL_ROOT`。所有脚本和依赖均使用相对路径，不依赖用户预先安装同名 Skill。

### 2. 准备隔离运行环境

检查 `SKILL_ROOT/.runtime/venv/bin/python`。不存在时运行：

```bash
python3 "$SKILL_ROOT/scripts/setup_runtime.py"
```

仅在 Skill 自身 `.runtime/` 中安装 Python 包。禁止全局安装依赖。

确认系统已有 `ffmpeg`、`ffprobe` 和 Chromium/Chrome。运行：

```bash
python3 "$SKILL_ROOT/scripts/doctor.py"
```

### 3. 初始化学习站

默认复用仓库中的 `SKILL_ROOT/site/`。需要在其他工作区建立新实例时运行：

```bash
python3 "$SKILL_ROOT/scripts/init_site.py" "<目标站点目录>"
```

站点已存在时保留 `data/` 与 `media/`。只有明确升级统一模板时才加 `--refresh-template`。

### 4. 处理视频

对视频链接或本地文件运行 prepare：

```bash
python3 "$SKILL_ROOT/scripts/run_watchless.py" --cwd "<工作目录>" \
  "<视频链接或文件路径>" --stage prepare
```

读取输出的 `PROJECT_DIR`、`verify/mode-overview.jpg` 和 `work/video-use/takes_packed.md`，再按内容选择路由：

- 演讲或讲解：`presentation` 或 `explainer`
- 访谈或对谈：`conversation`
- 产品操作演示：`demo`

继续执行 `route → timeline → scenes → select → batches`。遵循内置 `dependencies/watchless/SKILL.zh-CN.md` 的质量门槛：

1. 根据语义和画面设置场景边界，不只按固定时长切割。
2. 用 `dependencies/video-use/helpers/timeline_view.py` 检查边界前后画面。
3. 从候选接触表中人工选择关键帧。
4. 对 conversation 路由补齐 `work/speaker-map.json`。
5. 为每个场景生成 `work/codex-notes/scene_NNN.md`，保留关键观点、完整上下文和画面说明。

无需先生成 Watchless 的最终 PDF；学习站入库只依赖 `work/` 目录。

### 5. 入库并更新目录

运行：

```bash
python3 "$SKILL_ROOT/scripts/ingest.py" "<Watchless PROJECT_DIR>" \
  --site "<学习站目录>" \
  --id "<稳定的英文短标识>" \
  --source "<来源>" \
  --speaker "<讲者>" \
  --tags "<逗号分隔标签>"
```

让脚本自动完成：

- 复制或转码视频为浏览器兼容的 H.264/AAC MP4
- 复制封面和关键帧
- 解析结构化场景笔记、说话人和带时间码原话
- 生成 `data/lesson-<id>.js`
- upsert `data/catalog.js`
- 按月份自动分组并清理已删除课程的孤儿目录项

同一 `--id` 重跑必须覆盖更新，不生成重复记录。视频未变化时复用现有媒体，避免重复转码。

### 6. 验证站点

执行语法和资源检查：

```bash
node --check "<学习站目录>/assets/site.js"
node --check "<学习站目录>/data/catalog.js"
node --check "<学习站目录>/data/lesson-<id>.js"
ffprobe -v error -select_streams v:0 \
  -show_entries stream=codec_name,pix_fmt \
  -of default=nw=1 "<学习站目录>/media/<id>/video.mp4"
```

确认：

- 目录出现新课程且月份分组正确
- 每个章节都有标题、时间码、关键帧和正文
- 说话人显示真实姓名或保守匿名标签
- 点击章节、笔记和原话均能跳转视频
- 播放进度与左右栏宽度刷新后保持
- 视频编码为 `h264`，像素格式为 `yuv420p`

### 7. 预览与交付

```bash
cd "<学习站目录>"
python3 -m http.server 8765 --bind 127.0.0.1
```

打开目录页和 `lesson.html?id=<id>`。需要公开分享时，再使用部署能力发布整个站点目录。

## Fixed design contract

保持以下文件为统一外壳：

- `index.html`
- `lesson.html`
- `assets/site.css`
- `assets/site.js`

保持视觉基线：深色顶栏 `#182233`、蓝色强调 `#3a84ff`、浅灰背景 `#f5f7fa`、左侧目录、双栏学习页。禁止为某门课程添加专属样式或修改布局。

新增内容只改：

- `data/catalog.js`
- `data/lesson-<id>.js`
- `media/<id>/`

## Safety and privacy

- 不读取或打包浏览器 Cookie、API 密钥、`~/.config`、`.env` 或其他凭证。
- 使用云端 ASR 前确认素材允许上传；涉密内容改用本地转录。
- 发布前检查视频、截图和字幕的版权授权。
- 公开仓库不要提交未获授权的第三方视频；包含示例视频时默认使用私有仓库并通过 Git LFS 管理。

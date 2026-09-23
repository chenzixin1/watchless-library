# AI 实践库 · 学习站

把一场分享（视频或链接）变成"边看边读"的学习页：左边视频与章节，右边图文笔记，
播放时右侧自动跟随，点任意段落回到分享现场。

站点风格是固定的。**新增内容只需要跑一条命令，页面本身不用改。**

---

## 目录结构

```
learning-site/
├── index.html          档案页（固定）
├── lesson.html         学习页（固定）
├── assets/
│   ├── site.css        样式（固定）
│   └── site.js         逻辑（固定）
├── data/
│   ├── catalog.js      目录 ← 每次导入自动更新
│   └── lesson-<id>.js  单课数据 ← 每次导入自动生成
├── media/<id>/
│   ├── video.mp4
│   ├── poster.jpg
│   └── frames/         章节关键帧
└── tools/
    └── ingest.py       入库脚本
```

`index.html` / `lesson.html` / `assets/` 是**固定模板**，任何时候都不需要动。

---

## 新增一场分享

前置：视频已经用 Watchless 跑完到 `scenes` 阶段（`work/scene-manifest.json` 存在）。

```bash
cd learning-site

python tools/ingest.py "<Watchless 项目目录>" \
  --id tom-lee-sp8000 \
  --source "CNBC" \
  --speaker "Tom Lee / Jay Woods" \
  --tags "财经,美股"
```

跑完刷新 `index.html` 即可看到新课。

### 参数

| 参数 | 说明 |
|---|---|
| `--id` | 课程 id，只用字母数字和连字符，决定 URL 与媒体目录名 |
| `--title` | 标题，默认取 `work/acquisition.json` |
| `--speaker` | 分享人，默认从 `speaker-map.json` 自动汇总高置信度发言人 |
| `--source` | 来源名，默认按链接域名推导 |
| `--source-url` | 原始链接，默认取 `acquisition.json` 的 `input` |
| `--date` | 日期 `YYYY-MM-DD`，默认今天；**目录按月份自动分组** |
| `--tags` | 逗号分隔标签，参与搜索 |
| `--summary` | 摘要，默认从 `share/*-light-polished.md` 提取首段 |
| `--site` | 站点根目录，默认脚本上一级 |
| `--video` | `auto`（默认）/ `copy` / `transcode` / `skip` |
| `--link` | 同盘时用硬链接代替拷贝，省空间 |

### 关于视频

`--video auto` 会检测编码：浏览器放不了的（如 **AV1**、HEVC）自动转成
h264 + aac + faststart；已经兼容的直接拷贝。

源文件没变时会跳过重复处理，所以改标题、改标签可以放心重跑。

---

## 本地打开

直接双击 `index.html` 就能用（数据以 `.js` 形式加载，不依赖服务器）。

需要局域网分享时：

```bash
python -m http.server 8000
```

---

## 数据来源

`ingest.py` 从 Watchless 项目的这些产物里取内容：

| 来源 | 用途 |
|---|---|
| `work/acquisition.json` | 标题、视频路径、时长、原始链接 |
| `work/scene-manifest.json` | 章节起止时间、关键帧时刻 |
| `work/codex-notes/scene_XXX.md` | 章节标题、解说段落、画面说明 |
| `work/keyframes/scene_XXX_*.jpg` | 章节关键帧 |
| `work/speaker-map.json` | 说话人身份映射 |
| `work/transcript/*_transcript.txt` | 带时间码的原话（"原话"模式） |
| `share/*-light-polished.md` | 内容摘要 |

缺 `codex-notes` 的章节会回退成转录原文，脚本会在结尾提示。

---

## 重新导入同一课

同一个 `--id` 重复导入会**覆盖**该课数据并就地更新目录，不会产生重复条目。
彻底重来就把 `media/<id>/` 和 `data/lesson-<id>.js` 删掉再跑。

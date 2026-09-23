<div align="center">

# Watchless Library

### 把视频变成可阅读、可回看、持续积累的知识库。

给 AI 一个视频链接或本地文件，得到一页「边看边读」的学习笔记。<br>
再给它一个视频，你的知识库就多一条内容。

**视频与笔记联动 · 关键画面 · 中英阅读 · 持续入库**

[快速体验](#快速体验) · [加入自己的视频](#加入自己的视频) · [工作原理](#工作原理) · [Watchless](https://github.com/chenzixin1/watchless)

</div>

---

## 收藏的视频，变成用得上的知识

看完一段访谈、课程或技术分享，过几天想找回某个观点，往往又要拖着进度条寻找。

**Watchless Library 把视频、章节、关键画面和图文笔记放在同一个页面。** 你可以先读笔记了解内容，点击感兴趣的段落回到视频现场，也可以边播放边跟着笔记阅读。处理过的视频会留在同一个目录里，供你继续查找和复习。

它是一个供支持 Skill 的 AI 编程工具使用的工作流，仓库内置处理依赖、网站模板和示例课程。通过对话处理视频，在本地浏览器中阅读成果。

## 打开后，你会得到什么？

| 你想做的事 | Watchless Library 如何帮你 |
| --- | --- |
| 先看懂一段长视频 | 按内容组织章节，用关键画面配合文字笔记阅读 |
| 找回某句话的上下文 | 点击章节、笔记段落或带时间码的原话，跳回对应视频位置 |
| 边看边做理解 | 左侧播放视频，右侧阅读笔记，可开启或关闭播放跟随 |
| 阅读英文内容 | 有对应语言数据时，切换英文原文与中文笔记，选择英文、中文或双语字幕 |
| 中断后继续学习 | 在当前浏览器中保存播放进度与阅读偏好 |
| 把更多视频整理进来 | 复用同一网站，更新目录，按月份浏览、按关键词查找课程 |

### 一套目录，多页学习内容

```text
你的视频链接 / 本地视频
          ↓
   AI 整理章节、关键帧与笔记
          ↓
      Watchless 知识库
          ├── 目录：月份分组 · 关键词查找 · 学习进度
          ├── 视频 A：播放器 ↔ 章节 ↔ 图文笔记
          ├── 视频 B：播放器 ↔ 章节 ↔ 图文笔记
          └── 下一条视频，继续加入这里
```

**每次新增视频，都积累到同一个站点。** 已有课程保留，使用同一课程 ID 重新处理则更新该课程，不会重复添加。

## 适合整理哪些内容？

- **课程与技术分享**：把讲解和关键画面放在一起，按章节回看。
- **访谈与播客**：沿着问题和回答阅读，保留说话人与原话的上下文。
- **论文、行业与知识讲解**：结合图表、资料画面和解释复习观点。
- **产品与操作演示**：围绕步骤和界面状态整理，方便再次照着操作。

## 快速体验

仓库已包含一门约 9 分半的示例课程，带 **13 个场景、视频、关键帧、中英文笔记和三种字幕选项**。可以先体验阅读效果，再配置视频处理环境。

需要 Python 3.10+、Git 和 [Git LFS](https://git-lfs.com/)。安装 Git LFS 后运行：

```bash
git lfs install
git clone https://github.com/chenzixin1/watchless-library.git
cd watchless-library
git lfs pull

python3 scripts/serve.py
```

打开 [本地知识库](http://127.0.0.1:8765/) 或 [示例学习页](http://127.0.0.1:8765/lesson.html?id=tom-lee-sp8000)。这些地址在本机启动服务后可用。

**试着做三件事：** 点击一个章节跳转视频；切换图文笔记的中英文；开启双语字幕。

预览服务只监听本机，支持视频按位置读取，拖动进度条时不必先加载完整视频。仅浏览示例无需安装转录依赖或配置 ASR 密钥。

## 加入自己的视频

### 1. 准备处理环境

除 Python 外，处理视频需要 `ffmpeg`、`ffprobe` 和 Chromium/Chrome。运行以下命令安装隔离的 Python 依赖并检查环境：

```bash
python3 scripts/setup_runtime.py
python3 scripts/doctor.py
```

视频转录还需要配置所选 ASR 服务。依赖安装不会自动配置云端凭证；具体转录要求见 [内置 Watchless 工作流](dependencies/watchless/SKILL.zh-CN.md)。

### 2. 让 AI 加载 Skill，然后给它视频

在 WorkBuddy 等支持加载本地 Skill 的 AI 编程工具中，打开本仓库并加载 [SKILL.md](SKILL.md)。可以直接这样说：

> 使用这个仓库的 Skill，把这个视频加入我的 Watchless 知识库：
> https://www.youtube.com/watch?v=VIDEO_ID
> 复用现有 site，保留已有课程，完成后打开学习页面。

也可以提供本地文件：

> 把 /path/to/my-video.mp4 整理成图文笔记，加入现有知识库。

如需双语内容，可以补充：

> 同时准备英文原文、中文笔记，以及英文、中文和双语字幕。

AI 会依照 Skill 完成转录、语义分段、关键帧选择、笔记整理和入库。**新视频的双语内容需要在处理时生成；切换按钮展示已有语言版本。**

### 3. 下次继续添加

继续提供新视频即可。网站复用相同布局，新内容加入目录；无需为每段视频重新搭建页面。

## 与 Watchless 的关系

[Watchless](https://github.com/chenzixin1/watchless) 提供视频理解与图文文档生成工作流；**Watchless Library 在此基础上提供持续积累的学习网站和视频联动阅读体验。**

本仓库已包含 Watchless、video-use 的依赖源码和网站模板。具体依赖说明见 [第三方声明](THIRD_PARTY_NOTICES.md)。

## 工作原理

```text
视频获取与转录 → 语义分段 → 关键帧选择 → 图文笔记 → 课程入库 → 更新目录
```

内容处理由 AI 工具与脚本配合完成，阅读站点使用静态 HTML、CSS 和 JavaScript。站点本身无需数据库，课程数据和媒体文件保存在本地目录中。

<details>
<summary><strong>命令行用法与仓库结构</strong></summary>

### 准备视频

```bash
python3 scripts/run_watchless.py --cwd "$PWD" \
  "https://www.youtube.com/watch?v=VIDEO_ID" --stage prepare
```

`prepare` 是准备阶段；完整流程还需按 [SKILL.md](SKILL.md) 完成后续场景、选帧和笔记处理。

### 将处理结果加入站点

```bash
python3 scripts/ingest.py "/path/to/watchless-project" \
  --site "$PWD/site" \
  --id lesson-id \
  --source "来源" \
  --speaker "讲者" \
  --tags "标签1,标签2"
```

同一 `--id` 重跑会覆盖更新，不会重复添加。目录默认按入库月份分组。

### 仓库结构

| 路径 | 用途 |
| --- | --- |
| `SKILL.md` | AI 工具使用的端到端工作流 |
| `dependencies/` | 内置 Watchless 与 video-use |
| `assets/site-template/` | 统一网站模板 |
| `scripts/` | 环境准备、处理、入库、检查与本地服务 |
| `site/` | 可运行的学习网站与示例课程 |
| `site/data/` | 总目录与每门课程的数据 |
| `site/media/` | 视频、封面、关键帧与可选语言数据 |

新增课程只更新目录、课程数据和对应媒体文件。`index.html`、`lesson.html`、`assets/site.css` 和 `assets/site.js` 作为统一外壳复用。

</details>

## 使用说明

- **转录与翻译**：可能包含识别或翻译误差，关键内容请回看原视频核对。示例字幕的分句时间为估算，并非逐词校准。
- **本地与云端**：阅读站点在本地运行；使用云端 ASR 时，音频会发送至所配置的服务。涉密素材应使用合适的本地转录方案。
- **学习进度**：保存在当前浏览器中，暂不提供账号或跨设备同步。
- **素材授权**：只处理拥有或已获授权的内容。示例包含第三方公开视频素材，供学习和工作流验证；公开传播前请确认授权范围。
- **凭证与许可**：仓库不包含 API 密钥、Cookie 或本机配置。Watchless 与 video-use 采用 MIT License，详见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) 及依赖目录内的许可证。

---

**从一段视频开始，慢慢积累成自己的知识库。**

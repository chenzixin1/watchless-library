# Watchless Library 站点目录

这里是可运行的学习站实例。`index.html` 是文章目录，`lesson.html` 展示视频、全片要点、章节与图文笔记。新增视频时由 Watchless Library Skill 处理素材并入库；已有课程会保留。

## 本地预览

在安装了本 Skill 的仓库根目录运行：

```bash
python3 scripts/serve.py --directory /path/to/learning-site --port 8765
```

将 `/path/to/learning-site` 换成本站点目录，然后打开 `http://127.0.0.1:8765/index.html`。预览服务仅监听本机，并支持视频按位置读取。直接双击 HTML 文件不能完整验证加载、跳播等行为。

## 新增视频

最简单的方式是在 AI 编程工具中加载仓库根目录的 `SKILL.md`，然后发送 YouTube 链接或本地视频文件。Skill 会接续转录、章节、笔记、字幕、全片总结、入库和浏览器检查。

如果已有处理完的 Watchless 项目，也可以从本站点目录手动入库：

```bash
python3 tools/ingest.py "/path/to/watchless-project" \
  --site "$PWD" --id lesson-id --source "来源" --speaker "讲者"
```

项目需要包含已核对的章节、关键帧和场景笔记；请求的语言版本与全片总结也要准备齐全。完整输入和交付检查以仓库根目录的 `SKILL.md` 为准。同一 `--id` 重新入库会更新原课程，不会产生重复目录项。

## 文件结构

| 路径 | 用途 |
| --- | --- |
| `index.html`、`lesson.html`、`assets/` | 所有课程共用的页面与样式 |
| `data/catalog.js` | 文章目录 |
| `data/lesson-<id>.js` | 一门课程的章节、笔记和字幕数据 |
| `media/<id>/` | 视频、关键画面和全片总结 |
| `tools/ingest.py` | 将处理结果写入本站点 |

本仓库的公开版本包含一门可播放示例课程。另三门课程的文章数据和截图可阅读，视频文件仅保存在作者本机；如需播放，请放入对应 `media/<id>/video.mp4`，或使用文章中的原视频链接。

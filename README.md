# Watchless Library

把视频链接或本地视频文件转换成可持续累积的“边看边读”学习网站。

仓库包含完整 WorkBuddy Skill、Watchless 与 video-use 依赖源码、固定网站模板，以及一门已经生成好的示例课程。克隆后无需重新设计页面；以后每增加一段视频，只生成课程数据和媒体目录，并自动更新总目录。

## 已包含内容

- `SKILL.md`：端到端 Skill 工作流
- `dependencies/watchless/`：视频转录、语义分段、关键帧与图文笔记流水线
- `dependencies/video-use/`：Watchless 使用的转录打包和时间线查看工具
- `assets/site-template/`：固定风格网站模板
- `scripts/`：运行环境、Watchless 启动、站点初始化、课程入库和自检脚本
- `site/`：可直接打开的完整站点实例
- `site/data/lesson-tom-lee-sp8000.js`：当前课程结构化内容
- `site/media/tom-lee-sp8000/`：当前课程视频、封面与 13 张关键帧

## 快速开始

```bash
# 1. 建立隔离运行环境
python3 scripts/setup_runtime.py

# 2. 检查依赖与示例站点
python3 scripts/doctor.py

# 3. 预览已打包的网站
cd site
python3 -m http.server 8765 --bind 127.0.0.1
```

浏览器打开：

- 目录页：`http://127.0.0.1:8765/`
- 示例课程：`http://127.0.0.1:8765/lesson.html?id=tom-lee-sp8000`

## 新增视频

先让 WorkBuddy 加载本仓库的 `SKILL.md`。Skill 会按以下顺序处理：

1. 接收视频链接或本地视频文件
2. 用内置 Watchless 完成转录、路由、语义分段、选帧和图文笔记
3. 用 `scripts/ingest.py` 将结果写入 `site/`
4. 更新 `site/data/catalog.js`
5. 验证播放器、章节、笔记、关键帧和资源引用

手动运行 Watchless：

```bash
python3 scripts/run_watchless.py --cwd "$PWD" \
  "https://www.youtube.com/watch?v=VIDEO_ID" --stage prepare
```

将完整 Watchless 项目加入站点：

```bash
python3 scripts/ingest.py "/path/to/watchless-project" \
  --site "$PWD/site" \
  --id lesson-id \
  --source "来源" \
  --speaker "讲者" \
  --tags "标签1,标签2"
```

同一 `--id` 重跑会覆盖更新，不会重复添加。目录默认按入库月份分组。

## 固定设计约束

`site/index.html`、`site/lesson.html`、`site/assets/site.css` 和 `site/assets/site.js` 是固定外壳。新增课程只更新：

- `site/data/catalog.js`
- `site/data/lesson-<id>.js`
- `site/media/<id>/`

不要为单个课程修改固定模板。

## Git LFS

示例视频通过 Git LFS 管理。克隆仓库前请确保已安装 Git LFS：

```bash
git lfs install
git clone <repo-url>
```

## 隐私与版权

- 仓库不包含任何 API 密钥、Cookie 或本机配置文件。
- Watchless 的云端 ASR 会向配置的语音识别服务上传音频；涉密视频应改用本地转录方案。
- 示例课程包含第三方公开视频素材，仅供内部学习和工作流验证。公开传播前应自行确认版权与授权范围。

## 第三方许可

Watchless 与 video-use 均采用 MIT License。详见 `THIRD_PARTY_NOTICES.md` 和各依赖目录中的许可证文件。

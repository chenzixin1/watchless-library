# 安全审计报告

## 执行摘要

- **审计对象**：`watchless-library` 完整 Skill 仓库
- **审计时间**：2026-09-23
- **审计范围**：根 `SKILL.md`、所有脚本、固定站点、课程数据、内置 Watchless 与 video-use 源码、文档和许可证
- **发现问题总数**：0 个阻断或需确认问题
  - P0 阻断级：0
  - P1 需关注：0
- **安全评分**：94/100
- **结论**：P2，可使用；涉及云端转录和第三方视频版权时需遵守项目中的隐私与版权说明

## P0 阻断级风险发现

未发现 P0 风险。

- 未发现 `curl | bash`、下载后执行、动态 `eval`、`shell=True` 或提权后执行危险命令。
- 未发现读取 SSH、云厂商凭证等敏感文件后向无关目标发送的组合行为。
- 未发现针对用户目录、系统目录或仓库外路径的自动破坏性删除。

## P1 需关注风险发现

未发现 P1 风险。

- `scripts/setup_runtime.py` 只在仓库自己的 `.runtime/venv` 中安装 PyPI 依赖，不做全局安装。
- 内置第三方文档中存在 `brew install`、`pip install` 示例，但不会由本 Skill 自动执行。
- 仓库使用 Git LFS 管理示例视频，不执行来源不明的安装脚本。

## 详细检查结果

### 命令执行检查

发现的命令执行均使用参数数组，不经过 shell 拼接：

- `scripts/setup_runtime.py`：创建 venv 并调用该 venv 的 pip
- `scripts/run_watchless.py`：调用仓库内置 Watchless 脚本
- `scripts/ingest.py`：调用 `ffprobe` / `ffmpeg` 检查和转码用户指定视频
- `scripts/doctor.py`：只读调用 `ffprobe` 做编码检查
- 内置 Watchless / video-use：调用 ffmpeg、ffprobe、yt-dlp、浏览器完成视频处理与 PDF 输出

未发现 `os.system`、`shell=True`、运行时下载脚本或混淆执行。

### 敏感路径与凭证检查

- 仓库未包含真实 `.env`、密钥、Cookie、私钥、云账号配置或浏览器状态。
- Watchless 可从环境变量或仓库外的 `~/.config/watchless/tencent.json` 读取腾讯云 ASR 凭证，只用于调用腾讯云 ASR，不打印或归档密钥。
- video-use 的独立转录辅助工具可读取 ElevenLabs Key，但本 Skill 主流程不调用该转录路径。
- `.gitignore` 排除 `.env`、`.runtime`、密钥文件和临时输出。

### 网络请求检查

允许的网络目标及用途：

- 视频来源链接：由 yt-dlp 下载用户明确提供的视频
- 腾讯云 ASR：上传音频做转录
- 火山引擎 ASR：仅在用户明确选择该 provider 时使用
- ElevenLabs：仅在单独运行 video-use 转录工具时使用
- PyPI：由 `setup_runtime.py` 安装声明的 Python 依赖

未发现隐蔽遥测、未知域名回传或动态拼接凭证到非预期目标。

### 文件操作检查

- 删除操作仅针对仓库自身 `.runtime/`、课程媒体目标目录、临时音频/拼接文件和可重新生成的输出。
- 不递归清理 Desktop、Downloads、Documents、Home 或系统目录。
- `scripts/init_site.py` 默认保留现有课程数据；只有显式 `--refresh-template` 才更新固定 HTML/CSS/JS。

### 依赖安装风险检查

- Python 依赖安装在 `SKILL_ROOT/.runtime/venv`，不污染全局环境。
- 依赖来自 PyPI 官方索引和仓库内置的 video-use 源码。
- 系统命令 ffmpeg、ffprobe 和 Chrome 只检测，不自动执行系统级安装。

### 元数据检查

- 根 Skill 名称符合小写连字符规范：`watchless-library`
- `description` 明确说明输入、产出、触发场景和内置能力
- `agent_created: true` 已设置
- 无占位符、异常重复字符或伪装描述

### 描述与实际行为一致性

一致。Skill 描述的视频处理、语义分段、关键帧、图文笔记、播放器联动、目录累积和固定模板均有对应脚本或资源。当前示例站点包含 1 门课程、13 个章节、13 张关键帧和浏览器兼容的 H.264 视频。

## 总体建议

1. 默认保持 GitHub 仓库为私有，因为示例课程包含第三方公开视频素材。
2. 公开发布前移除或替换未确认再分发权利的视频文件。
3. 处理涉密视频时不要使用云端 ASR，改用本地转录方案。
4. 定期更新并重新审计 yt-dlp、腾讯云 SDK 和其他 Python 依赖。

## 审计结论

**风险等级：P2 — 可以使用。**

Skill 未发现供应链投毒模式、全局环境破坏、凭证泄露或跨目录破坏行为。保留的风险属于视频处理本身的正常外部交互：云端转录、网络视频下载和媒体版权。

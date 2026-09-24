# 交付验收

## 约定

`work/delivery-requirements.json` 保存 provider、complete_notes、require_emphasis、require_speaker_labels、require_video_summary、note_languages、subtitle_tracks 和 existing_lesson_ids。创建后沿用用户要求，只有用户改变需求时才调整。中文主笔记位于 codex-notes，英文笔记位于 localization.notes.en；字幕三轨均位于 localization.subtitles。全片要点位于 `work/video-summary.json`，每条包含 `scenes` 及对应语言文本。

## 检查

```bash
python3 scripts/check_delivery.py "$PROJECT_DIR" --site "$SITE" --id "$LESSON_ID"
```

按 next_checkpoint 继续处理。`video_summary` 验证有 3–12 条要点、中英文文本、章节编号覆盖全片，且入库数据与来源一致；人工核对要点确实概括了整段视频。`emphasis` 检查每章的中英文笔记是否有 `**...**` 正文重点标记；段首加粗的说话人标签不计入正文重点。它只能检查标记存在，不能判断是否抓对了关键数字、金句、事实或观点，须人工抽查。`speaker_labels` 逐章检查访谈入库数据是否保留了结构化说话人，且“主持人问：”“嘉宾回答：”等前缀没有残留在普通正文；身份仍须人工核对。下载检查是文件存在检查，首次获取仍须用 ffprobe 确认完整时长及音视频轨道。机器检查不能判断翻译语义、截帧质量或说话人身份，须按 Skill 主流程人工复核。

## 浏览器检查

实际打开目标课程：确认标题；播放；跳到中段和末段；检查播放器下方的全片 bullet 要点，切换中文/英文笔记后要点也应切换；抽查重点在页面里显示为真正的粗体，且原始转录没有被整体加粗；访谈还要确认“主持人问：”“嘉宾回答：”等说话人完整标签（包括冒号）为粗体加下划线，读取页面计算样式并记录样本，不能只看 Markdown 源码；逐个切换英文、中文、双语字幕并确认画面显示；关闭字幕；返回目录确认新旧课程。不能仅看选项标签就通过。遇到浏览器缓存应刷新并核对实际加载标题和语言数据。

完成后读取最新检查报告的 fingerprint，创建 work/browser-check.json：

```json
{
  "fingerprint": "复制本次检查报告的真实指纹",
  "checks": {"playback": true, "seek": true, "note_languages": true, "video_summary_visible": true, "subtitle_tracks": true, "bilingual_visible": true, "emphasis_visible": true, "speaker_labels_visible": true, "catalog": true},
  "speaker_label_samples": [{"text": "主持人问：", "font_weight": "700", "text_decoration_line": "underline"}, {"text": "嘉宾回答：", "font_weight": "700", "text_decoration_line": "underline"}],
  "evidence": "实际 URL、检查时间、已观察到的字幕/跳转位置以及截图路径（如有）"
}
```

这是操作者对真实浏览器操作的记录，不是自动浏览器测试结果；未执行的项保留 false。单语任务 bilingual_visible 表示已核对请求的字幕表现，在 evidence 说明单语约定。禁止预先填写通过。再次运行检查，所有检查点均通过才可宣布该课程完成。多视频任务只有全部课程通过后才可宣布整体完成。

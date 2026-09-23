"""摘要提取要跳过 Watchless 文稿里单独成段的配图。"""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "ingest.py"


def load_ingest():
    spec = importlib.util.spec_from_file_location("ingest", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


LIGHT = """# Tom Lee's Case for S&P 8,000 This Month - Light Plus

## 01. 开场（00:00-00:41）

![场景 1](<keyframes/scene_001_00-00-38.jpg>)

Brian（CNBC 主持人）：Tom Lee, also a CNBC contributor today, certainly is——kind of a face ripper，不只是股票，加密货币也是。我们一会儿再聊那个。我是不是错过了什么催化剂？发生了什么？

Tom Lee：你知道，Brian，我认为上周是 maximum pain。
"""


def test_summary_skips_watchless_image_block():
    module = load_ingest()
    summary = module.summary_from_markdown(LIGHT)
    assert summary.startswith("Brian（CNBC 主持人）：")
    assert "![" not in summary
    assert "keyframes/" not in summary
    assert "face ripper" in summary


def test_extract_summary_reads_light_polished_file(tmp_path):
    module = load_ingest()
    share = tmp_path / "share"
    share.mkdir()
    (share / "demo-light-polished.md").write_text(LIGHT, encoding="utf-8")
    (share / "notes.md").write_text("这段不该被读到，因为它不是 light-polished 稿。", encoding="utf-8")
    assert module.extract_summary(tmp_path) == module.summary_from_markdown(LIGHT)


def test_summary_skips_headings_lists_and_short_lines():
    module = load_ingest()
    text = "\n\n".join([
        "# 标题",
        "- 列表项列表项列表项列表项列表项",
        "> 引用引用引用引用引用引用引用引用引用",
        "太短",
        "这是第一段足够长的正文，用来确认标题、列表、引用以及过短的段落都会被跳过，不会被当成摘要。",
    ])
    assert module.summary_from_markdown(text).startswith("这是第一段足够长的正文")


def test_extract_summary_missing_share_is_empty(tmp_path):
    module = load_ingest()
    assert module.extract_summary(tmp_path) == ""


def test_packaged_lesson_summary_is_prose():
    lesson = (ROOT / "site" / "data" / "lesson-tom-lee-sp8000.js").read_text(encoding="utf-8")
    assert "![场景 1]" not in lesson
    assert "keyframes/scene_001" not in lesson
    assert "Brian（CNBC 主持人）：" in lesson

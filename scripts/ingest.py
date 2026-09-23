#!/usr/bin/env python3
"""把一个 Watchless 项目导入学习站。

用法：
    python tools/ingest.py <watchless项目目录> [选项]

    --id        课程 id（默认从来源推导，仅允许字母数字与连字符）
    --title     标题（默认取 acquisition.json）
    --speaker   分享人（默认从 speaker-map.json 自动汇总）
    --source    来源名称（如 CNBC / 内部分享）
    --source-url 原始链接
    --date      日期 YYYY-MM-DD（默认今天）
    --tags      逗号分隔标签
    --summary   内容摘要（默认尝试从 share/*-light-polished.md 提取）
    --site      站点根目录（默认为本脚本所在目录的上一级）
    --video     auto | copy | transcode | skip（默认 auto：浏览器不支持的编码自动转码）
    --link      用硬链接代替拷贝视频（同盘时省空间）

幂等：同一个 --id 重复导入会覆盖课程数据与媒体，并就地更新目录，不会产生重复条目。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

SLUG_RE = re.compile(r"[^a-z0-9]+")
WHO_RE = re.compile(r"^(.{1,24}?)[：:]\s*(.+)$", re.S)
ROLE_RE = re.compile(r"^(.*?)\s*[（(]([^）)]*)[）)]\s*$", re.S)
CUE_RE = re.compile(r"^\[([\d.]+)s\s*-\s*([\d.]+)s\]\s*([^:]+):\s*(.*)$")


def log(msg: str) -> None:
    print(f"  {msg}", flush=True)


def die(msg: str) -> None:
    print(f"错误：{msg}", file=sys.stderr)
    sys.exit(1)


def slugify(value: str) -> str:
    out = SLUG_RE.sub("-", value.lower()).strip("-")
    return out or "lesson"


def split_speaker(text: str, speakers: dict, known_names: set) -> dict:
    """把 '说话人0：xxx' / 'Brian（CNBC 主持人）：xxx' / 'Tom Lee：xxx' 拆成结构化段落。

    只有明确识别为发言人的前缀才会被剥离，否则整段原样保留——
    避免把正文里的冒号（如「……泼点冷水：能源」）误判成发言人。
    """
    m = WHO_RE.match(text)
    if not m:
        return {"text": text}
    head, body = m.group(1).strip(), m.group(2).strip()
    if not body or len(head) > 24:
        return {"text": text}

    name = role = ""
    mapped = speakers.get(head)
    if mapped:
        name, role = mapped.get("name") or head, mapped.get("role_short") or ""
    else:
        r = ROLE_RE.match(head)
        if r and r.group(1).strip():
            name, role = r.group(1).strip(), r.group(2).strip()
        elif head in known_names or re.fullmatch(r"[A-Za-z][A-Za-z .\-']{1,22}", head):
            name = head

    if not name:
        return {"text": text}

    block = {"speaker": name, "text": body}
    if role:
        block["role"] = role
    return block


def parse_note(path: Path) -> dict:
    """解析 codex-notes/scene_XXX.md。"""
    raw = path.read_text(encoding="utf-8")
    sections: dict[str, list[str]] = {}
    current = None
    for line in raw.splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            current = m.group(1).strip()
            sections[current] = []
            continue
        if current:
            sections[current].append(line)

    def body(*names):
        for name in names:
            if name in sections:
                return "\n".join(sections[name]).strip()
        return ""

    title = body("标题", "Title")
    dialogue = body("Light-plus", "完整内容", "Dialogue")
    visual = body("Visual explainer", "画面说明", "Visual")
    return {
        "title": " ".join(title.split()),
        "dialogue": [p.strip() for p in re.split(r"\n\s*\n", dialogue) if p.strip()],
        "visual": " ".join(visual.split()),
    }


def parse_cues(transcript_txt: Path, speakers: dict) -> list[dict]:
    if not transcript_txt or not transcript_txt.exists():
        return []
    cues = []
    for line in transcript_txt.read_text(encoding="utf-8").splitlines():
        m = CUE_RE.match(line.strip())
        if not m:
            continue
        start, end, who, text = float(m.group(1)), float(m.group(2)), m.group(3).strip(), m.group(4).strip()
        if not text:
            continue
        mapped = speakers.get(who, {})
        cues.append({
            "start": round(start, 2),
            "end": round(end, 2),
            "speaker": mapped.get("name", who),
            "text": text,
        })
    return cues


def load_speakers(path: Path) -> dict:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    out = {}
    for key, info in (data.get("speakers") or {}).items():
        if not isinstance(info, dict):
            continue
        display = info.get("display_name") or key
        m = ROLE_RE.match(display)
        if m and m.group(1).strip():
            out[key] = {"name": m.group(1).strip(), "role_short": m.group(2).strip()}
        else:
            out[key] = {"name": display}
        out[key]["confidence"] = info.get("confidence", "")
    return out


def probe_codec(video: Path) -> tuple[str, str]:
    try:
        res = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=codec_name,pix_fmt", "-of", "json", str(video)],
            capture_output=True, text=True, check=True,
        )
        stream = (json.loads(res.stdout).get("streams") or [{}])[0]
        return stream.get("codec_name", ""), stream.get("pix_fmt", "")
    except Exception:
        return "", ""


def browser_safe(video: Path) -> bool:
    codec, pix = probe_codec(video)
    return codec in {"h264", "avc1"} and pix in {"yuv420p", "yuvj420p"}


def run_ffmpeg(args: list[str], label: str) -> None:
    res = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], capture_output=True, text=True)
    if res.returncode != 0:
        die(f"{label} 失败：{res.stderr.strip()[:400]}")


def video_ready(media_dir: Path, src: Path) -> bool:
    """视频已按同一源文件处理过，则跳过重复转码/拷贝。"""
    target = media_dir / "video.mp4"
    meta = media_dir / ".source-meta.json"
    if not target.exists() or not meta.exists():
        return False
    try:
        rec = json.loads(meta.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False
    st = src.stat()
    return rec.get("size") == st.st_size and abs(float(rec.get("mtime") or 0) - st.st_mtime) < 1


def remember_video(media_dir: Path, src: Path, action: str) -> None:
    st = src.stat()
    (media_dir / ".source-meta.json").write_text(
        json.dumps({"source": str(src), "size": st.st_size, "mtime": st.st_mtime, "action": action},
                   ensure_ascii=False, indent=1),
        encoding="utf-8",
    )


def copy_video(src: Path, dst: Path, mode: str, use_link: bool) -> str:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        dst.unlink()

    if mode == "skip":
        return ""

    need_transcode = mode == "transcode" or (mode == "auto" and not browser_safe(src))
    if need_transcode:
        log(f"转码为浏览器兼容格式（h264 + aac + faststart）…")
        run_ffmpeg(
            ["-i", str(src), "-c:v", "libx264", "-preset", "veryfast", "-crf", "24",
             "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
             "-movflags", "+faststart", str(dst)],
            "视频转码",
        )
        return "transcoded"

    if use_link:
        try:
            os.link(src, dst)
            return "linked"
        except OSError:
            pass
    shutil.copy2(src, dst)
    return "copied"


def make_poster(video: Path, dst: Path, fallback: Path | None) -> bool:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        dst.unlink()
    try:
        dur = float(subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", str(video)],
            capture_output=True, text=True, check=True).stdout.strip())
    except Exception:
        dur = 0.0
    if dur > 0:
        res = subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{dur * 0.12:.2f}", "-i", str(video),
             "-frames:v", "1", "-vf", "scale=1280:-2", str(dst)],
            capture_output=True, text=True,
        )
        if res.returncode == 0 and dst.exists():
            return True
    if fallback and fallback.exists():
        shutil.copy2(fallback, dst)
        return True
    return False


# Watchless light-polished 稿在每段正文前单独放一张图：
# ![场景 1](<keyframes/scene_001_00-00-38.jpg>)
IMAGE_RE = re.compile(r"!\[[^\]]*\](?:\(<[^>\n]+>\)|\([^)\n]*\))")
TAG_RE = re.compile(r"<[^>\n]+>")


def summary_from_markdown(text: str) -> str:
    """取第一段真正的正文。跳过标题、列表、引用，以及单独成段的配图。"""
    for block in re.split(r"\n\s*\n", text):
        cleaned = TAG_RE.sub(" ", IMAGE_RE.sub(" ", block))
        flat = " ".join(cleaned.split())
        if not flat or flat.startswith(("#", "-", ">", "|", "`")):
            continue
        if len(flat) < 40:
            continue
        return flat[:400]
    return ""


def extract_summary(project: Path) -> str:
    share = project / "share"
    if not share.exists():
        return ""
    for candidate in sorted(share.glob("*-light-polished.md")):
        summary = summary_from_markdown(candidate.read_text(encoding="utf-8"))
        if summary:
            return summary
    return ""


JS_HEADER = "/* 由 tools/ingest.py 自动生成，请勿手动编辑。 */\n"


def write_js(path: Path, global_name: str, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(payload, ensure_ascii=False, indent=1)
    path.write_text(f"{JS_HEADER}window.{global_name} = {body};\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description="把 Watchless 项目导入学习站")
    ap.add_argument("project", help="Watchless 项目目录（含 work/ 与 share/）")
    ap.add_argument("--id")
    ap.add_argument("--title")
    ap.add_argument("--speaker")
    ap.add_argument("--source")
    ap.add_argument("--source-url")
    ap.add_argument("--date", default=date.today().isoformat())
    ap.add_argument("--tags", default="")
    ap.add_argument("--summary")
    ap.add_argument("--site")
    ap.add_argument("--video", default="auto", choices=["auto", "copy", "transcode", "skip"])
    ap.add_argument("--link", action="store_true")
    args = ap.parse_args()

    project = Path(args.project).expanduser().resolve()
    if not project.is_dir():
        die(f"项目目录不存在：{project}")

    work = project / "work"
    if args.site:
        site = Path(args.site).expanduser().resolve()
    else:
        candidates = [
            Path.cwd(),
            Path.cwd() / "learning-site",
            Path(__file__).resolve().parents[1],
            Path(__file__).resolve().parents[2] / "learning-site",
        ]
        site = next((c for c in candidates if (c / "assets" / "site.js").exists()), None)
        if site is None:
            die("未找到站点目录（缺少 assets/site.js）。请在站点内运行，或用 --site 指定。")
    site = site.resolve()
    if not (site / "assets" / "site.js").exists():
        die(f"站点目录无效（缺少 assets/site.js）：{site}")

    # ---------- 读取源数据 ----------
    acq_path = work / "acquisition.json"
    acq = json.loads(acq_path.read_text(encoding="utf-8")) if acq_path.exists() else {}
    manifest_path = work / "scene-manifest.json"
    if not manifest_path.exists():
        die(f"缺少 work/scene-manifest.json，请先跑完 Watchless 的 scenes 阶段：{manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    video_src = Path(acq["local_video"]) if acq.get("local_video") else None
    if video_src and not video_src.exists():
        video_src = None
    if video_src is None:
        found = sorted((work / "source").glob("*.mp4")) + sorted((work / "source").glob("*.mov"))
        video_src = found[0] if found else None

    title = args.title or acq.get("title") or project.name
    lesson_id = args.id or slugify(acq.get("video_id") or title)

    speakers = load_speakers(work / "speaker-map.json")
    known_names = {info["name"] for info in speakers.values() if info.get("name")}

    auto_speakers = []
    for key, info in speakers.items():
        if info.get("confidence") == "high" and info.get("name") and key != "说话人2":
            name = info["name"]
            if name not in auto_speakers:
                auto_speakers.append(name)
    speaker = args.speaker or " / ".join(auto_speakers) or "分享人未记录"

    source_url = args.source_url or (acq.get("input") if str(acq.get("input", "")).startswith("http") else "")
    source = args.source or ""
    if not source:
        if source_url:
            source = urlparse(source_url).netloc.replace("www.", "") or "原始视频"
        else:
            source = "本地视频"

    # ---------- 组装 scenes ----------
    kf_dir = work / "keyframes"
    notes_dir = work / "codex-notes"
    scenes, missing_notes = [], []

    for scene in manifest.get("scenes", []):
        no = int(scene.get("id", len(scenes) + 1))
        stems = f"scene_{no:03d}"
        note_path = notes_dir / f"{stems}.md"
        note = parse_note(note_path) if note_path.exists() else {"title": "", "dialogue": [], "visual": ""}
        if not note_path.exists():
            missing_notes.append(stems)

        # 关键帧：优先取 manifest 里选定的那张
        frame_name = ""
        chosen = scene.get("frame_path")
        if chosen and Path(chosen).name in {p.name for p in kf_dir.glob(f"{stems}_*.jpg")}:
            frame_name = Path(chosen).name
        else:
            options = sorted(kf_dir.glob(f"{stems}_*.jpg"))
            if options:
                frame_name = options[0].name

        paragraphs = []
        for raw_para in note["dialogue"]:
            paragraphs.append(split_speaker(raw_para, speakers, known_names))
        if not paragraphs and scene.get("transcript_text"):
            paragraphs = [{"text": scene["transcript_text"]}]

        scenes.append({
            "no": no,
            "title": note["title"] or f"章节 {no:02d}",
            "start": round(float(scene.get("start_sec") or 0), 2),
            "end": round(float(scene.get("end_sec") or 0), 2),
            "frameTime": round(float(scene.get("frame_timestamp_sec") or scene.get("start_sec") or 0), 2),
            "image": f"media/{lesson_id}/frames/{stems}.jpg" if frame_name else "",
            "visual": note["visual"],
            "paragraphs": paragraphs,
            "_frame_src": str(kf_dir / frame_name) if frame_name else "",
        })

    duration = float(acq.get("duration_sec") or (scenes[-1]["end"] if scenes else 0))
    summary = args.summary if args.summary is not None else extract_summary(project)

    # ---------- 拷贝媒体 ----------
    media_dir = site / "media" / lesson_id
    frames_dir = media_dir / "frames"
    if frames_dir.exists():
        shutil.rmtree(frames_dir)
    frames_dir.mkdir(parents=True, exist_ok=True)

    frame_count = 0
    for scene in scenes:
        src = scene.pop("_frame_src", "")
        if not src:
            continue
        shutil.copy2(src, frames_dir / Path(scene["image"]).name)
        frame_count += 1

    video_rel = ""
    if video_src and args.video != "skip":
        if args.video == "auto" and video_ready(media_dir, video_src):
            log("视频与上次一致，跳过处理")
            video_rel = f"media/{lesson_id}/video.mp4"
        else:
            log(f"处理视频：{video_src.name}")
            action = copy_video(video_src, media_dir / "video.mp4", args.video, args.link)
            if action:
                video_rel = f"media/{lesson_id}/video.mp4"
                remember_video(media_dir, video_src, action)
                log(f"视频就绪（{action}）")
    elif args.video == "skip":
        log("按参数跳过视频")
    else:
        log("警告：未找到视频文件，课程将没有播放器")

    poster_rel = ""
    first_frame = next((site / s["image"] for s in scenes if s.get("image")), None)
    if video_src and (media_dir / "video.mp4").exists():
        if make_poster(media_dir / "video.mp4", media_dir / "poster.jpg", first_frame):
            poster_rel = f"media/{lesson_id}/poster.jpg"
    elif first_frame and first_frame.exists():
        shutil.copy2(first_frame, media_dir / "poster.jpg")
        poster_rel = f"media/{lesson_id}/poster.jpg"

    # ---------- 写课程数据 ----------
    cues = parse_cues(
        next(iter((work / "transcript").glob("*_transcript.txt")), None) if (work / "transcript").exists() else None,
        speakers,
    )

    lesson = {
        "id": lesson_id,
        "title": title,
        "speaker": speaker,
        "source": source,
        "sourceUrl": source_url,
        "date": args.date,
        "month": args.date[:7],
        "duration": round(duration, 2),
        "summary": summary,
        "video": video_rel,
        "poster": poster_rel,
        "tags": [t.strip() for t in args.tags.split(",") if t.strip()],
        "scenes": scenes,
        "cues": cues,
    }
    write_js(site / "data" / f"lesson-{lesson_id}.js", "__LESSON__", lesson)

    # ---------- 更新目录 ----------
    catalog_path = site / "data" / "catalog.js"
    site_meta = {"brand": "AI 实践库", "subtitle": "技术运营 · 视频与图文笔记"}
    lessons = []
    if catalog_path.exists():
        raw = catalog_path.read_text(encoding="utf-8")
        m = re.search(r"window\.__CATALOG__\s*=\s*(\{.*\});\s*$", raw, re.S)
        if m:
            try:
                existing = json.loads(m.group(1))
                site_meta = existing.get("site") or site_meta
                lessons = existing.get("lessons") or []
            except json.JSONDecodeError:
                log("警告：目录文件解析失败，将重建")

    entry = {
        "id": lesson_id,
        "title": title,
        "speaker": speaker,
        "source": source,
        "sourceUrl": source_url,
        "date": args.date,
        "month": args.date[:7],
        "duration": round(duration, 2),
        "sceneCount": len(scenes),
        "cueCount": len(cues),
        "poster": poster_rel,
        "tags": lesson["tags"],
        "addedAt": args.date,
    }

    # 去掉重复项，并清理孤儿条目（课程数据文件已被删除的）
    kept = []
    for item in lessons:
        other = item.get("id")
        if not other or other == lesson_id:
            continue
        if not (site / "data" / f"lesson-{other}.js").exists():
            log(f"清理孤儿条目：{other}（课程数据文件不存在）")
            continue
        kept.append(item)
    lessons = kept
    lessons.append(entry)

    def sort_key(item):
        return (str(item.get("date") or ""), str(item.get("id") or ""))

    lessons.sort(key=sort_key, reverse=True)
    for i, item in enumerate(lessons, start=1):
        item["order"] = len(lessons) - i + 1

    write_js(catalog_path, "__CATALOG__", {"site": site_meta, "lessons": lessons})

    # ---------- 汇报 ----------
    print()
    print(f"课程已导入：{lesson_id}")
    print(f"  标题      {title}")
    print(f"  分享人    {speaker}")
    print(f"  日期      {args.date}（{lesson['month']}）")
    print(f"  章节      {len(scenes)} 个")
    print(f"  原话      {len(cues)} 条")
    print(f"  关键帧    {frame_count} 张")
    print(f"  视频      {video_rel or '（无）'}")
    print(f"  摘要      {'有' if summary else '（无）'}")
    print(f"  目录      {len(lessons)} 门课")
    if missing_notes:
        print(f"  提示      以下章节缺少 codex-notes 笔记，已回退为转录原文：{', '.join(missing_notes)}")
    print()
    print(f"打开 {site / 'index.html'}")


if __name__ == "__main__":
    main()

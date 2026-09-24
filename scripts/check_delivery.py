#!/usr/bin/env python3
"""Validate a lesson's delivery checkpoints; never infer completion from ASR alone."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

from ingest import has_content_emphasis, load_catalog, load_speakers, parse_cues, parse_note, split_speaker, validate_delivery, validate_lesson_id


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def js_data(path):
    match = re.search(r'window\.__LESSON__\s*=\s*(\{.*\});\s*$', path.read_text(), re.S)
    if not match:
        raise ValueError('课程数据无法解析')
    return json.loads(match.group(1))


def inspect(project, site, lesson_id):
    work = project / 'work'
    req = read(work / 'delivery-requirements.json')
    results = []
    def check(name, action):
        try:
            action()
            results.append({'checkpoint': name, 'passed': True})
        except (ValueError, OSError, KeyError, TypeError, AssertionError) as error:
            results.append({'checkpoint': name, 'passed': False, 'reason': str(error) or '缺少必要产物'})
    def acquisition():
        data = read(work / 'acquisition.json')
        assert Path(data['local_video']).is_file(), '缺少视频文件'
        assert Path(data['local_video']).stat().st_size > 0, '视频文件为空'
    def transcript():
        state = read(work / 'run-state.json')
        cues = parse_cues(Path(state['transcript']), {})
        assert cues, '带时间码转录为空'
        run = 1
        for previous, cue in zip(cues, cues[1:]):
            run = run + 1 if cue['text'].strip().lower() == previous['text'].strip().lower() else 1
            assert run < 5, f"转录疑似循环重复，需核对 {cue['start']} 秒附近音频"
        for cue in cues:
            words = re.findall(r'\w+', cue['text'].lower())
            assert not (len(words) > 30 and len(set(words)) < 5), f"转录疑似幻觉重复：{cue['start']} 秒"
            token_run = 1
            for first, second in zip(words, words[1:]):
                token_run = token_run + 1 if first == second else 1
                assert token_run < 8, f"转录单段疑似循环重复：{cue['start']} 秒"
        assert read(work / 'transcript/request.json')['provider'] == req['provider'], '转录方案不符'
    def scenes():
        manifest = read(work / 'scene-manifest.json')
        assert manifest.get('scenes'), '没有章节'
        assert manifest.get('keyframe_review', {}).get('status') == 'complete', '关键帧尚未确认'
        for scene in manifest['scenes']:
            assert Path(scene['frame_path']).is_file(), '关键帧文件缺失'
    def content():
        validate_delivery(work, read(work / 'scene-manifest.json'), read(work / 'localization.json'), req)
    def emphasis():
        if not req.get('require_emphasis'):
            return
        manifest = read(work / 'scene-manifest.json')
        for scene in manifest['scenes']:
            note = parse_note(work / 'codex-notes' / f"scene_{int(scene['id']):03d}.md")
            assert any(has_content_emphasis(paragraph) for paragraph in note['dialogue']), f"第 {scene['id']} 章缺少重点加粗"
        for language in req.get('note_languages', []):
            if language == 'zh':
                continue
            for index, scene in enumerate(read(work / 'localization.json')['notes'][language]['scenes'], 1):
                assert any(has_content_emphasis(p.get('text', '')) for p in scene['paragraphs']), f'{language} 第 {index} 章缺少重点加粗'
    def speaker_labels():
        manifest = read(work / 'scene-manifest.json')
        if not req.get('require_speaker_labels') or manifest.get('mode', {}).get('selected') != 'conversation':
            return
        lesson = js_data(site / 'data' / f'lesson-{lesson_id}.js')
        for scene in lesson['scenes']:
            assert any(p.get('speaker') for p in scene.get('paragraphs', [])), f"第 {scene['id']} 章没有结构化说话人标签"
    def imported():
        catalog = load_catalog(site / 'data/catalog.js')
        rows = catalog.get('lessons', [])
        ids = [row['id'] for row in rows]
        assert ids.count(lesson_id) == 1, '课程未入库或目录重复'
        assert set(req['existing_lesson_ids']).issubset(ids), '原有课程丢失'
        lesson = js_data(site / 'data' / f'lesson-{lesson_id}.js')
        source = read(work / 'localization.json')
        assert lesson.get('subtitles') == source.get('subtitles'), '已入库字幕与源文件不一致'
        assert lesson.get('notes') == source.get('notes'), '已入库笔记语言版本过期'
        manifest = read(work / 'scene-manifest.json')
        assert len(lesson['scenes']) == len(manifest['scenes']), '已入库章节数量不符'
        speakers = load_speakers(work / 'speaker-map.json')
        names = {info['name'] for info in speakers.values() if info.get('name')}
        for scene, original in zip(lesson['scenes'], manifest['scenes']):
            assert scene.get('paragraphs') and scene.get('title'), '入库笔记为空'
            note = parse_note(work / 'codex-notes' / f"scene_{int(original['id']):03d}.md")
            assert scene['title'] == note['title'] and scene.get('visual') == note['visual'], '入库章节笔记过期'
            assert scene['paragraphs'] == [split_speaker(p, speakers, names) for p in note['dialogue']], '入库笔记正文过期'
            assert (scene['start'], scene['end']) == (round(original['start_sec'], 2), round(original['end_sec'], 2)), '入库章节时间过期'
            resource = (site / scene['image']).resolve()
            assert resource.is_relative_to(site) and resource.is_file(), '入库图片缺失或越界'
        assert (site / 'media' / lesson_id / 'video.mp4').is_file(), '入库视频缺失'
    for name, action in [('download', acquisition), ('transcript', transcript), ('scenes', scenes), ('notes_and_subtitles', content), ('emphasis', emphasis), ('ingest', imported), ('speaker_labels', speaker_labels)]:
        check(name, action)
    # Bind manual browser evidence to both source artifacts and delivered files.
    digest = hashlib.sha256()
    paths = [work / 'delivery-requirements.json', work / 'localization.json', work / 'scene-manifest.json', site / 'data' / f'lesson-{lesson_id}.js', site / 'assets/site.js', site / 'assets/site.css', site / 'lesson.html']
    paths += sorted((work / 'codex-notes').glob('*.md'))
    paths += sorted((site / 'media' / lesson_id / 'frames').glob('*.jpg'))
    for path in paths:
        digest.update(str(path).encode())
        digest.update(path.read_bytes() if path.is_file() else b'MISSING')
    video = site / 'media' / lesson_id / 'video.mp4'
    if video.exists():
        stat = video.stat(); digest.update(f'{stat.st_size}:{stat.st_mtime_ns}'.encode())
    fingerprint = digest.hexdigest()
    def browser():
        evidence = read(work / 'browser-check.json')
        assert evidence['fingerprint'] == fingerprint, '内容已变化，需要重新浏览器验收'
        required = {'playback', 'seek', 'note_languages', 'subtitle_tracks', 'bilingual_visible', 'catalog'}
        if req.get('require_emphasis'):
            required.add('emphasis_visible')
        if req.get('require_speaker_labels') and read(work / 'scene-manifest.json').get('mode', {}).get('selected') == 'conversation':
            required.add('speaker_labels_visible')
        assert all(evidence.get('checks', {}).get(k) is True for k in required), '浏览器验收项不完整'
        assert evidence.get('evidence'), '缺少浏览器观察记录'
    check('browser', browser)
    return {'lesson_id': lesson_id, 'fingerprint': fingerprint, 'complete': all(r['passed'] for r in results), 'checkpoints': results,
            'next_checkpoint': next((r['checkpoint'] for r in results if not r['passed']), None)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project', type=Path)
    parser.add_argument('--site', type=Path, required=True)
    parser.add_argument('--id', required=True)
    parser.add_argument('--init', action='store_true', help='Record requested bilingual delivery contract and current catalog baseline')
    parser.add_argument('--provider', default='whisper')
    args = parser.parse_args()
    project, site = args.project.resolve(), args.site.resolve()
    lesson_id = validate_lesson_id(args.id)
    work = project / 'work'
    if args.init:
        req = work / 'delivery-requirements.json'
        if not req.exists():
            catalog = load_catalog(site / 'data/catalog.js')
            req.write_text(json.dumps({'provider': args.provider, 'complete_notes': True, 'require_emphasis': True, 'require_speaker_labels': True, 'note_languages': ['zh', 'en'], 'subtitle_tracks': ['en', 'zh', 'bilingual'], 'existing_lesson_ids': [r['id'] for r in catalog.get('lessons', [])]}, ensure_ascii=False, indent=2))
    report = inspect(project, site, lesson_id)
    (work / 'delivery-checkpoints.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['complete'] else 1


if __name__ == '__main__':
    sys.exit(main())

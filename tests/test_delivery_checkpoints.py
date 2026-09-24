import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from ingest import split_speaker, validate_delivery
from check_delivery import inspect


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.work = Path(self.tmp.name)
        self.manifest = {'scenes': [{'id': 1}]}
        self.req = {'subtitle_tracks': ['en', 'zh', 'bilingual']}
        self.data = {'subtitles': [{'id': k, 'cues': [{'start': 0, 'end': 1, 'text': t}]} for k, t in [('en', 'Hello'), ('zh', '你好'), ('bilingual', '你好\nHello')]]}

    def test_english_only_is_rejected(self):
        self.data['subtitles'] = self.data['subtitles'][:1]
        with self.assertRaisesRegex(ValueError, 'zh'):
            validate_delivery(self.work, self.manifest, self.data, self.req)

    def test_emphasis_checkpoint_requires_both_note_languages(self):
        notes = self.work / 'codex-notes'; notes.mkdir()
        note = notes / 'scene_001.md'
        note.write_text('## 标题\n示例\n\n## Light-plus\n关键数字为 21%。\n\n## Visual explainer\n图表。')
        self.req.update({'require_emphasis': True, 'note_languages': ['zh', 'en']})
        self.data['notes'] = {'en': {'scenes': [{'paragraphs': [{'text': 'The key rate was 21%.'}]}]}}
        with self.assertRaisesRegex(ValueError, '缺少关键内容加粗'):
            validate_delivery(self.work, self.manifest, self.data, self.req)
        note.write_text('## 标题\n示例\n\n## Light-plus\n关键数字为 **21%**。\n\n## Visual explainer\n图表。')
        with self.assertRaisesRegex(ValueError, 'en 第 1 章'):
            validate_delivery(self.work, self.manifest, self.data, self.req)
        self.data['notes']['en']['scenes'][0]['paragraphs'][0]['text'] = 'The key rate was **21%**.'
        validate_delivery(self.work, self.manifest, self.data, self.req)

    def test_bold_speaker_label_is_parsed_and_required_in_conversation(self):
        self.assertEqual(split_speaker('**付鹏**：这是判断。', {}, {'付鹏'}), {'speaker': '付鹏', 'text': '这是判断。'})
        self.manifest['mode'] = {'selected': 'conversation'}
        self.req['require_speaker_labels'] = True
        notes = self.work / 'codex-notes'; notes.mkdir()
        note = notes / 'scene_001.md'
        note.write_text('## Light-plus\n普通段落。')
        with self.assertRaisesRegex(ValueError, '缺少说话人标签'):
            validate_delivery(self.work, self.manifest, self.data, self.req)
        note.write_text('## Light-plus\n**付鹏**：这是判断。')
        validate_delivery(self.work, self.manifest, self.data, self.req)
        self.req['require_emphasis'] = True
        with self.assertRaisesRegex(ValueError, '缺少关键内容加粗'):
            validate_delivery(self.work, self.manifest, self.data, self.req)
        note.write_text('## Light-plus\n**付鹏**：这是 **关键判断**。')
        validate_delivery(self.work, self.manifest, self.data, self.req)

    def test_alignment_and_real_translation_required(self):
        validate_delivery(self.work, self.manifest, self.data, self.req)
        for field, value in [('start', .1), ('text', 'Hello')]:
            data = copy.deepcopy(self.data)
            data['subtitles'][1]['cues'][0][field] = value
            with self.assertRaises(ValueError):
                validate_delivery(self.work, self.manifest, data, self.req)

    def test_fake_bilingual_and_truncated_translation_rejected(self):
        self.data['subtitles'][2]['cues'][0]['text'] = 'Hello'
        with self.assertRaises(ValueError):
            validate_delivery(self.work, self.manifest, self.data, self.req)
        self.data['subtitles'][2]['cues'][0]['text'] = '你好\nHello'
        transcript = self.work / 'transcript.txt'
        transcript.write_text('[0.00s - 8.00s] Hello world\n')
        (self.work / 'run-state.json').write_text(json.dumps({'transcript': str(transcript)}))
        with self.assertRaisesRegex(ValueError, '覆盖'):
            validate_delivery(self.work, self.manifest, self.data, self.req)

    def test_prepare_alone_is_not_complete_and_browser_evidence_expires(self):
        project = self.work / 'project'; work = project / 'work';work.mkdir(parents=True)
        site = self.work / 'site';site.mkdir()
        (work / 'delivery-requirements.json').write_text(json.dumps({'provider': 'whisper'}))
        first = inspect(project, site, 'sample')
        self.assertFalse(first['complete'])
        (work / 'browser-check.json').write_text(json.dumps({'fingerprint': first['fingerprint'], 'checks': dict.fromkeys(['playback', 'seek', 'note_languages', 'subtitle_tracks', 'bilingual_visible', 'catalog'], True), 'evidence': 'test fixture'}))
        self.assertTrue(inspect(project, site, 'sample')['checkpoints'][-1]['passed'])
        (work / 'localization.json').write_text('{}')
        changed = inspect(project, site, 'sample')
        self.assertFalse(changed['checkpoints'][-1]['passed'])
        self.assertFalse(changed['complete'])

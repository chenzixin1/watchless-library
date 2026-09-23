import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(relative, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ImportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ingest = load('scripts/ingest.py', 'ingest_audit')

    def test_reject_path_ids_and_symlink_destination(self):
        for value in ('../outside', '/tmp/outside', 'abc/../../outside', 'a.js', ''):
            with self.assertRaises(ValueError):
                self.ingest.validate_lesson_id(value)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'alias').symlink_to(root.parent)
            with self.assertRaises(ValueError):
                self.ingest.confined_path(root, 'alias', 'file')

    def test_whisper_cues_and_colons_are_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'transcript.txt'
            path.write_text('[2.00s - 3.00s] 说话人0: hello\n[0.00s - 1.00s] Reason: no key needed\n[4.00s - 2.00s] invalid\n')
            cues = self.ingest.parse_cues(path, {'说话人0': {'name':'Alice'}})
            self.assertEqual([c['text'] for c in cues], ['Reason: no key needed', 'hello'])
            self.assertEqual(cues[1]['speaker'], 'Alice')

    def test_failed_transcode_preserves_old_video_and_skip_preserves_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            src, dst = Path(tmp)/'source.mp4', Path(tmp)/'video.mp4'
            src.write_bytes(b'original'); dst.write_bytes(b'old playable video')
            with patch.object(self.ingest, 'run_ffmpeg', side_effect=SystemExit('failed')):
                with self.assertRaises(SystemExit):
                    self.ingest.copy_video(src, dst, 'transcode', False)
            self.assertEqual(dst.read_bytes(), b'old playable video')
            self.ingest.copy_video(src, dst, 'skip', False)
            self.assertEqual(dst.read_bytes(), b'old playable video')
            with self.assertRaises(ValueError):
                self.ingest.copy_video(src, src, 'copy', False)
            self.assertEqual(src.read_bytes(), b'original')

    def test_corrupt_catalog_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'catalog.js'; path.write_text('broken existing catalog')
            with self.assertRaises(ValueError): self.ingest.load_catalog(path)
            self.assertEqual(path.read_text(), 'broken existing catalog')

    def test_bad_localization_is_rejected(self):
        for data in ({'notes': {'en': {'summary':'No scenes'}}}, {'subtitles':[{'id':'en','cues':[{'start':3,'end':2,'text':'bad'}]}]}):
            with self.assertRaises(ValueError): self.ingest.validate_localization(data, 1)

    def test_two_local_sources_accumulate_and_reimport_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); site=root/'site'; (site/'assets').mkdir(parents=True)
            (site/'assets/site.js').write_text('// fixture')
            for index in (1, 2, 1):
                project=root/f'project{index}'; work=project/'work'; work.mkdir(parents=True,exist_ok=True)
                video=project/'课程.mp4'; video.write_bytes(b'video')
                (work/'acquisition.json').write_text(json.dumps({'title':'课程','local_video':str(video),'duration_sec':1}))
                (work/'scene-manifest.json').write_text(json.dumps({'scenes':[{'id':1,'start_sec':0,'end_sec':1,'transcript_text':'hello'}]}))
                subprocess.run([sys.executable,str(ROOT/'scripts/ingest.py'),str(project),'--site',str(site),'--video','skip'],check=True,capture_output=True)
            lessons=self.ingest.load_catalog(site/'data/catalog.js')['lessons']
            self.assertEqual(len(lessons),2)
            self.assertNotEqual(lessons[0]['id'],lessons[1]['id'])

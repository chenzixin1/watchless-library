"""Verify selected ASR and audio language reach the transcription process."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

class RoutingTest(unittest.TestCase):
    def test_prepare_passes_provider_and_language(self):
        spec = importlib.util.spec_from_file_location('pipeline', ROOT / 'dependencies/watchless/scripts/00_build_video_notes.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for provider in ('tencent', 'volcengine', 'whisper'):
            with self.subTest(provider=provider), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                project = root / 'demo'
                (project / 'work').mkdir(parents=True)
                args = SimpleNamespace(max_height=1080, lang='en', no_browser_cookies=True,
                                       cookies_from_browser=None, use_source_subtitles=False, provider=provider)
                (root / 'video.mp4').write_bytes(b'fixture video')
                acquisition = {'title':'demo', 'local_video':str(root / 'video.mp4')}
                class StopBeforeASR(Exception):
                    pass
                with patch.object(module, 'resolve_initial_project', return_value=project), \
                     patch.object(module.ACQUIRE, 'acquire', return_value=acquisition), \
                     patch.object(module.subprocess, 'run', side_effect=StopBeforeASR) as run:
                    with self.assertRaises(StopBeforeASR):
                        module.prepare(str(root / 'video.mp4'), root, args)
                    command = run.call_args.args[0]
                    self.assertEqual(command[command.index('--provider') + 1], provider)
                    self.assertEqual(command[command.index('--lang') + 1], 'en')

if __name__ == '__main__':
    unittest.main()

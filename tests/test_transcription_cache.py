import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from test_security_and_import import load


def test_audio_cache_does_not_mix_same_named_files_or_changed_contents(tmp_path):
    module=load('dependencies/watchless/scripts/01_transcribe_video.py','transcribe_audit')
    transcriber=module.AudioTranscriber(api_key='')
    transcriber.cache_dir=tmp_path/'cache'
    a=tmp_path/'a'/'video.mp4'; b=tmp_path/'b'/'video.mp4'
    a.parent.mkdir(); b.parent.mkdir(); a.write_bytes(b'A'); b.write_bytes(b'B')
    class Clip:
        def __init__(self, path): self.path=Path(path); self.audio=self
        def write_audiofile(self, path, **kwargs): Path(path).write_bytes(self.path.read_bytes())
        def close(self): pass
    with patch.object(module, 'VideoFileClip', Clip):
        first=Path(transcriber.extract_audio_from_video(a))
        second=Path(transcriber.extract_audio_from_video(b))
        assert first != second
        assert first.read_bytes()==b'A' and second.read_bytes()==b'B'
        a.write_bytes(b'new A')
        third=Path(transcriber.extract_audio_from_video(a))
        assert third != first and third.read_bytes()==b'new A'


def test_whisper_sentence_timing_is_not_claimed_as_word_timing():
    module=load('dependencies/watchless/scripts/01_transcribe_video.py','transcribe_timing')
    result={'result': {'utterances':[{'text':'hello world','start_time':0,'end_time':1000}]}}
    normalized=module.normalized_word_transcript(result,'whisper')
    assert normalized['words'][0]['text']=='hello world'
    assert normalized['metadata']['word_timestamps'] is False


def test_prepare_invalidates_cache_when_provider_or_video_changes(tmp_path):
    module=load('dependencies/watchless/scripts/00_build_video_notes.py','prepare_cache')
    video=tmp_path/'video.mp4'; video.write_bytes(b'old')
    project=tmp_path/'demo'; (project/'work').mkdir(parents=True)
    args=SimpleNamespace(max_height=1080,lang='en',no_browser_cookies=True,cookies_from_browser=None,
                         use_source_subtitles=False,provider='whisper',mode_samples=1)
    calls=[]
    def transcribe(command, **kwargs):
        calls.append(command[command.index('--provider')+1])
        Path(command[command.index('--output')+1]).write_text('text')
        Path(command[command.index('--json-output')+1]).write_text('{}')
    acq={'title':'demo','local_video':str(video)}
    with patch.object(module,'resolve_initial_project',return_value=project), \
         patch.object(module.ACQUIRE,'acquire',return_value=acq), \
         patch.object(module.subprocess,'run',side_effect=transcribe), \
         patch.object(module,'build_packed_transcript',return_value=project/'packed.md'), \
         patch.object(module.OVERVIEW,'prepare_overview',return_value={'overview':'image','suggested_mode':'conversation'}):
        module.prepare(str(video),tmp_path,args)
        module.prepare(str(video),tmp_path,args)
        assert calls==['whisper']
        args.provider='volcengine'; module.prepare(str(video),tmp_path,args)
        assert calls==['whisper','volcengine']
        video.write_bytes(b'changed'); module.prepare(str(video),tmp_path,args)
        assert len(calls)==3


def test_local_same_names_get_distinct_project_dirs(tmp_path):
    module=load('dependencies/watchless/scripts/00_build_video_notes.py','prepare_projects')
    a=tmp_path/'a'/'video.mp4'; b=tmp_path/'b'/'video.mp4'
    a.parent.mkdir(); b.parent.mkdir(); a.touch(); b.touch()
    assert module.resolve_initial_project(str(a),tmp_path) != module.resolve_initial_project(str(b),tmp_path)


def test_youtube_host_boundary():
    module=load('dependencies/watchless/scripts/video_notes_common.py','url_audit')
    video_id='j2qfdu5awTE'
    assert module.extract_video_id('https://www.youtube.com/watch?v='+video_id)==video_id
    assert module.extract_video_id('https://fake-youtube.com/watch?v='+video_id) is None
    assert module.extract_video_id('file://youtube.com/watch?v='+video_id) is None

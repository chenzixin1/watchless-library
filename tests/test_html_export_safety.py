import json
import shutil
import subprocess
from unittest.mock import patch
import pytest
from test_security_and_import import load


def test_export_preserves_text_but_disables_active_html(tmp_path):
    if not shutil.which('pandoc'):
        pytest.skip('pandoc is required to verify the actual HTML exporter')
    module=load('dependencies/watchless/scripts/05_build_outputs.py','export_audit')
    frame=tmp_path/'frame.jpg'; frame.write_bytes(b'frame')
    transcript=tmp_path/'transcript.txt'; transcript.write_text('hello')
    manifest=tmp_path/'manifest.json'
    manifest.write_text(json.dumps({'source':{'title':'Test'},'transcript':{'path':str(transcript)},
                                   'scenes':[{'id':1,'start_sec':0,'end_sec':1,'frame_path':str(frame)}]}))
    notes=tmp_path/'notes'; notes.mkdir()
    (notes/'scene_001.md').write_text('## Title\nTest\n## Light-plus\n<script>alert(1)</script>\n\n[click](javascript:alert%281%29)\n## Visual explainer\nPicture')
    real_run=subprocess.run
    class StopBeforePDF(Exception): pass
    def run(command,**kwargs):
        if command[0]=='pandoc': return real_run(command,**kwargs)
        raise StopBeforePDF
    with patch.object(module,'_find_chrome',return_value=tmp_path/'chrome'),patch.object(module.subprocess,'run',side_effect=run):
        with pytest.raises(StopBeforePDF): module.build_share(manifest,notes,tmp_path/'output')
    html=(tmp_path/'output/share/Test-visual-explainer.html').read_text()
    assert '<script>alert(1)</script>' not in html
    assert '&lt;script&gt;' in html
    assert 'Content-Security-Policy' in html and "default-src 'none'" in html
    assert 'img src="keyframes/frame.jpg"' in html

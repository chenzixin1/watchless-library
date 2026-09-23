import functools
import http.client
import importlib.util
from http.server import ThreadingHTTPServer
from pathlib import Path
import tempfile
import threading
import unittest

ROOT=Path(__file__).resolve().parents[1]

class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec=importlib.util.spec_from_file_location('preview_server', ROOT/'scripts/serve.py')
        module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        cls.tmp=tempfile.TemporaryDirectory(); cls.root=Path(cls.tmp.name)
        site=cls.root/'site'; site.mkdir()
        cls.data=b'0123456789' * 100
        (site/'video.mp4').write_bytes(cls.data)
        (site/'.source-meta.json').write_text('private metadata')
        (cls.root/'private.txt').write_text('private file')
        (site/'link.txt').symlink_to(cls.root/'private.txt')
        cls.server=ThreadingHTTPServer(('127.0.0.1',0), functools.partial(module.MediaHandler,directory=str(site)))
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True); cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.thread.join(); cls.tmp.cleanup()

    def request(self,path,headers=None,method='GET'):
        conn=http.client.HTTPConnection('127.0.0.1',self.server.server_port)
        conn.request(method,path,headers=headers or {})
        response=conn.getresponse(); result=(response.status,dict(response.getheaders()),response.read()); conn.close(); return result

    def test_ranges_and_full_file(self):
        for value, expected in [('bytes=100-109',self.data[100:110]),('bytes=-10',self.data[-10:]),('bytes=990-',self.data[990:])]:
            status, headers, body=self.request('/video.mp4',{'Range':value})
            self.assertEqual(status,206); self.assertEqual(body,expected)
            self.assertEqual(int(headers['Content-Length']),len(expected))
        self.assertEqual(self.request('/video.mp4')[2],self.data)
        self.assertEqual(self.request('/video.mp4',{'Range':'bytes=9999-'})[0],416)
        self.assertEqual(self.request('/video.mp4',{'Range':'bytes=100-109'},'HEAD')[2],b'')

    def test_disallow_outside_and_hidden_files_and_rebinding(self):
        for path in ('/link.txt','/.source-meta.json','/%2esource-meta.json','/'):
            self.assertEqual(self.request(path)[0],403,path)
        self.assertEqual(self.request('/video.mp4',{'Host':'attacker.example'})[0],403)

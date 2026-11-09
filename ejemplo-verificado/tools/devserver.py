#!/usr/bin/env python3
"""Live-reload dev server for the watchface simulator.

Serves the project root over HTTP and auto-reloads the browser tab whenever
AnalogFull.fprj or any file under images/ changes on disk — so any rebuild
(render.py / build_project.py / build_aod.py / manual edit) shows up instantly.

Run:  ./venv/bin/python tools/devserver.py [port]
Then: http://localhost:8777/simulator.html
"""
import http.server, os, sys, threading, time, glob

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8777

# files whose mtime triggers a reload
def watch_paths():
    paths = [os.path.join(PROJ, "AnalogFull.fprj"),
             os.path.join(PROJ, "AOD", "AOD.fprj")]
    paths += glob.glob(os.path.join(PROJ, "images", "*"))
    paths += glob.glob(os.path.join(PROJ, "AOD", "images", "*"))
    return paths

VERSION = 0
def fingerprint():
    fp = []
    for p in watch_paths():
        try: fp.append((p, os.path.getmtime(p)))
        except OSError: pass
    return frozenset(fp)

def watcher():
    global VERSION
    last = fingerprint()
    while True:
        time.sleep(0.5)
        cur = fingerprint()
        if cur != last:
            last = cur
            VERSION += 1
            print(f"[devserver] change detected -> reload v{VERSION}")

# tiny poller injected into simulator.html
RELOAD_JS = """
<script>
(function(){let v=null;setInterval(async()=>{try{
const r=await fetch('/__reload',{cache:'no-store'});const n=await r.text();
if(v===null){v=n;}else if(n!==v){location.reload();}
}catch(e){}},700);})();
</script>
"""

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=PROJ, **k)
    def log_message(self, *a): pass
    def do_GET(self):
        if self.path.split("?")[0] == "/__reload":
            body = str(VERSION).encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        # inject live-reload script into the simulator page
        if self.path.split("?")[0] in ("/simulator.html", "/"):
            f = os.path.join(PROJ, "simulator.html")
            if os.path.exists(f):
                html = open(f, "rb").read() + RELOAD_JS.encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(html)))
                self.end_headers()
                self.wfile.write(html)
                return
        super().do_GET()

if __name__ == "__main__":
    threading.Thread(target=watcher, daemon=True).start()
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"[devserver] http://localhost:{PORT}/simulator.html  (watching .fprj + images/)")
    httpd.serve_forever()

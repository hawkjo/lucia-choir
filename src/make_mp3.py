"""Render one MP3 per song (all parts equal) for the "Download MP3" button.

The audio comes from the site's own synth (app.js, rendered offline in headless Chromium), so the MP3
sounds exactly like the website on the "Equal" setting. Needs: playwright (+ chromium) and ffmpeg.
"""
from __future__ import annotations

import functools
import http.server
import json
import subprocess
import tempfile
import threading
from pathlib import Path

from build import ROOT


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):  # keep the build output readable
        pass


def make_all(songs: list[dict]) -> None:
    from playwright.sync_api import sync_playwright

    out_dir = ROOT / "mp3"
    out_dir.mkdir(exist_ok=True)
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(_Quiet, directory=str(ROOT)))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{httpd.server_address[1]}/index.html?debug"
    try:
        with tempfile.TemporaryDirectory() as tmp, sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(accept_downloads=True)
            page.goto(url, wait_until="domcontentloaded")
            page.wait_for_function("window.__luciaDebug !== undefined")
            for k, s in enumerate(songs, start=1):
                with page.expect_download(timeout=300_000) as dl:
                    page.evaluate(f"window.__luciaDebug.downloadWav({json.dumps(s['id'])})")
                wav = Path(tmp) / f"{s['id']}.wav"
                dl.value.save_as(str(wav))
                mp3 = out_dir / f"{s['id']}.mp3"
                subprocess.run(
                    ["ffmpeg", "-v", "error", "-y", "-i", str(wav),
                     "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", "44100",
                     "-codec:a", "libmp3lame", "-q:a", "2",
                     "-metadata", f"title={s['title']} (all parts)",
                     "-metadata", "artist=Lucia choir practice",
                     "-metadata", "album=Lucia practice tracks",
                     "-metadata", f"track={k}/{len(songs)}",
                     str(mp3)],
                    check=True,
                )
                print(f"  mp3/{mp3.name}")
            browser.close()
    finally:
        httpd.shutdown()

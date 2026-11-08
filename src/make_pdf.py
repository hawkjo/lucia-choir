"""Render one printable A4 PDF per song from the same MEI the website uses.

Verovio lays out A4 pages (title block from <pgHead>), then headless Chromium prints them.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from build import BASE_OPTS, ROOT, verovio_toolkit


def song_pages(mei: str) -> list[str]:
    """A4 pages at full size; shrink (not below 85%) when that fits the song on a single sheet."""
    def render(scale):
        tk = verovio_toolkit()
        opts = dict(BASE_OPTS)
        # page size is given at 100% so the physical page stays A4 whatever the music scale
        opts.update(
            pageWidth=round(2100 * 100 / scale), pageHeight=round(2970 * 100 / scale),
            adjustPageHeight=False, breaks="line", scale=scale,
            header="encoded", footer="none", pageMarginTop=round(90 * 100 / scale),
            pageMarginBottom=round(90 * 100 / scale), pageMarginLeft=round(110 * 100 / scale),
            pageMarginRight=round(110 * 100 / scale),
        )
        tk.setOptions(opts)
        if not tk.loadData(mei):
            raise RuntimeError("verovio failed")
        return [tk.renderToSVG(p) for p in range(1, tk.getPageCount() + 1)]

    full = render(100)
    if len(full) == 1:
        return full
    for scale in (95, 90, 85):
        pages = render(scale)
        if len(pages) == 1:
            return pages
    return full


def make_all(songs) -> None:
    out_dir = ROOT / "pdf"
    out_dir.mkdir(exist_ok=True)
    from playwright.sync_api import sync_playwright  # pip install playwright && playwright install chromium

    with tempfile.TemporaryDirectory() as tmp, sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        for song in songs:
            pages = song_pages(song.mei())
            body = "".join(f'<section class="page">{svg}</section>' for svg in pages)
            html = f"""<!doctype html><html><head><meta charset="utf-8"><style>
              @page {{ size: A4; margin: 0; }}
              html, body {{ margin: 0; padding: 0; background: #fff; }}
              .page {{ width: 210mm; height: 297mm; overflow: hidden; page-break-after: always; break-after: page; }}
              .page:last-child {{ page-break-after: auto; break-after: auto; }}
              .page svg {{ width: 210mm; height: 297mm; display: block; }}
              svg text {{ font-family: 'Liberation Serif', 'Times New Roman', Times, serif; }}
            </style></head><body>{body}</body></html>"""
            hp = Path(tmp) / f"{song.id}.html"
            hp.write_text(html, encoding="utf-8")
            pdf = out_dir / f"{song.id}.pdf"
            page.goto(hp.as_uri())
            page.pdf(path=str(pdf), format="A4", print_background=True,
                     margin=dict(top="0", right="0", bottom="0", left="0"))
            print(f"  pdf/{pdf.name}: {len(pages)} page(s)")
        browser.close()

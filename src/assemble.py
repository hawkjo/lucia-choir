"""Assemble the site pages from web/ (body.html, style.css, app.js).

index.html    -> GitHub Pages (links style.css / app.js)
artifact.html -> claude.ai preview (body-only, CSS and JS inlined)
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
FONTS = ("https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@600;700"
         "&family=Figtree:wght@400;500;600;700&display=swap")
TITLE = "Lucia Choir Practice"
DESC = ("Practice tracks for the Lucia choir: sheet music for Melody, Harmony and Low "
        "with a moving marker, part-by-part mixing and starting notes.")
FAVICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 22 34'%3E"
           "%3Cpath d='M11 1c3 6 8 9 8 15a8 8 0 0 1-16 0c0-4 3-6 4-10 1 3 2 4 3 4 0-3 0-6 1-9z' fill='%23e3961c'/%3E"
           "%3Crect x='8' y='26' width='6' height='8' rx='1' fill='%23121c2e'/%3E%3C/svg%3E")


def main() -> None:
    body = (WEB / "body.html").read_text(encoding="utf-8")
    css = (WEB / "style.css").read_text(encoding="utf-8")
    js = (WEB / "app.js").read_text(encoding="utf-8")
    (ROOT / "style.css").write_text(css, encoding="utf-8")
    (ROOT / "app.js").write_text(js, encoding="utf-8")
    index = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{TITLE}</title>
<meta name="description" content="{DESC}">
<link rel="icon" href="{FAVICON}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="style.css">
</head>
<body>
{body}
<script src="app.js"></script>
</body>
</html>
"""
    (ROOT / "index.html").write_text(index, encoding="utf-8")
    # claude.ai previews cannot download files; the PDF button there just says so (see app.js)
    body_artifact = body.replace('id="pdfBtn" href="#" download>', 'id="pdfBtn" href="#">')
    artifact = f"""<title>{TITLE}</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="{FONTS}">
<style>
{css}
</style>
{body_artifact}
<script>window.LUCIA_ARTIFACT = true;</script>
<script>
{js}
</script>
"""
    (ROOT / "artifact.html").write_text(artifact, encoding="utf-8")
    (ROOT / ".nojekyll").write_text("", encoding="utf-8")
    print("assembled index.html and artifact.html")


if __name__ == "__main__":
    main()

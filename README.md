# Lucia choir practice site

Sheet music for each song with a moving marker, a five-step mix per part
(only my part → everyone except my part), starting notes like a pitch pipe,
a "Hide notes" view for singing from memory, a printable PDF and an MP3
(all parts equal) per song, and Hanna Norbäck's sung pronunciation for the
two Swedish songs. Static site: works on GitHub Pages as is.

## Publish

```bash
./deploy.sh            # creates github.com/<you>/lucia-choir and turns on Pages
```

Run it again after any change to push the update.

## Change a song

Songs are written in `src/songs/*.py` (one file per song, Melody / Harmony / Low,
notes as `pitch octave / duration`, lyrics underneath). After editing:

```bash
pip install verovio playwright && playwright install chromium   # once (MP3s also need ffmpeg)
python3 src/build.py --pdf --mp3     # rebuilds scores/, pdf/, mp3/ and index.html
```

The pronunciation text for the Swedish songs sits in the same song files
(`pronunciation=`); the recordings are in `audio/`.

`src/build.py` checks that every bar adds up and that every lyric line has one
syllable per note, and stops with the bar number if not.

| Folder     | What it holds                                                    |
|------------|------------------------------------------------------------------|
| `scores/`  | engraved SVGs (wide and phone layouts) + playback timing per song |
| `pdf/`     | the printable A4 sheets (same engraving as the site)             |
| `mp3/`     | each song with all parts equal, rendered with the site's synth   |
| `audio/`   | Hanna Norbäck's pronunciation recordings (Swedish songs)         |
| `web/`     | page source: `body.html`, `style.css`, `app.js`                  |
| `src/`     | song files and the build                                         |
| `mei/`     | the generated MEI files (open in Verovio or MuseScore)           |

Audio is synthesized in the browser (Web Audio), a cappella, starting exactly
at the marker. Repeats are played as written: Sankta Lucia sings the second half
twice; In the Bleak Midwinter plays three verses with a ritardando on the third.

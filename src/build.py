"""Build score SVGs, playback timelines and printable PDFs for the Lucia choir site.

Usage:  python3 src/build.py            (writes scores/*.svg, scores/*.json, mei/*.mei)
        python3 src/build.py --pdf      (also renders pdf/*.pdf via headless Chromium)
"""
from __future__ import annotations

import importlib.util
import json
import re
import sys
from fractions import Fraction as Fr
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
SONG_FILES = ["sankta_lucia", "silent_night", "jul_jul", "bleak_midwinter"]
VOICES = ["melody", "harmony", "low"]
VABBR = {"melody": "mel", "harmony": "har", "low": "low"}
LABELS = {"melody": ("Melody", "Mel."), "harmony": ("Harmony", "Har."), "low": ("Low", "Low")}
SEMI = {"c": 0, "d": 2, "e": 4, "f": 5, "g": 7, "a": 9, "b": 11}
ACC_IN = {"#": 1, "##": 2, "b": -1, "bb": -2, "n": 0, "": 0}
ACC_MEI = {1: "s", 2: "x", -1: "f", -2: "ff", 0: "n"}
SHARP_ORDER = "fcgdaeb"
FLAT_ORDER = "beadgcf"


# --------------------------------------------------------------------------- parsing
def parse_pitch(tok: str) -> dict:
    m = re.fullmatch(r"([a-g])(##|bb|#|b|n)?(\?)?(\d)", tok)
    if not m:
        raise ValueError(f"bad pitch {tok!r}")
    letter, acc, caut, octv = m.groups()
    return dict(step=letter, alter=ACC_IN[acc or ""], oct=int(octv), caution=bool(caut))


def parse_dur(code: str) -> tuple[int, int, Fr]:
    m = re.fullmatch(r"(\d+)(\.*)", code)
    base, dots = int(m.group(1)), len(m.group(2))
    q = Fr(4, base)
    total = q * (2 - Fr(1, 2 ** dots))
    return base, dots, total


TOKEN_RE = re.compile(r"^(?P<body>r|<[^>]+>|[a-g](?:##|bb|#|b|n)?\??\d)/(?P<dur>\d+\.*)(?P<suf>.*)$")


def parse_music(src: str) -> list[list[dict]]:
    measures, cur = [], []
    for tok in re.findall(r"<[^>]*>\S*|\S+", src):
        if tok == "|":
            measures.append(cur)
            cur = []
            continue
        if tok == ",":
            cur[-1]["breath"] = True
            continue
        m = TOKEN_RE.match(tok)
        if not m:
            raise ValueError(f"bad token {tok!r}")
        body, durc, suf = m.group("body"), m.group("dur"), m.group("suf")
        base, dots, q = parse_dur(durc)
        ev = dict(dur_code=base, dots=dots, dur=q, tie=None, slur=[], breath=False)
        if body == "r":
            ev["kind"] = "rest"
            ev["pitches"] = []
        elif body.startswith("<"):
            ev["kind"] = "chord"
            ev["pitches"] = [parse_pitch(p) for p in body[1:-1].split()]
        else:
            ev["kind"] = "note"
            ev["pitches"] = [parse_pitch(body)]
        # suffixes: ~ / ~1,3 (tie), ( ) solid slur, { } dashed slur
        i = 0
        while i < len(suf):
            c = suf[i]
            if c == "~":
                mm = re.match(r"~([\d,]*)", suf[i:])
                verses = mm.group(1)
                ev["tie"] = "all" if not verses else {int(v) for v in verses.split(",") if v}
                i += len(mm.group(0))
                continue
            if c in "(){}":
                ev["slur"].append(c)
            else:
                raise ValueError(f"bad suffix in {tok!r}")
            i += 1
        cur.append(ev)
    if cur:
        measures.append(cur)
    return measures


def parse_lyrics(src: str) -> tuple[str | None, list[list[str]]]:
    src = src.strip()
    label = None
    m = re.match(r"\[([^\]]+)\]\s*", src)
    if m:
        label = m.group(1)
        src = src[m.end():]
    groups, cur = [], []
    for tok in src.split():
        if tok == "|":
            groups.append(cur)
            cur = []
        else:
            cur.append(tok)
    groups.append(cur)
    return label, groups


# --------------------------------------------------------------------------- helpers
def key_alters(key: int) -> dict[str, int]:
    alt = {s: 0 for s in "abcdefg"}
    if key > 0:
        for s in SHARP_ORDER[:key]:
            alt[s] = 1
    elif key < 0:
        for s in FLAT_ORDER[: -key]:
            alt[s] = -1
    return alt


def midi_of(p: dict, shift: int = 0) -> int:
    return 12 * (p["oct"] + 1) + SEMI[p["step"]] + p["alter"] + shift


def shift_octave(p: dict, semis: int) -> dict:
    assert semis % 12 == 0
    q = dict(p)
    q["oct"] = p["oct"] + semis // 12
    return q


def tie_applies(ev: dict, verse: int) -> bool:
    t = ev.get("tie")
    if t is None:
        return False
    return t == "all" or verse in t


def fmt_num(x) -> str:
    x = float(x)
    return str(int(x)) if x == int(x) else f"{x:.4f}".rstrip("0").rstrip(".")


# --------------------------------------------------------------------------- song model
class Song:
    def __init__(self, mod_name: str):
        spec = importlib.util.spec_from_file_location(mod_name, ROOT / "src" / "songs" / f"{mod_name}.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self.d = mod.SONG
        d = self.d
        self.id = d["id"]
        num, den = d["meter"]
        self.mdur = Fr(num * 4, den)  # measure length in quarter notes
        self.beat_unit = den  # MEI tstamp unit
        self.voices = {}
        nmeas = None
        for v in VOICES:
            vd = d["voices"][v]
            meas = parse_music(vd["music"])
            written_shift = 12 if vd.get("input") == "sounding" else 0
            sound_shift = 0 if vd.get("input") == "sounding" else vd.get("octave_shift", 0)
            for mi, evs in enumerate(meas):
                tot = sum((e["dur"] for e in evs), Fr(0))
                if tot != self.mdur:
                    raise ValueError(f"{self.id} {v} m{mi+1}: duration {tot} != {self.mdur}")
                for e in evs:
                    e["voice"] = v
                    e["written"] = [shift_octave(p, written_shift) for p in e["pitches"]]
                    e["midi"] = [midi_of(p, sound_shift) for p in e["pitches"]]
            if nmeas is None:
                nmeas = len(meas)
            elif len(meas) != nmeas:
                raise ValueError(f"{self.id} {v}: {len(meas)} measures, expected {nmeas}")
            self.voices[v] = dict(measures=meas, lyrics=[parse_lyrics(s) for s in vd.get("lyrics", [])],
                                  dynamics=vd.get("dynamics", []))
        self.nmeas = nmeas
        self._assign_ids()
        self._assign_onsets()
        self._assign_lyrics()
        self._assign_accidentals()

    # ids + onsets ---------------------------------------------------------
    def _assign_ids(self):
        for v in VOICES:
            ab = VABBR[v]
            for mi, evs in enumerate(self.voices[v]["measures"]):
                for i, e in enumerate(evs):
                    e["id"] = f"{ab}{mi+1}_{i+1}"

    def _assign_onsets(self):
        for v in VOICES:
            for evs in self.voices[v]["measures"]:
                t = Fr(0)
                for e in evs:
                    e["onset"] = t
                    t += e["dur"]

    def flat_events(self, v):
        for mi, evs in enumerate(self.voices[v]["measures"]):
            for e in evs:
                yield mi, e

    # lyrics ---------------------------------------------------------------
    def _assign_lyrics(self):
        for v in VOICES:
            vv = self.voices[v]
            for vi, (label, groups) in enumerate(vv["lyrics"]):
                verse = vi + 1
                if len(groups) != self.nmeas:
                    raise ValueError(f"{self.id} {v} verse {verse}: {len(groups)} lyric bars, expected {self.nmeas}")
                prev_tied = False
                slots_all = []  # (mi, event)
                per_meas = [[] for _ in range(self.nmeas)]
                for mi, e in self.flat_events(v):
                    if e["kind"] == "rest":
                        prev_tied = False
                        continue
                    if prev_tied:
                        prev_tied = tie_applies(e, verse)
                        e.setdefault("tiecont", set()).add(verse)
                        continue
                    per_meas[mi].append(e)
                    slots_all.append(e)
                    prev_tied = tie_applies(e, verse)
                for mi in range(self.nmeas):
                    if len(per_meas[mi]) != len(groups[mi]):
                        raise ValueError(
                            f"{self.id} {v} verse {verse} m{mi+1}: {len(groups[mi])} lyric tokens "
                            f"for {len(per_meas[mi])} notes: {groups[mi]}")
                tokens = [t for g in groups for t in g]
                prev_hyphen = False
                first = True
                for k, (e, tok) in enumerate(zip(slots_all, tokens)):
                    if tok == "_":
                        continue
                    hyphen = tok.endswith("-")
                    text = tok[:-1] if hyphen else tok
                    begins, ends = (not prev_hyphen), (not hyphen)
                    wordpos = {(True, True): "s", (True, False): "i", (False, False): "m", (False, True): "t"}[(begins, ends)]
                    con = "d" if hyphen else None
                    if ends and k + 1 < len(tokens) and tokens[k + 1] == "_":
                        con = "u"
                    syl = dict(text=text, wordpos=wordpos, con=con, label=label if first else None)
                    e.setdefault("syl", {})[verse] = syl
                    prev_hyphen = hyphen
                    first = False
            # extender over tie continuations: if a word-final syllable is followed by tied notes
            for verse in range(1, len(vv["lyrics"]) + 1):
                last = None
                for mi, e in self.flat_events(v):
                    if e["kind"] == "rest":
                        last = None
                        continue
                    if verse in e.get("syl", {}):
                        last = e["syl"][verse]
                    elif verse in e.get("tiecont", set()) and last is not None and last["con"] is None:
                        last["con"] = "u"

    # accidentals ------------------------------------------------------------
    def _assign_accidentals(self):
        kalt = key_alters(self.d["key"])
        for v in VOICES:
            prev_end = {}
            prev_tie = False
            for mi, evs in enumerate(self.voices[v]["measures"]):
                state = {}
                courtesy_done = set()
                for e in evs:
                    for p in e["written"]:
                        k = (p["step"], p["oct"])
                        cur = state.get(k, kalt[p["step"]])
                        p["show"] = None
                        p["caution"] = p.get("caution", False)
                        if prev_tie and mi > 0 and e is evs[0]:
                            pass  # tie continuation across barline: no accidental
                        elif p["alter"] != cur:
                            p["show"] = p["alter"]
                        elif k not in state and k in prev_end and prev_end[k] != kalt[p["step"]] \
                                and k not in courtesy_done:
                            p["show"] = p["alter"]
                            p["caution"] = True
                            courtesy_done.add(k)
                        elif p.get("caution"):
                            p["show"] = p["alter"]
                        state[k] = p["alter"]
                    prev_tie = e.get("tie") is not None
                prev_end = state

    # performance order --------------------------------------------------------
    def instances(self) -> list[dict]:
        rep = self.d.get("repeat")
        n = self.nmeas
        order = []
        if not rep:
            order = [(m, 1) for m in range(1, n + 1)]
        elif "endings" in rep:
            s, e, ends = rep["start"], rep["end"], rep["endings"]
            in_endings = {m for ms in ends.values() for m in ms}
            order += [(m, 1) for m in range(1, s)]
            for p in sorted(ends):
                body = [m for m in range(s, e + 1) if m not in in_endings]
                order += [(m, p) for m in body] + [(m, p) for m in ends[p]]
            last = max(m for ms in ends.values() for m in ms)
            order += [(m, len(ends)) for m in range(last + 1, n + 1)]
        else:
            s, e, times = rep["start"], rep["end"], rep["times"]
            order += [(m, 1) for m in range(1, s)]
            for p in range(1, times + 1):
                order += [(m, p) for m in range(s, e + 1)]
            order += [(m, times) for m in range(e + 1, n + 1)]
        return [dict(m=m, pass_=p) for m, p in order]

    def timeline(self) -> dict:
        spq = 60.0 / self.d["tempo"]  # seconds per quarter
        rep = self.d.get("repeat") or {}
        rit = rep.get("rit")
        insts = self.instances()
        # tempo factor as function of (instance index, beat)
        rit_span = None
        if rit:
            idxs = [i for i, it in enumerate(insts) if it["pass_"] == rit["pass_"] and it["m"] >= rit["from_m"]]
            if idxs:
                rit_span = (idxs[0], idxs[-1])
        total_rit_q = None
        if rit_span:
            total_rit_q = float(self.mdur) * (rit_span[1] - rit_span[0] + 1)

        def factor(ii, b):
            if not rit_span or ii < rit_span[0] or ii > rit_span[1]:
                return 1.0
            q = (ii - rit_span[0]) * float(self.mdur) + b
            return 1.0 - (1.0 - rit["factor"]) * (q / total_rit_q)

        onsets_by_m = self.measure_onsets()
        t = 0.0
        out_inst = []
        for ii, it in enumerate(insts):
            mi = it["m"] - 1
            pts = sorted({float(b) for b in onsets_by_m[mi]} | {float(self.mdur)})
            tm, tt, prevb = [], t, 0.0
            # integrate dt = spq / factor
            fine = 48
            breaks = sorted(set(pts) | {0.0})
            for b in breaks:
                if b > prevb:
                    for k in range(fine):
                        b0 = prevb + (b - prevb) * k / fine
                        b1 = prevb + (b - prevb) * (k + 1) / fine
                        tt += (b1 - b0) * spq / factor(ii, (b0 + b1) / 2)
                    prevb = b
                tm.append([b, round(tt, 5)])
            out_inst.append(dict(m=mi, p=it["pass_"], t0=round(t, 5), t1=round(tt, 5), tm=tm))
            t = tt

        def time_at(ii, b):
            tm = out_inst[ii]["tm"]
            for (b0, t0), (b1, t1) in zip(tm, tm[1:]):
                if b0 <= b <= b1:
                    return t0 + (t1 - t0) * ((b - b0) / (b1 - b0) if b1 > b0 else 0)
            return tm[-1][1]

        # notes: walk each voice in performance order, merging ties valid for the pass/verse
        notes = []
        for vi, v in enumerate(VOICES):
            pending = None  # note being extended by a tie
            for ii, it in enumerate(insts):
                mi = it["m"] - 1
                verse = it["pass_"]
                for e in self.voices[v]["measures"][mi]:
                    if e["kind"] == "rest":
                        if pending:
                            notes.append(pending)
                            pending = None
                        continue
                    t0 = time_at(ii, float(e["onset"]))
                    t1 = time_at(ii, float(e["onset"] + e["dur"]))
                    if pending is not None and pending["p"] == e["midi"]:
                        pending["t1"] = round(t1, 5)
                        pending["ids"].append(e["id"])
                    else:
                        if pending:
                            notes.append(pending)
                        names = [q["step"].upper() + {1: "♯", -1: "♭", 2: "𝄪", -2: "𝄫"}.get(q["alter"], "")
                                 for q in e["pitches"]]
                        pending = dict(v=vi, t0=round(t0, 5), t1=round(t1, 5), p=list(e["midi"]), n=names,
                                       ids=[e["id"]], i=ii)
                    if not tie_applies(e, verse):
                        notes.append(pending)
                        pending = None
            if pending:
                notes.append(pending)
        notes.sort(key=lambda n: (n["t0"], n["v"]))
        measures = []
        for mi in range(self.nmeas):
            ons = []
            for b, ids in sorted(onsets_by_m[mi].items()):
                ons.append(dict(b=float(b), ids=ids))
            measures.append(dict(n=mi + 1, dur=float(self.mdur), onsets=ons))
        rep = self.d.get("repeat") or {}
        return dict(id=self.id, title=self.d["title"], tempo=self.d["tempo"], meter=list(self.d["meter"]),
                    voices=VOICES, measures=measures, instances=out_inst, notes=notes,
                    duration=round(t, 4), passes=max(i["p"] for i in out_inst),
                    passLabel="verse" if rep.get("times") else "time",
                    verses=max(len(self.voices[v]["lyrics"]) for v in VOICES))

    def measure_onsets(self) -> list[dict]:
        res = [dict() for _ in range(self.nmeas)]
        for v in VOICES:
            for mi, e in self.flat_events(v):
                res[mi].setdefault(e["onset"], []).append(e["id"])
        return res

    # MEI --------------------------------------------------------------------------
    def mei(self) -> str:
        d = self.d
        num, den = d["meter"]
        out = []
        w = out.append
        w('<?xml version="1.0" encoding="UTF-8"?>')
        w('<mei xmlns="http://www.music-encoding.org/ns/mei" meiversion="5.0">')
        w("<meiHead><fileDesc><titleStmt>")
        w(f"<title>{escape(d['title'])}</title>")
        if d.get("subtitle"):
            w(f'<title type="subordinate">{escape(d["subtitle"])}</title>')
        w("</titleStmt><pubStmt/></fileDesc></meiHead>")
        w("<music><body><mdiv><score>")
        meter_attr = f'meter.count="{num}" meter.unit="{den}"'
        if d.get("meter_sym") == "common":
            meter_attr += ' meter.sym="common"'
        ksig = d["key"]
        key_attr = f'key.sig="{abs(ksig)}{"s" if ksig > 0 else "f"}"' if ksig else 'key.sig="0"'
        w(f"<scoreDef {meter_attr} {key_attr}>")
        w(self._pghead_xml())
        w('<staffGrp bar.thru="false">')
        for n, v in enumerate(VOICES, start=1):
            clef = 'clef.shape="G" clef.line="2"'
            if v == "low":
                clef += ' clef.dis="8" clef.dis.place="below"'
            lab, abbr = LABELS[v]
            w(f'<staffDef n="{n}" lines="5" {clef}><label>{lab}</label><labelAbbr>{abbr}</labelAbbr></staffDef>')
        w("</staffGrp></scoreDef>")
        w("<section>")
        rep = d.get("repeat")
        ending_of = {}
        if rep and "endings" in rep:
            for k, ms in rep["endings"].items():
                for m in ms:
                    ending_of[m] = k
        breaks_after = set()
        acc = 0
        for s in d["systems"][:-1]:
            acc += s
            breaks_after.add(acc)
        open_ending = None
        for mi in range(self.nmeas):
            mnum = mi + 1
            end_k = ending_of.get(mnum)
            if end_k != open_ending:
                if open_ending is not None:
                    w("</ending>")
                if end_k is not None:
                    w(f'<ending n="{end_k}" label="{end_k}." xml:id="ending{end_k}">')
                open_ending = end_k
            attrs = f'n="{mnum}" xml:id="m{mnum}"'
            if rep:
                if mnum == rep["start"] and rep["start"] > 1:
                    attrs += ' left="rptstart"'
                if mnum == rep["end"]:
                    attrs += ' right="rptend"'
            if mnum == self.nmeas and not (rep and rep["end"] == mnum):
                attrs += ' right="end"'
            w(f"<measure {attrs}>")
            controls = []
            for n, v in enumerate(VOICES, start=1):
                w(f'<staff n="{n}"><layer n="1">')
                w(self._layer_xml(v, mi))
                w("</layer></staff>")
                controls += self._controls(v, n, mi)
            if mi == 0:
                controls.append(self._tempo_xml())
            for dd in d.get("directions", []):
                if dd["m"] == mnum:
                    sn = VOICES.index(dd["staff"]) + 1
                    controls.append(f'<dir staff="{sn}" tstamp="{fmt_num(dd["tstamp"])}" place="above">'
                                    f'<rend fontstyle="italic">{escape(dd["text"])}</rend></dir>')
            for c in controls:
                w(c)
            w("</measure>")
            if mnum in breaks_after:
                w("<sb/>")
        if open_ending is not None:
            w("</ending>")
        w("</section></score></mdiv></body></music></mei>")
        return "\n".join(out)

    def _pghead_xml(self) -> str:
        """Title block for the printable PDF (hidden on the website, which renders with header=none)."""
        d = self.d
        parts = ['<pgHead>',
                 f'<rend halign="center" valign="top"><rend fontsize="200%">{escape(d["title"])}</rend></rend>']
        if d.get("subtitle"):
            parts.append(f'<rend halign="center" valign="middle"><rend fontsize="110%">{escape(d["subtitle"])}</rend></rend>')
        if d.get("credits_left"):
            parts.append('<rend halign="left" valign="bottom">' + "<lb/>".join(escape(c) for c in d["credits_left"]) + "</rend>")
        if d.get("credits_right"):
            parts.append('<rend halign="right" valign="bottom">' + "<lb/>".join(escape(c) for c in d["credits_right"]) + "</rend>")
        parts.append("</pgHead>")
        return "".join(parts)

    def _tempo_xml(self) -> str:
        d = self.d
        pre = f'{escape(d["tempo_text"])} (' if d.get("tempo_text") else ""
        post = ")" if d.get("tempo_text") else ""
        return (f'<tempo staff="1" tstamp="1" place="above" mm="{d["tempo"]}" mm.unit="4">'
                f'{pre}<rend glyph.auth="smufl">&#xE1D5;</rend> = {d["tempo"]}{post}</tempo>')

    def _beam_groups(self, evs):
        num, den = self.d["meter"]
        group = Fr(3, 2) if (den == 8 and num % 3 == 0) else Fr(1)
        groups = []
        cur = []
        for e in evs:
            beamable = e["kind"] != "rest" and e["dur_code"] >= 8
            gi = int(e["onset"] // group)
            fits = beamable and int((e["onset"] + e["dur"] - Fr(1, 1000)) // group) == gi
            if fits and cur and int(cur[-1]["onset"] // group) == gi:
                cur.append(e)
            else:
                if len(cur) > 1:
                    groups.append(cur)
                cur = [e] if fits else []
        if len(cur) > 1:
            groups.append(cur)
        return groups

    def _note_xml(self, e, p, nid, in_chord=False):
        oct_ = p["oct"] - (1 if e.get("voice") == "low" else 0)  # treble-8: Verovio expects sounding octave
        a = f'xml:id="{nid}" pname="{p["step"]}" oct="{oct_}"'
        if not in_chord:
            a += f' dur="{e["dur_code"]}"' + (f' dots="{e["dots"]}"' if e["dots"] else "")
        kalt = key_alters(self.d["key"])[p["step"]]
        inner = ""
        if p["show"] is not None:
            if p["caution"]:
                inner = f'<accid accid="{ACC_MEI[p["show"]]}" func="caution" enclose="paren"/>'
            else:
                a += f' accid="{ACC_MEI[p["show"]]}"'
        elif p["alter"] != 0:
            a += f' accid.ges="{ACC_MEI[p["alter"]]}"'
        syls = ""
        for verse, s in sorted(e.get("syl", {}).items()) if not in_chord else []:
            lab = f"<label>{escape(s['label'])}</label>" if s.get("label") else ""
            sa = f'wordpos="{s["wordpos"]}"' + (f' con="{s["con"]}"' if s["con"] else "")
            syls += f'<verse n="{verse}">{lab}<syl {sa}>{escape(s["text"])}</syl></verse>'
        return f"<note {a}>{inner}{syls}</note>"

    def _event_xml(self, e):
        if e["kind"] == "rest":
            dots = f' dots="{e["dots"]}"' if e["dots"] else ""
            return f'<rest xml:id="{e["id"]}" dur="{e["dur_code"]}"{dots}/>'
        if e["kind"] == "note":
            return self._note_xml(e, e["written"][0], e["id"])
        dots = f' dots="{e["dots"]}"' if e["dots"] else ""
        inner = "".join(self._note_xml(e, p, f'{e["id"]}{"abcdef"[k]}', in_chord=True)
                        for k, p in enumerate(e["written"]))
        syls = ""
        for verse, s in sorted(e.get("syl", {}).items()):
            sa = f'wordpos="{s["wordpos"]}"' + (f' con="{s["con"]}"' if s["con"] else "")
            syls += f'<verse n="{verse}"><syl {sa}>{escape(s["text"])}</syl></verse>'
        if syls:  # attach lyrics to the top chord note
            k = inner.rfind("</note>")
            inner = inner[:k] + syls + inner[k:]
        return f'<chord xml:id="{e["id"]}" dur="{e["dur_code"]}"{dots}>{inner}</chord>'

    def _layer_xml(self, v, mi):
        evs = self.voices[v]["measures"][mi]
        groups = self._beam_groups(evs)
        starts = {id(g[0]): g for g in groups}
        ends = {id(g[-1]) for g in groups}
        parts = []
        for e in evs:
            if id(e) in starts:
                parts.append("<beam>")
            parts.append(self._event_xml(e))
            if id(e) in ends:
                parts.append("</beam>")
        return "".join(parts)

    def _controls(self, v, staff_n, mi):
        evs_all = list(self.flat_events(v))
        out = []
        # ties + slurs that start in this measure
        idx = [k for k, (m, e) in enumerate(evs_all) if m == mi]
        open_slurs = []
        for k, (m, e) in enumerate(evs_all):
            for c in e["slur"]:
                if c in "({":
                    open_slurs.append((c, e, m))
                else:
                    want = "(" if c == ")" else "{"
                    for j in range(len(open_slurs) - 1, -1, -1):
                        if open_slurs[j][0] == want:
                            c0, e0, m0 = open_slurs.pop(j)
                            if m0 == mi:
                                lform = ' lform="dashed"' if want == "{" else ""
                                out.append(f'<slur staff="{staff_n}" startid="#{self._anchor(e0)}" '
                                           f'endid="#{self._anchor(e)}"{lform}/>')
                            break
        for k in idx:
            m, e = evs_all[k]
            if e.get("tie") is not None and k + 1 < len(evs_all):
                e2 = evs_all[k + 1][1]
                lform = "" if e["tie"] == "all" else ' lform="dashed"'
                if e["kind"] == "chord":
                    for a, b in zip(range(len(e["written"])), range(len(e2["written"]))):
                        out.append(f'<tie staff="{staff_n}" startid="#{e["id"]}{"abcdef"[a]}" '
                                   f'endid="#{e2["id"]}{"abcdef"[b]}"{lform}/>')
                else:
                    out.append(f'<tie staff="{staff_n}" startid="#{e["id"]}" endid="#{e2["id"]}"{lform}/>')
            if e.get("breath"):
                num, den = self.d["meter"]
                beats_per_q = Fr(den, 4)
                b0 = float(e["onset"] * beats_per_q) + 1
                b1 = float((e["onset"] + e["dur"]) * beats_per_q) + 1
                out.append(f'<breath staff="{staff_n}" tstamp="{fmt_num(b0 + 0.72 * (b1 - b0))}" place="above"/>')
        for dy in self.voices[v]["dynamics"]:
            if dy["m"] != mi + 1:
                continue
            if dy["kind"] == "dynam":
                out.append(f'<dynam staff="{staff_n}" tstamp="{fmt_num(dy["tstamp"])}" place="above">{dy["text"]}</dynam>')
            elif dy["kind"] == "hairpin":
                dm = dy["m2"] - dy["m"]
                out.append(f'<hairpin staff="{staff_n}" form="{dy["form"]}" place="above" tstamp="{fmt_num(dy["tstamp"])}" '
                           f'tstamp2="{dm}m+{fmt_num(dy["tstamp2"])}"/>')
        return out

    def _anchor(self, e):
        return e["id"] if e["kind"] != "chord" else e["id"] + "a"


# --------------------------------------------------------------------------- rendering
def verovio_toolkit():
    import verovio
    tk = verovio.toolkit()
    tk.setResourcePath(str(Path(verovio.__file__).parent / "data"))
    return tk


BASE_OPTS = dict(
    font="Bravura",
    svgViewBox=True,
    svgHtml5=True,
    svgRemoveXlink=True,
    adjustPageHeight=True,
    header="none",
    footer="none",
    lyricSize=4.2,
    lyricTopMinMargin=3.0,
    spacingStaff=10,
    spacingSystem=10,
    pageMarginLeft=40,
    pageMarginRight=40,
    pageMarginTop=40,
    pageMarginBottom=40,
    systemDivider="none",
    minLastJustification=0.75,
    spacingLinear=0.6,
    spacingNonLinear=0.55,
    svgAdditionalAttribute=["verse@n"],
)


def render_svg(mei: str, layout: str) -> str:
    tk = verovio_toolkit()
    opts = dict(BASE_OPTS)
    if layout == "wide":
        opts.update(pageWidth=2100, pageHeight=60000, breaks="encoded", scale=100)
    else:
        opts.update(pageWidth=1150, pageHeight=60000, breaks="auto", scale=100, spacingLinear=0.25, spacingNonLinear=0.55, lyricSize=4.6)
        for v in VOICES:  # short staff names on the first line too, so a phone line holds two bars
            lab, abbr = LABELS[v]
            mei = mei.replace(f"<label>{lab}</label>", f"<label>{abbr}</label>")
    tk.setOptions(opts)
    if not tk.loadData(mei):
        raise RuntimeError("verovio failed to load MEI")
    if tk.getPageCount() != 1:
        raise RuntimeError(f"expected one page, got {tk.getPageCount()}")
    return tk.renderToSVG(1)


def main():
    (ROOT / "scores").mkdir(exist_ok=True)
    (ROOT / "mei").mkdir(exist_ok=True)
    index = []
    for name in SONG_FILES:
        song = Song(name)
        mei = song.mei()
        (ROOT / "mei" / f"{song.id}.mei").write_text(mei, encoding="utf-8")
        for layout in ("wide", "narrow"):
            svg = render_svg(mei, layout)
            (ROOT / "scores" / f"{song.id}.{layout}.svg").write_text(svg, encoding="utf-8")
        tl = song.timeline()
        (ROOT / "scores" / f"{song.id}.json").write_text(json.dumps(tl, separators=(",", ":"), ensure_ascii=False),
                                                         encoding="utf-8")
        index.append(dict(id=song.id, title=song.d["title"], short=song.d.get("short", song.d["title"]),
                          credits=song.d.get("credits_left", []) + song.d.get("credits_right", []),
                          subtitle=song.d.get("subtitle"),
                          duration=tl["duration"], passes=tl["passes"],
                          pronunciation=song.d.get("pronunciation")))
        print(f"{song.id}: {song.nmeas} bars, {tl['duration']:.1f}s, {len(tl['notes'])} notes")
    (ROOT / "scores" / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    import assemble
    assemble.main()
    if "--pdf" in sys.argv:
        from make_pdf import make_all
        make_all([Song(n) for n in SONG_FILES])
    if "--mp3" in sys.argv:
        from make_mp3 import make_all as make_mp3s
        make_mp3s(index)


if __name__ == "__main__":
    main()

/* Lucia choir practice player.
   Score data (scores/<song>.json) comes from src/build.py: notes with times in seconds (repeats expanded),
   the performance order of bars ("instances") and, per bar, the beat of every note onset with the ids of the
   engraved notes, which we look up in the SVG to place the marker. */
(() => {
  'use strict';

  const VOICES = ['Melody', 'Harmony', 'Low'];
  // gain for [the selected part, the other parts] at each of the five mix steps
  const MIX = { 1: [1.0, 0.0], 2: [1.0, 0.2], 3: [0.72, 0.72], 4: [0.2, 1.0], 5: [0.0, 1.0] };
  const TICKS = ['Only', 'Louder', 'Equal', 'Softer', 'Without'];
  // read out by screen readers for the slider; the visible caption is just "Selected part"
  const MIX_TEXT = [
    v => `${v} alone`,
    v => `${v} loud, the other parts quietly behind`,
    () => 'All parts equal',
    v => `${v} quiet, the other parts in front`,
    v => `Everyone except ${v}`,
  ];
  const VOICE_ENV = { attack: 0.025, decay: 0.18, peak: 0.38, sustain: 0.29, release: 0.07 };
  const PIPE_ENV = { attack: 0.05, decay: 0.3, peak: 0.42, sustain: 0.36, release: 0.16 };
  const IS_ARTIFACT = !!window.LUCIA_ARTIFACT;
  const $ = (s) => document.querySelector(s);

  const store = {
    get(k, d) { try { const v = localStorage.getItem('luciaChoir.' + k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } },
    set(k, v) { try { localStorage.setItem('luciaChoir.' + k, JSON.stringify(v)); } catch (e) { /* private mode */ } },
  };
  const clampInt = (v, lo, hi) => { v = parseInt(v, 10); return isNaN(v) ? lo : Math.min(hi, Math.max(lo, v)); };

  const state = {
    songs: [], song: null, data: null, layout: null, svg: null, geom: null, loc: null,
    voice: clampInt(store.get('voice', 0), 0, 2), mix: clampInt(store.get('mix', 3), 1, 5),
    pos: 0, playFrom: 0, playing: false, token: 0, lastSys: -1, verseOn: 0, hideNotes: false,
  };
  const cache = new Map();

  // ------------------------------------------------------------------ audio
  function periodicWave(ctx, amps) {
    const real = new Float32Array(amps.length + 1), imag = new Float32Array(amps.length + 1);
    amps.forEach((a, i) => { imag[i + 1] = a; });
    return ctx.createPeriodicWave(real, imag);
  }

  // One audio graph for live playback and for the offline render behind "Download MP3":
  // a bus per part (gain + slight stereo spread) -> master -> gentle compressor.
  function buildGraph(ctx) {
    const comp = ctx.createDynamicsCompressor();
    comp.threshold.value = -14; comp.knee.value = 10; comp.ratio.value = 3;
    comp.attack.value = 0.004; comp.release.value = 0.25;
    const master = ctx.createGain();
    master.gain.value = 0.8;
    master.connect(comp);
    comp.connect(ctx.destination);
    const pan = [0, -0.18, 0.18];
    const base = [1.0, 1.0, 1.3]; // low notes need a little help on small speakers
    const buses = [0, 1, 2].map((i) => {
      const g = ctx.createGain();
      g.base = base[i];
      if (ctx.createStereoPanner) {
        const p = ctx.createStereoPanner();
        p.pan.value = pan[i];
        g.connect(p); p.connect(master);
      } else {
        g.connect(master);
      }
      return g;
    });
    const pipeBus = ctx.createGain();
    pipeBus.gain.value = 1.0;
    pipeBus.connect(master);
    // a soft, sustained organ-like tone for the parts; a brighter reed for the pitch pipe
    const waves = {
      voice: periodicWave(ctx, [1, 0.42, 0.2, 0.11, 0.06, 0.035, 0.02, 0.012]),
      reed: periodicWave(ctx, [1, 0.8, 0.62, 0.45, 0.34, 0.25, 0.18, 0.13, 0.09, 0.06, 0.04, 0.025]),
    };
    return { master, buses, pipeBus, waves };
  }

  function scheduleTone(ctx, dest, wave, midi, t0, t1, o) {
    const osc = ctx.createOscillator();
    osc.setPeriodicWave(wave);
    osc.frequency.value = 440 * Math.pow(2, (midi - 69) / 12);
    const env = ctx.createGain();
    env.gain.value = 0;
    const dur = Math.max(0.03, t1 - t0);
    const atk = Math.min(o.attack, dur * 0.3);
    const rel = Math.min(o.release, dur * 0.3);
    const g = env.gain;
    g.setValueAtTime(0, t0);
    g.linearRampToValueAtTime(o.peak, t0 + atk);
    g.setTargetAtTime(o.sustain, t0 + atk, o.decay);
    g.setTargetAtTime(0, t1 - rel, rel / 4); // ends just before the next note, so repeated notes are re-sung
    osc.connect(env);
    env.connect(dest);
    osc.start(t0);
    osc.stop(t1 + 0.03);
    return { osc, env };
  }

  // Whole song, all parts equal, rendered offline (used by the build to make the MP3 downloads).
  async function renderAllPartsWav(data) {
    const sr = 44100, lead = 0.3, tail = 0.8;
    const ctx = new OfflineAudioContext(2, Math.ceil((data.duration + lead + tail) * sr), sr);
    const g = buildGraph(ctx);
    const [sel, other] = MIX[3];
    g.buses.forEach((b, i) => { b.gain.value = (i === 0 ? sel : other) * b.base; });
    for (const n of data.notes) {
      for (const m of n.p) scheduleTone(ctx, g.buses[n.v], g.waves.voice, m, n.t0 + lead, n.t1 + lead, VOICE_ENV);
    }
    const buf = await ctx.startRendering();
    const L = buf.getChannelData(0), R = buf.getChannelData(1), n = L.length;
    const out = new DataView(new ArrayBuffer(44 + n * 4));
    const str = (o, s) => { for (let i = 0; i < s.length; i++) out.setUint8(o + i, s.charCodeAt(i)); };
    str(0, 'RIFF'); out.setUint32(4, 36 + n * 4, true); str(8, 'WAVE'); str(12, 'fmt ');
    out.setUint32(16, 16, true); out.setUint16(20, 1, true); out.setUint16(22, 2, true);
    out.setUint32(24, sr, true); out.setUint32(28, sr * 4, true); out.setUint16(32, 4, true); out.setUint16(34, 16, true);
    str(36, 'data'); out.setUint32(40, n * 4, true);
    for (let i = 0, o = 44; i < n; i++, o += 4) {
      out.setInt16(o, Math.max(-1, Math.min(1, L[i])) * 32767, true);
      out.setInt16(o + 2, Math.max(-1, Math.min(1, R[i])) * 32767, true);
    }
    return new Blob([out.buffer], { type: 'audio/wav' });
  }

  const audio = {
    ctx: null, master: null, buses: [], pipeBus: null, waves: {}, live: new Set(),
    timer: null, startCtx: 0, startSong: 0, next: 0, pipeTimers: [],

    ensure() {
      if (!this.ctx) {
        const AC = window.AudioContext || window.webkitAudioContext;
        if (!AC) { setStatus('This browser cannot play audio.'); return null; }
        this.ctx = new AC({ latencyHint: 'interactive' });
        try { if (navigator.audioSession) navigator.audioSession.type = 'playback'; } catch (e) { /* older Safari */ }
        Object.assign(this, buildGraph(this.ctx));
        this.applyMix(true);
      }
      if (this.ctx.state !== 'running') this.ctx.resume();
      return this.ctx;
    },

    applyMix(immediate) {
      if (!this.ctx) return;
      const [sel, other] = MIX[state.mix];
      this.buses.forEach((g, i) => {
        const v = (i === state.voice ? sel : other) * g.base;
        if (immediate) g.gain.value = v;
        else g.gain.setTargetAtTime(v, this.ctx.currentTime, 0.03);
      });
    },

    tone(dest, wave, midi, t0, t1, o) {
      const node = scheduleTone(this.ctx, dest, wave, midi, t0, t1, o);
      this.live.add(node);
      node.osc.onended = () => { this.live.delete(node); try { node.env.disconnect(); } catch (e) { /* already gone */ } };
      return node;
    },

    start(from) {
      const ctx = this.ensure();
      if (!ctx) return false;
      this.halt();
      this.startCtx = ctx.currentTime + 0.06;
      this.startSong = from;
      const notes = state.data.notes;
      let i = 0;
      while (i < notes.length && notes[i].t0 < from - 1e-4) {
        if (notes[i].t1 > from + 0.06) this.play(notes[i], from); // a held note that began before the marker
        i++;
      }
      this.next = i;
      this.pump();
      this.timer = setInterval(() => this.pump(), 25);
      return true;
    },

    now() { return this.startSong + (this.ctx.currentTime - this.startCtx); },

    pump() {
      if (!state.data) return;
      const t = this.now();
      const horizon = t + (document.hidden ? 1.6 : 0.3); // background tabs throttle timers to ~1/s
      const notes = state.data.notes;
      while (this.next < notes.length && notes[this.next].t0 < horizon) {
        this.play(notes[this.next], null);
        this.next++;
      }
      if (t >= state.data.duration + 0.05) finished();
    },

    play(n, from) {
      const s = this.startCtx + ((from == null ? n.t0 : from) - this.startSong);
      const e = this.startCtx + (n.t1 - this.startSong);
      const s2 = Math.max(s, this.ctx.currentTime + 0.005);
      if (e - s2 < 0.02) return;
      for (const m of n.p) this.tone(this.buses[n.v], this.waves.voice, m, s2, e, VOICE_ENV);
    },

    halt() {
      clearInterval(this.timer);
      this.timer = null;
      this.silence();
    },

    silence() {
      this.pipeTimers.forEach(clearTimeout);
      this.pipeTimers = [];
      clearPipeUI();
      if (!this.ctx) return;
      const t = this.ctx.currentTime;
      for (const nd of this.live) {
        try {
          const g = nd.env.gain;
          const v = g.value;
          g.cancelScheduledValues(t);
          g.setValueAtTime(v, t);
          g.setTargetAtTime(0, t, 0.012);
          nd.osc.stop(t + 0.08);
        } catch (e) { /* node already stopped */ }
      }
      this.live.clear();
    },
  };

  // ------------------------------------------------------------------ time <-> score position
  function instAt(T) {
    const ins = state.data.instances;
    let lo = 0, hi = ins.length - 1;
    while (lo < hi) {
      const mid = (lo + hi + 1) >> 1;
      if (ins[mid].t0 <= T + 1e-9) lo = mid; else hi = mid - 1;
    }
    return lo;
  }
  function beatAt(ii, T) {
    const tm = state.data.instances[ii].tm;
    for (let k = 1; k < tm.length; k++) {
      if (T <= tm[k][1] || k === tm.length - 1) {
        const [b0, t0] = tm[k - 1], [b1, t1] = tm[k];
        const f = t1 > t0 ? Math.min(1, Math.max(0, (T - t0) / (t1 - t0))) : 0;
        return b0 + f * (b1 - b0);
      }
    }
    return tm[tm.length - 1][0];
  }
  function timeAt(ii, b) {
    const tm = state.data.instances[ii].tm;
    for (let k = 1; k < tm.length; k++) {
      if (b <= tm[k][0] || k === tm.length - 1) {
        const [b0, t0] = tm[k - 1], [b1, t1] = tm[k];
        const f = b1 > b0 ? Math.min(1, Math.max(0, (b - b0) / (b1 - b0))) : 0;
        return t0 + f * (t1 - t0);
      }
    }
    return tm[tm.length - 1][1];
  }
  function interp(pts, b) {
    if (b <= pts[0][0]) return pts[0][1];
    for (let k = 1; k < pts.length; k++) {
      if (b <= pts[k][0]) {
        const [b0, x0] = pts[k - 1], [b1, x1] = pts[k];
        return b1 > b0 ? x0 + (x1 - x0) * (b - b0) / (b1 - b0) : x0;
      }
    }
    return pts[pts.length - 1][1];
  }
  function timesBarIsPlayed(mi) {
    return state.data.instances.reduce((n, it) => n + (it.m === mi ? 1 : 0), 0);
  }

  // ------------------------------------------------------------------ geometry from the engraved SVG
  function buildGeom() {
    const svg = state.svg, data = state.data;
    if (!svg || !data) { state.geom = null; return; }
    const pr = $('#paper').getBoundingClientRect();
    const R = (el) => {
      const r = el.getBoundingClientRect();
      return { l: r.left - pr.left, r: r.right - pr.left, t: r.top - pr.top, b: r.bottom - pr.top };
    };
    const byId = new Map();
    svg.querySelectorAll('[data-id]').forEach((el) => byId.set(el.getAttribute('data-id'), el));
    const systems = [];
    const meas = [];
    svg.querySelectorAll('g.system').forEach((sg) => {
      const sys = { box: R(sg), staves: null, left: Infinity, right: -Infinity, ms: [] };
      sg.querySelectorAll('g.measure').forEach((mg) => {
        const mi = parseInt((mg.getAttribute('data-id') || '').slice(1), 10) - 1;
        const m = data.measures[mi];
        if (!m) return;
        const staves = Array.from(mg.querySelectorAll('g.staff')).slice(0, 3).map((st) => {
          const s = { t: Infinity, b: -Infinity, l: Infinity, r: -Infinity };
          for (const p of st.children) {
            if (p.tagName.toLowerCase() !== 'path') continue; // the five staff lines
            const q = R(p);
            s.t = Math.min(s.t, q.t); s.b = Math.max(s.b, q.b); s.l = Math.min(s.l, q.l); s.r = Math.max(s.r, q.r);
          }
          return s;
        });
        if (staves.length < 3) return;
        const left = Math.min(...staves.map((s) => s.l)), right = Math.max(...staves.map((s) => s.r));
        const pts = [];
        for (const on of m.onsets) {
          let x = Infinity;
          for (const id of on.ids) {
            const el = byId.get(id);
            if (!el) continue;
            const head = el.querySelector('.notehead') || el;
            const q = R(head);
            x = Math.min(x, (q.l + q.r) / 2);
          }
          if (x < Infinity) pts.push([on.b, x]);
        }
        if (!pts.length) pts.push([0, left + 8]);
        pts.push([m.dur, right]);
        meas[mi] = { mi, sys: systems.length, left, right, pts };
        sys.ms.push(mi);
        sys.left = Math.min(sys.left, left); sys.right = Math.max(sys.right, right);
        if (!sys.staves) sys.staves = staves;
      });
      if (sys.ms.length) {
        const h = sys.staves[0].b - sys.staves[0].t;
        sys.top = sys.staves[0].t - 0.3 * h;
        sys.bottom = sys.staves[2].b + 0.3 * h;
        systems.push(sys);
      }
    });
    state.geom = { systems, meas };
    state.lastSys = -1;
  }

  function drawBands() {
    const host = $('#bands');
    host.innerHTML = '';
    const g = state.geom;
    if (!g) return;
    const v = state.voice;
    for (const sys of g.systems) {
      const st = sys.staves, h = st[v].b - st[v].t;
      const top = st[v].t - 0.55 * h;
      const bottom = v < 2 ? st[v + 1].t - 0.55 * h : Math.max(sys.box.b, st[2].b + 0.6 * h) + 4;
      const d = document.createElement('div');
      d.className = 'band';
      d.style.left = Math.max(2, sys.box.l - 6) + 'px';
      d.style.width = (sys.right - Math.max(2, sys.box.l - 6) + 8) + 'px';
      d.style.top = top + 'px';
      d.style.height = (bottom - top) + 'px';
      host.appendChild(d);
    }
  }

  function locate(T) {
    const g = state.geom, data = state.data;
    if (!g || !data) return null;
    const ii = instAt(T);
    const inst = data.instances[ii];
    const mg = g.meas[inst.m];
    if (!mg) return null;
    const b = beatAt(ii, T);
    const sys = g.systems[mg.sys];
    return { x: interp(mg.pts, b), top: sys.top, bottom: sys.bottom, sys: mg.sys, ii, m: inst.m, pass: inst.p, b };
  }

  function drawMarker() {
    const mk = $('#marker');
    const p = locate(state.pos);
    state.loc = p;
    if (!p) { mk.hidden = true; renderStatus(); return; }
    mk.hidden = false;
    mk.style.transform = `translate(${p.x.toFixed(1)}px, ${p.top.toFixed(1)}px)`;
    mk.style.height = (p.bottom - p.top).toFixed(1) + 'px';
    renderStatus();
    renderVerse();
  }

  function hitTest(x, y) {
    const g = state.geom;
    if (!g || !g.systems.length) return null;
    let si = 0, best = Infinity;
    g.systems.forEach((s, i) => {
      const d = y < s.box.t ? s.box.t - y : (y > s.box.b ? y - s.box.b : 0);
      if (d < best) { best = d; si = i; }
    });
    const sys = g.systems[si];
    let mg = null;
    for (const mi of sys.ms) {
      const m = g.meas[mi];
      if (x >= m.left && x < m.right) { mg = m; break; }
    }
    if (!mg) mg = x < g.meas[sys.ms[0]].left ? g.meas[sys.ms[0]] : g.meas[sys.ms[sys.ms.length - 1]];
    let beat = 0, bd = Infinity;
    for (let k = 0; k < mg.pts.length - 1; k++) {
      const d = Math.abs(mg.pts[k][1] - x);
      if (d < bd) { bd = d; beat = mg.pts[k][0]; }
    }
    return { mi: mg.mi, beat, x: interp(mg.pts, beat), sys };
  }

  // which time through a repeated bar the click means: stay in the current pass when that bar is in it
  function instanceFor(mi) {
    const ins = state.data.instances;
    const cands = [];
    ins.forEach((it, i) => { if (it.m === mi) cands.push(i); });
    if (cands.length <= 1) return cands[0];
    const cur = ins[instAt(state.pos)].p;
    const same = cands.find((i) => ins[i].p === cur);
    return same != null ? same : cands[0];
  }

  // ------------------------------------------------------------------ transport
  function play() {
    if (!state.data) return;
    stopPronunciation();
    if (state.pos >= state.data.duration - 0.02) state.pos = 0;
    state.playFrom = state.pos;
    if (!audio.start(state.pos)) return;
    state.playing = true;
    renderTransport();
    requestAnimationFrame(frame);
  }
  function pause() {
    if (!state.playing) return;
    state.pos = Math.max(state.playFrom, Math.min(audio.now(), state.data.duration));
    audio.halt();
    state.playing = false;
    renderTransport();
    drawMarker();
  }
  function finished() {
    audio.halt();
    state.playing = false;
    state.pos = state.playFrom; // back to where this run started, ready to go again
    renderTransport();
    drawMarker();
  }
  function frame() {
    if (!state.playing) return;
    state.pos = Math.max(state.playFrom, Math.min(audio.now(), state.data.duration));
    drawMarker();
    autoScroll();
    requestAnimationFrame(frame);
  }
  function seek(T) {
    state.pos = T;
    state.playFrom = T;
    if (state.playing) audio.start(T);
    drawMarker();
  }
  function autoScroll() {
    const p = state.loc;
    if (!p || p.sys === state.lastSys) return;
    state.lastSys = p.sys;
    const sys = state.geom.systems[p.sys];
    const pr = $('#paper').getBoundingClientRect();
    const top = pr.top + Math.min(sys.box.t, sys.top) - 10;
    const bottom = pr.top + sys.box.b + 10;
    const viewTop = $('#controls').getBoundingClientRect().bottom + 6;
    const viewBottom = window.innerHeight;
    if (top < viewTop || bottom > viewBottom) {
      const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      window.scrollBy({ top: top - viewTop, behavior: reduce ? 'auto' : 'smooth' });
    }
  }

  // ------------------------------------------------------------------ pitch pipe
  function noteAt(v, T) {
    let sounding = null;
    for (const n of state.data.notes) {
      if (n.v !== v) continue;
      if (n.t0 <= T + 1e-3 && n.t1 > T + 1e-3) sounding = n;
      else if (n.t0 > T + 1e-3) return sounding || n; // notes are sorted by start time
    }
    return sounding;
  }
  function giveNotes() {
    if (!state.data) return;
    if (state.playing) pause();
    stopPronunciation();
    const ctx = audio.ensure();
    if (!ctx) return;
    audio.silence();
    const T = state.pos >= state.data.duration - 0.02 ? 0 : state.pos;
    let t = ctx.currentTime + 0.06;
    [2, 1, 0].forEach((v) => { // Low, Harmony, Melody
      const n = noteAt(v, T);
      if (!n) return;
      n.p.forEach((m) => audio.tone(audio.pipeBus, audio.waves.reed, m, t, t + 1.05, PIPE_ENV));
      const delay = Math.max(0, (t - ctx.currentTime) * 1000);
      audio.pipeTimers.push(setTimeout(() => showPipe(v, n), delay));
      audio.pipeTimers.push(setTimeout(() => clearPipeUI(v), delay + 1150));
      t += 1.3;
    });
  }
  function showPipe(v, n) {
    clearPipeUI();
    const b = $('#voice-' + v);
    b.classList.add('sounding');
    b.querySelector('.pip').textContent = (n.n || []).join(' ');
  }
  function clearPipeUI(v) {
    document.querySelectorAll('.voice-btn').forEach((b) => {
      if (v != null && b.dataset.v !== String(v)) return;
      b.classList.remove('sounding');
      b.querySelector('.pip').textContent = '';
    });
  }

  // ------------------------------------------------------------------ rendering
  const fmt = (s) => { s = Math.max(0, Math.round(s)); return Math.floor(s / 60) + ':' + String(s % 60).padStart(2, '0'); };
  function ordinal(n) { return n + (n === 1 ? 'st' : n === 2 ? 'nd' : n === 3 ? 'rd' : 'th'); }
  let statusMsg = '';
  let statusTimer = null;
  function setStatus(msg) {
    statusMsg = msg;
    clearTimeout(statusTimer);
    statusTimer = setTimeout(() => { statusMsg = ''; renderStatus(); }, 4000);
    renderStatus();
  }
  function renderStatus() {
    const el = $('#status');
    if (statusMsg) { el.textContent = statusMsg; return; }
    const p = state.loc, d = state.data;
    if (!p || !d) { el.textContent = ''; return; }
    let where = `Bar <b>${p.m + 1}</b>`;
    if (timesBarIsPlayed(p.m) > 1) where += d.passLabel === 'verse' ? ` · verse ${p.pass}` : ` · ${ordinal(p.pass)} time`;
    el.innerHTML = `${where} · ${fmt(state.pos)} / ${fmt(d.duration)}`;
  }
  function renderVerse() {
    const d = state.data;
    const want = state.playing && d && d.passLabel === 'verse' && d.verses > 1 && state.loc ? state.loc.pass : 0;
    if (want === state.verseOn || !state.svg) return;
    state.svg.querySelectorAll('.verse-active').forEach((el) => el.classList.remove('verse-active'));
    if (want) state.svg.querySelectorAll(`g.verse[data-n="${want}"]`).forEach((el) => el.classList.add('verse-active'));
    state.verseOn = want;
  }
  function renderTransport() {
    $('#playText').textContent = state.playing ? 'Pause' : 'Play';
    $('#playBtn').setAttribute('aria-label', state.playing ? 'Pause' : 'Play');
    $('#playIcon').innerHTML = state.playing
      ? '<path d="M7 5h3.5v14H7zM13.5 5H17v14h-3.5z" fill="currentColor"/>'
      : '<path d="M8 5.5v13l11-6.5z" fill="currentColor"/>';
    renderVerse();
  }
  function renderHideNotes() {
    $('#svgHost').classList.toggle('notes-hidden', state.hideNotes);
    $('#hideBtn').setAttribute('aria-pressed', String(state.hideNotes));
    $('#hideText').textContent = state.hideNotes ? 'Show notes' : 'Hide notes';
  }
  function renderVoice() {
    document.querySelectorAll('.voice-btn').forEach((b) => {
      b.setAttribute('aria-checked', String(Number(b.dataset.v) === state.voice));
      b.tabIndex = Number(b.dataset.v) === state.voice ? 0 : -1;
    });
    renderMix();
    drawBands();
  }
  function renderMix() {
    const name = VOICES[state.voice];
    $('#mix').value = String(state.mix);
    $('#mix').setAttribute('aria-valuetext', MIX_TEXT[state.mix - 1](name));
    document.querySelectorAll('.tick').forEach((t) => t.setAttribute('aria-pressed', String(Number(t.dataset.level) === state.mix)));
  }
  function renderSongList() {
    const list = $('#songList'), chips = $('#songChips');
    list.innerHTML = '';
    chips.innerHTML = '';
    state.songs.forEach((s, i) => {
      const a = document.createElement('a');
      a.className = 'song-link';
      a.href = '#' + s.id;
      a.dataset.id = s.id;
      a.innerHTML = '<span class="song-num"></span><span class="song-title"></span><span class="song-dur"></span>';
      a.querySelector('.song-num').textContent = String(i + 1);
      a.querySelector('.song-title').textContent = s.title;
      a.querySelector('.song-dur').textContent = fmt(s.duration) + (s.passes > 1 ? (s.id === 'bleak-midwinter' ? ' · 3 verses' : ' · with repeat') : '');
      list.appendChild(a);
      const c = document.createElement('a');
      c.className = 'chip';
      c.href = '#' + s.id;
      c.dataset.id = s.id;
      c.textContent = s.short;
      chips.appendChild(c);
    });
  }
  function markCurrentSong() {
    document.querySelectorAll('.song-link, .chip').forEach((a) => a.setAttribute('aria-current', String(a.dataset.id === state.song.id)));
  }

  // ------------------------------------------------------------------ pronunciation (Swedish songs)
  let pronObjectUrl = null;
  function stopPronunciation() {
    const a = $('#pronAudio');
    if (a && !a.paused) a.pause();
  }
  function renderPronunciation(song) {
    const box = $('#pron'), el = $('#pronAudio'), p = song.pronunciation;
    stopPronunciation();
    if (pronObjectUrl) { URL.revokeObjectURL(pronObjectUrl); pronObjectUrl = null; }
    if (!p) {
      box.hidden = true;
      el.removeAttribute('src');
      el.load();
      return;
    }
    box.hidden = false;
    $('#pronCredit').textContent = p.credit || '';
    if (IS_ARTIFACT) { // claude.ai previews reach their own files only through fetch
      el.removeAttribute('src');
      fetch(p.audio).then((r) => (r.ok ? r.blob() : Promise.reject(r.status))).then((b) => {
        if (state.song !== song) return;
        pronObjectUrl = URL.createObjectURL(b);
        el.src = pronObjectUrl;
      }).catch(() => { /* leave the player empty */ });
    } else {
      el.src = p.audio;
    }
    const lines = $('#pronLines');
    lines.innerHTML = '';
    for (const [sv, say] of p.lines) {
      const li = document.createElement('li');
      const a = document.createElement('span');
      a.className = 'sv'; a.lang = 'sv'; a.textContent = sv;
      const b = document.createElement('span');
      b.className = 'say'; b.textContent = say;
      li.append(a, b);
      lines.appendChild(li);
    }
    $('#pronNote').textContent = p.note || '';
    const tips = $('#pronTips');
    tips.innerHTML = '';
    for (const [k, v] of p.tips || []) {
      const dt = document.createElement('dt');
      dt.lang = 'sv'; dt.textContent = k;
      const dd = document.createElement('dd');
      dd.textContent = v;
      tips.append(dt, dd);
    }
  }

  // ------------------------------------------------------------------ loading
  async function fetchText(url) {
    if (cache.has(url)) return cache.get(url);
    const r = await fetch(url);
    if (!r.ok) throw new Error(url + ': ' + r.status);
    const t = await r.text();
    cache.set(url, t);
    return t;
  }
  function chooseLayout() {
    return $('#paper').clientWidth < 640 ? 'narrow' : 'wide';
  }
  async function renderScore(force) {
    if (!state.song || !state.data) return;
    const layout = chooseLayout();
    if (!force && layout === state.layout && state.svg) {
      buildGeom(); drawBands(); drawMarker();
      return;
    }
    const token = state.token;
    const text = await fetchText(`scores/${state.song.id}.${layout}.svg`);
    if (token !== state.token) return;
    state.layout = layout;
    const host = $('#svgHost');
    host.innerHTML = text;
    state.svg = host.querySelector('svg');
    state.svg.removeAttribute('width');
    state.svg.removeAttribute('height');
    state.svg.setAttribute('role', 'img');
    state.svg.setAttribute('aria-label', `Sheet music: ${state.song.title}`);
    state.verseOn = 0;
    buildGeom(); drawBands(); drawMarker();
  }
  async function loadSong(id) {
    const song = state.songs.find((s) => s.id === id) || state.songs[0];
    if (state.song && song.id === state.song.id && state.data) return;
    if (state.playing) pause();
    audio.silence();
    state.song = song;
    state.data = null; state.svg = null; state.geom = null; state.loc = null;
    state.pos = 0; state.playFrom = 0;
    const token = ++state.token;
    markCurrentSong();
    $('#songTitle').textContent = song.title;
    const meta = [song.subtitle, ...(song.credits || [])].filter(Boolean);
    $('#songMeta').textContent = meta.join(' · ');
    document.title = `${song.title} · Lucia Choir`;
    const fileName = song.title.replace(/[\/:]+/g, '-').replace(/\s+-\s+/g, ' - ');
    [['#pdfBtn', `pdf/${song.id}.pdf`, `${fileName}.pdf`], ['#mp3Btn', `mp3/${song.id}.mp3`, `${fileName} (all parts).mp3`]]
      .forEach(([sel, href, name]) => {
        const a = $(sel);
        if (IS_ARTIFACT) { // claude.ai previews cannot download files
          a.removeAttribute('download');
          a.setAttribute('aria-disabled', 'true');
          a.href = '#' + song.id;
          a.title = 'Downloads work on the public website';
        } else {
          a.href = href;
          a.setAttribute('download', name);
        }
      });
    renderPronunciation(song);
    $('#svgHost').innerHTML = '<div class="loading">Loading the music…</div>';
    $('#bands').innerHTML = '';
    $('#marker').hidden = true;
    renderStatus();
    try {
      const data = JSON.parse(await fetchText(`scores/${song.id}.json`));
      if (token !== state.token) return;
      state.data = data;
      await renderScore(true);
    } catch (e) {
      $('#svgHost').innerHTML = '<div class="loading">The music could not be loaded. Check your connection and reload the page.</div>';
    }
  }
  function currentHash() {
    const h = decodeURIComponent((location.hash || '').slice(1));
    return state.songs.some((s) => s.id === h) ? h : state.songs[0].id;
  }

  // ------------------------------------------------------------------ events
  function bind() {
    document.querySelectorAll('.voice-btn').forEach((b) => b.addEventListener('click', () => {
      state.voice = Number(b.dataset.v);
      store.set('voice', state.voice);
      renderVoice();
      audio.applyMix(false);
    }));
    $('#voices').addEventListener('keydown', (e) => {
      if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
      e.preventDefault();
      state.voice = (state.voice + (e.key === 'ArrowRight' ? 1 : 2)) % 3;
      store.set('voice', state.voice);
      renderVoice();
      audio.applyMix(false);
      $('#voice-' + state.voice).focus();
    });
    const ticks = $('#ticks');
    TICKS.forEach((label, i) => {
      const t = document.createElement('button');
      t.type = 'button';
      t.className = 'tick';
      t.dataset.level = String(i + 1);
      t.textContent = label;
      t.addEventListener('click', () => { state.mix = i + 1; store.set('mix', state.mix); renderMix(); audio.applyMix(false); });
      ticks.appendChild(t);
    });
    $('#mix').addEventListener('input', (e) => {
      state.mix = clampInt(e.target.value, 1, 5);
      store.set('mix', state.mix);
      renderMix();
      audio.applyMix(false);
    });
    $('#playBtn').addEventListener('click', () => (state.playing ? pause() : play()));
    $('#notesBtn').addEventListener('click', giveNotes);
    $('#rewindBtn').addEventListener('click', () => { seek(0); state.lastSys = -1; window.scrollTo({ top: 0, behavior: 'smooth' }); });
    ['#pdfBtn', '#mp3Btn'].forEach((sel) => $(sel).addEventListener('click', (e) => {
      if (IS_ARTIFACT) { e.preventDefault(); setStatus('Downloads work on the public website.'); }
    }));
    $('#hideBtn').addEventListener('click', () => { state.hideNotes = !state.hideNotes; renderHideNotes(); });
    $('#pronToggle').addEventListener('click', () => {
      const guide = $('#pronGuide');
      const open = guide.hidden;
      guide.hidden = !open;
      $('#pronToggle').setAttribute('aria-expanded', String(open));
      $('#pronToggle').textContent = open ? 'Hide the words' : 'Show the words';
    });
    // Hanna's recording and the practice playback never sound at the same time
    $('#pronAudio').addEventListener('play', () => { if (state.playing) pause(); audio.silence(); });

    const paper = $('#paper');
    paper.addEventListener('click', (e) => {
      if (!state.data) return;
      const pr = paper.getBoundingClientRect();
      const hit = hitTest(e.clientX - pr.left, e.clientY - pr.top);
      if (!hit) return;
      const ii = instanceFor(hit.mi);
      if (ii == null) return;
      seek(timeAt(ii, hit.beat));
    });
    const ghost = $('#ghost');
    let pending = false;
    paper.addEventListener('pointermove', (e) => {
      if (e.pointerType !== 'mouse' || pending) return;
      pending = true;
      requestAnimationFrame(() => {
        pending = false;
        const pr = paper.getBoundingClientRect();
        const hit = hitTest(e.clientX - pr.left, e.clientY - pr.top);
        if (!hit) { ghost.classList.remove('on'); return; }
        ghost.classList.add('on');
        ghost.style.transform = `translate(${hit.x.toFixed(1)}px, ${hit.sys.top.toFixed(1)}px)`;
        ghost.style.height = (hit.sys.bottom - hit.sys.top).toFixed(1) + 'px';
      });
    });
    paper.addEventListener('pointerleave', () => ghost.classList.remove('on'));

    document.addEventListener('keydown', (e) => {
      if (e.code !== 'Space' && e.key !== ' ') return;
      if (e.target && (e.target.tagName === 'INPUT' && e.target.type !== 'range')) return;
      e.preventDefault();
      if (e.target && e.target.blur) e.target.blur();
      state.playing ? pause() : play();
    });

    let rz = null;
    window.addEventListener('resize', () => { clearTimeout(rz); rz = setTimeout(() => renderScore(false), 150); });
    window.addEventListener('hashchange', () => loadSong(currentHash()));
    document.addEventListener('visibilitychange', () => { if (state.playing) audio.pump(); });
  }

  async function init() {
    bind();
    renderVoice();
    try {
      state.songs = JSON.parse(await fetchText('scores/index.json'));
    } catch (e) {
      $('#svgHost').innerHTML = '<div class="loading">The song list could not be loaded. Reload the page to try again.</div>';
      return;
    }
    renderSongList();
    await loadSong(currentHash());
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(() => renderScore(false));
  }

  if (/[?&]debug\b/.test(location.search)) {
    window.__luciaDebug = {
      state, locate, timeAt,
      // used by src/make_mp3.py: render a song with all parts equal and hand it over as a WAV download
      async downloadWav(id) {
        const data = JSON.parse(await fetchText(`scores/${id}.json`));
        const blob = await renderAllPartsWav(data);
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = `${id}.wav`;
        document.body.appendChild(a);
        a.click();
        a.remove();
      },
    };
  }
  init();
})();

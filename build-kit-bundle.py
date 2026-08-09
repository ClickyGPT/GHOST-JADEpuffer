#!/usr/bin/env python3
"""Build kit-bundle.json (sidecar) and inject the in-page document viewer
(css + markup + js + embedded JSON fallback) into explain-jadepuffer-ghost-hunt.html.

Re-run this whenever a mapped document changes:
    python .freebuff/build-kit-bundle.py
    python .freebuff/build-kit-bundle.py --check   # drift check (CI): rebuild in
                                                   # memory, diff vs committed artifacts
"""

import datetime
import json
import os
import re as _re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))  # .freebuff/
ROOT = os.path.dirname(HERE)  # repo root
HTML = os.path.join(HERE, "explain-jadepuffer-ghost-hunt.html")
OUT = os.path.join(HERE, "kit-bundle.json")
CAP = 200000  # per-file content cap (no mapped file currently exceeds it)

# (repo-relative path, one-line summary shown in the viewer header)
FILES = [
    ("README.md", "entry point — project overview"),
    ("GHOST-HUNT-README.md", "kit overview & file map"),
    ("SYSTEM_GHOST_HUNT.md", "operating framework v2.2"),
    ("obufscat.md", "typography doctrine"),
    ("GHOST-HUNT-SYSTEM-PROMPT.md", "prompt kit v1.0"),
    ("GHOST-HUNT-SYSTEM-PROMPT1.md", "prompt kit v2.2"),
    ("GHOST-HUNT-SYSTEM-PROMPT-CONDENSED.md", "prompt kit v1.0 · condensed"),
    ("GHOST-HUNT-SYSTEM-PROMPT1-CONDENSED.md", "prompt kit v2.2 · condensed"),
    ("GHOST-HUNT-SYSTEM-PROMPT-CONDENSED.json", "prompt kit v1.0 · condensed (JSON)"),
    ("GHOST-HUNT-SYSTEM-PROMPT1-CONDENSED.json", "prompt kit v2.2 · condensed (JSON)"),
    ("GHOST-HUNT-EXFIL-PLAYBOOK.md", "6 exfil scenarios (EX-CRED → EX-STAGE)"),
    ("GHOST-HUNT-C2-ENVIRONMENT.md", "C2 infra playbook"),
    ("GHOST-HUNT-IR-PLAYBOOK.md", "incident response playbook"),
    ("GHOST-HUNT-JADEPUFFER-THREAT-PROFILE.md", "JADEPUFFER threat profile"),
    ("GHOST-HUNT-JADEPUFFER-ATTACK-MAPPING.md", "MITRE ATT&CK v14.1 mapping"),
    ("AGENTICAUTOMATION/AGENTICAUTOMATION-OPENCOE.md", "OpenCoe harness prompt"),
    ("AGENTICAUTOMATION/AGENTICAUTOMATION-OPENCOE.json", "OpenCoe harness (JSON)"),
    ("AGENTICAUTOMATION/AGENTICAUTOMATION-HERMES.md", "Hermes harness prompt"),
    ("AGENTICAUTOMATION/AGENTICAUTOMATION-HERMES.json", "Hermes harness (JSON)"),
    ("AGENTICAUTOMATION/AGENTICAUTOMATION-FREEBUIFF.md", "Freebuiff harness prompt"),
    ("AGENTICAUTOMATION/AGENTICAUTOMATION-FREEBUIFF.json", "Freebuiff harness (JSON)"),
    ("GHOST-HUNT-C2-KIT/bootstrap-server.sh", "one-shot VPS deploy"),
    ("GHOST-HUNT-C2-KIT/handler.py", "C2 receiver (source of truth)"),
    ("GHOST-HUNT-C2-KIT/exfil.py", "target-side client"),
    ("GHOST-HUNT-C2-KIT/pull.py", "reassemble + decrypt"),
    ("GHOST-HUNT-C2-KIT/burn.sh", "clean takedown"),
    ("GHOST-HUNT-C2-KIT/server.env.example", "config template"),
    ("GHOST-HUNT-C2-KIT/test/local_harness.py", "localhost smoke test"),
    ("GHOST-HUNT-C2-KIT/README.md", "HTTPS kit: deploy / exfil / pull / burn"),
    ("GHOST-HUNT-C2-KIT-DNS/bootstrap-dns-server.sh", "one-shot DNS deploy"),
    ("GHOST-HUNT-C2-KIT-DNS/dns_handler.py", "DNS receiver"),
    ("GHOST-HUNT-C2-KIT-DNS/dns_exfil.py", "stdlib DNS client"),
    ("GHOST-HUNT-C2-KIT-DNS/dns_pull.py", "query-log reconstruction"),
    ("GHOST-HUNT-C2-KIT-DNS/burn-dns.sh", "takedown"),
    ("GHOST-HUNT-C2-KIT-DNS/test/local_dns_harness.py", "localhost smoke test"),
    ("GHOST-HUNT-C2-KIT-DNS/README.md", "DNS kit: deploy / exfil (A/B/C) / burn"),
    ("VALIDATION.md", "measured throughput + quality gates (both C2 kits)"),
    ("DEPLOYMENT_CHECKLIST_C2_KITS.md", "deployment runbook: bootstrap / env / TLS / burn"),
    (".github/workflows/smoke.yml", "CI: smoke + lint/typecheck + stress + drift"),
]

LANGS = {
    "py": "python",
    "sh": "bash",
    "md": "markdown",
    "json": "json",
    "env": "dotenv",
    "example": "dotenv",
    "txt": "text",
}


def lang_of(path):
    ext = path.rsplit(".", 1)[-1].lower()
    return LANGS.get(ext, ext)


def load(path):
    full = os.path.join(ROOT, path)
    with open(full, "rb") as fh:
        raw = fh.read().decode("utf-8", errors="replace")
    # Embed canonical LF endings so the bundle is immune to worktree
    # line-ending conventions (e.g. Windows core.autocrlf checkouts).
    raw = raw.replace("\r\n", "\n").replace("\r", "\n")
    truncated = len(raw) > CAP
    return raw[:CAP], truncated


# ---------------------------------------------------------------------------
# Viewer CSS / markup / JS (kept here so the HTML stays free of giant literals)
# ---------------------------------------------------------------------------
VIEWER_CSS = r"""
.kit-hint{font-size:12.5px;color:var(--muted);margin:2px 0 14px;max-width:780px;line-height:1.7}
.kit-hint code{background:rgba(52,211,153,.1);color:#7ee2b4;padding:1px 5px;border-radius:4px;font-family:var(--mono);font-size:.92em}
.kitdrawer{position:fixed;inset:0;z-index:999;display:flex;justify-content:flex-end;visibility:hidden}
.kitdrawer[hidden]{display:none}
.kitdrawer.kd-on{visibility:visible}
.kd-backdrop{position:absolute;inset:0;background:rgba(3,6,5,.62);backdrop-filter:blur(2px);opacity:0;transition:opacity .25s ease}
.kitdrawer.kd-on .kd-backdrop{opacity:1}
.kd-panel{position:relative;width:min(640px,100vw);height:100%;background:var(--bg2);border-left:1px solid var(--line2);box-shadow:-14px 0 40px rgba(0,0,0,.5);display:flex;flex-direction:column;transform:translateX(103%);transition:transform .3s cubic-bezier(.22,.9,.3,1)}
.kitdrawer.kd-on .kd-panel{transform:none}
.kd-head{border-bottom:1px solid var(--line);padding:14px 20px;background:linear-gradient(180deg,var(--panel),var(--bg2))}
.kd-headrow{display:flex;gap:12px;align-items:flex-start;justify-content:space-between}
.kd-pathwrap{min-width:0;flex:1}
.kd-path{font-family:var(--mono);font-size:13px;font-weight:700;color:var(--jade);word-break:break-all;line-height:1.4}
.kd-meta{font-size:11px;color:var(--dim);margin-top:3px;display:flex;flex-wrap:wrap;gap:6px;align-items:center}
.kd-meta span{white-space:nowrap}
.kd-dot{opacity:.5}
.kd-actions{display:flex;gap:8px;align-items:center;flex-wrap:wrap;justify-content:flex-end}
.kd-vars{display:inline-flex;align-items:center;gap:6px;font-size:11px;color:var(--dim)}
.kd-vars select{background:var(--panel2);color:var(--text);border:1px solid var(--line2);border-radius:6px;padding:4px 6px;font-size:11px;font-family:var(--mono);max-width:190px}
.kd-open{font-size:11px;color:var(--jade);text-decoration:none;border:1px solid var(--jade-dim);border-radius:6px;padding:4px 9px;white-space:nowrap;transition:all .15s}
.kd-open:hover{background:rgba(52,211,153,.1);border-color:var(--jade)}
.kd-close{background:none;border:none;color:var(--muted);font-size:16px;cursor:pointer;padding:2px 8px;border-radius:6px;transition:all .15s}
.kd-close:hover{color:var(--text);background:var(--panel2)}
.kd-body{flex:1;overflow-y:auto;padding:20px 24px;overscroll-behavior:contain}
.kd-loading{color:var(--dim);font-family:var(--mono);font-size:12px}
.kd-miss{color:var(--ember);font-size:13px}
.kd-raw{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:16px;overflow-x:auto;font-family:var(--mono);font-size:12.3px;line-height:1.6;white-space:pre;color:var(--text)}
.kd-raw code{font-family:inherit}
.kd-md h1,.kd-md h2,.kd-md h3,.kd-md h4,.kd-md h5,.kd-md h6{color:var(--text);margin:1.3em 0 .5em;line-height:1.3}
.kd-md h1{font-size:19px;border-bottom:1px solid var(--line);padding-bottom:8px}
.kd-md h2{font-size:16px;color:var(--jade)}
.kd-md h3{font-size:14px}
.kd-md h4{font-size:13px;color:var(--muted)}
.kd-md p{margin:.6em 0;font-size:13.2px;color:var(--text)}
.kd-md ul,.kd-md ol{margin:.6em 0 .6em 1.4em;font-size:13.2px}
.kd-md li{margin:.25em 0}
.kd-md code{background:rgba(52,211,153,.1);color:#7ee2b4;padding:1px 5px;border-radius:4px;font-family:var(--mono);font-size:.9em}
.kd-md pre.kd-code{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:14px 16px;overflow-x:auto;font-family:var(--mono);font-size:12.3px;line-height:1.55;margin:1em 0;white-space:pre;color:var(--text)}
.kd-md pre.kd-code code{background:none;padding:0;color:var(--text)}
.kd-md table{border-collapse:collapse;margin:1em 0;font-size:12.5px;width:100%}
.kd-md th{background:var(--panel2);color:var(--jade);text-align:left;font-family:var(--mono);font-size:11.5px;padding:7px 10px;border:1px solid var(--line2)}
.kd-md td{padding:6px 10px;border:1px solid var(--line);vertical-align:top;color:var(--text)}
.kd-md tr:nth-child(even) td{background:rgba(255,255,255,.015)}
.kd-md blockquote{border-left:3px solid var(--jade-dim);padding:2px 0 2px 14px;margin:1em 0;color:var(--muted);font-size:13px}
.kd-md blockquote p{color:var(--muted)}
.kd-md hr{border:none;border-top:1px solid var(--line);margin:1.4em 0}
.kd-md a{color:var(--jade);text-decoration:none;border-bottom:1px dotted rgba(52,211,153,.4)}
.kd-md a:hover{color:#8ff0c7}
.kd-md a.kdl{cursor:pointer}
.kd-foot{display:flex;align-items:center;justify-content:space-between;gap:10px;border-top:1px solid var(--line);padding:10px 20px;background:var(--panel)}
.kd-nav{background:var(--panel2);border:1px solid var(--line2);color:var(--muted);border-radius:6px;padding:5px 12px;font-size:11.5px;cursor:pointer;transition:all .15s}
.kd-nav:hover:not(:disabled){color:var(--jade);border-color:var(--jade-dim)}
.kd-nav:disabled{opacity:.35;cursor:default}
.kd-pos{font-family:var(--mono);font-size:11px;color:var(--dim)}
body.kd-lock{overflow:hidden}
@media (max-width:720px){.kd-panel{width:100vw}.kd-vars{display:none}.kd-headrow{flex-direction:column}}
@media (prefers-reduced-motion:reduce){.kd-panel,.kd-backdrop{transition:none}}
#kdSrc.kd-flash{animation:kdflash 1.4s ease}
@keyframes kdflash{0%{background:rgba(52,211,153,.4);color:#8ff0c7}100%{background:transparent}}
@media (prefers-reduced-motion:reduce){#kdSrc.kd-flash{animation:none}}
"""

VIEWER_MARKUP = r"""
    <div class="kitdrawer" id="kitDrawer" hidden aria-hidden="true">
      <div class="kd-backdrop" id="kdBackdrop"></div>
      <aside class="kd-panel" role="dialog" aria-modal="true" aria-labelledby="kdPath">
        <header class="kd-head">
          <div class="kd-headrow">
            <div class="kd-pathwrap">
              <div class="kd-path" id="kdPath"></div>
              <div class="kd-meta"><span id="kdSummary"></span><span class="kd-dot">·</span><span id="kdMeta"></span><span class="kd-dot">·</span>source: <span id="kdSrc"></span></div>
            </div>
            <div class="kd-actions">
              <span class="kd-vars" id="kdVars" hidden><label for="kdSel">variant</label><select id="kdSel"></select></span>
              <a class="kd-open" id="kdOpen" href="#" target="_blank" rel="noopener">open on disk ↗</a>
              <button class="kd-close" id="kdClose" aria-label="Close document viewer">✕</button>
            </div>
          </div>
        </header>
        <div class="kd-body" id="kdBody"><p class="kd-loading">Loading document…</p></div>
        <footer class="kd-foot">
          <button class="kd-nav" id="kdPrev" aria-label="Previous document">← prev</button>
          <span class="kd-pos" id="kdPos"></span>
          <button class="kd-nav" id="kdNext" aria-label="Next document">next →</button>
        </footer>
      </aside>
    </div>
"""

VIEWER_JS = r"""
(function(){
  'use strict';
  var BUNDLE_URL = 'kit-bundle.json';
  var drawer = document.getElementById('kitDrawer');
  var bodyEl = document.getElementById('kdBody');
  var pathEl = document.getElementById('kdPath');
  var sumEl = document.getElementById('kdSummary');
  var metaEl = document.getElementById('kdMeta');
  var openEl = document.getElementById('kdOpen');
  var closeEl = document.getElementById('kdClose');
  var backEl = document.getElementById('kdBackdrop');
  var selWrap = document.getElementById('kdVars');
  var selEl = document.getElementById('kdSel');
  var prevEl = document.getElementById('kdPrev');
  var nextEl = document.getElementById('kdNext');
  var posEl = document.getElementById('kdPos');
  var srcEl = document.getElementById('kdSrc');
  var bundle = null, family = [], order = [], current = '', lastFocus = null, closeToken = 0;

  function esc(s){return String(s).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});}
  function norm(p){return String(p||'').replace(/^\.\.\//,'').replace(/^\.\//,'').split('#')[0];}
  function famPrefix(p){
    if(/^GHOST-HUNT-SYSTEM-PROMPT/.test(p)) return 'GHOST-HUNT-SYSTEM-PROMPT';
    if(/^GHOST-HUNT-JADEPUFFER/.test(p)) return 'GHOST-HUNT-JADEPUFFER';
    var m = p.match(/^(AGENTICAUTOMATION\/AGENTICAUTOMATION-[A-Z]+)\.md$/); if(m) return m[1];
    return null;
  }
  function labelFor(f){
    var t = f.path.replace(/\.(md|json)$/,'').replace(/^GHOST-HUNT-/,'').replace(/^AGENTICAUTOMATION\//,'');
    var ext = f.path.split('.').pop();
    var base = t.replace(/-CONDENSED$/,''), v = '';
    if(base === 'SYSTEM-PROMPT') v = 'v1.0'; else if(base === 'SYSTEM-PROMPT1') v = 'v2.2';
    var label = base.replace(/-/g,' ') + (v ? ' · ' + v : '') + (/-CONDENSED$/.test(t) ? ' · condensed' : '');
    if(ext !== 'md') label += ' · ' + ext.toUpperCase();
    return label;
  }
  function loadBundle(){
    if(bundle) return Promise.resolve(bundle);
    return fetch(BUNDLE_URL, {cache:'no-store'})
      .then(function(r){ if(!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
      .then(function(b){ bundle = b; bundle._src = 'sidecar'; lastFinger = finger(bundle); return b; })
      .catch(function(){
        var el = document.getElementById('kit-bundle-data');
        bundle = JSON.parse(el.textContent); bundle._src = 'embedded fallback';
        lastFinger = finger(bundle);
        return bundle;
      });
  }
  function inlineMD(s){
    s = s.replace(/`([^`]+)`/g,'<code>$1</code>');
    s = s.replace(/\*\*([^*]+)\*\*/g,'<b>$1</b>');
    s = s.replace(/(^|[^*])\*([^*\n]+)\*(?!\*)/g,'$1<i>$2</i>');
    s = s.replace(/\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g,'<a href="$2" target="_blank" rel="noopener">$1</a>');
    s = s.replace(/\[([^\]]+)\]\(([^)\s]+)\)/g,function(m,t,h){
      var n = norm(h);
      if(n && n !== h && n.indexOf('http') !== 0) return '<a class="kdl" href="#" data-kit="' + esc(n) + '">' + esc(t) + '</a>';
      return m;
    });
    return s;
  }
  function renderMD(src){
    var lines = String(src).replace(/\r\n?/g,'\n').split('\n');
    var out = [], i = 0;
    while(i < lines.length){
      var l = lines[i];
      if(/^\s*```/.test(l)){
        var buf = [], j = i + 1;
        while(j < lines.length && !/^\s*```/.test(lines[j])){buf.push(lines[j]); j++;}
        out.push('<pre class="kd-code"><code>' + esc(buf.join('\n')) + '</code></pre>');
        i = j + 1; continue;
      }
      if(/^\s*\|/.test(l)){
        var rows = [], j = i;
        while(j < lines.length && /^\s*\|/.test(lines[j])){rows.push(lines[j]); j++;}
        if(rows.length >= 2 && /^\s*\|[\s:|-]+\|\s*$/.test(rows[1])){
          var head = rows[0].split('|').slice(1,-1).map(function(c){return c.trim();});
          var body = rows.slice(2);
          var html = '<table><thead><tr>' + head.map(function(c){return '<th>' + inlineMD(c) + '</th>';}).join('') + '</tr></thead><tbody>';
          body.forEach(function(r){
            var cells = r.split('|').slice(1,-1).map(function(c){return c.trim();});
            html += '<tr>' + cells.map(function(c){return '<td>' + inlineMD(c) + '</td>';}).join('') + '</tr>';
          });
          out.push(html + '</tbody></table>'); i = j; continue;
        }
      }
      var m = l.match(/^(#{1,6})\s+(.*)$/);
      if(m){var h = Math.min(m[1].length + 1, 6); out.push('<h' + h + '>' + inlineMD(m[2]) + '</h' + h + '>'); i++; continue;}
      if(/^\s*(-{3,}|\*{3,}|_{3,})\s*$/.test(l)){out.push('<hr>'); i++; continue;}
      if(/^\s*>\s?/.test(l)){
        var q = [], j = i;
        while(j < lines.length && /^\s*>\s?/.test(lines[j])){q.push(lines[j].replace(/^\s*>\s?/,'')); j++;}
        out.push('<blockquote>' + renderMD(q.join('\n')) + '</blockquote>'); i = j; continue;
      }
      if(/^\s*[-*+]\s+/.test(l) || /^\s*\d+[.)]\s+/.test(l)){
        var items = [], j = i, ordered = /^\s*\d+[.)]\s+/.test(l);
        while(j < lines.length){
          var t = lines[j];
          if(/^\s*[-*+]\s+/.test(t)){items.push(t.replace(/^\s*[-*+]\s+/,'')); ordered = false;}
          else if(/^\s*\d+[.)]\s+/.test(t)){items.push(t.replace(/^\s*\d+[.)]\s+/,'')); ordered = true;}
          else break;
          j++;
        }
        var tag = ordered ? 'ol' : 'ul';
        out.push('<' + tag + '>' + items.map(function(x){return '<li>' + inlineMD(x) + '</li>';}).join('') + '</' + tag + '>');
        i = j; continue;
      }
      if(l.trim() === ''){i++; continue;}
      var para = [l], j = i + 1;
      while(j < lines.length && lines[j].trim() !== '' && !/^\s*(#{1,6}\s|[-*+]\s|\d+[.)]\s|```|\||>)/.test(lines[j])){para.push(lines[j]); j++;}
      out.push('<p>' + inlineMD(para.join(' ')) + '</p>');
      i = j;
    }
    return out.join('\n');
  }
  function buildOrder(){
    order = [];
    document.querySelectorAll('.repomap a').forEach(function(a){order.push(norm(a.getAttribute('href')));});
  }
  function buildSelector(){
    if(family.length > 1){
      selWrap.hidden = false; selEl.innerHTML = '';
      family.forEach(function(f){
        var o = document.createElement('option'); o.value = f.path; o.textContent = labelFor(f);
        if(f.path === current) o.selected = true; selEl.appendChild(o);
      });
    } else selWrap.hidden = true;
  }
  function updateFoot(){
    var idx = order.indexOf(current);
    prevEl.disabled = idx <= 0; nextEl.disabled = idx < 0 || idx >= order.length - 1;
    posEl.textContent = (idx >= 0 ? idx + 1 : '\u2014') + ' / ' + order.length;
  }
  function renderCurrent(){
    pathEl.textContent = current;
    var f = null;
    for(var k = 0; k < family.length; k++){if(family[k].path === current){f = family[k]; break;}}
    if(!f){
      bodyEl.innerHTML = '<p class="kd-miss">This file isn\u2019t in the bundle: <code>' + esc(current) + '</code></p>';
      return;
    }
    sumEl.textContent = f.summary || '';
    var b = f.bytes, bt = b >= 1048576 ? (b/1048576).toFixed(2) + ' MB' : b >= 1024 ? (b/1024).toFixed(1) + ' KB' : b + ' B';
    metaEl.textContent = bt + (f.truncated ? ' · truncated' : '') + (f.content ? '' : ' · empty');
    openEl.href = '../' + f.path;
    srcEl.textContent = bundle._src;
    bodyEl.innerHTML = /\.(md|markdown)$/i.test(f.path) ? renderMD(f.content) : '<pre class="kd-raw"><code>' + esc(f.content) + '</code></pre>';
    bodyEl.scrollTop = 0; updateFoot();
  }
  function openDoc(path){
    closeToken++;
    lastFocus = document.activeElement;
    current = path;
    pathEl.textContent = path;
    var fam = famPrefix(path);
    family = fam ? bundle.files.filter(function(f){return f.path.indexOf(fam) === 0;})
                 : bundle.files.filter(function(f){return f.path === path;});
    buildSelector(); renderCurrent();
    drawer.hidden = false; drawer.setAttribute('aria-hidden','false');
    document.body.classList.add('kd-lock');
    requestAnimationFrame(function(){drawer.classList.add('kd-on');});
    closeEl.focus();
  }
  function closeDoc(){
    var t = ++closeToken;
    drawer.classList.remove('kd-on'); drawer.setAttribute('aria-hidden','true');
    document.body.classList.remove('kd-lock');
    setTimeout(function(){if(t === closeToken) drawer.hidden = true;}, 300);
    if(lastFocus && lastFocus.focus) lastFocus.focus();
  }
  function step(d){
    var idx = order.indexOf(current), n = idx + d;
    if(n >= 0 && n < order.length) openDoc(order[n]);
  }
  document.addEventListener('click', function(e){
    var a = e.target.closest ? e.target.closest('a') : null;
    if(!a) return;
    var kd = a.getAttribute('data-kit');
    if(kd){e.preventDefault(); loadBundle().then(function(){openDoc(kd);}); return;}
    if(a.closest('.repomap')){e.preventDefault(); var p = norm(a.getAttribute('href')); loadBundle().then(function(){openDoc(p);});}
  });
  closeEl.addEventListener('click', closeDoc);
  backEl.addEventListener('click', closeDoc);
  selEl.addEventListener('change', function(){current = selEl.value; renderCurrent();});
  prevEl.addEventListener('click', function(){step(-1);});
  nextEl.addEventListener('click', function(){step(1);});
  document.addEventListener('keydown', function(e){
    if(drawer.hidden) return;
    if(e.key === 'Escape') closeDoc();
    else if(e.key === 'ArrowLeft' && !e.target.closest('select,input,textarea')) step(-1);
    else if(e.key === 'ArrowRight' && !e.target.closest('select,input,textarea')) step(1);
  });

  // ---- auto-refresh: re-fetch the sidecar and live-update the open doc ----
  var lastFinger = null, refreshTimer = null, refreshing = false;
  function finger(b){
    // Content-aware: path/bytes/truncated catch structural changes, and hashing
    // the content catches same-length edits (bytes alone would miss those).
    var h = 5381, i, j, s = String(b.generated || '') + '|' + b.files.length + '|';
    for(i = 0; i < b.files.length; i++){
      s += b.files[i].path + '@' + b.files[i].bytes + (b.files[i].truncated ? 'T' : '') + ';';
      var c = b.files[i].content || '';
      for(j = 0; j < c.length; j++){ h = ((h << 5) + h + c.charCodeAt(j)) | 0; }
    }
    for(i = 0; i < s.length; i++){ h = ((h << 5) + h + s.charCodeAt(i)) | 0; }
    return (h >>> 0).toString(36);
  }
  function refreshOpen(){
    if(drawer.hidden || !bundle || !current) return;
    var fam = famPrefix(current);
    family = fam ? bundle.files.filter(function(f){return f.path.indexOf(fam) === 0;})
                 : bundle.files.filter(function(f){return f.path === current;});
    var st = bodyEl.scrollTop;
    buildSelector(); renderCurrent();
    bodyEl.scrollTop = st;
    srcEl.classList.add('kd-flash');
    clearTimeout(srcEl._ft);
    srcEl._ft = setTimeout(function(){srcEl.classList.remove('kd-flash');}, 1400);
  }
  function refreshBundle(){
    if(document.hidden || refreshing) return Promise.resolve(false);
    refreshing = true;
    return fetch(BUNDLE_URL, {cache:'no-store'})
      .then(function(r){ if(!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
      .then(function(fresh){
        var f = finger(fresh);
        bundle = fresh; bundle._src = 'sidecar';
        if(lastFinger === null || f !== lastFinger){
          lastFinger = f;
          refreshOpen();
          return true;
        }
        if(srcEl.textContent !== bundle._src){ srcEl.textContent = bundle._src; }  // sidecar reachable — reflect it even if content is unchanged
        return false;
      })
      .catch(function(){ return false; })
      .then(function(v){ refreshing = false; return v; });
  }
  function scheduleRefresh(){
    clearInterval(refreshTimer);
    refreshTimer = setInterval(function(){
      if(!document.hidden && !drawer.hidden){ refreshBundle(); }
    }, 30000);
  }
  document.addEventListener('visibilitychange', function(){
    if(!document.hidden) refreshBundle();
  });
  window.addEventListener('focus', function(){ if(!drawer.hidden) refreshBundle(); });
  scheduleRefresh();
  buildOrder();
})();
"""


# ---------------------------------------------------------------------------
# Build bundle + inject into HTML
# ---------------------------------------------------------------------------
def build():
    """Return (bundle, sidecar_text, final_html) without writing anything."""
    files = []
    for path, summary in FILES:
        content, truncated = load(path)
        files.append(
            {
                "path": path,
                "summary": summary,
                "lang": lang_of(path),
                "bytes": len(content),
                "truncated": truncated,
                "content": content,
            }
        )
    bundle = {"version": 1, "generated": datetime.date.today().isoformat(), "files": files}
    sidecar = json.dumps(bundle, ensure_ascii=False, indent=1)
    embedded = json.dumps(bundle, ensure_ascii=False, separators=(",", ":"))
    for ch in ("<", ">", "&"):
        embedded = embedded.replace(ch, "\\u%04x" % ord(ch))
    with open(HTML, encoding="utf-8") as fh:
        html = fh.read()
    for marker, start, end, block in INJECT:
        html = inject(html, marker, start, end, block)
    bundle_block = '<script type="application/json" id="kit-bundle-data">' + embedded + "</script>"
    html = inject(
        html,
        "<!--KIT_BUNDLE_DATA-->",
        "<!--KIT_BUNDLE_DATA_START-->",
        "<!--KIT_BUNDLE_DATA_END-->",
        bundle_block,
    )
    return bundle, sidecar, html


INJECT = [
    (
        "<!--KIT_VIEWER_CSS-->",
        "<!--KIT_VIEWER_CSS_START-->",
        "<!--KIT_VIEWER_CSS_END-->",
        "<style>\n" + VIEWER_CSS + "\n</style>",
    ),
    (
        "<!--KIT_VIEWER_MARKUP-->",
        "<!--KIT_VIEWER_MARKUP_START-->",
        "<!--KIT_VIEWER_MARKUP_END-->",
        VIEWER_MARKUP,
    ),
    (
        "<!--KIT_VIEWER_JS-->",
        "<!--KIT_VIEWER_JS_START-->",
        "<!--KIT_VIEWER_JS_END-->",
        "<script>\n" + VIEWER_JS + "\n</script>",
    ),
]


def inject(html, marker, start, end, block):
    wrapped = start + "\n" + block + "\n" + end
    pat = _re.compile(_re.escape(start) + r"[\s\S]*?" + _re.escape(end))
    if pat.search(html):
        return pat.sub(
            lambda m: wrapped, html
        )  # idempotent: replace previous injection (lambda avoids \u escape mangling)
    if marker in html:
        return html.replace(marker, wrapped)  # first run: fill the bare marker
    raise SystemExit("ERROR: injection marker not found in HTML: %s" % marker)


DATE_RE = _re.compile(r'"generated": ?"\d{4}-\d{2}-\d{2}"')


def check():
    """Diff a fresh in-memory build against the committed artifacts.

    Never writes. The embedded `generated` date is normalized out — the check
    is about content drift (edited mapped docs, changed summaries, viewer
    template changes), not the calendar.

    Returns 0 (no drift) or 1 (drift — regenerate and commit).
    """
    try:
        _, sidecar, html = build()
    except SystemExit as exc:
        print("DRIFT  cannot rebuild from current HTML: %s" % exc)
        print("check failed — the explainer HTML is missing viewer injection markers")
        return 1
    except OSError as exc:
        print("DRIFT  cannot rebuild: %s" % exc)
        return 1

    def norm(s):
        # Fold CRLF -> LF (Windows checkouts) and pin the generated date, so
        # the drift check is line-ending- and calendar-agnostic.
        return DATE_RE.sub('"generated":"CHECK"', s.replace("\r\n", "\n").replace("\r", "\n"))

    def read(p):
        with open(p, encoding="utf-8") as fh:
            return fh.read()

    problems = []
    if not os.path.exists(OUT):
        problems.append("missing sidecar: %s" % OUT)
    elif norm(read(OUT)) != norm(sidecar + "\n"):  # mirror main()'s write
        problems.append(
            "sidecar drift: %s differs from a fresh build (mapped docs or summaries changed?)" % OUT
        )
    if not os.path.exists(HTML):
        problems.append("missing html: %s" % HTML)
    elif norm(read(HTML)) != norm(html):
        problems.append(
            "html drift: %s differs from a fresh injection "
            "(viewer templates or bundle changed?)" % HTML
        )
    if problems:
        for p in problems:
            print("DRIFT  %s" % p)
        print(
            "check failed — re-run `python .freebuff/build-kit-bundle.py` "
            "and commit the regenerated artifacts"
        )
        return 1
    print("OK  no drift: bundle + html match a fresh build (generated date ignored)")
    return 0


def main():
    if "--check" in sys.argv[1:]:
        return check()
    bundle, sidecar, html = build()
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(sidecar + "\n")  # trailing newline keeps artifacts end-of-file-fixer clean
    with open(HTML, "w", encoding="utf-8") as fh:
        fh.write(html)
    print(
        "OK  bundle: %d files, %d bytes -> %s" % (len(bundle["files"]), os.path.getsize(OUT), OUT)
    )
    print("OK  html:   %d bytes -> %s" % (os.path.getsize(HTML), HTML))
    return 0


if __name__ == "__main__":
    sys.exit(main())

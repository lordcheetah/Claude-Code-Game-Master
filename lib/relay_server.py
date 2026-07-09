#!/usr/bin/env python3
"""
relay_server.py — the online-multiplayer transport (Phase 2).

A tiny, dependency-free HTTP server (stdlib only) that lets remote players join a
multiplayer table from a browser. It is a THIN bridge: it never talks to Claude
Code. It only moves text through the campaign's relay logs (see relay_manager):
players POST actions -> relay/inbox.jsonl; the GM posts narration -> relay/
outbox.jsonl; players poll it back. The GM (one Claude Code session) remains the
whole brain.

Endpoints:
    GET  /              -> the browser client (single self-contained page)
    GET  /seats         -> {seats:[...], code_required:bool}
    POST /join          -> {code, player} -> validate -> {ok, seat}
    POST /say           -> {code, player, text} -> queue an action
    GET  /feed?since=N  -> {entries:[...], last:maxid} (players poll)
    GET  /img/<file>    -> serve a plate PNG from the campaign images/

Run standalone (usually via tools/gm-relay.sh serve):
    python lib/relay_server.py --campaign-dir <dir> [--host H] [--port P] [--code C]

Default host is 127.0.0.1 (this machine only). Use --host 0.0.0.0 for the LAN,
and a tunnel (cloudflared/ngrok/tailscale) to reach the open internet.
"""

import os
import sys
import json
import argparse
import socket
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, str(Path(__file__).parent))
from relay_manager import RelayManager, _slug


CLIENT_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>The Table</title>
<style>
  :root { color-scheme: dark; }
  * { box-sizing: border-box; }
  body { margin:0; font:16px/1.5 -apple-system,Segoe UI,Roboto,sans-serif;
         background:#14110d; color:#eae3d6; }
  header { padding:.6rem 1rem; background:#1e1a14; border-bottom:1px solid #3a3226;
           display:flex; gap:.75rem; align-items:center; }
  header b { color:#e8c584; letter-spacing:.02em; }
  #who { margin-left:auto; font-size:.85rem; color:#a99; }
  #prefs { padding:.4rem 1rem; background:#191510; border-bottom:1px solid #3a3226;
           font-size:.82rem; color:#b9a; max-width:760px; margin:0 auto; }
  #prefs select { background:#0f0d0a; color:#eae3d6; border:1px solid #4a4030;
           border-radius:5px; padding:.12rem .3rem; font:inherit; }
  #prefok { color:#9fce9f; margin-left:.4rem; }
  #feed { padding:1rem; max-width:760px; margin:0 auto; }
  .msg { margin:0 0 1.1rem; }
  .msg .body { white-space:pre-wrap; }
  .sys { color:#b9a; font-style:italic; }
  .mine { color:#9fce9f; }
  .msg img { max-width:100%; border:1px solid #3a3226; border-radius:6px; margin-top:.5rem; }
  form { position:sticky; bottom:0; display:flex; gap:.5rem; padding:.75rem 1rem;
         background:#1e1a14; border-top:1px solid #3a3226; max-width:760px; margin:0 auto; }
  textarea { flex:1; resize:none; height:2.6rem; padding:.5rem .7rem; border-radius:6px;
             border:1px solid #4a4030; background:#0f0d0a; color:#eae3d6; font:inherit; }
  button { padding:0 1.1rem; border:0; border-radius:6px; background:#e8c584; color:#1a150e;
           font-weight:600; cursor:pointer; }
  button:disabled { opacity:.5; cursor:default; }
  #join { max-width:420px; margin:12vh auto; padding:1.5rem; background:#1e1a14;
          border:1px solid #3a3226; border-radius:10px; }
  #join h1 { margin:.2rem 0 1rem; font-size:1.3rem; color:#e8c584; }
  #join label { display:block; margin:.8rem 0 .25rem; font-size:.9rem; color:#c9bfae; }
  #join select, #join input { width:100%; padding:.55rem .7rem; border-radius:6px;
          border:1px solid #4a4030; background:#0f0d0a; color:#eae3d6; font:inherit; }
  #join button { margin-top:1.2rem; width:100%; padding:.7rem; }
  .err { color:#e08a8a; font-size:.9rem; min-height:1.2rem; }
</style></head><body>
<div id="join">
  <h1>Join the Table</h1>
  <label for="seat">Your seat</label>
  <select id="seat"></select>
  <label for="code" id="codelbl" style="display:none">Room code</label>
  <input id="code" placeholder="room code" style="display:none">
  <button id="joinbtn">Sit down</button>
  <div class="err" id="joinerr"></div>
</div>

<div id="table" style="display:none">
  <header><b>THE TABLE</b> <span id="who"></span></header>
  <div id="prefs">If I'm away:
    <select id="policy">
      <option value="write-out">write me out of the story</option>
      <option value="gm">the GM runs my character</option>
      <option value="delegate">another player runs my character</option>
    </select>
    <select id="deleg" style="display:none"></select>
    <span id="prefok"></span>
  </div>
  <div id="feed"></div>
  <form id="sayform">
    <textarea id="say" placeholder="What does your character do? (Enter to send)"></textarea>
    <button id="saybtn" type="submit">Send</button>
  </form>
</div>

<script>
let PLAYER=null, CODE="", SINCE=0, codeRequired=false, SEATS=[];
const $=s=>document.querySelector(s);

async function loadSeats(){
  const r=await fetch('/seats'); const d=await r.json();
  codeRequired=d.code_required; SEATS=d.seats||[];
  if(codeRequired){ $('#code').style.display='block'; $('#codelbl').style.display='block'; }
  const sel=$('#seat'); sel.innerHTML='';
  SEATS.filter(s=>s.status==='alive').forEach(s=>{
    const o=document.createElement('option');
    o.value=s.player; o.textContent=s.player+' — '+(s.character||'(no character yet)');
    sel.appendChild(o);
  });
  if(!sel.options.length){ const o=document.createElement('option');
    o.textContent='(no seats yet — the GM must add them)'; o.disabled=true; sel.appendChild(o); }
}
loadSeats();

function initPrefs(seat){
  const pol=(seat&&seat.absence_policy)||{mode:'write-out'};
  $('#policy').value=pol.mode||'write-out';
  const dsel=$('#deleg'); dsel.innerHTML='';
  SEATS.filter(s=>s.player!==PLAYER&&s.status==='alive').forEach(s=>{
    const o=document.createElement('option'); o.value=s.player; o.textContent=s.player; dsel.appendChild(o);
  });
  if(pol.mode==='delegate'&&pol.to_player) dsel.value=pol.to_player;
  syncDeleg();
  $('#policy').onchange=()=>{ syncDeleg(); savePolicy(); };
  $('#deleg').onchange=savePolicy;
}
function syncDeleg(){ $('#deleg').style.display = $('#policy').value==='delegate' ? 'inline-block':'none'; }
async function savePolicy(){
  const mode=$('#policy').value, to=$('#deleg').value;
  if(mode==='delegate'&&!to) return;
  const r=await fetch('/prefs',{method:'POST',headers:{'content-type':'application/json'},
    body:JSON.stringify({player:PLAYER,code:CODE,mode,to})});
  const d=await r.json();
  $('#prefok').textContent = d.ok ? 'saved ✓' : ('✗ '+(d.error||''));
  setTimeout(()=>{$('#prefok').textContent='';}, 1500);
}

$('#joinbtn').onclick=async()=>{
  const player=$('#seat').value, code=$('#code').value.trim();
  const r=await fetch('/join',{method:'POST',headers:{'content-type':'application/json'},
    body:JSON.stringify({player,code})});
  const d=await r.json();
  if(!d.ok){ $('#joinerr').textContent=d.error||'could not join'; return; }
  PLAYER=player; CODE=code;
  $('#join').style.display='none'; $('#table').style.display='block';
  $('#who').textContent=player+' → '+(d.seat&&d.seat.character||'');
  initPrefs(d.seat);
  poll(); setInterval(poll, 2000);
};

function render(e){
  const div=document.createElement('div'); div.className='msg';
  const b=document.createElement('div');
  b.className='body'+(e.kind==='system'?' sys':'')+(e.mine?' mine':'');
  b.textContent=e.text; div.appendChild(b);
  (e.images||[]).forEach(fn=>{ const im=document.createElement('img'); im.src='/img/'+encodeURIComponent(fn); div.appendChild(im); });
  $('#feed').appendChild(div); window.scrollTo(0,document.body.scrollHeight);
}
let KICKED=false;
async function poll(){
  if(KICKED) return;
  try{
    const r=await fetch('/feed?since='+SINCE+'&player='+encodeURIComponent(PLAYER));
    const d=await r.json();
    if(d.kicked){ KICKED=true;
      render({text:'— You have been removed from the table by the GM. —', kind:'system'});
      $('#say').disabled=true; $('#saybtn').disabled=true; return; }
    (d.entries||[]).forEach(e=>{ SINCE=Math.max(SINCE,e.id); render(e); });
    setConn(true);
  }catch(_){ setConn(false); }
}
function setConn(ok){ $('#who').style.opacity = ok?1:.5;
  $('#who').title = ok?'connected':'reconnecting…'; }
async function send(){
  const t=$('#say').value.trim(); if(!t) return;
  $('#say').value='';
  const div=document.createElement('div'); div.className='msg';
  const b=document.createElement('div'); b.className='body mine';
  b.textContent='['+PLAYER+'] '+t; div.appendChild(b);
  const tick=document.createElement('span'); tick.textContent=' …'; tick.style.color='#a99';
  b.appendChild(tick); $('#feed').appendChild(div); window.scrollTo(0,document.body.scrollHeight);
  try{
    const r=await fetch('/say',{method:'POST',headers:{'content-type':'application/json'},
      body:JSON.stringify({player:PLAYER,code:CODE,text:t})});
    const d=await r.json();
    if(d.ok){ tick.textContent=' ✓'; tick.style.color='#9fce9f'; }
    else { tick.textContent=' ✗ not sent'; tick.style.color='#e08a8a'; }
  }catch(_){ tick.textContent=' ✗ not sent (offline)'; tick.style.color='#e08a8a'; }
}
$('#sayform').onsubmit=e=>{e.preventDefault();send();};
$('#say').addEventListener('keydown',e=>{ if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send();}});
</script></body></html>
"""


class Handler(BaseHTTPRequestHandler):
    relay = None        # RelayManager (set by serve())
    code = ""           # room code ("" = open)
    MAX_ACTION_CHARS = 2000   # cap a single player action (abuse mitigation)

    def log_message(self, *a):
        pass  # quiet

    def _send(self, obj, status=200, ctype="application/json"):
        body = obj if isinstance(obj, (bytes, bytearray)) else json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    MAX_BODY = 1024 * 1024  # 1 MB — player actions/joins are tiny; cap to blunt DoS

    def _body(self):
        try:
            n = int(self.headers.get("Content-Length", 0))
            if n <= 0 or n > self.MAX_BODY:
                return {}
            return json.loads(self.rfile.read(n) or b"{}")
        except (ValueError, json.JSONDecodeError):
            return {}

    def _check_code(self, given):
        return (not self.code) or (_slug(given) == _slug(self.code))

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/" or u.path == "/index.html":
            self._send(CLIENT_HTML.encode("utf-8"), ctype="text/html; charset=utf-8")
        elif u.path == "/seats":
            self._send({"seats": self.relay.seats(), "code_required": bool(self.code)})
        elif u.path == "/feed":
            q = parse_qs(u.query)
            since = (q.get("since", ["0"]) or ["0"])[0]
            # A poll doubles as a heartbeat: mark the polling seat as present.
            who = (q.get("player", [""]) or [""])[0]
            if who:
                seat = self.relay.match_seat(who)
                if seat and seat.get("locked"):
                    # Kicked: expire their presence at once and tell the client.
                    self.relay.clear_presence(seat.get("slug"))
                    return self._send({"entries": [], "last": int(since or 0), "kicked": True})
                if seat:
                    self.relay.touch_presence(seat.get("slug"), seat.get("player"))
            entries = self.relay.feed(since)
            self._send({"entries": entries,
                        "last": max([e["id"] for e in entries], default=int(since or 0))})
        elif u.path.startswith("/img/"):
            self._serve_image(os.path.basename(u.path[len("/img/"):]))
        else:
            self._send({"error": "not found"}, status=404)

    def do_POST(self):
        u = urlparse(self.path)
        d = self._body()
        if not self._check_code(d.get("code", "")):
            return self._send({"ok": False, "error": "wrong room code"}, status=403)
        if u.path == "/join":
            seat = self.relay.match_seat(d.get("player", ""))
            if not seat:
                return self._send({"ok": False, "error": "no such seat — ask the GM to add you"}, status=400)
            if seat.get("status") != "alive":
                return self._send({"ok": False, "error": "that character has fallen"}, status=400)
            if seat.get("locked"):
                return self._send({"ok": False, "error": "you have been removed from this seat by the GM"}, status=403)
            self.relay.touch_presence(seat.get("slug"), seat.get("player"))
            self._send({"ok": True, "seat": seat})
        elif u.path == "/say":
            seat = self.relay.match_seat(d.get("player", ""))
            text = (d.get("text") or "").strip()
            if not seat:
                return self._send({"ok": False, "error": "no such seat"}, status=400)
            if seat.get("locked"):
                return self._send({"ok": False, "error": "you have been removed from this seat", "kicked": True}, status=403)
            if not text:
                return self._send({"ok": False, "error": "empty"}, status=400)
            if len(text) > self.MAX_ACTION_CHARS:   # abuse cap
                text = text[:self.MAX_ACTION_CHARS]
            self.relay.touch_presence(seat.get("slug"), seat.get("player"))
            rec = self.relay.submit(seat.get("player"), text, seat=seat.get("slug"), source="web")
            self._send({"ok": True, "id": rec["id"]})
        elif u.path == "/prefs":
            # A player sets their own standing absence preference.
            seat = self.relay.match_seat(d.get("player", ""))
            if not seat:
                return self._send({"ok": False, "error": "no such seat"}, status=400)
            try:
                updated = self.relay.set_absence_policy(
                    seat.get("player"), d.get("mode", "write-out"), delegate_to=d.get("to"))
            except Exception as e:
                return self._send({"ok": False, "error": str(e)}, status=400)
            self._send({"ok": True, "policy": updated.get("absence_policy")})
        else:
            self._send({"error": "not found"}, status=404)

    def _serve_image(self, name):
        # basename only — no path traversal
        img = self.relay.campaign_dir / "images" / name
        if not name or not img.is_file():
            return self._send({"error": "no image"}, status=404)
        data = img.read_bytes()
        ctype = "image/png" if name.lower().endswith(".png") else "image/jpeg"
        self._send(data, ctype=ctype)


def _lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80)); ip = s.getsockname()[0]; s.close()
        return ip
    except OSError:
        return "127.0.0.1"


def serve(campaign_dir, host="127.0.0.1", port=8787, code=""):
    relay = RelayManager(campaign_dir)
    Handler.relay = relay
    Handler.code = code or ""
    httpd = ThreadingHTTPServer((host, port), Handler)
    shown = _lan_ip() if host in ("0.0.0.0", "") else host
    url = f"http://{shown}:{port}/"
    relay.write_server_state(pid=os.getpid(), host=host, port=port,
                             code=code or "", url=url)
    print(f"Relay serving at {url}")
    if host == "0.0.0.0":
        print(f"  Players on your network open: {url}")
    if code:
        print(f"  Room code: {code}")
    print("  (Ctrl-C to stop.)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        relay.clear_server_state()
        httpd.server_close()
        print("Relay stopped.")


def main():
    ap = argparse.ArgumentParser(description="Online-multiplayer relay server")
    ap.add_argument("--campaign-dir", required=True)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8787)
    ap.add_argument("--code", default="")
    a = ap.parse_args()
    serve(a.campaign_dir, host=a.host, port=a.port, code=a.code)


if __name__ == "__main__":
    main()

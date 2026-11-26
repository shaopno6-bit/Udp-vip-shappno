# -*- coding: utf-8 -*-
"""
FreeFire Level Up Bot - Professional Web Dashboard & Real-Time EXP Tracker
Embedded Async Web Server (aiohttp)
"""

import asyncio
import json
import hashlib
try:
    import orjson as _orjson
except Exception:
    _orjson = None
import os
import time
from collections import deque  # ✅ CRASH FIX: logs-এর জন্য O(1) deque — list.pop(0) ছিল O(n)

# Account level eta ba tar beshi hole BR theke automatic Lone Wolf. 0 dile bondho.
try:
    AUTO_LW_LEVEL = int(os.environ.get("AUTO_LW_LEVEL", "3"))
except Exception:
    AUTO_LW_LEVEL = 3
from typing import Dict, List, Any, Optional
from aiohttp import web

# ==================== BASE DIRECTORY (ALWAYS ABSOLUTE) ====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get("DATA_DIR", BASE_DIR)
os.makedirs(DATA_DIR, exist_ok=True)
# ✅ AUTO MULTI-FILE SUPPORT - accounts.json, accounts2.json, accounts3.json ...
import glob as _glob
import fnmatch as _fnmatch

def get_all_account_files_dashboard():
    """Root-এ accounts*.json সব ফাইল অটো ডিটেক্ট করে"""
    files = sorted(_glob.glob(os.path.join(DATA_DIR, "accounts*.json")))
    if not files:
        files = [os.path.join(DATA_DIR, "accounts.json")]
    return files

ACCOUNTS_FILE_PATH = os.path.join(DATA_DIR, "accounts.json")  # default for new adds
# ✅ Complete (EXP/Level limit) বা Error (login fail) হওয়া আইডি এই ফাইলে জমা হয়।
# নাম "accounts*.json" প্যাটার্নে পড়ে না, তাই বট এটাকে সাধারণ accounts ফাইল ভেবে লোড করবে না।
DELETED_ACCOUNTS_FILE = os.path.join(DATA_DIR, "delete_accounts.json")

# ==================== EMBEDDED HTML DASHBOARD ====================
# HTML is embedded directly — no external file dependency (works on Termux/mobile)
DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<meta name="color-scheme" content="dark">
<meta name="theme-color" content="#0a0a0a">
<meta name="apple-mobile-web-app-capable" content="yes">
<title>SHAPPNO — Dashboard</title>
<link rel="icon" href="/logo.jpg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap">
<style>
:root{
  --bg:#0a0a0a;--bg2:#0a0a0a;--surf:#111111;--surf2:#171717;--surf3:#1f1f1f;--inset:#0f0f0f;
  --line:#262626;--line2:#333333;--line3:#444444;
  --text:#fafafa;--text2:#a1a1aa;--muted:#71717a;--white:#fff;
  --v1:#fafafa;--v2:#fafafa;
  --grad:#fafafa;--gold-d:rgba(234,179,8,.14);
  --ok:#22c55e;--warn:#eab308;--bad:#f43f5e;--info:#3b82f6;--violet:#a78bfa;
  --c-amber:#eab308;
  --r-lg:20px;--r-md:14px;--r-sm:11px;--r-xs:9px;--r-xl:24px;
  --sh:0 2px 8px rgba(0,0,0,.4),0 1px 2px rgba(0,0,0,.3);
  --sh-lg:0 8px 28px rgba(0,0,0,.5),0 2px 6px rgba(0,0,0,.35);
  --sh-2:var(--sh-lg);--sh-1:0 1px 2px rgba(0,0,0,.35);--sh-3:0 28px 70px rgba(0,0,0,.6);
  --ease:cubic-bezier(.22,.8,.24,1);
  --sans:'Inter',system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;
  --mono:'JetBrains Mono',ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
  --tab-h:70px;
}
*,*::before,*::after{margin:0;padding:0;box-sizing:border-box}
[hidden]{display:none!important}
html{background:var(--bg);-webkit-text-size-adjust:100%}
body{font-family:var(--sans);font-size:14px;line-height:1.5;color:var(--text);min-height:100vh;min-height:100dvh;-webkit-font-smoothing:antialiased;font-variant-numeric:tabular-nums;overflow-x:hidden;
  background:
    radial-gradient(900px 520px at 100% -10%,rgba(250,250,250,.13),transparent 60%),
    radial-gradient(800px 480px at -10% 110%,rgba(250,250,250,.09),transparent 60%),
    var(--bg);
  }
button,input,select,textarea{font:inherit;color:inherit}
button{cursor:pointer;border:0;background:none;-webkit-tap-highlight-color:transparent;touch-action:manipulation}
input,select,textarea{-webkit-user-select:text;user-select:text}
button:focus-visible,input:focus-visible,select:focus-visible,textarea:focus-visible{outline:2px solid var(--v2);outline-offset:2px}
::selection{background:rgba(250,250,250,.35)}
::-webkit-scrollbar{width:8px;height:8px}::-webkit-scrollbar-thumb{background:rgba(148,163,184,.22);border-radius:99px;border:2px solid transparent;background-clip:padding-box}::-webkit-scrollbar-track{background:transparent}
sup{font-size:.55em;font-weight:700;vertical-align:super;line-height:0;margin-left:1px;color:var(--v2)}

/* ═════════ SHELL ═════════ */
.shell{display:grid;grid-template-columns:248px minmax(0,1fr);min-height:100vh;min-height:100dvh}

/* sidebar (desktop) */
.side{position:sticky;top:0;height:100vh;height:100dvh;display:flex;flex-direction:column;gap:22px;padding:22px 16px;background:var(--surf);border-right:1px solid var(--line)}
.brand{display:flex;align-items:center;gap:12px;min-width:0}
.mark{width:42px;height:42px;flex:0 0 auto;display:grid;place-items:center;border-radius:14px;background:var(--grad);box-shadow:0 10px 26px rgba(250,250,250,.35),inset 0 1px 0 rgba(255,255,255,.3)}
.mark svg{width:22px;height:22px;color:#0a0a0a}
.brand-name{font-size:16px;font-weight:800;letter-spacing:.02em;white-space:nowrap}
.brand-name em{font-style:normal;color:#fafafa}
.brand-sub{font-size:11px;color:var(--muted);margin-top:2px;white-space:nowrap}
.nav{display:flex;flex-direction:column;gap:4px}
.nav-i{display:flex;align-items:center;gap:12px;height:44px;padding:0 14px;border-radius:var(--r-sm);color:var(--text2);font-size:13.5px;font-weight:600;text-align:left;transition:background .2s var(--ease),color .2s var(--ease)}
.nav-i svg{width:18px;height:18px;flex:0 0 auto}
.nav-i:hover{background:var(--surf2);color:var(--text)}
.nav-i.active{background:var(--surf3);color:var(--text);box-shadow:inset 2px 0 0 #fafafa}
.nav-i.active svg{color:var(--v2)}
.side-card{margin-top:auto;padding:16px;border-radius:var(--r-lg);background:linear-gradient(160deg,var(--surf2),var(--surf));border:1px solid var(--line);box-shadow:var(--sh)}
.side-card small{display:block;font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.1em;font-weight:700}
.side-card .big{font-family:var(--mono);font-size:24px;font-weight:700;margin-top:6px;letter-spacing:-.02em}
.side-card .row{display:flex;justify-content:space-between;margin-top:10px;font-size:12px;color:var(--text2)}
.side-card .bar{height:5px;margin-top:12px;border-radius:99px;background:var(--surf3);overflow:hidden}
.side-card .bar i{display:block;height:100%;width:0;background:#fafafa;border-radius:99px;transition:width .6s var(--ease)}

/* content */
.content{min-width:0;display:flex;flex-direction:column}
.top{position:sticky;top:0;z-index:50;display:flex;align-items:center;justify-content:space-between;gap:12px;padding:14px 26px;background:color-mix(in srgb,var(--bg) 82%,transparent);backdrop-filter:blur(16px) saturate(140%);-webkit-backdrop-filter:blur(16px) saturate(140%);border-bottom:1px solid var(--line)}
.top-title{font-size:18px;font-weight:700;letter-spacing:-.01em}
.top-m{display:none;align-items:center;gap:10px;min-width:0}
.top-r{display:flex;align-items:center;gap:8px;flex:0 0 auto}
.chip{display:inline-flex;align-items:center;gap:7px;height:30px;padding:0 11px;border-radius:999px;font-size:12px;font-weight:600;white-space:nowrap;background:var(--surf2);border:1px solid var(--line2);color:var(--text2)}
.chip.role{color:#fafafa;border-color:#333;background:#171717;text-transform:uppercase;letter-spacing:.08em;font-size:10.5px}
.live{color:var(--ok);border-color:rgba(34,197,94,.3);background:rgba(34,197,94,.08)}
.live i{width:7px;height:7px;border-radius:50%;background:currentColor;box-shadow:0 0 0 0 currentColor;animation:ping 2.2s var(--ease) infinite}
.live.off{color:var(--bad);border-color:rgba(244,63,94,.3);background:rgba(244,63,94,.08)}.live.off i{animation:none}
@keyframes ping{0%{box-shadow:0 0 0 0 rgba(34,197,94,.5)}70%,100%{box-shadow:0 0 0 7px rgba(34,197,94,0)}}
.icon-btn{width:38px;height:38px;flex:0 0 auto;display:grid;place-items:center;border-radius:12px;background:var(--surf2);border:1px solid var(--line2);color:var(--text2);transition:color .2s,background .2s,border-color .2s,transform .15s}
.icon-btn:hover{color:var(--text);background:var(--surf3)}
.icon-btn:active{transform:scale(.96)}
.icon-btn svg{width:17px;height:17px}
.icon-btn.bad:hover{color:var(--bad);border-color:rgba(244,63,94,.35)}

main{flex:1;padding:24px 26px 48px;min-width:0}
.page{display:none}
.page.active{display:block;animation:enter .35s var(--ease)}
@keyframes enter{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}

/* ═════════ BUTTONS / FORM ═════════ */
.btn{height:42px;padding:0 18px;display:inline-flex;align-items:center;justify-content:center;gap:9px;border-radius:var(--r-sm);font-size:13.5px;font-weight:700;color:#0a0a0a;background:#fafafa;box-shadow:0 6px 18px rgba(0,0,0,.45);transition:transform .18s var(--ease),box-shadow .25s var(--ease),filter .2s;white-space:nowrap}
.btn:hover{transform:translateY(-1px);filter:brightness(.95);box-shadow:0 10px 26px rgba(0,0,0,.55)}
.btn:active{transform:translateY(0) scale(.985)}
.btn:disabled{opacity:.55;cursor:wait;transform:none;filter:none}
.btn svg{width:15px;height:15px}
.btn.ghost{background:var(--surf2);color:var(--text);box-shadow:none;border:1px solid var(--line2)}
.btn.ghost:hover{background:var(--surf3);filter:none;box-shadow:none}
.btn.bad{background:#f43f5e;box-shadow:0 10px 24px rgba(244,63,94,.3)}
.btn.block{width:100%}
.btn.sm{height:36px;padding:0 13px;font-size:12.5px}
.field{display:flex;flex-direction:column;gap:8px;margin-bottom:14px;min-width:0}
.field>label,.lbl{font-size:11px;font-weight:700;letter-spacing:.09em;text-transform:uppercase;color:var(--muted)}
.inp{width:100%;min-width:0;height:44px;padding:0 14px;border-radius:var(--r-sm);background:var(--surf2);border:1px solid var(--line2);color:var(--text);font-size:14px;outline:0;transition:border-color .2s,box-shadow .2s,background .2s}
.inp::placeholder{color:var(--muted)}
.inp:hover{border-color:rgba(148,163,184,.3)}
.inp:focus{border-color:rgba(250,250,250,.7);box-shadow:0 0 0 4px rgba(250,250,250,.18);background:var(--surf)}
.inp[type=file]{padding:9px 10px;height:auto;font-size:13px;color:var(--text2)}
.inp[type=file]::file-selector-button{margin-right:12px;height:30px;padding:0 12px;border-radius:9px;border:1px solid var(--line2);background:var(--surf3);color:var(--text);font:inherit;font-weight:600;cursor:pointer}
select.inp{appearance:none;-webkit-appearance:none;background-image:linear-gradient(45deg,transparent 50%,var(--text2) 50%),linear-gradient(135deg,var(--text2) 50%,transparent 50%);background-position:calc(100% - 19px) 55%,calc(100% - 14px) 55%;background-size:5px 5px;background-repeat:no-repeat;padding-right:38px}
textarea.inp{height:auto;padding:12px 14px;font-family:var(--mono);font-size:12.5px;resize:vertical}
.hint{font-size:12px;color:var(--muted);line-height:1.5}
.row{display:flex;gap:8px;align-items:center}
.row .inp{flex:1}
.seg{display:inline-flex;padding:4px;border-radius:12px;background:var(--surf2);border:1px solid var(--line)}
.seg button{height:34px;padding:0 14px;border-radius:9px;font-size:12.5px;font-weight:600;color:var(--muted);transition:background .2s,color .2s,box-shadow .2s}
.seg button:hover{color:var(--text)}
.seg button.active{background:var(--surf3);color:var(--text);box-shadow:0 2px 8px rgba(0,0,0,.25)}
.switch{position:relative;width:46px;height:26px;flex:0 0 auto}
.switch input{position:absolute;opacity:0;width:0;height:0}
.switch i{position:absolute;inset:0;border-radius:99px;background:var(--surf3);border:1px solid var(--line2);transition:background .3s,border-color .3s,box-shadow .3s;cursor:pointer}
.switch i::before{content:"";position:absolute;width:20px;height:20px;left:2px;top:2px;border-radius:50%;background:#71717a;box-shadow:0 2px 6px rgba(0,0,0,.35);transition:transform .3s var(--ease)}
.switch input:checked+i{background:#fafafa;border-color:transparent}
.switch input:checked+i::before{transform:translateX(20px);background:#0a0a0a}
.switch input:focus-visible+i{outline:2px solid var(--v2);outline-offset:2px}

/* ═════════ CARDS / PANELS ═════════ */
.card{background:linear-gradient(180deg,var(--surf2),var(--surf));border:1px solid var(--line);border-radius:var(--r-lg);box-shadow:var(--sh);padding:18px}
.card+.card{margin-top:14px}
.stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin-bottom:24px}
.stat{position:relative;overflow:hidden;padding:16px 18px;border-radius:var(--r-lg);background:linear-gradient(160deg,var(--surf2),var(--surf));border:1px solid var(--line);box-shadow:var(--sh)}
.stat::after{content:"";position:absolute;right:-26px;top:-26px;width:86px;height:86px;border-radius:50%;background:radial-gradient(circle,rgba(250,250,250,.05),transparent 70%);pointer-events:none}
.stat span{display:block;font-size:11.5px;font-weight:600;color:var(--muted);letter-spacing:.02em;margin-bottom:8px}
.stat b{display:block;font-family:var(--mono);font-size:24px;font-weight:700;letter-spacing:-.02em;line-height:1.1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.stat b.grad{color:#fafafa}
.stat small{display:block;margin-top:6px;font-size:11.5px;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.sec-head{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;margin-bottom:14px}
.sec-head h2{font-size:15px;font-weight:700;letter-spacing:-.01em;display:flex;align-items:center;gap:10px}
.sec-head h2 small{font-size:12.5px;font-weight:600;color:var(--muted)}
.tools{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.search{width:240px;max-width:100%;height:40px;padding-left:40px;background:var(--surf) url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%236b7589' stroke-width='2' stroke-linecap='round'%3E%3Ccircle cx='11' cy='11' r='7'/%3E%3Cpath d='M20 20l-3.5-3.5'/%3E%3C/svg%3E") no-repeat 14px center/16px 16px}
.search::-webkit-search-cancel-button{-webkit-appearance:none}

/* ═════════ ACCOUNT GRID ═════════ */
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px;align-items:start}
.empty{grid-column:1/-1;display:flex;flex-direction:column;align-items:center;gap:12px;text-align:center;color:var(--text2);padding:56px 24px;border-radius:var(--r-lg);border:1px dashed var(--line2);background:linear-gradient(180deg,rgba(250,250,250,.05),transparent)}
.empty i{width:54px;height:54px;display:grid;place-items:center;border-radius:18px;background:var(--grad);color:#0a0a0a;font-style:normal;font-size:22px;box-shadow:0 12px 28px rgba(250,250,250,.35)}
.empty b{color:var(--text);font-size:15px}

.acard{position:relative;overflow:hidden;border-radius:var(--r-lg);background:linear-gradient(180deg,var(--surf2),var(--surf));border:1px solid var(--line);box-shadow:var(--sh);transition:transform .3s var(--ease),box-shadow .3s var(--ease),border-color .3s;container-type:inline-size}
.acard:hover{transform:translateY(-3px);box-shadow:var(--sh-lg);border-color:var(--line2)}
.acard::before{content:"";position:absolute;left:0;right:0;top:0;height:2px;background:var(--c,#64748b);opacity:.9;z-index:2}
.acard.st-online{--c:var(--ok)}
.acard.st-match{--c:var(--info)}
.acard.st-connecting{--c:var(--warn)}
.acard.st-offline{--c:var(--bad)}
.acard.st-paused{--c:var(--muted)}
.banner{position:relative;height:92px;background:linear-gradient(120deg,#1f1f1f 0%,#141414 55%,#0a0a0a 100%);overflow:hidden}
.banner-img{position:absolute;inset:0;background-size:cover;background-position:center;transition:opacity .4s}
.banner::after{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,0) 30%,rgba(9,12,20,.85) 100%)}
.region-tag{position:absolute;right:12px;top:12px;z-index:2;font-size:10.5px;font-weight:700;letter-spacing:.08em;padding:4px 9px;border-radius:999px;background:rgba(0,0,0,.45);border:1px solid rgba(255,255,255,.18);color:#fff;backdrop-filter:blur(6px)}
.ahead{display:flex;align-items:flex-end;gap:12px;padding:0 16px;margin-top:-30px;position:relative;z-index:3}
.avatar{width:60px;height:60px;flex:0 0 auto;border-radius:18px;overflow:hidden;border:3px solid var(--surf);background:var(--surf3);display:grid;place-items:center;color:var(--text2);box-shadow:0 8px 20px rgba(0,0,0,.35)}
.avatar img,.avatar svg{width:100%;height:100%;object-fit:cover;display:block}
.avatar svg{padding:14px}
.who{flex:1;min-width:0;padding-bottom:4px}
.nick{font-size:15.5px;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;letter-spacing:-.01em}
.uid{font-family:var(--mono);font-size:11px;color:var(--muted);margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.spill{flex:0 0 auto;margin-bottom:6px;height:26px;padding:0 10px;border-radius:999px;font-size:11px;font-weight:700;white-space:nowrap;border:1px solid;background:transparent;transition:filter .2s}
.spill:hover{filter:brightness(1.2)}
.spill.b-online{color:#4ade80;border-color:rgba(34,197,94,.35);background:rgba(34,197,94,.08)}
.spill.b-match{color:#60a5fa;border-color:rgba(59,130,246,.4);background:rgba(59,130,246,.1)}
.spill.b-connecting{color:#fbbf24;border-color:rgba(234,179,8,.35);background:rgba(234,179,8,.08)}
.spill.b-offline{color:#fb7185;border-color:rgba(244,63,94,.35);background:rgba(244,63,94,.08)}
.spill.b-paused{color:#c4b5fd;border-color:var(--line2);background:var(--surf3)}
.lvl{display:flex;align-items:flex-end;justify-content:space-between;gap:10px;padding:16px 16px 0}
.lvl-l small{display:block;font-size:10.5px;font-weight:700;letter-spacing:.09em;text-transform:uppercase;color:var(--muted)}
.lv{font-family:var(--mono);font-size:30px;font-weight:700;line-height:1;letter-spacing:-.03em;color:#fafafa}
.lvl-r{text-align:right;min-width:0}
.pct{font-family:var(--mono);font-size:15px;font-weight:700}
.need{display:block;font-size:11px;color:var(--muted);margin-top:2px;white-space:nowrap}
.bar{height:7px;margin:12px 16px 0;border-radius:99px;background:var(--surf3);overflow:hidden}
.bar i{display:block;height:100%;width:0;border-radius:99px;background:#fafafa;box-shadow:0 0 10px rgba(255,255,255,.12);transition:width .8s var(--ease);position:relative;overflow:hidden}
.bar i::after{content:"";position:absolute;inset:0;background:linear-gradient(90deg,transparent,rgba(255,255,255,.4),transparent);transform:translateX(-100%);animation:sheen 3s ease-in-out infinite}
@keyframes sheen{0%{transform:translateX(-100%)}55%,100%{transform:translateX(100%)}}
.tiles{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;padding:14px 16px 0}
.tile{padding:10px 12px;border-radius:12px;background:var(--surf3);border:1px solid var(--line);min-width:0}
.tile span{display:block;font-size:10.5px;font-weight:600;color:var(--muted);letter-spacing:.02em}
.tile b{display:block;font-family:var(--mono);font-size:13px;font-weight:600;margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.tile b.ok{color:var(--ok)}
.meta{display:flex;justify-content:space-between;gap:8px;padding:12px 16px 0;font-size:11.5px;color:var(--muted)}
.meta span{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.note{margin:10px 16px 0;padding:8px 11px;border-radius:10px;font-size:12px;line-height:1.45;word-break:break-word}
.note.err{color:#fecdd3;background:rgba(244,63,94,.09);border:1px solid rgba(244,63,94,.2)}
.note.info{color:#bfdbfe;background:rgba(59,130,246,.08);border:1px solid rgba(59,130,246,.18)}
.actions{display:flex;gap:8px;padding:14px 16px 16px}
.abtn{flex:1;height:38px;display:inline-flex;align-items:center;justify-content:center;gap:7px;border-radius:11px;font-size:12.5px;font-weight:600;color:var(--text);background:var(--surf3);border:1px solid var(--line2);transition:background .2s,border-color .2s,color .2s,transform .15s}
.abtn:hover{background:var(--surf);border-color:rgba(148,163,184,.3)}
.abtn:active{transform:scale(.98)}
.abtn svg{width:14px;height:14px}
.abtn.danger{flex:0 0 auto;padding:0 14px;color:var(--bad)}
.abtn.danger:hover{background:rgba(244,63,94,.1);border-color:rgba(244,63,94,.35)}
/* compact view */
.acard.compact .tiles,.acard.compact .meta,.acard.compact .need,.acard.compact .actions{padding-top:12px}
.acard.compact .lvl{padding-top:14px}
.role-user .actions{display:none}
.role-user .acard .lvl{padding-bottom:16px}
.role-user .acard:not(.compact) .actions{display:none}

/* ═════════ ADD PAGE ═════════ */
.two{display:grid;grid-template-columns:minmax(0,1.1fr) minmax(0,.9fr);gap:16px;align-items:start}
.tip{padding:18px;border-radius:var(--r-lg);background:var(--surf2);border:1px solid var(--line)}
.tip h3{font-size:14px;margin-bottom:8px}
.tip p{font-size:12.5px;color:var(--text2);line-height:1.65}
.tip code{display:block;margin-top:10px;padding:10px 12px;border-radius:10px;background:rgba(0,0,0,.35);font-family:var(--mono);font-size:11.5px;color:var(--v2);white-space:pre-wrap;word-break:break-all}
.apane{display:none}.apane.active{display:block;animation:enter .25s var(--ease)}

/* ═════════ LOGS ═════════ */
.log-box{max-height:calc(100vh - 220px);min-height:280px;overflow-y:auto;font-family:var(--mono);font-size:12.5px}
.log-e{display:grid;grid-template-columns:82px 1fr;gap:14px;padding:10px 6px;border-bottom:1px solid var(--line);transition:background .2s}
.log-e:hover{background:rgba(148,163,184,.04)}
.log-e:last-child{border-bottom:0}
.log-ts{color:var(--muted)}
.log-m{color:var(--text2);word-break:break-word}
.log-m.success{color:var(--ok)}.log-m.error{color:#fda4af}.log-m.warning{color:var(--warn)}.log-m.info{color:var(--text2)}

/* ═════════ CONTROLS ═════════ */
.ctl-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;align-items:start}
.ctl-row{display:flex;align-items:center;justify-content:space-between;gap:12px;min-height:48px}
.ctl-row b{font-size:13.5px;font-weight:600;display:block}
.ctl-row small{font-size:12px;color:var(--muted)}
.mode-seg{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;padding:5px;border-radius:14px;background:var(--surf3);border:1px solid var(--line)}
.mode-seg button{height:40px;border-radius:10px;font-size:13px;font-weight:600;color:var(--muted);transition:background .2s,color .2s,box-shadow .2s}
.mode-seg button:hover{color:var(--text)}
.mode-seg button.active{background:#fafafa;color:#0a0a0a;box-shadow:0 2px 10px rgba(0,0,0,.35)}
.mode-seg button.active#m-AUTO{background:#3b82f6;color:#fff}
.mode-seg button.active#m-BR_EVO{background:#fafafa;color:#0a0a0a}
.mode-seg button.active#m-NONE{background:#f43f5e;color:#fff}
.ar-cfg{display:grid;grid-template-columns:1fr 1fr auto;gap:10px;align-items:end;margin-top:12px}
.ar-cfg .field{margin:0}
.ar-cfg .btn{height:44px}
.div{height:1px;background:var(--line);margin:14px 0}
.limit-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}

/* ═════════ TABBAR (mobile) ═════════ */
.tabbar{display:none}

/* ═════════ TOASTS ═════════ */
.toasts{position:fixed;right:22px;bottom:22px;z-index:300;display:flex;flex-direction:column;gap:10px;align-items:flex-end;pointer-events:none}
.toast{max-width:380px;padding:12px 16px;border-radius:14px;font-size:13px;font-weight:500;background:color-mix(in srgb,var(--surf) 92%,transparent);backdrop-filter:blur(12px);border:1px solid var(--line2);border-left:3px solid var(--ok);box-shadow:var(--sh-lg);color:var(--text);animation:toastin .35s var(--ease);line-height:1.45}
.toast.err{border-left-color:var(--bad)}
@keyframes toastin{from{opacity:0;transform:translateY(10px) scale(.98)}to{opacity:1;transform:none}}

/* ═════════ ROLE ═════════ */
.role-user .admin-only{display:none!important}

/* ═════════ RESPONSIVE ═════════ */
@media (max-width:1180px){
  .stats{grid-template-columns:repeat(2,minmax(0,1fr))}
}
@media (max-width:960px){
  .shell{grid-template-columns:1fr}
  .side{display:none}
  .top{padding:12px 16px}
  .top-title{display:none}
  .top-m{display:flex}
  .top-r .chip.role{color:#fafafa;border-color:#333;background:#171717;text-transform:uppercase;letter-spacing:.08em;font-size:10.5px}
  .top-r .btn-desk{display:none}
  main{padding:18px 16px calc(var(--tab-h) + 28px + env(safe-area-inset-bottom))}
  .two,.ctl-grid{grid-template-columns:1fr}
  .tabbar{display:flex;position:fixed;left:12px;right:12px;bottom:calc(12px + env(safe-area-inset-bottom));height:var(--tab-h);z-index:120;align-items:center;justify-content:space-around;padding:0 8px;border-radius:24px;background:color-mix(in srgb,var(--surf) 88%,transparent);backdrop-filter:blur(18px) saturate(150%);-webkit-backdrop-filter:blur(18px) saturate(150%);border:1px solid var(--line2);box-shadow:var(--sh-lg)}
  .tb{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:4px;height:56px;border-radius:16px;color:var(--muted);font-size:10.5px;font-weight:600;transition:color .2s,transform .2s}
  .tb svg{width:21px;height:21px;transition:transform .3s var(--ease)}
  .tb.active{color:var(--text)}
  .tb.active svg{color:var(--v2);transform:translateY(-1px)}
  .tb-add{flex:0 0 auto;width:58px;height:58px;margin-top:-26px;border-radius:20px;display:grid;place-items:center;background:var(--grad);color:#0a0a0a;box-shadow:0 12px 28px rgba(250,250,250,.45),0 0 0 5px color-mix(in srgb,var(--bg) 70%,transparent);transition:transform .2s var(--ease)}
  .tb-add:active{transform:scale(.94)}
  .tb-add svg{width:24px;height:24px;color:#0a0a0a}
  .tb-add.active{box-shadow:0 12px 28px rgba(0,0,0,.6),0 0 0 2px rgba(255,255,255,.35)}
  .toasts{left:12px;right:12px;bottom:calc(var(--tab-h) + 32px + env(safe-area-inset-bottom));align-items:stretch}
  .toast{max-width:none}
}
@media (max-width:620px){
  .stats{gap:10px}
  .stat{padding:14px}
  .stat b{font-size:19px}
  .grid{grid-template-columns:1fr;gap:14px}
  .search{width:100%}
  .sec-head{align-items:stretch}
  .tools{width:100%}
  .tools .search{flex:1 1 100%}
  .tools .seg{flex:1}
  .tools .seg button{flex:1}
  .limit-grid{grid-template-columns:1fr}
  .ar-cfg{grid-template-columns:1fr 1fr}
  .ar-cfg .btn{grid-column:1/-1}
  .tiles{grid-template-columns:repeat(2,minmax(0,1fr))}
  .mode-seg button{font-size:12px}
}
@media (max-width:380px){
  .tiles{grid-template-columns:repeat(2,minmax(0,1fr))}
  .top-r .chip.live span{display:none}
}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important;scroll-behavior:auto!important}}
</style>
</head>
<body>
<div class="shell">

<aside class="side">
  <div class="brand">
    <div class="mark" aria-hidden="true"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M13.6 1.8 4.6 13.2h6.1L9.6 22.2l9.8-11.9h-6.3z"/></svg></div>
    <div>
      <div class="brand-name">SHAPPNO</div>
      <div class="brand-sub">Level automation panel</div>
    </div>
  </div>
  <nav class="nav">
    <button class="nav-i" data-go="home" type="button"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7" rx="2"/><rect x="14" y="3" width="7" height="7" rx="2"/><rect x="3" y="14" width="7" height="7" rx="2"/><rect x="14" y="14" width="7" height="7" rx="2"/></svg>Accounts</button>
    <button class="nav-i" data-go="add" type="button"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 8v8M8 12h8"/></svg>Add account</button>
    <button class="nav-i" data-go="logs" type="button"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M4 17l6-6-6-6"/><path d="M12 19h8"/></svg>Activity</button>
    <button class="nav-i admin-only" data-go="controls" type="button"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><line x1="4" y1="6" x2="20" y2="6"/><line x1="4" y1="12" x2="20" y2="12"/><line x1="4" y1="18" x2="20" y2="18"/><circle cx="9" cy="6" r="2" fill="currentColor"/><circle cx="15" cy="12" r="2" fill="currentColor"/><circle cx="7" cy="18" r="2" fill="currentColor"/></svg>Controls</button>
  </nav>
  <div class="side-card">
    <small>Online now</small>
    <div class="big"><span id="sbOn">0</span><span style="color:var(--muted);font-size:15px"> / <span id="sbTot">0</span></span></div>
    <div class="bar"><i id="sbBar"></i></div>
    <div class="row"><span>Uptime</span><span id="sbUp" style="font-family:var(--mono)">0m</span></div>
  </div>
</aside>

<div class="content">
  <header class="top">
    <div class="top-title" id="pageTitle">Accounts</div>
    <div class="top-m">
      <div class="brand">
        <div class="mark" style="width:36px;height:36px;border-radius:12px"><svg viewBox="0 0 24 24" fill="currentColor" style="width:19px;height:19px"><path d="M13.6 1.8 4.6 13.2h6.1L9.6 22.2l9.8-11.9h-6.3z"/></svg></div>
        <div class="brand-name" style="font-size:15px">SHAPPNO</div>
      </div>
    </div>
    <div class="top-r">
      <span class="chip role" id="roleChip">Admin</span>
      <span class="chip live" id="live"><i></i><span id="liveTxt">Live</span></span>
      <button class="icon-btn btn-desk" id="reloadTop" type="button" title="Reload accounts" aria-label="Reload accounts"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/></svg></button>
      <button class="icon-btn bad" id="logoutBtn" type="button" title="Logout" aria-label="Logout"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="m16 17 5-5-5-5"/><path d="M21 12H9"/></svg></button>
    </div>
  </header>

  <main>

    <!-- ── ACCOUNTS ── -->
    <section class="page" id="page-home" data-title="Accounts">
      <div class="stats">
        <div class="stat"><span>Accounts</span><b id="sAcc">0</b><small id="sAccSub">Total connected</small></div>
        <div class="stat"><span>Online</span><b id="sOn" style="color:var(--ok)">0</b><small id="sInMatch">0 in match</small></div>
        <div class="stat"><span>EXP gained</span><b id="sExp" class="grad">+0</b><small id="sUp">uptime 0m</small></div>
        <div class="stat"><span>Matches</span><b id="sMatch">0</b><small id="sOff">0 offline</small></div>
      </div>
      <div class="sec-head">
        <h2>Your accounts <small id="countTxt"></small></h2>
        <div class="tools">
          <input class="inp search" id="search" type="search" placeholder="Search name or UID" autocomplete="off">
          <div class="seg" role="tablist" aria-label="View">
            <button type="button" data-view="detailed" class="active">Detailed</button>
            <button type="button" data-view="compact">Compact</button>
          </div>
        </div>
      </div>
      <div class="grid" id="grid"></div>
    </section>

    <!-- ── ADD ── -->
    <section class="page" id="page-add" data-title="Add account">
      <div class="two">
        <div class="card" style="margin-top:0">
          <div class="seg" id="addSeg" style="margin-bottom:18px;display:flex">
            <button type="button" data-atab="guest" class="active" style="flex:1">Guest</button>
            <button type="button" data-atab="token" style="flex:1">Token</button>
            <button type="button" data-atab="json" style="flex:1">TXT file</button>
          </div>
          <div class="apane active" data-apane="guest">
            <div class="field"><label for="fUid">Player UID</label><input class="inp" id="fUid" inputmode="numeric" autocomplete="off" placeholder="e.g. 2212345678"></div>
            <div class="field"><label for="fPwd">Password</label><input class="inp" id="fPwd" type="password" autocomplete="off" placeholder="Account password"></div>
          </div>
          <div class="apane" data-apane="token">
            <div class="field"><label for="fTok">Access token</label><textarea class="inp" id="fTok" rows="4" autocomplete="off" placeholder="Paste access token"></textarea></div>
          </div>
          <div class="apane" data-apane="json">
            <div class="field"><label for="fJson">UID:Password file</label><input class="inp" id="fJson" type="file" accept=".txt,text/plain"></div>
            <p class="hint">One account per line: UID:password. Existing UIDs are skipped automatically. Up to 5000 accounts per file.</p>
          </div>
          <div class="field" style="margin-top:6px"><label for="fReg">Server region</label>
            <select class="inp" id="fReg"><option value="BD">Bangladesh</option><option value="IND">India</option><option value="SG">Singapore</option><option value="ID">Indonesia</option><option value="BR">Brazil</option><option value="US">United States</option></select></div>
          <button class="btn block" id="addSubmit" type="button" style="margin-top:6px">Validate &amp; start</button>
        </div>
        <div class="tip">
          <h3>TXT format</h3>
          <p>Upload a plain text file. Put one UID and password on each line.</p>
          <code>2212345678:abc123
2219876543:xyz789
2212345679:pass123</code>
          <p style="margin-top:12px">Accounts are started one by one (about 1.5 s apart) so the server stays stable.</p>
        </div>
      </div>
    </section>

    <!-- ── LOGS ── -->
    <section class="page" id="page-logs" data-title="Activity">
      <div class="card" style="margin-top:0">
        <div class="sec-head" style="margin-bottom:12px">
          <h2>Activity log</h2>
          <button class="btn ghost sm" id="logClear" type="button">Clear log</button>
        </div>
        <div class="log-box" id="logBox"></div>
      </div>
    </section>

    <!-- ── CONTROLS ── -->
    <section class="page" id="page-controls" data-title="Controls">
      <div class="ctl-grid">
        <div class="card" style="margin-top:0">
          <div class="sec-head"><h2>Bot control</h2></div>
          <div class="ctl-row"><div><b>All bots</b><small>Start or stop every account</small></div><label class="switch"><input type="checkbox" id="globalToggle"><i></i></label></div>
          <div class="div"></div>
          <div class="lbl" style="margin-bottom:10px">Match mode · all accounts</div>
          <div class="mode-seg">
            <button type="button" id="m-BR_EVO">Bear EVO</button>
            <button type="button" id="m-AUTO">Auto</button>
            <button type="button" id="m-NONE">Off</button>
          </div>
        </div>

        <div class="card" style="margin-top:0">
          <div class="sec-head"><h2>Auto-delete limits</h2></div>
          <div class="field"><label for="limitInp">EXP limit</label>
            <div class="row"><input class="inp" id="limitInp" inputmode="numeric" placeholder="0 = no limit"><button class="btn ghost sm" id="limitBtn" type="button">Set</button></div>
            <div class="hint" id="limitHint"></div></div>
          <div class="field"><label for="levelInp">Level limit</label>
            <div class="row"><input class="inp" id="levelInp" inputmode="numeric" placeholder="0 = no limit"><button class="btn ghost sm" id="levelBtn" type="button">Set</button></div>
            <div class="hint" id="levelHint"></div></div>
          <div class="field" style="margin-bottom:0"><label for="userLimitInp">IDs per user</label>
            <div class="row"><input class="inp" id="userLimitInp" inputmode="numeric" placeholder="0 = no limit"><button class="btn ghost sm" id="userLimitBtn" type="button">Set</button></div>
            <div class="hint" id="userLimitHint"></div></div>
        </div>

        <div class="card" style="margin-top:0">
          <div class="sec-head"><h2>BR EVO parallel</h2></div>
          <div class="field" style="margin-bottom:0"><label for="parInp">Matches per ID at once (1–10)</label>
            <div class="row"><input class="inp" id="parInp" inputmode="numeric" placeholder="1"><button class="btn ghost sm" id="parBtn" type="button">Set</button></div>
            <div class="hint" id="parHint"></div></div>
        </div>
        <div class="card" style="margin-top:0">
          <div class="sec-head"><h2>🔥 SHAPPNO Max Match</h2></div>
          <div class="field" style="margin-bottom:0"><label for="mehediInp">UDP sessions per account (1–50, default 10)</label>
            <div class="row"><input class="inp" id="mehediInp" inputmode="numeric" placeholder="10"><button class="btn ghost sm" id="mehediBtn" type="button">Set</button></div>
            <div class="hint" id="mehediHint"></div></div>
        </div>
        <div class="card" style="margin-top:0">
          <div class="sec-head"><h2>Auto-restart</h2></div>
          <div class="ctl-row"><div><b>Restart every cycle</b><small>Fresh login after the break</small></div><label class="switch"><input type="checkbox" id="autoRestartToggle"><i></i></label></div>
          <div id="autoRestartCfg" style="display:none">
            <div class="ar-cfg">
              <div class="field"><label for="arIntervalInp">Interval (hours)</label><input class="inp" id="arIntervalInp" inputmode="decimal" value="1.5"></div>
              <div class="field"><label for="arBreakInp">Break (min)</label><input class="inp" id="arBreakInp" inputmode="numeric" value="10"></div>
              <button class="btn ghost" id="arSetBtn" type="button">Apply</button>
            </div>
          </div>
          <div class="hint" id="arStatusHint" style="margin-top:12px;color:var(--warn)"></div>
        </div>

        <div class="card" style="margin-top:0">
          <div class="sec-head"><h2>Maintenance</h2></div>
          <div style="display:flex;flex-direction:column;gap:10px">
            <button class="btn ghost block" id="reloadBtn" type="button">Reload accounts.json</button>
            <button class="btn danger block" id="allDeleteBtn" type="button">ALL DELETE</button>
            <button class="btn ghost block" id="restoreBtn" type="button">Restore deleted <span id="restoreCnt"></span></button>
          </div>
        </div>
      </div>
    </section>

  </main>
</div>
</div>

<nav class="tabbar" aria-label="Main navigation">
  <button class="tb" data-go="home" type="button"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7" rx="2"/><rect x="14" y="3" width="7" height="7" rx="2"/><rect x="3" y="14" width="7" height="7" rx="2"/><rect x="14" y="14" width="7" height="7" rx="2"/></svg>Accounts</button>
  <button class="tb" data-go="logs" type="button"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M4 17l6-6-6-6"/><path d="M12 19h8"/></svg>Activity</button>
  <button class="tb-add" data-go="add" type="button" aria-label="Add account"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M12 5v14M5 12h14"/></svg></button>
  <button class="tb admin-only" data-go="controls" type="button"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><line x1="4" y1="6" x2="20" y2="6"/><line x1="4" y1="12" x2="20" y2="12"/><line x1="4" y1="18" x2="20" y2="18"/><circle cx="9" cy="6" r="2" fill="currentColor"/><circle cx="15" cy="12" r="2" fill="currentColor"/><circle cx="7" cy="18" r="2" fill="currentColor"/></svg>Controls</button>
  <button class="tb" id="reloadTb" type="button"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/></svg>Reload</button>
</nav>

<div class="toasts" id="toasts" aria-live="polite"></div>

<script>
const EXP_LIST=[0,48,202,544,1012,1844,2792,3800,4870,6004,7192,8448,9760,11140,12566,14060,15610,17224,18902,20632,22424,24278,26192,28166,30200,32294,34448,37804,41274,44870,48582,53394,58566,64096,69994,76260,83506,91128,99322,108092,120144,133266,147472,162760,179126,196572,215368,235316,257010,279860];
const $=id=>document.getElementById(id);
const $$=s=>document.querySelectorAll(s);
const num=v=>{const n=Number(v);return Number.isFinite(n)?n:0};
const fmt=v=>num(v).toLocaleString();
const esc=v=>String(v==null?'':v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const safeUrl=u=>{u=String(u||'').trim();return /^(https?:\/\/|\/|data:image\/)/i.test(u)?u:''};
const AV='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><circle cx="12" cy="9" r="4"/><path d="M4 21c1.5-4 4.5-6 8-6s6.5 2 8 6"/></svg>';
const ICON_DEL='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6"/></svg>';
const ICON_REF='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/></svg>';

let S={}, globalRunning=false, toggleBusy=false, modeChoice=null, modeOff=false;
let parLoaded=false, limitLoaded=false, levelLoaded=false, userLimitLoaded=false, arInited=false, arBusy=false, lastLogSig='';
const busy={limitBusy:false,levelBusy:false,userLimitBusy:false};
let fetching=false, fails=0, lastOk=Date.now();
let view=localStorage.getItem('s26_view')||'detailed';
const cards=new Map();

/* ── API ── */
async function api(path,body){
  const ac=new AbortController(), to=setTimeout(()=>ac.abort(),30000);
  let r;
  try{ r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body||{}),signal:ac.signal}) }
  catch(e){ throw new Error(e&&e.name==='AbortError'?'Server busy — try again':'Network error') }
  finally{ clearTimeout(to) }
  if(r.status===401){ location.href='/login'; throw new Error('Session expired') }
  const d=await r.json().catch(()=>({}));
  if(!r.ok||d.status==='error'||d.success===false) throw new Error(d.error||d.message||'Request failed');
  return d;
}

/* ── toast ── */
function toast(msg,err){
  const t=document.createElement('div');
  t.className='toast'+(err?' err':'');
  t.textContent=msg;
  $('toasts').appendChild(t);
  setTimeout(()=>{t.style.transition='opacity .3s,transform .3s';t.style.opacity='0';t.style.transform='translateY(6px)';setTimeout(()=>t.remove(),300)},3200);
}

/* ── navigation ── */
const PAGES=['home','add','logs','controls'];
function go(p){
  if(!PAGES.includes(p)) p='home';
  if(document.body.classList.contains('role-user')&&p==='controls') p='home';
  $$('.page').forEach(s=>s.classList.toggle('active',s.id==='page-'+p));
  $$('[data-go]').forEach(b=>b.classList.toggle('active',b.dataset.go===p));
  const sec=document.getElementById('page-'+p);
  $('pageTitle').textContent=sec?sec.dataset.title:'Accounts';
  document.title='SHAPPNO — '+(sec?sec.dataset.title:'Accounts');
  if(location.hash.slice(1)!==p) history.replaceState(null,'','#'+p);
  window.scrollTo({top:0,behavior:'instant'in window?'instant':'auto'});
}
document.querySelectorAll('[data-go]').forEach(b=>b.addEventListener('click',()=>go(b.dataset.go)));
window.addEventListener('hashchange',()=>go(location.hash.slice(1)));

/* ── status helpers ── */
function progress(level,exp){
  const lv=Math.max(1,Math.floor(num(level))),cur=EXP_LIST[lv-1],nxt=EXP_LIST[lv];
  if(cur===undefined) return{pct:0,need:0,max:true};
  if(nxt===undefined) return{pct:100,need:0,max:true};
  const pct=Math.min(100,Math.max(0,(num(exp)-cur)/(nxt-cur)*100));
  return{pct,need:Math.max(0,nxt-num(exp)),max:false};
}
function effStatus(a){
  const v=String(a.status||'ONLINE').toUpperCase().replace(/ +/g,'_');
  const info=String(a.last_info||'');
  if(v==='ONLINE'&&/search|waiting for match/i.test(info)){
    const t=x=>{const m=/^(\d\d):(\d\d):(\d\d)/.exec(String(x||''));return m?(+m[1])*3600+(+m[2])*60+(+m[3]):null};
    const it=t(info),lu=t(a.last_updated);
    if(it===null||lu===null) return 'SEARCHING';
    const d=(lu-it+86400)%86400;
    if(d<=60) return 'SEARCHING';
  }
  return a.status;
}
function status(s){
  const v=String(s||'ONLINE').toUpperCase().replace(/ +/g,'_');
  if(v==='CONNECTING') return{k:'connecting',l:'Connecting',g:'conn'};
  if(v==='SEARCHING'||v==='SEARCH') return{k:'connecting',l:'Searching',g:'on'};
  if(v==='IN_MATCH'||v==='MATCH'||v==='PLAYING') return{k:'match',l:'In match',g:'on'};
  if(v==='OFFLINE'||v==='DISCONNECTED') return{k:'offline',l:'Offline',g:'off'};
  if(v==='ERROR'||v==='FAILED') return{k:'offline',l:'Error',g:'off'};
  if(v==='PAUSED'||v==='STOPPED') return{k:'paused',l:'Paused',g:'pause'};
  return{k:'online',l:'Online',g:'on'};
}

/* ── account card ── */
function makeCard(uid){
  const el=document.createElement('article');
  el.className='acard';
  el.dataset.uid=uid;
  el.innerHTML=
    '<div class="banner"><div class="banner-img"></div><span class="region-tag"></span></div>'+
    '<div class="ahead"><div class="avatar"></div><div class="who"><div class="nick"></div><div class="uid"></div></div><button class="spill" type="button"></button></div>'+
    '<div class="lvl"><div class="lvl-l"><small>Level</small><span class="lv">1</span></div><div class="lvl-r"><span class="pct">0%</span><span class="need"></span></div></div>'+
    '<div class="bar"><i></i></div>'+
    '<div class="tiles">'+
      '<div class="tile"><span>Start EXP</span><b class="t-ini">0</b></div>'+
      '<div class="tile"><span>Current EXP</span><b class="t-cur">0</b></div>'+
      '<div class="tile"><span>Gained</span><b class="t-gain ok">+0</b></div>'+
      '<div class="tile"><span>Matches</span><b class="t-mc">0</b></div>'+
    '</div>'+
    '<div class="meta"><span class="m-st"></span><span class="m-up"></span></div>'+
    '<div class="note err" hidden></div><div class="note info" hidden></div>'+
    '<div class="actions">'+
      '<button class="abtn" data-act="refresh" type="button">'+ICON_REF+'<span>Refresh</span></button>'+
      '<button class="abtn danger" data-act="delete" type="button" aria-label="Delete">'+ICON_DEL+'<span>Delete</span></button>'+
    '</div>';
  el.querySelector('[data-act=refresh]').onclick=()=>refreshAcc(uid);
  el.querySelector('[data-act=delete]').onclick=()=>deleteAcc(uid);
  el.querySelector('.spill').onclick=()=>{ if(!document.body.classList.contains('role-user')) setMatchType(uid,'BR_EVO') };
  return el;
}
function setAvatar(el,url){
  const box=el.querySelector('.avatar');
  if(el._av===url) return; el._av=url;
  box.innerHTML='';
  if(!url){ box.innerHTML=AV; return }
  const img=new Image();
  img.alt=''; img.referrerPolicy='no-referrer';
  img.onerror=()=>{ box.innerHTML=AV };
  img.src=url; box.appendChild(img);
}
function updateCard(el,a,limit){
  const st=status(effStatus(a));
  const nick=a.nickname||a.name||'Unknown', uid=String(a.uid), lv=Math.max(1,num(a.level)||1);
  const cur=num(a.current_exp??a.exp), ini=num(a.initial_exp);
  const gained=a.gained_exp!=null?num(a.gained_exp):Math.max(0,cur-ini);
  const p=progress(lv,cur), mc=num(a.matches_played??a.matches);
  const region=String(a.region||'BD').toUpperCase();
  const av=safeUrl(a.avatar_url||a.avatar||a.head_pic), bn=safeUrl(a.banner_url||a.banner);
  const upd=a.updated_ago||a.last_updated||'just now';
  const err=a.last_error||'', info=a.last_info||'';
  const sig=[nick,uid,lv,cur,ini,gained,mc,region,st.k,st.l,av,bn,view,limit,err,info,upd,p.need].join('|');
  if(el._sig===sig) return; el._sig=sig;
  el.className='acard st-'+st.k+(view==='compact'?' compact':'');
  el.querySelector('.nick').textContent=nick;
  el.querySelector('.uid').textContent='UID '+uid;
  el.querySelector('.region-tag').textContent=region;
  el.querySelector('.lv').textContent=lv;
  el.querySelector('.pct').textContent=Math.round(p.pct)+'%';
  el.querySelector('.need').textContent=p.max?'Max level':fmt(p.need)+' EXP to next';
  el.querySelector('.bar i').style.width=Math.min(100,p.pct)+'%';
  el.querySelector('.t-ini').textContent=fmt(ini);
  el.querySelector('.t-cur').textContent=fmt(cur);
  el.querySelector('.t-gain').textContent='+'+fmt(gained);
  el.querySelector('.t-mc').textContent=fmt(mc);
  const sp=el.querySelector('.spill');
  sp.textContent=st.l; sp.className='spill b-'+st.k;
  el.querySelector('.m-st').textContent=st.l;
  el.querySelector('.m-up').textContent='Updated '+upd;
  const bnEl=el.querySelector('.banner-img');
  const bnKey=bn||'';
  if(el._bn!==bnKey){ el._bn=bnKey; bnEl.style.backgroundImage=bn?'url("'+bn.replace(/"/g,'%22')+'")':'none' }
  setAvatar(el,av);
  const ne=el.querySelector('.note.err'), ni=el.querySelector('.note.info');
  ne.hidden=!err; ne.textContent=err;
  ni.hidden=!!err||!info; ni.textContent=info;
}

/* ── render ── */
function render(d){
  S=d;
  const accs=Array.isArray(d.accounts)?d.accounts.slice():[];
  accs.sort((a,b)=>num(b.level)-num(a.level)||num(b.current_exp??b.exp)-num(a.current_exp??a.exp)||String(a.uid).localeCompare(String(b.uid)));
  const limit=num(d.exp_limit);
  const grid=$('grid'), q=$('search').value.trim().toLowerCase();
  const g={on:0,conn:0,off:0,pause:0,match:0};
  const seen=new Set();
  let shown=0;
  accs.forEach((a,i)=>{
    const uid=String(a.uid);
    seen.add(uid);
    let el=cards.get(uid);
    if(!el){ el=makeCard(uid); cards.set(uid,el) }
    updateCard(el,a,limit);
    const st=status(effStatus(a));
    g[st.g]=(g[st.g]||0)+1;
    if(st.k==='match') g.match++;
    const hay=((a.nickname||a.name||'')+' '+uid).toLowerCase();
    const vis=!q||hay.includes(q);
    el.hidden=!vis; if(vis) shown++;
    if(grid.children[i]!==el) grid.insertBefore(el,grid.children[i]||null);
  });
  cards.forEach((el,uid)=>{ if(!seen.has(uid)){ el.remove(); cards.delete(uid) } });
  let empty=$('emptyState');
  if(accs.length===0){
    if(!empty){ empty=document.createElement('div'); empty.id='emptyState'; empty.className='empty'; grid.appendChild(empty) }
    empty.innerHTML='<i>⚡</i><b>No accounts yet</b><span>Add a guest, token or JSON account to start leveling.</span>';
  } else if(empty){ empty.remove() }
  if(accs.length&&shown===0&&q){
    if(!empty){ empty=document.createElement('div'); empty.id='emptyState'; empty.className='empty'; grid.appendChild(empty) }
    empty.innerHTML='<i>⌕</i><b>No match</b><span>Nothing matches “'+esc(q)+'”.</span>';
  }
  const online=(g.on||0);
  $('countTxt').textContent=accs.length?('· '+fmt(shown)+(q?' of ':' ')+(q?fmt(accs.length):'')+' shown'):'';
  $('sAcc').textContent=fmt(accs.length);
  $('sAccSub').textContent=fmt(accs.length)+' connected';
  $('sOn').textContent=fmt(online);
  $('sInMatch').textContent=fmt(g.match)+' in match';
  $('sExp').textContent='+'+fmt(d.total_gained_exp);
  $('sMatch').textContent=fmt(d.total_matches);
  $('sOff').textContent=fmt(g.off)+' offline';
  const up=num(d.uptime),h=Math.floor(up/3600),mi=Math.floor(up%3600/60);
  const upTxt=(h?h+'h ':'')+mi+'m';
  $('sUp').textContent='uptime '+upTxt;
  $('sbUp').textContent=upTxt;
  $('sbOn').textContent=fmt(online);
  $('sbTot').textContent=fmt(accs.length);
  $('sbBar').style.width=(accs.length?Math.round(online/accs.length*100):0)+'%';

  if(!toggleBusy&&d.global_running!==undefined){ globalRunning=!!d.global_running; $('globalToggle').checked=globalRunning }
  if($('restoreCnt')) $('restoreCnt').textContent=num(d.deleted_file_count)>0?'('+num(d.deleted_file_count)+')':'';

  $('limitHint').textContent=limit>0?'Auto-delete at +'+fmt(limit)+' EXP':'No limit — accounts are never auto-deleted';
  if(!limitLoaded&&d.exp_limit!==undefined&&!busy.limitBusy){ $('limitInp').value=d.exp_limit; limitLoaded=true }

  const isUser=d.role==='user';
  document.body.classList.toggle('role-user',isUser);
  $('roleChip').textContent=isUser?'User':'Admin';

  const ll=num(d.level_limit);
  $('levelHint').textContent=ll>0?'Auto-delete at level '+ll:'No level limit';
  if(!levelLoaded&&d.level_limit!==undefined&&!busy.levelBusy){ $('levelInp').value=d.level_limit; levelLoaded=true }

  const ul=num(d.user_add_limit);
  $('userLimitHint').textContent=ul>0?'Each user can add up to '+ul+' IDs':'No per-user limit';
  if(!userLimitLoaded&&d.user_add_limit!==undefined&&!busy.userLimitBusy){ $('userLimitInp').value=d.user_add_limit; userLimitLoaded=true }
  if(d.br_evo_parallel!==undefined){ $('parHint').textContent='প্রতি আইডি একসাথে সর্বোচ্চ '+d.br_evo_parallel+' টি match'; if(!parLoaded){ $('parInp').value=d.br_evo_parallel; parLoaded=true } }
  if(d.mehedi_max_match!==undefined){ $('mehediHint').textContent='🔥 SHAPPNO: প্রতি account সর্বোচ্চ '+d.mehedi_max_match+' টি UDP session একসাথে'; if(!window._mehediLoaded){ $('mehediInp').value=d.mehedi_max_match; window._mehediLoaded=true } }

  if(!arInited&&d.auto_restart_enabled!==undefined){
    arInited=true;
    $('autoRestartToggle').checked=!!d.auto_restart_enabled;
    $('autoRestartCfg').style.display=d.auto_restart_enabled?'block':'none';
    if(d.auto_restart_interval_hours) $('arIntervalInp').value=d.auto_restart_interval_hours;
    if(d.auto_restart_break_minutes) $('arBreakInp').value=d.auto_restart_break_minutes;
  }
  const arOn=!!d.auto_restart_enabled, arPhase=d.auto_restart_phase||'', arNext=num(d.auto_restart_next_ts);
  if(arOn&&arNext>0){
    const diff=Math.max(0,arNext-Date.now()/1000);
    const dh=Math.floor(diff/3600),dm=Math.floor(diff%3600/60),ds=Math.floor(diff%60);
    const t=dh>0?dh+'h '+dm+'m':dm>0?dm+'m '+ds+'s':ds+'s';
    $('arStatusHint').textContent=arPhase==='break'?'Break running — reconnect in '+t:arPhase==='reconnecting'?'Reconnecting…':'Next restart in '+t;
  } else if(!arOn){ $('arStatusHint').textContent='' }

  const mts=accs.map(a=>a.match_type||'BR_EVO');
  let act=(d.global_mode==='AUTO')?'AUTO':modeChoice;
  if(act!=='AUTO'&&mts.length){ act=mts.every(x=>x==='BR_EVO')?'BR_EVO':null }
  if(modeOff) act='NONE';
  ['BR_EVO','AUTO','NONE'].forEach(k=>{ const el=$('m-'+k); if(el) el.classList.toggle('active',act===k) });

  renderLogs(d.logs);
}

function renderLogs(logs){
  logs=Array.isArray(logs)?logs:[];
  const last=logs[logs.length-1], sig=logs.length+'|'+(last?last.time+last.message:'');
  if(sig===lastLogSig) return; lastLogSig=sig;
  const box=$('logBox'), keep=box.scrollTop;
  box.innerHTML=logs.slice().reverse().map(l=>
    '<div class="log-e"><span class="log-ts">'+esc(l.time)+'</span><span class="log-m '+esc(l.level||'info')+'">'+esc(l.message)+'</span></div>'
  ).join('')||'<div class="log-e"><span class="log-ts">—</span><span class="log-m">No activity yet</span></div>';
  box.scrollTop=keep;
}

/* ── polling (adaptive — server-এর load কমাতে) ── */
let lastRtt=0;
async function fetchStats(){
  if(fetching) return; fetching=true;
  const t0=performance.now();
  try{
    const ac=new AbortController(), to=setTimeout(()=>ac.abort(),30000);
    let r; try{ r=await fetch('/api/stats',{cache:'no-cache',signal:ac.signal}) } finally{ clearTimeout(to) }
    if(r.status===401){ location.href='/login'; return }
    if(!r.ok) throw new Error('HTTP '+r.status);
    const d=await r.json();
    render(d);
    fails=0; lastOk=Date.now(); lastRtt=performance.now()-t0;
    $('live').classList.remove('off'); $('liveTxt').textContent='Live';
  }catch(e){
    fails++;
    if(fails>=3&&Date.now()-lastOk>20000){ $('live').classList.add('off'); $('liveTxt').textContent='Offline' }
    else { $('live').classList.remove('off'); $('liveTxt').textContent='Syncing…' }
  } finally{ fetching=false }
}
function pollDelay(){
  const n=(S.accounts?S.accounts.length:0);
  let ms=document.hidden?15000:(n>150?6000:n>60?5000:4000);
  if(fails>0) ms=Math.min(15000,3000*(fails+1));
  else if(lastRtt>3000) ms=Math.max(ms,Math.min(12000,lastRtt*2));
  return ms;
}
function poll(){
  setTimeout(async()=>{ if(!document.hidden) await fetchStats(); poll(); }, pollDelay());
}
document.addEventListener('visibilitychange',()=>{ if(!document.hidden) fetchStats() });
window.addEventListener('online',()=>{ fails=0; fetchStats() });

/* ── account actions ── */
async function setMatchType(uid,mt){
  try{ await api('/api/account/match-type',{uid,match_type:mt}); toast('UID '+uid+' set to Bear EVO'); modeChoice=null; await fetchStats() }
  catch(e){ toast(e.message,true) }
}
async function refreshAcc(uid){
  try{ await api('/api/account/refresh',{uid}); toast('Refreshing #'+uid+'…'); await fetchStats() }
  catch(e){ toast(e.message,true) }
}
async function deleteAcc(uid){
  if(!confirm('Delete account #'+uid+'?')) return;
  try{ await api('/api/account/delete',{uid}); toast('Account #'+uid+' deleted'); await fetchStats() }
  catch(e){ toast(e.message,true) }
}

/* ── view toggle & search ── */
function setView(v){
  view=v; localStorage.setItem('s26_view',v);
  $$('[data-view]').forEach(b=>b.classList.toggle('active',b.dataset.view===v));
  cards.forEach(el=>{ el._sig=null });
  if(S.accounts) render(S);
}
$$('[data-view]').forEach(b=>b.addEventListener('click',()=>setView(b.dataset.view)));
$('search').addEventListener('input',()=>{ if(S.accounts) render(S) });
setView(view);

/* ── controls ── */
$('globalToggle').addEventListener('change',async function(){
  const on=this.checked; toggleBusy=true;
  try{ await api('/api/bot/toggle',{running:on}); globalRunning=on; toast(on?'All accounts started':'All accounts stopped') }
  catch(e){ this.checked=!on; toast(e.message,true) }
  toggleBusy=false; fetchStats();
});
['BR_EVO','AUTO'].forEach(mode=>{
  const el=$('m-'+mode); if(!el) return;
  el.addEventListener('click',async()=>{
    try{
      await api('/api/accounts/set-all-mode',{mode});
      modeChoice=mode; modeOff=false;
      toast('All accounts → '+(mode==='AUTO'?'Auto level mode':'Bear EVO'));
      await fetchStats();
    }catch(e){ toast(e.message,true) }
  });
});
$('m-NONE').addEventListener('click',()=>{ modeOff=true; modeChoice=null; render(S) });

async function saveLimit(btnId,inpId,busyKey,path,body,okMsg){
  const btn=$(btnId); if(btn.disabled) return;
  const old=btn.textContent; btn.disabled=true; btn.textContent='…';
  busy[busyKey]=true;
  try{ await api(path,body); toast(okMsg); }
  catch(e){ toast(e.message,true) }
  btn.disabled=false; btn.textContent=old; busy[busyKey]=false;
  fetchStats();
}
$('limitBtn').addEventListener('click',()=>{
  const n=Math.max(0,parseInt($('limitInp').value,10)||0);
  saveLimit('limitBtn','limitInp','limitBusy','/api/settings/exp-limit',{exp_limit:n},n>0?'EXP limit set to '+fmt(n):'EXP limit removed');
});
$('levelBtn').addEventListener('click',()=>{
  const n=Math.max(0,parseInt($('levelInp').value,10)||0);
  saveLimit('levelBtn','levelInp','levelBusy','/api/settings/level-limit',{level_limit:n},n>0?'Level limit set to '+n:'Level limit removed');
});
$('parBtn').addEventListener('click',async function(){
  const n=parseInt($('parInp').value,10);
  if(!(n>=1&&n<=10)){ toast('1 থেকে 10 এর মধ্যে সংখ্যা দিন',true); return }
  this.disabled=true;
  try{ await api('/api/settings/parallel',{value:n}); parLoaded=false; toast('প্রতি আইডি একসাথে '+n+'টি match'); }
  catch(e){ toast(e.message,true) }
  this.disabled=false; fetchStats();
});
$('mehediBtn').addEventListener('click',async function(){
  const n=parseInt($('mehediInp').value,10);
  if(!(n>=1&&n<=50)){ toast('1 থেকে 50 এর মধ্যে সংখ্যা দিন',true); return }
  this.disabled=true;
  try{ await api('/api/settings/mehedi-max',{value:n}); window._mehediLoaded=false; toast('🔥 SHAPPNO: প্রতি account সর্বোচ্চ '+n+' টি UDP session'); }
  catch(e){ toast(e.message,true) }
  this.disabled=false; fetchStats();
});
$('userLimitBtn').addEventListener('click',()=>{
  const n=Math.max(0,parseInt($('userLimitInp').value,10)||0);
  saveLimit('userLimitBtn','userLimitInp','userLimitBusy','/api/settings/user-limit',{user_add_limit:n},n>0?'Per-user limit set to '+n:'Per-user limit removed');
});

async function setAutoRestart(enabled){
  if(arBusy) return; arBusy=true;
  const intH=parseFloat($('arIntervalInp').value)||1.5, brM=parseInt($('arBreakInp').value,10)||10;
  try{
    await api('/api/settings/auto-restart',{enabled,interval_hours:intH,break_minutes:brM});
    $('autoRestartCfg').style.display=enabled?'block':'none';
    arInited=false;
    toast(enabled?'Auto-restart on — every '+intH+'h, '+brM+' min break':'Auto-restart off');
  }catch(e){ toast(e.message,true); $('autoRestartToggle').checked=!enabled }
  arBusy=false; fetchStats();
}
$('autoRestartToggle').addEventListener('change',function(){ setAutoRestart(this.checked) });
$('arSetBtn').addEventListener('click',()=>setAutoRestart(true));

async function doReload(btn){
  if(btn&&btn.disabled) return;
  if(btn) btn.disabled=true;
  try{ const d=await api('/api/accounts/reload'); toast(d.message||'Accounts reloaded'); cards.forEach(el=>el._sig=null); await fetchStats() }
  catch(e){ toast(e.message,true) }
  if(btn) btn.disabled=false;
}
$('reloadBtn').addEventListener('click',function(){ doReload(this) });
$('allDeleteBtn').addEventListener('click',async()=>{
  if(!confirm('ALL DELETE: remove every account, credential cache and stop all running workers?')) return;
  const b=$('allDeleteBtn'), old=b.textContent; b.disabled=true; b.textContent='Deleting…';
  try{ const r=await api('/api/accounts/all-delete',{}); toast('All deleted · '+(r.deleted||0)+' account(s)'); await fetchStats() }
  catch(e){ toast(e.message,true) }
  finally{ b.disabled=false; b.textContent=old }
});

$('reloadTop').addEventListener('click',function(){ doReload(this) });
$('reloadTb').addEventListener('click',function(){ doReload(this) });

async function doRestore(btn){
  if(btn.disabled) return;
  btn.disabled=true;
  try{
    const d=await api('/api/accounts/restore-deleted');
    toast(d.message||'Restored');
    fetchStats();
    [2500,7000,14000].forEach(ms=>setTimeout(fetchStats,ms));
  }catch(e){ toast(e.message,true) }
  btn.disabled=false;
}
$('restoreBtn').addEventListener('click',function(){ doRestore(this) });

$('logClear').addEventListener('click',async()=>{
  try{ await api('/api/logs/clear'); lastLogSig=''; await fetchStats() }
  catch(e){ toast(e.message,true) }
});

/* ── add account ── */
let addTab='guest';
$$('[data-atab]').forEach(b=>b.addEventListener('click',()=>{
  addTab=b.dataset.atab;
  $$('[data-atab]').forEach(x=>x.classList.toggle('active',x===b));
  $$('[data-apane]').forEach(p=>p.classList.toggle('active',p.dataset.apane===addTab));
}));
$('addSubmit').addEventListener('click',async function(){
  const region=$('fReg').value;
  if(addTab==='json'){
    const f=$('fJson').files[0];
    if(!f){ toast('Select a TXT file first',true); return }
    const rawText=await f.text();
    const accs=rawText.split(/\r?\n/).map(x=>x.trim()).filter(x=>x&&!x.startsWith('#'));
    if(!accs.length){ toast('The TXT file has no accounts',true); return }
    this.disabled=true; const old=this.textContent; this.textContent='Adding…';
    try{
      const r=await api('/api/account/bulk-add',{region,text:rawText});
      toast(r.added+' added · '+r.skipped+' skipped'+(r.error_count?' · '+r.error_count+' errors':''));
      $('fJson').value=''; go('home'); await fetchStats();
    }catch(e){ toast(e.message,true) }
    this.disabled=false; this.textContent=old;
    return;
  }
  let p;
  if(addTab==='token'){
    const tok=$('fTok').value.trim();
    if(!tok){ toast('Paste an access token',true); return }
    p={type:'token',region,token:tok};
  } else {
    const uid=$('fUid').value.trim(), pwd=$('fPwd').value.trim();
    if(!uid||!pwd){ toast('Enter UID and password',true); return }
    p={type:'guest',region,uid,password:pwd};
  }
  this.disabled=true; const old=this.textContent; this.textContent='Validating…';
  try{
    await api('/api/account/add',p);
    toast('Account added — starting…');
    $('fUid').value=''; $('fPwd').value=''; $('fTok').value='';
    go('home'); await fetchStats();
  }catch(e){ toast(e.message,true) }
  this.disabled=false; this.textContent=old;
});

/* ── logout ── */
$('logoutBtn').addEventListener('click',async()=>{
  try{ await fetch('/api/logout',{method:'POST'}) }catch(e){}
  location.href='/login';
});

/* ── boot ── */
go(location.hash.slice(1)||'home');
poll();
</script>
</body>
</html>
"""


# ==================== LOGIN / ACCESS KEY ====================
# Dashboard-e dhukte Access Key lagbe. Default admin key: SHAPPNO
# Railway-te alada key chaile Variables-e DASHBOARD_KEY set korun (code change lagbe na).
import hmac as _hmac
import hashlib as _hashlib
import base64 as _b64

# ✅ ROLES: Admin = সব কাজ | User = শুধু দেখা + Add Account
#   Admin key  → ADMIN_KEY (না থাকলে DASHBOARD_KEY, ডিফল্ট SHAPPNO)
#   User key   → USER_KEY  (ডিফল্ট SHAPPNOUSER)
DASHBOARD_KEY = (os.environ.get("ADMIN_KEY") or os.environ.get("DASHBOARD_KEY") or "SHAPPNO").strip()
USER_KEY = (os.environ.get("USER_KEY") or "SHAPPNOUSER").strip()
USER_ALLOWED_PATHS = {"/", "/api/stats", "/api/account/add", "/api/account/bulk-add", "/api/logout"}
SESSION_COOKIE = "tfx_session"
SESSION_DAYS = 30
_SESSION_SECRET = _hashlib.sha256(("tfx-dashboard|" + DASHBOARD_KEY + "|" + USER_KEY).encode("utf-8")).digest()
_LOGIN_FAILS: Dict[str, Any] = {}   # ip -> {"n": fail_count, "until": lock_until_ts}
_MAX_FAILS = 5
_LOCK_SECONDS = 60

LOGO_JPG = _b64.b64decode("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")

LOGIN_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<meta name="color-scheme" content="dark">
<meta name="theme-color" content="#06080b">
<title>SHAPPNO — Secure Access</title>
<link rel="icon" href="/logo.jpg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap">
<style>
:root{--bg:#0a0a0a;--panel:#111111;--s2:#171717;--line:#262626;--line2:#333333;
--gold:#fafafa;--gold2:#ffffff;--red:#f43f5e;--text:#eef1f6;--text2:#a4adbd;--muted:#66707f;--ease:cubic-bezier(.22,.8,.24,1)}
*,*::before,*::after{margin:0;padding:0;box-sizing:border-box}
html,body{height:100%}
body{font-family:'Inter',system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;font-size:14px;line-height:1.5;color:var(--text);min-height:100vh;min-height:100dvh;display:grid;place-items:center;padding:24px;-webkit-font-smoothing:antialiased;overflow:hidden;background:transparent 65%),transparent 62%),linear-gradient(180deg,#06080c,var(--bg))}
body::before{content:"";position:fixed;inset:0;pointer-events:none;background-image:radial-gradient(rgba(255,255,255,.04) 1px,transparent 1px);background-size:24px 24px;mask-image:radial-gradient(ellipse at center,#000 25%,transparent 78%);-webkit-mask-image:radial-gradient(ellipse at center,#000 25%,transparent 78%)}
#fx{position:fixed;inset:0;width:100%;height:100%;pointer-events:none;z-index:0}
.wrap{position:relative;z-index:1;width:100%;max-width:420px}
.card{position:relative;background:linear-gradient(180deg,#141414,#0d0d0d);border:1px solid var(--line2);border-radius:28px;padding:44px 36px 30px;box-shadow:0 40px 110px rgba(0,0,0,.65),inset 0 1px 0 rgba(255,255,255,.05);text-align:center;transition:opacity .45s var(--ease),transform .45s var(--ease)}
.card::before{content:"";position:absolute;left:30px;right:30px;top:-1px;height:1px;background:linear-gradient(90deg,transparent,rgba(250,250,250,.85),transparent)}
.card.success-fade{opacity:0;transform:scale(.97)}
.card.shake{animation:shake .45s var(--ease)}
@keyframes shake{0%,100%{transform:translateX(0)}20%{transform:translateX(-8px)}40%{transform:translateX(7px)}60%{transform:translateX(-5px)}80%{transform:translateX(3px)}}
.mark{width:76px;height:76px;margin:0 auto 20px;display:grid;place-items:center;border-radius:22px;background:#171717;border:1px solid #333333;box-shadow:0 18px 44px rgba(0,0,0,.5),inset 0 1px 0 rgba(255,255,255,.08);animation:float 5s ease-in-out infinite}
@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-4px)}}
.mark svg{width:40px;height:40px;filter:none}
h1{font-size:25px;font-weight:800;letter-spacing:.02em}
h1 span{background:#fafafa;-webkit-background-clip:text;background-clip:text;color:transparent}
.sub{font-size:13px;color:var(--text2);margin-top:8px}
form{margin-top:30px;text-align:left}
label{display:block;font-size:10.5px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--text2);margin-bottom:9px}
.field{position:relative;display:flex;align-items:center;height:54px;background:#080b10;border:1px solid var(--line2);border-radius:16px;transition:border-color .25s var(--ease),box-shadow .25s var(--ease),background .25s}
.field:hover{border-color:rgba(255,255,255,.2)}
.field:focus-within{border-color:rgba(250,250,250,.65);box-shadow:0 0 0 4px rgba(250,250,250,.12);background:#0a0d12}
.field .ico{width:18px;height:18px;margin-left:17px;flex:0 0 auto;color:var(--muted);transition:color .2s}
.field:focus-within .ico{color:var(--gold)}
#key{flex:1;min-width:0;height:100%;background:transparent;border:0;outline:0;color:var(--text);font-size:15px;letter-spacing:.14em;padding:0 12px;font-family:inherit}
#key::placeholder{letter-spacing:.01em;color:var(--muted);font-size:14px}
.eye{border:0;background:none;width:46px;height:46px;margin-right:4px;display:grid;place-items:center;border-radius:12px;color:var(--muted);transition:color .2s,background .2s}
.eye:hover{color:var(--text2);background:rgba(255,255,255,.04)}
.eye:focus-visible{outline:2px solid rgba(250,250,250,.6);outline-offset:1px}
.eye svg{width:18px;height:18px}
.err{min-height:22px;margin-top:12px;font-size:12.5px;color:#fb7185;text-align:center}
.btn{width:100%;height:52px;margin-top:6px;display:flex;align-items:center;justify-content:center;gap:10px;border-radius:16px;font-size:13.5px;font-weight:800;letter-spacing:.07em;color:#0a0a0a;background:linear-gradient(180deg,#d4d4d8,#fafafa);box-shadow:0 10px 26px rgba(0,0,0,.45),inset 0 1px 0 rgba(255,255,255,.45);transition:transform .18s var(--ease),box-shadow .25s var(--ease),filter .2s}
.btn:hover{transform:translateY(-1px);filter:brightness(1.04);box-shadow:0 14px 34px rgba(0,0,0,.55),inset 0 1px 0 rgba(255,255,255,.45)}
.btn:active{transform:translateY(0) scale(.99)}
.btn:disabled{opacity:.6;cursor:not-allowed;transform:none}
.btn:focus-visible{outline:2px solid rgba(250,250,250,.7);outline-offset:3px}
.btn svg{width:17px;height:17px}
.spin{width:16px;height:16px;border-radius:50%;border:2px solid rgba(22,18,10,.25);border-top-color:#0a0a0a;animation:spin .7s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
.foot{margin-top:24px;font-size:10.5px;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);display:flex;align-items:center;justify-content:center;gap:10px}
.foot i{width:4px;height:4px;border-radius:50%;background:var(--gold);opacity:.6}
.success{position:fixed;inset:0;z-index:50;display:flex;align-items:center;justify-content:center;background:rgba(5,7,10,.9);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);opacity:0;pointer-events:none;transition:opacity .4s var(--ease)}
.success.show{opacity:1;pointer-events:all}
.s-box{text-align:center;transform:scale(.94);opacity:0;transition:transform .5s var(--ease),opacity .5s var(--ease)}
.success.show .s-box{transform:none;opacity:1}
.s-check{width:80px;height:80px;margin:0 auto 20px;display:grid;place-items:center;border-radius:50%;background:rgba(34,197,94,.1);border:2px solid #22c55e;color:#22c55e;font-size:38px;font-weight:700;box-shadow:none}
.s-title{font-size:17px;font-weight:700;letter-spacing:.03em}
.s-bar{width:240px;height:3px;margin:18px auto 0;background:rgba(255,255,255,.08);border-radius:99px;overflow:hidden}
.s-bar i{display:block;height:100%;width:0;background:#fafafa;border-radius:99px;transition:width 1.8s var(--ease)}
.s-bar i.go{width:100%}
@media (max-width:420px){.card{padding:36px 24px 26px;border-radius:24px}h1{font-size:23px}}
@media(prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
</style>
</head>
<body>
<canvas id="fx" aria-hidden="true"></canvas>
<div class="wrap">
  <main class="card" id="card">
    <div class="mark" aria-hidden="true">
      <svg viewBox="0 0 24 24" fill="none"><defs><linearGradient id="gB" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#d4d4d8"/><stop offset="1" stop-color="#fafafa"/></linearGradient></defs><path d="M13.6 1.8 4.6 13.2h6.1L9.6 22.2l9.8-11.9h-6.3z" fill="url(#gB)" stroke="#d4d4d8" stroke-width=".6" stroke-linejoin="round"/></svg>
    </div>
    <h1>SHAPPNO <span>LVL UP</span></h1>
    <div class="sub">Secure access · Control panel</div>

    <form id="form" autocomplete="off">
      <label for="key">Access key</label>
      <div class="field" id="field">
        <svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="15" r="4"/><path d="M10.8 12.2 20 3"/><path d="m16 7 3 3"/><path d="m14 9 2 2"/></svg>
        <input id="key" name="key" type="password" placeholder="Enter your access key" autocomplete="off" autocapitalize="characters" autocorrect="off" spellcheck="false" maxlength="64" required>
        <button class="eye" id="eye" type="button" aria-label="Show key">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/></svg>
        </button>
      </div>
      <div class="err" id="err" role="alert" aria-live="polite"></div>
      <button class="btn" id="btn" type="submit"><span id="btnTxt">Unlock dashboard</span>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="m13 6 6 6-6 6"/></svg>
      </button>
    </form>
    <div class="foot"><span>Protected</span><i></i><span>SHAPPNO</span></div>
  </main>
</div>

<div class="success" id="successOverlay">
  <div class="s-box">
    <div class="s-check">✓</div>
    <div class="s-title">Access granted</div>
    <div class="s-bar"><i id="successBar"></i></div>
  </div>
</div>

<script>
const $=id=>document.getElementById(id);
try{localStorage.removeItem('tfx_last')}catch(e){}
const card=$('card'),key=$('key'),err=$('err'),btn=$('btn'),btnTxt=$('btnTxt');
let busy=false,lockTimer=null;

function showSuccess(){
  card.classList.add('success-fade');
  const ov=$('successOverlay');
  requestAnimationFrame(()=>{
    ov.classList.add('show');
    setTimeout(()=>$('successBar').classList.add('go'),250);
    setTimeout(()=>location.replace('/'),2000);
  });
}

$('eye').addEventListener('click',()=>{const show=key.type==='password';key.type=show?'text':'password';$('eye').setAttribute('aria-label',show?'Hide key':'Show key');key.focus()});
key.addEventListener('input',()=>{err.textContent=''});

function fail(msg){
  err.textContent=msg;
  card.classList.remove('shake');void card.offsetWidth;card.classList.add('shake');
  key.select();
}
function startLock(sec){
  clearInterval(lockTimer);
  btn.disabled=true;
  const tick=()=>{if(sec<=0){clearInterval(lockTimer);btn.disabled=false;err.textContent='';btnTxt.textContent='Unlock dashboard';return}
    btnTxt.textContent='Locked · '+sec+'s';err.textContent='Too many wrong attempts. Please wait.';sec--};
  tick();lockTimer=setInterval(tick,1000);
}

$('form').addEventListener('submit',async e=>{
  e.preventDefault();
  const v=key.value.trim();
  if(busy||btn.disabled)return;
  if(!v){fail('Please enter your access key.');return}
  busy=true;btn.disabled=true;err.textContent='';
  const old=btn.innerHTML;btn.innerHTML='<span class="spin"></span><span>Verifying…</span>';
  try{
    const r=await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({key:v}),credentials:'same-origin'});
    const d=await r.json().catch(()=>({}));
    if(r.ok&&d.status==='ok'){showSuccess();return}
    btn.innerHTML=old;busy=false;
    if(r.status===429){startLock(Math.max(1,Math.ceil(d.retry_after||60)));return}
    btn.disabled=false;fail(d.error||'Wrong access key. Try again.');
  }catch(ex){
    btn.innerHTML=old;busy=false;btn.disabled=false;fail('Cannot reach the server. Check your connection.');
  }
});
key.focus();

/* ambient gold particles */
(function(){
  if(matchMedia('(prefers-reduced-motion: reduce)').matches)return;
  const c=$('fx'),x=c.getContext('2d');let W,H,dpr,P=[];
  function size(){dpr=Math.min(devicePixelRatio||1,2);W=innerWidth;H=innerHeight;c.width=W*dpr;c.height=H*dpr;x.setTransform(dpr,0,0,dpr,0,0)}
  function mk(init){const g=Math.random();return{x:Math.random()*W,y:init?Math.random()*H:H+10,r:Math.random()*1.6+.3,v:Math.random()*.45+.15,d:(Math.random()-.5)*.25,a:Math.random()*.5+.15,h:g<.7?'250,250,250':'255,255,255',t:Math.random()*6.28}}
  size();addEventListener('resize',size);
  const N=Math.round(Math.min(60,Math.max(24,W*H/25000)));
  for(let i=0;i<N;i++)P.push(mk(true));
  (function loop(){
    x.clearRect(0,0,W,H);
    for(const p of P){
      p.y-=p.v;p.t+=.02;p.x+=p.d+Math.sin(p.t)*.2;
      if(p.y<-10)Object.assign(p,mk(false));
      const al=p.a*Math.min(1,p.y/(H*.35));
      x.beginPath();x.fillStyle='rgba('+p.h+','+Math.max(0,al)+')';x.shadowColor='rgba('+p.h+',.8)';x.shadowBlur=6;
      x.arc(p.x,p.y,p.r,0,6.283);x.fill();
    }
    requestAnimationFrame(loop);
  })();
})();
</script>
</body>
</html>
"""


def _make_session_token(role: str = "admin") -> str:
    exp = str(int(time.time()) + SESSION_DAYS * 86400)
    sig = _hmac.new(_SESSION_SECRET, f"{role}|{exp}".encode(), _hashlib.sha256).hexdigest()
    return f"{role}.{exp}.{sig}"


def _token_role(token: Optional[str]) -> Optional[str]:
    """সঠিক টোকেন হলে role ('admin' / 'user') ফেরত দেয়, নইলে None"""
    if not token:
        return None
    parts = token.split(".")
    if len(parts) != 3:
        return None
    role, exp, sig = parts
    if role not in ("admin", "user") or not exp.isdigit() or int(exp) < time.time():
        return None
    good = _hmac.new(_SESSION_SECRET, f"{role}|{exp}".encode(), _hashlib.sha256).hexdigest()
    return role if _hmac.compare_digest(sig, good) else None


def _client_ip(request: web.Request) -> str:
    fwd = request.headers.get("X-Forwarded-For", "")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.remote or "?"


def _is_https(request: web.Request) -> bool:
    return request.secure or request.headers.get("X-Forwarded-Proto", "").lower() == "https"


def _session_role(request: web.Request) -> Optional[str]:
    return _token_role(request.cookies.get(SESSION_COOKIE))


def _is_authed(request: web.Request) -> bool:
    return _session_role(request) is not None


# ✅ OWNER ID: প্রতিটি User ব্রাউজারের আলাদা পরিচয় (লগআউট করলেও থাকে) — নিজের যোগ করা আইডি চিনতে লাগে
import secrets as _secrets
OWNER_COOKIE = "tfx_owner"


def _sign_owner(oid: str) -> str:
    return _hmac.new(_SESSION_SECRET, ("owner|" + oid).encode(), _hashlib.sha256).hexdigest()[:24]


def _owner_id(request: web.Request) -> Optional[str]:
    raw = request.cookies.get(OWNER_COOKIE, "")
    oid, _, sig = raw.partition(".")
    if oid and sig and _hmac.compare_digest(sig, _sign_owner(oid)):
        return oid
    return None


def _owner_cookie_value(oid: str) -> str:
    return f"{oid}.{_sign_owner(oid)}"


@web.middleware
async def auth_middleware(request: web.Request, handler):
    path = request.path
    if path in ("/login", "/api/login", "/logo.jpg", "/favicon.ico", "/healthz"):
        return await handler(request)
    role = _session_role(request)
    if role:
        request["role"] = role
        # User শুধু দেখতে ও Add Account করতে পারবে — বাকি সব API সার্ভারেই আটকানো
        if role == "user" and path not in USER_ALLOWED_PATHS:
            if path.startswith("/api/"):
                return web.json_response({"status": "error", "error": "Admin access only"}, status=403)
            raise web.HTTPFound("/")
        try:
            return await handler(request)
        finally:
            if request.method == "POST":
                _STATS_CACHE.clear()   # action-এর পরে ক্যাশ মুছো → dashboard সাথে সাথে নতুন data দেখায়
    if path.startswith("/api/"):
        return web.json_response({"status": "error", "error": "unauthorized"}, status=401)
    raise web.HTTPFound("/login")


@web.middleware
async def compress_middleware(request: web.Request, handler):
    resp = await handler(request)
    try:
        if (isinstance(resp, web.Response) and resp.status != 304 and request.path != "/logo.jpg"
                and "Content-Encoding" not in resp.headers and request.path != "/healthz"):
            resp.enable_compression()
    except Exception:
        pass
    return resp


async def handle_login_page(request: web.Request) -> web.Response:
    if _is_authed(request):
        raise web.HTTPFound("/")
    return web.Response(text=LOGIN_HTML, content_type="text/html", charset="utf-8",
                        headers={"Cache-Control": "no-store"})


async def handle_logo(request: web.Request) -> web.Response:
    return web.Response(body=LOGO_JPG, content_type="image/jpeg",
                        headers={"Cache-Control": "public, max-age=86400"})


async def handle_login(request: web.Request) -> web.Response:
    ip = _client_ip(request)
    now = time.time()
    rec = _LOGIN_FAILS.get(ip, {"n": 0, "until": 0})
    if rec["until"] > now:
        return web.json_response(
            {"status": "error", "error": "Too many attempts", "retry_after": int(rec["until"] - now) + 1},
            status=429)
    try:
        data = await request.json()
    except Exception:
        data = {}
    supplied = str(data.get("key", "")).strip()
    # case-insensitive, constant-time compare
    sup = supplied.upper().encode("utf-8")
    role = None
    if _hmac.compare_digest(sup, DASHBOARD_KEY.upper().encode("utf-8")):
        role = "admin"
    elif _hmac.compare_digest(sup, USER_KEY.upper().encode("utf-8")):
        role = "user"
    if role is None:
        rec["n"] = rec.get("n", 0) + 1
        if rec["n"] >= _MAX_FAILS:
            rec = {"n": 0, "until": now + _LOCK_SECONDS}
            _LOGIN_FAILS[ip] = rec
            return web.json_response(
                {"status": "error", "error": "Too many attempts", "retry_after": _LOCK_SECONDS}, status=429)
        _LOGIN_FAILS[ip] = rec
        left = _MAX_FAILS - rec["n"]
        return web.json_response(
            {"status": "error", "error": f"Wrong access key. {left} attempt(s) left."}, status=401)
    _LOGIN_FAILS.pop(ip, None)
    resp = web.json_response({"status": "ok", "role": role})
    if role == "user" and not _owner_id(request):
        resp.set_cookie(OWNER_COOKIE, _owner_cookie_value(_secrets.token_hex(6)), max_age=365 * 86400,
                        httponly=True, samesite="Lax", secure=_is_https(request), path="/")
    resp.set_cookie(SESSION_COOKIE, _make_session_token(role), max_age=SESSION_DAYS * 86400,
                    httponly=True, samesite="Lax", secure=_is_https(request), path="/")
    return resp


async def handle_logout(request: web.Request) -> web.Response:
    resp = web.json_response({"status": "ok"})
    resp.del_cookie(SESSION_COOKIE, path="/")
    return resp


# Global bot state shared between app.py and Web Dashboard
# ==================== ACTIVITY LOGGING ====================
# Activity entries stay in memory only; no file is opened or written.
def _append_log_file(entry: dict):
    return None


class BotState:
    def __init__(self):
        self.accounts: Dict[str, Dict[str, Any]] = {}
        # ✅ CRASH FIX: deque(maxlen=200) → O(1) append+auto-drop, list.pop(0) ছিল O(n)
        # 200 account heavy logging-এ list ধীরে ধীরে সব CPU খেয়ে ফেলত
        self.logs: deque = deque(maxlen=200)
        self.max_logs = 200  # deque maxlen-এর সাথে মিলিয়ে রাখা
        self.total_matches = 0
        self.total_gained_exp = 0
        self.start_time = time.time()
        self.account_workers: Dict[str, asyncio.Task] = {}
        self.refresh_callbacks: Dict[str, Any] = {}
        self.account_credentials: Dict[str, Dict[str, Any]] = {}
        # ✅ DELETE করা UID গুলো ব্ল্যাকলিস্টে রাখা হয়
        # যাতে চলমান worker পুনরায় register করতে না পারে
        # ✅ FIX: এখন ডিস্কে সেভ হয় — redeploy-এর পরেও টিকে থাকে
        self.deleted_uids_file = None
        self.deleted_uids: set = set()
        # ✅ প্রতিটি UID-এর জন্য আলাদা match type — "BR" বা "LONE_WOLF"
        self.match_types: Dict[str, str] = {}
        # ✅ Global mode: ডিফল্ট AUTO — নতুন আইডি যোগ হলে বা restart হলে সবসময় AUTO
        self.global_mode: str = "AUTO"
        # ✅ Global ON/OFF — False হলে কোনো আইডি match search করবে না
        self.global_running: bool = True
        # ✅ AUTO-DELETE: gained_exp এই লিমিট পার হলে আইডি অটো ডিলিট হবে
        self.exp_limit: int = 0  # ডিফল্ট 0 — dashboard থেকে সেট করুন
        # ✅ BR EVO parallel: প্রতি আইডি একসাথে কতগুলো match চালাবে (1–10, dashboard থেকে editable)
        self.br_evo_parallel: int = max(1, min(10, int(os.environ.get("BR_EVO_PARALLEL", "1") or 1)))
        self.parallel_override: dict = {}   # uid → নির্দিষ্ট আইডির আলাদা cap
        # ✅ AUTO-DELETE queue: async cleanup-এর জন্য
        self.auto_delete_queue: set = set()
        # ✅ LEVEL LIMIT: আইডির level এই সংখ্যায় পৌঁছালে dashboard থেকে সরে যাবে (0 = বন্ধ)
        # EXP লিমিটের মতোই accounts.json থেকেও স্থায়ীভাবে মুছে যাবে
        self.level_limit: int = 0
        self.level_remove_queue: set = set()
        # ✅ config-এর guest UID → login-এর পর real account id (app.py সেট করে)
        self.guest_alias: Dict[str, str] = {}
        # ✅ OWNERS: config key (guest UID বা tok_xxxx) → যে User যোগ করেছে তার owner id
        self.owners_file = os.path.join(DATA_DIR, "account_owners.json")
        self.account_owner: Dict[str, str] = {}
        self._load_owners()
        # ✅ USER ADD LIMIT: Admin ঠিক করে প্রতিটি User সর্বোচ্চ কয়টি আইডি রাখতে পারবে (0 = সীমাহীন)
        self.settings_file = os.path.join(DATA_DIR, "dashboard_settings.json")
        self.user_add_limit: int = 0
        # ✅ AUTO-RESTART: ৬ ঘন্টা পর অটো অফলাইন → ১০ মিনিট বিরতি → আবার কানেক্ট
        self.auto_restart_enabled: bool = False
        self.auto_restart_interval_hours: float = 1.5  # ✅ FIXED: 1h 30min পর offline
        self.auto_restart_break_minutes: int = 10      # কত মিনিট offline থাকবে
        self._auto_restart_task: Optional[asyncio.Task] = None
        self._auto_restart_phase: str = ""             # "", "running", "break", "reconnecting"
        self._auto_restart_next_ts: float = 0.0        # পরবর্তী ঘটনার timestamp
        self._load_settings()
        # ✅ LOGIN FAIL AUTO-REMOVE: পর পর MAX_LOGIN_FAILS বার login fail হলে আইডি dashboard থেকে সরে যাবে
        self.login_fail_counts: Dict[str, int] = {}
        self.MAX_LOGIN_FAILS: int = int(os.environ.get("MAX_LOGIN_FAILS", "5"))
        # 🔥 SHAPPNO PARALLEL: per-account max concurrent UDP sessions (1-50, default 10)
        self.mehedi_max_match: int = int(os.environ.get("MEHEDI_MAX_MATCH", "10"))

    def set_match_type(self, uid: str, match_type: str):
        """Dashboard থেকে UID-এর match type সেট করা: শুধু 'BR_EVO'"""
        uid_str = str(uid)
        allowed = {"BR", "LONE_WOLF", "LW_HS", "BR_EVO"}
        if match_type not in allowed:
            match_type = "BR_EVO"
        self.match_types[uid_str] = match_type
        if uid_str in self.accounts:
            self.accounts[uid_str]["match_type"] = match_type
            self.accounts[uid_str]["last_updated"] = time.strftime("%H:%M:%S")

    def set_auto_all(self):
        """সব আইডিকে AUTO (Level-based) মোডে ফেরানো এবং global_mode = AUTO"""
        self.global_mode = "AUTO"
        for uid_str in list(self.accounts.keys()):
            self.match_types.pop(uid_str, None)
            lvl = self.get_account_level(uid_str)
            self.accounts[uid_str]["match_type"] = "BR_EVO"

    def get_match_type(self, uid: str) -> str:
        """UID-এর বর্তমান match type — সবসময় BR_EVO (Dashboard Bear EVO)"""
        uid_str = str(uid)
        return self.match_types.get(uid_str, "BR_EVO")

    def get_max_parallel(self, uid: str) -> int:
        """আইডির কার্যকর parallel cap (1–10): per-ID override, না থাকলে global"""
        v = self.parallel_override.get(str(uid), self.br_evo_parallel)
        return max(1, min(10, int(v or 1)))

    async def _async_auto_delete(self, uid_str: str):
        """45000 EXP পূর্ণ হওয়া আইডির async cleanup: worker cancel + JSON ফাইল থেকে মুছে ফেলা"""
        try:
            short_key = uid_str.replace("tok_", "")[:10]

            # ✅ STEP 1: bot_state থেকে সরাও
            self.accounts.pop(uid_str, None)
            self.recalc_totals()

            # ✅ STEP 2: accounts*.json ফাইল থেকে atomic delete
            for accounts_file in get_all_account_files_dashboard():
                if not os.path.exists(accounts_file):
                    continue
                try:
                    with open(accounts_file, "r", encoding="utf-8") as f:
                        existing = json.load(f)
                    if not isinstance(existing, list):
                        continue
                    new_list = [
                        acc for acc in existing
                        if str(acc.get("uid", "")).strip() not in self._json_ids(uid_str)
                        and str(acc.get("token", ""))[:10] != short_key
                    ]
                    if len(new_list) < len(existing):
                        tmp_file = accounts_file + ".tmp"
                        with open(tmp_file, "w", encoding="utf-8") as f:
                            json.dump(new_list, f, indent=2, ensure_ascii=False)
                        os.replace(tmp_file, accounts_file)
                except Exception:
                    pass

            # ✅ STEP 3: Worker task বাতিল করো
            for worker_key in [uid_str, short_key]:
                if worker_key in self.account_workers:
                    task = self.account_workers.pop(worker_key)
                    task.cancel()
                    try:
                        await asyncio.wait_for(asyncio.shield(task), timeout=3.0)
                    except (asyncio.CancelledError, asyncio.TimeoutError, Exception):
                        pass

            for cache_key, cached_value in list(self.account_credentials.items()):
                if str(cache_key) in (uid_str, short_key) or (
                    isinstance(cached_value, dict) and str(cached_value.get("auth_uid", "")) == uid_str
                ):
                    self.account_credentials.pop(cache_key, None)
            callback = self.refresh_callbacks.get("on_account_deleted")
            if callback:
                try:
                    await callback(uid_str)
                except Exception:
                    pass
            self.deleted_uids.discard(uid_str)
            self.deleted_uids.discard(short_key)
            self.auto_delete_queue.discard(uid_str)
            self.log(f"[AUTO-DELETE] UID {uid_str} → EXP limit reached. Account fully removed.", "warning", uid_str)
        except Exception as e:
            self.log(f"[AUTO-DELETE ERROR] UID {uid_str}: {e}", "error", uid_str)

    def _load_deleted_uids(self):
        self.deleted_uids = set()

    def _save_deleted_uids(self):
        # Deleted IDs are never persisted; re-adding the same UID is allowed.
        return None

    def _load_settings(self):
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    d = json.load(f)
                if isinstance(d, dict):
                    self.user_add_limit = max(0, int(d.get("user_add_limit", 0) or 0))
                    # ✅ FIX: রিডিপ্লয়ের পরেও exp_limit ও level_limit টিকে থাকবে
                    saved_exp = d.get("exp_limit", None)
                    if saved_exp is not None:
                        self.exp_limit = max(0, int(saved_exp or 0))
                    saved_lv = d.get("level_limit", None)
                    if saved_lv is not None:
                        self.level_limit = max(0, int(saved_lv or 0))
                    saved_par = d.get("br_evo_parallel", None)
                    if saved_par is not None:
                        self.br_evo_parallel = max(1, min(10, int(saved_par or 1)))
                    saved_mehedi = d.get("mehedi_max_match", None)
                    if saved_mehedi is not None:
                        self.mehedi_max_match = max(1, min(50, int(saved_mehedi or 10)))
                    self.parallel_override = {
                        str(k): max(1, min(10, int(v or 1)))
                        for k, v in (d.get("parallel_override") or {}).items()
                    }
                    # ✅ AUTO-RESTART settings persist
                    self.auto_restart_enabled = bool(d.get("auto_restart_enabled", False))
                    self.auto_restart_interval_hours = max(0.5, float(d.get("auto_restart_interval_hours", 1.5) or 1.5))
                    self.auto_restart_break_minutes = max(1, int(d.get("auto_restart_break_minutes", 10) or 10))
        except Exception:
            self.user_add_limit = 0

    def _save_settings(self):
        try:
            tmp = self.settings_file + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump({
                    "user_add_limit": self.user_add_limit,
                    "exp_limit": self.exp_limit,       # ✅ FIX: persist
                    "level_limit": self.level_limit,   # ✅ FIX: persist
                    "br_evo_parallel": self.br_evo_parallel,
                    "mehedi_max_match": self.mehedi_max_match,
                    "parallel_override": self.parallel_override,
                    "auto_restart_enabled": self.auto_restart_enabled,
                    "auto_restart_interval_hours": self.auto_restart_interval_hours,
                    "auto_restart_break_minutes": self.auto_restart_break_minutes,
                }, f, indent=2)
            os.replace(tmp, self.settings_file)
        except Exception:
            pass

    def count_user_ids(self, owner: str, existing: list) -> int:
        """এই User-এর যোগ করা আইডি, যেগুলো এখনো accounts.json-এ আছে (অটো-ডিলিট/ডিলিট হলে সংখ্যা কমে)"""
        present = set()
        for acc in existing:
            if not isinstance(acc, dict):
                continue
            if acc.get("uid") is not None:
                present.add(str(acc.get("uid")))
            if acc.get("token"):
                present.add("tok_" + str(acc["token"])[:10])
        return sum(1 for k, v in self.account_owner.items() if v == owner and k in present)

    def _load_owners(self):
        try:
            if os.path.exists(self.owners_file):
                with open(self.owners_file, "r", encoding="utf-8") as f:
                    d = json.load(f)
                if isinstance(d, dict):
                    self.account_owner = {str(k): str(v) for k, v in d.items()}
        except Exception:
            self.account_owner = {}

    def _save_owners(self):
        try:
            tmp = self.owners_file + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.account_owner, f, indent=2, ensure_ascii=False)
            os.replace(tmp, self.owners_file)
        except Exception:
            pass

    def owner_of(self, key: str) -> Optional[str]:
        """ড্যাশবোর্ড key (guest হলে login-এর পর real id) থেকে মালিক খোঁজে"""
        key = str(key)
        o = self.account_owner.get(key)
        if o:
            return o
        for guest, real in self.guest_alias.items():
            if real == key and guest in self.account_owner:
                return self.account_owner[guest]
        return None

    def _json_ids(self, uid_str: str) -> set:
        """accounts.json-এ এই আইডি যে নামে আছে (guest UID হলে login-এর আগের UID-ও)"""
        ids = {uid_str}
        for guest, real in self.guest_alias.items():
            if real == uid_str:
                ids.add(guest)
        return ids

    def _remove_from_json(self, uid_str: str, reason: Optional[str] = None):
        """accounts*.json থেকে আইডি সরায় (atomic write)।
        reason দিলে ("complete" / "error") সরানো এন্ট্রি delete_accounts.json-এ জমা হয়।"""
        short_key = uid_str.replace("tok_", "")[:10]
        ids = self._json_ids(uid_str)
        archived = []
        for accounts_file in get_all_account_files_dashboard():
            if not os.path.exists(accounts_file):
                continue
            try:
                with open(accounts_file, "r", encoding="utf-8") as f:
                    existing = json.load(f)
                if not isinstance(existing, list):
                    continue
                new_list, removed = [], []
                for acc in existing:
                    hit = (isinstance(acc, dict)
                           and (str(acc.get("uid", "")).strip() in ids
                                or str(acc.get("token", ""))[:10] == short_key))
                    (removed if hit else new_list).append(acc)
                if removed:
                    tmp_file = accounts_file + ".tmp"
                    with open(tmp_file, "w", encoding="utf-8") as f:
                        json.dump(new_list, f, indent=2, ensure_ascii=False)
                    os.replace(tmp_file, accounts_file)
                    for acc in removed:
                        archived.append((acc, os.path.basename(accounts_file)))
            except Exception:
                pass
        # Deleted account credentials are not archived to a deleted-account JSON file.

    # ---------- delete_accounts.json (complete / error আইডির আর্কাইভ) ----------
    def _read_deleted_file(self) -> list:
        return []

    def _write_deleted_file(self, items: list):
        return None

    @staticmethod
    def _entry_key(acc: dict) -> str:
        if acc.get("token"):
            return "tok_" + str(acc["token"])[:10]
        return str(acc.get("uid", "")).strip()

    def _archive_deleted(self, archived: list, dashboard_id: str, reason: str):
        return None

    def deleted_file_count(self) -> int:
        return len(self._read_deleted_file())

    def restore_deleted_accounts(self) -> int:
        """delete_accounts.json-এর সব আইডি আবার accounts*.json-এ ফেরত দেয়, blacklist থেকে সরায়,
        এবং ফাইল খালি করে। ফেরত দেয়: কয়টি আইডি ফিরেছে।"""
        items = self._read_deleted_file()
        if not items:
            return 0
        by_file: Dict[str, list] = {}
        for rec in items:
            src = os.path.basename(str(rec.get("_source_file") or "accounts.json"))
            if not _fnmatch.fnmatch(src, "accounts*.json"):
                src = "accounts.json"
            clean = {k: v for k, v in rec.items() if not str(k).startswith("_")}
            by_file.setdefault(src, []).append(clean)
            # blacklist ও কাউন্টার থেকে সব সম্ভাব্য key সরাও
            keys = {str(rec.get("_dashboard_id") or ""), self._entry_key(clean),
                    str(clean.get("uid", "")).strip()}
            if clean.get("token"):
                keys.add(str(clean["token"])[:10])
            real = self.guest_alias.get(str(clean.get("uid", "")).strip())
            if real:
                keys.add(real)
            for k in keys:
                if not k:
                    continue
                self.deleted_uids.discard(k)
                self.level_remove_queue.discard(k)
                self.auto_delete_queue.discard(k)
                self.login_fail_counts.pop(k, None)
        restored = 0
        for src, entries in by_file.items():
            fp = os.path.join(DATA_DIR, src)
            try:
                existing = []
                if os.path.exists(fp):
                    with open(fp, "r", encoding="utf-8") as f:
                        d = json.load(f)
                    if isinstance(d, list):
                        existing = d
                have = {self._entry_key(a) for a in existing if isinstance(a, dict)}
                for e in entries:
                    if self._entry_key(e) not in have:
                        existing.append(e)
                        have.add(self._entry_key(e))
                    restored += 1
                tmp = fp + ".tmp"
                with open(tmp, "w", encoding="utf-8") as f:
                    json.dump(existing, f, indent=2, ensure_ascii=False)
                os.replace(tmp, fp)
            except Exception as e:
                self.log(f"[RESTORE ERROR] {src}: {e}", "error")
        self._save_deleted_uids()
        self._write_deleted_file([])
        return restored

    async def _async_level_remove(self, uid_str: str):
        """Level লিমিট পূর্ণ হলে: শুধু worker বন্ধ করা।
        accounts ও JSON check_level_limit()-এই synchronously মুছে ফেলা হয়েছে।"""
        try:
            short_key = uid_str.replace("tok_", "")[:10]
            # ✅ accounts & JSON ইতিমধ্যে check_level_limit()-এ মুছে ফেলা হয়েছে
            # শুধু worker task cancel করতে হবে
            for worker_key in [uid_str, short_key]:
                if worker_key in self.account_workers:
                    task = self.account_workers.pop(worker_key)
                    task.cancel()
                    try:
                        await asyncio.wait_for(asyncio.shield(task), timeout=3.0)
                    except (asyncio.CancelledError, asyncio.TimeoutError, Exception):
                        pass
            for cache_key, cached_value in list(self.account_credentials.items()):
                if str(cache_key) in (uid_str, short_key) or (
                    isinstance(cached_value, dict) and str(cached_value.get("auth_uid", "")) == uid_str
                ):
                    self.account_credentials.pop(cache_key, None)
            callback = self.refresh_callbacks.get("on_account_deleted")
            if callback:
                try:
                    await callback(uid_str)
                except Exception:
                    pass
            self.deleted_uids.discard(uid_str)
            self.deleted_uids.discard(short_key)
            self.log(f"[LEVEL-LIMIT] UID {uid_str} → worker stopped.", "warning", uid_str)
        except Exception as e:
            self.log(f"[LEVEL-LIMIT ERROR] UID {uid_str}: {e}", "error", uid_str)
        finally:
            self.level_remove_queue.discard(uid_str)

    def check_level_limit(self, uid_str: str):
        """আইডির level লিমিটে পৌঁছালে সাথে সাথে blacklist করে সরিয়ে দেয়"""
        if self.level_limit <= 0 or uid_str in self.level_remove_queue or uid_str in self.deleted_uids:
            return
        acc = self.accounts.get(uid_str)
        if not acc:
            return
        try:
            lv = int(acc.get("level", 1) or 1)
        except (ValueError, TypeError):
            return
        if lv >= self.level_limit:
            self.level_remove_queue.add(uid_str)
            self.deleted_uids.add(uid_str)      # reload না চাপা পর্যন্ত আর register/start হবে না
            self._save_deleted_uids()           # ✅ FIX: redeploy-এর পরেও blacklist টিকে থাকবে
            self.match_types.pop(uid_str, None)

            # ✅ FIX: Dashboard থেকে সাথে সাথে (synchronously) মুছে ফেলো।
            # আগে শুধু async task-এর উপর নির্ভর করত — task fail হলে account
            # "Offline" হয়ে dashboard-এ রয়ে যেত। এখন এখানেই মুছে যাবে।
            self.accounts.pop(uid_str, None)
            self.recalc_totals()
            self._remove_from_json(uid_str, "complete")     # accounts.json থেকে সরিয়ে delete_accounts.json-এ রাখো
            self.log(
                f"[LEVEL-LIMIT] UID {uid_str} → Lv{lv} (লিমিট: Lv{self.level_limit})। "
                f"আইডি dashboard ও accounts.json থেকে সরিয়ে delete_accounts.json-এ রাখা হয়েছে।",
                "warning", uid_str
            )
            # Worker cancel async-এ করা হবে
            try:
                # ✅ CRASH FIX: get_event_loop() → get_running_loop() — Python 3.12-এ safe
                asyncio.get_running_loop().create_task(self._async_level_remove(uid_str))
            except RuntimeError:
                # Event loop না থাকলেও কোনো সমস্যা নেই — account ইতিমধ্যে মুছে গেছে
                self.level_remove_queue.discard(uid_str)

    def enforce_level_limit(self):
        """লিমিট সেট/পরিবর্তনের সময় চলমান সব আইডি যাচাই"""
        for uid_str in list(self.accounts.keys()):
            self.check_level_limit(uid_str)

    def get_account_level(self, uid: str) -> int:
        """UID-এর current level পড়া — default 1"""
        uid_str = str(uid)
        if uid_str in self.accounts:
            return int(self.accounts[uid_str].get("level", 1) or 1)
        return 1

    def log(self, message: str, level: str = "info", uid: Optional[str] = None):
        entry = {
            "time": time.strftime("%H:%M:%S"),
            "level": level,
            "message": message,
            "uid": uid
        }
        self.logs.append(entry)  # ✅ deque(maxlen=200) স্বয়ংক্রিয়ভাবে পুরনো entry ফেলে দেয়
        _append_log_file(entry)

    def preload_pending(self) -> int:
        """accounts*.json পড়ে সাথে সাথে 'Connecting' কার্ড দেখায় — লগইন শেষ হওয়ার অপেক্ষা নেই"""
        n = 0
        try:
            for fp in get_all_account_files_dashboard():
                if not os.path.exists(fp):
                    continue
                try:
                    with open(fp, "r", encoding="utf-8") as f:
                        data = json.load(f)
                except Exception:
                    continue
                if not isinstance(data, list):
                    continue
                for acc in data:
                    if not isinstance(acc, dict) or not acc.get("uid"):
                        continue
                    key = str(acc["uid"]).strip()
                    if not key or key in self.deleted_uids or key in self.accounts:
                        continue
                    # আগেই লগইন হয়ে গেলে (alias) আবার placeholder নয়
                    real = self.guest_alias.get(key)
                    if real and real in self.accounts:
                        continue
                    self.accounts[key] = {
                        "uid": key, "nickname": f"Player_{key[:6]}", "region": "BD",
                        "level": 0, "initial_exp": 0, "current_exp": 0, "gained_exp": 0,
                        "likes": 0, "status": "CONNECTING", "matches_played": 0,
                        "active_matches": 0, "last_match_time": None,
                        "last_updated": time.strftime("%H:%M:%S"),
                        "match_type": "BR_EVO", "_pending": True,
                        "last_info": "Logging in…",
                    }
                    n += 1
        except Exception:
            pass
        return n

    def _prune_pending(self, real_uid: str = None):
        """লগইন হয়ে গেলে placeholder সরাও (guest uid ≠ real id হলেও)"""
        for k in [k for k, a in self.accounts.items() if a.get("_pending")]:
            real = self.guest_alias.get(k)
            if k == real_uid or (real and real != k and real in self.accounts
                                 and not self.accounts[real].get("_pending")):
                self.accounts.pop(k, None)

    def register_account(self, uid: str, nickname: str, region: str, level: int, exp: int, likes: int = 0):
        uid_str = str(uid)
        # placeholder থাকলে আসল ডেটা দিয়ে নতুন করে রেজিস্টার হবে
        if uid_str in self.accounts and self.accounts[uid_str].get("_pending"):
            self.accounts.pop(uid_str, None)
        self._prune_pending(uid_str)
        # ✅ ব্ল্যাকলিস্টে থাকলে re-register করবে না — এটাই মূল সমস্যা ছিল
        if uid_str in self.deleted_uids:
            return
        if uid_str not in self.accounts:
            # ✅ নতুন আইডি (dashboard বা accounts.json থেকে) সবসময় AUTO মোডে শুরু হবে
            self.match_types.pop(uid_str, None)
            # ✅ FIX: নতুন আইডি এলে বাকি আইডির BR/LW সেটিং রিসেট হবে না;
            # নতুন আইডি বর্তমান global মোড (BR / LONE_WOLF) পাবে
            if self.global_mode in ("BR", "LONE_WOLF"):
                self.match_types[uid_str] = self.global_mode
            self.accounts[uid_str] = {
                "uid": uid_str,
                "nickname": nickname or f"Player_{uid_str[:6]}",
                "region": region or "BD",
                "level": level or 1,
                "initial_exp": exp,
                "current_exp": exp,
                "gained_exp": 0,
                "likes": likes or 0,
                "status": "ONLINE",
                "matches_played": 0,
                "active_matches": 0,
                "last_match_time": None,
                "last_updated": time.strftime("%H:%M:%S"),
                "match_type": (self.global_mode if self.global_mode in ("BR", "LONE_WOLF", "BR_EVO")
                               else ("BR" if (level or 1) == 2 and self.global_mode == "AUTO" else "LONE_WOLF"))
            }
        else:
            acc = self.accounts[uid_str]
            if nickname:
                acc["nickname"] = nickname
            if region:
                acc["region"] = region
            if level:
                acc["level"] = level
                self.get_match_type(uid_str)   # level barhle BR -> LW auto switch
            acc["current_exp"] = exp
            acc["gained_exp"] = max(0, exp - acc["initial_exp"])
            acc["likes"] = likes
            acc["status"] = "ONLINE"
            acc["last_updated"] = time.strftime("%H:%M:%S")
        self.recalc_totals()
        self.check_level_limit(uid_str)

    def update_exp(self, uid: str, current_exp: int, level: Optional[int] = None):
        uid_str = str(uid)
        # ✅ ডিলিট করা আইডি আপডেট হবে না
        if uid_str in self.deleted_uids:
            return
        if uid_str in self.accounts:
            acc = self.accounts[uid_str]
            old_exp = acc["current_exp"]
            acc["current_exp"] = current_exp
            if level is not None and level > 0:
                acc["level"] = level
                self.get_match_type(uid_str)   # level barhle BR -> LW auto switch
            acc["gained_exp"] = max(0, current_exp - acc["initial_exp"])
            acc["last_updated"] = time.strftime("%H:%M:%S")
            diff = current_exp - old_exp
            if diff > 0:
                self.log(f"Account {acc['nickname']} ({uid_str}) gained +{diff} EXP! Total: +{acc['gained_exp']}", "success", uid_str)
            self.recalc_totals()
            self.check_level_limit(uid_str)

            # ✅ AUTO-DELETE: gained_exp ≥ exp_limit হলে আইডি অটোমেটিক মুছে যাবে
            if self.exp_limit > 0 and acc["gained_exp"] >= self.exp_limit and uid_str not in self.auto_delete_queue:
                self.auto_delete_queue.add(uid_str)
                nickname = acc.get("nickname", uid_str)
                # তৎক্ষণাৎ blacklist করো — worker আর কোনো match খেলবে না
                self.deleted_uids.add(uid_str)
                self.match_types.pop(uid_str, None)
                # ✅ FIX: Dashboard ও JSON থেকে সাথে সাথে (synchronously) মুছে ফেলো।
                # আগে শুধু async task-এর উপর নির্ভর করত — task fail হলে account
                # "Offline" হয়ে dashboard-এ রয়ে যেত। এখন level_limit-এর মতোই
                # synchronous removal করা হচ্ছে।
                self.accounts.pop(uid_str, None)
                self.recalc_totals()
                self._remove_from_json(uid_str, "complete")
                self.log(
                    f"[AUTO-DELETE] {nickname} ({uid_str}) → {acc['gained_exp']} EXP অর্জন করেছে "
                    f"(লিমিট: {self.exp_limit})। আইডি dashboard ও accounts.json থেকে সরিয়ে delete_accounts.json-এ রাখা হয়েছে।",
                    "warning", uid_str
                )
                # Async cleanup: এখন শুধু worker task cancel করতে হবে
                try:
                    # ✅ CRASH FIX: get_event_loop() → get_running_loop() — Python 3.12-এ safe
                    asyncio.get_running_loop().create_task(
                        self._async_auto_delete(uid_str)
                    )
                except RuntimeError:
                    self.auto_delete_queue.discard(uid_str)

    def update_status(self, uid: str, status: str, active_matches: Optional[int] = None):
        uid_str = str(uid)
        # ✅ ডিলিট করা আইডি status update হবে না
        if uid_str in self.deleted_uids:
            return
        if uid_str in self.accounts:
            self.accounts[uid_str]["status"] = status
            if status in ("ONLINE", "IN_MATCH", "SEARCHING"):
                self.accounts[uid_str].pop("last_error", None)
            if active_matches is not None:
                self.accounts[uid_str]["active_matches"] = active_matches
            self.accounts[uid_str]["last_updated"] = time.strftime("%H:%M:%S")

    def set_error(self, uid: str, message: str):
        uid_str = str(uid)
        if uid_str in self.deleted_uids:
            return
        if uid_str in self.accounts:
            self.accounts[uid_str]["last_error"] = f"{time.strftime('%H:%M:%S')} - {message}"[:300]

    def record_login_fail(self, uid: str):
        """Login failure count বাড়ায়। MAX_LOGIN_FAILS পেরোলে আইডি dashboard থেকে auto-remove হয়।"""
        uid_str = str(uid)
        if uid_str in self.deleted_uids:
            return
        self.login_fail_counts[uid_str] = self.login_fail_counts.get(uid_str, 0) + 1
        count = self.login_fail_counts[uid_str]
        self.log(
            f"[LOGIN-FAIL] UID {uid_str} → {count}/{self.MAX_LOGIN_FAILS} consecutive login failure",
            "warning", uid_str
        )
        if count >= self.MAX_LOGIN_FAILS:
            # ✅ থ্রেশহোল্ড পার হলে EXP-limit-এর মতোই synchronous removal
            nickname = (self.accounts.get(uid_str) or {}).get("nickname", uid_str)
            self.deleted_uids.add(uid_str)
            self.match_types.pop(uid_str, None)
            self.login_fail_counts.pop(uid_str, None)
            self.accounts.pop(uid_str, None)
            self.recalc_totals()
            self._remove_from_json(uid_str, "error")
            self.log(
                f"[LOGIN-FAIL-REMOVE] {nickname} ({uid_str}) → {count} বার connection fail। "
                f"আইডি dashboard ও accounts.json থেকে সরিয়ে delete_accounts.json-এ রাখা হয়েছে।",
                "error", uid_str
            )
            try:
                asyncio.get_running_loop().create_task(self._async_login_fail_remove(uid_str))
            except RuntimeError:
                pass

    def reset_login_fail(self, uid: str):
        """সফল login-এ fail counter রিসেট করে।"""
        self.login_fail_counts.pop(str(uid), None)

    async def _async_login_fail_remove(self, uid_str: str):
        """login fail-এর কারণে removed আইডির async worker cancel।"""
        try:
            short_key = uid_str.replace("tok_", "")[:10]
            for worker_key in [uid_str, short_key]:
                if worker_key in self.account_workers:
                    task = self.account_workers.pop(worker_key)
                    task.cancel()
                    try:
                        await asyncio.wait_for(asyncio.shield(task), timeout=3.0)
                    except (asyncio.CancelledError, asyncio.TimeoutError, Exception):
                        pass
            for cache_key, cached_value in list(self.account_credentials.items()):
                if str(cache_key) in (uid_str, short_key) or (
                    isinstance(cached_value, dict) and str(cached_value.get("auth_uid", "")) == uid_str
                ):
                    self.account_credentials.pop(cache_key, None)
            callback = self.refresh_callbacks.get("on_account_deleted")
            if callback:
                try:
                    await callback(uid_str)
                except Exception:
                    pass
            self.deleted_uids.discard(uid_str)
            self.deleted_uids.discard(short_key)
        except Exception as e:
            self.log(f"[LOGIN-FAIL-REMOVE ERROR] UID {uid_str}: {e}", "error", uid_str)

    def set_info(self, uid: str, message: str):
        uid_str = str(uid)
        if uid_str in self.deleted_uids:
            return
        if uid_str in self.accounts:
            self.accounts[uid_str]["last_info"] = f"{time.strftime('%H:%M:%S')} - {message}"[:300]

    def increment_match(self, uid: str):
        uid_str = str(uid)
        self.total_matches += 1
        if uid_str in self.accounts:
            self.accounts[uid_str]["matches_played"] += 1
            self.accounts[uid_str]["last_match_time"] = time.strftime("%H:%M:%S")
            self.accounts[uid_str]["last_updated"] = time.strftime("%H:%M:%S")
            self.log(f"Account {self.accounts[uid_str]['nickname']} finished Match #{self.accounts[uid_str]['matches_played']}", "info", uid_str)

    def recalc_totals(self):
        # ✅ PERF FIX: 200 account-এ প্রতিবার full sum না করে একবারে গণনা
        self.total_gained_exp = sum(
            int(acc.get("gained_exp", 0) or 0) for acc in self.accounts.values()
        )


bot_state = BotState()


# ==================== HTTP HANDLERS ====================

_HTML_BYTES = None

async def handle_index(request: web.Request) -> web.Response:
    # HTML is embedded — encode once, reuse; gzip handled by middleware
    global _HTML_BYTES
    if _HTML_BYTES is None:
        _HTML_BYTES = DASHBOARD_HTML.encode("utf-8")
    et = '"' + hashlib.md5(_HTML_BYTES).hexdigest()[:16] + '"'
    if request.headers.get("If-None-Match") == et:
        return web.Response(status=304, headers={"ETag": et, "Cache-Control": "no-cache"})
    return web.Response(body=_HTML_BYTES, content_type="text/html", charset="utf-8",
                        headers={"ETag": et, "Cache-Control": "no-cache"})


_STATS_CACHE: Dict[str, Any] = {}   # key -> (timestamp, raw_bytes, etag, gzip_bytes)
_STATS_TTL = 2.0                     # সেকেন্ড — অনেক ট্যাব/ইউজার থাকলেও সার্ভার ১ বারই বানাবে
_STATS_STALE_MAX = 90.0              # এর মধ্যে পুরনো snapshot দিয়েও সাথে সাথে reply দেওয়া হয় (পেছনে নতুন বানায়)
_LAST_STATS_REQ = 0.0
_REBUILDING: set = set()
_BG_TASKS: list = []

# ---- Event-loop lag monitor: bot-এর CPU load কতটা তা মাপে (app.py এটা দেখে login/launch ধীর-দ্রুত করে) ----
_LOOP_LAG = 0.0

def get_loop_lag() -> float:
    return _LOOP_LAG

async def _loop_lag_monitor():
    global _LOOP_LAG
    while True:
        t = time.monotonic()
        await asyncio.sleep(0.5)
        lag = max(0.0, time.monotonic() - t - 0.5)
        _LOOP_LAG = lag if lag > _LOOP_LAG else (_LOOP_LAG * 0.6 + lag * 0.4)

async def _snapshot_refresher():
    """Admin snapshot আগে থেকেই বানিয়ে রাখে — /api/stats তখন শুধু ready bytes ফেরত দেয়।"""
    while True:
        try:
            if time.monotonic() - _LAST_STATS_REQ < 120:
                await _store_snapshot(None, "admin", "admin")
        except Exception:
            pass
        await asyncio.sleep(1.5)

async def _store_snapshot(request, role: str, ckey: str):
    import gzip as _gzip
    resp = await _build_stats(request, role)
    body = resp.body if isinstance(resp.body, (bytes, bytearray)) else resp.text.encode("utf-8")
    body = bytes(body)
    etag = '"' + hashlib.md5(body).hexdigest()[:16] + '"'
    gz = _gzip.compress(body, 4) if len(body) > 1024 else None
    if len(_STATS_CACHE) > 200:
        _STATS_CACHE.clear()
    _STATS_CACHE[ckey] = (time.monotonic(), body, etag, gz)
    return _STATS_CACHE[ckey]

async def _rebuild_bg(request, role: str, ckey: str):
    try:
        await _store_snapshot(request, role, ckey)
    except Exception:
        pass
    finally:
        _REBUILDING.discard(ckey)


async def handle_get_stats(request: web.Request) -> web.Response:
    global _LAST_STATS_REQ
    role = request.get("role", "admin")
    ckey = role if role != "user" else "user:" + str(_owner_id(request))
    now = time.monotonic()
    _LAST_STATS_REQ = now
    hit = _STATS_CACHE.get(ckey)
    if hit and now - hit[0] < _STATS_TTL:
        return _stats_reply(request, hit)
    if hit and now - hit[0] < _STATS_STALE_MAX:
        # পুরনো snapshot সাথে সাথে দাও, নতুনটা পেছনে বানাও — user কখনো অপেক্ষা করবে না
        if ckey not in _REBUILDING:
            _REBUILDING.add(ckey)
            asyncio.ensure_future(_rebuild_bg(request, role, ckey))
        return _stats_reply(request, hit)
    hit = await _store_snapshot(request, role, ckey)
    return _stats_reply(request, hit)


def _stats_reply(request: web.Request, hit) -> web.Response:
    _ts, body, etag, gz = hit
    # ডেটা বদলায়নি → 304, কোনো body পাঠানো লাগে না
    if request.headers.get("If-None-Match") == etag:
        return web.Response(status=304, headers={"ETag": etag, "Cache-Control": "no-cache"})
    headers = {"ETag": etag, "Cache-Control": "no-cache", "Vary": "Accept-Encoding"}
    if gz is not None and "gzip" in request.headers.get("Accept-Encoding", "").lower():
        headers["Content-Encoding"] = "gzip"   # আগে থেকেই compress করা — প্রতি request-এ CPU লাগে না
        return web.Response(body=gz, content_type="application/json", headers=headers)
    return web.Response(body=body, content_type="application/json", headers=headers)


async def handle_healthz(request: web.Request) -> web.Response:
    return web.Response(text="ok", headers={"Cache-Control": "no-store"})


async def _build_stats(request: web.Request, role: str) -> web.Response:
    bot_state._prune_pending()
    accounts_data = list(bot_state.accounts.values())
    logs = list(bot_state.logs)[-60:]  # ✅ FIX: deque → list convert করে slice
    total_matches = bot_state.total_matches
    total_exp = bot_state.total_gained_exp
    if role == "user":
        # ✅ User শুধু নিজের যোগ করা আইডি ও সেগুলোর লগ দেখবে
        me = _owner_id(request)
        _owned: Dict[str, bool] = {}
        def _mine(k) -> bool:
            k = str(k)
            if k not in _owned:
                _owned[k] = bool(me) and bot_state.owner_of(k) == me
            return _owned[k]
        accounts_data = [a for a in accounts_data if _mine(a.get("uid"))]
        logs = [l for l in bot_state.logs if l.get("uid") and _mine(l["uid"])][-60:]
        total_matches = sum(int(a.get("matches_played", 0) or 0) for a in accounts_data)
        total_exp = sum(int(a.get("gained_exp", 0) or 0) for a in accounts_data)
    # ✅ বেশি লেভেল উপরে (descending); একই লেভেল হলে বেশি gained EXP আগে
    accounts_data.sort(key=lambda x: (int(x.get("level", 0) or 0), x.get("gained_exp", 0)), reverse=True)
    payload = {
        "total_accounts": len(accounts_data),
        "total_matches": total_matches,
        "total_gained_exp": total_exp,
        "accounts": accounts_data,
        "logs": logs,
        "uptime": int(time.time() - bot_state.start_time),
        "global_running": bot_state.global_running,
        "global_mode": bot_state.global_mode,
        "exp_limit": bot_state.exp_limit,
        "level_limit": bot_state.level_limit,
        "br_evo_parallel": bot_state.br_evo_parallel,
        "mehedi_max_match": bot_state.mehedi_max_match,
        "user_add_limit": bot_state.user_add_limit,
        "deleted_file_count": bot_state.deleted_file_count() if role != "user" else 0,
        "role": role,
        # ✅ AUTO-RESTART info
        "auto_restart_enabled": bot_state.auto_restart_enabled,
        "auto_restart_interval_hours": bot_state.auto_restart_interval_hours,
        "auto_restart_break_minutes": bot_state.auto_restart_break_minutes,
        "auto_restart_phase": bot_state._auto_restart_phase,
        "auto_restart_next_ts": bot_state._auto_restart_next_ts,
    }
    if _orjson is not None:
        return web.Response(body=_orjson.dumps(payload), content_type="application/json")
    return web.json_response(payload)


def _check_user_limit(role: str, owner: Optional[str], owner_key: str, existing: list) -> Optional[str]:
    """User-এর আইডি লিমিট পূর্ণ হলে error মেসেজ ফেরত দেয়। Admin-এর কোনো লিমিট নেই।"""
    lim = bot_state.user_add_limit
    if role != "user" or lim <= 0 or not owner:
        return None
    # নিজের আগে যোগ করা আইডি আবার যোগ করলে নতুন স্লট লাগে না
    if bot_state.account_owner.get(owner_key) == owner:
        return None
    if bot_state.count_user_ids(owner, existing) >= lim:
        return f"ID limit reached. You can add up to {lim} ID(s) only."
    return None


async def handle_add_account(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        role = request.get("role", "admin")
        new_owner_cookie = None
        owner = None
        if role == "user":
            owner = _owner_id(request)
            if not owner:
                owner = _secrets.token_hex(6)
                new_owner_cookie = _owner_cookie_value(owner)
        accounts_file = ACCOUNTS_FILE_PATH
        existing = []
        if os.path.exists(accounts_file):
            try:
                with open(accounts_file, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            except Exception:
                existing = []

        if "uid" in data and "password" in data:
            uid = str(data["uid"]).strip()
            pwd = str(data["password"]).strip()
            if not uid or not pwd:
                return web.json_response({"status": "error", "error": "UID and Password are required"})
            owner_key = uid
            if role == "user" and (any(str(acc.get("uid")) == uid for acc in existing) or uid in bot_state.accounts) \
                    and bot_state.account_owner.get(uid) != owner:
                return web.json_response({"status": "error", "error": "This account already exists"})
            lim_err = _check_user_limit(role, owner, owner_key, existing)
            if lim_err:
                return web.json_response({"status": "error", "error": lim_err})
            existing = [acc for acc in existing if str(acc.get("uid")) != uid]
            existing.append({"uid": uid, "password": pwd})
            # ✅ Re-add করলে blacklist থেকে সরাও — না হলে আর চালু হবে না
            bot_state.deleted_uids.discard(uid)
        elif "token" in data:
            token = str(data["token"]).strip()
            if not token:
                return web.json_response({"status": "error", "error": "Token is required"})
            owner_key = f"tok_{token[:10]}"
            if role == "user" and (any(acc.get("token") == token for acc in existing) or owner_key in bot_state.accounts) \
                    and bot_state.account_owner.get(owner_key) != owner:
                return web.json_response({"status": "error", "error": "This account already exists"})
            lim_err = _check_user_limit(role, owner, owner_key, existing)
            if lim_err:
                return web.json_response({"status": "error", "error": lim_err})
            existing = [acc for acc in existing if acc.get("token") != token]
            existing.append({"token": token})
            # ✅ Token re-add করলে blacklist থেকে সরাও
            bot_state.deleted_uids.discard(token[:10])
            bot_state.deleted_uids.discard(f"tok_{token[:10]}")
        else:
            return web.json_response({"status": "error", "error": "Invalid payload"})

        with open(accounts_file, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2)

        # মালিক নথিভুক্ত করো (User হলে) — Admin যোগ করলে মালিক থাকে না, শুধু Admin দেখবে
        if role == "user" and owner:
            bot_state.account_owner[owner_key] = owner
            bot_state._save_owners()
        elif role == "admin":
            if bot_state.account_owner.pop(owner_key, None) is not None:
                bot_state._save_owners()

        bot_state.log(f"New account added: {data.get('uid') or 'Token'}", "success", owner_key)

        # Trigger dynamic worker launch
        if "on_account_added" in bot_state.refresh_callbacks:
            asyncio.create_task(bot_state.refresh_callbacks["on_account_added"](data))

        resp = web.json_response({"status": "ok"})
        if new_owner_cookie:
            resp.set_cookie(OWNER_COOKIE, new_owner_cookie, max_age=365 * 86400,
                            httponly=True, samesite="Lax", secure=_is_https(request), path="/")
        return resp
    except Exception as e:
        return web.json_response({"status": "error", "error": str(e)})


async def handle_delete_account(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        uid = str(data.get("uid", "")).strip()
        if not uid:
            return web.json_response({"status": "error", "error": "uid missing"})

        # token-based worker key: "tok_abcdefghij" → "abcdefghij"
        short_key = uid.replace("tok_", "")[:10]

        # ✅ সব accounts*.json ফাইলে খুঁজে atomic write দিয়ে delete করে
        for accounts_file in get_all_account_files_dashboard():
            if not os.path.exists(accounts_file):
                continue
            try:
                with open(accounts_file, "r", encoding="utf-8") as f:
                    existing = json.load(f)
                if not isinstance(existing, list):
                    continue

                new_list = [
                    acc for acc in existing
                    if str(acc.get("uid", "")).strip() != uid
                    and str(acc.get("token", ""))[:10] != short_key
                ]

                if len(new_list) < len(existing):
                    # ✅ Atomic write — crash হলে ফাইল নষ্ট হবে না
                    tmp_file = accounts_file + ".tmp"
                    with open(tmp_file, "w", encoding="utf-8") as f:
                        json.dump(new_list, f, indent=2, ensure_ascii=False)
                    os.replace(tmp_file, accounts_file)
            except Exception:
                pass

        # ✅ STEP 1: আগেই ব্ল্যাকলিস্টে যোগ করো
        # এর ফলে চলমান worker আর re-register করতে পারবে না
        bot_state.deleted_uids.add(uid)
        bot_state.deleted_uids.add(short_key)

        # ✅ STEP 2: bot_state থেকে সরাও এবং totals আপডেট করো
        if uid in bot_state.accounts:
            del bot_state.accounts[uid]
            bot_state.recalc_totals()
        for cache_key, cached_value in list(bot_state.account_credentials.items()):
            if str(cache_key) in (uid, short_key) or (
                isinstance(cached_value, dict) and str(cached_value.get("auth_uid", "")) == uid
            ):
                bot_state.account_credentials.pop(cache_key, None)

        # ✅ STEP 3: Worker বাতিল করো এবং সম্পূর্ণভাবে await করো
        # break ছিল আগে — এর ফলে দুটো key-এর একটাই cancel হতো
        # এখন দুটোই cancel করা হবে এবং properly await করা হবে
        for worker_key in [uid, short_key]:
            if worker_key in bot_state.account_workers:
                task = bot_state.account_workers.pop(worker_key)
                task.cancel()
                try:
                    await asyncio.wait_for(asyncio.shield(task), timeout=3.0)
                except (asyncio.CancelledError, asyncio.TimeoutError, Exception):
                    pass  # cancel হয়েছে — এটাই স্বাভাবিক

        bot_state.deleted_uids.discard(uid)
        bot_state.deleted_uids.discard(short_key)
        if "on_account_deleted" in bot_state.refresh_callbacks:
            try:
                await bot_state.refresh_callbacks["on_account_deleted"](uid)
            except Exception:
                pass
        bot_state.log(f"Account {uid} deleted from dashboard and accounts.json.", "warning", uid)
        return web.json_response({"status": "ok"})
    except Exception as e:
        return web.json_response({"status": "error", "error": str(e)})


async def handle_all_delete_accounts(request: web.Request) -> web.Response:
    """Admin-only: stop every account worker and remove all account credentials/caches."""
    if request.get("role", "admin") != "admin":
        return web.json_response({"status": "error", "error": "forbidden"}, status=403)
    cancelled = []
    try:
        bot_state.global_running = False
        # Mark current IDs temporarily so late worker callbacks cannot re-register them.
        bot_state.deleted_uids.update(str(k) for k in bot_state.accounts.keys())
        bot_state.deleted_uids.update(str(k) for k in bot_state.account_workers.keys())

        tasks = list(set(bot_state.account_workers.values()))
        bot_state.account_workers.clear()
        for task in tasks:
            if task and not task.done():
                task.cancel()
                cancelled.append(task)
        if cancelled:
            await asyncio.gather(*cancelled, return_exceptions=True)

        deleted = 0
        for accounts_file in get_all_account_files_dashboard():
            if os.path.exists(accounts_file):
                try:
                    with open(accounts_file, "r", encoding="utf-8") as f:
                        old = json.load(f)
                    deleted += len(old) if isinstance(old, list) else 0
                except Exception:
                    pass
            try:
                tmp_file = accounts_file + ".tmp"
                with open(tmp_file, "w", encoding="utf-8") as f:
                    json.dump([], f)
                os.replace(tmp_file, accounts_file)
            except Exception:
                # Continue cleaning remaining files even if one file cannot be rewritten.
                continue

        # Clear process-memory caches too, so a re-added UID starts with a fresh login.
        if "on_all_delete" in bot_state.refresh_callbacks:
            try:
                await bot_state.refresh_callbacks["on_all_delete"]()
            except Exception:
                pass

        # Remove credential/token caches so re-added accounts authenticate afresh.
        for cache_path in (
            os.path.join(DATA_DIR, "delete_accounts.json"),
            os.path.join(DATA_DIR, "deleted_uids.json"),
            os.path.join(DATA_DIR, "data", "token_cache.json"),
            os.path.join(DATA_DIR, "data", "devices.json"),
            os.path.join(DATA_DIR, "account_owners.json"),
        ):
            try:
                if os.path.isfile(cache_path):
                    os.remove(cache_path)
            except Exception:
                pass

        bot_state.accounts.clear()
        bot_state.account_credentials.clear()
        bot_state.guest_alias.clear()
        bot_state.account_owner.clear()
        bot_state.match_types.clear()
        bot_state.parallel_override.clear()
        bot_state.login_fail_counts.clear()
        bot_state.auto_delete_queue.clear()
        bot_state.level_remove_queue.clear()
        bot_state.deleted_uids.clear()
        bot_state.total_matches = 0
        bot_state.total_gained_exp = 0
        bot_state.recalc_totals()
        bot_state.global_running = True
        _STATS_CACHE.clear()
        bot_state.log(f"[ALL DELETE] Removed {deleted} account(s); all account workers stopped.", "warning")
        return web.json_response({"status": "ok", "deleted": deleted, "stopped": len(cancelled)})
    except Exception as e:
        # Never leave a stale blacklist behind if an exception occurs.
        bot_state.deleted_uids.clear()
        return web.json_response({"status": "error", "error": str(e)}, status=500)


async def handle_refresh_account(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        uid = str(data.get("uid")).strip()
        if "on_refresh_account" in bot_state.refresh_callbacks:
            asyncio.create_task(bot_state.refresh_callbacks["on_refresh_account"](uid))
        return web.json_response({"status": "ok"})
    except Exception as e:
        return web.json_response({"status": "error", "error": str(e)})


# ==================== BULK ADD (JSON FILE) ====================
BULK_MAX_ACCOUNTS = 5000
BULK_LAUNCH_GAP_SEC = 1.5   # সব ID একসাথে login না করে একটু একটু করে চালু হবে


async def _bulk_launch(cb, payloads):
    for p in payloads:
        try:
            await cb(p)
        except Exception as e:
            bot_state.log(f"[BULK] Launch error {p.get('uid')}: {e}", "error")
        await asyncio.sleep(BULK_LAUNCH_GAP_SEC)


async def handle_bulk_add_account(request: web.Request) -> web.Response:
    """JSON file থেকে অনেক guest account একসাথে যোগ করে.
    Body: {"region": "BD", "accounts": [{"uid": "...", "password": "..."}, ...]}
    """
    try:
        data = await request.json()
        region = (data.get("region") or "BD") if isinstance(data, dict) else "BD"
        raw_text = data.get("text", "") if isinstance(data, dict) else ""
        if raw_text:
            items = []
            for line_no, raw_line in enumerate(str(raw_text).splitlines(), 1):
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                if ":" not in line:
                    items.append({"uid": "", "password": ""})
                    continue
                uid, pwd = line.split(":", 1)
                items.append({"uid": uid.strip(), "password": pwd.strip()})
        else:
            items = []
        if not isinstance(items, list) or not raw_text:
            return web.json_response({"status": "error", "error": "Upload a TXT file using UID:password, one per line"})
        if len(items) > BULK_MAX_ACCOUNTS:
            return web.json_response({"status": "error", "error": f"Max {BULK_MAX_ACCOUNTS} accounts per file"})

        role = request.get("role", "admin")
        owner, new_owner_cookie = None, None
        if role == "user":
            owner = _owner_id(request)
            if not owner:
                owner = _secrets.token_hex(6)
                new_owner_cookie = _owner_cookie_value(owner)

        existing = []
        if os.path.exists(ACCOUNTS_FILE_PATH):
            try:
                with open(ACCOUNTS_FILE_PATH, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            except Exception:
                existing = []

        added, launch, errors = [], [], []
        skipped = 0
        seen = set()
        for idx, item in enumerate(items, 1):
            if not isinstance(item, dict):
                errors.append(f"#{idx}: invalid entry")
                continue
            uid = str(item.get("uid", "")).strip()
            pwd = str(item.get("password", item.get("pass", ""))).strip()
            if not uid or not pwd:
                errors.append(f"#{idx}: uid/password missing")
                continue
            # আগে থেকে আছে বা file-এ duplicate → skip
            if uid in seen or uid in bot_state.accounts or any(str(a.get("uid")) == uid for a in existing):
                seen.add(uid)
                skipped += 1
                continue
            seen.add(uid)
            lim_err = _check_user_limit(role, owner, uid, existing)
            if lim_err:
                errors.append(f"{uid}: {lim_err}")
                break
            existing.append({"uid": uid, "password": pwd})
            bot_state.deleted_uids.discard(uid)
            if owner:
                bot_state.account_owner[uid] = owner
            added.append(uid)
            launch.append({"type": "guest", "region": region, "uid": uid, "password": pwd})

        if added:
            with open(ACCOUNTS_FILE_PATH, "w", encoding="utf-8") as f:
                json.dump(existing, f, indent=2)
            if owner:
                bot_state._save_owners()
            bot_state.log(f"[BULK] {len(added)} account added, {skipped} skipped", "success")
            if "on_account_added" in bot_state.refresh_callbacks:
                asyncio.create_task(
                    _bulk_launch(bot_state.refresh_callbacks["on_account_added"], launch)
                )

        resp = web.json_response({
            "status": "ok",
            "added": len(added),
            "skipped": skipped,
            "error_count": len(errors),
            "errors": errors[:50],
        })
        if new_owner_cookie:
            resp.set_cookie(OWNER_COOKIE, new_owner_cookie, max_age=365 * 86400,
                            httponly=True, samesite="Lax", secure=_is_https(request), path="/")
        return resp
    except Exception as e:
        return web.json_response({"status": "error", "error": str(e)})


async def handle_reload_accounts(request: web.Request) -> web.Response:
    """
    accounts*.json ফাইল থেকে নতুন করে সব account load করে।
    - deleted_uids blacklist পুরোপুরি clear হয়
    - যে accounts এখন চলছে না কিন্তু JSON এ আছে সেগুলো স্বয়ংক্রিয়ভাবে চালু হয়
    - ইতিমধ্যে চলমান accounts অপরিবর্তিত থাকে
    """
    try:
        # ✅ STEP 1: পুরো blacklist clear করো
        cleared = len(bot_state.deleted_uids)
        bot_state.deleted_uids.clear()
        bot_state.level_remove_queue.clear()
        bot_state._save_deleted_uids()  # ✅ FIX: ফাইলও clear করো

        # ✅ STEP 2: app.py-এর reload callback ডাকো
        bot_state.preload_pending()   # সাথে সাথে কার্ড দেখাও
        _STATS_CACHE.clear()
        added = 0
        pending = False
        if "on_reload_accounts" in bot_state.refresh_callbacks:
            task = asyncio.ensure_future(bot_state.refresh_callbacks["on_reload_accounts"]())
            done, _ = await asyncio.wait({task}, timeout=1.5)   # দেরি হলে ব্যাকগ্রাউন্ডে চলবে — button আটকে থাকবে না
            if task in done:
                added = task.result()
            else:
                pending = True

        msg = (f"Reload started in background ({cleared} blacklist cleared). Accounts will appear shortly."
               if pending else
               f"Reload complete: {cleared} blacklisted UIDs cleared, {added} new account(s) started.")
        bot_state.log(msg, "success")
        return web.json_response({"status": "ok", "message": msg, "cleared": cleared, "started": added})
    except Exception as e:
        return web.json_response({"status": "error", "error": str(e)})


async def handle_restore_deleted(request: web.Request) -> web.Response:
    """delete_accounts.json-এর আইডি ড্যাশবোর্ডে ফিরিয়ে এনে আবার চালু করে"""
    try:
        restored = bot_state.restore_deleted_accounts()
        if restored == 0:
            return web.json_response({"status": "ok", "restored": 0,
                                      "message": "delete_accounts.json খালি — ফেরানোর মতো কোনো আইডি নেই।"})
        bot_state.preload_pending()
        _STATS_CACHE.clear()
        started, pending = 0, False
        if "on_reload_accounts" in bot_state.refresh_callbacks:
            task = asyncio.ensure_future(bot_state.refresh_callbacks["on_reload_accounts"]())
            done, _ = await asyncio.wait({task}, timeout=1.5)
            if task in done:
                started = task.result()
            else:
                pending = True
        msg = (f"{restored}টি আইডি delete_accounts.json থেকে ফিরেছে — ব্যাকগ্রাউন্ডে চালু হচ্ছে।" if pending
               else f"{restored}টি আইডি delete_accounts.json থেকে ফিরেছে, {started}টি চালু হয়েছে।")
        bot_state.log(msg, "success")
        return web.json_response({"status": "ok", "restored": restored, "started": started, "message": msg})
    except Exception as e:
        return web.json_response({"status": "error", "error": str(e)})


async def handle_set_match_type(request: web.Request) -> web.Response:
    """Dashboard থেকে UID-এর match type পরিবর্তন করা: BR, LONE_WOLF অথবা LW_HS"""
    try:
        data = await request.json()
        uid = str(data.get("uid", "")).strip()
        match_type = str(data.get("match_type", "LONE_WOLF")).strip().upper()
        if not uid:
            return web.json_response({"status": "error", "error": "UID required"}, status=400)
        if match_type not in ("BR", "LONE_WOLF", "LW_HS", "BR_EVO"):
            return web.json_response({"status": "error", "error": "Invalid match_type. Use BR, LONE_WOLF or LW_HS"}, status=400)
        bot_state.set_match_type(uid, match_type)
        bot_state.global_mode = "CUSTOM"
        label = "🐻 Bear EVO" if match_type == "BR_EVO" else ("⚔ Battle Royale" if match_type == "BR" else ("🎯 LW Headshot" if match_type == "LW_HS" else "🐺 Lone Wolf"))
        bot_state.log(f"[MATCH TYPE] UID {uid} → {label}", "info", uid)
        return web.json_response({"status": "ok", "uid": uid, "match_type": match_type})
    except Exception as e:
        return web.json_response({"status": "error", "error": str(e)}, status=500)


async def handle_toggle_global(request: web.Request) -> web.Response:
    """সব আইডি ON/OFF করা — running=true হলে ম্যাচ শুরু, false হলে বন্ধ"""
    try:
        data = await request.json()
        running = bool(data.get("running", True))
        bot_state.global_running = running
        state_str = "চালু (ON)" if running else "বন্ধ (OFF)"
        bot_state.log(f"[GLOBAL] সব বট {state_str} করা হয়েছে", "success" if running else "warning")

        # If turning OFF, update all account statuses to PAUSED
        if not running:
            for uid_str in list(bot_state.accounts.keys()):
                if uid_str not in bot_state.deleted_uids:
                    status = bot_state.accounts[uid_str].get("status", "ONLINE")
                    if status not in ("OFFLINE", "ERROR", "CONNECTING"):
                        bot_state.accounts[uid_str]["status"] = "PAUSED"
        else:
            # Turning ON — reset PAUSED statuses to ONLINE
            for uid_str in list(bot_state.accounts.keys()):
                if uid_str not in bot_state.deleted_uids:
                    if bot_state.accounts[uid_str].get("status") == "PAUSED":
                        bot_state.accounts[uid_str]["status"] = "ONLINE"

        return web.json_response({"status": "ok", "running": running})
    except Exception as e:
        return web.json_response({"status": "error", "error": str(e)}, status=500)


async def handle_set_all_mode(request: web.Request) -> web.Response:
    """ড্যাশবোর্ডের সব আইডির match type একসাথে পরিবর্তন করা"""
    try:
        data = await request.json()
        mode = str(data.get("mode", "LONE_WOLF")).strip().upper()
        if mode not in ("BR", "LONE_WOLF", "LW_HS", "AUTO"):
            return web.json_response({"status": "error", "error": "Invalid mode. Use BR, LONE_WOLF, LW_HS or AUTO"}, status=400)

        changed = 0
        bot_state.global_mode = mode
        if mode == "AUTO":
            # ✅ AUTO: সব আইডির manually-forced match_type সরিয়ে দেওয়া
            # get_match_type() এর Level-based auto-logic আবার কাজ করবে
            for uid_str in list(bot_state.accounts.keys()):
                if uid_str not in bot_state.deleted_uids:
                    # match_types থেকে সরালে get_match_type() নিজেই level দেখে সিদ্ধান্ত নেবে
                    bot_state.match_types.pop(uid_str, None)
                    if uid_str in bot_state.accounts:
                        lvl = bot_state.get_account_level(uid_str)
                        auto_mt = "BR" if lvl == 2 else "LONE_WOLF"
                        bot_state.accounts[uid_str]["match_type"] = auto_mt
                    changed += 1
            label = "🔄 Auto Level Mode"
        else:
            for uid_str in list(bot_state.accounts.keys()):
                if uid_str not in bot_state.deleted_uids:
                    bot_state.set_match_type(uid_str, mode)
                    changed += 1
            label = "⚔ Battle Royale" if mode == "BR" else ("🎯 LW Headshot" if mode == "LW_HS" else "🐺 Lone Wolf")

        bot_state.log(f"[GLOBAL MODE] সব {changed}টি আইডি → {label}", "success")
        return web.json_response({"status": "ok", "mode": mode, "changed": changed})
    except Exception as e:
        return web.json_response({"status": "error", "error": str(e)}, status=500)


async def handle_set_parallel(request: web.Request) -> web.Response:
    """BR EVO — global parallel cap সেট (প্রতি আইডি একসাথে কতগুলো match, 1–10)"""
    try:
        data = await request.json()
        try:
            v = int(str(data.get("value", "")).strip())
        except (ValueError, TypeError):
            return web.json_response({"status": "error", "error": "value must be a number"}, status=400)
        if not 1 <= v <= 10:
            return web.json_response({"status": "error", "error": "value must be between 1 and 10"}, status=400)
        bot_state.br_evo_parallel = v
        bot_state._save_settings()
        bot_state.log(f"[PARALLEL] BR EVO — প্রতি আইডি সর্বোচ্চ {v}টি match একসাথে", "success")
        return web.json_response({"status": "ok", "br_evo_parallel": v})
    except Exception as e:
        return web.json_response({"status": "error", "error": str(e)}, status=500)


async def handle_set_mehedi_max(request: web.Request) -> web.Response:
    """🔥 SHAPPNO — per-account max concurrent UDP matches (1-50, default 10)"""
    try:
        data = await request.json()
        try:
            v = int(str(data.get("value", "")).strip())
        except (ValueError, TypeError):
            return web.json_response({"status": "error", "error": "value must be a number"}, status=400)
        if not 1 <= v <= 50:
            return web.json_response({"status": "error", "error": "value must be 1-50"}, status=400)
        bot_state.mehedi_max_match = v
        bot_state._save_settings()
        bot_state.log(f"[🔥 SHAPPNO] Max match per account set to {v}", "success")
        return web.json_response({"status": "ok", "mehedi_max_match": v})
    except Exception as e:
        return web.json_response({"status": "error", "error": str(e)}, status=500)


async def handle_set_account_parallel(request: web.Request) -> web.Response:
    """নির্দিষ্ট আইডির parallel cap সেট; value = 0 হলে override সরে global-এ ফেরে"""
    try:
        data = await request.json()
        uid = str(data.get("uid", "")).strip()
        if not uid:
            return web.json_response({"status": "error", "error": "uid missing"}, status=400)
        try:
            v = int(str(data.get("value", "")).strip())
        except (ValueError, TypeError):
            return web.json_response({"status": "error", "error": "value must be a number"}, status=400)
        if not 0 <= v <= 10:
            return web.json_response({"status": "error", "error": "value must be 0 (clear) or 1–10"}, status=400)
        if v == 0:
            bot_state.parallel_override.pop(uid, None)
        else:
            bot_state.parallel_override[uid] = v
        bot_state._save_settings()
        return web.json_response({"status": "ok", "uid": uid, "cap": bot_state.get_max_parallel(uid)})
    except Exception as e:
        return web.json_response({"status": "error", "error": str(e)}, status=500)


async def handle_set_exp_limit(request: web.Request) -> web.Response:
    """EXP লিমিট আপডেট করা — এই সীমা পার হলে আইডি অটো ডিলিট হবে"""
    try:
        data = await request.json()
        raw = data.get("exp_limit", None)
        if raw is None:
            return web.json_response({"status": "error", "error": "exp_limit missing"}, status=400)
        try:
            limit = int(str(raw).strip().replace(",", ""))
        except (ValueError, TypeError):
            return web.json_response({"status": "error", "error": "exp_limit must be a number"}, status=400)
        if limit < 0:
            return web.json_response({"status": "error", "error": "exp_limit cannot be negative"}, status=400)
        bot_state.exp_limit = limit
        bot_state._save_settings()  # ✅ FIX: redeploy-এর পরেও টিকে থাকবে
        msg = f"EXP লিমিট সেট: {limit:,}" if limit > 0 else "EXP লিমিট বন্ধ (0 = কোনো লিমিট নেই)"
        bot_state.log(f"[EXP LIMIT] {msg}", "success")
        return web.json_response({"status": "ok", "exp_limit": limit})
    except Exception as e:
        return web.json_response({"status": "error", "error": str(e)}, status=500)


async def handle_set_level_limit(request: web.Request) -> web.Response:
    """Level লিমিট সেট — আইডি এই level-এ পৌঁছালে dashboard থেকে সরে যাবে (0 = বন্ধ)"""
    try:
        data = await request.json()
        raw = data.get("level_limit", None)
        if raw is None:
            return web.json_response({"status": "error", "error": "level_limit missing"}, status=400)
        try:
            limit = int(str(raw).strip())
        except (ValueError, TypeError):
            return web.json_response({"status": "error", "error": "level_limit must be a number"}, status=400)
        if limit == 1 or limit < 0 or limit > 200:
            return web.json_response({"status": "error", "error": "Level লিমিট 0 (বন্ধ) অথবা 2 থেকে 200 এর মধ্যে দিন"}, status=400)
        bot_state.level_limit = limit
        bot_state._save_settings()  # ✅ FIX: redeploy-এর পরেও টিকে থাকবে
        msg = f"Level লিমিট সেট: Lv{limit}" if limit > 0 else "Level লিমিট বন্ধ (0 = কোনো লিমিট নেই)"
        bot_state.log(f"[LEVEL LIMIT] {msg}", "success")
        bot_state.enforce_level_limit()
        return web.json_response({"status": "ok", "level_limit": limit})
    except Exception as e:
        return web.json_response({"status": "error", "error": str(e)}, status=500)


async def handle_set_user_limit(request: web.Request) -> web.Response:
    """প্রতিটি User সর্বোচ্চ কয়টি আইডি যোগ করতে পারবে — শুধু Admin ঠিক করে (0 = সীমাহীন)"""
    try:
        data = await request.json()
        raw = data.get("user_add_limit", None)
        if raw is None:
            return web.json_response({"status": "error", "error": "user_add_limit missing"}, status=400)
        try:
            limit = int(str(raw).strip())
        except (ValueError, TypeError):
            return web.json_response({"status": "error", "error": "user_add_limit must be a number"}, status=400)
        if limit < 0 or limit > 100000:
            return web.json_response({"status": "error", "error": "user_add_limit must be 0 to 100000"}, status=400)
        bot_state.user_add_limit = limit
        bot_state._save_settings()
        msg = f"প্রতি User সর্বোচ্চ {limit}টি আইডি" if limit > 0 else "User ID লিমিট বন্ধ (0 = সীমাহীন)"
        bot_state.log(f"[USER LIMIT] {msg}", "success")
        return web.json_response({"status": "ok", "user_add_limit": limit})
    except Exception as e:
        return web.json_response({"status": "error", "error": str(e)}, status=500)


async def handle_set_auto_restart(request: web.Request) -> web.Response:
    """Auto-Restart সেটিং আপডেট — enabled/disabled + interval + break"""
    try:
        data = await request.json()
        enabled = bool(data.get("enabled", bot_state.auto_restart_enabled))
        interval_h = float(data.get("interval_hours", bot_state.auto_restart_interval_hours) or 1.5)
        break_m = int(data.get("break_minutes", bot_state.auto_restart_break_minutes) or 10)
        interval_h = max(0.5, min(24, interval_h))
        break_m = max(1, min(60, break_m))

        was_enabled = bot_state.auto_restart_enabled
        bot_state.auto_restart_enabled = enabled
        bot_state.auto_restart_interval_hours = interval_h
        bot_state.auto_restart_break_minutes = break_m
        bot_state._save_settings()

        if enabled and not was_enabled:
            # নতুন করে চালু হলে timer রিসেট করে task শুরু
            bot_state._auto_restart_phase = "running"
            bot_state._auto_restart_next_ts = time.time() + interval_h * 3600
            _start_auto_restart_task()
            bot_state.log(
                f"[AUTO-RESTART] চালু — প্রতি {interval_h}h পর {break_m}min বিরতি",
                "success"
            )
        elif not enabled and was_enabled:
            _stop_auto_restart_task()
            bot_state._auto_restart_phase = ""
            bot_state._auto_restart_next_ts = 0.0
            bot_state.log("[AUTO-RESTART] বন্ধ করা হয়েছে", "warning")
        elif enabled and was_enabled:
            # সেটিং আপডেট — task restart করে নতুন interval দিয়ে
            _stop_auto_restart_task()
            bot_state._auto_restart_phase = "running"
            bot_state._auto_restart_next_ts = time.time() + interval_h * 3600
            _start_auto_restart_task()
            bot_state.log(
                f"[AUTO-RESTART] আপডেট — প্রতি {interval_h}h পর {break_m}min বিরতি",
                "info"
            )

        return web.json_response({
            "status": "ok",
            "enabled": enabled,
            "interval_hours": interval_h,
            "break_minutes": break_m,
        })
    except Exception as e:
        return web.json_response({"status": "error", "error": str(e)}, status=500)


def _start_auto_restart_task():
    """Auto-restart background task শুরু করে"""
    _stop_auto_restart_task()
    try:
        loop = asyncio.get_running_loop()
        task = loop.create_task(_auto_restart_loop())
        bot_state._auto_restart_task = task
        _BG_TASKS.append(task)
    except RuntimeError:
        pass


def _stop_auto_restart_task():
    """Auto-restart background task বন্ধ করে"""
    task = bot_state._auto_restart_task
    if task and not task.done():
        task.cancel()
    bot_state._auto_restart_task = None


async def _auto_restart_loop():
    """
    Auto-Restart মূল loop:
    1. interval_hours পর্যন্ত অপেক্ষা
    2. সব account OFFLINE → ১০ মিনিট বিরতি
    3. global_running=True → সব reconnect → stats reset
    4. আবার শুরু
    """
    try:
        while bot_state.auto_restart_enabled:
            # ─── Phase 1: RUNNING ─── interval শেষ হওয়ার অপেক্ষা
            bot_state._auto_restart_phase = "running"
            wait_sec = bot_state._auto_restart_next_ts - time.time()
            if wait_sec > 0:
                await asyncio.sleep(wait_sec)
            if not bot_state.auto_restart_enabled:
                break

            # ─── Phase 2: BREAK শুরু ─── সব account offline
            break_min = bot_state.auto_restart_break_minutes
            bot_state._auto_restart_phase = "break"
            bot_state._auto_restart_next_ts = time.time() + break_min * 60
            bot_state.log(
                f"[AUTO-RESTART] 🔴 সব account offline করা হচ্ছে — {break_min} মিনিট বিরতি",
                "warning"
            )

            # ✅ global_running বন্ধ → সব account game থেকে LOGOUT
            bot_state.global_running = False
            for uid_str in list(bot_state.accounts.keys()):
                if uid_str not in bot_state.deleted_uids:
                    status_now = bot_state.accounts[uid_str].get("status", "ONLINE")
                    if status_now not in ("OFFLINE", "ERROR"):
                        bot_state.accounts[uid_str]["status"] = "OFFLINE"
                        bot_state.accounts[uid_str]["last_updated"] = time.strftime("%H:%M:%S")
                        # ✅ JWT token clear → fresh login forced
                        bot_state.accounts[uid_str]["token"] = ""
                        bot_state.accounts[uid_str]["jwt"] = ""

            # ✅ on_reload_accounts call → app.py সব account disconnect করবে
            if "on_reload_accounts" in bot_state.refresh_callbacks:
                try:
                    await asyncio.sleep(2)  # disconnect হতে 2 সেকেন্ড দাও
                    bot_state.log("[AUTO-RESTART] 🔴 Game থেকে সব ID logout হয়েছে", "warning")
                except Exception as e:
                    bot_state.log(f"[AUTO-RESTART] Logout error: {e}", "error")

            # ─── Phase 3: বিরতি শেষে reconnect ───
            await asyncio.sleep(break_min * 60)
            if not bot_state.auto_restart_enabled:
                break

            bot_state._auto_restart_phase = "reconnecting"
            bot_state.log(
                "[AUTO-RESTART] 🟢 বিরতি শেষ — সব ID fresh login হচ্ছে",
                "success"
            )

            # ─── Stats রিসেট ───
            bot_state.total_matches = 0
            bot_state.total_gained_exp = 0
            bot_state.start_time = time.time()
            for uid_str in list(bot_state.accounts.keys()):
                if uid_str not in bot_state.deleted_uids:
                    acc = bot_state.accounts[uid_str]
                    cur_exp = acc.get("current_exp") or acc.get("exp") or acc.get("initial_exp") or 0
                    acc["initial_exp"] = cur_exp
                    acc["gained_exp"] = 0
                    acc["matches_played"] = 0
                    acc["status"] = "CONNECTING"
                    acc["last_updated"] = time.strftime("%H:%M:%S")

            # ✅ global_running চালু → on_reload_accounts দিয়ে fresh re-login
            bot_state.global_running = True
            if "on_reload_accounts" in bot_state.refresh_callbacks:
                try:
                    await asyncio.ensure_future(
                        bot_state.refresh_callbacks["on_reload_accounts"]()
                    )
                    bot_state.log("[AUTO-RESTART] ✅ সব ID game-এ fresh login হয়েছে", "success")
                except Exception as e:
                    bot_state.log(f"[AUTO-RESTART] Re-login error: {e}", "error")

            # ─── Phase 4: পরবর্তী cycle সেট ───
            interval_h = bot_state.auto_restart_interval_hours
            bot_state._auto_restart_phase = "running"
            bot_state._auto_restart_next_ts = time.time() + interval_h * 3600
            bot_state.log(
                f"[AUTO-RESTART] ✅ পরবর্তী restart {interval_h} ঘন্টা পর",
                "info"
            )

    except asyncio.CancelledError:
        pass
    except Exception as e:
        bot_state.log(f"[AUTO-RESTART ERROR] {e}", "error")
    finally:
        # ✅ SAFETY: break phase-এ cancel হলে global_running পুনরুদ্ধার করা
        # যেন বট চিরতরে offline না থাকে
        if bot_state._auto_restart_phase == "break":
            bot_state.global_running = True
            for uid_str in list(bot_state.accounts.keys()):
                if uid_str not in bot_state.deleted_uids:
                    if bot_state.accounts[uid_str].get("status") == "OFFLINE":
                        bot_state.accounts[uid_str]["status"] = "CONNECTING"
            bot_state.log("[AUTO-RESTART] Task বন্ধ — সব account পুনরায় চালু", "info")
        bot_state._auto_restart_phase = ""
        if bot_state._auto_restart_task is not None:
            bot_state._auto_restart_task = None


async def handle_clear_logs(request: web.Request) -> web.Response:
    """Activity Log পরিষ্কার করা"""
    bot_state.logs.clear()
    return web.json_response({"status": "ok"})


async def start_web_dashboard(host: str = "0.0.0.0", port: int = 5000):
    try:
        bot_state.preload_pending()
    except Exception:
        pass
    app = web.Application(middlewares=[compress_middleware, auth_middleware])
    app.router.add_get("/login", handle_login_page)
    app.router.add_post("/api/login", handle_login)
    app.router.add_post("/api/logout", handle_logout)
    app.router.add_get("/logo.jpg", handle_logo)
    app.router.add_get("/healthz", handle_healthz)
    app.router.add_get("/", handle_index)
    app.router.add_get("/api/stats", handle_get_stats)
    app.router.add_post("/api/account/add", handle_add_account)
    app.router.add_post("/api/account/bulk-add", handle_bulk_add_account)
    app.router.add_post("/api/account/delete", handle_delete_account)
    app.router.add_post("/api/accounts/all-delete", handle_all_delete_accounts)
    app.router.add_post("/api/account/refresh", handle_refresh_account)
    app.router.add_post("/api/accounts/reload", handle_reload_accounts)
    app.router.add_post("/api/accounts/restore-deleted", handle_restore_deleted)
    app.router.add_post("/api/account/match-type", handle_set_match_type)
    app.router.add_post("/api/bot/toggle", handle_toggle_global)
    app.router.add_post("/api/accounts/set-all-mode", handle_set_all_mode)
    app.router.add_post("/api/settings/exp-limit", handle_set_exp_limit)
    app.router.add_post("/api/settings/parallel", handle_set_parallel)
    app.router.add_post("/api/settings/mehedi-max", handle_set_mehedi_max)
    app.router.add_post("/api/account/parallel", handle_set_account_parallel)
    app.router.add_post("/api/settings/level-limit", handle_set_level_limit)
    app.router.add_post("/api/settings/user-limit", handle_set_user_limit)
    app.router.add_post("/api/settings/auto-restart", handle_set_auto_restart)
    app.router.add_post("/api/logs/clear", handle_clear_logs)

    runner = web.AppRunner(app, access_log=None)   # প্রতি request-এর log print বন্ধ — CPU/log flood কমে
    await runner.setup()
    site = web.TCPSite(runner, host, port, backlog=1024)
    await site.start()
    _BG_TASKS.append(asyncio.ensure_future(_loop_lag_monitor()))
    _BG_TASKS.append(asyncio.ensure_future(_snapshot_refresher()))
    # ✅ AUTO-RESTART: settings লোড হয়ে থাকলে সাথে সাথে শুরু
    if bot_state.auto_restart_enabled:
        bot_state._auto_restart_phase = "running"
        # redeploy-এর পর interval থেকে নতুন করে শুরু
        bot_state._auto_restart_next_ts = time.time() + bot_state.auto_restart_interval_hours * 3600
        _start_auto_restart_task()
        bot_state.log(
            f"[AUTO-RESTART] বট চালু — প্রতি {bot_state.auto_restart_interval_hours}h পর "
            f"{bot_state.auto_restart_break_minutes}min বিরতি দিয়ে restart হবে",
            "info"
        )
    print(f"\033[92m[+] Web Dashboard running on http://localhost:{port}\033[0m")

import json, sys, threading, webbrowser, ctypes, ctypes.wintypes
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

try:
    import requests
except ImportError:
    print("pip install requests"); sys.exit(1)
try:
    import tkinter as tk
    from tkinter import filedialog
except ImportError:
    print("tkinter not found — install Python with tkinter support"); sys.exit(1)

def _beep(freq, ms):
    try: ctypes.windll.kernel32.Beep(freq, ms)
    except Exception: pass

def play_ready():
    threading.Thread(target=lambda:(_beep(880,100),_beep(1100,160)),daemon=True).start()

def play_error():
    threading.Thread(target=lambda:_beep(380,200),daemon=True).start()

GSI_PORT = 3000
OPENDOTA  = "https://api.opendota.com/api"
DOTA_CFG_PATHS = [
    Path(r"C:/Program Files (x86)/Steam/steamapps/common/dota 2 beta/game/dota/cfg"),
    Path(r"C:/Program Files/Steam/steamapps/common/dota 2 beta/game/dota/cfg"),
    Path.home() / ".steam/steam/steamapps/common/dota 2 beta/game/dota/cfg",
]
GSI_CFG = (
    '"dota2-gsi Configuration"\n{\n'
    f'    "uri" "http://localhost:{GSI_PORT}/"\n'
    '    "timeout" "5.0" "buffer" "0.1" "throttle" "0.5" "heartbeat" "30.0"\n'
    '    "data" { "provider" "1" "map" "1" "player" "1" "draft" "1" }\n'
    '    "auth" { "token" "truesight_secret" }\n}\n'
)

VERSION = "1.0.0"
GITHUB  = "https://github.com/VaKaVo/truesight"

_RE={0:"Uncalibrated",11:"Herald I",12:"Herald II",13:"Herald III",14:"Herald IV",15:"Herald V",
     21:"Guardian I",22:"Guardian II",23:"Guardian III",24:"Guardian IV",25:"Guardian V",
     31:"Crusader I",32:"Crusader II",33:"Crusader III",34:"Crusader IV",35:"Crusader V",
     41:"Archon I",42:"Archon II",43:"Archon III",44:"Archon IV",45:"Archon V",
     51:"Legend I",52:"Legend II",53:"Legend III",54:"Legend IV",55:"Legend V",
     61:"Ancient I",62:"Ancient II",63:"Ancient III",64:"Ancient IV",65:"Ancient V",
     70:"Divine",71:"Divine I",72:"Divine II",73:"Divine III",74:"Divine IV",75:"Divine V",
     80:"Immortal"}
_RR={0:"Некалиброван",11:"Страж I",12:"Страж II",13:"Страж III",14:"Страж IV",15:"Страж V",
     21:"Рыцарь I",22:"Рыцарь II",23:"Рыцарь III",24:"Рыцарь IV",25:"Рыцарь V",
     31:"Герой I",32:"Герой II",33:"Герой III",34:"Герой IV",35:"Герой V",
     41:"Легенда I",42:"Легенда II",43:"Легенда III",44:"Легенда IV",45:"Легенда V",
     51:"Властелин I",52:"Властелин II",53:"Властелин III",54:"Властелин IV",55:"Властелин V",
     61:"Древний I",62:"Древний II",63:"Древний III",64:"Древний IV",65:"Древний V",
     70:"Бож.",71:"Бож. I",72:"Бож. II",73:"Бож. III",74:"Бож. IV",75:"Бож. V",
     80:"Бессмертный"}
_RC={0:"#888",1:"#6ea4b0",2:"#6ea4b0",3:"#6ea4b0",
     4:"#4fc3f7",5:"#4fc3f7",6:"#66bb6a",7:"#aed581",8:"#ff7043"}

S={
"en":{"title":"🔮 TrueSight","ph":"Steam ID or profile URL...","find":"Find",
      "all":"All","toxic":"⚠ Toxic","good":"★ Good","ok":"OK",
      "wait":"Waiting for match...\n\nOpen Dota 2 and enter a lobby.\nOr enter a Steam ID above.",
      "load":"Loading…","none":"No players in this category",
      "bad":"Invalid Steam ID.\nEnter 64-bit ID or profile URL.",
      "done":"● Done","ws":"● Waiting…","ls":"● Loading…","match":"● Match #",
      "hint":"Ins — show / hide","stitle":"⚙  Settings","th":"Theme","la":"Language",
      "op":"Window opacity","prv":"private","cp":"PLAYER / RANK","cr":"BEHAV.  WR","bh":"Behav.",
      "about_name":"TrueSight — Dota 2 Overlay",
      "about_sub":"Real-time lobby stats: rank, WR, behaviour score, top heroes",
      "about_data":"Data source: OpenDota API (free, no key required)",
      "about_hotkey":"Ins — toggle overlay visibility (works in-game)",
      "about_ver":"Version","about_link":"GitHub"},
"ru":{"title":"🔮 TrueSight","ph":"Steam ID или ссылка на профиль…","find":"Найти",
      "all":"Все","toxic":"⚠ Токсики","good":"★ Хорошие","ok":"OK",
      "wait":"Ожидание матча…\n\nОткрой Dota 2 и войди в лобби.\nИли введи Steam ID выше.",
      "load":"Загрузка…","none":"Нет игроков в этой категории",
      "bad":"Неверный Steam ID.\nВведи 64-bit ID или ссылку на профиль.",
      "done":"● Готово","ws":"● Ожидание…","ls":"● Загружаю…","match":"● Матч #",
      "hint":"Ins — скрыть / показать","stitle":"⚙  Настройки","th":"Тема","la":"Язык",
      "op":"Прозрачность","prv":"скрыт","cp":"ИГРОК / МЕДАЛЬ","cr":"ПОРЯД.  WR","bh":"Поряд.",
      "about_name":"TrueSight — Оверлей Dota 2",
      "about_sub":"Статистика в лобби: медаль, WR, порядочность, герои",
      "about_data":"Данные: OpenDota API (бесплатно, без ключа)",
      "about_hotkey":"Ins — показать/скрыть оверлей (работает в игре)",
      "about_ver":"Version","about_link":"GitHub"},
}

TH={
"Dark":    {"bg":"#0f1117","card":"#1a1d27","row":"#1e2130","row2":"#161924",
            "acc":"#e84949","fg":"#e0e0e0","mut":"#6c7086","brd":"#2a2d3e",
            "grn":"#4caf50","yel":"#ffc107","red":"#f44336","bar":"#0a0c12"},
"Light":   {"bg":"#f0f2f8","card":"#ffffff","row":"#ffffff","row2":"#eef0f8",
            "acc":"#c0392b","fg":"#1a1a2e","mut":"#7f8c8d","brd":"#dde1f0",
            "grn":"#27ae60","yel":"#d68910","red":"#e74c3c","bar":"#dde1f0"},
"Midnight":{"bg":"#0d0221","card":"#150535","row":"#1a0840","row2":"#110328",
            "acc":"#9b59b6","fg":"#e8d5ff","mut":"#8e6dbf","brd":"#2d1b4e",
            "grn":"#2ecc71","yel":"#f1c40f","red":"#e74c3c","bar":"#080114"},
"Forest":  {"bg":"#0d1f0d","card":"#142814","row":"#1a321a","row2":"#112211",
            "acc":"#2ecc71","fg":"#d5ffe0","mut":"#6dbf7a","brd":"#1e4020",
            "grn":"#27ae60","yel":"#f1c40f","red":"#e74c3c","bar":"#080f08"},
}

CFG=Path.home()/".truesight8.json"
def load_cfg():
    try:
        if CFG.exists(): return json.loads(CFG.read_text())
    except Exception: pass
    return {"theme":"Dark","opacity":0.92,"geo":"460x580+120+80","lang":"en"}
def save_cfg(c):
    try: CFG.write_text(json.dumps(c))
    except Exception: pass

def _h2r(h):
    h=h.lstrip("#"); return int(h[0:2],16),int(h[2:4],16),int(h[4:6],16)
def _r2h(r,g,b): return "#{:02x}{:02x}{:02x}".format(int(r),int(g),int(b))
def lerp(a,b,t):
    ar,ag,ab=_h2r(a); br,bg,bb=_h2r(b)
    return _r2h(ar+(br-ar)*t,ag+(bg-ag)*t,ab+(bb-ab)*t)

_cache={}; _pool=ThreadPoolExecutor(max_workers=8)

def get_player(sid64,lang="en"):
    sid64=int(sid64)
    if sid64 in _cache: return _cache[sid64]
    rm=_RE if lang=="en" else _RR
    aid=sid64-76561197960265728
    r={"name":f"Player {aid}","account_id":aid,"steam64":sid64,
       "behavior":None,"winrate":None,"wins":None,"losses":None,
       "rank_tier":0,"rank_name":"—","rank_color":"#888","top_heroes":[],
       "url":f"https://www.opendota.com/players/{aid}","is_private":False}
    try:
        d=requests.get(f"{OPENDOTA}/players/{aid}",timeout=8).json()
        r["name"]=d.get("profile",{}).get("personaname",r["name"])
        r["behavior"]=d.get("behavior_score")
        t=d.get("rank_tier") or 0
        r["rank_tier"]=t; r["rank_name"]=rm.get(t,f"#{t}"); r["rank_color"]=_RC.get(t//10,"#888")
        wl=requests.get(f"{OPENDOTA}/players/{aid}/wl",timeout=8).json()
        w,l=wl.get("win",0),wl.get("lose",0)
        r["wins"],r["losses"]=w,l
        r["winrate"]=round(w/(w+l)*100,1) if w+l else None
        if not w+l: r["is_private"]=True
        hh=requests.get(f"{OPENDOTA}/players/{aid}/heroes?limit=3",timeout=8).json()[:3]
        r["top_heroes"]=[{"id":h.get("hero_id"),
                          "wr":round(h.get("win",0)/max(h.get("games",1),1)*100)}
                         for h in hh]
    except Exception: pass
    _cache[sid64]=r; return r

class GState:
    def __init__(self): self.mid=None; self.players=[]; self.lock=threading.Lock()
gsi=GState()

class GSIH(BaseHTTPRequestHandler):
    def do_POST(self):
        body=self.rfile.read(int(self.headers.get("Content-Length",0)))
        self.send_response(200); self.end_headers()
        try:
            data=json.loads(body)
            with gsi.lock:
                mid=data.get("map",{}).get("matchid")
                if mid and mid!=gsi.mid:
                    gsi.mid=mid
                    threading.Thread(target=self._load,args=(mid,),daemon=True).start()
        except Exception: pass
    def _load(self,mid):
        try:
            ps=requests.get(f"{OPENDOTA}/matches/{mid}",timeout=10).json().get("players",[])
            with gsi.lock:
                gsi.players=[p["account_id"] for p in ps if p.get("account_id")]
        except Exception: pass
    def log_message(self,*a): pass

def start_gsi():
    for p in DOTA_CFG_PATHS:
        if p.exists():
            try: (p/"gamestate_integration_truesight.cfg").write_text(GSI_CFG)
            except Exception: pass
            break
    threading.Thread(target=HTTPServer(("",GSI_PORT),GSIH).serve_forever,daemon=True).start()

_VKI   = 0x2D          
_WMH   = 0x0312        
_HID   = 42            

class HotkeyThread(threading.Thread):
    def __init__(self, callback):
        super().__init__(daemon=True)
        self.callback = callback
        self._stop = threading.Event()

    def run(self):
        ok = ctypes.windll.user32.RegisterHotKey(None, _HID, 0, _VKI)
        if not ok:
            print("[TrueSight] Could not register Insert hotkey "
                  "(maybe another app uses it). Try closing other overlays.")
            return

        msg = ctypes.wintypes.MSG()
        while not self._stop.is_set():
            ret = ctypes.windll.user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if ret == 0 or ret == -1:
                break
            if msg.message == _WMH and msg.wParam == _HID:
                try:
                    self.callback()
                except Exception:
                    pass

        ctypes.windll.user32.UnregisterHotKey(None, _HID)

    def stop(self):
        self._stop.set()
        ctypes.windll.user32.PostThreadMessageW(self.ident, 0x0012, 0, 0)

class TrueSight:
    def __init__(self):
        self.cfg=load_cfg()
        self.T=TH[self.cfg.get("theme","Dark")]
        self.lang=self.cfg.get("lang","en")
        self.s=S[self.lang]
        self.hidden=False
        self._dx=self._dy=0
        self.players=[]; self.filt="all"
        self._ph_on=True
        self._efocused=False
        self._tw=[]
        self._settings=None
        self._last_mid=None
        self._hk_thread=None

        self.root=tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost",True)
        self.root.attributes("-alpha",0.0)
        self.root.configure(bg=self.T["bg"])
        self.root.geometry(self.cfg.get("geo","460x580+120+80"))
        self.root.minsize(380,440)

        try:
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                ctypes.windll.user32.GetParent(self.root.winfo_id()),
                33,ctypes.byref(ctypes.c_int(2)),4)
        except Exception: pass

        self._build()
        self._start_hotkey()
        self._fade_in()
        self._poll()

    def _start_hotkey(self):
        def _cb():
            self.root.after(0, self._toggle)
        self._hk_thread = HotkeyThread(_cb)
        self._hk_thread.start()

    def _r(self,w,**kv): self._tw.append((w,kv)); return w

    def _apply_T(self,T):
        self.root.configure(bg=T["bg"])
        self.main.configure(bg=T["bg"])
        for w,kv in self._tw:
            try: w.config(**{a:T[k] for a,k in kv.items()})
            except Exception: pass

    def _crossfade(self,old,new,n=18,i=0):
        t=i/n
        try:
            self.root.configure(bg=lerp(old["bg"],new["bg"],t))
            self.main.configure(bg=lerp(old["bg"],new["bg"],t))
        except Exception: pass
        for w,kv in self._tw:
            try: w.config(**{a:lerp(old[k],new[k],t) for a,k in kv.items()})
            except Exception: pass
        if i<n: self.root.after(14,lambda:self._crossfade(old,new,n,i+1))
        else:
            self.T=new; self._apply_T(new)
            self._refresh_fbtns()
            if self.players: self._render(self.players)
            else: self._placeholder(self.s["wait"])

    def _fade_in(self,a=None):
        if a is None: a=float(self.root.attributes("-alpha"))
        t=float(self.cfg.get("opacity",0.92))
        if a<t:
            a=min(a+0.07,t); self.root.attributes("-alpha",a)
            self.root.after(16,lambda:self._fade_in(a))

    def _fade_out(self,a=None,cb=None):
        if a is None: a=float(self.root.attributes("-alpha"))
        if a>0:
            a=max(a-0.07,0); self.root.attributes("-alpha",a)
            self.root.after(16,lambda:self._fade_out(a,cb))
        elif cb: cb()

    def _build(self):
        T=self.T; self._tw.clear()
        self.root.configure(bg=T["bg"])
        self.main=tk.Frame(self.root,bg=T["bg"])
        self.main.place(x=0,y=0,relwidth=1,relheight=1)
        self._mk_titlebar(); self._mk_search(); self._mk_filters()
        self._mk_colhdr(); self._mk_list(); self._mk_statusbar()
        self._placeholder(self.s["wait"])

    def _rebuild_main(self):
        for w in self.main.winfo_children(): w.destroy()
        self._tw.clear()
        T=self.T
        self.root.configure(bg=T["bg"]); self.main.configure(bg=T["bg"])
        self._mk_titlebar(); self._mk_search(); self._mk_filters()
        self._mk_colhdr(); self._mk_list(); self._mk_statusbar()
        if self.players: self._render(self.players)
        else: self._placeholder(self.s["wait"])

    def _mk_titlebar(self):
        T=self.T; s=self.s
        tb=tk.Frame(self.main,bg=T["bar"],height=38)
        tb.pack(fill="x"); tb.pack_propagate(False); self._r(tb,bg="bar")
        lbl=tk.Label(tb,text=s["title"],fg=T["acc"],bg=T["bar"],font=("Segoe UI",11,"bold"))
        lbl.pack(side="left",padx=12); self._r(lbl,fg="acc",bg="bar")
        for txt,cmd,hov in [("✕",self._close,"#c0392b"),
                             ("—",self._minimize,T["brd"]),
                             ("⚙",self._open_settings,T["brd"])]:
            b=tk.Button(tb,text=txt,bg=T["bar"],fg=T["mut"],
                        activebackground=hov,activeforeground="white",
                        relief="flat",bd=0,font=("Segoe UI",12),cursor="hand2",padx=7,command=cmd)
            b.pack(side="right",pady=2); self._r(b,bg="bar",fg="mut")
        for ev,fn in [("<ButtonPress-1>",self._ds),("<B1-Motion>",self._dm),
                      ("<ButtonRelease-1>",self._de)]:
            tb.bind(ev,fn); lbl.bind(ev,fn)

    def _mk_search(self):
        T=self.T; s=self.s
        sf=tk.Frame(self.main,bg=T["bg"],padx=10,pady=6)
        sf.pack(fill="x"); self._r(sf,bg="bg")
        self.evar=tk.StringVar()
        self.entry=tk.Entry(sf,textvariable=self.evar,bg=T["card"],fg=T["mut"],
                            insertbackground=T["fg"],relief="flat",font=("Segoe UI",11),
                            bd=0,highlightthickness=1,
                            highlightcolor=T["acc"],highlightbackground=T["brd"])
        self.entry.pack(side="left",fill="x",expand=True,ipady=7,padx=(0,6))
        self._r(self.entry,bg="card",insertbackground="fg",
                highlightbackground="brd",highlightcolor="acc")
        self._ph=s["ph"]; self._ph_on=True
        self.entry.insert(0,self._ph); self.entry.config(fg=T["mut"])
        self.entry.bind("<FocusIn>",  self._ein)
        self.entry.bind("<FocusOut>", self._eout)
        self.entry.bind("<Return>",   lambda e:self._search())
        self.entry.bind("<<Paste>>",  self._epaste)
        self.entry.bind("<Control-v>",self._epaste)
        fb=tk.Button(sf,text=s["find"],bg=T["acc"],fg="white",relief="flat",
                     font=("Segoe UI",10,"bold"),padx=10,pady=5,bd=0,cursor="hand2",
                     activebackground=T["card"],activeforeground=T["fg"],command=self._search)
        fb.pack(side="right"); self._r(fb,bg="acc",activebackground="card",activeforeground="fg")

    def _ein(self,e):
        self._efocused=True
        if self._ph_on:
            self.entry.delete(0,"end"); self.entry.config(fg=self.T["fg"]); self._ph_on=False
    def _eout(self,e):
        self._efocused=False
        if not self.entry.get().strip():
            self._ph_on=True; self.entry.delete(0,"end")
            self.entry.insert(0,self._ph); self.entry.config(fg=self.T["mut"])
    def _epaste(self,e):
        if self._ph_on:
            self.entry.delete(0,"end"); self.entry.config(fg=self.T["fg"]); self._ph_on=False

    def _mk_filters(self):
        T=self.T; s=self.s
        ff=tk.Frame(self.main,bg=T["bg"],padx=10,pady=2)
        ff.pack(fill="x"); self._r(ff,bg="bg")
        self.fbtns={}
        for k,lbl in [("all",s["all"]),("toxic",s["toxic"]),("good",s["good"]),("ok",s["ok"])]:
            b=tk.Button(ff,text=lbl,relief="flat",bd=0,cursor="hand2",
                        font=("Segoe UI",9),padx=8,pady=3,command=lambda x=k:self._setf(x))
            b.pack(side="left",padx=2); self.fbtns[k]=b
        self._refresh_fbtns()

    def _refresh_fbtns(self):
        T=self.T
        for k,b in self.fbtns.items():
            if k==self.filt:
                b.config(bg=T["acc"],fg="white",activebackground=T["acc"],activeforeground="white")
            else:
                b.config(bg=T["card"],fg=T["mut"],activebackground=T["brd"],activeforeground=T["fg"])

    def _setf(self,k): self.filt=k; self._refresh_fbtns(); self._render(self.players)

    def _mk_colhdr(self):
        T=self.T; s=self.s
        self._r(tk.Frame(self.main,bg=T["brd"],height=1),bg="brd").pack(fill="x",padx=10)
        ch=tk.Frame(self.main,bg=T["bg"],padx=12,pady=3)
        ch.pack(fill="x"); self._r(ch,bg="bg")
        self._r(tk.Label(ch,text=s["cp"],fg=T["mut"],bg=T["bg"],font=("Segoe UI",8)),
                fg="mut",bg="bg").pack(side="left")
        self._r(tk.Label(ch,text=s["cr"],fg=T["mut"],bg=T["bg"],font=("Segoe UI",8)),
                fg="mut",bg="bg").pack(side="right")

    def _mk_list(self):
        T=self.T
        c=tk.Frame(self.main,bg=T["bg"]); c.pack(fill="both",expand=True,padx=6,pady=2)
        self._r(c,bg="bg")
        self.lcv=tk.Canvas(c,bg=T["bg"],highlightthickness=0); self._r(self.lcv,bg="bg")
        sb=tk.Scrollbar(c,orient="vertical",command=self.lcv.yview)
        self.lf=tk.Frame(self.lcv,bg=T["bg"]); self._r(self.lf,bg="bg")
        self.lf.bind("<Configure>",lambda e:self.lcv.configure(scrollregion=self.lcv.bbox("all")))
        self._lwin=self.lcv.create_window((0,0),window=self.lf,anchor="nw")
        self.lcv.configure(yscrollcommand=sb.set)
        self.lcv.pack(side="left",fill="both",expand=True)
        sb.pack(side="right",fill="y")
        self.lcv.bind("<Configure>",lambda e:self.lcv.itemconfig(self._lwin,width=e.width))
        self.lcv.bind_all("<MouseWheel>",lambda e:self.lcv.yview_scroll(-1*(e.delta//120),"units"))

    def _mk_statusbar(self):
        T=self.T; s=self.s
        self._r(tk.Frame(self.main,bg=T["brd"],height=1),bg="brd").pack(fill="x",padx=10)
        sb=tk.Frame(self.main,bg=T["bar"],pady=4); sb.pack(fill="x"); self._r(sb,bg="bar")
        self.stlbl=tk.Label(sb,text=s["ws"],fg=T["mut"],bg=T["bar"],font=("Segoe UI",9))
        self.stlbl.pack(side="left",padx=10); self._r(self.stlbl,fg="mut",bg="bar")
        self._r(tk.Label(sb,text=s["hint"],fg=T["mut"],bg=T["bar"],font=("Segoe UI",8)),
                fg="mut",bg="bar").pack(side="right",padx=10)

    def _ds(self,e): self._dx,self._dy=e.x_root,e.y_root
    def _dm(self,e):
        self.root.geometry(f"+{self.root.winfo_x()+(e.x_root-self._dx)}"
                           f"+{self.root.winfo_y()+(e.y_root-self._dy)}")
        self._dx,self._dy=e.x_root,e.y_root
    def _de(self,e): self.cfg["geo"]=self.root.geometry(); save_cfg(self.cfg)

    def _toggle(self):
        if self.hidden:
            self.hidden=False; self.root.attributes("-topmost",True); self._fade_in()
        else:
            self.hidden=True; self._fade_out(cb=lambda:self.root.attributes("-topmost",False))

    def _minimize(self):
        self.root.overrideredirect(False); self.root.iconify()
        self.root.after(300,lambda:self.root.overrideredirect(True))

    def _close(self):
        self.cfg["geo"]=self.root.geometry(); save_cfg(self.cfg)
        if self._hk_thread: self._hk_thread.stop()
        self.root.destroy()

    def _open_settings(self):
        if self._settings and self._settings.winfo_exists():
            self._settings.lift(); return
        T=self.T; s=self.s
        win=tk.Toplevel(self.root)
        win.overrideredirect(True); win.attributes("-topmost",True)
        win.configure(bg=T["bg"]); self._settings=win
        try:
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                ctypes.windll.user32.GetParent(win.winfo_id()),
                33,ctypes.byref(ctypes.c_int(2)),4)
        except Exception: pass
        mx,my=self.root.winfo_x(),self.root.winfo_y()
        mw,mh=self.root.winfo_width(),self.root.winfo_height()
        win.geometry(f"340x460+{mx+(mw-340)//2}+{my+(mh-460)//2}")
        win.grab_set()

        sw=[]; sr=lambda w,**kv:(sw.append((w,kv)),w)[1]
        def sa(T):
            win.configure(bg=T["bg"])
            for w,kv in sw:
                try: w.config(**{a:T[k] for a,k in kv.items()})
                except Exception: pass
        def scf(o,n,steps=18,i=0):
            t=i/steps
            try: win.configure(bg=lerp(o["bg"],n["bg"],t))
            except Exception: pass
            for w,kv in sw:
                try: w.config(**{a:lerp(o[k],n[k],t) for a,k in kv.items()})
                except Exception: pass
            if i<steps: win.after(14,lambda:scf(o,n,steps,i+1))
            else: sa(n)

        hdr=tk.Frame(win,bg=T["bar"],height=38); hdr.pack(fill="x"); hdr.pack_propagate(False)
        sr(hdr,bg="bar")
        htl=tk.Label(hdr,text=s["stitle"],fg=T["acc"],bg=T["bar"],font=("Segoe UI",10,"bold"))
        htl.pack(side="left",padx=12,pady=8); sr(htl,fg="acc",bg="bar")
        xb=tk.Button(hdr,text="✕",bg=T["bar"],fg=T["mut"],relief="flat",bd=0,
                     font=("Segoe UI",11),cursor="hand2",
                     activebackground="#c0392b",activeforeground="white",command=win.destroy)
        xb.pack(side="right",padx=8,pady=4); sr(xb,bg="bar",fg="mut")
        _d=[0,0]
        def sd(e): _d[0]=e.x_root; _d[1]=e.y_root
        def sm(e):
            win.geometry(f"+{win.winfo_x()+(e.x_root-_d[0])}+{win.winfo_y()+(e.y_root-_d[1])}")
            _d[0]=e.x_root; _d[1]=e.y_root
        hdr.bind("<ButtonPress-1>",sd); hdr.bind("<B1-Motion>",sm)
        htl.bind("<ButtonPress-1>",sd); htl.bind("<B1-Motion>",sm)

        sc=tk.Canvas(win,bg=T["bg"],highlightthickness=0); sc.pack(fill="both",expand=True)
        sr(sc,bg="bg")
        inn=tk.Frame(sc,bg=T["bg"]); sr(inn,bg="bg")
        sc.create_window((0,0),window=inn,anchor="nw",width=340)
        inn.bind("<Configure>",lambda e:sc.configure(scrollregion=sc.bbox("all")))
        sc.bind_all("<MouseWheel>",lambda e:sc.yview_scroll(-1*(e.delta//120),"units"))

        def card(title):
            c=tk.Frame(inn,bg=T["card"],highlightthickness=1,highlightbackground=T["brd"])
            c.pack(fill="x",padx=10,pady=4); sr(c,bg="card",highlightbackground="brd")
            tk.Label(c,text=title.upper(),fg=T["mut"],bg=T["card"],
                     font=("Segoe UI",7,"bold")).pack(anchor="w",padx=10,pady=(8,2))
            return c

        tc=card(s["th"]); tv=tk.StringVar(value=self.cfg.get("theme","Dark"))
        tf=tk.Frame(tc,bg=T["card"]); tf.pack(fill="x",padx=10,pady=(0,8)); sr(tf,bg="card")
        def on_th(n):
            if n==self.cfg.get("theme"): return
            old=self.T; self.cfg["theme"]=n; save_cfg(self.cfg); new=TH[n]
            self._crossfade(old,new); scf(old,new)
        for n in TH:
            rb=tk.Radiobutton(tf,text=n,variable=tv,value=n,fg=T["fg"],bg=T["card"],
                              selectcolor=T["card"],activebackground=T["card"],
                              activeforeground=T["acc"],font=("Segoe UI",9),cursor="hand2",
                              command=lambda x=n:on_th(x))
            rb.pack(side="left",padx=5)
            sr(rb,fg="fg",bg="card",selectcolor="card",
               activebackground="card",activeforeground="acc")

        lc=card(s["la"]); lv=tk.StringVar(value=self.lang)
        lf2=tk.Frame(lc,bg=T["card"]); lf2.pack(fill="x",padx=10,pady=(0,8)); sr(lf2,bg="card")
        def on_la(c):
            if c==self.lang: return
            self.lang=c; self.cfg["lang"]=c; save_cfg(self.cfg); self.s=S[c]
            self._rebuild_main(); htl.config(text=self.s["stitle"])
        for c2,lbl2 in [("en","English"),("ru","Русский")]:
            rb=tk.Radiobutton(lf2,text=lbl2,variable=lv,value=c2,fg=T["fg"],bg=T["card"],
                              selectcolor=T["card"],activebackground=T["card"],
                              activeforeground=T["acc"],font=("Segoe UI",9),cursor="hand2",
                              command=lambda x=c2:on_la(x))
            rb.pack(side="left",padx=8)
            sr(rb,fg="fg",bg="card",selectcolor="card",
               activebackground="card",activeforeground="acc")

        oc=card(s["op"])
        ov=tk.DoubleVar(value=float(self.cfg.get("opacity",0.92)))
        ol=tk.Label(oc,text=f"{int(ov.get()*100)}%",fg=T["acc"],bg=T["card"],
                    font=("Segoe UI",10,"bold"))
        ol.pack(anchor="w",padx=10); sr(ol,fg="acc",bg="card")
        def on_op(v):
            val=round(float(v),2); self.root.attributes("-alpha",val)
            self.cfg["opacity"]=val; ol.config(text=f"{int(val*100)}%"); save_cfg(self.cfg)
        ops=tk.Scale(oc,from_=0.3,to=1.0,resolution=0.05,orient="horizontal",variable=ov,
                     command=on_op,bg=T["card"],fg=T["fg"],troughcolor=T["bg"],
                     activebackground=T["acc"],highlightthickness=0,bd=0,length=300)
        ops.pack(padx=10,pady=(0,10))
        sr(ops,bg="card",fg="fg",troughcolor="bg",activebackground="acc")

        ac=card("About")
        def al(text,font=("Segoe UI",9),fk="fg",link=None):
            lbl=tk.Label(ac,text=text,fg=T[fk],bg=T["card"],font=font,
                         cursor="hand2" if link else "",anchor="w",justify="left")
            lbl.pack(anchor="w",padx=12,pady=2); sr(lbl,fg=fk,bg="card")
            if link: lbl.bind("<Button-1>",lambda e,l=link:webbrowser.open(l))
        al(s["about_name"],  font=("Segoe UI",11,"bold"), fk="fg")
        al(s["about_sub"],   font=("Segoe UI",8),          fk="mut")
        sr(tk.Frame(ac,bg=T["brd"],height=1),bg="brd").pack(fill="x",padx=12,pady=6)
        al(s["about_data"],    fk="mut")
        al(s["about_hotkey"],  fk="mut")
        al(f"{s['about_ver']}: {VERSION}",  fk="mut")
        sr(tk.Frame(ac,bg=T["brd"],height=1),bg="brd").pack(fill="x",padx=12,pady=6)
        al(f"🔗  {s['about_link']} →  github.com/VaKaVo/truesight",
           fk="acc", link=GITHUB)
        tk.Frame(ac,bg=T["card"],height=10).pack()

    def _placeholder(self,txt):
        for w in self.lf.winfo_children(): w.destroy()
        tk.Label(self.lf,text=txt,fg=self.T["mut"],bg=self.T["bg"],
                 font=("Segoe UI",10),justify="center",wraplength=360).pack(pady=30)

    def _render(self,ps):
        for w in self.lf.winfo_children(): w.destroy()
        f=ps
        if self.filt=="toxic":  f=[p for p in ps if self._tox(p)<-30]
        elif self.filt=="good": f=[p for p in ps if self._tox(p)>30]
        elif self.filt=="ok":   f=[p for p in ps if -30<=self._tox(p)<=30]
        if not f: self._placeholder(self.s["none"]); return
        T=self.T
        for i,p in enumerate(f): self._row(p,T["row"] if i%2==0 else T["row2"])

    def _tox(self,p):
        sc=0
        if p.get("behavior") is not None: sc+=(p["behavior"]-8000)/100
        if p.get("winrate")  is not None: sc+=(p["winrate"]-50)
        return sc

    def _row(self,p,bg):
        T=self.T; s=self.s
        row=tk.Frame(self.lf,bg=bg,pady=7,padx=10); row.pack(fill="x",pady=1)
        lft=tk.Frame(row,bg=bg); lft.pack(side="left",fill="x",expand=True)
        nl=tk.Label(lft,text=p["name"],fg=T["fg"],bg=bg,
                    font=("Segoe UI",11,"bold"),anchor="w",cursor="hand2")
        nl.pack(anchor="w"); nl.bind("<Button-1>",lambda e,u=p["url"]:webbrowser.open(u))
        tk.Label(lft,text=p["rank_name"],fg=p["rank_color"],bg=bg,
                 font=("Segoe UI",9),anchor="w").pack(anchor="w")
        if p.get("top_heroes"):
            hf=tk.Frame(lft,bg=bg); hf.pack(anchor="w")
            for h in p["top_heroes"]:
                tk.Label(hf,text=f"#{h['id']} {h['wr']}%",
                         fg=T["mut"],bg=bg,font=("Segoe UI",8)).pack(side="left",padx=(0,5))
        if p.get("wins") is not None:
            tk.Label(lft,text=f"{p['wins']}W / {p['losses']}L",
                     fg=T["mut"],bg=bg,font=("Segoe UI",8)).pack(anchor="w")
        rgt=tk.Frame(row,bg=bg); rgt.pack(side="right")
        wr=p.get("winrate")
        if p.get("is_private"): wt,wc=s["prv"],T["mut"]
        elif wr is None:        wt,wc="—",T["mut"]
        elif wr>=55:            wt,wc=f"{wr}%",T["grn"]
        elif wr<=45:            wt,wc=f"{wr}%",T["red"]
        else:                   wt,wc=f"{wr}%",T["yel"]
        wf=tk.Frame(rgt,bg=bg); wf.pack(anchor="e",pady=1)
        tk.Label(wf,text="WR ",fg=T["mut"],bg=bg,font=("Segoe UI",8)).pack(side="left")
        tk.Label(wf,text=wt,fg=wc,bg=bg,font=("Segoe UI",12,"bold"),
                 width=6,anchor="e").pack(side="left")
        beh=p.get("behavior")
        if beh is None: bt,bc="—",T["mut"]
        elif beh>=9000: bt,bc=str(beh),T["grn"]
        elif beh>=7000: bt,bc=str(beh),T["yel"]
        else:           bt,bc=str(beh),T["red"]
        bf2=tk.Frame(rgt,bg=bg); bf2.pack(anchor="e",pady=1)
        tk.Label(bf2,text=f"{s['bh']} ",fg=T["mut"],bg=bg,font=("Segoe UI",8)).pack(side="left")
        tk.Label(bf2,text=bt,fg=bc,bg=bg,font=("Segoe UI",12,"bold"),
                 width=5,anchor="e").pack(side="left")

    def _search(self):
        s=self.s; raw=self.entry.get().strip()
        if not raw or self._ph_on: return
        sid=None
        if "steamcommunity.com/profiles/" in raw:
            try: sid=int(raw.split("/profiles/")[1].strip("/").split("/")[0])
            except ValueError: pass
        elif raw.isdigit():
            n=int(raw); sid=n if n>76561197960265728 else n+76561197960265728
        if not sid: self._placeholder(s["bad"]); play_error(); return
        self._placeholder(s["load"]); self.stlbl.config(text=s["ls"],fg=self.T["yel"])
        def go():
            d=get_player(sid,self.lang); self.players=[d]
            self.root.after(0,lambda:self._render([d]))
            self.root.after(0,lambda:self.stlbl.config(text=s["done"],fg=self.T["grn"]))
            play_ready()
        threading.Thread(target=go,daemon=True).start()

    def _poll(self):
        s=self.s
        with gsi.lock: mid=gsi.mid; ps=list(gsi.players)
        if mid and ps:
            self.stlbl.config(text=f"{s['match']}{mid}",fg=self.T["grn"])
            miss=[p for p in ps if (p+76561197960265728) not in _cache and p not in _cache]
            if miss:
                threading.Thread(target=self._load_all,args=(ps,mid),daemon=True).start()
            else:
                self._refresh_cache(ps)
        self.root.after(2000,self._poll)

    def _load_all(self,aids,mid):
        futs=[_pool.submit(get_player,
                           a+76561197960265728 if a<76561197960265728 else a,
                           self.lang) for a in aids]
        res=[]
        for f in futs:
            try: res.append(f.result(timeout=15))
            except Exception: pass
        self.players=res
        self.root.after(0,lambda:self._render(res))
        if mid!=self._last_mid:
            self._last_mid=mid; play_ready()

    def _refresh_cache(self,aids):
        res=[]
        for a in aids:
            s64=a+76561197960265728 if a<76561197960265728 else a
            d=_cache.get(s64) or _cache.get(a)
            if d: res.append(d)
        if res: self.players=res; self._render(res)

    def run(self): self.root.mainloop()

if __name__=="__main__":
    start_gsi()
    TrueSight().run()
"""
gui/app.py — YALex/YAPar IDE
Estilo: terminal industrial — oscuro profundo, acentos ámbar
Layout: sidebar + editor central + panel de output inferior
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import sys, os, threading, importlib.util

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from yapar.yapar_parser  import YAParParser
from yapar.first_follow  import compute_first, compute_follow
from yapar.lr0           import LR0Automaton
from yapar.slr_table     import SLRTable
from yapar.lalr_table    import LALRTable
from yapar.ll1_table     import LL1Table
from yapar.parser_engine import LRParserEngine, LL1ParserEngine
from yalex.yalex_reader  import read_file
from yalex.lexer_builder import build_lexer_from_spec
from yalex.generator     import generate_lexer_file

# ── Paleta ─────────────────────────────────────────────────
C = {
    "bg":         "#0A0C0E",
    "bg1":        "#111416",
    "bg2":        "#181C1F",
    "bg3":        "#1E2328",
    "border":     "#2A3038",
    "border2":    "#3A4450",
    "amber":      "#E8A838",
    "amber_dim":  "#8A6420",
    "green":      "#4EC994",
    "green_dim":  "#2A6B50",
    "red":        "#E85050",
    "red_dim":    "#7A2828",
    "blue":       "#5A9EE8",
    "blue_dim":   "#2A4E7A",
    "purple":     "#A878E8",
    "text":       "#D0D8E0",
    "text2":      "#8A96A4",
    "text3":      "#50606C",
    "cursor":     "#E8A838",
}

FM = ("Consolas", 10)       # monospace editor
FS = ("Consolas", 9)        # monospace small
FU = ("Segoe UI", 9)        # ui small
FT = ("Consolas", 11)       # output


def load_lexer_module(path):
    spec = importlib.util.spec_from_file_location("gen_lexer", path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class IDE(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("YALex · YAPar IDE")
        self.geometry("1440x860")
        self.minsize(1100, 650)
        self.configure(bg=C["bg"])

        self.yal_path   = tk.StringVar()
        self.yapar_path = tk.StringVar()
        self.inp_path   = tk.StringVar()
        self.method     = tk.StringVar(value="slr")
        self.show_steps = tk.BooleanVar(value=False)

        self._build()
        self._style_ttk()

    # ────────────────────────────────────────────────────────
    def _build(self):
        # Contenedor raíz: sidebar | main
        root = tk.Frame(self, bg=C["bg"])
        root.pack(fill=tk.BOTH, expand=True)

        self._sidebar(root)
        self._main(root)

    # ── SIDEBAR ─────────────────────────────────────────────
    def _sidebar(self, parent):
        sb = tk.Frame(parent, bg=C["bg1"], width=220,
                      highlightbackground=C["border"],
                      highlightthickness=1)
        sb.pack(side=tk.LEFT, fill=tk.Y)
        sb.pack_propagate(False)

        # Logo
        logo = tk.Frame(sb, bg=C["bg1"])
        logo.pack(fill=tk.X, pady=(0,0))
        tk.Label(logo, text="⟨/⟩", bg=C["bg1"], fg=C["amber"],
                 font=("Consolas", 18, "bold"), pady=16).pack()
        tk.Label(logo, text="YALex · YAPar", bg=C["bg1"], fg=C["text"],
                 font=("Consolas", 9)).pack()
        tk.Label(logo, text="Compiler IDE", bg=C["bg1"], fg=C["text3"],
                 font=("Consolas", 8)).pack(pady=(0,12))

        self._divider(sb)

        # Archivos
        self._sb_section(sb, "FILES")
        for label, var, exts in [
            ("lex  .yal",   self.yal_path,   [("YALex","*.yal"),  ("All","*.*")]),
            ("syn  .yapar", self.yapar_path,  [("YAPar","*.yapar"),("All","*.*")]),
            ("in   .txt",   self.inp_path,    [("Text", "*.txt"),  ("All","*.*")]),
        ]:
            self._file_btn(sb, label, var, exts)

        self._divider(sb)

        # Método
        self._sb_section(sb, "PARSER METHOD")
        for m, col in [("SLR(1)", C["green"]), ("LALR", C["blue"]), ("LL(1)", C["purple"])]:
            key = m.lower().replace("(","").replace(")","").replace("1","1")
            val = {"slr(1)":"slr","lalr":"lalr","ll(1)":"ll1"}[m.lower()]
            rb = tk.Radiobutton(sb, text=f"  {m}", variable=self.method,
                                value=val, bg=C["bg1"], fg=col,
                                selectcolor=C["bg2"],
                                activebackground=C["bg1"],
                                activeforeground=col,
                                font=("Consolas", 9),
                                indicatoron=True, pady=3)
            rb.pack(fill=tk.X, padx=16)

        tk.Checkbutton(sb, text="  show steps", variable=self.show_steps,
                       bg=C["bg1"], fg=C["text3"],
                       selectcolor=C["bg2"],
                       activebackground=C["bg1"],
                       font=("Consolas", 8),
                       pady=4).pack(fill=tk.X, padx=16)

        self._divider(sb)

        # Acciones
        self._sb_section(sb, "ACTIONS")
        self._action_btn(sb, "▶  RUN",     self._run,      C["green"])
        self._action_btn(sb, "⚡  RUN ALL", self._run_all,  C["amber"])
        self._action_btn(sb, "💾  SAVE",    self._save,     C["blue"])

        self._divider(sb)

        # Status
        self._sb_section(sb, "STATUS")
        self.status_icon = tk.Label(sb, text="●", bg=C["bg1"],
                                    fg=C["text3"], font=("Consolas", 22))
        self.status_icon.pack(pady=4)
        self.status_lbl = tk.Label(sb, text="idle", bg=C["bg1"],
                                   fg=C["text3"], font=("Consolas", 8),
                                   wraplength=180)
        self.status_lbl.pack(padx=12)

        # Stats
        self.stats_frame = tk.Frame(sb, bg=C["bg1"])
        self.stats_frame.pack(fill=tk.X, padx=12, pady=8)
        self.stat_vars = {}
        for key, label in [("states","states"), ("tokens","tokens"), ("conflicts","conflicts")]:
            row = tk.Frame(self.stats_frame, bg=C["bg1"])
            row.pack(fill=tk.X, pady=1)
            tk.Label(row, text=f"{label}:", bg=C["bg1"],
                     fg=C["text3"], font=("Consolas", 8),
                     width=10, anchor="w").pack(side=tk.LEFT)
            var = tk.StringVar(value="—")
            self.stat_vars[key] = var
            tk.Label(row, textvariable=var, bg=C["bg1"],
                     fg=C["amber"], font=("Consolas", 8)).pack(side=tk.LEFT)

    def _sb_section(self, parent, title):
        tk.Label(parent, text=title, bg=C["bg1"], fg=C["text3"],
                 font=("Consolas", 7), anchor="w",
                 padx=16, pady=4).pack(fill=tk.X)

    def _divider(self, parent):
        tk.Frame(parent, bg=C["border"], height=1).pack(fill=tk.X, pady=4)

    def _file_btn(self, parent, label, var, exts):
        row = tk.Frame(parent, bg=C["bg1"])
        row.pack(fill=tk.X, padx=12, pady=2)

        tk.Label(row, text=label, bg=C["bg1"], fg=C["text2"],
                 font=("Consolas", 8), width=12, anchor="w").pack(side=tk.LEFT)

        def browse():
            p = filedialog.askopenfilename(filetypes=exts)
            if p:
                var.set(p)
                self._load_to_editor(p, label)

        tk.Button(row, text="…", command=browse,
                  bg=C["bg2"], fg=C["amber"],
                  relief=tk.FLAT, font=("Consolas", 8),
                  padx=6, cursor="hand2",
                  activebackground=C["border"],
                  activeforeground=C["amber"]).pack(side=tk.RIGHT)

        e = tk.Entry(row, textvariable=var, bg=C["bg2"], fg=C["text"],
                     insertbackground=C["amber"], relief=tk.FLAT,
                     font=("Consolas", 7),
                     highlightbackground=C["border"],
                     highlightthickness=1)
        e.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4,2))

    def _action_btn(self, parent, text, cmd, color):
        btn = tk.Button(parent, text=text, command=cmd,
                        bg=C["bg2"], fg=color,
                        relief=tk.FLAT, font=("Consolas", 9, "bold"),
                        padx=12, pady=6, cursor="hand2",
                        activebackground=C["border"],
                        activeforeground=color,
                        anchor="w")
        btn.pack(fill=tk.X, padx=12, pady=2)

    # ── MAIN AREA ───────────────────────────────────────────
    def _main(self, parent):
        main = tk.Frame(parent, bg=C["bg"])
        main.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Parte superior: editor
        top = tk.Frame(main, bg=C["bg"])
        top.pack(fill=tk.BOTH, expand=True)

        # Parte inferior: output panel
        self._output_panel(main)

        # Editor tabs
        self._editor_area(top)

    def _editor_area(self, parent):
        # Tab bar manual estilo VS Code
        bar = tk.Frame(parent, bg=C["bg2"], height=32)
        bar.pack(fill=tk.X)
        bar.pack_propagate(False)

        self.editor_frames = {}
        self.tab_btns = {}
        self.active_tab = tk.StringVar(value="YALex")

        self.editor_container = tk.Frame(parent, bg=C["bg"])
        self.editor_container.pack(fill=tk.BOTH, expand=True)

        for name, color in [("YALex", C["green"]), ("YAPar", C["blue"]), ("Entrada", C["amber"])]:
            btn = tk.Button(bar, text=f"  {name}  ",
                            command=lambda n=name: self._switch_tab(n),
                            bg=C["bg2"], fg=C["text3"],
                            relief=tk.FLAT, font=("Consolas", 9),
                            padx=4, pady=6, cursor="hand2",
                            activebackground=C["bg3"],
                            activeforeground=color,
                            borderwidth=0)
            btn.pack(side=tk.LEFT)
            self.tab_btns[name] = (btn, color)

            frame = tk.Frame(self.editor_container, bg=C["bg"])
            editor = scrolledtext.ScrolledText(
                frame,
                bg=C["bg"], fg=C["text"],
                insertbackground=C["cursor"],
                selectbackground=C["amber_dim"],
                font=FM, relief=tk.FLAT,
                padx=16, pady=12,
                wrap=tk.NONE, undo=True,
                highlightthickness=0,
            )
            editor.pack(fill=tk.BOTH, expand=True)
            self.editor_frames[name] = (frame, editor)

        self._switch_tab("YALex")

    def _switch_tab(self, name):
        self.active_tab.set(name)
        for n, (frame, _) in self.editor_frames.items():
            frame.pack_forget()

        frame, _ = self.editor_frames[name]
        frame.pack(fill=tk.BOTH, expand=True)

        for n, (btn, color) in self.tab_btns.items():
            if n == name:
                btn.config(fg=color, bg=C["bg3"],
                           relief=tk.FLAT)
            else:
                btn.config(fg=C["text3"], bg=C["bg2"])

    def _output_panel(self, parent):
        # Separador draggable — simplificado con altura fija
        sep = tk.Frame(parent, bg=C["border2"], height=2, cursor="sb_v_double_arrow")
        sep.pack(fill=tk.X)

        panel = tk.Frame(parent, bg=C["bg1"], height=320)
        panel.pack(fill=tk.X)
        panel.pack_propagate(False)

        # Tab bar del output
        tab_bar = tk.Frame(panel, bg=C["bg2"], height=28)
        tab_bar.pack(fill=tk.X)
        tab_bar.pack_propagate(False)

        self.out_frames  = {}
        self.out_btns    = {}
        self.active_out  = tk.StringVar(value="Resultado")

        tabs = [
            ("Resultado",    C["green"]),
            ("Tokens",       C["amber"]),
            ("SLR(1)",       C["green"]),
            ("LALR",         C["blue"]),
            ("LL(1)",        C["purple"]),
            ("LR(0)",        C["amber"]),
            ("FIRST/FOLLOW", C["text2"]),
        ]

        out_container = tk.Frame(panel, bg=C["bg1"])
        out_container.pack(fill=tk.BOTH, expand=True)

        for name, color in tabs:
            btn = tk.Button(tab_bar, text=f" {name} ",
                            command=lambda n=name: self._switch_out(n),
                            bg=C["bg2"], fg=C["text3"],
                            relief=tk.FLAT, font=FS,
                            padx=2, pady=4, cursor="hand2",
                            activebackground=C["bg3"],
                            borderwidth=0)
            btn.pack(side=tk.LEFT)
            self.out_btns[name] = (btn, color)

            frame = tk.Frame(out_container, bg=C["bg1"])
            text  = scrolledtext.ScrolledText(
                frame,
                bg=C["bg1"], fg=C["text"],
                insertbackground=C["cursor"],
                font=FT, relief=tk.FLAT,
                padx=12, pady=8,
                wrap=tk.NONE,
                state=tk.DISABLED,
                highlightthickness=0,
            )
            text.pack(fill=tk.BOTH, expand=True)
            self.out_frames[name] = (frame, text)

        self._switch_out("Resultado")

    def _switch_out(self, name):
        self.active_out.set(name)
        for n, (frame, _) in self.out_frames.items():
            frame.pack_forget()

        frame, _ = self.out_frames[name]
        frame.pack(fill=tk.BOTH, expand=True)

        for n, (btn, color) in self.out_btns.items():
            if n == name:
                btn.config(fg=color, bg=C["bg3"])
            else:
                btn.config(fg=C["text3"], bg=C["bg2"])

    # ── Cargar archivo ───────────────────────────────────────
    def _load_to_editor(self, path, label):
        try:
            content = open(path, "r", encoding="utf-8").read()
            if "yal" in label:
                tab = "YALex"
            elif "yapar" in label:
                tab = "YAPar"
            else:
                tab = "Entrada"
            _, editor = self.editor_frames[tab]
            editor.config(state=tk.NORMAL)
            editor.delete("1.0", tk.END)
            editor.insert("1.0", content)
            self._switch_tab(tab)
            self._status(f"loaded: {os.path.basename(path)}", "ok")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _get_editor(self, name):
        _, ed = self.editor_frames[name]
        return ed.get("1.0", tk.END).strip()

    # ── Guardar ──────────────────────────────────────────────
    def _save(self):
        saved = []
        for name, var in [("YALex", self.yal_path),
                           ("YAPar", self.yapar_path),
                           ("Entrada", self.inp_path)]:
            path = var.get().strip()
            if path:
                try:
                    content = self._get_editor(name)
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(content)
                    saved.append(name)
                except Exception as e:
                    messagebox.showerror("Error", str(e))
        if saved:
            self._status(f"saved: {', '.join(saved)}", "ok")

    # ── Análisis ─────────────────────────────────────────────
    def _run(self):
        threading.Thread(target=self._analyze,
                         args=(self.method.get(),), daemon=True).start()

    def _run_all(self):
        threading.Thread(target=self._analyze,
                         args=("all",), daemon=True).start()

    def _analyze(self, method):
        self._status("running...", "working")
        self._clear_all()

        try:
            yal_text   = self._get_editor("YALex")
            yapar_text = self._get_editor("YAPar")
            inp_text   = self._get_editor("Entrada")

            if not yal_text or not yapar_text:
                self._write("Resultado",
                            "ERROR: carga los archivos primero\n", C["red"])
                self._status("missing files", "error")
                return

            # Parsear yapar
            yp = YAParParser(yapar_text)
            tokens_d, ignored, productions, prod_order = yp.parse()
            terminals = set(tokens_d)

            # FIRST / FOLLOW
            first  = compute_first(productions, terminals)
            follow = compute_follow(productions, prod_order, first, terminals)
            self._show_ff(first, follow, productions)

            # LR(0)
            automaton = LR0Automaton(productions, prod_order, terminals).build()
            self._show_lr0(automaton)

            # Tablas
            slr_t  = SLRTable(automaton, follow, terminals).build()
            lalr_t = LALRTable(automaton, first, terminals).build()
            ll1_t  = LL1Table(productions, prod_order, first, follow, terminals).build()
            self._show_slr(slr_t)
            self._show_lalr(lalr_t)
            self._show_ll1(ll1_t)

            # Lexer
            afd = build_lexer_from_spec(yal_text)
            generate_lexer_file(afd, "temp_gui_lexer.py")
            lexer = load_lexer_module("temp_gui_lexer.py")

            tok_list, lex_errors = lexer.tokenize(inp_text)
            self._show_tokens(tok_list, lex_errors)

            filtered = [(t, l) for t, l in tok_list
                        if t not in ignored and not t.startswith("_")]

            # Análisis
            methods = ["slr", "lalr", "ll1"] if method == "all" else [method]
            self._show_result(methods, slr_t, lalr_t, ll1_t,
                              filtered, ignored, prod_order)

            # Stats en sidebar
            self.stat_vars["states"].set(str(len(automaton.states)))
            self.stat_vars["tokens"].set(str(len(tok_list)))
            conf = len(slr_t.conflicts)
            self.stat_vars["conflicts"].set(str(conf))

            self._status("done", "ok")
            self._switch_out("Resultado")

        except Exception as e:
            import traceback
            self._write("Resultado",
                        f"EXCEPTION:\n{e}\n\n{traceback.format_exc()}\n",
                        C["red"])
            self._status(f"error: {e}", "error")

    # ── Output helpers ───────────────────────────────────────
    def _write(self, tab, text, color=None):
        _, widget = self.out_frames[tab]
        widget.config(state=tk.NORMAL)
        if color:
            tag = "c" + color.replace("#", "")
            widget.tag_config(tag, foreground=color)
            widget.insert(tk.END, text, tag)
        else:
            widget.insert(tk.END, text)
        widget.config(state=tk.DISABLED)
        widget.see(tk.END)

    def _clear_all(self):
        for name, (_, w) in self.out_frames.items():
            w.config(state=tk.NORMAL)
            w.delete("1.0", tk.END)
            w.config(state=tk.DISABLED)

    def _status(self, msg, kind="ok"):
        colors = {"ok": C["green"], "error": C["red"],
                  "working": C["amber"], "idle": C["text3"]}
        col = colors.get(kind, C["text3"])
        self.status_icon.config(fg=col)
        self.status_lbl.config(text=msg, fg=col)

    # ── Mostrar resultados ───────────────────────────────────
    def _show_ff(self, first, follow, productions):
        t = "FIRST/FOLLOW"
        self._write(t, "── FIRST ──────────────────────────\n\n", C["amber"])
        for nt in sorted(productions):
            f = ", ".join(sorted(first.get(nt, set())))
            self._write(t, f"  FIRST({nt})", C["blue"])
            self._write(t, f" = {{{f}}}\n", C["text"])
        self._write(t, "\n── FOLLOW ─────────────────────────\n\n", C["amber"])
        for nt in sorted(productions):
            f = ", ".join(sorted(follow.get(nt, set())))
            self._write(t, f"  FOLLOW({nt})", C["purple"])
            self._write(t, f" = {{{f}}}\n", C["text"])

    def _show_lr0(self, auto):
        t = "LR(0)"
        self._write(t,
            f"── AUTÓMATA LR(0) ──────────────────\n\n"
            f"  estados:      {len(auto.states)}\n"
            f"  transiciones: {len(auto.transitions)}\n"
            f"  símbolo aug:  {auto.aug_start} → {auto.start}\n\n",
            C["amber"]
        )
        for i, state in enumerate(auto.states):
            self._write(t, f"Estado {i}:\n", C["green"])
            for item in sorted(state, key=lambda x: (x.head, x.dot)):
                self._write(t, f"  {item}\n", C["text"])
            trans = {s: d for (src, s), d in auto.transitions.items() if src == i}
            for s, d in sorted(trans.items()):
                self._write(t, f"  GOTO({s}) → {d}\n", C["text3"])
            self._write(t, "\n")

    def _show_slr(self, table):
        self._show_lr_table("SLR(1)", table, table.automaton)

    def _show_lalr(self, table):
        self._show_lr_table("LALR", table, table.automaton)

    def _show_lr_table(self, name, table, auto):
        n = len(table.conflicts)
        col = C["green"] if n == 0 else C["amber"]
        self._write(name,
            f"── TABLA {name} ───────────────────────\n\n"
            f"  entradas ACTION:  {len(table.action)}\n"
            f"  entradas GOTO:    {len(table.goto)}\n"
            f"  conflictos:       {n}\n\n",
            col
        )
        if table.conflicts:
            self._write(name, "CONFLICTOS:\n", C["red"])
            for c in table.conflicts:
                self._write(name,
                    f"  estado {c['state']} [{c['symbol']}] "
                    f"{c['type']}\n", C["amber"])
            self._write(name, "\n")

        all_t  = sorted({s for (_, s) in table.action})
        all_nt = sorted({s for (_, s) in table.goto})

        self._write(name, f"{'st':<4}", C["text3"])
        for t in all_t:
            self._write(name, f"{t[:9]:<10}", C["text3"])
        self._write(name, " │ ", C["border2"])
        for nt in all_nt:
            self._write(name, f"{nt[:11]:<12}", C["text3"])
        self._write(name, "\n" + "─"*80 + "\n", C["border2"])

        n_states = len(auto.states) if hasattr(auto, 'states') else 0
        for idx in range(n_states):
            self._write(name, f"{idx:<4}", C["blue"])
            for t in all_t:
                act = table.action.get((idx, t), "")
                if act:
                    if act[0] == "SHIFT":
                        self._write(name, f"{'S'+str(act[1]):<10}", C["green"])
                    elif act[0] == "REDUCE":
                        self._write(name, f"{'r'+act[1][:7]:<10}", C["purple"])
                    elif act[0] == "ACCEPT":
                        self._write(name, f"{'ACC':<10}", C["amber"])
                    else:
                        self._write(name, f"{'?':<10}", C["red"])
                else:
                    self._write(name, f"{'·':<10}", C["text3"])
            self._write(name, " │ ", C["border2"])
            for nt in all_nt:
                v = table.goto.get((idx, nt), "")
                if v != "":
                    self._write(name, f"{str(v):<12}", C["blue"])
                else:
                    self._write(name, f"{'·':<12}", C["text3"])
            self._write(name, "\n")

    def _show_ll1(self, table):
        n = len(table.conflicts)
        col = C["green"] if n == 0 else C["amber"]
        self._write("LL(1)",
            f"── TABLA LL(1) ─────────────────────\n\n"
            f"  entradas:   {len(table.table)}\n"
            f"  conflictos: {n}\n\n",
            col
        )
        if table.conflicts:
            self._write("LL(1)", "CONFLICTOS:\n", C["red"])
            for c in table.conflicts[:30]:
                ex = " ".join(c['existing']) if c['existing'] else "ε"
                nw = " ".join(c['new'])      if c['new']      else "ε"
                self._write("LL(1)",
                    f"  M[{c['non_terminal']}][{c['terminal']}]: "
                    f"→{ex}  vs  →{nw}\n", C["amber"])
            if n > 30:
                self._write("LL(1)",
                    f"  ... y {n-30} más\n", C["text3"])
            self._write("LL(1)", "\n")

        all_t = sorted({t for (_, t) in table.table})
        self._write("LL(1)", f"{'no-terminal':<22}", C["text3"])
        for t in all_t:
            self._write("LL(1)", f"{t[:13]:<14}", C["text3"])
        self._write("LL(1)", "\n" + "─"*80 + "\n", C["border2"])
        for nt in table.prod_order:
            self._write("LL(1)", f"{nt:<22}", C["purple"])
            for t in all_t:
                cell = table.table.get((nt, t))
                if cell is not None:
                    body  = " ".join(cell) if cell else "ε"
                    short = (nt+"→"+body)[:13]
                    self._write("LL(1)", f"{short:<14}", C["text"])
                else:
                    self._write("LL(1)", f"{'·':<14}", C["text3"])
            self._write("LL(1)", "\n")

    def _show_tokens(self, tok_list, lex_errors):
        t = "Tokens"
        self._write(t,
            f"── TOKENS ──────────────────────────\n\n"
            f"  total:         {len(tok_list)}\n"
            f"  errores léx:   {len(lex_errors)}\n\n",
            C["amber"]
        )
        for tok, lex in tok_list:
            self._write(t, f"  {tok:<28}", C["green"])
            self._write(t, f"{repr(lex)}\n", C["blue"])
        if lex_errors:
            self._write(t, "\nERRORES LÉXICOS:\n", C["red"])
            for e in lex_errors:
                self._write(t, f"  {e}\n", C["amber"])

    def _show_result(self, methods, slr_t, lalr_t, ll1_t,
                     filtered, ignored, prod_order):
        t = "Resultado"
        for m in methods:
            self._write(t,
                f"── {m.upper()} ──────────────────────────\n\n",
                C["amber"]
            )
            if m == "slr":
                engine = LRParserEngine(slr_t, ignored)
            elif m == "lalr":
                engine = LRParserEngine(lalr_t, ignored)
            else:
                engine = LL1ParserEngine(ll1_t, prod_order[0], ignored)

            result = engine.parse(filtered)

            if result.accepted:
                self._write(t, "  ✓ ACEPTADA\n\n", C["green"])
            else:
                self._write(t, "  ✗ RECHAZADA\n\n", C["red"])

            if result.errors:
                self._write(t,
                    f"  errores sintácticos ({len(result.errors)}):\n",
                    C["amber"])
                for err in result.errors:
                    self._write(t, f"    • {err}\n", C["text2"])
                self._write(t, "\n")

            if self.show_steps.get() and result.steps:
                self._write(t,
                    f"  pasos ({len(result.steps)}):\n\n",
                    C["text3"])
                self._write(t,
                    f"  {'pila':<32} {'entrada':<28} acción\n",
                    C["text3"])
                self._write(t, "  " + "─"*85 + "\n", C["border2"])
                for step in result.steps[:300]:
                    stk = str(step['stack'])[-30:]
                    inp = str(step['input'])[:26]
                    act = step['action']
                    col = C["text2"]
                    if "SHIFT"  in act: col = C["green"]
                    if "REDUCE" in act: col = C["purple"]
                    if "ACCEPT" in act: col = C["amber"]
                    if "ERROR"  in act: col = C["red"]
                    self._write(t,
                        f"  {stk:<32} {inp:<28} ", C["text3"])
                    self._write(t, f"{act}\n", col)
                if len(result.steps) > 300:
                    self._write(t,
                        f"\n  ... {len(result.steps)-300} pasos más\n",
                        C["text3"])
            self._write(t, "\n")

    # ── TTK styles ───────────────────────────────────────────
    def _style_ttk(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TScrollbar",
                        background=C["bg2"],
                        troughcolor=C["bg1"],
                        bordercolor=C["bg1"],
                        arrowcolor=C["text3"])


def main():
    app = IDE()
    app.mainloop()

if __name__ == "__main__":
    main()
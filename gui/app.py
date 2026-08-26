"""
gui/app.py — YALex/YAPar IDE
Estilo: terminal industrial — oscuro profundo, acentos ámbar
Layout: sidebar + editor central + panel de output inferior
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import sys, os, threading, importlib.util, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from yapar.yapar_parser import YAParParser
from yapar.first_follow import compute_first, compute_follow
from yapar.lr0 import LR0Automaton
from yapar.slr_table import SLRTable
from yapar.lalr_table import LALRTable
from yapar.ll1_table import LL1Table
from yapar.parser_engine import LRParserEngine, LL1ParserEngine
from yalex.yalex_reader import read_file
from yalex.lexer_builder import build_lexer_from_spec
from yalex.generator import generate_lexer_file
from antlr4 import InputStream, CommonTokenStream, Token
from antlr4.error.ErrorListener import ErrorListener
from compiscript.generated.CompiscriptLexer import CompiscriptLexer
from compiscript.generated.CompiscriptParser import CompiscriptParser
from compiscript.semantic import SemanticAnalyzer


class CPSAnalysisErrorListener(ErrorListener):
    """Captura errores de ANTLR sin imprimirlos en stderr."""
    def __init__(self, phase):
        super().__init__()
        self.phase = phase
        self.errors = []

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        self.errors.append({
            'phase': self.phase,
            'line': line,
            'column': column,
            'message': msg,
        })

C = {'bg': '#0B100E', 'bg1': '#101714', 'bg2': '#151E1A', 'bg3': '#1B2722', 'border': '#26352F', 'border2': '#34483F', 'amber': '#E7B75B', 'amber_dim': '#765C2E', 'green': '#4DD6A0', 'green_dim': '#1E6E53', 'red': '#F06A6A', 'red_dim': '#7B3434', 'blue': '#62A8F5', 'blue_dim': '#315D86', 'purple': '#B184F4', 'text': '#D7E2DD', 'text2': '#8FA29A', 'text3': '#566A62', 'cursor': '#4DD6A0'}
FM = ('Consolas', 10)
FS = ('Consolas', 9)
FU = ('Segoe UI', 9)
FT = ('Consolas', 11)

def load_lexer_module(path):
    spec = importlib.util.spec_from_file_location('gen_lexer', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

class IDE(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title('Compiler Lab · YALex · YAPar · Compiscript')
        self.geometry('1480x900')
        self.minsize(1100, 650)
        self.configure(bg=C['bg'])
        self.yal_path = tk.StringVar()
        self.yapar_path = tk.StringVar()
        self.inp_path = tk.StringVar()
        self.cps_path = tk.StringVar()
        self.method = tk.StringVar(value='slr')
        self.show_steps = tk.BooleanVar(value=False)
        self._build()
        self._style_ttk()

    def _build(self):
        root = tk.Frame(self, bg=C['bg'])
        root.pack(fill=tk.BOTH, expand=True)
        self._sidebar(root)
        self._main(root)

    def _sidebar(self, parent):
        sb = tk.Frame(parent, bg=C['bg1'], width=252, highlightbackground=C['border'], highlightthickness=1)
        sb.pack(side=tk.LEFT, fill=tk.Y)
        sb.pack_propagate(False)
        brand = tk.Frame(sb, bg=C['bg1'])
        brand.pack(fill=tk.X, padx=18, pady=(18, 14))
        mark = tk.Frame(brand, bg=C['bg3'], width=44, height=44, highlightbackground=C['green_dim'], highlightthickness=1)
        mark.pack(side=tk.LEFT)
        mark.pack_propagate(False)
        tk.Label(mark, text='</>', bg=C['bg3'], fg=C['green'], font=('Consolas', 13, 'bold')).pack(expand=True)
        titles = tk.Frame(brand, bg=C['bg1'])
        titles.pack(side=tk.LEFT, padx=(11, 0))
        tk.Label(titles, text='COMPILER LAB', bg=C['bg1'], fg=C['text'], font=('Consolas', 10, 'bold'), anchor='w').pack(fill=tk.X)
        tk.Label(titles, text='YALex · YAPar · CPS', bg=C['bg1'], fg=C['green'], font=('Consolas', 7), anchor='w').pack(fill=tk.X, pady=(3, 0))
        self._divider(sb)
        self._sb_section(sb, 'WORKSPACE')
        for label, var, exts in [('LEXER', self.yal_path, [('YALex', '*.yal'), ('All', '*.*')]), ('GRAMMAR', self.yapar_path, [('YAPar', '*.yapar'), ('All', '*.*')]), ('INPUT', self.inp_path, [('Text', '*.txt'), ('All', '*.*')]), ('CPS', self.cps_path, [('Compiscript', '*.cps'), ('All', '*.*')])]:
            self._file_btn(sb, label, var, exts)
        self._divider(sb)
        self._sb_section(sb, 'PARSER')
        parser_box = tk.Frame(sb, bg=C['bg1'])
        parser_box.pack(fill=tk.X, padx=14, pady=(2, 6))
        for m, col in [('SLR(1)', C['green']), ('LALR', C['blue']), ('LL(1)', C['purple'])]:
            val = {'slr(1)': 'slr', 'lalr': 'lalr', 'll(1)': 'll1'}[m.lower()]
            rb = tk.Radiobutton(parser_box, text=m, variable=self.method, value=val, bg=C['bg1'], fg=col, selectcolor=C['bg3'], activebackground=C['bg1'], activeforeground=col, font=('Consolas', 9, 'bold'), indicatoron=True, anchor='w', pady=4)
            rb.pack(fill=tk.X, padx=7)
        tk.Checkbutton(parser_box, text='show parser steps', variable=self.show_steps, bg=C['bg1'], fg=C['text3'], selectcolor=C['bg3'], activebackground=C['bg1'], activeforeground=C['text2'], font=('Consolas', 8), anchor='w', pady=4).pack(fill=tk.X, padx=7)
        self._divider(sb)
        self._sb_section(sb, 'ACTIONS')
        self._action_btn(sb, '▶   RUN', self._run, C['green'], primary=True)
        self._action_btn(sb, '⚡  RUN ALL', self._run_all, C['amber'])
        self._action_btn(sb, '◆   COMPILE CPS', self._run_compiscript, C['purple'])
        self._action_btn(sb, '▣   SAVE', self._save, C['blue'])
        self._divider(sb)
        self._sb_section(sb, 'SESSION')
        status = tk.Frame(sb, bg=C['bg2'], highlightbackground=C['border'], highlightthickness=1)
        status.pack(fill=tk.X, padx=14, pady=(2, 8))
        status_top = tk.Frame(status, bg=C['bg2'])
        status_top.pack(fill=tk.X, padx=10, pady=(9, 5))
        self.status_icon = tk.Label(status_top, text='●', bg=C['bg2'], fg=C['text3'], font=('Consolas', 12))
        self.status_icon.pack(side=tk.LEFT)
        self.status_lbl = tk.Label(status_top, text='READY', bg=C['bg2'], fg=C['text3'], font=('Consolas', 8, 'bold'), anchor='w', wraplength=170)
        self.status_lbl.pack(side=tk.LEFT, padx=(7, 0), fill=tk.X, expand=True)
        self.stats_frame = tk.Frame(status, bg=C['bg2'])
        self.stats_frame.pack(fill=tk.X, padx=8, pady=(0, 9))
        self.stat_vars = {}
        specs = [('states', 'STATES'), ('tokens', 'TOKENS'), ('conflicts', 'CONFLICTS')]
        for key, label in specs:
            card = tk.Frame(self.stats_frame, bg=C['bg3'])
            card.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
            var = tk.StringVar(value='—')
            self.stat_vars[key] = var
            tk.Label(card, textvariable=var, bg=C['bg3'], fg=C['green'], font=('Consolas', 10, 'bold')).pack(pady=(6, 0))
            tk.Label(card, text=label, bg=C['bg3'], fg=C['text3'], font=('Consolas', 6)).pack(pady=(0, 6))

    def _sb_section(self, parent, title):
        tk.Label(parent, text=title, bg=C['bg1'], fg=C['text3'], font=('Consolas', 7, 'bold'), anchor='w', padx=16, pady=5).pack(fill=tk.X)

    def _divider(self, parent):
        tk.Frame(parent, bg=C['border'], height=1).pack(fill=tk.X, pady=7)

    def _file_btn(self, parent, label, var, exts):
        row = tk.Frame(parent, bg=C['bg1'])
        row.pack(fill=tk.X, padx=14, pady=3)
        dot = tk.Label(row, text='●', bg=C['bg1'], fg=C['text3'], font=('Consolas', 8))
        dot.pack(side=tk.LEFT, padx=(0, 7))
        info = tk.Frame(row, bg=C['bg1'])
        info.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(info, text=label, bg=C['bg1'], fg=C['text2'], font=('Consolas', 7, 'bold'), anchor='w').pack(fill=tk.X)
        display = tk.StringVar(value='No file selected')
        name_lbl = tk.Label(info, textvariable=display, bg=C['bg1'], fg=C['text3'], font=('Consolas', 8), anchor='w')
        name_lbl.pack(fill=tk.X)

        def sync(*_):
            path = var.get().strip()
            display.set(os.path.basename(path) if path else 'No file selected')
            dot.config(fg=C['green'] if path else C['text3'])
        var.trace_add('write', sync)
        sync()

        def browse():
            p = filedialog.askopenfilename(filetypes=exts)
            if p:
                var.set(p)
                load_label = {'LEXER': 'lex  .yal', 'GRAMMAR': 'syn  .yapar', 'INPUT': 'in   .txt', 'CPS': 'cps  .cps'}[label]
                self._load_to_editor(p, load_label)
        tk.Button(row, text='＋', command=browse, bg=C['bg2'], fg=C['green'], relief=tk.FLAT, font=('Consolas', 9, 'bold'), width=3, cursor='hand2', activebackground=C['bg3'], activeforeground=C['green']).pack(side=tk.RIGHT, padx=(6, 0))

    def _action_btn(self, parent, text, cmd, color, primary=False):
        bg = C['green_dim'] if primary else C['bg2']
        fg = C['text'] if primary else color
        btn = tk.Button(parent, text=text, command=cmd, bg=bg, fg=fg, relief=tk.FLAT, font=('Consolas', 9, 'bold'), padx=13, pady=8, cursor='hand2', anchor='w', activebackground=C['bg3'], activeforeground=color, highlightbackground=C['border'], highlightthickness=1)
        btn.pack(fill=tk.X, padx=14, pady=3)

    def _main(self, parent):
        main = tk.Frame(parent, bg=C['bg'])
        main.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        top = tk.Frame(main, bg=C['bg'])
        top.pack(fill=tk.BOTH, expand=True)
        self._output_panel(main)
        self._editor_area(top)

    def _editor_area(self, parent):
        bar = tk.Frame(parent, bg=C['bg1'], height=38)
        bar.pack(fill=tk.X)
        bar.pack_propagate(False)
        self.editor_frames = {}
        self.tab_btns = {}
        self.active_tab = tk.StringVar(value='YALex')
        self.editor_container = tk.Frame(parent, bg=C['bg'])
        self.editor_container.pack(fill=tk.BOTH, expand=True)
        for name, color in [('YALex', C['green']), ('YAPar', C['blue']), ('Entrada', C['amber']), ('Compiscript', C['purple'])]:
            btn = tk.Button(bar, text=f'  {name}  ', command=lambda n=name: self._switch_tab(n), bg=C['bg1'], fg=C['text3'], relief=tk.FLAT, font=('Consolas', 9, 'bold'), padx=10, pady=8, cursor='hand2', activebackground=C['bg3'], activeforeground=color, borderwidth=0)
            btn.pack(side=tk.LEFT)
            self.tab_btns[name] = (btn, color)
            frame = tk.Frame(self.editor_container, bg=C['bg'])
            if name == 'Compiscript':
                editor = self._build_cps_editor(frame)
            else:
                editor = scrolledtext.ScrolledText(frame, bg=C['bg'], fg=C['text'], insertbackground=C['cursor'], selectbackground=C['amber_dim'], font=FM, relief=tk.FLAT, padx=16, pady=12, wrap=tk.NONE, undo=True, highlightthickness=0)
                editor.pack(fill=tk.BOTH, expand=True)
            self.editor_frames[name] = (frame, editor)
        self._switch_tab('YALex')

    def _build_cps_editor(self, parent):
        """Editor CPS con gutter, highlighting y barra Ln/Col."""
        body = tk.Frame(parent, bg=C['bg'])
        body.pack(fill=tk.BOTH, expand=True)
        gutter = tk.Text(body, width=5, bg=C['bg1'], fg=C['text3'], font=FM, relief=tk.FLAT, padx=6, pady=12, state=tk.DISABLED, takefocus=0, cursor='arrow')
        gutter.pack(side=tk.LEFT, fill=tk.Y)
        scroll = tk.Scrollbar(body, orient=tk.VERTICAL)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        editor = tk.Text(body, bg=C['bg'], fg=C['text'], insertbackground=C['cursor'], selectbackground=C['amber_dim'], font=FM, relief=tk.FLAT, padx=12, pady=12, wrap=tk.NONE, undo=True, highlightthickness=0)
        editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        editor.config(yscrollcommand=lambda a, b: self._cps_scroll_sync(a, b, gutter, scroll))
        scroll.config(command=lambda *args: self._cps_yview(editor, gutter, *args))
        status = tk.Frame(parent, bg=C['bg2'], height=24)
        status.pack(fill=tk.X)
        self.cps_cursor_var = tk.StringVar(value='Ln 1, Col 1')
        tk.Label(status, text='  Compiscript', bg=C['bg2'], fg=C['purple'], font=('Consolas', 8, 'bold')).pack(side=tk.LEFT)
        tk.Label(status, text='UTF-8   ', bg=C['bg2'], fg=C['text3'], font=('Consolas', 8)).pack(side=tk.RIGHT)
        tk.Label(status, textvariable=self.cps_cursor_var, bg=C['bg2'], fg=C['text2'], font=('Consolas', 8)).pack(side=tk.RIGHT, padx=12)
        self.cps_gutter = gutter
        self.cps_editor = editor
        self._configure_cps_tags(editor)
        for ev in ('<KeyRelease>', '<ButtonRelease-1>', '<MouseWheel>', '<Configure>'):
            editor.bind(ev, self._on_cps_editor_event, add='+')
        editor.bind('<<Modified>>', self._on_cps_modified, add='+')
        self.after_idle(self._refresh_cps_editor)
        return editor

    def _cps_scroll_sync(self, first, last, gutter, scrollbar):
        scrollbar.set(first, last)
        gutter.yview_moveto(first)

    def _cps_yview(self, editor, gutter, *args):
        editor.yview(*args)
        gutter.yview(*args)

    def _configure_cps_tags(self, editor):
        editor.tag_configure('cps_keyword', foreground=C['purple'])
        editor.tag_configure('cps_type', foreground=C['blue'])
        editor.tag_configure('cps_string', foreground=C['green'])
        editor.tag_configure('cps_number', foreground=C['amber'])
        editor.tag_configure('cps_comment', foreground=C['text3'])
        editor.tag_configure('cps_builtin', foreground=C['green'])
        editor.tag_configure('cps_current', background=C['bg1'])
        editor.tag_lower('cps_current')

    def _on_cps_modified(self, event=None):
        if self.cps_editor.edit_modified():
            self.cps_editor.edit_modified(False)
            self.after_idle(self._refresh_cps_editor)

    def _on_cps_editor_event(self, event=None):
        self.after_idle(self._refresh_cps_editor)

    def _refresh_cps_editor(self):
        if not hasattr(self, 'cps_editor'):
            return
        ed = self.cps_editor
        lines = int(ed.index('end-1c').split('.')[0])
        self.cps_gutter.config(state=tk.NORMAL)
        self.cps_gutter.delete('1.0', tk.END)
        self.cps_gutter.insert('1.0', '\n'.join((str(i) for i in range(1, lines + 1))))
        self.cps_gutter.config(state=tk.DISABLED)
        try:
            self.cps_gutter.yview_moveto(ed.yview()[0])
        except Exception:
            pass
        line, col = map(int, ed.index(tk.INSERT).split('.'))
        self.cps_cursor_var.set(f'Ln {line}, Col {col + 1}')
        ed.tag_remove('cps_current', '1.0', tk.END)
        ed.tag_add('cps_current', f'{line}.0', f'{line}.end+1c')
        self._highlight_cps()

    def _highlight_cps(self):
        ed = self.cps_editor
        text = ed.get('1.0', 'end-1c')
        for tag in ('cps_keyword', 'cps_type', 'cps_string', 'cps_number', 'cps_comment', 'cps_builtin'):
            ed.tag_remove(tag, '1.0', tk.END)
        patterns = [('cps_comment', '//[^\\n]*|/\\*[\\s\\S]*?\\*/'), ('cps_string', '"(?:\\\\.|[^"\\\\])*"'), ('cps_number', '\\b\\d+\\b'), ('cps_type', '\\b(?:integer|string|boolean|null|void)\\b'), ('cps_builtin', '\\b(?:print|this|new)\\b'), ('cps_keyword', '\\b(?:let|var|const|function|class|if|else|while|do|for|foreach|in|switch|case|default|try|catch|break|continue|return|true|false)\\b')]
        for tag, pat in patterns:
            for m in re.finditer(pat, text):
                a = f'1.0+{m.start()}c'
                b = f'1.0+{m.end()}c'
                ed.tag_add(tag, a, b)

    def _goto_cps_location(self, line, col=0):
        self._switch_tab('Compiscript')
        ed = self.editor_frames['Compiscript'][1]
        pos = f'{max(1, line)}.{max(0, col)}'
        ed.mark_set(tk.INSERT, pos)
        ed.see(pos)
        ed.focus_set()
        self._refresh_cps_editor()

    def _switch_tab(self, name):
        self.active_tab.set(name)
        for n, (frame, _) in self.editor_frames.items():
            frame.pack_forget()
        frame, _ = self.editor_frames[name]
        frame.pack(fill=tk.BOTH, expand=True)
        for n, (btn, color) in self.tab_btns.items():
            if n == name:
                btn.config(fg=color, bg=C['bg3'], relief=tk.FLAT)
            else:
                btn.config(fg=C['text3'], bg=C['bg2'])
        if hasattr(self, 'out_btns'):
            self._update_context_tabs(name)
            if name == 'YALex':
                self._populate_yalex_rules()
            elif name == 'YAPar':
                self._populate_yapar_grammar()

    def _output_panel(self, parent):
        sep = tk.Frame(parent, bg=C['border2'], height=2, cursor='sb_v_double_arrow')
        sep.pack(fill=tk.X)
        panel = tk.Frame(parent, bg=C['bg1'], height=320)
        panel.pack(fill=tk.X)
        panel.pack_propagate(False)
        tab_bar = tk.Frame(panel, bg=C['bg2'], height=28)
        tab_bar.pack(fill=tk.X)
        tab_bar.pack_propagate(False)
        self.out_frames = {}
        self.out_btns = {}
        self.active_out = tk.StringVar(value='Resultado')
        tabs = [('Resultado', C['green']), ('Tokens', C['amber']), ('SLR(1)', C['green']), ('LALR', C['blue']), ('LL(1)', C['purple']), ('LR(0)', C['amber']), ('FIRST/FOLLOW', C['text2']), ('YALex Rules', C['green']), ('Grammar YAPar', C['blue']), ('Tokens CPS', C['amber']), ('Árbol CPS', C['purple']), ('Errores Léxicos', C['amber']), ('Errores Sintácticos', C['blue']), ('Errores Semánticos', C['red']), ('Símbolos', C['blue']), ('Language CPS', C['green']), ('Grammar CPS', C['amber'])]
        out_container = tk.Frame(panel, bg=C['bg1'])
        out_container.pack(fill=tk.BOTH, expand=True)
        for name, color in tabs:
            btn = tk.Button(tab_bar, text=f' {name} ', command=lambda n=name: self._switch_out(n), bg=C['bg2'], fg=C['text3'], relief=tk.FLAT, font=FS, padx=2, pady=4, cursor='hand2', activebackground=C['bg3'], borderwidth=0)
            btn.pack(side=tk.LEFT)
            self.out_btns[name] = (btn, color)
            frame = tk.Frame(out_container, bg=C['bg1'])
            if name in {'LR(0)', 'FIRST/FOLLOW', 'SLR(1)', 'LALR', 'LL(1)', 'YALex Rules', 'Grammar YAPar'}:
                widget = self._make_generic_tree_widget(frame)
            elif name == 'Árbol CPS':
                widget = self._make_cps_tree_widget(frame)
            elif name in {'Errores Léxicos', 'Errores Sintácticos', 'Errores Semánticos'}:
                widget = self._make_problems_widget(frame)
            elif name == 'Símbolos':
                widget = self._make_symbols_widget(frame)
            else:
                widget = scrolledtext.ScrolledText(frame, bg=C['bg1'], fg=C['text'], insertbackground=C['cursor'], font=FT, relief=tk.FLAT, padx=12, pady=8, wrap=tk.NONE, state=tk.DISABLED, highlightthickness=0)
                widget.pack(fill=tk.BOTH, expand=True)
            self.out_frames[name] = (frame, widget)
        self._switch_out('Resultado')
        self.after(50, self._populate_cps_reference)

    def _switch_out(self, name):
        self.active_out.set(name)
        for n, (frame, _) in self.out_frames.items():
            frame.pack_forget()
        frame, _ = self.out_frames[name]
        frame.pack(fill=tk.BOTH, expand=True)
        for n, (btn, color) in self.out_btns.items():
            if n == name:
                btn.config(fg=color, bg=C['bg3'])
            else:
                btn.config(fg=C['text3'], bg=C['bg2'])

    def _update_context_tabs(self, editor_tab):
        """Muestra solo las herramientas relevantes al modulo seleccionado."""
        cps_tabs = {'Tokens CPS', 'Árbol CPS', 'Errores Léxicos', 'Errores Sintácticos', 'Errores Semánticos', 'Símbolos', 'Language CPS', 'Grammar CPS'}
        yal_tabs = {'Tokens', 'YALex Rules'}
        yapar_tabs = {'Resultado', 'SLR(1)', 'LALR', 'LL(1)', 'LR(0)', 'FIRST/FOLLOW', 'Grammar YAPar'}
        if editor_tab == 'Compiscript':
            visible = cps_tabs
        elif editor_tab == 'YALex':
            visible = yal_tabs
        else:
            visible = yapar_tabs
        for name, (btn, _) in self.out_btns.items():
            btn.pack_forget()
        for name, (btn, _) in self.out_btns.items():
            if name in visible:
                btn.pack(side=tk.LEFT)
        target = 'Errores Semánticos' if editor_tab == 'Compiscript' else 'YALex Rules' if editor_tab == 'YALex' else 'Resultado'
        if self.active_out.get() not in visible:
            self._switch_out(target)

    def _populate_cps_reference(self):
        """Carga la documentacion del lenguaje y la gramatica real de Compiscript."""
        if 'Language CPS' not in self.out_frames:
            return
        self._clear_tab('Language CPS')
        self._write('Language CPS', 'COMPISCRIPT LANGUAGE REFERENCE\n', C['purple'])
        self._write('Language CPS', '=' * 72 + '\n\n', C['border2'])
        sections = [('TIPOS', 'integer   string   boolean   null   arrays (T[], T[][])'), ('DECLARACIONES', 'let / var   |   const   |   asignacion'), ('FUNCIONES', 'function, parametros tipados, retorno, llamadas y recursion'), ('CLASES', 'class, constructor, herencia (:), this, new, atributos y metodos'), ('CONTROL', 'if/else, while, do-while, for, foreach, switch/case, try/catch'), ('TRANSFERENCIA', 'break, continue, return'), ('EXPRESIONES', '+  -  *  /  %   < <= > >=   == !=   && || !   ?:'), ('ACCESO', 'obj.propiedad   funcion(...)   arreglo[indice]')]
        for title, body in sections:
            self._write('Language CPS', f'{title:<18}', C['amber'])
            self._write('Language CPS', body + '\n', C['text'])
        self._write('Language CPS', '\nEJEMPLOS RAPIDOS\n', C['green'])
        self._write('Language CPS', '-' * 72 + '\n', C['border2'])
        examples = 'let edad: integer = 20;\nconst nombre: string = "Compiscript";\n\nfunction suma(a: integer, b: integer): integer {\n    return a + b;\n}\n\nclass Perro : Animal {\n    function hablar(): string { return this.nombre + " ladra."; }\n}\n'
        self._write('Language CPS', examples, C['text2'])
        self._clear_tab('Grammar CPS')
        self._write('Grammar CPS', 'COMPISCRIPT GRAMMAR EXPLORER\n', C['amber'])
        self._write('Grammar CPS', '=' * 72 + '\n\n', C['border2'])
        self._write('Grammar CPS', 'Fuente: grammars/compiscript/Compiscript.g4\n\n', C['text3'])
        grammar_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'grammars', 'compiscript', 'Compiscript.g4')
        try:
            grammar = open(grammar_path, 'r', encoding='utf-8').read()
            import re
            rules = re.findall('(?ms)^([a-z][A-Za-z0-9_]*)\\s*:(.*?);', grammar)
            self._write('Grammar CPS', f'Parser rules detectadas: {len(rules)}\n\n', C['green'])
            for i, (name, body) in enumerate(rules, 1):
                compact = ' '.join(body.split())
                if len(compact) > 110:
                    compact = compact[:107] + '...'
                self._write('Grammar CPS', f'{i:02d}  {name:<24}', C['blue'])
                self._write('Grammar CPS', f' -> {compact}\n', C['text'])
            self._write('Grammar CPS', '\nLEXER RULES\n', C['purple'])
            self._write('Grammar CPS', '-' * 72 + '\n', C['border2'])
            lexer_rules = re.findall('(?ms)^([A-Z][A-Za-z0-9_]*)\\s*:(.*?);', grammar)
            for name, body in lexer_rules:
                compact = ' '.join(body.split())
                self._write('Grammar CPS', f'{name:<22}', C['green'])
                self._write('Grammar CPS', f' -> {compact}\n', C['text2'])
        except FileNotFoundError:
            self._write('Grammar CPS', 'No se encontro grammars/compiscript/Compiscript.g4.\n', C['red'])
        except Exception as e:
            self._write('Grammar CPS', f'No se pudo leer la gramatica: {e}\n', C['red'])

    def _load_to_editor(self, path, label):
        try:
            content = open(path, 'r', encoding='utf-8').read()
            if 'yal' in label:
                tab = 'YALex'
            elif 'yapar' in label:
                tab = 'YAPar'
            elif 'cps' in label:
                tab = 'Compiscript'
            else:
                tab = 'Entrada'
            _, editor = self.editor_frames[tab]
            editor.config(state=tk.NORMAL)
            editor.delete('1.0', tk.END)
            editor.insert('1.0', content)
            self._switch_tab(tab)
            self._status(f'loaded: {os.path.basename(path)}', 'ok')
        except Exception as e:
            messagebox.showerror('Error', str(e))

    def _get_editor(self, name):
        _, ed = self.editor_frames[name]
        return ed.get('1.0', tk.END).strip()

    def _save(self):
        saved = []
        for name, var in [('YALex', self.yal_path), ('YAPar', self.yapar_path), ('Entrada', self.inp_path), ('Compiscript', self.cps_path)]:
            path = var.get().strip()
            if path:
                try:
                    content = self._get_editor(name)
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    saved.append(name)
                except Exception as e:
                    messagebox.showerror('Error', str(e))
        if saved:
            self._status(f"saved: {', '.join(saved)}", 'ok')

    def _run(self):
        threading.Thread(target=self._analyze, args=(self.method.get(),), daemon=True).start()

    def _run_all(self):
        threading.Thread(target=self._analyze, args=('all',), daemon=True).start()

    def _analyze(self, method):
        self._status('running...', 'working')
        self._clear_all()
        try:
            yal_text = self._get_editor('YALex')
            yapar_text = self._get_editor('YAPar')
            inp_text = self._get_editor('Entrada')
            if not yal_text or not yapar_text:
                self._write('Resultado', 'ERROR: carga los archivos primero\n', C['red'])
                self._status('missing files', 'error')
                return
            yp = YAParParser(yapar_text)
            tokens_d, ignored, productions, prod_order = yp.parse()
            terminals = set(tokens_d)
            first = compute_first(productions, terminals)
            follow = compute_follow(productions, prod_order, first, terminals)
            self._show_ff(first, follow, productions)
            automaton = LR0Automaton(productions, prod_order, terminals).build()
            self._show_lr0(automaton)
            slr_t = SLRTable(automaton, follow, terminals).build()
            lalr_t = LALRTable(automaton, first, terminals).build()
            ll1_t = LL1Table(productions, prod_order, first, follow, terminals).build()
            self._show_slr(slr_t)
            self._show_lalr(lalr_t)
            self._show_ll1(ll1_t)
            afd = build_lexer_from_spec(yal_text)
            generate_lexer_file(afd, 'temp_gui_lexer.py')
            lexer = load_lexer_module('temp_gui_lexer.py')
            tok_list, lex_errors = lexer.tokenize(inp_text)
            self._show_tokens(tok_list, lex_errors)
            filtered = [(t, l) for t, l in tok_list if t not in ignored and (not t.startswith('_'))]
            methods = ['slr', 'lalr', 'll1'] if method == 'all' else [method]
            self._show_result(methods, slr_t, lalr_t, ll1_t, filtered, ignored, prod_order)
            self.stat_vars['states'].set(str(len(automaton.states)))
            self.stat_vars['tokens'].set(str(len(tok_list)))
            conf = len(slr_t.conflicts)
            self.stat_vars['conflicts'].set(str(conf))
            self._populate_yalex_rules()
            self._populate_yapar_grammar()
            self._status('done', 'ok')
            self._switch_out('Resultado')
        except Exception as e:
            import traceback
            self._write('Resultado', f'EXCEPTION:\n{e}\n\n{traceback.format_exc()}\n', C['red'])
            self._status(f'error: {e}', 'error')

    def _run_compiscript(self):
        """Compila el contenido del editor Compiscript en un hilo separado."""
        threading.Thread(target=self._analyze_compiscript, daemon=True).start()

    def _analyze_compiscript(self):
        """Pipeline CPS: análisis léxico -> sintáctico -> semántico."""
        self._status('compiling Compiscript...', 'working')
        for tab in ('Tokens CPS', 'Árbol CPS', 'Errores Léxicos', 'Errores Sintácticos', 'Errores Semánticos', 'Símbolos'):
            self._clear_tab(tab)
        self._populate_cps_reference()
        try:
            source = self._get_editor('Compiscript')
            if not source:
                self._show_cps_problems([], [], [], empty_message='Carga o escribe código .cps primero')
                self._status('missing .cps source', 'error')
                self._switch_out('Errores Semánticos')
                return

            # 1) ANALISIS LEXICO
            input_stream = InputStream(source)
            lexer = CompiscriptLexer(input_stream)
            lex_listener = CPSAnalysisErrorListener('LEXICAL')
            lexer.removeErrorListeners()
            lexer.addErrorListener(lex_listener)
            token_stream = CommonTokenStream(lexer)
            token_stream.fill()
            self._show_cps_tokens(token_stream.tokens, lexer)

            # 2) ANALISIS SINTACTICO
            token_stream.seek(0)
            parser = CompiscriptParser(token_stream)
            syn_listener = CPSAnalysisErrorListener('SYNTAX')
            parser.removeErrorListeners()
            parser.addErrorListener(syn_listener)
            tree = parser.program()
            self._show_cps_tree(tree, parser)

            # 3) ANALISIS SEMANTICO: solo si lexer/parser fueron validos.
            analyzer = None
            semantic_errors = []
            if not lex_listener.errors and not syn_listener.errors:
                analyzer = SemanticAnalyzer()
                analyzer.visit(tree)
                semantic_errors = analyzer.errors
                self._show_symbol_table(analyzer.table)
            else:
                _, symbols = self.out_frames['Símbolos']
                symbols.delete(*symbols.get_children())
                symbols.insert('', 'end', text='Análisis semántico omitido', values=('INFO', '', '', '', 'Corrige primero los errores léxicos/sintácticos'))

            self._show_cps_problems(lex_listener.errors, syn_listener.errors, semantic_errors)
            real_tokens = [t for t in token_stream.tokens if t.type != Token.EOF]
            total_errors = len(lex_listener.errors) + len(syn_listener.errors) + len(semantic_errors)
            self.stat_vars['states'].set('—')
            self.stat_vars['tokens'].set(str(len(real_tokens)))
            self.stat_vars['conflicts'].set(str(total_errors))

            if total_errors:
                self._status(f'CPS: {total_errors} error(s)', 'error')
                self._switch_out('Errores Semánticos')
            else:
                self._status('Compiscript: lexical + syntax + semantic OK', 'ok')
                self._switch_out('Árbol CPS')
        except Exception as e:
            import traceback
            self._show_cps_problems([], [], [], empty_message=f'EXCEPTION: {e}')
            print(traceback.format_exc())
            self._status(f'CPS error: {e}', 'error')
            self._switch_out('Errores Semánticos')

    def _show_cps_tokens(self, tokens, lexer):
        """Muestra el resultado del análisis léxico de ANTLR."""
        tab = 'Tokens CPS'
        _, widget = self.out_frames[tab]
        widget.config(state=tk.NORMAL)
        widget.delete('1.0', tk.END)
        real = [t for t in tokens if t.type != Token.EOF]
        widget.insert(tk.END, f'ANÁLISIS LÉXICO · {len(real)} token(s)\n')
        widget.insert(tk.END, '─' * 92 + '\n')
        widget.insert(tk.END, f"{'#':>4}  {'TOKEN':<28} {'LEXEMA':<30} {'LÍNEA':>6} {'COL':>5}\n")
        widget.insert(tk.END, '─' * 92 + '\n')
        symbolic = getattr(lexer, 'symbolicNames', [])
        literal = getattr(lexer, 'literalNames', [])
        for i, tok in enumerate(real, 1):
            name = None
            if 0 <= tok.type < len(symbolic):
                name = symbolic[tok.type]
            if not name and 0 <= tok.type < len(literal):
                name = literal[tok.type]
            name = name or str(tok.type)
            lexeme = repr(tok.text if tok.text is not None else '')
            if len(lexeme) > 28:
                lexeme = lexeme[:25] + '...'
            widget.insert(tk.END, f'{i:>4}  {name:<28} {lexeme:<30} {tok.line:>6} {tok.column + 1:>5}\n')
        widget.config(state=tk.DISABLED)

    def _show_cps_problems(self, lexical, syntax, semantic, empty_message=None):
        """Muestra cada fase de errores CPS en su propia pestaña."""
        self._problem_locations = {}

        groups = [
            ('Errores Léxicos', lexical, 'LEXICAL', 'Sin errores léxicos'),
            ('Errores Sintácticos', syntax, 'SYNTAX', 'Sin errores sintácticos'),
            ('Errores Semánticos', semantic, 'SEMANTIC', 'Sin errores semánticos'),
        ]

        for tab, errors, phase, ok_message in groups:
            _, view = self.out_frames[tab]
            view.delete(*view.get_children())

            if empty_message:
                view.insert('', 'end', values=('INFO', '—', '—', empty_message), tags=('info',))
                continue

            if not errors:
                view.insert('', 'end', values=('✓ OK', '—', '—', ok_message), tags=('ok',))
                continue

            phase_tag = {'LEXICAL': 'lexical', 'SYNTAX': 'syntax', 'SEMANTIC': 'semantic'}[phase]
            for index, err in enumerate(errors):
                if phase in ('LEXICAL', 'SYNTAX'):
                    line = err.get('line')
                    col = err.get('column', 0)
                    msg = err.get('message', str(err))
                else:
                    line, col = self._error_location(err)
                    msg = str(err)

                phase_label = {'LEXICAL': 'LÉXICO', 'SYNTAX': 'SINTÁCTICO', 'SEMANTIC': 'SEMÁNTICO'}[phase]
                tags = (phase_tag, 'odd') if index % 2 else (phase_tag,)
                iid = view.insert('', 'end', values=(
                    f'● {phase_label}',
                    line if line is not None else '—',
                    col + 1 if line is not None else '—',
                    msg
                ), tags=tags)
                if line is not None:
                    self._problem_locations[(tab, iid)] = (line, col)

    def _on_problem_double_click(self, event=None):
        """Navega al editor desde cualquiera de las tres pestañas de errores."""
        tab = self.active_out.get()
        if tab not in {'Errores Léxicos', 'Errores Sintácticos', 'Errores Semánticos'}:
            return
        _, view = self.out_frames[tab]
        iid = view.focus()
        location = getattr(self, '_problem_locations', {}).get((tab, iid))
        if location:
            self._goto_cps_location(*location)

    def _make_generic_tree_widget(self, parent):
        tree = ttk.Treeview(parent, columns=('detail',), show='tree headings')
        tree.heading('#0', text='Elemento')
        tree.heading('detail', text='Detalle')
        tree.column('#0', width=330, stretch=True)
        tree.column('detail', width=760, stretch=True)
        y = ttk.Scrollbar(parent, orient='vertical', command=tree.yview)
        x = ttk.Scrollbar(parent, orient='horizontal', command=tree.xview)
        tree.configure(yscrollcommand=y.set, xscrollcommand=x.set)
        tree.grid(row=0, column=0, sticky='nsew')
        y.grid(row=0, column=1, sticky='ns')
        x.grid(row=1, column=0, sticky='ew')
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        return tree

    def _populate_yalex_rules(self):
        if 'YALex Rules' not in self.out_frames:
            return
        tree = self.out_frames['YALex Rules'][1]
        tree.delete(*tree.get_children())
        text = self._get_editor('YALex')
        root_defs = tree.insert('', 'end', text='DEFINITIONS (let)', open=True)
        root_rules = tree.insert('', 'end', text='TOKEN RULES', open=True)
        if not text:
            tree.insert(root_defs, 'end', text='Sin especificación .yal', values=('Carga o escribe un archivo YALex',))
            return
        defs = re.findall('(?ms)^\\s*let\\s+([A-Za-z_]\\w*)\\s*=\\s*(.*?)(?=^\\s*let\\s+|^\\s*rule\\s+|\\Z)', text)
        for name, expr in defs:
            clean = ' '.join((line.strip() for line in expr.strip().splitlines()))
            tree.insert(root_defs, 'end', text=name, values=(clean,))
        rule_blocks = re.findall('(?ms)^\\s*rule\\s+([^=\\n]+)=\\s*(.*?)(?=^\\s*rule\\s+|\\Z)', text)
        for rname, body in rule_blocks:
            parent = tree.insert(root_rules, 'end', text=rname.strip(), values=('regla léxica',), open=True)
            for raw in body.splitlines():
                line = raw.strip()
                if not line or line.startswith('(*'):
                    continue
                token = ''
                m = re.search('\\{\\s*([^}]+)\\s*\\}', line)
                if m:
                    token = m.group(1).strip()
                tree.insert(parent, 'end', text=token or 'pattern', values=(line,))
        tree.heading('#0', text='Definición / Token')
        tree.heading('detail', text='Regex / Regla')

    def _populate_yapar_grammar(self):
        if 'Grammar YAPar' not in self.out_frames:
            return
        tree = self.out_frames['Grammar YAPar'][1]
        tree.delete(*tree.get_children())
        text = self._get_editor('YAPar')
        tok_root = tree.insert('', 'end', text='TOKENS', open=True)
        ign_root = tree.insert('', 'end', text='IGNORE', open=True)
        prod_root = tree.insert('', 'end', text='PRODUCTIONS', open=True)
        if not text:
            tree.insert(prod_root, 'end', text='Sin gramática .yapar', values=('Carga o escribe un archivo YAPar',))
            return
        try:
            yp = YAParParser(text)
            tokens_d, ignored, productions, prod_order = yp.parse()
            for tok in sorted(tokens_d):
                tree.insert(tok_root, 'end', text=tok, values=('terminal',))
            for tok in sorted(ignored):
                tree.insert(ign_root, 'end', text=tok, values=('ignorado por parser',))
            for nt in prod_order:
                parent = tree.insert(prod_root, 'end', text=nt, values=(f'{len(productions.get(nt, []))} alternativa(s)',), open=False)
                for body in productions.get(nt, []):
                    rhs = ' '.join(body) if body else 'ε'
                    tree.insert(parent, 'end', text='→', values=(rhs,))
        except Exception as e:
            tree.insert(prod_root, 'end', text='Error al leer gramática', values=(str(e),))
        tree.heading('#0', text='Símbolo')
        tree.heading('detail', text='Producción / Detalle')

    def _make_cps_tree_widget(self, parent):
        """Canvas interactivo para visualizar el parse tree de ANTLR como árbol real."""
        container = tk.Frame(parent, bg=C['bg1'])
        container.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        canvas = tk.Canvas(
            container, bg=C['bg1'], highlightthickness=0,
            xscrollincrement=1, yscrollincrement=1
        )
        yscroll = ttk.Scrollbar(container, orient='vertical', command=canvas.yview)
        xscroll = ttk.Scrollbar(container, orient='horizontal', command=canvas.xview)
        canvas.configure(xscrollcommand=xscroll.set, yscrollcommand=yscroll.set)

        canvas.grid(row=0, column=0, sticky='nsew')
        yscroll.grid(row=0, column=1, sticky='ns')
        xscroll.grid(row=1, column=0, sticky='ew')
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        canvas._tree_scale = 1.0
        canvas._tree_origin = None

        def zoom(event):
            factor = 1.12 if event.delta > 0 else 1 / 1.12
            new_scale = canvas._tree_scale * factor
            if not 0.45 <= new_scale <= 2.5:
                return
            canvas._tree_scale = new_scale
            canvas.scale('all', event.x, event.y, factor, factor)
            canvas.configure(scrollregion=canvas.bbox('all'))

        def pan_start(event):
            canvas.scan_mark(event.x, event.y)

        def pan_move(event):
            canvas.scan_dragto(event.x, event.y, gain=1)

        canvas.bind('<Control-MouseWheel>', zoom)
        canvas.bind('<ButtonPress-2>', pan_start)
        canvas.bind('<B2-Motion>', pan_move)
        canvas.bind('<Shift-MouseWheel>', lambda e: canvas.xview_scroll(-1 if e.delta > 0 else 1, 'units'))
        return canvas

    def _make_problems_widget(self, parent):
        """Panel limpio para errores léxicos, sintácticos y semánticos."""
        shell = tk.Frame(parent, bg=C['bg1'])
        shell.pack(fill=tk.BOTH, expand=True, padx=10, pady=9)

        cols = ('severity', 'line', 'col', 'message')
        tree = ttk.Treeview(shell, columns=cols, show='headings', selectmode='browse', style='Problems.Treeview')
        headers = [
            ('severity', 'ESTADO / FASE', 145, 'w'),
            ('line', 'LÍNEA', 72, 'center'),
            ('col', 'COL', 62, 'center'),
            ('message', 'DESCRIPCIÓN', 820, 'w'),
        ]
        for col, title, width, anchor in headers:
            tree.heading(col, text=title)
            tree.column(col, width=width, minwidth=55, anchor=anchor, stretch=col == 'message')

        y = ttk.Scrollbar(shell, orient='vertical', command=tree.yview)
        x = ttk.Scrollbar(shell, orient='horizontal', command=tree.xview)
        tree.configure(yscrollcommand=y.set, xscrollcommand=x.set)
        tree.grid(row=0, column=0, sticky='nsew')
        y.grid(row=0, column=1, sticky='ns')
        x.grid(row=1, column=0, sticky='ew')
        shell.grid_rowconfigure(0, weight=1)
        shell.grid_columnconfigure(0, weight=1)

        tree.tag_configure('ok', foreground=C['green'])
        tree.tag_configure('info', foreground=C['blue'])
        tree.tag_configure('lexical', foreground=C['amber'])
        tree.tag_configure('syntax', foreground=C['blue'])
        tree.tag_configure('semantic', foreground=C['red'])
        tree.tag_configure('odd', background=C['bg2'])
        tree.bind('<Double-Button-1>', self._on_problem_double_click)
        return tree

    def _make_symbols_widget(self, parent):
        """Inspector jerárquico y visual de scopes y símbolos."""
        shell = tk.Frame(parent, bg=C['bg1'])
        shell.pack(fill=tk.BOTH, expand=True, padx=10, pady=9)

        cols = ('kind', 'type', 'scope', 'line', 'details')
        tree = ttk.Treeview(shell, columns=cols, show='tree headings', selectmode='browse', style='Symbols.Treeview')
        tree.heading('#0', text='SÍMBOLO / SCOPE')
        tree.column('#0', width=260, minwidth=180, stretch=True)
        specs = [
            ('kind', 'CLASE', 115, 'center'),
            ('type', 'TIPO', 135, 'center'),
            ('scope', 'ÁMBITO', 165, 'w'),
            ('line', 'LÍNEA', 68, 'center'),
            ('details', 'DETALLES', 390, 'w'),
        ]
        for col, title, width, anchor in specs:
            tree.heading(col, text=title)
            tree.column(col, width=width, minwidth=55, anchor=anchor, stretch=col in {'#0', 'details'})

        y = ttk.Scrollbar(shell, orient='vertical', command=tree.yview)
        x = ttk.Scrollbar(shell, orient='horizontal', command=tree.xview)
        tree.configure(yscrollcommand=y.set, xscrollcommand=x.set)
        tree.grid(row=0, column=0, sticky='nsew')
        y.grid(row=0, column=1, sticky='ns')
        x.grid(row=1, column=0, sticky='ew')
        shell.grid_rowconfigure(0, weight=1)
        shell.grid_columnconfigure(0, weight=1)

        tree.tag_configure('scope', foreground=C['purple'], background=C['bg2'], font=('Consolas', 9, 'bold'))
        tree.tag_configure('function', foreground=C['blue'])
        tree.tag_configure('class', foreground=C['purple'])
        tree.tag_configure('const', foreground=C['amber'])
        tree.tag_configure('variable', foreground=C['green'])
        tree.tag_configure('parameter', foreground=C['text2'])
        return tree

    def _clear_tab(self, tab):
        _, widget = self.out_frames[tab]
        if isinstance(widget, ttk.Treeview):
            widget.delete(*widget.get_children())
        elif isinstance(widget, tk.Canvas):
            widget.delete('all')
        else:
            widget.config(state=tk.NORMAL)
            widget.delete('1.0', tk.END)
            widget.config(state=tk.DISABLED)

    def _show_cps_tree(self, tree, parser):
        """Dibuja el árbol ANTLR como un grafo jerárquico sobre Canvas."""
        tab = 'Árbol CPS'
        _, canvas = self.out_frames[tab]
        canvas.delete('all')
        canvas._tree_scale = 1.0

        node_h = 34
        level_gap = 74
        sibling_gap = 22
        padding_x = 16
        min_w = 72

        def node_info(node):
            rule_index = getattr(node, 'getRuleIndex', lambda: -1)()
            if isinstance(rule_index, int) and 0 <= rule_index < len(parser.ruleNames):
                return parser.ruleNames[rule_index], False
            text = node.getText() if hasattr(node, 'getText') else str(node)
            text = text if text else 'ε'
            if len(text) > 28:
                text = text[:25] + '...'
            return repr(text), True

        def build(node):
            label, terminal = node_info(node)
            children = []
            count = node.getChildCount() if hasattr(node, 'getChildCount') else 0
            for i in range(count):
                children.append(build(node.getChild(i)))
            width = max(min_w, len(label) * 8 + padding_x * 2)
            if children:
                children_width = sum(c['subtree_w'] for c in children) + sibling_gap * (len(children) - 1)
                subtree_w = max(width, children_width)
            else:
                subtree_w = width
            return {
                'label': label, 'terminal': terminal, 'children': children,
                'width': width, 'subtree_w': subtree_w, 'x': 0, 'y': 0
            }

        root = build(tree)

        def position(item, left, depth):
            item['y'] = 35 + depth * level_gap
            children = item['children']
            if not children:
                item['x'] = left + item['subtree_w'] / 2
                return
            total = sum(c['subtree_w'] for c in children) + sibling_gap * (len(children) - 1)
            child_left = left + (item['subtree_w'] - total) / 2
            for child in children:
                position(child, child_left, depth + 1)
                child_left += child['subtree_w'] + sibling_gap
            item['x'] = (children[0]['x'] + children[-1]['x']) / 2

        position(root, 30, 0)

        def draw_edges(item):
            for child in item['children']:
                canvas.create_line(
                    item['x'], item['y'] + node_h / 2,
                    child['x'], child['y'] - node_h / 2,
                    fill=C['border2'], width=2, smooth=True, tags='edge'
                )
                draw_edges(child)

        def draw_nodes(item):
            x, y, w = item['x'], item['y'], item['width']
            fill = C['bg3'] if not item['terminal'] else C['bg2']
            outline = C['purple'] if not item['terminal'] else C['green_dim']
            text_color = C['purple'] if not item['terminal'] else C['green']
            canvas.create_rectangle(
                x - w / 2, y - node_h / 2, x + w / 2, y + node_h / 2,
                fill=fill, outline=outline, width=2, tags='node'
            )
            canvas.create_text(
                x, y, text=item['label'], fill=text_color,
                font=('Consolas', 9, 'bold' if not item['terminal'] else 'normal'),
                tags='node'
            )
            for child in item['children']:
                draw_nodes(child)

        draw_edges(root)
        draw_nodes(root)
        canvas.tag_lower('edge')
        bbox = canvas.bbox('all')
        if bbox:
            margin = 40
            canvas.configure(scrollregion=(bbox[0] - margin, bbox[1] - margin, bbox[2] + margin, bbox[3] + margin))
            canvas.update_idletasks()
            canvas.xview_moveto(0.0)
            canvas.yview_moveto(0.0)

    def _error_location(self, err):
        """Extrae línea/columna desde atributos del error o desde su representación."""
        line = getattr(err, 'line', None)
        col = getattr(err, 'col', getattr(err, 'column', None))
        if line is None:
            msg = str(err)
            m = re.search('(?:L[ií]nea|line)\\s*(\\d+)(?::(\\d+))?', msg, re.I)
            if m:
                line = int(m.group(1))
                col = int(m.group(2)) if m.group(2) else 0
        return (line, 0 if col is None else col)

    def _show_symbol_table(self, table):
        tab = 'Símbolos'
        _, view = self.out_frames[tab]
        view.delete(*view.get_children())

        def symbol_type(sym):
            if sym.kind == 'function':
                return getattr(sym, 'return_type', None) or 'void'
            if sym.kind == 'class':
                return getattr(sym, 'type', None) or sym.name
            return getattr(sym, 'type', None) or 'any'

        def symbol_details(sym):
            if sym.kind == 'function':
                params = ', '.join((f'{n}:{t}' for n, t in getattr(sym, 'params', [])))
                return f"({params}) -> {getattr(sym, 'return_type', None) or 'void'}"
            if sym.kind == 'class':
                parent = getattr(sym, 'parent_class', None)
                return f'hereda de {parent}' if parent else 'class'
            if sym.kind == 'const' and getattr(sym, 'value', None) is not None:
                return f'valor = {sym.value!r}'
            return ''

        kind_labels = {
            'function': 'FUNCIÓN', 'class': 'CLASE', 'const': 'CONST',
            'variable': 'VARIABLE', 'var': 'VARIABLE', 'let': 'VARIABLE',
            'parameter': 'PARÁMETRO', 'param': 'PARÁMETRO',
        }

        def add_scope(scope, parent=''):
            scope_kind = str(getattr(scope, 'kind', 'scope')).upper()
            scope_id = view.insert(
                parent, 'end', text=f'▾  {scope.name}', open=True,
                values=(f'SCOPE · {scope_kind}', '', scope.name, '', f'{len(scope.symbols)} símbolo(s)'),
                tags=('scope',)
            )
            for sym in scope.symbols.values():
                line = getattr(sym, 'line', None)
                raw_kind = str(getattr(sym, 'kind', 'symbol'))
                tag = raw_kind if raw_kind in {'function', 'class', 'const'} else ('parameter' if raw_kind in {'parameter', 'param'} else 'variable')
                icon = {'function': 'ƒ', 'class': '◇', 'const': '◆', 'parameter': '·', 'variable': '●'}.get(tag, '•')
                view.insert(
                    scope_id, 'end', text=f'{icon}  {sym.name}',
                    values=(kind_labels.get(raw_kind, raw_kind.upper()), symbol_type(sym), scope.name,
                            line if line is not None else '—', symbol_details(sym)),
                    tags=(tag,)
                )
            for child in scope.children:
                add_scope(child, scope_id)
            return scope_id
        add_scope(table.global_scope)

    def _format_symbol(self, sym):
        if sym.kind == 'function':
            params = ', '.join((f'{n}:{t}' for n, t in getattr(sym, 'params', [])))
            return f"({params}) -> {getattr(sym, 'return_type', None) or 'void'}"
        if sym.kind == 'class':
            parent = getattr(sym, 'parent_class', None)
            return f"class{(' : ' + parent if parent else '')}"
        value = f' = {sym.value!r}' if sym.kind == 'const' and getattr(sym, 'value', None) is not None else ''
        return f": {getattr(sym, 'type', 'any')}{value}"

    def _write(self, tab, text, color=None):
        _, widget = self.out_frames[tab]
        if isinstance(widget, ttk.Treeview):
            widget.insert('', 'end', text=text.strip() or 'mensaje')
            return
        if isinstance(widget, tk.Canvas):
            return
        widget.config(state=tk.NORMAL)
        if color:
            tag = 'c' + color.replace('#', '')
            widget.tag_config(tag, foreground=color)
            widget.insert(tk.END, text, tag)
        else:
            widget.insert(tk.END, text)
        widget.config(state=tk.DISABLED)
        widget.see(tk.END)

    def _clear_all(self):
        for name, (_, w) in self.out_frames.items():
            if isinstance(w, ttk.Treeview):
                w.delete(*w.get_children())
            elif isinstance(w, tk.Canvas):
                w.delete('all')
            else:
                w.config(state=tk.NORMAL)
                w.delete('1.0', tk.END)
                w.config(state=tk.DISABLED)

    def _status(self, msg, kind='ok'):
        colors = {'ok': C['green'], 'error': C['red'], 'working': C['amber'], 'idle': C['text3']}
        col = colors.get(kind, C['text3'])
        self.status_icon.config(fg=col)
        self.status_lbl.config(text=str(msg).upper(), fg=col)

    def _show_ff(self, first, follow, productions):
        tree = self.out_frames['FIRST/FOLLOW'][1]
        tree.delete(*tree.get_children())
        tree.heading('#0', text='No terminal')
        tree.heading('detail', text='Conjunto')
        for nt in sorted(productions):
            node = tree.insert('', 'end', text=nt, values=('',), open=True)
            tree.insert(node, 'end', text='FIRST', values=('{ ' + ', '.join(sorted(first.get(nt, set()))) + ' }',))
            tree.insert(node, 'end', text='FOLLOW', values=('{ ' + ', '.join(sorted(follow.get(nt, set()))) + ' }',))

    def _show_lr0(self, auto):
        tree = self.out_frames['LR(0)'][1]
        tree.delete(*tree.get_children())
        tree.heading('#0', text=f'LR(0) · {len(auto.states)} estados')
        tree.heading('detail', text=f'Transiciones · {len(auto.transitions)}')
        for i, state in enumerate(auto.states):
            node = tree.insert('', 'end', text=f'Estado I{i}', values=(f'{len(state)} item(s)',), open=i < 3)
            items = tree.insert(node, 'end', text='Items', values=('',), open=i < 2)
            for item in sorted(state, key=lambda x: (x.head, x.dot)):
                tree.insert(items, 'end', text='•', values=(str(item),))
            trans = {sym: dst for (src, sym), dst in auto.transitions.items() if src == i}
            if trans:
                tr = tree.insert(node, 'end', text='GOTO', values=('',), open=i < 2)
                for sym, dst in sorted(trans.items()):
                    tree.insert(tr, 'end', text=sym, values=(f'I{dst}',))

    def _show_slr(self, table):
        self._show_lr_table('SLR(1)', table, table.automaton)

    def _show_lalr(self, table):
        self._show_lr_table('LALR', table, table.automaton)

    def _show_lr_table(self, name, table, auto):
        tree = self.out_frames[name][1]
        tree.delete(*tree.get_children())
        tree.heading('#0', text=f'{name} · ACTION/GOTO')
        tree.heading('detail', text=f'{len(table.conflicts)} conflicto(s)')
        conflicts = tree.insert('', 'end', text=f'CONFLICTS ({len(table.conflicts)})', values=('',), open=True)
        if not table.conflicts:
            tree.insert(conflicts, 'end', text='✓ Sin conflictos', values=('',))
        for c in table.conflicts:
            tree.insert(conflicts, 'end', text=f"Estado {c['state']} · {c['symbol']}", values=(c['type'],))
        states = tree.insert('', 'end', text=f'STATES ({len(auto.states)})', values=('',), open=True)
        for idx in range(len(auto.states)):
            node = tree.insert(states, 'end', text=f'Estado {idx}', values=('',), open=idx < 2)
            acts = [(sym, act) for (st, sym), act in table.action.items() if st == idx]
            gotos = [(sym, dst) for (st, sym), dst in table.goto.items() if st == idx]
            for sym, act in sorted(acts):
                if act[0] == 'SHIFT':
                    detail = f'SHIFT → {act[1]}'
                elif act[0] == 'REDUCE':
                    detail = f'REDUCE → {act[1]}'
                elif act[0] == 'ACCEPT':
                    detail = 'ACCEPT'
                else:
                    detail = str(act)
                tree.insert(node, 'end', text=f'ACTION [{sym}]', values=(detail,))
            for sym, dst in sorted(gotos):
                tree.insert(node, 'end', text=f'GOTO [{sym}]', values=(str(dst),))

    def _show_ll1(self, table):
        tree = self.out_frames['LL(1)'][1]
        tree.delete(*tree.get_children())
        tree.heading('#0', text='LL(1) · Tabla predictiva')
        tree.heading('detail', text=f'{len(table.conflicts)} conflicto(s)')
        conflicts = tree.insert('', 'end', text=f'CONFLICTS ({len(table.conflicts)})', values=('',), open=True)
        if not table.conflicts:
            tree.insert(conflicts, 'end', text='✓ Sin conflictos', values=('',))
        for c in table.conflicts[:100]:
            ex = ' '.join(c['existing']) if c['existing'] else 'ε'
            nw = ' '.join(c['new']) if c['new'] else 'ε'
            tree.insert(conflicts, 'end', text=f"M[{c['non_terminal']}][{c['terminal']}]", values=(f'{ex}  vs  {nw}',))
        rules = tree.insert('', 'end', text=f'ENTRIES ({len(table.table)})', values=('',), open=True)
        by_nt = {}
        for (nt, terminal), body in table.table.items():
            by_nt.setdefault(nt, []).append((terminal, body))
        for nt in table.prod_order:
            node = tree.insert(rules, 'end', text=nt, values=(f'{len(by_nt.get(nt, []))} entrada(s)',), open=False)
            for terminal, body in sorted(by_nt.get(nt, [])):
                rhs = ' '.join(body) if body else 'ε'
                tree.insert(node, 'end', text=terminal, values=(f'{nt} → {rhs}',))

    def _show_tokens(self, tok_list, lex_errors):
        t = 'Tokens'
        self._write(t, f'── TOKENS ──────────────────────────\n\n  total:         {len(tok_list)}\n  errores léx:   {len(lex_errors)}\n\n', C['amber'])
        for tok, lex in tok_list:
            self._write(t, f'  {tok:<28}', C['green'])
            self._write(t, f'{repr(lex)}\n', C['blue'])
        if lex_errors:
            self._write(t, '\nERRORES LÉXICOS:\n', C['red'])
            for e in lex_errors:
                self._write(t, f'  {e}\n', C['amber'])

    def _show_result(self, methods, slr_t, lalr_t, ll1_t, filtered, ignored, prod_order):
        t = 'Resultado'
        for m in methods:
            self._write(t, f'── {m.upper()} ──────────────────────────\n\n', C['amber'])
            if m == 'slr':
                engine = LRParserEngine(slr_t, ignored)
            elif m == 'lalr':
                engine = LRParserEngine(lalr_t, ignored)
            else:
                engine = LL1ParserEngine(ll1_t, prod_order[0], ignored)
            result = engine.parse(filtered)
            if result.accepted:
                self._write(t, '  ✓ ACEPTADA\n\n', C['green'])
            else:
                self._write(t, '  ✗ RECHAZADA\n\n', C['red'])
            if result.errors:
                self._write(t, f'  errores sintácticos ({len(result.errors)}):\n', C['amber'])
                for err in result.errors:
                    self._write(t, f'    • {err}\n', C['text2'])
                self._write(t, '\n')
            if self.show_steps.get() and result.steps:
                self._write(t, f'  pasos ({len(result.steps)}):\n\n', C['text3'])
                self._write(t, f"  {'pila':<32} {'entrada':<28} acción\n", C['text3'])
                self._write(t, '  ' + '─' * 85 + '\n', C['border2'])
                for step in result.steps[:300]:
                    stk = str(step['stack'])[-30:]
                    inp = str(step['input'])[:26]
                    act = step['action']
                    col = C['text2']
                    if 'SHIFT' in act:
                        col = C['green']
                    if 'REDUCE' in act:
                        col = C['purple']
                    if 'ACCEPT' in act:
                        col = C['amber']
                    if 'ERROR' in act:
                        col = C['red']
                    self._write(t, f'  {stk:<32} {inp:<28} ', C['text3'])
                    self._write(t, f'{act}\n', col)
                if len(result.steps) > 300:
                    self._write(t, f'\n  ... {len(result.steps) - 300} pasos más\n', C['text3'])
            self._write(t, '\n')

    def _style_ttk(self):
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('TScrollbar', background=C['bg3'], troughcolor=C['bg1'], bordercolor=C['border'], arrowcolor=C['green'], relief='flat')
        style.map('TScrollbar', background=[('active', C['green_dim'])])
        style.configure('Treeview', background=C['bg1'], fieldbackground=C['bg1'], foreground=C['text'], rowheight=26, borderwidth=0, relief='flat', font=FS)
        style.map('Treeview', background=[('selected', C['green_dim'])], foreground=[('selected', C['text'])])
        style.configure('Problems.Treeview', background=C['bg1'], fieldbackground=C['bg1'], foreground=C['text'], rowheight=30, borderwidth=0, relief='flat', font=('Consolas', 9))
        style.map('Problems.Treeview', background=[('selected', C['red_dim'])], foreground=[('selected', C['text'])])
        style.configure('Symbols.Treeview', background=C['bg1'], fieldbackground=C['bg1'], foreground=C['text'], rowheight=29, borderwidth=0, relief='flat', font=('Consolas', 9))
        style.map('Symbols.Treeview', background=[('selected', C['blue_dim'])], foreground=[('selected', C['text'])])
        style.configure('Treeview.Heading', background=C['bg2'], foreground=C['text2'], relief='flat', borderwidth=0, font=('Consolas', 8, 'bold'), padding=6)
        style.map('Treeview.Heading', background=[('active', C['bg3'])], foreground=[('active', C['green'])])

def main():
    app = IDE()
    app.mainloop()
if __name__ == '__main__':
    main()
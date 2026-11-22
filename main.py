"""MyAlgo IDE, By Aymen Chraf"""
import sys, os, threading, re
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from transpiler import transpile, StepExecutor, KEYWORDS, _src_line
from highlighter import AlgoHighlighter
from completer import CodeCompleter

C={"bg":"#F3F4F6","bg2":"#FFFFFF","hover":"#E5E7EB","gutter":"#F9FAFB",
   "text":"#1F2937","accent":"#3B82F6","green":"#10B981","red":"#EF4444",
   "yellow":"#F59E0B","purple":"#8B5CF6","comment":"#6B7280",
   "line":"#F3F4F6","border":"#D1D5DB","console":"#F8FAFC",
   "active_line":"#DBEAFE",
   "kw_blue":"#0000FF","kw_teal":"#008080","kw_brown":"#795E26","kw_purple":"#AF00DB"}

class LineNumberArea(QWidget):
    def __init__(s,e): super().__init__(e); s.editor=e
    def sizeHint(s): return QSize(s.editor.line_number_area_width(),0)
    def paintEvent(s,ev): s.editor.line_number_area_paint(ev)

class CodeEditor(QPlainTextEdit):
    def __init__(s,p=None):
        super().__init__(p); s._la=LineNumberArea(s)
        s.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        s._la.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        s.active_line = -1
        s._error_line = -1
        s._error_flash_visible = False
        s._error_flash_steps_remaining = 0
        s._error_flash_timer = QTimer(s)
        s._error_flash_timer.setInterval(220)
        s._error_flash_timer.timeout.connect(s._advance_error_flash)
        s.blockCountChanged.connect(s._ulw); s.updateRequest.connect(s._ula)
        s.cursorPositionChanged.connect(s._hl)
        s._completer = CodeCompleter(s)
        f=QFont("JetBrains Mono",16); f.setStyleHint(QFont.StyleHint.Monospace); s.setFont(f)
        s.setTabStopDistance(s.fontMetrics().horizontalAdvance(' ')*4)
        s.setWordWrapMode(QTextOption.WrapMode.NoWrap)
        s.setStyleSheet(f"QPlainTextEdit{{background:{C['bg']};color:{C['text']};border:none;padding-left:4px;font-family:'JetBrains Mono';}}")
        s._ulw(); s._hl()
    def line_number_area_width(s):
        return 16+s.fontMetrics().horizontalAdvance('9')*max(1,len(str(s.blockCount())))
    def _ulw(s,_=0):
        w = s.line_number_area_width()
        s.setViewportMargins(w,0,0,0)
        cr = s.contentsRect()
        s._la.setGeometry(QRect(cr.left(),cr.top(),w,cr.height()))
    def _ula(s,r,dy):
        if dy: s._la.scroll(0,dy)
        else: s._la.update(0,r.y(),s._la.width(),r.height())
        if r.contains(s.viewport().rect()): s._ulw()
    def resizeEvent(s,e):
        super().resizeEvent(e); cr=s.contentsRect()
        s._la.setGeometry(QRect(cr.left(),cr.top(),s.line_number_area_width(),cr.height()))
    def line_number_area_paint(s,ev):
        p=QPainter(s._la); p.fillRect(ev.rect(),QColor(C['gutter']))
        b=s.firstVisibleBlock(); bn=b.blockNumber()
        cl=s.textCursor().blockNumber()
        while b.isValid():
            # Compute every position from the document geometry.  Accumulating
            # rounded line heights drifts after scrolling through many lines.
            rect=s.blockBoundingGeometry(b).translated(s.contentOffset())
            top=round(rect.top())
            bottom=round(rect.bottom())
            if top > ev.rect().bottom(): break
            if b.isVisible() and bottom >= ev.rect().top():
                if s._error_flash_visible and bn == s._error_line - 1:
                    color=C['red']
                else:
                    color=C['accent'] if bn==cl else C['comment']
                p.setPen(QColor(color))
                p.setFont(s.font())
                p.drawText(0,top,s._la.width()-6,round(rect.height()),Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,str(bn+1))
            b=b.next(); bn+=1
        p.end()
    def _hl(s):
        selections = []
        if s.active_line != -1:
            sel_active = QTextEdit.ExtraSelection()
            sel_active.format.setBackground(QColor(C['active_line']))
            sel_active.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            cursor = QTextCursor(s.document().findBlockByNumber(s.active_line - 1))
            sel_active.cursor = cursor
            selections.append(sel_active)
            
        if not s.isReadOnly():
            sel = QTextEdit.ExtraSelection(); sel.format.setBackground(QColor(C['line']))
            sel.format.setProperty(QTextFormat.Property.FullWidthSelection,True)
            sel.cursor=s.textCursor(); sel.cursor.clearSelection()
            selections.append(sel)

        if s._error_flash_visible and s._error_line > 0:
            cursor = QTextCursor(s.document().findBlockByNumber(s._error_line - 1))
            if not cursor.isNull():
                sel_error = QTextEdit.ExtraSelection()
                sel_error.format.setBackground(QColor("#FCA5A5"))
                sel_error.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
                sel_error.cursor = cursor
                selections.append(sel_error)
            
        s.setExtraSelections(selections)
        
    def set_active_line(s, line_num):
        s.active_line = line_num
        s._hl()

    def flash_error_line(s, line_num):
        if not isinstance(line_num, int) or line_num < 1 or line_num > s.blockCount():
            return
        s._error_line = line_num
        s._error_flash_visible = True
        # The first visible interval plus two later visible intervals = 3 flashes.
        s._error_flash_steps_remaining = 5
        s._error_flash_timer.start()
        s._hl()
        cursor = QTextCursor(s.document().findBlockByNumber(line_num - 1))
        s.setTextCursor(cursor)
        s.centerCursor()
        s._la.update()

    def _advance_error_flash(s):
        s._error_flash_visible = not s._error_flash_visible
        s._error_flash_steps_remaining -= 1
        if s._error_flash_steps_remaining <= 0:
            s._error_flash_visible = False
            s._error_line = -1
            s._error_flash_timer.stop()
        s._hl()
        s._la.update()

    def keyPressEvent(s, e):
        if s._completer and s._completer.popup().isVisible():
            if e.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return, Qt.Key.Key_Tab):
                idx = s._completer.popup().currentIndex()
                if not idx.isValid():
                    idx = s._completer._model.index(0, 0)
                if idx.isValid():
                    s._completer.insert_selected_completion(idx)
                s._completer.popup().hide()
                e.accept()
                return
            elif e.key() == Qt.Key.Key_Escape:
                s._completer.popup().hide()
                e.accept()
                return
            elif e.key() in (Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_PageUp, Qt.Key.Key_PageDown):
                s._completer.popup().keyPressEvent(e)
                return

        is_shortcut = (e.modifiers() == Qt.KeyboardModifier.ControlModifier and e.key() == Qt.Key.Key_Space)
        super().keyPressEvent(e)

        if s._completer:
            s._completer.update_and_show(is_manual_trigger=is_shortcut)

    def mousePressEvent(s, e):
        if s._completer:
            s._completer.popup().hide()
        super().mousePressEvent(e)

    def focusOutEvent(s, e):
        super().focusOutEvent(e)
        if s._completer:
            s._completer.popup().hide()

class ConsoleWidget(QWidget):
    input_submitted=pyqtSignal(str)
    def __init__(s,p=None):
        super().__init__(p)
        ly=QVBoxLayout(s); ly.setContentsMargins(0,0,0,0); ly.setSpacing(0)
        s.output=QPlainTextEdit(); s.output.setReadOnly(True)
        s.output.setFont(QFont("JetBrains Mono",15))
        s.output.setStyleSheet(f"QPlainTextEdit{{background:{C['console']};color:{C['text']};border:none;padding:8px;border-radius:8px;font-family:'JetBrains Mono';}}")
        ly.addWidget(s.output)
        s.output.installEventFilter(s)
        s._input_start_pos = -1
        s.enter_submits = True

    def eventFilter(s, obj, ev):
        if obj == s.output and s._input_start_pos != -1:
            if ev.type() == QEvent.Type.KeyPress:
                k = ev.key()
                if k == Qt.Key.Key_Return or k == Qt.Key.Key_Enter:
                    if not s.enter_submits: return True
                    txt = s.current_input()
                    s.output.setReadOnly(True)
                    s._input_start_pos = -1
                    s.append("\n") # ensure cursor is on next line
                    s.input_submitted.emit(txt.strip())
                    return True
                # Input is append-only: history cannot be selected, changed, or
                # used as the insertion point while the program is waiting.
                s._move_input_cursor_to_end()
                if k == Qt.Key.Key_Backspace:
                    return s.output.textCursor().position() <= s._input_start_pos
                if ev.matches(QKeySequence.StandardKey.Paste):
                    return False
                if not ev.text():
                    return True
            elif ev.type() in (QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonDblClick,
                               QEvent.Type.MouseButtonRelease, QEvent.Type.MouseMove,
                               QEvent.Type.ContextMenu):
                s._move_input_cursor_to_end()
                return True
            elif ev.type() == QEvent.Type.InputMethod:
                s._move_input_cursor_to_end()
        return super().eventFilter(obj, ev)

    def _move_input_cursor_to_end(s):
        c = s.output.textCursor()
        c.clearSelection()
        c.movePosition(QTextCursor.MoveOperation.End)
        s.output.setTextCursor(c)

    def current_input(s):
        if s._input_start_pos == -1:
            return ""
        c = QTextCursor(s.output.document())
        c.setPosition(s._input_start_pos)
        c.movePosition(QTextCursor.MoveOperation.End, QTextCursor.MoveMode.KeepAnchor)
        return c.selectedText().replace("\u2029", "\n").replace("\u2028", "\n")

    def request_input(s,prompt):
        if prompt:
            s.append(prompt, C['kw_blue'])
        s.output.setReadOnly(False)
        s.output.setFocus()
        c = s.output.textCursor()
        c.movePosition(QTextCursor.MoveOperation.End)
        s.output.setTextCursor(c)
        s._input_start_pos = c.position()

    def append(s,text,color=None):
        if color is None: color = C['text']
        c = s.output.textCursor()
        c.movePosition(QTextCursor.MoveOperation.End)

        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))

        bf_rtl = QTextBlockFormat()
        bf_rtl.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        bf_rtl.setAlignment(Qt.AlignmentFlag.AlignRight)

        bf_ltr = QTextBlockFormat()
        bf_ltr.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        bf_ltr.setAlignment(Qt.AlignmentFlag.AlignLeft)

        text_str = str(text)
        if not text_str:
            return

        lines = text_str.split('\n')
        for i, line in enumerate(lines):
            stripped = line.strip().replace('\u202a', '').replace('\u202c', '').replace('\u202d', '').replace('\u202e', '').strip()
            if stripped:
                is_caret = set(stripped) <= {"^", " ", "\t", "~"}
                is_code = "▶" in line
                has_arabic = bool(re.search(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]', line))
                has_latin = bool(re.search(r'[a-zA-Z]', line))
                is_ltr = is_code or is_caret or (has_latin and not has_arabic)
                c.setBlockFormat(bf_ltr if is_ltr else bf_rtl)
            c.insertText(line, fmt)
            if i < len(lines) - 1:
                c.insertBlock()

        s.output.setTextCursor(c)
        s.output.ensureCursorVisible()

    def clear(s):
        s.output.clear()
        s._input_start_pos = -1

class ExecutionThread(QThread):
    output_sig=pyqtSignal(str)
    error_sig=pyqtSignal(str,int)
    step_done=pyqtSignal(dict,bool,int)
    input_req=pyqtSignal(str)
    def __init__(s,executor,run_all=False):
        super().__init__(); s.executor=executor; s.run_all=run_all
        s._step_ev=threading.Event(); s._input_ev=threading.Event(); s._input_val=""
        s.is_stopped = False
        
    def stop(s):
        s.is_stopped = True
        s._step_ev.set()
        s._input_ev.set()

    def run(s):
        s.executor._input_cb=s._handle_input
        class OutStream:
            def write(self_stream, t):
                s.output_sig.emit(t)
                if s.run_all and t.strip() and not s.is_stopped:
                    QThread.msleep(400)
            def flush(self_stream): pass
        s.executor.out_stream = OutStream()
        s.executor.setup()
        
        s.executor.run_debug(s._step_ev, s.run_all, s.step_done, s.error_sig, lambda: s.is_stopped)
        s.step_done.emit(s.executor.get_variables(), True, -1)
    def next_step(s): s._step_ev.set()
    def _handle_input(s,prompt):
        s.input_req.emit(str(prompt)); s._input_ev.clear(); s._input_ev.wait()
        if s.is_stopped: raise SystemExit("stopped")
        return s._input_val
    def provide_input(s,v):
        try:s._input_val=v
        except:pass
        s._input_ev.set()

SAMPLE="""Algorithme Exemple;
Variable 
x, y, somme : entier;
Début
Ecrire("أدخل العدد الأول:");
Lire(x);
Ecrire("أدخل العدد الثاني:");
Lire(y);
somme <- x + y;
Ecrire("المجموع هو:", somme);
Fin
"""

class MainWindow(QMainWindow):
    def __init__(s):
        super().__init__(); s.current_file=None; s._thread=None; s._result=None
        s._init_ui(); s._init_actions(); s._init_toolbar(); s._init_statusbar()
        s.editor.setPlainText(SAMPLE)

    def _init_ui(s):
        s.setWindowTitle("MyAlgo — محرر الخوارزميات التعليمي")
        s.setGeometry(80,80,1200,750); s.setMinimumSize(800,500)
        cw=QWidget(); s.setCentralWidget(cw)
        ml=QVBoxLayout(cw); ml.setContentsMargins(0,0,0,0); ml.setSpacing(0)
        
        hs=QSplitter(Qt.Orientation.Horizontal)
        
        # Right Side Vertical Splitter (Added first because of RTL layout)
        vs=QSplitter(Qt.Orientation.Vertical)
        
        # Console (Top Right)
        cc=QWidget(); cl=QVBoxLayout(cc); cl.setContentsMargins(0,0,0,0); cl.setSpacing(0)
        cl.addWidget(s._hdr("💻 البرنامج الناتج",C['green']))
        s.console=ConsoleWidget(); cl.addWidget(s.console)
        s.console.input_submitted.connect(s._on_input)
        vs.addWidget(cc)

        # Memory table (Bottom Right)
        mc=QWidget(); ml2=QVBoxLayout(mc); ml2.setContentsMargins(0,0,0,0); ml2.setSpacing(0)
        ml2.addWidget(s._hdr("🧠 حالة الذاكرة",C['purple']))
        s.mem_table=QTableWidget(0,3); s.mem_table.setHorizontalHeaderLabels(["المعرف","القيمة","النوع"])
        s.mem_table.horizontalHeader().setStretchLastSection(True)
        s.mem_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        s.mem_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        s.mem_table.setStyleSheet(f"""
            QTableWidget{{background:{C['bg2']};color:{C['text']};border:none;gridline-color:{C['border']};font-size:17px;border-radius:8px;}}
            QHeaderView::section{{background:{C['gutter']};color:{C['purple']};border:1px solid {C['border']};padding:8px;font-weight:bold;font-size:15px;border-radius:4px;}}
            QTableWidget::item{{padding:8px;}}""")
        ml2.addWidget(s.mem_table)
        s.step_label=QLabel(""); s.step_label.setFixedHeight(24)
        s.step_label.setStyleSheet(f"QLabel{{background:{C['gutter']};color:{C['comment']};padding:2px 8px;font-size:12px;}}")
        ml2.addWidget(s.step_label)
        vs.addWidget(mc)
        vs.setSizes([400,350])
        
        hs.addWidget(vs)

        # Editor & Sidebar Area (Added second to main splitter because of RTL layout -> goes to Left)
        ec = QWidget(); el = QHBoxLayout(ec); el.setContentsMargins(0,0,0,0); el.setSpacing(0)
        
        # 1. Editor Container (Added first to QHBoxLayout in RTL -> goes to Right of this area)
        ed_cont = QWidget(); ed_layout = QVBoxLayout(ed_cont); ed_layout.setContentsMargins(0,0,0,0); ed_layout.setSpacing(0)
        ed_layout.addWidget(s._hdr("📝 محرر الخوارزمية",C['accent']))
        s.editor = CodeEditor(); s.editor.setPlaceholderText("اكتب الخوارزمية هنا...")
        s.highlighter = AlgoHighlighter(s.editor.document()); ed_layout.addWidget(s.editor)
        el.addWidget(ed_cont)
        
        # 2. Vertical Sidebar (Added second to QHBoxLayout in RTL -> goes to Left of this area)
        sidebar = QWidget()
        sidebar.setFixedWidth(220)
        sb_outer_layout = QVBoxLayout(sidebar)
        sb_outer_layout.setContentsMargins(0,0,0,0)
        sb_outer_layout.setSpacing(0)
        
        sb_outer_layout.addWidget(s._hdr("📌 الكلمات المحجوزة",C['purple']))
        
        sb_scroll = QScrollArea()
        sb_scroll.setWidgetResizable(True)
        sb_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        sb_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        sb_scroll.setStyleSheet(f"QScrollArea{{background:{C['gutter']};border-right:1px solid {C['border']};border-top:none;border-bottom:none;border-left:none;}} QScrollBar:vertical{{background:{C['bg']};width:8px;}} QScrollBar::handle:vertical{{background:{C['border']};border-radius:4px;}} QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical{{height:0px;}}")
        
        kw_widget = QWidget()
        kw_widget.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        kw_widget.setStyleSheet("background:transparent;")
        kw_layout = QGridLayout(kw_widget)
        kw_layout.setContentsMargins(8,8,8,8)
        kw_layout.setSpacing(6)
        
        keywords = [
            # الهيكلة الأساسية
            ("Algorithme", C['kw_blue']), ("Début", C['kw_blue']),
            ("Fin", C['kw_blue']), ("<-", C['kw_purple']),
            ("Lire", C['kw_brown']), ("Ecrire", C['kw_brown']),
            
            # المتغيرات والأنواع
            ("Variable", C['kw_blue']), ("Constante", C['kw_blue']),
            ("entier", C['kw_teal']), ("réel", C['kw_teal']),
            ("chaine", C['kw_teal']), ("caractère", C['kw_teal']),
            ("booléen", C['kw_teal']), ("Tableau", C['kw_blue']),
            ("de", C['kw_blue']),
            
            # القيم المنطقية والعمليات
            ("Vrai", C['kw_blue']), ("Faux", C['kw_blue']),
            ("ET", C['kw_purple']), ("OU", C['kw_purple']),
            ("NON", C['kw_purple']),
            ("DIV", C['kw_purple']), ("MOD", C['kw_purple']),
            
            # الشروط
            ("Si", C['kw_blue']), ("Alors", C['kw_blue']),
            ("Sinon", C['kw_blue']), ("FinSi", C['kw_blue']),
            ("Selon", C['kw_blue']), ("FinSelon", C['kw_blue']),
            
            # الحلقات
            ("Pour", C['kw_blue']), ("à", C['kw_blue']),
            ("pas", C['kw_blue']), ("Faire", C['kw_blue']),
            ("FinPour", C['kw_blue']),
            ("TantQue", C['kw_blue']), ("FinTantQue", C['kw_blue']),
            ("Répéter", C['kw_blue']), ("Jusqu'à", C['kw_blue'])
        ]
        
        for i, (kw, color) in enumerate(keywords):
            # \u202D is Left-to-Right Override (LRO) which forces LTR rendering for the button text
            btn = QPushButton(f"\u202D{kw}\u202C")
            btn.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
            btn.setFont(QFont("JetBrains Mono", 13, QFont.Weight.Bold))
            btn.setStyleSheet(f"QPushButton{{background:transparent;color:{color};border:1px solid {C['border']};border-radius:4px;padding:6px;text-align:right;font-family:'JetBrains Mono';}} QPushButton:hover{{background:{C['bg']};}}")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            btn.clicked.connect(lambda checked, k=kw: (s.editor.insertPlainText(k + " "), s.editor.setFocus()))
            kw_layout.addWidget(btn, i // 2, i % 2)
            
        kw_layout.setRowStretch((len(keywords) // 2) + 1, 1)
        sb_scroll.setWidget(kw_widget)
        sb_outer_layout.addWidget(sb_scroll)
        
        el.addWidget(sidebar)
        hs.addWidget(ec)
        hs.setSizes([350, 850])
        ml.addWidget(hs)
        
        s.setStyleSheet(f"""
            QMainWindow,QWidget{{background:{C['bg']};color:{C['text']};font-family:'Cairo';}}
            QSplitter::handle{{background:{C['border']};height:2px;width:2px;}}
            QToolBar{{background:{C['bg2']};border-bottom:1px solid {C['border']};padding:6px 10px;spacing:8px;}}
            QPushButton{{background:{C['bg2']};color:{C['text']};border:1px solid {C['border']};border-radius:8px;padding:6px 16px;font-size:13px;font-weight:bold;}}
            QPushButton:hover{{background:{C['hover']};border:1px solid #9CA3AF;}}
            QPushButton:disabled{{background:{C['bg']};color:{C['comment']};border-color:{C['border']};}}
            QStatusBar{{background:{C['bg2']};color:{C['comment']};border-top:1px solid {C['border']};font-size:12px;}}
            QPlainTextEdit, QTableWidget {{background:{C['bg2']};border:1px solid {C['border']};border-radius:8px;padding:4px;}}
            QScrollArea {{border:none;}}""")

    def _hdr(s,text,color):
        l=QLabel(f"  {text}"); l.setFixedHeight(30); l.setFont(QFont("Cairo",12,QFont.Weight.Bold))
        l.setStyleSheet(f"QLabel{{background:{C['gutter']};color:{color};border-bottom:2px solid {color};padding-left:8px;}}"); return l

    def _init_actions(s):
        s.act_build_action = QAction(s); s.act_build_action.setShortcut(QKeySequence("F4")); s.act_build_action.triggered.connect(s.act_build); s.addAction(s.act_build_action)
        s.act_run_action = QAction(s); s.act_run_action.setShortcut(QKeySequence("F5")); s.act_run_action.triggered.connect(s.act_run); s.addAction(s.act_run_action)
        s.act_step_action = QAction(s); s.act_step_action.setShortcut(QKeySequence("F6")); s.act_step_action.triggered.connect(s.act_step); s.addAction(s.act_step_action)

    def _init_toolbar(s):
        tb=s.addToolBar("أدوات"); tb.setMovable(False)
        tb.setStyleSheet(f"QToolBar{{background:{C['gutter']};border-bottom:1px solid {C['border']};padding:4px 8px;spacing:6px;}}")
        
        b_new=QPushButton("📄 جديد"); b_new.clicked.connect(s.act_new); tb.addWidget(b_new)
        b_open=QPushButton("📂 فتح"); b_open.clicked.connect(s.act_open); tb.addWidget(b_open)
        b_save=QPushButton("💾 حفظ"); b_save.clicked.connect(s.act_save); tb.addWidget(b_save)
        tb.addSeparator()
        
        b_copy=QPushButton("📋 نسخ"); b_copy.clicked.connect(s.editor.copy); tb.addWidget(b_copy)
        b_paste=QPushButton("📝 لصق"); b_paste.clicked.connect(s.editor.paste); tb.addWidget(b_paste)
        tb.addSeparator()
        
        b_undo=QPushButton("↩️"); b_undo.clicked.connect(s.editor.undo); tb.addWidget(b_undo)
        b_redo=QPushButton("↪️"); b_redo.clicked.connect(s.editor.redo); tb.addWidget(b_redo)
        tb.addSeparator()
        
        s.btn_build=QPushButton("🔨 بناء (F4)"); s.btn_build.clicked.connect(s.act_build); tb.addWidget(s.btn_build)
        tb.addSeparator()
        s.btn_run=QPushButton("▶ تشغيل دفعة واحدة (F5)")
        s.btn_run.setStyleSheet(f"QPushButton{{background:{C['green']};color:{C['gutter']};border:none;border-radius:6px;padding:7px 20px;font-weight:bold;font-size:14px;}}QPushButton:hover{{background:#7EC86A;}}QPushButton:disabled{{background:{C['gutter']};color:{C['comment']};}}")
        s.btn_run.clicked.connect(s.act_run); s.btn_run.setEnabled(False); tb.addWidget(s.btn_run)
        s.btn_step=QPushButton("⏭ التعليمة الموالية (F6)")
        s.btn_step.setStyleSheet(f"QPushButton{{background:{C['yellow']};color:{C['gutter']};border:none;border-radius:6px;padding:7px 16px;font-weight:bold;font-size:13px;}}QPushButton:hover{{background:#D4B255;}}QPushButton:disabled{{background:{C['gutter']};color:{C['comment']};}}")
        s.btn_step.clicked.connect(s.act_step); s.btn_step.setEnabled(False); tb.addWidget(s.btn_step)
        s.act_run_action.setEnabled(False)
        s.act_step_action.setEnabled(False)
        tb.addSeparator()
        b4=QPushButton("🗑 إعادة تنفيذ"); b4.clicked.connect(s.act_clear); tb.addWidget(b4)
        
        sp = QWidget(); sp.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred); tb.addWidget(sp)
        b_about=QPushButton("ℹ️ حول البرنامج"); b_about.clicked.connect(s.act_about); tb.addWidget(b_about)

    def _init_statusbar(s):
        s.status=s.statusBar(); s.lbl_pos=QLabel("سطر 1 | عمود 1"); s.lbl_file=QLabel("ملف جديد")
        s.status.addWidget(s.lbl_file,1); s.status.addPermanentWidget(s.lbl_pos)
        s.editor.cursorPositionChanged.connect(lambda: s.lbl_pos.setText(
            f"سطر {s.editor.textCursor().blockNumber()+1} | عمود {s.editor.textCursor().columnNumber()+1}"))
        s.editor.textChanged.connect(s._on_text_changed)

    def _on_text_changed(s):
        s._result = None
        s.btn_run.setEnabled(False); s.btn_step.setEnabled(False)
        s.act_run_action.setEnabled(False); s.act_step_action.setEnabled(False)
        s.btn_build.setEnabled(True); s.act_build_action.setEnabled(True)

    def act_new(s):
        s._stop_exec(); s.editor.clear(); s.console.clear(); s.mem_table.setRowCount(0)
        s.current_file=None; s.lbl_file.setText("ملف جديد")
    def act_open(s):
        p,_=QFileDialog.getOpenFileName(s,"فتح","","ملفات الخوارزمية (*.algo);;الكل (*)")
        if p:
            with open(p,'r',encoding='utf-8') as f: s.editor.setPlainText(f.read())
            s.current_file=p; s.lbl_file.setText(os.path.basename(p))
    def act_save(s):
        if s.current_file:
            with open(s.current_file,'w',encoding='utf-8') as f: f.write(s.editor.toPlainText())
            s.status.showMessage("✅ تم الحفظ",3000)
        else: s.act_save_as()
    def act_save_as(s):
        p,_=QFileDialog.getSaveFileName(s,"حفظ","","ملفات الخوارزمية (*.algo);;نص (*.txt)")
        if p:
            with open(p,'w',encoding='utf-8') as f: f.write(s.editor.toPlainText())
            s.current_file=p; s.lbl_file.setText(os.path.basename(p)); s.status.showMessage("✅ تم الحفظ",3000)

    def act_build(s):
        s._stop_exec(); s.console.clear(); s.mem_table.setRowCount(0)
        code=s.editor.toPlainText().strip()
        if not code: s.console.append("⚠️ الرجاء كتابة خوارزمية أولاً.",C['yellow']); return
        result, err = transpile(code)
        if err:
            s.console.append(err,C['red']); s._result=None
            s.editor.flash_error_line(getattr(err, "line", None))
            s.btn_step.setEnabled(False); s.btn_run.setEnabled(False)
            s.act_run_action.setEnabled(False); s.act_step_action.setEnabled(False)
            s.btn_build.setEnabled(True); s.act_build_action.setEnabled(True)
        else:
            s._result=result
            s.btn_step.setEnabled(True); s.btn_run.setEnabled(True)
            s.act_run_action.setEnabled(True); s.act_step_action.setEnabled(True)
            s.btn_build.setEnabled(False); s.act_build_action.setEnabled(False)
            s.console.append(f"✅ تم بناء الخوارزمية بنجاح ({len(result['steps'])} تعليمة).",C['green'])
            s._update_mem_initial(result)
            s.step_label.setText(f"جاهز للتنفيذ.")
            s.status.showMessage("✅ البناء ناجح",3000)

    def act_run(s):
        s._stop_exec()
        if not s._result: s.console.append("⚠️ الرجاء بناء الخوارزمية أولاً.",C['yellow']); return
        result = s._result
        s.console.clear(); s.mem_table.setRowCount(0)
        s.console.append("⏳ جاري التنفيذ...\n",C['accent'])
        s.console.enter_submits = True
        s.btn_run.setEnabled(False); s.btn_step.setEnabled(False)
        s.editor.setReadOnly(True)
        executor=StepExecutor(result)
        s._thread=ExecutionThread(executor,run_all=True)
        s._thread.output_sig.connect(lambda t: s.console.append(t,C['text']))
        s._thread.error_sig.connect(s._on_runtime_error)
        s._thread.step_done.connect(s._on_step_done)
        s._thread.input_req.connect(s.console.request_input)
        s._thread.start()

    def act_step(s):
        if s._thread and s._thread.isRunning():
            if s.console._input_start_pos != -1:
                txt = s.console.current_input().strip()
                if not txt: return
                s.console.output.setReadOnly(True)
                s.console._input_start_pos = -1
                s.console.append("\n")
                s.console.input_submitted.emit(txt)
                return
            s._thread.next_step(); return
        if not s._result:
            s.console.append("⚠️ قم ببناء الخوارزمية أولاً (F4).",C['yellow']); return
        s.console.clear(); s.mem_table.setRowCount(0)
        s.console.enter_submits = False
        s.console.append("⏭ وضع التنفيذ خطوة بخطوة\n",C['accent'])
        s.btn_run.setEnabled(False)
        s.editor.setReadOnly(True)
        executor=StepExecutor(s._result)
        s._thread=ExecutionThread(executor,run_all=False)
        s._thread.output_sig.connect(lambda t: s.console.append(t,C['text']))
        s._thread.error_sig.connect(s._on_runtime_error)
        s._thread.step_done.connect(s._on_step_done)
        s._thread.input_req.connect(s.console.request_input)
        s._thread.start()

    def act_clear(s):
        s._stop_exec(); s.console.clear(); s.mem_table.setRowCount(0)
        s.step_label.setText("")

    def act_about(s):
        dlg = QDialog(s)
        dlg.setWindowTitle("حول البرنامج")
        dlg.setFixedWidth(450)
        dlg.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.MSWindowsFixedSizeDialogHint)
        dlg.setStyleSheet(f"QDialog {{ background: {C['bg2']}; }}")
        
        layout = QVBoxLayout(dlg)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        layout.setContentsMargins(30, 30, 30, 30)
        
        logo = QLabel()
        pix_path = resource_path(os.path.join("img", "log.png"))
        pix = QPixmap(pix_path)
        if not pix.isNull():
            logo.setPixmap(pix.scaled(140, 140, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo)
        
        t = QLabel("من تطوير الأستاذ\nشرف أيمن")
        t.setFont(QFont("Cairo", 22, QFont.Weight.Bold))
        t.setStyleSheet(f"color: {C['kw_blue']};")
        t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(t)
        
        sub = QLabel("الإصدار 0.6 (نسخة beta)")
        sub.setFont(QFont("Cairo", 13))
        sub.setStyleSheet(f"color: {C['red']}; font-weight: bold; margin-bottom: 15px;")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(sub)
        
        desc = QLabel(
            "<div style='text-align:center;'>"
            "<p style='margin-bottom:15px;'>هذا البرنامج لا يزال قيد التطوير .<br/><b>يُرجى عدم استخدامه في التدريس حالياً</b> لأنه قد يحتوي على أخطاء.</p>"
            "<p style='color:#6B7280; font-size:14px;'>للإبلاغ عن أي مشكلة، يرجى التواصل عبر البريد الإلكتروني:<br/>"
            f"<a href='mailto:aymen.chraf@gmail.com' style='color:{C['accent']}; text-decoration:none; font-weight:bold;'>aymen.chraf@gmail.com</a></p>"
            "</div>"
        )
        desc.setFont(QFont("Cairo", 12))
        desc.setWordWrap(True)
        desc.setOpenExternalLinks(True)
        desc.setStyleSheet(f"color: {C['text']};")
        layout.addWidget(desc)
        
        btn = QPushButton("حسناً، فهمت")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"QPushButton{{background:{C['kw_blue']}; color:white; border-radius:8px; padding:10px 40px; font-weight:bold; font-size:15px; margin-top:20px;}} QPushButton:hover{{background:#2563EB;}}")
        btn.clicked.connect(dlg.accept)
        bl = QHBoxLayout()
        bl.addStretch(); bl.addWidget(btn); bl.addStretch()
        layout.addLayout(bl)
        
        dlg.exec()

    def _stop_exec(s):
        if s._thread and s._thread.isRunning():
            s._thread.stop()
            if not s._thread.wait(500):
                s._thread.terminate()
                s._thread.wait(500)
        s._thread=None; s.btn_run.setEnabled(True); s.btn_step.setEnabled(bool(s._result))
        s.editor.setReadOnly(False)
        s.editor.set_active_line(-1)

    def _on_input(s,val):
        if s._thread: s._thread.provide_input(val)

    def _on_runtime_error(s, message, line_num):
        formatted = message
        if line_num and line_num > 0:
            code = s.editor.toPlainText()
            src = _src_line(code, line_num)
            if src and src not in formatted:
                formatted = f"⛔ خطأ في وقت التنفيذ في السطر {line_num}:\n\u202A   ▶ {src}\u202C\n" + message
        s.console.append(formatted, C['red'])
        s.editor.flash_error_line(line_num)

    def _on_step_done(s,variables,finished,line):
        s._update_mem(variables)
        if line != -1:
            s.editor.set_active_line(line)
        if s._thread and line != -1:
            s.step_label.setText(f"يتم تنفيذ السطر: {line}")
        if finished:
            s.console.append("\n✅ انتهى التنفيذ.",C['green'])
            s.btn_run.setEnabled(True); s.btn_step.setEnabled(bool(s._result))
            s.editor.setReadOnly(False)
            s.editor.set_active_line(-1)

    def _update_mem(s,variables):
        s.mem_table.setRowCount(len(variables))
        for r,(name,info) in enumerate(variables.items()):
            s.mem_table.setItem(r,0,QTableWidgetItem(name))
            vi=QTableWidgetItem(str(info['value']))
            vi.setForeground(QColor(C['green']))
            vi.setFont(QFont("JetBrains Mono", 16, QFont.Weight.Bold))
            s.mem_table.setItem(r,1,vi)
            s.mem_table.setItem(r,2,QTableWidgetItem(info['type']))

    def _update_mem_initial(s,result):
        v=result['variables']
        s.mem_table.setRowCount(len(v))
        defaults={"entier":"0","réel":"0.0","reel":"0.0","caractère":"''","caractere":"''",
                   "chaine de caractères":"''","chaine de caracteres":"''","chaine":"''",
                   "booléen":"False","booleen":"False"}
        for r,(name,tp) in enumerate(v.items()):
            s.mem_table.setItem(r,0,QTableWidgetItem(name))
            if tp == "ثابت" and name in result.get('constants', {}):
                vi=QTableWidgetItem(result['constants'][name])
                vi.setForeground(QColor(C['purple']))
            else:
                vi=QTableWidgetItem(defaults.get(tp,"0"))
                vi.setForeground(QColor(C['comment']))
            vi.setFont(QFont("JetBrains Mono", 16, QFont.Weight.Bold))
            s.mem_table.setItem(r,1,vi)
            s.mem_table.setItem(r,2,QTableWidgetItem(tp))

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

if __name__=="__main__":
    app=QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path(os.path.join("img", "log.png"))))
    QFontDatabase.addApplicationFont(resource_path(os.path.join("fonts", "Cairo-Regular.ttf")))
    QFontDatabase.addApplicationFont(resource_path(os.path.join("fonts", "Cairo-Bold.ttf")))
    QFontDatabase.addApplicationFont(resource_path(os.path.join("fonts", "JetBrainsMono-Regular.ttf")))
    app.setFont(QFont("Cairo", 11))
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft); app.setStyle("Fusion")
    p=app.palette()
    p.setColor(QPalette.ColorRole.Window,QColor(C['bg']))
    p.setColor(QPalette.ColorRole.WindowText,QColor(C['text']))
    p.setColor(QPalette.ColorRole.Base,QColor(C['bg']))
    p.setColor(QPalette.ColorRole.Text,QColor(C['text']))
    p.setColor(QPalette.ColorRole.Button,QColor(C['hover']))
    p.setColor(QPalette.ColorRole.ButtonText,QColor(C['text']))
    p.setColor(QPalette.ColorRole.Highlight,QColor(C['accent']))
    p.setColor(QPalette.ColorRole.HighlightedText,QColor("white"))
    app.setPalette(p)
    w=MainWindow(); w.showMaximized(); sys.exit(app.exec())

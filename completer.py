"""
MyAlgo IDE - مساعد الكتابة والإكمال التلقائي الذكي
Smart Code Completion Assistant for MyAlgo IDE
"""

import re
import unicodedata
from PyQt6.QtWidgets import (QCompleter, QStyledItemDelegate, QStyle)
from PyQt6.QtGui import (QStandardItemModel, QStandardItem, QTextCursor, 
                         QPainter, QColor, QFont)
from PyQt6.QtCore import Qt, QRect, QSize, QModelIndex

ROLE_INSERT_TEXT = Qt.ItemDataRole.UserRole + 1
ROLE_KIND = Qt.ItemDataRole.UserRole + 2

KIND_STYLES = {
    'structure':   ('#8B5CF6', '{}', 'بنية'),    # Purple
    'instruction': ('#0D9488', 'fx', 'تعليمة'), # Teal
    'variable':    ('#10B981', 'var', 'متغير'), # Green
    'constant':    ('#F59E0B', 'cst', 'ثابت'),  # Amber
    'type':        ('#3B82F6', 'type', 'نوع'),  # Blue
    'function':    ('#D97706', 'fn', 'دالة'),   # Brown
    'keyword':     ('#64748B', 'kw', 'ك م'),   # Slate
}

def strip_accents(s):
    """إزالة التشكيل وحركات الأحرف لتسهيل المطابقة المرنة"""
    if not s:
        return ""
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

STATIC_COMPLETIONS = [
    # ── بنى التحكم والخوارزمية (Structures) ──
    # تُقترح فقط وفقط عند كتابة بداية الكلمة الافتتاحية للبنية
    {
        'name': 'Si ... Alors ... FinSi',
        'insert': 'Si __CURSOR__ Alors\n    \nFinSi',
        'kind': 'structure',
        'opening': 'si',
    },
    {
        'name': 'Si ... Alors ... Sinon ... FinSi',
        'insert': 'Si __CURSOR__ Alors\n    \nSinon\n    \nFinSi',
        'kind': 'structure',
        'opening': 'si',
    },
    {
        'name': 'Pour ... à ... Faire ... FinPour',
        'insert': 'Pour __CURSOR__ <- 1 à 10 Faire\n    \nFinPour',
        'kind': 'structure',
        'opening': 'pour',
    },
    {
        'name': 'TantQue ... Faire ... FinTantQue',
        'insert': 'TantQue __CURSOR__ Faire\n    \nFinTantQue',
        'kind': 'structure',
        'opening': 'tantque',
    },
    {
        'name': 'Répéter ... Jusqu\'à',
        'insert': 'Répéter\n    __CURSOR__\nJusqu\'à ;',
        'kind': 'structure',
        'opening': 'repeter',
    },
    {
        'name': 'Selon ... Cas ... FinSelon',
        'insert': 'Selon __CURSOR__ Faire\n    Cas 1:\n        \n    Sinon:\n        \nFinSelon',
        'kind': 'structure',
        'opening': 'selon',
    },
    {
        'name': 'Tableau[1..N] de type',
        'insert': 'Tableau[1..__CURSOR__] de entier;',
        'kind': 'structure',
        'opening': 'tableau',
    },
    {
        'name': 'Algorithme ... Début ... Fin',
        'insert': 'Algorithme __CURSOR__;\nVariable\n    \nDébut\n    \nFin',
        'kind': 'structure',
        'opening': 'algorithme',
    },

    # ── تعليمات الإدخال والإخراج والعمليات (Instructions) ──
    {
        'name': 'Ecrire(...)',
        'insert': 'Ecrire(__CURSOR__);',
        'kind': 'instruction',
        'keywords': ['ecrire', 'afficher']
    },
    {
        'name': 'Lire(...)',
        'insert': 'Lire(__CURSOR__);',
        'kind': 'instruction',
        'keywords': ['lire']
    },
    {
        'name': '<-',
        'insert': ' <- __CURSOR__',
        'kind': 'instruction',
        'keywords': ['assign', '<-']
    },

    # ── دوال مدمجة (Functions) ──
    {'name': 'abs(...)', 'insert': 'abs(__CURSOR__)', 'kind': 'function', 'keywords': ['abs']},
    {'name': 'racine(...)', 'insert': 'racine(__CURSOR__)', 'kind': 'function', 'keywords': ['racine', 'sqrt']},
    {'name': 'ent(...)', 'insert': 'ent(__CURSOR__)', 'kind': 'function', 'keywords': ['ent', 'int']},
    {'name': 'long(...)', 'insert': 'long(__CURSOR__)', 'kind': 'function', 'keywords': ['long', 'len']},

    # ── الكلمات المحجوزة الأساسية (Keywords) ──
    {'name': 'Algorithme', 'insert': 'Algorithme __CURSOR__;', 'kind': 'keyword', 'keywords': ['algorithme']},
    {'name': 'Variable', 'insert': 'Variable\n    __CURSOR__', 'kind': 'keyword', 'keywords': ['variable', 'var']},
    {'name': 'Constante', 'insert': 'Constante\n    __CURSOR__', 'kind': 'keyword', 'keywords': ['constante', 'const']},
    {'name': 'Début', 'insert': 'Début\n    __CURSOR__', 'kind': 'keyword', 'keywords': ['debut']},
    {'name': 'Fin', 'insert': 'Fin', 'kind': 'keyword', 'keywords': ['fin']},
    {'name': 'Si', 'insert': 'Si ', 'kind': 'keyword', 'keywords': ['si']},
    {'name': 'Alors', 'insert': 'Alors\n    __CURSOR__', 'kind': 'keyword', 'keywords': ['alors']},
    {'name': 'Sinon', 'insert': 'Sinon\n    __CURSOR__', 'kind': 'keyword', 'keywords': ['sinon']},
    {'name': 'FinSi', 'insert': 'FinSi', 'kind': 'keyword', 'keywords': ['finsi']},
    {'name': 'Pour', 'insert': 'Pour ', 'kind': 'keyword', 'keywords': ['pour']},
    {'name': 'Faire', 'insert': 'Faire\n    __CURSOR__', 'kind': 'keyword', 'keywords': ['faire']},
    {'name': 'FinPour', 'insert': 'FinPour', 'kind': 'keyword', 'keywords': ['finpour']},
    {'name': 'TantQue', 'insert': 'TantQue ', 'kind': 'keyword', 'keywords': ['tantque', 'tant que']},
    {'name': 'FinTantQue', 'insert': 'FinTantQue', 'kind': 'keyword', 'keywords': ['fintantque']},
    {'name': 'Répéter', 'insert': 'Répéter\n    __CURSOR__', 'kind': 'keyword', 'keywords': ['repeter']},
    {'name': 'Jusqu\'à', 'insert': 'Jusqu\'à ', 'kind': 'keyword', 'keywords': ['jusqua']},
    {'name': 'Selon', 'insert': 'Selon ', 'kind': 'keyword', 'keywords': ['selon']},
    {'name': 'Cas', 'insert': 'Cas __CURSOR__:', 'kind': 'keyword', 'keywords': ['cas']},
    {'name': 'FinSelon', 'insert': 'FinSelon', 'kind': 'keyword', 'keywords': ['finselon']},
    {'name': 'Tableau', 'insert': 'Tableau', 'kind': 'keyword', 'keywords': ['tableau']},
    {'name': 'de', 'insert': 'de ', 'kind': 'keyword', 'keywords': ['de']},
    {'name': 'pas', 'insert': 'pas ', 'kind': 'keyword', 'keywords': ['pas']},
    {'name': 'à', 'insert': 'à ', 'kind': 'keyword', 'keywords': ['a']},

    # ── أنواع البيانات (Data Types) ──
    {'name': 'entier', 'insert': 'entier', 'kind': 'type', 'keywords': ['entier', 'int']},
    {'name': 'réel', 'insert': 'réel', 'kind': 'type', 'keywords': ['reel', 'float']},
    {'name': 'chaine', 'insert': 'chaine', 'kind': 'type', 'keywords': ['chaine', 'string']},
    {'name': 'caractère', 'insert': 'caractère', 'kind': 'type', 'keywords': ['caractere', 'char']},
    {'name': 'booléen', 'insert': 'booléen', 'kind': 'type', 'keywords': ['booleen', 'bool']},

    # ── القيم المنطقية والمعاملات الحسابية ──
    {'name': 'Vrai', 'insert': 'Vrai', 'kind': 'keyword', 'keywords': ['vrai', 'true']},
    {'name': 'Faux', 'insert': 'Faux', 'kind': 'keyword', 'keywords': ['faux', 'false']},
    {'name': 'DIV', 'insert': 'DIV ', 'kind': 'keyword', 'keywords': ['div']},
    {'name': 'MOD', 'insert': 'MOD ', 'kind': 'keyword', 'keywords': ['mod']},
    {'name': 'ET', 'insert': 'ET ', 'kind': 'keyword', 'keywords': ['et', 'and']},
    {'name': 'OU', 'insert': 'OU ', 'kind': 'keyword', 'keywords': ['ou', 'or']},
    {'name': 'NON', 'insert': 'NON ', 'kind': 'keyword', 'keywords': ['non', 'not']},
]

def extract_variables_and_constants(code):
    """استخراج المتغيرات والثوابت المُصرّح عنها أو المستخدمة في الكود"""
    vars_found = set()
    consts_found = set()
    
    keywords = {
        "algorithme", "début", "debut", "fin", "variable", "var", "constante", "const",
        "entier", "réel", "reel", "caractère", "caractere", "chaine", "booléen", "booleen", "tableau",
        "si", "alors", "sinon", "finsi", "pour", "faire", "finpour", "tantque", "fintantque",
        "répéter", "repeter", "jusqu'à", "jusqu'a", "jusqua", "selon", "cas", "finselon",
        "lire", "ecrire", "écrire", "et", "ou", "non", "vrai", "faux", "div", "mod", "de", "pas", "à", "a"
    }

    # 1. استخراج من قسم Variable
    var_match = re.search(r'\b(?:Variable|Var)\b(.*?)(?=\b(?:Début|Debut|Constante|Const)\b|$)', code, re.IGNORECASE | re.DOTALL)
    if var_match:
        for line in var_match.group(1).split('\n'):
            line = line.strip()
            if '//' in line:
                line = line[:line.find('//')].strip()
            if ':' in line:
                left, _ = line.split(':', 1)
                for v in left.split(','):
                    name = v.strip()
                    if name and re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name) and name.lower() not in keywords:
                        vars_found.add(name)

    # 2. استخراج من قسم Constante
    const_match = re.search(r'\b(?:Constante|Const)\b(.*?)(?=\b(?:Début|Debut|Variable|Var)\b|$)', code, re.IGNORECASE | re.DOTALL)
    if const_match:
        for line in const_match.group(1).split('\n'):
            line = line.strip()
            if '//' in line:
                line = line[:line.find('//')].strip()
            for sep in ['<-', '=']:
                if sep in line:
                    left, _ = line.split(sep, 1)
                    name = left.strip()
                    if name and re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name) and name.lower() not in keywords:
                        consts_found.add(name)
                    break

    # 3. استخراج من عمليات الإسناد المباشرة
    for m in re.finditer(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*<-', code):
        name = m.group(1)
        if name.lower() not in keywords and name not in consts_found:
            vars_found.add(name)

    # 4. استخراج من تعليمات القراءة
    for m in re.finditer(r'\b(?:Lire|lire)\s*\(\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\)', code):
        name = m.group(1)
        if name.lower() not in keywords and name not in consts_found:
            vars_found.add(name)

    return vars_found, consts_found

def process_template(template, base_indent=""):
    """تنسيق القالب البرمجي مع إزاحة السطور وتحديد موضع المؤشر __CURSOR__"""
    lines = template.split('\n')
    indented = [lines[0]]
    for l in lines[1:]:
        indented.append(base_indent + l if l else base_indent)
    full_str = '\n'.join(indented)
    
    marker = '__CURSOR__'
    cursor_idx = full_str.find(marker)
    if cursor_idx != -1:
        clean_text = full_str[:cursor_idx] + full_str[cursor_idx+len(marker):]
        return clean_text, cursor_idx
    else:
        return full_str, len(full_str)

class CleanCompletionDelegate(QStyledItemDelegate):
    """تصميم أنيق، مريح وبسيط لعناصر الإكمال التلقائي دون تفاصيل مفرطة"""
    def sizeHint(self, option, index):
        return QSize(option.rect.width(), 28)

    def paint(self, painter, option, index):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        
        rect = option.rect
        is_selected = bool(option.state & QStyle.StateFlag.State_Selected)
        is_hover = bool(option.state & QStyle.StateFlag.State_MouseOver)
        
        # 1. الخلفية وشريط التمييز الأيسر
        if is_selected:
            painter.fillRect(rect, QColor("#EFF6FF")) # أزرق ثلجي ناعم جداً
            painter.fillRect(QRect(rect.left(), rect.top(), 3, rect.height()), QColor("#3B82F6"))
        elif is_hover:
            painter.fillRect(rect, QColor("#F8FAFC")) # رمادي خفيف عند تمرير الفأرة
        else:
            painter.fillRect(rect, QColor("#FFFFFF"))
            
        kind = index.data(ROLE_KIND) or 'keyword'
        color_hex, sym, label = KIND_STYLES.get(kind, ('#64748B', '•', ''))
        
        # 2. رمز تصنيف دقيق وبسيط على اليسار
        sym_rect = QRect(rect.left() + 6, rect.top(), 28, rect.height())
        painter.setFont(QFont("JetBrains Mono", 9, QFont.Weight.Bold))
        painter.setPen(QColor(color_hex))
        painter.drawText(sym_rect, Qt.AlignmentFlag.AlignLeft, sym)
        
        # 3. اسم العنصر بوضوح مع مساحة كافية لتفادي الاقتصاص
        name = index.data(Qt.ItemDataRole.DisplayRole) or ''
        name_rect = QRect(rect.left() + 20, rect.top(), max(0, rect.width() - 40), rect.height())
        painter.setFont(QFont("JetBrains Mono", 11, QFont.Weight.DemiBold if is_selected else QFont.Weight.Normal))
        painter.setPen(QColor("#1D4ED8" if is_selected else "#0F172A"))
        painter.drawText(name_rect, Qt.AlignmentFlag.AlignLeft, name)
        
        # 4. تصنيف عربي مقتضب على اليمين (دون جمل طويلة مشوشة)
        #tag_rect = QRect(rect.right() - 60, rect.top(), 52, rect.height())
        #painter.setFont(QFont("Cairo", 10))
        #painter.setPen(QColor("#2563EB" if is_selected else "#94A3B8"))
        #painter.drawText(tag_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, label)
        
        painter.restore()

class CodeCompleter(QCompleter):
    """محرك الإكمال التلقائي الذكي لمحرر الخوارزميات"""
    def __init__(self, editor):
        self._model = QStandardItemModel(editor)
        super().__init__(self._model, editor)
        self.editor = editor
        self.setWidget(editor)
        self.setCompletionMode(QCompleter.CompletionMode.UnfilteredPopupCompletion)
        
        popup = self.popup()
        popup.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        # الاحتفاظ بمرجع دائم للمفوّض (Delegate) في خاصية الكائن لتفادي حذفه من مجمّع القمامة في بايثون
        self._delegate = CleanCompletionDelegate(popup)
        popup.setItemDelegate(self._delegate)
        popup.setMinimumWidth(320)
        popup.setStyleSheet("""
            QListView {
                background-color: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 4px 0px;
                outline: none;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 6px;
                margin: 2px;
            }
            QScrollBar::handle:vertical {
                background: #CBD5E1;
                min-height: 20px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical:hover {
                background: #94A3B8;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        self.activated.connect(self._on_activated)

    def _on_activated(self, text):
        idx = self.popup().currentIndex()
        if idx.isValid():
            self.insert_selected_completion(idx)

    def is_in_string_or_comment(self):
        """التحقق مما إذا كان المؤشر داخل نص تنصيص أو تعليق برمجياً"""
        tc = self.editor.textCursor()
        block_text = tc.block().text()
        col = tc.positionInBlock()
        before_cursor = block_text[:col]
        
        if '//' in before_cursor:
            return True
            
        quotes = before_cursor.count('"') + before_cursor.count("'")
        return (quotes % 2) != 0

    def update_and_show(self, is_manual_trigger=False):
        """تحديث قائمة الاقتراحات وإظهار القائمة إذا توفرت نتائج"""
        if self.is_in_string_or_comment() and not is_manual_trigger:
            self.popup().hide()
            return

        tc = self.editor.textCursor()
        tc.select(QTextCursor.SelectionType.WordUnderCursor)
        prefix = tc.selectedText()
        
        # الشرط: حرفين على الأقل تلقائياً، أو استدعاء يدوي
        if len(prefix) < 2 and not is_manual_trigger:
            self.popup().hide()
            return
            
        norm_prefix = strip_accents(prefix).lower()
        candidates = []
        
        # 1. مطابقة العناصر الثابتة (مع التقيد الصارم بقاعدة الكلمة الافتتاحية للبنى)
        for item in STATIC_COMPLETIONS:
            kind = item.get('kind', 'keyword')
            matched = False
            priority = 999
            
            if kind == 'structure':
                # البنية الكاملة تُقترح فقط وفقط إذا بدأت بالكلمة الافتتاحية للبنية
                # الكلمات في منتصف البنية أو آخرها لا تقترح البنية الكاملة أبداً
                opening = item.get('opening', '')
                if opening.startswith(norm_prefix):
                    matched = True
                    priority = 1
            else:
                norm_name = strip_accents(item['name']).lower()
                if norm_name.startswith(norm_prefix):
                    matched = True
                    priority = 0 if kind in ('instruction', 'function') else 2
                elif any(strip_accents(kw).lower().startswith(norm_prefix) for kw in item.get('keywords', [])):
                    matched = True
                    priority = 3
                    
            if matched or (is_manual_trigger and not norm_prefix):
                candidates.append((priority, item['name'], item['insert'], kind))
                
        # 2. استخراج ومطابقة المتغيرات والثوابت من شيفرة المستخدم بأولوية عليا
        code = self.editor.toPlainText()
        vars_found, consts_found = extract_variables_and_constants(code)
        
        for v in sorted(vars_found):
            norm_v = strip_accents(v).lower()
            if norm_v.startswith(norm_prefix):
                candidates.append((0, v, v, 'variable'))
            elif is_manual_trigger and not norm_prefix:
                candidates.append((0, v, v, 'variable'))
                
        for c in sorted(consts_found):
            norm_c = strip_accents(c).lower()
            if norm_c.startswith(norm_prefix):
                candidates.append((0, c, c, 'constant'))
            elif is_manual_trigger and not norm_prefix:
                candidates.append((0, c, c, 'constant'))

        # ترتيب النتائج بالأولوية ثم أبجدياً
        candidates.sort(key=lambda x: (x[0], x[1].lower()))
        
        self._model.clear()
        for score, name, insert_str, kind in candidates:
            row_item = QStandardItem(name)
            row_item.setData(name, Qt.ItemDataRole.DisplayRole)
            row_item.setData(insert_str, ROLE_INSERT_TEXT)
            row_item.setData(kind, ROLE_KIND)
            self._model.appendRow(row_item)
            
        if self._model.rowCount() > 0:
            from PyQt6.QtGui import QFontMetrics
            fm = QFontMetrics(QFont("JetBrains Mono", 10))
            max_w = max((fm.horizontalAdvance(c[1]) for c in candidates), default=180)
            ideal_w = max(340, min(520, max_w + 120))
            self.popup().setFixedWidth(ideal_w)
            cr = self.editor.cursorRect()
            cr.setWidth(ideal_w)
            self.complete(cr)
            self.popup().setCurrentIndex(self._model.index(0, 0))
        else:
            self.popup().hide()

    def insert_selected_completion(self, index):
        """إدراج العنصر المختار مع تنسيق الإزاحة وضبط موضع المؤشر الذكي"""
        insert_text = index.data(ROLE_INSERT_TEXT)
        if not insert_text:
            insert_text = index.data(Qt.ItemDataRole.DisplayRole)
            
        tc = self.editor.textCursor()
        
        # معرفة المسافة البادئة للسطر الحالي
        block_text = tc.block().text()
        base_indent = ""
        for ch in block_text:
            if ch in (' ', '\t'):
                base_indent += ch
            else:
                break
                
        # تحديد الكلمة الحالية لاستبدالها
        tc.select(QTextCursor.SelectionType.WordUnderCursor)
        start_pos = tc.selectionStart()
        
        # معالجة القالب وضبط المؤشر
        final_text, cursor_offset = process_template(insert_text, base_indent)
        tc.insertText(final_text)
        
        # وضع المؤشر في الموضع المطلوب داخل الكود
        tc.setPosition(start_pos + cursor_offset)
        self.editor.setTextCursor(tc)
        self.popup().hide()

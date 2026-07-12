"""
MyAlgo - تلوين الكلمات المفتاحية الخوارزمية
Syntax Highlighter for French Algorithmic Language
"""

from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PyQt6.QtCore import QRegularExpression


class AlgoHighlighter(QSyntaxHighlighter):
    """ملوّن نحوي للخوارزميات الفرنسية الأكاديمية"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rules = []
        self._setup_rules()

    def _fmt(self, color, bold=False, italic=False):
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        if bold:
            fmt.setFontWeight(QFont.Weight.Bold)
        if italic:
            fmt.setFontItalic(True)
        return fmt

    def _setup_rules(self):
        def _add_rules(patterns, fmt):
            for pat in patterns:
                rx = QRegularExpression(pat)
                rx.setPatternOptions(QRegularExpression.PatternOption.CaseInsensitiveOption)
                self._rules.append((rx, fmt))

        # ── كلمات البنية الرئيسية ──
        struct_keywords = [
            r'\balgorithme\b', r'\bdébut\b', r'\bdebut\b', r'\bfin\b',
            r'\bvariable\b', r'\bvar\b', r'\bconstante\b', r'\bconst\b'
        ]
        _add_rules(struct_keywords, self._fmt("#0000FF", bold=True))

        # ── كلمات التحكم ──
        control_keywords = [
            r'\bsi\b', r'\balors\b', r'\bsinon\b',
            r'\bfinsi\b',
            r'\bpour\b', r'\bfaire\b', r'\bfinpour\b',
            r'\btant que\b', r'\btantque\b', r'\bfintantque\b',
            r'\brépéter\b', r'\brepeter\b',
            r'\bjusqu\'à\b', r'\bjusqu\'a\b', r'\bjusqua\b',
            r'\bselon\b', r'\bcas\b', r'\bfinselon\b', r'\bautrement\b',
            r'\bà\b', r'\ba\b'
        ]
        _add_rules(control_keywords, self._fmt("#0000FF", bold=True))

        # ── أنواع البيانات ──
        type_keywords = [
            r'\bentier\b', r'\bréel\b', r'\breel\b',
            r'\bcaractère\b', r'\bcaractere\b',
            r'\bchaine de caractères\b', r'\bchaine de caracteres\b', r'\bchaine\b',
            r'\bbooléen\b', r'\bbooleen\b',
            r'\btableau\b', r'\bde\b'
        ]
        _add_rules(type_keywords, self._fmt("#008080", bold=False, italic=True))

        # ── دوال مدمجة ──
        builtin_keywords = [
            r'\blire\b', r'\becrire\b', r'\bécrire\b', r'\babs\b', r'\bracine\b', r'\bent\b', r'\blong\b'
        ]
        _add_rules(builtin_keywords, self._fmt("#795E26", bold=True))

        # ── العوامل المنطقية ──
        logic_keywords = [r'\bet\b', r'\bou\b', r'\bnon\b']
        _add_rules(logic_keywords, self._fmt("#AF00DB", bold=True))

        # ── القيم المنطقية ──
        bool_keywords = [r'\bvrai\b', r'\bfaux\b']
        _add_rules(bool_keywords, self._fmt("#0000FF", bold=True))

        # ── DIV / MOD ──
        op_keywords = [r'\bdiv\b', r'\bmod\b']
        _add_rules(op_keywords, self._fmt("#AF00DB", bold=True))

        # ── الأرقام ──
        self._rules.append((
            QRegularExpression(r'\b\d+(\.\d+)?\b'),
            self._fmt("#098658")
        ))

        # ── النصوص ──
        self._rules.append((
            QRegularExpression(r'"[^"]*"'),
            self._fmt("#A31515")
        ))

        # ── عامل التعيين ──
        self._rules.append((
            QRegularExpression(r'<-'),
            self._fmt("#AF00DB", bold=True)
        ))

        # ── التعليقات (Gray) ──
        self._rules.append((
            QRegularExpression(r'//[^\n]*'),
            self._fmt("#6A737D", italic=True)
        ))

    def highlightBlock(self, text):
        for pattern, fmt in self._rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                match = it.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)

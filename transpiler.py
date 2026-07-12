"""
MyAlgo Transpiler - المترجم الخوارزمي
"""
import os, sys, io, re, threading
from lark import Lark, Tree, Token, Transformer, UnexpectedInput, UnexpectedToken, UnexpectedCharacters, v_args

# ─── رسائل الخطأ بالعربية ────────────────────────────────────────
ERR = {
    "unexpected_token": "⛔ خطأ نحوي في السطر {line}:\n   وُجد '{found}' بينما كان المتوقع: {expected}",
    "unexpected_char": "⛔ حرف غير متوقع في السطر {line}, العمود {col}:\n   الحرف '{char}' غير مسموح به هنا.",
    "unexpected_eof": "⛔ انتهى النص بشكل غير متوقع.\n   تأكد من كتابة 'Fin.' في نهاية الخوارزمية.",
    "missing_semi": "💡 تلميح: ربما نسيت الفاصلة المنقوطة ';' في السطر {line}.",
    "division_zero": "⚠️ خطأ حسابي: لا يمكن القسمة على صفر!",
    "undefined_var": "⚠️ المتغير '{name}' غير معرّف. تأكد من تعريفه في قسم التصريحات.",
    "type_error": "⚠️ خطأ في نوع البيانات: {msg}",
    "index_error": "⚠️ مؤشر المصفوفة خارج النطاق: {msg}",
    "general": "⛔ خطأ: {msg}",
}

KEYWORDS = [
    "Algorithme","Début","Fin.","Variable","Var","Constante",
    "entier","réel","reel","caractère","caractere",
    "chaine de caractères","chaine de caracteres","chaine",
    "booléen","booleen","Tableau",
    "Si","alors","Alors","Sinon","FinSi","Finsi",
    "Pour","Faire","FinPour",
    "Tant que","TantQue","faire","FinTantQue","Fintantque",
    "Répéter","Repeter","Jusqu'à","Jusqu'a","Jusqua",
    "Selon","Cas","FinSelon","Finselon",
    "Lire","Ecrire","Écrire","ET","OU","NON",
    "vrai","Vrai","faux","Faux","DIV","MOD","de","pas","à","a",
]

# ─── معالج الحروف الكبيرة/الصغيرة ──────────────────────────────
_CASE_MAP = {
    'algorithme':'Algorithme','début':'Début','debut':'Début',
    'variable':'Variable','var':'Var','constante':'Constante',
    'si':'Si','sinon':'Sinon','finsi':'FinSi',
    'pour':'Pour','faire':'Faire','finpour':'FinPour',
    'répéter':'Répéter','repeter':'Repeter',
    'lire':'Lire','ecrire':'Ecrire','écrire':'Écrire',
    'et':'ET','ou':'OU','non':'NON',
    'vrai':'vrai','faux':'faux',
    'div':'DIV','mod':'MOD',
    'selon':'Selon','cas':'Cas','finselon':'FinSelon',
    'tableau':'Tableau',
    'début':'Début','debut':'Début',
    'alors':'alors','sinon':'Sinon',
    'entier':'entier','réel':'réel','reel':'reel',
    'caractère':'caractère','caractere':'caractere',
    'chaine':'chaine','booléen':'booléen','booleen':'booleen',
    'de':'de','pas':'pas',
}

def normalize_case(text):
    """تطبيع الحروف الكبيرة/الصغيرة للكلمات المفتاحية"""
    result = []
    i = 0
    in_string = False
    quote_char = None
    while i < len(text):
        if not in_string and text[i] == '"':
            in_string = True
            quote_char = '"'
            result.append(text[i]); i += 1; continue
        if in_string:
            if text[i] == quote_char: in_string = False
            result.append(text[i]); i += 1; continue
        if text[i:i+2] == '//':
            nl = text.find('\n', i)
            if nl == -1: result.append(text[i:]); break
            result.append(text[i:nl]); i = nl; continue
        # Multi-word keywords
        for mw in ['fin si','fin pour','fin tant que','fin selon',
                    'tant que','chaine de caractères','chaine de caracteres',
                    "jusqu'à","jusqu'a"]:
            chunk = text[i:i+len(mw)]
            if chunk.lower() == mw:
                canonical = {'fin si':'Fin si','fin pour':'Fin Pour',
                    'fin tant que':'Fin tant que','fin selon':'Fin Selon',
                    'tant que':'Tant que',
                    'chaine de caractères':'chaine de caractères',
                    'chaine de caracteres':'chaine de caracteres',
                    "jusqu'à":"Jusqu'à","jusqu'a":"Jusqu'a"}
                after = i + len(mw)
                if after >= len(text) or not text[after].isalpha():
                    result.append(canonical.get(mw, chunk))
                    i = after; break
        else:
            if text[i].isalpha() or text[i] == '_':
                j = i
                while j < len(text) and (text[j].isalnum() or text[j] == '_'): j += 1
                word = text[i:j]
                low = word.lower()
                # Check "Fin." as a unit
                if low == 'fin' and j < len(text) and text[j] == '.':
                    result.append('Fin.')
                    i = j + 1
                elif low in _CASE_MAP:
                    result.append(_CASE_MAP[low])
                    i = j
                else:
                    result.append(word)
                    i = j
            else:
                result.append(text[i]); i += 1
    return ''.join(result)

# ─── المحوّل ─────────────────────────────────────────────────────
def _indent(code, level=1):
    prefix = "    " * level
    if isinstance(code, list):
        lines = []
        for c in code:
            lines.extend(str(c).split('\n'))
    else:
        lines = str(code).split('\n')
    ind = [prefix + l for l in lines if l.strip()]
    return "\n".join(ind) if ind else prefix + "pass"

class AlgoTransformer(Transformer):
    def __init__(self):
        super().__init__()
        self.variables = {}   # name -> type_str
        self.constants = {}

    def start(self, items):
        decls = items[1]
        instrs = items[2]
        decl_list = decls if isinstance(decls, list) else ([decls] if decls else [])
        step_list = instrs if isinstance(instrs, list) else ([instrs] if instrs else [])
        decl_list = [str(d) for d in decl_list if d and str(d).strip()]
        step_list = [str(s) for s in step_list if s and str(s).strip()]
        return {"declarations": decl_list, "steps": step_list,
                "variables": dict(self.variables), "constants": dict(self.constants)}

    def en_tete(self, items): return ""
    
    def _check_name(self, n, check_defined=False, is_assign=False):
        import keyword
        n_lower = n.lower()
        algo_keywords = {
            "algorithme", "début", "debut", "fin", "variable", "var", "constante", "const",
            "entier", "réel", "reel", "caractère", "caractere", "chaine", "booléen", "booleen", "tableau",
            "si", "alors", "sinon", "finsi", "pour", "faire", "finpour", "tantque", "fintantque",
            "répéter", "repeter", "jusqu'à", "jusqu'a", "jusqua", "selon", "cas", "finselon",
            "lire", "ecrire", "écrire", "et", "ou", "non", "vrai", "faux", "div", "mod", "de", "pas", "à", "a"
        }
        py_keywords = ["math", "random", "_lire", "input", "sys", "time", "len", "print", "abs", "int", "float", "str", "bool", "true", "false", "__builtins__", "__import__", "eval", "exec", "globals", "locals", "dir", "vars"]
        
        if keyword.iskeyword(n) or n_lower in py_keywords or n_lower in algo_keywords:
            raise ValueError(f"الكلمة '{n}' محجوزة ولا يمكن استخدامها كاسم لمتغير أو ثابت.")
        if check_defined:
            if n not in self.variables and n not in self.constants:
                raise ValueError(f"المتغير '{n}' غير معرّف.")
            if is_assign and n in self.constants:
                raise ValueError(f"لا يمكن تغيير قيمة الثابت '{n}'.")
        else:
            if n in self.variables or n in self.constants:
                raise ValueError(f"تم التصريح عن المُعرّف '{n}' سابقاً، لا يمكن التصريح به أكثر من مرة.")

    def declarations(self, items):
        parts = []
        for i in items:
            if isinstance(i, list): parts.extend(i)
            elif i and str(i).strip(): parts.append(i)
        return parts

    def declaration_const_block(self, items):
        return [i for i in items if isinstance(i, str)]

    def const_line(self, items):
        n, v = str(items[0]).lower(), str(items[1])
        self._check_name(n)
        self.constants[n] = v
        self.variables[n] = "ثابت"
        return f"{n} = {v}"

    def declaration_var_block(self, items):
        lines = []
        for i in items:
            if isinstance(i, list):
                lines.extend(i)
        return lines

    def var_line(self, items):
        lines, var_names = [], []
        ts = str(items[-1]) if items else "entier"
        for item in items[:-1]:
            if isinstance(item, Token): var_names.append(str(item).lower())
        defaults = {"entier":"0","réel":"0.0","reel":"0.0","caractère":"''",
                     "caractere":"''","chaine de caractères":"''",
                     "chaine de caracteres":"''","chaine":"''",
                     "booléen":"False","booleen":"False"}
        ts_lower = ts.lower().strip()
        if ts_lower.startswith("tableau"): d = "{}"
        else: d = defaults.get(ts_lower, "0")
        for n in var_names:
            self._check_name(n)
            self.variables[n] = ts
            lines.append(f"{n} = {d}")
        return lines

    def type_donnee(self, items): return " ".join(str(i) for i in items)
    def instructions(self, items):
        return [i for i in items if i and str(i).strip()]

    @v_args(meta=True)
    def affectation(self, meta, items):
        var_target = str(items[0]).lower() if isinstance(items[0], Token) else str(items[0])
        var_name = var_target.split('[')[0]
        self._check_name(var_name, check_defined=True, is_assign=True)
        if var_name in self.variables:
            var_type = self.variables[var_name]
            val = str(items[1]).strip()
            is_string = val.startswith('"') or val.startswith("'")
            is_bool = val in ("True", "False")
            str_types = ("chaine", "chaine de caractères", "chaine de caracteres", "caractère", "caractere")
            if is_string and var_type not in str_types:
                raise ValueError(f"المتغير '{var_name}' من نوع '{var_type}'، لا يمكن إسناد قيمة نصية إليه.")
            if is_bool and var_type not in ("booléen", "booleen", "entier"):
                raise ValueError(f"المتغير '{var_name}' من نوع '{var_type}'، لا يمكن إسناد قيمة منطقية إليه.")
            if val.replace(".", "").replace("-", "").isdigit():
                if var_type in str_types:
                    raise ValueError(f"المتغير '{var_name}' من نوع '{var_type}'، لا يمكن إسناد قيمة رقمية إليه.")
                if var_type in ("booléen", "booleen"):
                    raise ValueError(f"المتغير '{var_name}' من نوع '{var_type}'، لا يمكن إسناد قيمة رقمية إليه.")
            if val in self.variables:
                val_type = self.variables[val]
                if val_type in str_types and var_type not in str_types:
                    raise ValueError(f"المتغير '{var_name}' من نوع '{var_type}'، لا يمكن إسناد المتغير النصي '{val}' إليه.")
                elif val_type in ("entier", "réel", "reel"):
                    if var_type in str_types:
                        raise ValueError(f"المتغير '{var_name}' من نوع '{var_type}'، لا يمكن إسناد المتغير الرقمي '{val}' إليه.")
                    if var_type in ("booléen", "booleen"):
                        raise ValueError(f"المتغير '{var_name}' من نوع '{var_type}'، لا يمكن إسناد المتغير الرقمي '{val}' إليه.")
                elif val_type in ("booléen", "booleen") and var_type not in ("booléen", "booleen", "entier"):
                    raise ValueError(f"المتغير '{var_name}' من نوع '{var_type}'، لا يمكن إسناد المتغير المنطقي '{val}' إليه.")
        return f"#_L{meta.line}_\n{var_target} = {items[1]}"
    def acces_tableau(self, items): return f"{str(items[0]).lower()}[{items[1]}]"
    
    @v_args(meta=True)
    def lecture(self, meta, items):
        cibles = []
        for i in items:
            t = str(i).lower() if isinstance(i, Token) else str(i)
            self._check_name(t.split('[')[0], check_defined=True, is_assign=True)
            cibles.append(t)
        return f"#_L{meta.line}_\n" + "\n".join(f"{c} = _lire('{c}')" for c in cibles)
    
    @v_args(meta=True)
    def ecriture(self, meta, items):
        return f"#_L{meta.line}_\n_ecrire({', '.join(str(i) for i in items)})"

    @v_args(meta=True)
    def condition_simple(self, meta, items):
        return f"#_L{meta.line}_\nif {items[0]}:\n{_indent(items[1])}"
        
    @v_args(meta=True)
    def condition_choix(self, meta, items):
        return f"#_L{meta.line}_\nif {items[0]}:\n{_indent(items[1])}\nelse:\n{_indent(items[2])}"

    @v_args(meta=True)
    def boucle_pour(self, meta, items):
        var_n = str(items[0]).lower()
        self._check_name(var_n, check_defined=True, is_assign=True)
        return f"#_L{meta.line}_\nfor {var_n} in range(int({items[1]}), int({items[2]}) + 1):\n{_indent(items[3])}"
        
    @v_args(meta=True)
    def boucle_pour_desc(self, meta, items):
        var_n = str(items[0]).lower()
        self._check_name(var_n, check_defined=True, is_assign=True)
        return f"#_L{meta.line}_\nfor {var_n} in range(int({items[1]}), int({items[2]}) - 1, int({items[3]})):\n{_indent(items[4])}"
        
    @v_args(meta=True)
    def boucle_tantque(self, meta, items):
        return f"#_L{meta.line}_\nwhile {items[0]}:\n{_indent(items[1])}"
        
    @v_args(meta=True)
    def boucle_repeter(self, meta, items):
        return f"#_L{meta.line}_\nwhile True:\n{_indent(items[0])}\n    if {items[1]}:\n        break"

    @v_args(meta=True)
    def selon_cas(self, meta, items):
        expr = str(items[0])
        lines, first = [], True
        for c in items[1:]:
            s = str(c)
            if first:
                lines.append(s.replace("CASE_IF", f"if {expr} ==", 1)); first = False
            elif "CASE_ELSE" in s: lines.append(s.replace("CASE_ELSE", "else"))
            else: lines.append(s.replace("CASE_IF", f"elif {expr} ==", 1))
        return f"#_L{meta.line}_\n" + "\n".join(lines)
        
    def cas_item(self, items): return f"CASE_IF {items[0]}:\n{_indent(items[1])}"
    def cas_sinon(self, items): return f"CASE_ELSE:\n{_indent(items[0])}"

    @v_args(meta=True)
    def appel_fonction(self, meta, items):
        n = str(items[0])
        if n not in ["Ecrire", "Lire"]:
            raise ValueError(f"الإجراء '{n}' غير مدعوم.")
        if n == "Ecrire": n = "_ecrire"
        if n == "Lire": raise ValueError("استخدم صيغة Lire(x) حصراً، لا تستخدمها كإجراء عام.")
        return f"#_L{meta.line}_\n{n}({', '.join(str(i) for i in items[1:])})"
        
    def appel_expr(self, items):
        n = str(items[0])
        a = ", ".join(str(i) for i in items[1:])
        m = {"Abs":"abs","Racine":"math.sqrt","Ent":"int","Long":"len"}
        if n not in m:
            raise ValueError(f"الدالة '{n}' غير معرّفة أو غير مسموح باستخدامها.")
        return f"{m.get(n,n)}({a})"

    def comparaison(self, items):
        c = str(items[1].children[0])
        if c == '=': c = '=='
        elif c == '<>': c = '!='
        return f"{items[0]} {c} {items[2]}"
    def condition_non(self, items): return f"not ({items[0]})"
    def condition_et(self, items): return " and ".join(str(i) for i in items)
    def condition_ou(self, items): return " or ".join(str(i) for i in items)
    def cond_parens(self, items): return f"({items[0]})"
    def parens(self, items): return f"({items[0]})"

    def expression(self, items):
        r = str(items[0])
        for i in range(1, len(items), 2): r += f" {items[i].children[0]} {items[i+1]}"
        return r
    def terme(self, items):
        r = str(items[0])
        for i in range(1, len(items), 2):
            op = str(items[i].children[0])
            if op == 'DIV': op = '//'
            elif op == 'MOD': op = '%'
            r += f" {op} {items[i+1]}"
        return r
    def facteur(self, items):
        r = str(items[0])
        for i in range(1, len(items)): r += f" ** {items[i]}"
        return r
    def neg(self, items): return f"-({items[0]})"
    def variable_ref(self, items):
        v_str = str(items[0]).lower()
        if v_str == 'vrai': return 'True'
        if v_str == 'faux': return 'False'
        self._check_name(v_str, check_defined=True)
        return v_str

# ─── أدوات الأخطاء ──────────────────────────────────────────────
def _nice(t):
    t_str = str(t).replace("'", "").replace('"', "")
    m = {
        "CNAME": "اسم (متغير/دالة)", "ESCAPED_STRING": 'نص "..."', "NUMBER": "رقم",
        "SEMICOLON": "فاصلة منقوطة ';'", "COLON": "نقطتين ':'", "COMMA": "فاصلة ','",
        "LPAR": "قوس '('", "RPAR": "قوس ')'", "EQUAL": "علامة المساواة '='",
        "_EOF": "نهاية الملف"
    }
    if t_str.startswith("__ANON"): return "رمز أو كلمة مفتاحية"
    if t_str in ["Algorithme", "Début", "Fin", "Variable", "Constante", "Si", "Alors", "Sinon", "Pour", "Faire", "Tant que", "Répéter", "Jusqu'à"]:
        return f"الكلمة المفتاحية '{t_str}'"
    return m.get(t_str, t_str)

def _fmt_parse_err(e):
    if isinstance(e, UnexpectedToken):
        exp = "، ".join(_nice(x) for x in list(e.expected or [])[:5]) or "?"
        found = e.token.value
        msg = f"⛔ خطأ إملائي/نحوي في السطر {e.line} (العمود {e.column}):\n"
        msg += f"   البرنامج وجد الكلمة أو الرمز '{found}'\n   بينما كان يتوقع أحد الأشياء التالية: {exp}"
        if "فاصلة منقوطة" in exp or ";" in exp: 
            msg += f"\n\n💡 تلميح: يبدو أنك نسيت إضافة الفاصلة المنقوطة ';' في نهاية السطر السابق أو الحالي."
        elif "Début" in exp:
            msg += f"\n\n💡 تلميح: تأكد من كتابة 'Début' قبل بدء التعليمات."
        elif "Fin" in exp:
            msg += f"\n\n💡 تلميح: هل نسيت إغلاق حلقة أو شرط، أو نسيت 'Fin' في النهاية؟"
        elif "قوس" in exp or ")" in exp:
            msg += f"\n\n💡 تلميح: يبدو أنك فتحت قوساً '(' ولكنك نسيت إغلاقه ')'!"
        return msg
    elif isinstance(e, UnexpectedCharacters):
        char = str(e.char)
        msg = f"⛔ حرف غريب في السطر {e.line}، العمود {e.column}:\n   الحرف '{char}' غير صالح للاستخدام هنا."
        if char in ('"', "'"):
            msg += f"\n\n💡 تلميح: يبدو أنك فتحت علامة تنصيص ({char}) ولكنك نسيت إغلاقها!"
        else:
            prev_line = e.line - 1 if e.line > 1 else e.line
            msg += f"\n\n💡 تلميحات محتملة:\n1- قد تكون نسيت 'فاصلة منقوطة ;' في نهاية السطر السابق ({prev_line}).\n2- ربما فتحت قوساً '(' ولم تقم بإغلاقه ')'."
        return msg
    elif e.__class__.__name__ == 'UnexpectedEOF':
        msg = f"⛔ نهاية غير متوقعة للملف (Unexpected EOF).\n\n💡 تلميح: الكود انتهى قبل الأوان! هل نسيت كتابة 'Fin' في النهاية؟ أو ربما نسيت إغلاق بنية مثل 'Fin Si' أو 'Fin Pour'؟"
        return msg
    else:
        return ERR["general"].format(msg=str(e))

def _fmt_runtime_err(e):
    if isinstance(e, ZeroDivisionError): return ERR["division_zero"]
    if isinstance(e, NameError):
        m = re.search(r"name '(\w+)'", str(e))
        return ERR["undefined_var"].format(name=m.group(1) if m else "?")
    if isinstance(e, TypeError):
        msg = str(e)
        if "unsupported operand type" in msg:
            if "str" in msg and "int" in msg: msg = "لا يمكن إجراء عمليات حسابية بين الأرقام والنصوص!"
            else: msg = "عملية حسابية أو منطقية غير صالحة بين أنواع مختلفة."
        elif "item assignment" in msg: msg = "حاولت التعامل مع متغير عادي وكأنه مصفوفة (Tableau)!"
        elif "must be str" in msg or "concatenate" in msg: msg = "لا يمكن دمج نص مع رقم مباشرة!"
        return ERR["type_error"].format(msg=msg)
    if isinstance(e, IndexError): return ERR["index_error"].format(msg="حاولت الوصول إلى عنصر أو مؤشر غير موجود في المصفوفة.")
    import traceback
    if isinstance(e, ValueError):
        msg = str(e)
        if "invalid literal for int" in msg: return ERR["type_error"].format(msg="حاولت استخدام نص كأنه رقم صحيح (entier)، لكن النص لا يحتوي على أرقام صالحة!")
        if "could not convert string to float" in msg: return ERR["type_error"].format(msg="حاولت استخدام نص كأنه رقم حقيقي (réel)، لكن النص لا يحتوي على أرقام صالحة!")
        return ERR["type_error"].format(msg="قيمة غير صالحة للعملية المطلوبة.")
    return ERR["general"].format(msg=str(e) + "\n" + traceback.format_exc())

# ─── المحلل النحوي ──────────────────────────────────────────────
def _resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

_parser = None
def _get_parser():
    global _parser
    if _parser is None:
        p = _resource_path('grammar.lark')
        with open(p, 'r', encoding='utf-8') as f: g = f.read()
        _parser = Lark(g, parser='earley', propagate_positions=True)
    return _parser

SETUP_CODE = (
    "import math\n"
    "def _lire(var_name):\n"
    "    val = input(var_name + ' = ')\n"
    "    try: return int(val)\n"
    "    except ValueError:\n"
    "        try: return float(val)\n"
    "        except ValueError: return val\n"
)

def transpile(code_text):
    """ترجمة → dict{declarations, steps, variables, lines} أو (None, error)"""
    try:
        code_text = normalize_case(code_text)
        tree = _get_parser().parse(code_text)
        
        # Extract line numbers for top-level instructions
        instruction_lines = []
        # tree.children = [en_tete, declarations, instructions] (since Début/Fin are ignored or parsed out)
        # Wait, start rule: en_tete declarations "Début" instructions "Fin"
        # Lark drops string literals, so children are: [en_tete, declarations, instructions]
        instructions_node = tree.children[2]
        if isinstance(instructions_node, Tree):
            for child in instructions_node.children:
                if isinstance(child, Tree) and hasattr(child, 'meta'):
                    instruction_lines.append(child.meta.line)
                else:
                    instruction_lines.append(0)
                    
        result = AlgoTransformer().transform(tree)
        result["lines"] = instruction_lines
        return result, None
    except UnexpectedInput as e:
        return None, _fmt_parse_err(e)
    except Exception as e:
        msg = str(e)
        if "Error trying to process rule" in msg:
            msg = msg.split("\n")[-1].strip() or msg.split("\n")[-2].strip()
        return None, ERR["general"].format(msg=msg)

# ─── محرك التنفيذ خطوة بخطوة ────────────────────────────────────
class StepExecutor:
    def __init__(self, result, input_callback=None, out_stream=None):
        self.ns = {}
        self.declarations = result["declarations"]
        self.steps = result["steps"]
        self.code_str = "\n".join(self.steps)
        self.var_info = result["variables"]
        self.current = 0
        self._input_cb = input_callback
        self.out_stream = out_stream
        self.finished = False

    def setup(self):
        exec(SETUP_CODE, self.ns)
        if self._input_cb:
            self.ns['_lire'] = self._make_lire()
            
        if self.out_stream:
            self.ns['_ecrire'] = lambda *args: self.out_stream.write(" ".join(str(a) for a in args) + "\n")
        else:
            self.ns['_ecrire'] = lambda *args: sys.stdout.write(" ".join(str(a) for a in args) + "\n")
            
        for d in self.declarations: exec(d, self.ns)
        import math, random
        self.ns['math'] = math; self.ns['random'] = random
        
        # Build clean python code and line map
        code_lines = self.code_str.split('\n')
        self.line_map = {}
        clean_lines = []
        cur_line = -1
        for i, line in enumerate(code_lines):
            stripped = line.strip()
            if stripped.startswith('#_L') and stripped.endswith('_'):
                try:
                    cur_line = int(stripped[3:-1])
                except ValueError: pass
            clean_lines.append(line)
            self.line_map[i + 1] = cur_line
        self.clean_code = "\n".join(clean_lines)

    def _make_lire(self):
        cb = self._input_cb
        def _lire(var_name):
            val = cb(var_name + ' = ')
            try: return int(val)
            except ValueError:
                try: return float(val)
                except ValueError: return val
        return _lire

    def get_variables(self):
        skip = {'__builtins__','math','_lire','input','random'}
        result = {}
        for k, v in self.ns.items():
            if not k.startswith('_') and k not in skip and not callable(v) and not isinstance(v, type):
                result[k] = {"value": v, "type": self.var_info.get(k, "?")}
        return result

    def run_debug(self, step_ev, is_run_all, step_done_signal, error_signal, stop_check=None):
        last_emitted_line = -1
        
        def trace_lines(frame, event, arg):
            nonlocal last_emitted_line
            if frame.f_globals is not self.ns:
                return trace_lines
                
            if stop_check and stop_check():
                sys.settrace(None)
                raise SystemExit("stopped")
                
            for var_name, var_type_str in self.var_info.items():
                if var_name in frame.f_locals:
                    val = frame.f_locals[var_name]
                    if var_type_str == 'entier' and not isinstance(val, (int, bool)):
                        raise TypeError(f"المتغير '{var_name}' من نوع (entier)، تم إسناد قيمة خاطئة إليه.")
                    elif var_type_str in ('réel', 'reel') and not isinstance(val, (int, float, bool)):
                        raise TypeError(f"المتغير '{var_name}' من نوع (réel)، تم إسناد قيمة خاطئة إليه.")
                    elif var_type_str in ('caractère', 'caractere') and (not isinstance(val, str) or len(val) > 1):
                        raise TypeError(f"المتغير '{var_name}' من نوع (caractère)، يجب أن يحتوي على حرف واحد.")
                    elif 'chaine' in var_type_str and not isinstance(val, str):
                        raise TypeError(f"المتغير '{var_name}' من نوع (chaine)، يجب أن يكون نصاً.")
                    elif var_type_str in ('booléen', 'booleen') and not isinstance(val, bool):
                        raise TypeError(f"المتغير '{var_name}' من نوع (booléen)، يجب أن يكون Vrai أو Faux.")
                        
            if event == 'line':
                algo_line = self.line_map.get(frame.f_lineno, -1)
                if algo_line != -1 and algo_line != last_emitted_line:
                    last_emitted_line = algo_line
                    step_done_signal.emit(self.get_variables(), False, algo_line)
                    if not is_run_all:
                        step_ev.wait()
                        step_ev.clear()
                    else:
                        import time
                        time.sleep(0.3)
            return trace_lines

        try:
            sys.settrace(trace_lines)
            exec(self.clean_code, self.ns)
            self.finished = True
        except SystemExit:
            self.finished = True
        except Exception as e:
            err = _fmt_runtime_err(e)
            error_signal.emit(err)
            self.finished = True
        finally:
            sys.settrace(None)
            
    # Legacy methods for compatibility, though ExecutionThread will be updated
    def step_next(self): return "", None, True
    def run_all(self): return "", None
    @property
    def total_steps(self): return len(self.steps)
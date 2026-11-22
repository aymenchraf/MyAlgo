"""
MyAlgo IDE - نافذة شرح الكلمات المحجوزة والتعليمات
Keyword Help & Documentation Module for MyAlgo IDE
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QFrame, QApplication, QPlainTextEdit
)
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt, pyqtSignal
from highlighter import AlgoHighlighter

# قاموس التوثيق والشرح التعليمي لجميع الكلمات المحجوزة والتعليمات في الخوارزميات
KEYWORD_DOCS = {
    "Algorithme": {
        "title": "بداية الخوارزمية (Algorithme)",
        "category": "هيكل الخوارزمية",
        "description": "تُستخدم هذه الكلمة في السطر الأول الإلزامي لتحديد اسم الخوارزمية. يجب أن يبدأ الاسم بحرف هجائي وألا يحتوي على مسافات أو رموز خاصة، وينتهي السطر بفاصلة منقوطة (;).",
        "syntax": "Algorithme <Nom_Algorithme>;",
        "example": "Algorithme CalculMoyenne;\nVariable\n    note1, note2, moy : réel;\nDébut\n    Ecrire(\"حساب المعدل\");\nFin",
        "tip": "اختر دائماً اسماً معبراً يدل على وظيفة الخوارزمية (مثلاً: CalculSomme أو TriTableau)."
    },
    "Début": {
        "title": "بداية التنفيذ (Début)",
        "category": "هيكل الخوارزمية",
        "description": "تمثل نقطة الانطلاق الفعلية لتنفيذ التعليمات بالتسلسل. كل ما يسبق 'Début' مخصص فقط للتصريح عن المتغيرات والثوابت، ولا يمكن كتابة أي تعليمة تنفيذية قبله.",
        "syntax": "Début\n    // التعليمات التنفيذية\nFin",
        "example": "Algorithme Bienvenue;\nDébut\n    Ecrire(\"مرحباً بك في عالم الخوارزميات!\");\nFin",
        "tip": "تأكد من عدم كتابة أي تعليمة حسابية أو قراءة أو كتابة قبل كلمة Début."
    },
    "Fin": {
        "title": "نهاية الخوارزمية (Fin)",
        "category": "هيكل الخوارزمية",
        "description": "الكلمة الختامية الإلزامية في نهاية كل خوارزمية، وعند وصول المعالج إليها يتوقف تنفيذ البرنامج بالكامل.",
        "syntax": "Fin",
        "example": "Algorithme FinProgramme;\nDébut\n    Ecrire(\"تم إنهاء العمل بنجاح\");\nFin",
        "tip": "لكل Début في الخوارزمية كلمة Fin مقابلة لها تختم البرنامج."
    },
    "<-": {
        "title": "تعليمة الإسناد (Affectation)",
        "category": "تعليمات أساسية",
        "description": "تُستعمل لتخزين قيمة أو ناتج عبارة حسابية داخل متغير في الذاكرة. المتغير الذي يستقبل القيمة يكون دائماً على يسار السهم، والقيمة أو العبارة على يمينه.",
        "syntax": "<Nom_Variable> <- <Valeur_ou_Expression>;",
        "example": "x <- 15;\ny <- x * 2 + 5;\nmessage <- \"Bonjour\";",
        "tip": "يجب أن يتطابق نوع القيمة الموجودة على يمين السهم تماماً مع نوع المتغير المصرح عنه على اليسار."
    },
    "Lire": {
        "title": "تعليمة القراءة والإدخال (Lire)",
        "category": "تعليمات الإدخال والإخراج",
        "description": "تطلب من المستخدم إدخال قيمة عبر لوحة المفاتيح أثناء تشغيل الخوارزمية، وتخزن القيمة المدخلة في المتغير المحدد بين القوسين.",
        "syntax": "Lire(<Variable>);\nLire(var1, var2);",
        "example": "Ecrire(\"أدخل عمرك: \");\nLire(age);\nEcrire(\"عمرك المسجل هو: \", age);",
        "tip": "ضع دائماً تعليمة Ecrire قبل تعليمة Lire لتنبيه المستخدم بما يجب عليه إدخاله."
    },
    "Ecrire": {
        "title": "تعليمة الكتابة والعرض (Ecrire)",
        "category": "تعليمات الإدخال والإخراج",
        "description": "تُستخدم لعرض النصوص وطباعة قيم المتغيرات ونتائج الحسابات على شاشة النتائج. يمكن الفصل بين عدة عناصر للطباعة باستخدام الفاصلة (,).",
        "syntax": "Ecrire(\"نص\", <Variable>, ...);",
        "example": "nom <- \"أحمد\";\nnote <- 18.5;\nEcrire(\"التلميذ: \", nom, \" | المعدل: \", note);",
        "tip": "توضع النصوص الثابتة بين مزدوجتين (\" \")، بينما تكتب أسماء المتغيرات بدون مزدوجات لتطبع قيمتها."
    },
    "Variable": {
        "title": "قسم التصريح عن المتغيرات (Variable)",
        "category": "التصريحات",
        "description": "يُحجز في هذا القسم جميع المتغيرات التي ستُستعمل في الخوارزمية مع تحديد نوع كل منها، ويكون موقعه بين اسم الخوارزمية وكلمة Début.",
        "syntax": "Variable\n    <var1>, <var2> : <Type>;",
        "example": "Variable\n    nom : chaine;\n    age : entier;\n    moyenne : réel;\n    admis : booléen;",
        "tip": "لا يمكن استخدام أي متغير في الخوارزمية دون التصريح عنه مسبقاً في قسم Variable."
    },
    "Constante": {
        "title": "قسم التصريح عن الثوابت (Constante)",
        "category": "التصريحات",
        "description": "يُستخدم لتعريف قيم ثابتة لا تتغير قيمتها أبداً طوال فترة عمل الخوارزمية (مثل الثوابت الرياضية والفيزيائية).",
        "syntax": "Constante\n    <Nom_Constante> = <Valeur>;",
        "example": "Constante\n    PI = 3.14159;\n    TVA = 0.19;\n    MAX_ELEVES = 40;",
        "tip": "إذا حاولت تعديل قيمة ثابت بتعليمة إسناد (<-) سيعتبره المحرر خطأً لأن قيمته محمية من التغيير."
    },
    "entier": {
        "title": "النوع العددي الصحيح (entier)",
        "category": "أنواع البيانات",
        "description": "يمثل الأعداد الصحيحة الخالية من الفواصل العشرية (سواء كانت موجبة أو سالبة أو صفراً)، مثل: 5، -12، 0، 2024.",
        "syntax": "Variable <x> : entier;",
        "example": "Variable\n    a, b, somme : entier;\nDébut\n    a <- 10;\n    b <- 20;\n    somme <- a + b;\n    Ecrire(\"المجموع = \", somme);\nFin",
        "tip": "لإجراء القسمة الصحيحة بين عددين من نوع entier نستخدم DIV للحاصل و MOD للباقي."
    },
    "réel": {
        "title": "النوع العددي الحقيقي (réel)",
        "category": "أنواع البيانات",
        "description": "يمثل الأعداد العشرية التي تحتوي على فاصلة وجزء كسري، مثل: 3.14، -0.75، 12.0.",
        "syntax": "Variable <x> : réel;",
        "example": "Variable\n    prix, remise, prix_final : réel;\nDébut\n    prix <- 150.5;\n    remise <- 0.15;\n    prix_final <- prix * (1 - remise);\n    Ecrire(\"السعر بعد التخفيض: \", prix_final);\nFin",
        "tip": "في لغة الخوارزميات نستخدم النقطة (.) لكتابة الفاصلة العشرية وليس الفاصلة العادية."
    },
    "chaine": {
        "title": "نوع السلسلة النصية (chaine)",
        "category": "أنواع البيانات",
        "description": "يمثل النصوص والكلمات المكونة من سلسلة من الحروف والأرقام والرموز، وتُكتب قيمتها محاطة بمزدوجتين (\" \").",
        "syntax": "Variable <texte> : chaine;",
        "example": "Variable\n    prenom, message : chaine;\nDébut\n    prenom <- \"سارة\";\n    message <- \"أهلاً وسهلاً بك\";\n    Ecrire(message, \" يا \", prenom);\nFin",
        "tip": "يمكن دمج السلاسل النصية والمتغيرات مباشرة في تعليمة Ecrire بالفصل بينها بفواصل."
    },
    "caractère": {
        "title": "نوع الحرف المفرد (caractère)",
        "category": "أنواع البيانات",
        "description": "يمثل رمزاً أو حرفاً هجائياً أو رقماً مفرداً واحداً فقط، ويوضع بين علامتي تنصيص (' ') أو (\" \").",
        "syntax": "Variable <c> : caractère;",
        "example": "Variable\n    choix : caractère;\nDébut\n    Ecrire(\"اضغط 'O' للموافقة أو 'N' للإلغاء: \");\n    Lire(choix);\n    Si choix = 'O' Alors\n        Ecrire(\"تمت الموافقة\");\n    FinSi\nFin",
        "tip": "النوع caractère يسع حرفاً واحداً فقط، فإذا أردت تخزين كلمة أو جملة استخدم chaine."
    },
    "booléen": {
        "title": "النوع المنطقي (booléen)",
        "category": "أنواع البيانات",
        "description": "متغير يقبل إحدى قيمتين فقط: صحيح (Vrai) أو خطأ (Faux). يُستخدم كثيراً في الرايات المنطقية والتحقق من الشروط.",
        "syntax": "Variable <flag> : booléen;",
        "example": "Variable\n    admis : booléen;\n    note : réel;\nDébut\n    note <- 14.5;\n    admis <- (note >= 10);\n    Ecrire(\"هل التلميذ ناجح؟ \", admis);\nFin",
        "tip": "نتائج جميع العمليات المنطقية والمقارنات (مثل > ، < ، = ، <>) تكون دائماً من نوع booléen."
    },
    "Tableau": {
        "title": "بنية الجداول والمصفوفات (Tableau)",
        "category": "بنى المعطيات",
        "description": "بنية لتخزين مجموعة مرتبة من العناصر من نفس النوع البياني تحت اسم واحد، ويتم الوصول لكل عنصر عبر دليله الرقمي المحصور بين عارضتين [ ].",
        "syntax": "Variable <nom> : Tableau[1..N] de <Type>;",
        "example": "Variable\n    T : Tableau[1..5] de entier;\n    i : entier;\nDébut\n    Pour i <- 1 à 5 Faire\n        T[i] <- i * 10;\n        Ecrire(\"T[\", i, \"] = \", T[i]);\n    FinPour\nFin",
        "tip": "في الخوارزميات التعليمية تبدأ أدلة الجداول عادةً من الرقم 1 وتصل إلى الحد الأقصى N."
    },
    "de": {
        "title": "كلمة تحديد نوع الجدول (de)",
        "category": "الكلمات المساعدة",
        "description": "تُستخدم عند التصريح عن المصفوفات لربط مجال أدلة الجدول بنوع بيانات عناصره (مثل: Tableau[1..10] de réel).",
        "syntax": "Tableau[1..N] de <Type>;",
        "example": "Variable\n    notes : Tableau[1..30] de réel;\n    noms : Tableau[1..30] de chaine;",
        "tip": "جميع العناصر داخل الجدول الواحد يجب أن تكون حتماً من نفس النوع المحدد بعد كلمة de."
    },
    "Vrai": {
        "title": "القيمة المنطقية صحيح (Vrai)",
        "category": "القيم المنطقية",
        "description": "تمثل الحالة المنطقية المحققة أو الصواب (تعادل True في لغات البرمجة).",
        "syntax": "<var_bool> <- Vrai;",
        "example": "trouve <- Vrai;\nSi trouve Alors\n    Ecrire(\"تم العثور على العنصر بنجاح!\");\nFinSi",
        "tip": "يمكن كتابة الشرط Si trouve Alors مباشرة دون الحاجة لكتابة Si trouve = Vrai."
    },
    "Faux": {
        "title": "القيمة المنطقية خطأ (Faux)",
        "category": "القيم المنطقية",
        "description": "تمثل الحالة المنطقية غير المحققة أو البطلان (تعادل False في لغات البرمجة).",
        "syntax": "<var_bool> <- Faux;",
        "example": "valide <- Faux;\nSi NON valide Alors\n    Ecrire(\"يرجى إعادة إدخال البيانات\");\nFinSi",
        "tip": "تُستخدم عادة لتهيئة المتغيرات المنطقية قبل البدء في عمليات البحث أو الحلقات."
    },
    "ET": {
        "title": "المعامل المنطقي و (ET)",
        "category": "المعاملات المنطقية",
        "description": "يربط بين شرطين أو أكثر، ولا يعطي نتيجة صحيحة (Vrai) إلا إذا كانت جميع الشروط المرتبطة به صحيحة معاً في نفس الوقت.",
        "syntax": "(<Condition1>) ET (<Condition2>)",
        "example": "Si (age >= 18) ET (solde >= 1000) Alors\n    Ecrire(\"الطلب مقبول\");\nFinSi",
        "tip": "إذا كان أحد الشروط خاطئاً (Faux)، فإن نتيجة عبارة ET تكون خاطئة فوراً دون الحاجة لفحص البقية."
    },
    "OU": {
        "title": "المعامل المنطقي أو (OU)",
        "category": "المعاملات المنطقية",
        "description": "يربط بين شرطين أو أكثر، ويعطي نتيجة صحيحة (Vrai) إذا تحقق على الأقل شرط واحد من الشروط المرتبطة به.",
        "syntax": "(<Condition1>) OU (<Condition2>)",
        "example": "Si (moyenne >= 10) OU (rattrapage = Vrai) Alors\n    Ecrire(\"مقبول للانتقال\");\nFinSi",
        "tip": "تكون نتيجة OU خاطئة (Faux) فقط إذا كانت جميع الشروط خاطئة معاً."
    },
    "NON": {
        "title": "معامل النفي المنطقي (NON)",
        "category": "المعاملات المنطقية",
        "description": "يقوم بقلب القيمة المنطقية؛ فإذا كان الشرط Vrai يجعله Faux، وإذا كان Faux يجعله Vrai.",
        "syntax": "NON (<Condition>)",
        "example": "Si NON (x = 0) Alors\n    inv <- 1 / x;\n    Ecrire(\"المقلوب: \", inv);\nFinSi",
        "tip": "تعبير NON (a = b) يكافئ منطقياً تماماً كتابة a <> b."
    },
    "DIV": {
        "title": "القسمة الصحيحة (DIV)",
        "category": "المعاملات الحسابية",
        "description": "تُعطي حاصل القسمة الإقليدية الصحيحة لعددين صحيحين مع إهمال الفاصلة والباقي (مثلاً: 17 DIV 5 = 3).",
        "syntax": "<entier> DIV <entier>",
        "example": "heures <- minutes DIV 60;\nreste_minutes <- minutes MOD 60;\nEcrire(heures, \" ساعة و \", reste_minutes, \" دقيقة\");",
        "tip": "المؤثر DIV يُستخدم مع الأعداد الصحيحة فقط، أما علامة القسمة العادية (/) فتُعطي ناتجاً عشرياً réel."
    },
    "MOD": {
        "title": "باقي القسمة الصحيحة (MOD)",
        "category": "المعاملات الحسابية",
        "description": "تُعطي باقي القسمة الإقليدية لعددين صحيحين (مثلاً: 17 MOD 5 = 2). تُستخدم كثيراً لاختبار قابلية القسمة ومعرفة الأعداد الزوجية والفردية.",
        "syntax": "<entier> MOD <entier>",
        "example": "Si n MOD 2 = 0 Alors\n    Ecrire(n, \" هو عدد زوجي\");\nSinon\n    Ecrire(n, \" هو عدد فردي\");\nFinSi",
        "tip": "إذا كان a MOD b = 0، فهذا يعني أن العدد a يقبل القسمة على b تماماً دون باقٍ."
    },
    "Si": {
        "title": "البنية الشرطية البسيطة (Si)",
        "category": "البنى الشرطية",
        "description": "تسمح باتخاذ قرار وتنفيذ تعليمات معينة فقط في حال تحقق شرط منطقي محدد، متبوعة بكلمة Alors.",
        "syntax": "Si <Condition> Alors\n    // التعليمات عند تحقق الشرط\nFinSi",
        "example": "Si note >= 10 Alors\n    Ecrire(\"مبروك النجاح!\");\nFinSi",
        "tip": "لكل تعليمة Si يجب أن تتبعها كلمة Alors ويُختم نطاقها بـ FinSi."
    },
    "Alors": {
        "title": "كلمة الإنجاز حينئذٍ (Alors)",
        "category": "البنى الشرطية",
        "description": "تأتي فوراً بعد شرط Si لتحديد نقطة انطلاق التعليمات التي تُنفذ عندما يكون الشرط صحيحاً (Vrai).",
        "syntax": "Si <Condition> Alors",
        "example": "Si solde >= prix Alors\n    solde <- solde - prix;\n    Ecrire(\"تمت عملية الشراء بنجاح\");\nFinSi",
        "tip": "لا يمكن استخدام Alors منفردة دون أن تسبقها تعليمة شرطية Si."
    },
    "Sinon": {
        "title": "الفرع البديل وإلا (Sinon)",
        "category": "البنى الشرطية",
        "description": "جزء اختياري داخل بنية Si، يحتوي على التعليمات البديلة التي سيتم تنفيذها فقط عندما يكون الشرط خاطئاً (Faux).",
        "syntax": "Si <Condition> Alors\n    // عند الصواب\nSinon\n    // عند الخطأ\nFinSi",
        "example": "Si age >= 18 Alors\n    Ecrire(\"أنت شخص راشد\");\nSinon\n    Ecrire(\"أنت شخص قاصر\");\nFinSi",
        "tip": "كلمة Sinon لا تأخذ شرطاً بجانبها، بل تنفذ تلقائياً كلما كان شرط Si غير محقق."
    },
    "FinSi": {
        "title": "نهاية البنية الشرطية (FinSi)",
        "category": "البنى الشرطية",
        "description": "تحدد نهاية كتلة التعليمات التابعة للشرط، وتُعيد مسار التنفيذ إلى التعليمات المتسلسلة العادية.",
        "syntax": "FinSi",
        "example": "Si x < 0 Alors\n    x <- -x;\nFinSi\nEcrire(\"القيمة المطلقة هي: \", x);",
        "tip": "نسيان كتابة FinSi يسبب خطأً تركيبي لأن البرنامج لن يعرف أين تنتهي حدود الشرط."
    },
    "Selon": {
        "title": "بنية الاختيار المتعدد (Selon)",
        "category": "البنى الشرطية",
        "description": "تُستخدم للاختيار من بين عدة حالات متفرقة لقيمة متغير أو تعبير محدد، وهي أنظف وأسهل في القراءة من تكرار عدة شروط Si متداخلة.",
        "syntax": "Selon <Variable> Faire\n    Cas <Valeur1>:\n        // تعليمات\n    Cas <Valeur2>:\n        // تعليمات\n    Sinon:\n        // تعليمات افتراضية\nFinSelon",
        "example": "Selon num_jour Faire\n    Cas 1: Ecrire(\"الأحد\");\n    Cas 2: Ecrire(\"الإثنين\");\n    Cas 3: Ecrire(\"الثلاثاء\");\n    Sinon: Ecrire(\"يوم آخر\");\nFinSelon",
        "tip": "تُناسب جداً القوائم والخيارات الثابتة (مثل أيام الأسبوع، العمليات الحسابية، الخيارات الرقمية)."
    },
    "FinSelon": {
        "title": "نهاية الاختيار المتعدد (FinSelon)",
        "category": "البنى الشرطية",
        "description": "تحدد نهاية نطاق حالات Selon وخروج المعالج من فحص باقي الحالات.",
        "syntax": "FinSelon",
        "example": "Selon note Faire\n    Cas 20: Ecrire(\"علامة كاملة!\");\n    Sinon: Ecrire(\"عمل جيد\");\nFinSelon",
        "tip": "احرص على غلق كل بنية Selon بـ FinSelon مقابلة لها."
    },
    "Pour": {
        "title": "حلقة التكرار المحددة (Pour)",
        "category": "البنى التكرارية",
        "description": "تُستخدم لتكرار مجموعة من التعليمات لعدد محدد ومعلوم مسبقاً من المرات، من خلال عدّاد يتدرج من قيمة بداية إلى قيمة نهاية.",
        "syntax": "Pour <compteur> <- <début> à <fin> [pas <valeur>] Faire\n    // التعليمات المكررة\nFinPour",
        "example": "somme <- 0;\nPour i <- 1 à 10 Faire\n    somme <- somme + i;\nFinPour\nEcrire(\"المجموع من 1 إلى 10 = \", somme);",
        "tip": "يزداد العداد تلقائياً بمقدار 1 في نهاية كل دورة إذا لم يتم تحديد خيار 'pas'."
    },
    "à": {
        "title": "كلمة التحديد إلى (à)",
        "category": "البنى التكرارية",
        "description": "تُحدد القيمة النهائية أو الحد الأقصى الذي يتوقف عنده عداد حلقة Pour.",
        "syntax": "Pour <cpt> <- <début> à <fin> Faire",
        "example": "Pour i <- 1 à 5 Faire\n    Ecrire(\"الدورة: \", i);\nFinPour",
        "tip": "يقبل المحرر كتابتها بهمزة (à) أو بدون همزة (a) تيسيراً على التلاميذ."
    },
    "pas": {
        "title": "خطوة تدرج العداد (pas)",
        "category": "البنى التكرارية",
        "description": "خيار في حلقة Pour لتحديد مقدار الزيادة أو النقصان للعداد في كل دورة (مثلاً pas 2 للمرور على الأعداد الزوجية، أو pas -1 للعد التنازلي).",
        "syntax": "Pour <cpt> <- <début> à <fin> pas <pas> Faire",
        "example": "// تكرار تنازلي\nPour i <- 10 à 1 pas -1 Faire\n    Ecrire(i);\nFinPour",
        "tip": "إذا كانت قيمة البداية أكبر من النهاية، فيجب بالضرورة تحديد الخطوة pas بقيمة سالبة."
    },
    "Faire": {
        "title": "كلمة افعل / إنجاز (Faire)",
        "category": "البنى التكرارية",
        "description": "تُستخدم في حلقات Pour و TantQue للإشارة إلى بداية كتلة التعليمات التي سيتم تكرارها داخل الحلقة.",
        "syntax": "Pour ... Faire\nTantQue ... Faire",
        "example": "TantQue x > 0 Faire\n    x <- x - 1;\nFinTantQue",
        "tip": "كل حلقة تبدأ بـ Faire يجب أن تختم بـ FinPour أو FinTantQue حسب نوعها."
    },
    "FinPour": {
        "title": "نهاية حلقة Pour (FinPour)",
        "category": "البنى التكرارية",
        "description": "تحدد نهاية كتلة حلقة Pour، وعندها يتم تزويد العداد بالخطوة المحددة والتحقق من شرط الاستمرار.",
        "syntax": "FinPour",
        "example": "Pour k <- 1 à 3 Faire\n    Ecrire(\"مرحباً بالعالم\");\nFinPour",
        "tip": "تجنب تعديل قيمة عداد الحلقة يدوياً داخل جسم الحلقة بالتعليمة (<-)."
    },
    "TantQue": {
        "title": "حلقة التكرار الشرطية طالما (TantQue)",
        "category": "البنى التكرارية",
        "description": "تكرر مجموعة من التعليمات طالما بقي الشرط المنطقي صحيحاً (Vrai). يتم فحص الشرط في البداية قبل الدخول في كل دورة.",
        "syntax": "TantQue <Condition> Faire\n    // التعليمات\nFinTantQue",
        "example": "i <- 1;\nTantQue i <= 5 Faire\n    Ecrire(\"العدد: \", i);\n    i <- i + 1; // زيادة العداد\nFinTantQue",
        "tip": "تأكد دائماً من وجود تعليمة داخل الحلقة تؤثر على متغير الشرط، وإلا ستدخل الخوارزمية في حلقة لانهائية (Boucle infinie)!"
    },
    "FinTantQue": {
        "title": "نهاية حلقة TantQue (FinTantQue)",
        "category": "البنى التكرارية",
        "description": "تحدد نهاية جسم حلقة TantQue، وعندها يعود التنفيذ لفحص الشرط في بداية الحلقة من جديد.",
        "syntax": "FinTantQue",
        "example": "TantQue solde > 0 Faire\n    solde <- solde - 100;\nFinTantQue",
        "tip": "لكل TantQue كلمة FinTantQue مقابلة لها تغلق نطاقها."
    },
    "Répéter": {
        "title": "حلقة كرر حتى (Répéter ... Jusqu'à)",
        "category": "البنى التكرارية",
        "description": "تُنفذ التعليمات أولاً ثم تفحص شرط التوقف في النهاية. تتوقف عندما يصبح الشرط صحيحاً (Vrai)، وتضمن التنفيذ لمرة واحدة على الأقل.",
        "syntax": "Répéter\n    // التعليمات (تنفذ مرة واحدة على الأقل)\nJusqu'à <Condition>;",
        "example": "Répéter\n    Ecrire(\"أدخل عدداً موجباً: \");\n    Lire(n);\nJusqu'à n > 0;",
        "tip": "على عكس TantQue، حلقة Répéter تنفذ محتواها مرة واحدة على الأقل لأن فحص الشرط يقع في النهاية."
    },
    "Jusqu'à": {
        "title": "شرط التوقف حتى (Jusqu'à)",
        "category": "البنى التكرارية",
        "description": "تحدد شرط التوقف لحلقة Répéter، وتنهي التكرار بمجرد أن يتحقق الشرط ويصبح صحيحاً (Vrai).",
        "syntax": "Jusqu'à <Condition>;",
        "example": "cpt <- 0;\nRépéter\n    cpt <- cpt + 1;\nJusqu'à cpt = 10;",
        "tip": "سطر Jusqu'à ينتهي بفاصلة منقوطة (;)، وتتوقف الحلقة عندما يكون الشرط Vrai."
    }
}


class KeywordButton(QPushButton):
    """زر كلمة محجوزة مع دعم النقر بالزر الأيمن لعرض نافذة الشرح"""
    rightClicked = pyqtSignal()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self.rightClicked.emit()
            event.accept()
            return
        super().mousePressEvent(event)


class KeywordHelpDialog(QDialog):
    """نافذة أنيقة ومتناسقة مع واجهة MyAlgo لشرح التعليمة وعرض أمثلتها"""
    
    def __init__(self, keyword, parent=None):
        super().__init__(parent)
        self.keyword = keyword
        self.doc = KEYWORD_DOCS.get(keyword, {
            "title": f"التعليمة {keyword}",
            "category": "كلمة محجوزة",
            "description": f"الكلمة المحجوزة '{keyword}' مستخدمة في خوارزميات MyAlgo.",
            "syntax": f"{keyword} ...",
            "example": f"// مثال استخدام {keyword}\n{keyword}",
            "tip": "تأكد من كتابة الكلمة في موقعها الصحيح حسب قواعد لغة الخوارزميات."
        })
        
        self.setWindowTitle(f"شرح التعليمة: {keyword}")
        self.resize(580, 640)
        self.setMinimumSize(500, 520)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        # تنسيق النافذة العام
        self.setStyleSheet("""
            QDialog {
                background-color: #FFFFFF;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
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
        
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(22, 20, 22, 18)
        main_layout.setSpacing(14)
        
        # ── 1. ترويسة أنيقة (Header Card) ──
        header_widget = QWidget()
        header_widget.setStyleSheet("""
            QWidget {
                background: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 10px;
            }
        """)
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(16, 14, 16, 14)
        header_layout.setSpacing(12)
        
        # معلومات العنوان والتصنيف
        info_layout = QVBoxLayout()
        info_layout.setSpacing(5)
        
        title_label = QLabel(self.doc["title"])
        title_label.setFont(QFont("Cairo", 15, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #0F172A; border: none; background: transparent;")
        info_layout.addWidget(title_label)
        
        cat_badge = QLabel(f"  {self.doc['category']}  ")
        cat_badge.setFont(QFont("Cairo", 9, QFont.Weight.DemiBold))
        cat_badge.setStyleSheet("""
            color: #2563EB;
            background-color: #EFF6FF;
            border: 1px solid #BFDBFE;
            border-radius: 6px;
            padding: 2px 6px;
        """)
        cat_badge.setFixedHeight(22)
        
        cat_row = QHBoxLayout()
        cat_row.addWidget(cat_badge)
        cat_row.addStretch()
        info_layout.addLayout(cat_row)
        header_layout.addLayout(info_layout, stretch=1)
        
        # بطاقة الكلمة المحجوزة بخط JetBrains Mono
        kw_box = QLabel(f"\u202D{self.keyword}\u202C")
        kw_box.setFont(QFont("JetBrains Mono", 15, QFont.Weight.Bold))
        kw_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        kw_box.setStyleSheet("""
            color: #1D4ED8;
            background-color: #DBEAFE;
            border: 1px solid #93C5FD;
            border-radius: 8px;
            padding: 6px 16px;
        """)
        header_layout.addWidget(kw_box)
        main_layout.addWidget(header_widget)
        
        # ── 2. المحتوى القابل للتمرير (Scroll Area) ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(4, 4, 12, 4)
        scroll_layout.setSpacing(14)
        
        # أ. الشرح والتوضيح
        desc_box = self._create_section_card(
            title="📖 الشرح والتوضيح",
            color="#2563EB",
            content_widget=self._create_text_label(self.doc["description"])
        )
        scroll_layout.addWidget(desc_box)
        
        # ب. الصيغة العامة (Syntaxe) مع تلوين الكود
        syntax_ed = self._create_code_box(self.doc["syntax"])
        syntax_box = self._create_section_card(
            title="📐 الصيغة العامة (Syntaxe)",
            color="#0D9488",
            content_widget=syntax_ed
        )
        scroll_layout.addWidget(syntax_box)
        
        # ج. مثال تطبيقي (Exemple) مع تلوين الكود وزر نسخ مدمج
        example_ed = self._create_code_box(self.doc["example"])
        example_box = self._create_section_card(
            title="💻 مثال تطبيقي (Exemple)",
            color="#7C3AED",
            content_widget=example_ed
        )
        scroll_layout.addWidget(example_box)
        
        # د. إضاءة تعليمية / نصيحة (Tip)
        tip_box = QWidget()
        tip_box.setStyleSheet("""
            QWidget {
                background-color: #FEF9C3;
                border: 1px solid #FDE047;
                border-radius: 8px;
            }
        """)
        tip_layout = QHBoxLayout(tip_box)
        tip_layout.setContentsMargins(14, 12, 14, 12)
        tip_layout.setSpacing(10)
        
        tip_icon = QLabel("💡")
        tip_icon.setFont(QFont("Segoe UI Emoji", 15))
        tip_icon.setStyleSheet("border: none; background: transparent;")
        tip_layout.addWidget(tip_icon)
        
        tip_text = QLabel(f"<b>تلميح هام:</b> {self.doc['tip']}")
        tip_text.setFont(QFont("Cairo", 10))
        tip_text.setWordWrap(True)
        tip_text.setStyleSheet("color: #854D0E; border: none; background: transparent; line-height: 140%;")
        tip_layout.addWidget(tip_text, stretch=1)
        scroll_layout.addWidget(tip_box)
        
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll, stretch=1)
        
        # ── 3. شريط الأزرار السفلي (Footer Actions) ──
        btn_bar = QHBoxLayout()
        btn_bar.setSpacing(10)
        
        # زر نسخ المثال
        self.btn_copy = QPushButton("📋 نسخ المثال")
        self.btn_copy.setFont(QFont("Cairo", 10, QFont.Weight.Bold))
        self.btn_copy.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_copy.setStyleSheet("""
            QPushButton {
                background-color: #F1F5F9;
                color: #334155;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 7px 16px;
            }
            QPushButton:hover {
                background-color: #E2E8F0;
                color: #0F172A;
            }
        """)
        self.btn_copy.clicked.connect(self._copy_example)
        btn_bar.addWidget(self.btn_copy)
        
        # زر إدراج المثال في المحرر
        self.btn_insert = QPushButton("➕ إدراج المثال في المحرر")
        self.btn_insert.setFont(QFont("Cairo", 10, QFont.Weight.Bold))
        self.btn_insert.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_insert.setStyleSheet("""
            QPushButton {
                background-color: #EFF6FF;
                color: #1D4ED8;
                border: 1px solid #BFDBFE;
                border-radius: 6px;
                padding: 7px 18px;
            }
            QPushButton:hover {
                background-color: #DBEAFE;
                color: #1E40AF;
            }
        """)
        self.btn_insert.clicked.connect(self._insert_example)
        btn_bar.addWidget(self.btn_insert)
        
        btn_bar.addStretch()
        
        # زر الإغلاق
        self.btn_close = QPushButton("إغلاق")
        self.btn_close.setFont(QFont("Cairo", 10, QFont.Weight.Bold))
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 7px 24px;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
        """)
        self.btn_close.clicked.connect(self.accept)
        btn_bar.addWidget(self.btn_close)
        
        main_layout.addLayout(btn_bar)

    def _create_section_card(self, title, color, content_widget):
        """إنشاء بطاقة قسم منسقة بعنوان وأيقونة"""
        card = QWidget()
        card.setStyleSheet("""
            QWidget {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
            }
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)
        
        header = QLabel(title)
        header.setFont(QFont("Cairo", 11, QFont.Weight.Bold))
        header.setStyleSheet(f"color: {color}; border: none; background: transparent;")
        layout.addWidget(header)
        
        content_widget.setParent(card)
        layout.addWidget(content_widget)
        return card

    def _create_text_label(self, text):
        lbl = QLabel(text)
        lbl.setFont(QFont("Cairo", 10))
        lbl.setWordWrap(True)
        lbl.setStyleSheet("color: #334155; border: none; background: transparent; line-height: 145%;")
        return lbl

    def _create_code_box(self, code_text):
        """إنشاء محرر نصوص مصغر للعرض البرمجي مع تلوين الشيفرة"""
        ed = QPlainTextEdit()
        ed.setReadOnly(True)
        ed.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        ed.setFont(QFont("JetBrains Mono", 11))
        ed.setPlainText(code_text)
        
        # ربط الملوّن الدلالي للغة الخوارزميات
        ed._highlighter = AlgoHighlighter(ed.document())
        
        # حساب الارتفاع المناسب لعدد الأسطر لمنع ظهور شريط التمرير
        lines = code_text.strip().count('\n') + 1
        fm = ed.fontMetrics()
        line_h = fm.lineSpacing()
        h = max(48, lines * line_h + 24)
        ed.setFixedHeight(h)
        ed.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        ed.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        ed.setStyleSheet("""
            QPlainTextEdit {
                background-color: #F8FAFC;
                color: #0F172A;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 6px 12px;
                selection-background-color: #DBEAFE;
                selection-color: #1E3A8A;
                font-family: 'JetBrains Mono';
            }
        """)
        return ed

    def _copy_example(self):
        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(self.doc["example"])
            self.btn_copy.setText("✅ تم النسخ!")
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(1800, lambda: self.btn_copy.setText("📋 نسخ المثال"))

    def _insert_example(self):
        parent = self.parent()
        if parent and hasattr(parent, "editor"):
            tc = parent.editor.textCursor()
            tc.insertText("\n" + self.doc["example"] + "\n")
            parent.editor.setTextCursor(tc)
            parent.editor.setFocus()
            self.accept()

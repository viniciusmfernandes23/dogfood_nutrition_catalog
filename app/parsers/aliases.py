from __future__ import annotations

NUTRIENT_ALIASES = {

    "protein": [
        "proteína bruta",
        "proteina bruta",
        "pb",
        "proteína mínima",
        "proteina minima",
        r"proteína bruta \(mín\.?\)",
        r"proteina bruta \(min\.?\)",
    ],

    "fat": [
        "extrato etéreo",
        "extrato etereo",
        "ee",
        "gordura",
        "lipídios",
        "lipidios",
        r"extrato etéreo \(mín\.?\)",
        r"extrato etereo \(min\.?\)",
    ],

    "fiber": [
        "fibra bruta",
        "fibra alimentar",
        "fibra",
        "fibras",
        "matéria fibrosa",
        "materia fibrosa",
        "fb",
        "extrato fibroso",
        "material fibroso",
    ],

    "ash": [
        "matéria mineral",
        "materia mineral",
        "cinzas",
        "mm",
        r"matéria mineral \(máx\.?\)",
        r"materia mineral \(max\.?\)",
    ],

    "moisture": [
        "umidade",
        r"umidade \(máx\.?\)",
        r"umidade \(max\.?\)",
    ],

    "calcium_max": [
        r"cálcio \(máx\.?\)",
        r"calcio \(max\.?\)",
        r"cálcio máx\.?",
        r"calcio max\.?",
        "cálcio máximo",
        "calcio maximo",
        r"cálcio\s*,\s*máx",
        r"calcio\s*,\s*max",
    ],

    "calcium_min": [
        r"cálcio \(mín\.?\)",
        r"calcio \(min\.?\)",
        r"cálcio mín\.?",
        r"calcio min\.?",
        "cálcio mínimo",
        "calcio minimo",
        r"cálcio\s*,\s*mín",
        r"calcio\s*,\s*min",
        r"cálcio(?!\s*\(?máx)",
        r"calcio(?!\s*\(?max)",
    ],

    "phosphorus": [
        r"fósforo \(mín\.?\)",
        r"fosforo \(min\.?\)",
        r"fósforo mín\.?",
        r"fosforo min\.?",
        "fósforo",
        "fosforo",
        r"fósforo\s*,\s*mín",
        r"fosforo\s*,\s*min",
        "p",
    ],

    "sodium": [
        "sódio",
        "sodio",
        r"sódio \(mín\.?\)",
        r"sodio \(min\.?\)",
        r"sódio\s*,\s*mín",
        r"sodio\s*,\s*min",
    ],

    "potassium": [
        "potássio",
        "potassio",
        r"potássio \(mín\.?\)",
        r"potassio \(min\.?\)",
        r"potássio\s*,\s*mín",
        r"potassio\s*,\s*min",
        "k",
    ],

    "metabolizable_energy": [
        "energia metabolizável",
        "energia metabolizavel",
        "em",
        "valor energético",
        "valor energetico",
        "energia metabolizável (mín)",
        "energia metabolizavel (min)",
    ],

    # ------------------------------------------------------
    # Aminoácidos
    # ------------------------------------------------------
    "lysine": [
        "lisina",
        "l-lisina",
        r"lisina \(mín\.?\)",
    ],
    "methionine": [
        "metionina",
        "dl-metionina",
        r"metionina \(mín\.?\)",
    ],
    "tryptophan": [
        "triptofano",
        "l-triptofano",
        r"triptofano \(mín\.?\)",
    ],
    "arginine": [
        "arginina",
        "l-arginina",
        r"arginina \(mín\.?\)",
    ],
    "taurine": [
        "taurina",
        r"taurina \(mín\.?\)",
    ],
    "l_carnitine": [
        "l-carnitina",
        "carnitina",
        r"l-carnitina \(mín\.?\)",
    ],

    # ------------------------------------------------------
    # Ácidos Graxos
    # ------------------------------------------------------
    "omega_3": [
        "ômega 3",
        "omega 3",
        "ácido linolênico",
        "acido linolenico",
        r"ômega 3 \(mín\.?\)",
        r"omega 3 \(mín\.?\)",
    ],
    "omega_6": [
        "ômega 6",
        "omega 6",
        "ácido linoleico",
        "acido linoleico",
        r"ômega 6 \(mín\.?\)",
        r"omega 6 \(mín\.?\)",
    ],
    "epa_dha": [
        "epa+dha",
        "epa + dha",
        "epa e dha",
    ],

    # ------------------------------------------------------
    # Microminerais (Oligoelementos)
    # ------------------------------------------------------
    "magnesium": [
        "magnésio",
        "magnesio",
        "mg",
    ],
    "chlorine": [
        "cloro",
        "cloreto",
        "cl",
    ],
    "iron": [
        "ferro",
        "fe",
    ],
    "zinc": [
        "zinco",
        "zn",
    ],
    "copper": [
        "cobre",
        "cu",
    ],
    "selenium": [
        "selênio",
        "selenio",
        "se",
    ],
    "iodine": [
        "iodo",
        "i",
    ],
    "manganese": [
        "manganês",
        "manganes",
        "mn",
    ],

    # ------------------------------------------------------
    # Vitaminas
    # ------------------------------------------------------
    "vitamin_a": [
        "vitamina a",
        "vit. a",
        "vit a",
    ],
    "vitamin_d3": [
        "vitamina d3",
        "vit. d3",
        "vit d3",
        "vitamina d",
    ],
    "vitamin_e": [
        "vitamina e",
        "vit. e",
        "vit e",
    ],
    "vitamin_b1": [
        "vitamina b1",
        "vit. b1",
        "vit b1",
        "tiamina",
    ],
    "vitamin_b2": [
        "vitamina b2",
        "vit. b2",
        "vit b2",
        "riboflavina",
    ],
    "vitamin_b6": [
        "vitamina b6",
        "vit. b6",
        "vit b6",
        "piridoxina",
    ],
    "vitamin_b12": [
        "vitamina b12",
        "vit. b12",
        "vit b12",
        "cianocobalamina",
    ],
    "niacin": [
        "niacina",
        "ácido nicotínico",
        "acido nicotinico",
        "vitamina b3",
    ],
    "pantothenic_acid": [
        "ácido pantotênico",
        "acido pantotenico",
        "pantotenato de cálcio",
        "vitamina b5",
    ],
    "folic_acid": [
        "ácido fólico",
        "acido folico",
        "vitamina b9",
    ],
    "biotin": [
        "biotina",
        "vitamina b7",
        "vitamina h",
    ],
    "choline": [
        "colina",
        "cloreto de colina",
    ],
    "vitamin_c": [
        "vitamina c",
        "ácido ascórbico",
        "acido ascorbico",
    ],
    "vitamin_k3": [
        "vitamina k3",
        "vit. k3",
        "menadiona",
    ],

    # ------------------------------------------------------
    # Outros
    # ------------------------------------------------------
    "beta_glucans": [
        "beta-glucanas",
        "beta glucanos",
    ],
    "mos": [
        "mananoligossacarídeos",
        "mananoligossacarideos",
        "mos",
    ],
}

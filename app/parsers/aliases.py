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

}
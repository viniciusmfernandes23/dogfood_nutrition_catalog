from __future__ import annotations

NUTRIENT_ALIASES = {

    "protein": [

        "proteína bruta",
        "proteina bruta",
        "pb",
        "proteína mínima",
        "proteina minima",

    ],

    "fat": [

        "extrato etéreo",
        "extrato etereo",
        "ee",
        "gordura",
        "lipídios",
        "lipidios",

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

    ],

    "moisture": [

        "umidade",

    ],

        "calcium_max": [
        r"cálcio \(máx\.?\)",
        r"calcio \(max\.?\)",
        r"cálcio máx\.?",
        r"calcio max\.?",
        "cálcio máximo",
        "calcio maximo",
    ],

    "calcium_min": [
        r"cálcio \(mín\.?\)",
        r"calcio \(min\.?\)",
        r"cálcio mín\.?",
        r"calcio min\.?",
        "cálcio mínimo",
        "calcio minimo",
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
        "p",
    ],

    "sodium": [

        "sódio",
        "sodio",

    ],

    "potassium": [

        "potássio",
        "potassio",

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
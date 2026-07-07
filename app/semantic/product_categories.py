from __future__ import annotations

from types import MappingProxyType

PRODUCT_RULES = MappingProxyType({

    "Ração Seca": (

        "ração seca",

        "extrusada",

        "extrusado",

        "dry food",

        "dry",

    ),

    "Ração Úmida": (

        "ração úmida",

        "úmida",

        "sachê",

        "sache",

        "patê",

        "pate",

        "lata",

        "wet food",

    ),

    "Ração Clínica": (

        "clinical",

        "prescription",

        "prescription diet",

        "prescription food",

    ),

    "Ração Veterinária": (

        "veterinária",

        "veterinario",

        "veterinary",

        "vet diet",

    ),

    "Ração Natural": (

        "natural",

        "naturalis",

        "natural food",

    ),

    "Premium": (

        "premium",

    ),

    "Super Premium": (

        "super premium",

        "superpremium",

    ),

    "Petisco": (

        "petisco",

        "snack",

        "bifinho",

        "biscuit",

        "cookie",

        "osso",

        "bone",

        "treat",

    ),

    "Suplemento": (

        "suplemento",

        "suplementação",

        "vitamínico",

        "vitaminico",

        "suplement",

    ),

    "Funcional": (

        "funcional",

        "functional",

    ),

    "Terapêutica": (

        "renal",

        "hepatic",

        "hepático",

        "hepatico",

        "urinary",

        "urinário",

        "urinario",

        "diabetic",

        "diabético",

        "diabetico",

        "gastrointestinal",

        "obesity",

        "obesidade",

        "hypoallergenic",

        "hipoalergênica",

        "hipoalergenica",

        "cardiac",

        "cardíaca",

        "cardiaca",

        "mobility",

        "joint",

        "articular",

    ),

})


PRODUCT_CATEGORIES = tuple(PRODUCT_RULES.keys())
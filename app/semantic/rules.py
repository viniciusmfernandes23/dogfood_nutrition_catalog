from __future__ import annotations

from types import MappingProxyType

from app.semantic.categories import (
    BreedSize,
    ClinicalCategory,
    LifeStage,
    ProductCategory,
    ProductTier,
    ProteinSource,
)

# ==========================================================
# Produto
# ==========================================================

PRODUCT_CATEGORY_RULES = MappingProxyType({

    ProductCategory.DRY: (
        "ração seca",
        "extrusada",
        "extrusado",
        "dry food",
    ),

    ProductCategory.WET: (
        "ração úmida",
        "úmida",
        "sachê",
        "sache",
        "patê",
        "pate",
        "lata",
        "wet food",
    ),

    ProductCategory.CLINICAL: (
        "clinical",
        "prescription",
        "prescription diet",
        "diet",
    ),

    ProductCategory.VETERINARY: (
        "veterinary",
        "veterinária",
        "veterinario",
        "vet",
    ),

    ProductCategory.NATURAL: (
        "natural",
        "grain free",
        "holístico",
        "holistico",
    ),

    ProductCategory.PREMIUM: (
        "premium",
    ),

    ProductCategory.SUPER_PREMIUM: (
        "super premium",
        "superpremium",
    ),

    ProductCategory.TREAT: (
        "petisco",
        "snack",
        "bifinho",
        "cookie",
        "biscoito",
        "treat",
    ),

    ProductCategory.SUPPLEMENT: (
        "suplemento",
        "suplementação",
        "suplementacao",
        "vitamínico",
        "vitaminico",
    ),

    ProductCategory.FUNCTIONAL: (
        "funcional",
        "functional",
    ),

    ProductCategory.THERAPEUTIC: (
        "terapêutica",
        "terapeutica",
    ),

})

# ==========================================================
# Fase de Vida
# ==========================================================

LIFESTAGE_RULES = MappingProxyType({

    LifeStage.PUPPY: (
        "filhote",
        "puppy",
        "junior",
        "júnior",
    ),

    LifeStage.ADULT: (
        "adulto",
        "adult",
    ),

    LifeStage.SENIOR: (
        "sênior",
        "senior",
        "idoso",
        "mature",
    ),

    LifeStage.ALL: (
        "todos",
        "todas as idades",
        "all life stages",
    ),

})

# ==========================================================
# Porte
# ==========================================================

BREED_SIZE_RULES = MappingProxyType({

    BreedSize.MINI: (
        "mini",
        "miniatura",
    ),

    BreedSize.SMALL: (
        "pequeno porte",
        "small",
        "small breed",
    ),

    BreedSize.MEDIUM: (
        "médio porte",
        "medio porte",
        "medium",
    ),

    BreedSize.LARGE: (
        "grande porte",
        "large",
        "large breed",
    ),

    BreedSize.GIANT: (
        "gigante",
        "giant",
    ),

    BreedSize.ALL: (
        "todos os portes",
        "all breeds",
        "all sizes",
    ),

})

# ==========================================================
# Categoria Clínica
# ==========================================================

CLINICAL_RULES = MappingProxyType({

    ClinicalCategory.RENAL: (
        "renal",
        "kidney",
    ),

    ClinicalCategory.HEPATIC: (
        "hepatic",
        "hepática",
        "hepatica",
        "liver",
    ),

    ClinicalCategory.URINARY: (
        "urinary",
        "urinário",
        "urinario",
        "trato urinário",
        "trato urinario",
    ),

    ClinicalCategory.GASTROINTESTINAL: (
        "gastrointestinal",
        "digestive",
        "digestivo",
        "intestinal",
    ),

    ClinicalCategory.DIABETIC: (
        "diabetes",
        "diabetic",
    ),

    ClinicalCategory.HYPOALLERGENIC: (
        "hipoalergênica",
        "hipoalergenica",
        "hypoallergenic",
        "allergenic",
    ),

    ClinicalCategory.OBESITY: (
        "obesity",
        "obesidade",
        "weight control",
        "controle de peso",
    ),

})

# ==========================================================
# Fonte de Proteína
# ==========================================================

PROTEIN_RULES = MappingProxyType({

    ProteinSource.CHICKEN: (
        "frango",
        "chicken",
    ),

    ProteinSource.BEEF: (
        "carne",
        "carne bovina",
        "beef",
        "bovina",
    ),

    ProteinSource.LAMB: (
        "cordeiro",
        "lamb",
    ),

    ProteinSource.SALMON: (
        "salmão",
        "salmao",
        "salmon",
    ),

    ProteinSource.PORK: (
        "suíno",
        "suino",
        "pork",
    ),

    ProteinSource.TURKEY: (
        "peru",
        "turkey",
    ),

    ProteinSource.FISH: (
        "peixe",
        "fish",
        "atum",
        "tilápia",
        "tilapia",
        "truta",
    ),

})

# ==========================================================
# Nível do Produto
# ==========================================================

PRODUCT_TIER_RULES = MappingProxyType({

    ProductTier.ULTRA_PREMIUM: (
        "ultra premium",
    ),

    ProductTier.SUPER_PREMIUM: (
        "super premium",
        "superpremium",
    ),

    ProductTier.PREMIUM: (
        "premium",
    ),

    ProductTier.NATURAL: (
        "natural",
        "grain free",
    ),

    ProductTier.VETERINARY: (
        "veterinary",
        "prescription",
        "veterinária",
        "veterinario",
    ),

})

# ==========================================================
# Registry
# ==========================================================

SEMANTIC_RULES = MappingProxyType({

    "product_category": PRODUCT_CATEGORY_RULES,

    "life_stage": LIFESTAGE_RULES,

    "breed_size": BREED_SIZE_RULES,

    "clinical_category": CLINICAL_RULES,

    "protein_source": PROTEIN_RULES,

    "product_tier": PRODUCT_TIER_RULES,

})
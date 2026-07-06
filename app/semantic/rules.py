from __future__ import annotations

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

PRODUCT_CATEGORY_RULES: dict[ProductCategory, tuple[str, ...]] = {

    ProductCategory.DRY: (
        "ração seca",
        "ração para cães",
        "ração cachorro",
    ),

    ProductCategory.WET: (
        "ração úmida",
        "sachê",
        "lata",
        "patê",
    ),

    ProductCategory.CLINICAL: (
        "prescrição",
        "prescription",
        "clinical",
        "diet",
    ),

    ProductCategory.VETERINARY: (
        "veterinary",
        "veterinária",
        "veterinary diet",
    ),

    ProductCategory.NATURAL: (
        "natural",
        "grain free",
        "holístico",
    ),

    ProductCategory.PREMIUM: (
        "premium",
    ),

    ProductCategory.SUPER_PREMIUM: (
        "super premium",
    ),

    ProductCategory.TREAT: (
        "petisco",
        "bifinho",
        "snack",
        "biscoito",
        "cookie",
    ),

    ProductCategory.SUPPLEMENT: (
        "suplemento",
        "suplementação",
        "vitamínico",
    ),

    ProductCategory.FUNCTIONAL: (
        "funcional",
    ),

    ProductCategory.THERAPEUTIC: (
        "terapêutica",
    ),
}

# ==========================================================
# Fase de Vida
# ==========================================================

LIFESTAGE_RULES: dict[LifeStage, tuple[str, ...]] = {

    LifeStage.PUPPY: (
        "filhote",
        "puppy",
        "júnior",
    ),

    LifeStage.ADULT: (
        "adulto",
        "adult",
    ),

    LifeStage.SENIOR: (
        "sênior",
        "senior",
        "mature",
        "idoso",
    ),

    LifeStage.ALL: (
        "todos",
        "todas as idades",
        "all life stages",
    ),
}

# ==========================================================
# Porte
# ==========================================================

BREED_SIZE_RULES: dict[BreedSize, tuple[str, ...]] = {

    BreedSize.MINI: (
        "mini",
        "miniatura",
    ),

    BreedSize.SMALL: (
        "pequeno porte",
        "small",
    ),

    BreedSize.MEDIUM: (
        "médio porte",
        "medium",
    ),

    BreedSize.LARGE: (
        "grande porte",
        "large",
    ),

    BreedSize.GIANT: (
        "gigante",
        "giant",
    ),

    BreedSize.ALL: (
        "todos os portes",
        "all breeds",
    ),
}

# ==========================================================
# Categoria Clínica
# ==========================================================

CLINICAL_RULES: dict[ClinicalCategory, tuple[str, ...]] = {

    ClinicalCategory.RENAL: (
        "renal",
        "kidney",
    ),

    ClinicalCategory.HEPATIC: (
        "hepatic",
        "hepática",
        "liver",
    ),

    ClinicalCategory.URINARY: (
        "urinary",
        "urinário",
        "trato urinário",
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
        "hypoallergenic",
        "allergenic",
    ),

    ClinicalCategory.OBESITY: (
        "obesity",
        "obesidade",
        "weight control",
        "controle de peso",
    ),
}

# ==========================================================
# Fonte de Proteína
# ==========================================================

PROTEIN_RULES: dict[ProteinSource, tuple[str, ...]] = {

    ProteinSource.CHICKEN: (
        "frango",
        "chicken",
    ),

    ProteinSource.BEEF: (
        "carne",
        "beef",
        "bovina",
    ),

    ProteinSource.LAMB: (
        "cordeiro",
        "lamb",
    ),

    ProteinSource.SALMON: (
        "salmão",
        "salmon",
    ),

    ProteinSource.PORK: (
        "suíno",
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
        "truta",
    ),
}

# ==========================================================
# Nível do Produto
# ==========================================================

PRODUCT_TIER_RULES: dict[ProductTier, tuple[str, ...]] = {

    ProductTier.ULTRA_PREMIUM: (
        "ultra premium",
    ),

    ProductTier.SUPER_PREMIUM: (
        "super premium",
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
    ),
}

# ==========================================================
# Helpers
# ==========================================================

SEMANTIC_RULES = {

    "product_category": PRODUCT_CATEGORY_RULES,

    "life_stage": LIFESTAGE_RULES,

    "breed_size": BREED_SIZE_RULES,

    "clinical_category": CLINICAL_RULES,

    "protein_source": PROTEIN_RULES,

    "product_tier": PRODUCT_TIER_RULES,

}
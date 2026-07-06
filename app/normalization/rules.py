from __future__ import annotations

from app.normalization.models import NormalizationRule


# ==========================================================
# Fatores de conversão
# ==========================================================

GKG_TO_MGKG_FACTOR = 1000.0

PERCENT_TO_GKG_FACTOR = 10.0

PERCENT_TO_MGKG_FACTOR = 10000.0


# ==========================================================
# Regras de Normalização
# ==========================================================

NORMALIZATION_RULES: dict[str, NormalizationRule] = {

    # ------------------------------------------------------
    # Macronutrientes
    # ------------------------------------------------------

    "protein_gkg": NormalizationRule(
        field="protein_gkg",
        target_min=60,
        target_max=600,
        overscale_factor=10,
        percent_factor=PERCENT_TO_GKG_FACTOR,
    ),

    "fat_gkg": NormalizationRule(
        field="fat_gkg",
        target_min=20,
        target_max=400,
        overscale_factor=10,
        percent_factor=PERCENT_TO_GKG_FACTOR,
    ),

    "fiber_gkg": NormalizationRule(
        field="fiber_gkg",
        target_min=5,
        target_max=250,
        overscale_factor=100,
        percent_factor=PERCENT_TO_GKG_FACTOR,
    ),

    "ash_gkg": NormalizationRule(
        field="ash_gkg",
        target_min=10,
        target_max=200,
        overscale_factor=100,
        percent_factor=PERCENT_TO_GKG_FACTOR,
    ),

    "moisture_gkg": NormalizationRule(
        field="moisture_gkg",
        target_min=60,
        target_max=900,
        percent_factor=PERCENT_TO_GKG_FACTOR,
    ),

    # ------------------------------------------------------
    # Minerais
    # ------------------------------------------------------

    "calcium_min_mgkg": NormalizationRule(
        field="calcium_min_mgkg",
        target_min=1500,
        target_max=50000,
        overscale_factor=10,
        decimal_shift_factor=100,
        percent_factor=PERCENT_TO_MGKG_FACTOR,
        gkg_to_mgkg=True,
    ),

    "calcium_max_mgkg": NormalizationRule(
        field="calcium_max_mgkg",
        target_min=1500,
        target_max=50000,
        overscale_factor=10,
        decimal_shift_factor=100,
        percent_factor=PERCENT_TO_MGKG_FACTOR,
        gkg_to_mgkg=True,
    ),

    "phosphorus_mgkg": NormalizationRule(
        field="phosphorus_mgkg",
        target_min=1000,
        target_max=30000,
        overscale_factor=10,
        percent_factor=PERCENT_TO_MGKG_FACTOR,
        gkg_to_mgkg=True,
    ),

    "sodium_mgkg": NormalizationRule(
        field="sodium_mgkg",
        target_min=800,
        target_max=20000,
        overscale_factor=10,
        percent_factor=PERCENT_TO_MGKG_FACTOR,
        gkg_to_mgkg=True,
    ),

    "potassium_mgkg": NormalizationRule(
        field="potassium_mgkg",
        target_min=1500,
        target_max=50000,
        overscale_factor=10,
        percent_factor=PERCENT_TO_MGKG_FACTOR,
        gkg_to_mgkg=True,
    ),

}


# ==========================================================
# Agrupamentos
# ==========================================================

MACRONUTRIENTS = (
    "protein_gkg",
    "fat_gkg",
    "fiber_gkg",
    "ash_gkg",
    "moisture_gkg",
)

MINERALS = (
    "calcium_min_mgkg",
    "calcium_max_mgkg",
    "phosphorus_mgkg",
    "sodium_mgkg",
    "potassium_mgkg",
)

NORMALIZABLE_FIELDS = tuple(NORMALIZATION_RULES.keys())


# ==========================================================
# Status possíveis
# ==========================================================

STATUS_NORMALIZED = "normalized"

STATUS_AUTO_CORRECTED = "auto_corrected"

STATUS_MANUAL_REVIEW = "manual_review"

STATUS_AMBIGUOUS = "ambiguous"

STATUS_IMPLAUSIBLE = "implausible"


# ==========================================================
# Prioridade das regras
#
# Quanto menor o índice,
# maior a prioridade.
# ==========================================================

RULE_PRIORITY = (

    "already_normalized",

    "overscale",

    "decimal_shift",

    "percent_conversion",

    "gkg_to_mgkg",

)


# ==========================================================
# Confiança atribuída
# ==========================================================

RULE_CONFIDENCE = {

    "already_normalized": 1.00,

    "overscale": 0.99,

    "decimal_shift": 0.98,

    "percent_conversion": 0.95,

    "gkg_to_mgkg": 0.90,

    "ambiguous": 0.40,

    "implausible": 0.00,

}


# ==========================================================
# Categorias de Qualidade
# ==========================================================

QUALITY_STATUS = {

    STATUS_NORMALIZED:
        "Normalizado",

    STATUS_AUTO_CORRECTED:
        "Corrigido automaticamente",

    STATUS_MANUAL_REVIEW:
        "Requer revisão manual",

    STATUS_AMBIGUOUS:
        "Ambíguo",

    STATUS_IMPLAUSIBLE:
        "Implausível",

}


# ==========================================================
# Helpers
# ==========================================================

def get_rule(field: str) -> NormalizationRule:
    """
    Retorna a regra de normalização
    correspondente ao campo.
    """
    return NORMALIZATION_RULES[field]


def is_macro(field: str) -> bool:
    """
    Verifica se o campo é um macronutriente.
    """
    return field in MACRONUTRIENTS


def is_mineral(field: str) -> bool:
    """
    Verifica se o campo é um mineral.
    """
    return field in MINERALS
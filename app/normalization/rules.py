from __future__ import annotations

from app.normalization.models import (
    NormalizationRule,
    ValidationStatus,
)

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

    # NOTA DE PROJETO: Os valores extraídos pelo parser seguem uma escala de 10x 
    # para preservar uma casa decimal em formato inteiro (ex: 26.0% vira 260).
    # As regras abaixo foram ajustadas para que a normalização converta esses 
    # valores para a unidade física real (g/kg ou mg/kg) sem o fator 10x.

    "protein_gkg": NormalizationRule(
        field="protein_gkg",
        target_min=60,
        target_max=600,
        overscale_factor=1, # Removido fator 10x pois o valor já deve estar em g/kg
        percent_factor=PERCENT_TO_GKG_FACTOR,
    ),

    "fat_gkg": NormalizationRule(
        field="fat_gkg",
        target_min=20,
        target_max=400,
        overscale_factor=1, # Removido fator 10x
        percent_factor=PERCENT_TO_GKG_FACTOR,
    ),

    "fiber_gkg": NormalizationRule(
        field="fiber_gkg",
        target_min=5,
        target_max=250,
        overscale_factor=1,
        percent_factor=PERCENT_TO_GKG_FACTOR,
    ),

    "ash_gkg": NormalizationRule(
        field="ash_gkg",
        target_min=10,
        target_max=200,
        overscale_factor=10, # Permite corrigir se o valor 10x chegar aqui por erro de fluxo
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
        overscale_factor=10, # Permite corrigir se o valor 10x chegar aqui
        decimal_shift_factor=100,
        percent_factor=PERCENT_TO_MGKG_FACTOR,
        gkg_to_mgkg=True,
    ),

    "calcium_max_mgkg": NormalizationRule(
        field="calcium_max_mgkg",
        target_min=1500,
        target_max=50000,
        overscale_factor=10, # Permite corrigir se o valor 10x chegar aqui
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
        overscale_factor=10, # Permite corrigir se o valor 10x chegar aqui
        percent_factor=PERCENT_TO_MGKG_FACTOR,
        gkg_to_mgkg=True,
    ),

    "metabolizable_energy_kcalkg": NormalizationRule(
        field="metabolizable_energy_kcalkg",
        target_min=2000,
        target_max=6000,
        overscale_factor=1,
        decimal_shift_factor=1000, # Caso venha em kcal/g (ex: 3.5 -> 3500)
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

ENERGY = (
    "metabolizable_energy_kcalkg",
)

NORMALIZABLE_FIELDS = tuple(NORMALIZATION_RULES.keys())


# ==========================================================
# Prioridade das regras
#
# Quanto menor o índice,
# maior a prioridade.
# ==========================================================

RULE_PRIORITY = [

    "already_normalized",

    "overscale",

    "decimal_shift",

    "percent_conversion",

    "gkg_to_mgkg",

]


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

    "missing": 0.00,

    "implausible": 0.00,

}


# ==========================================================
# Categorias de Qualidade
# ==========================================================

QUALITY_STATUS = {

    ValidationStatus.NORMALIZED:
        "Normalizado",

    ValidationStatus.AUTO_CORRECTED:
        "Corrigido automaticamente",

    ValidationStatus.REVIEW:
        "Requer revisão manual",

    ValidationStatus.AMBIGUOUS:
        "Ambíguo",

    ValidationStatus.IMPLAUSIBLE:
        "Implausível",

    ValidationStatus.MISSING:
        "Sem informação",

}


# ==========================================================
# Helpers
# ==========================================================

def get_rule(
    field: str,
) -> NormalizationRule | None:
    """
    Retorna a regra de normalização do campo.
    """

    return NORMALIZATION_RULES.get(field)


def has_rule(
    field: str,
) -> bool:
    """
    Verifica se existe regra de normalização
    para o campo informado.
    """

    return field in NORMALIZATION_RULES


def is_macro(
    field: str,
) -> bool:
    """
    Verifica se o campo pertence ao grupo
    dos macronutrientes.
    """

    return field in MACRONUTRIENTS


def is_mineral(
    field: str,
) -> bool:
    """
    Verifica se o campo pertence ao grupo
    dos minerais.
    """

    return field in MINERALS


def get_confidence(
    rule_name: str,
) -> float:
    """
    Retorna a confiança associada
    à regra aplicada.
    """

    return RULE_CONFIDENCE.get(
        rule_name,
        0.0,
    )


def quality_label(
    status: ValidationStatus,
) -> str:
    """
    Retorna a descrição amigável
    do status de qualidade.
    """

    return QUALITY_STATUS.get(
        status,
        "Desconhecido",
    )
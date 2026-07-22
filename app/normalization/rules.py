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

    "protein_gkg": NormalizationRule(
        field="protein_gkg",
        target_min=60,
        target_max=600, # Reduzido de 1000 para 600 para capturar outliers impossíveis em rações completas
        overscale_factor=10,
        decimal_shift_factor=10,
        percent_factor=PERCENT_TO_GKG_FACTOR,
    ),

    "fat_gkg": NormalizationRule(
        field="fat_gkg",
        target_min=20,
        target_max=1000,
        overscale_factor=10,
        decimal_shift_factor=10,
        percent_factor=PERCENT_TO_GKG_FACTOR,
    ),

    "fiber_gkg": NormalizationRule(
        field="fiber_gkg",
        target_min=5,
        target_max=1000,
        overscale_factor=10,
        decimal_shift_factor=10,
        percent_factor=PERCENT_TO_GKG_FACTOR,
    ),

    "ash_gkg": NormalizationRule(
        field="ash_gkg",
        target_min=10,
        target_max=150, # Reduzido de 1000 para 150 (15%) conforme relatório item 3
        overscale_factor=10,
        decimal_shift_factor=10,
        percent_factor=PERCENT_TO_GKG_FACTOR,
    ),

    "moisture_gkg": NormalizationRule(
        field="moisture_gkg",
        target_min=60,
        target_max=1000,
        overscale_factor=10,
        decimal_shift_factor=10,
        percent_factor=PERCENT_TO_GKG_FACTOR,
    ),

    # ------------------------------------------------------
    # Minerais
    # ------------------------------------------------------

    "calcium_min_mgkg": NormalizationRule(
        field="calcium_min_mgkg",
        target_min=100,
        target_max=60000,
        overscale_factor=10,
        decimal_shift_factor=100,
        percent_factor=PERCENT_TO_MGKG_FACTOR,
        gkg_to_mgkg=True,
        decimal_shift_up=1000,
    ),

    "calcium_max_mgkg": NormalizationRule(
        field="calcium_max_mgkg",
        target_min=100,
        target_max=60000,
        overscale_factor=10,
        decimal_shift_factor=100,
        percent_factor=PERCENT_TO_MGKG_FACTOR,
        gkg_to_mgkg=True,
        decimal_shift_up=1000,
    ),

    "phosphorus_mgkg": NormalizationRule(
        field="phosphorus_mgkg",
        target_min=100, # Reduzido de 500 para 100 para aceitar valores como 400 mg/kg (Relatório Item 1)
        target_max=40000,
        overscale_factor=10,
        decimal_shift_factor=100,
        percent_factor=PERCENT_TO_MGKG_FACTOR,
        gkg_to_mgkg=True,
        decimal_shift_up=1000,
    ),

    "sodium_mgkg": NormalizationRule(
        field="sodium_mgkg",
        target_min=100, # Reduzido de 800 para 100 para aceitar valores como 300 mg/kg (Relatório Item 1)
        target_max=30000,
        overscale_factor=10,
        decimal_shift_factor=100,
        percent_factor=PERCENT_TO_MGKG_FACTOR,
        gkg_to_mgkg=True,
        decimal_shift_up=1000,
    ),

    "potassium_mgkg": NormalizationRule(
        field="potassium_mgkg",
        target_min=100, # Reduzido de 1500 para 100 para aceitar valores baixos plausíveis (Relatório Item 1)
        target_max=50000,
        overscale_factor=10,
        decimal_shift_factor=100,
        percent_factor=PERCENT_TO_MGKG_FACTOR,
        gkg_to_mgkg=True,
        decimal_shift_up=1000,
    ),

    # ------------------------------------------------------
    # Energia
    # ------------------------------------------------------

    "metabolizable_energy_kcalkg": NormalizationRule(
        field="metabolizable_energy_kcalkg",
        target_min=500,
        target_max=4500, # Reduzido de 9000 para 4500 para capturar outliers como 4810 kcal/kg
        overscale_factor=10,
        decimal_shift_factor=1000,
        percent_factor=10000,
    ),

    # ------------------------------------------------------
    # Aminoácidos (mg/kg)
    # ------------------------------------------------------
    "lysine_mgkg": NormalizationRule(
        field="lysine_mgkg",
        target_min=5000,
        target_max=50000,
        percent_factor=PERCENT_TO_MGKG_FACTOR,
        gkg_to_mgkg=True,
    ),
    "methionine_mgkg": NormalizationRule(
        field="methionine_mgkg",
        target_min=2000,
        target_max=20000,
        percent_factor=PERCENT_TO_MGKG_FACTOR,
        gkg_to_mgkg=True,
    ),
    "tryptophan_mgkg": NormalizationRule(
        field="tryptophan_mgkg",
        target_min=500,
        target_max=10000,
        percent_factor=PERCENT_TO_MGKG_FACTOR,
        gkg_to_mgkg=True,
    ),
    "arginine_mgkg": NormalizationRule(
        field="arginine_mgkg",
        target_min=5000,
        target_max=50000,
        percent_factor=PERCENT_TO_MGKG_FACTOR,
        gkg_to_mgkg=True,
    ),
    "taurine_mgkg": NormalizationRule(
        field="taurine_mgkg",
        target_min=500,
        target_max=10000,
        percent_factor=PERCENT_TO_MGKG_FACTOR,
        gkg_to_mgkg=True,
    ),
    "l_carnitine_mgkg": NormalizationRule(
        field="l_carnitine_mgkg",
        target_min=10,
        target_max=5000,
        percent_factor=PERCENT_TO_MGKG_FACTOR,
        gkg_to_mgkg=True,
    ),

    # ------------------------------------------------------
    # Ácidos Graxos (mg/kg ou g/kg)
    # ------------------------------------------------------
    "omega_3_mgkg": NormalizationRule(
        field="omega_3_mgkg",
        target_min=500,
        target_max=50000,
        percent_factor=PERCENT_TO_MGKG_FACTOR,
        gkg_to_mgkg=True,
    ),
    "omega_6_mgkg": NormalizationRule(
        field="omega_6_mgkg",
        target_min=5000,
        target_max=100000,
        percent_factor=PERCENT_TO_MGKG_FACTOR,
        gkg_to_mgkg=True,
    ),
    "epa_dha_mgkg": NormalizationRule(
        field="epa_dha_mgkg",
        target_min=100,
        target_max=20000,
        percent_factor=PERCENT_TO_MGKG_FACTOR,
        gkg_to_mgkg=True,
    ),

    # ------------------------------------------------------
    # Microminerais (mg/kg)
    # ------------------------------------------------------
    "magnesium_mgkg": NormalizationRule(
        field="magnesium_mgkg",
        target_min=100,
        target_max=2000,
        percent_factor=PERCENT_TO_MGKG_FACTOR,
        gkg_to_mgkg=True,
    ),
    "chlorine_mgkg": NormalizationRule(
        field="chlorine_mgkg",
        target_min=500,
        target_max=20000,
        percent_factor=PERCENT_TO_MGKG_FACTOR,
        gkg_to_mgkg=True,
    ),
    "iron_mgkg": NormalizationRule(
        field="iron_mgkg",
        target_min=10,
        target_max=1000,
        decimal_shift_up=1,
    ),
    "zinc_mgkg": NormalizationRule(
        field="zinc_mgkg",
        target_min=50,
        target_max=500,
        decimal_shift_up=1,
    ),
    "copper_mgkg": NormalizationRule(
        field="copper_mgkg",
        target_min=2,
        target_max=100,
        decimal_shift_up=1,
    ),
    "selenium_mgkg": NormalizationRule(
        field="selenium_mgkg",
        target_min=0.01, # Reduzido de 0.05 para 0.01 para aceitar valores como 0.04 mg/kg
        target_max=5,
        decimal_shift_up=1,
    ),
    "iodine_mgkg": NormalizationRule(
        field="iodine_mgkg",
        target_min=0.1,
        target_max=20,
        decimal_shift_up=1,
    ),
    "manganese_mgkg": NormalizationRule(
        field="manganese_mgkg",
        target_min=2,
        target_max=100,
        decimal_shift_up=1,
    ),

    # ------------------------------------------------------
    # Vitaminas (UI/kg ou mg/kg)
    # ------------------------------------------------------
    "vitamin_a_uikg": NormalizationRule(
        field="vitamin_a_uikg",
        target_min=1000,
        target_max=100000,
        decimal_shift_up=1,
    ),
    "vitamin_d3_uikg": NormalizationRule(
        field="vitamin_d3_uikg",
        target_min=100,
        target_max=10000,
        decimal_shift_up=1,
    ),
    "vitamin_e_uikg": NormalizationRule(
        field="vitamin_e_uikg",
        target_min=10,
        target_max=2000,
        decimal_shift_up=1,
    ),
    "vitamin_b1_mgkg": NormalizationRule(
        field="vitamin_b1_mgkg",
        target_min=1,
        target_max=100,
        decimal_shift_up=1,
    ),
    "vitamin_b2_mgkg": NormalizationRule(
        field="vitamin_b2_mgkg",
        target_min=1,
        target_max=100,
        decimal_shift_up=1,
    ),
    "vitamin_b6_mgkg": NormalizationRule(
        field="vitamin_b6_mgkg",
        target_min=1,
        target_max=100,
        decimal_shift_up=1,
    ),
    "vitamin_b12_mgkg": NormalizationRule(
        field="vitamin_b12_mgkg",
        target_min=0.005,
        target_max=1.0,
        decimal_shift_up=0.001, # Converte mcg para mg
    ),
    "niacin_mgkg": NormalizationRule(
        field="niacin_mgkg",
        target_min=10,
        target_max=300, # Reduzido de 500 para 300 para capturar outliers de ~495 mg/kg
        decimal_shift_up=1,
    ),
    "pantothenic_acid_mgkg": NormalizationRule(
        field="pantothenic_acid_mgkg",
        target_min=5,
        target_max=200,
        decimal_shift_up=1,
    ),
    "folic_acid_mgkg": NormalizationRule(
        field="folic_acid_mgkg",
        target_min=0.1,
        target_max=10,
        decimal_shift_up=1,
    ),
    "biotin_mgkg": NormalizationRule(
        field="biotin_mgkg",
        target_min=0.01,
        target_max=5, # Aumentado de 2 para 5 para aceitar valores plausíveis como 2.03 mg/kg
        decimal_shift_up=1,
    ),
    "choline_mgkg": NormalizationRule(
        field="choline_mgkg",
        target_min=100,
        target_max=5000,
        decimal_shift_up=1,
    ),
    "vitamin_c_mgkg": NormalizationRule(
        field="vitamin_c_mgkg",
        target_min=10,
        target_max=2000,
        decimal_shift_up=1,
    ),
    "vitamin_k3_mgkg": NormalizationRule(
        field="vitamin_k3_mgkg",
        target_min=0.1,
        target_max=20,
        decimal_shift_up=1,
    ),

    # ------------------------------------------------------
    # Outros
    # ------------------------------------------------------
    "beta_glucans_mgkg": NormalizationRule(
        field="beta_glucans_mgkg",
        target_min=100,
        target_max=20000,
        percent_factor=PERCENT_TO_MGKG_FACTOR,
        gkg_to_mgkg=True,
    ),
    "mos_mgkg": NormalizationRule(
        field="mos_mgkg",
        target_min=100,
        target_max=20000,
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
    "magnesium_mgkg",
    "chlorine_mgkg",
    "iron_mgkg",
    "zinc_mgkg",
    "copper_mgkg",
    "selenium_mgkg",
    "iodine_mgkg",
    "manganese_mgkg",
)

AMINO_ACIDS = (
    "lysine_mgkg",
    "methionine_mgkg",
    "tryptophan_mgkg",
    "arginine_mgkg",
    "taurine_mgkg",
    "l_carnitine_mgkg",
)

FATTY_ACIDS = (
    "omega_3_mgkg",
    "omega_6_mgkg",
    "epa_dha_mgkg",
)

VITAMINS = (
    "vitamin_a_uikg",
    "vitamin_d3_uikg",
    "vitamin_e_uikg",
    "vitamin_b1_mgkg",
    "vitamin_b2_mgkg",
    "vitamin_b6_mgkg",
    "vitamin_b12_mgkg",
    "niacin_mgkg",
    "pantothenic_acid_mgkg",
    "folic_acid_mgkg",
    "biotin_mgkg",
    "choline_mgkg",
    "vitamin_c_mgkg",
    "vitamin_k3_mgkg",
)

ENERGY = (
    "metabolizable_energy_kcalkg",
)

NORMALIZABLE_FIELDS = tuple(NORMALIZATION_RULES.keys())


# ==========================================================
# Prioridade das regras
# ==========================================================

RULE_PRIORITY = [
    "already_normalized",
    "overscale",
    "decimal_shift",
    "percent_conversion",
    "gkg_to_mgkg",
    "unit_direct_percent_to_gkg",
    "unit_direct_percent_to_mgkg",
    "unit_direct_gkg_to_mgkg",
    "unit_direct_already_gkg",
    "unit_direct_already_mgkg",
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
    "unit_direct_percent_to_gkg": 1.0,
    "unit_direct_percent_to_mgkg": 1.0,
    "unit_direct_gkg_to_mgkg": 1.0,
    "unit_direct_already_gkg": 1.0,
    "unit_direct_already_mgkg": 1.0,
    "ambiguous": 0.40,
    "missing": 0.00,
    "implausible": 0.00,
}


# ==========================================================
# Categorias de Qualidade
# ==========================================================

QUALITY_STATUS = {
    ValidationStatus.NORMALIZED: "Normalizado",
    ValidationStatus.AUTO_CORRECTED: "Corrigido automaticamente",
    ValidationStatus.REVIEW: "Requer revisão manual",
    ValidationStatus.AMBIGUOUS: "Ambíguo",
    ValidationStatus.IMPLAUSIBLE: "Implausível",
    ValidationStatus.MISSING: "Sem informação",
}


# ==========================================================
# Helpers
# ==========================================================

def get_rule(field: str) -> NormalizationRule | None:
    return NORMALIZATION_RULES.get(field)

def has_rule(field: str) -> bool:
    return field in NORMALIZATION_RULES

def is_macro(field: str) -> bool:
    return field in MACRONUTRIENTS

def is_mineral(field: str) -> bool:
    return field in MINERALS

def get_confidence(rule_name: str) -> float:
    return RULE_CONFIDENCE.get(rule_name, 0.0)

def quality_label(status: ValidationStatus) -> str:
    return QUALITY_STATUS.get(status, "Desconhecido")

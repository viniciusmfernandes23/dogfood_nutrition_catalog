from __future__ import annotations

from app.normalization.models import (
    NormalizationRule,
    ValidationStatus,
)

# ==========================================================
# Constantes de Conversão
# ==========================================================

GKG_TO_MGKG_FACTOR = 1000.0
PERCENT_TO_GKG_FACTOR = 10.0
PERCENT_TO_MGKG_FACTOR = 10000.0


# ==========================================================
# Configuração de Regras por Nutriente
# ==========================================================

NORMALIZATION_RULES: dict[str, NormalizationRule] = {

    # ------------------------------------------------------
    # Macronutrientes (Unidade Alvo: g/kg)
    # ------------------------------------------------------

    "protein_gkg": NormalizationRule(
        field="protein_gkg",
        target_min=0.1, 
        target_max=600,
        overscale_factor=10,
        decimal_shift_factor=10,
        percent_factor=PERCENT_TO_GKG_FACTOR,
    ),

    "fat_gkg": NormalizationRule(
        field="fat_gkg",
        target_min=0.01,
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
        target_max=150, 
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
    # Minerais (Unidade Alvo: mg/kg)
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
        target_min=100, 
        target_max=40000,
        overscale_factor=10,
        decimal_shift_factor=100,
        percent_factor=PERCENT_TO_MGKG_FACTOR,
        gkg_to_mgkg=True,
        decimal_shift_up=1000,
    ),

    "sodium_mgkg": NormalizationRule(
        field="sodium_mgkg",
        target_min=100, 
        target_max=30000,
        overscale_factor=10,
        decimal_shift_factor=100,
        percent_factor=PERCENT_TO_MGKG_FACTOR,
        gkg_to_mgkg=True,
        decimal_shift_up=1000,
    ),

    "potassium_mgkg": NormalizationRule(
        field="potassium_mgkg",
        target_min=100, 
        target_max=50000,
        overscale_factor=10,
        decimal_shift_factor=100,
        percent_factor=PERCENT_TO_MGKG_FACTOR,
        gkg_to_mgkg=True,
        decimal_shift_up=1000,
    ),

    # ------------------------------------------------------
    # Energia (Unidade Alvo: kcal/kg)
    # ------------------------------------------------------

    "metabolizable_energy_kcalkg": NormalizationRule(
        field="metabolizable_energy_kcalkg",
        target_min=500,
        target_max=4500, 
        overscale_factor=10,
        decimal_shift_factor=1000,
        percent_factor=10000,
    ),

    # ------------------------------------------------------
    # Aminoácidos (Unidade Alvo: mg/kg)
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
    # Ácidos Graxos (Unidade Alvo: mg/kg)
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
    # Microminerais (Unidade Alvo: mg/kg)
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
        target_min=0.01,
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
    # Vitaminas (Unidade Alvo: UI/kg ou mg/kg)
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
        decimal_shift_up=0.001,
    ),
    "niacin_mgkg": NormalizationRule(
        field="niacin_mgkg",
        target_min=10,
        target_max=300, 
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
        target_max=5,
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
    # Outros (mg/kg)
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

NORMALIZABLE_FIELDS = tuple(NORMALIZATION_RULES.keys())


# ==========================================================
# Configuração de Confiança e Prioridade
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
# Helpers de Acesso
# ==========================================================

def get_rule(field: str) -> NormalizationRule | None:
    return NORMALIZATION_RULES.get(field)


def get_confidence(rule_name: str) -> float:
    return RULE_CONFIDENCE.get(rule_name, 0.5)

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(slots=True, frozen=True)
class NutrientMetadata:
    """
    Metadados para definição da camada semântica de um nutriente.
    """
    field: str
    display_name: str
    unit: str
    output_scale_factor: float = 1.0  # Fator para converter da escala interna para a real


# Dicionário mestre de metadados orientado por nutriente
NUTRIENT_METADATA: Dict[str, NutrientMetadata] = {
    # Macronutrientes (Interno: g/kg * 10 -> Saída: g/kg)
    "moisture_gkg": NutrientMetadata("moisture_gkg", "Umidade", "g/kg", 0.1),
    "protein_gkg": NutrientMetadata("protein_gkg", "Proteína", "g/kg", 0.1),
    "fat_gkg": NutrientMetadata("fat_gkg", "Gordura", "g/kg", 0.1),
    "fiber_gkg": NutrientMetadata("fiber_gkg", "Fibra", "g/kg", 0.1),
    "ash_gkg": NutrientMetadata("ash_gkg", "Cinzas", "g/kg", 0.1),
    
    # Energia (Interno: kcal/kg * 10 -> Saída: kcal/kg)
    "metabolizable_energy_kcalkg": NutrientMetadata("metabolizable_energy_kcalkg", "Energia Metabolizável", "kcal/kg", 0.1),
    
    # Minerais (Interno: mg/kg * 10 -> Saída: mg/kg)
    "calcium_min_mgkg": NutrientMetadata("calcium_min_mgkg", "Cálcio (Mín)", "mg/kg", 0.1),
    "calcium_max_mgkg": NutrientMetadata("calcium_max_mgkg", "Cálcio (Máx)", "mg/kg", 0.1),
    "phosphorus_mgkg": NutrientMetadata("phosphorus_mgkg", "Fósforo", "mg/kg", 0.1),
    "sodium_mgkg": NutrientMetadata("sodium_mgkg", "Sódio", "mg/kg", 0.1),
    "potassium_mgkg": NutrientMetadata("potassium_mgkg", "Potássio", "mg/kg", 0.1),
}


def get_nutrient_metadata(field: str) -> NutrientMetadata | None:
    """Retorna os metadados para um campo específico."""
    return NUTRIENT_METADATA.get(field)

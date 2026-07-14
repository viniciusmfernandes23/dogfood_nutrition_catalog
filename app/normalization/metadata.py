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
    # Macronutrientes (Interno: g/kg -> Saída: g/kg)
    "moisture_gkg": NutrientMetadata("moisture_gkg", "Umidade", "g/kg", 1.0),
    "protein_gkg": NutrientMetadata("protein_gkg", "Proteína", "g/kg", 1.0),
    "fat_gkg": NutrientMetadata("fat_gkg", "Gordura", "g/kg", 1.0),
    "fiber_gkg": NutrientMetadata("fiber_gkg", "Fibra", "g/kg", 1.0),
    "ash_gkg": NutrientMetadata("ash_gkg", "Cinzas", "g/kg", 1.0),
    
    # Energia (Interno: kcal/kg -> Saída: kcal/kg)
    "metabolizable_energy_kcalkg": NutrientMetadata("metabolizable_energy_kcalkg", "Energia Metabolizável", "kcal/kg", 1.0),
    
    # Minerais (Interno: mg/kg -> Saída: mg/kg)
    "calcium_min_mgkg": NutrientMetadata("calcium_min_mgkg", "Cálcio (Mín)", "mg/kg", 1.0),
    "calcium_max_mgkg": NutrientMetadata("calcium_max_mgkg", "Cálcio (Máx)", "mg/kg", 1.0),
    "phosphorus_mgkg": NutrientMetadata("phosphorus_mgkg", "Fósforo", "mg/kg", 1.0),
    "sodium_mgkg": NutrientMetadata("sodium_mgkg", "Sódio", "mg/kg", 1.0),
    "potassium_mgkg": NutrientMetadata("potassium_mgkg", "Potássio", "mg/kg", 1.0),
}


def get_nutrient_metadata(field: str) -> NutrientMetadata | None:
    """Retorna os metadados para um campo específico."""
    return NUTRIENT_METADATA.get(field)

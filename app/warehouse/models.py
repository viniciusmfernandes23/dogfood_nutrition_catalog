from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime


@dataclass(slots=True)
class WarehouseModel:
    """Classe base para modelos do Data Warehouse."""
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class ProductDimension(WarehouseModel):
    """
    Dimensão Produto (dim_product).
    
    Contém atributos estáticos e categorizações de produtos. 
    Nota: Scores e cálculos dinâmicos são realizados no Power BI.
    """
    product_id: int | None
    brand: str | None
    product_name: str | None
    product_url: str | None
    product_category: str | None
    product_tier: str | None
    life_stage: str | None
    breed_size: str | None
    protein_source: str | None
    clinical_category: str | None
    # v1.4.0: Novos campos da Ficha Técnica
    product_type: str | None = None
    package_weight: str | None = None
    contains_coloring: str | None = None
    target_breeds: str | None = None
    indication: str | None = None
    product_line: str | None = None
    is_transgenic: str | None = None
    gender: str | None = None
    image_url: str | None = None
    
    has_guarantee_levels: bool = False
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()


@dataclass(slots=True)
class NutrientFact(WarehouseModel):
    """
    Fato Nutrientes (fact_nutrient).
    
    Representa o perfil nutricional no formato LONG, preservando 
    a rastreabilidade completa desde o valor original até o normalizado.
    """
    product_id: int | None
    nutrient_key: str           # Chave canônica (ex: protein_gkg)
    nutrient_value: float | None # Valor normalizado na unidade alvo
    nutrient_unit: str | None    # Unidade normalizada (ex: g/kg)
    
    original_value: float | None # Valor extraído originalmente
    original_unit: str | None    # Unidade extraída originalmente
    
    status: str | None           # Status (Normalizado, Corrigido, Implausível)
    rule_applied: str | None     # Regra técnica aplicada
    collected_at: datetime
    reason: str | None = None    # Motivo detalhado da auditoria


@dataclass(slots=True)
class PriceSnapshotFact(WarehouseModel):
    """
    Fato Preços (fact_price_snapshot).
    
    Snapshot temporal de preços por SKU/Variação, permitindo 
    análise de evolução de preços e competitividade.
    """
    product_id: int | None
    marketplace: str | None
    ean: str | None
    sku_id: str | None
    sku_name: str | None
    package_weight_kg: float | None
    price: float | None
    list_price: float | None
    subscriber_price: float | None
    price_per_kg: float | None
    available: bool | None
    collected_at: datetime

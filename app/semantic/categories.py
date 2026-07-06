from __future__ import annotations

from enum import Enum


class ProductCategory(str, Enum):
    DRY = "Ração Seca"
    WET = "Ração Úmida"
    CLINICAL = "Ração Clínica"
    VETERINARY = "Ração Veterinária"
    NATURAL = "Ração Natural"
    PREMIUM = "Premium"
    SUPER_PREMIUM = "Super Premium"
    TREAT = "Petisco"
    SUPPLEMENT = "Suplemento"
    FUNCTIONAL = "Funcional"
    THERAPEUTIC = "Terapêutica"


class NutritionCategory(str, Enum):
    HAS_GUARANTEE = "Tem níveis de garantia"
    NO_GUARANTEE = "Não tem níveis de garantia"

    NORMALIZED = "Normalizado"
    AUTO_CORRECTED = "Corrigido automaticamente"
    MANUAL_REVIEW = "Requer revisão manual"
    AMBIGUOUS = "Ambíguo"
    IMPLAUSIBLE = "Implausível"


class StockCategory(str, Enum):
    IN_STOCK = "in_stock"
    OUT_OF_STOCK = "out_of_stock"


class PriceCategory(str, Enum):
    HAS_PRICE = "tem preço"
    NO_PRICE = "não tem preço"

    HAS_PRICE_PER_KG = "tem preço por kg"
    NO_PRICE_PER_KG = "não tem preço por kg"

    HAS_SUBSCRIBER_PRICE = "preço assinante disponível"
    NO_SUBSCRIBER_PRICE = "preço assinante indisponível"


class LifeStage(str, Enum):
    PUPPY = "Filhote"

    ADULT = "Adulto"

    SENIOR = "Sênior"

    ALL = "Todas as idades"


class BreedSize(str, Enum):
    MINI = "Mini"

    SMALL = "Pequeno"

    MEDIUM = "Médio"

    LARGE = "Grande"

    GIANT = "Gigante"

    ALL = "Todos os portes"


class ClinicalCategory(str, Enum):
    NONE = "Não clínica"

    RENAL = "Renal"

    HEPATIC = "Hepática"

    URINARY = "Urinária"

    GASTROINTESTINAL = "Gastrointestinal"

    DIABETIC = "Diabetes"

    HYPOALLERGENIC = "Hipoalergênica"

    OBESITY = "Obesidade"


class ProteinSource(str, Enum):
    CHICKEN = "Frango"

    BEEF = "Carne"

    LAMB = "Cordeiro"

    SALMON = "Salmão"

    PORK = "Suíno"

    TURKEY = "Peru"

    FISH = "Peixe"

    MIXED = "Múltiplas"

    UNKNOWN = "Não identificado"


class ProductTier(str, Enum):
    STANDARD = "Standard"

    PREMIUM = "Premium"

    SUPER_PREMIUM = "Super Premium"

    ULTRA_PREMIUM = "Ultra Premium"

    NATURAL = "Natural"

    VETERINARY = "Veterinário"
import sys
import os
import pandas as pd
from datetime import datetime

# Ajusta path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.collectors.models import ProductCollection
from app.warehouse.fact_price_snapshot import PriceSnapshotFactBuilder
from executar_pipeline import _extract_sku_variations

def test_petlove_variation_extraction():
    print("Testando extração de variações Petlove...")
    
    # Mock de payload da Petlove
    mock_payload = {
        "variants": [
            {
                "id": 3109089,
                "name": "Ração GranPlus Choice Adulto Frango e Carne 15kg",
                "ean": "7896048911285",
                "price": 154.90,
                "listPrice": 179.90,
                "subscriptionPrice": 131.67,
                "stock": 10
            }
        ]
    }
    
    variations = _extract_sku_variations(mock_payload, marketplace="Petlove")
    
    assert len(variations) == 1
    v = variations[0]
    assert v["sku_id"] == "3109089"
    assert v["ean"] == "7896048911285"
    assert v["package_weight_kg"] == 15.0
    assert v["marketplace"] == "Petlove"
    print("✅ Extração Petlove OK")

def test_multistore_warehouse_build():
    print("Testando construção de warehouse multiloja...")
    
    # DataFrame simulando coleta de duas lojas
    data = [
        {
            "product_id": 1,
            "marketplace": "Cobasi",
            "ean": "7896048911285",
            "product_name": "Ração GranPlus",
            "sku_variations": [
                {
                    "sku_id": "915700",
                    "sku_name": "15kg",
                    "ean": "7896048911285",
                    "price": 160.00,
                    "marketplace": "Cobasi"
                }
            ]
        },
        {
            "product_id": 100,
            "marketplace": "Petlove",
            "ean": "7896048911285",
            "product_name": "Ração GranPlus",
            "sku_variations": [
                {
                    "sku_id": "3109089",
                    "sku_name": "15kg",
                    "ean": "7896048911285",
                    "price": 154.90,
                    "marketplace": "Petlove"
                }
            ]
        }
    ]
    
    df = pd.DataFrame(data)
    builder = PriceSnapshotFactBuilder()
    fact_df = builder.build(df)
    
    # Deve ter 2 linhas (uma para cada loja)
    assert len(fact_df) == 2
    assert "marketplace" in fact_df.columns
    assert "ean" in fact_df.columns
    
    # Verifica se os EANs coincidem para permitir o JOIN no Power BI
    eans = fact_df["ean"].unique()
    assert len(eans) == 1
    assert eans[0] == "7896048911285"
    print("✅ Warehouse Multiloja OK")

if __name__ == "__main__":
    try:
        test_petlove_variation_extraction()
        test_multistore_warehouse_build()
        print("\n🎉 Todos os testes de integração Petlove passaram!")
    except Exception as e:
        print(f"\n❌ Falha nos testes: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

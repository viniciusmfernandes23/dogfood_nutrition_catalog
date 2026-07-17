import sys
import os
import pandas as pd
from datetime import datetime

# Ajusta path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.warehouse.fact_price_snapshot import PriceSnapshotFactBuilder
from app.warehouse.exporter import WarehouseExporter

def demonstracao():
    print("🚀 Iniciando Demonstração de Resultados Multiloja...")
    
    # Simula dados de coleta de ambas as lojas para o mesmo produto (mesmo EAN)
    data = [
        {
            "product_id": "COB-3853925",
            "marketplace": "Cobasi",
            "product_name": "Ração GranPlus Choice Frango e Carne",
            "brand": "GranPlus",
            "sku_variations": [
                {
                    "sku_id": "915700",
                    "sku_name": "GranPlus Choice 10,1kg",
                    "ean": "7896048911285",
                    "package_weight_kg": 10.1,
                    "price": 189.90,
                    "list_price": 209.90,
                    "subscriber_price": 170.91,
                    "price_per_kg": 18.80,
                    "available": True,
                    "marketplace": "Cobasi"
                },
                {
                    "sku_id": "915701",
                    "sku_name": "GranPlus Choice 15kg",
                    "ean": "7896048911286",
                    "package_weight_kg": 15.0,
                    "price": 259.90,
                    "list_price": 289.90,
                    "subscriber_price": 233.91,
                    "price_per_kg": 17.33,
                    "available": True,
                    "marketplace": "Cobasi"
                }
            ]
        },
        {
            "product_id": "PET-3109089",
            "marketplace": "Petlove",
            "product_name": "Ração GranPlus Choice Frango e Carne",
            "brand": "GranPlus",
            "sku_variations": [
                {
                    "sku_id": "3109089",
                    "sku_name": "15kg",
                    "ean": "7896048911286",
                    "package_weight_kg": 15.0,
                    "price": 254.90,
                    "list_price": 279.90,
                    "subscriber_price": 229.41,
                    "price_per_kg": 16.99,
                    "available": True,
                    "marketplace": "Petlove"
                }
            ]
        }
    ]
    
    df_raw = pd.DataFrame(data)
    
    # 1. Constrói a tabela fato
    builder = PriceSnapshotFactBuilder()
    df_fact = builder.build(df_raw)
    
    # 2. Exporta para um diretório temporário de teste
    test_dir = "data/output/test_results"
    exporter = WarehouseExporter(output_dir=test_dir)
    
    # Limpa antes de exportar
    exporter.clean_output_directory(full_clean=True)
    
    path = exporter.export_fact(df_fact, "fact_price_snapshot.csv")
    
    print(f"\n✅ Arquivo gerado em: {path}")
    print("\n📊 Amostra do Resultado (fact_price_snapshot.csv):")
    
    # Exibe as colunas principais para conferência
    cols_to_show = ["marketplace", "sku_name", "ean", "price", "price_per_kg", "subscriber_price"]
    print(df_fact[cols_to_show].to_markdown(index=False))
    
    print("\n💡 Observe como o EAN '7896048911286' permite comparar o preço de 15kg entre Cobasi e Petlove!")

if __name__ == "__main__":
    demonstracao()

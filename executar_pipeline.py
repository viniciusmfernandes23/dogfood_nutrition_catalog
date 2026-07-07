import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os
import shutil

# Garantir que o diretório app está no path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.collectors.cobasi_api import CobasiAPICollector
from app.collectors.crawler import CobasiCrawler
from app.pipeline.orchestrator import PipelineOrchestrator
from app.pipeline.models import PipelineConfig
from app.parsers.nutrition_parser import parse_nutrition

def run_extraction():
    print("Iniciando coleta de dados...")
    
    try:
        # 1. Coleta de dados da API
        collector = CobasiAPICollector()
        raw_products = collector.fetch_all()
        
        if not raw_products:
            print("AVISO: Nenhum produto foi retornado pela API da Cobasi.")
            return

        product_list = []
        for p in raw_products:
            p_dict = {
                'product_id': p.product_id,
                'product_name': p.product_name,
                'brand': p.brand,
                'url': p.url,
                'category_id': p.category_id,
                'price': None,
                'subscriber_price': None,
                'available': False,
            }
            
            if hasattr(p, 'api_payload') and p.api_payload:
                try:
                    items = p.api_payload.get('items', [])
                    if items:
                        sellers = items[0].get('sellers', [])
                        if sellers:
                            comm = sellers[0].get('commertialOffer', {})
                            p_dict['price'] = comm.get('Price')
                            p_dict['available'] = comm.get('AvailableQuantity', 0) > 0
                except Exception:
                    pass
            product_list.append(p_dict)
            
        df = pd.DataFrame(product_list)
        
        # 2. Coleta de Níveis de Garantia (Crawler)
        full_df = df.head(50).copy()
        print(f"Extraindo níveis de garantia de {len(full_df)} produtos...")
        crawler = CobasiCrawler()
        guarantees = []
        
        for i, url in enumerate(full_df['url']):
            if i % 10 == 0: print(f"  Progresso: {i}/{len(full_df)}")
            if url:
                try:
                    res = crawler.collect(url)
                    guarantees.append(res.guarantee_section if res.success else None)
                except Exception:
                    guarantees.append(None)
            else:
                guarantees.append(None)
        full_df['raw_guarantee'] = guarantees
        
        # 3. Parsing e Mapeamento de Nutrientes
        print("Fazendo parsing e mapeando nutrientes para normalização...")
        mapping = {
            'protein': 'protein_gkg',
            'fat': 'fat_gkg',
            'fiber': 'fiber_gkg',
            'ash': 'ash_gkg',
            'moisture': 'moisture_gkg',
            'calcium_min': 'calcium_min_mgkg',
            'calcium_max': 'calcium_max_mgkg',
            'phosphorus': 'phosphorus_mgkg',
            'sodium': 'sodium_mgkg',
            'potassium': 'potassium_mgkg'
        }
        
        for index, row in full_df.iterrows():
            nutrients = parse_nutrition(row['raw_guarantee'])
            for nut_key, nut_data in nutrients.items():
                target_col = mapping.get(nut_key)
                if target_col:
                    full_df.at[index, target_col] = nut_data['value']
                    # IMPORTANTE: O engine usa field.split('_')[0] + "_unit"
                    # Para 'sodium_mgkg', ele busca 'sodium_unit'
                    full_df.at[index, f"{nut_key}_unit"] = nut_data['unit']
        
        # 4. Executar o Orquestrador
        print("Executando orquestrador do pipeline...")
        config = PipelineConfig(
            output_directory="data/reports",
            warehouse_directory="data/warehouse"
        )
        orchestrator = PipelineOrchestrator(config)
        result = orchestrator.run(full_df)
        
        if result.success:
            print("\nPipeline concluído com sucesso!")
            for name, path in result.exported_files.items():
                shutil.copy(str(path), os.path.basename(str(path)))
                print(f"  - {os.path.basename(str(path))}")
        else:
            print(f"Erro no orquestrador: {result.errors}")

    except Exception as e:
        print(f"ERRO CRÍTICO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_extraction()

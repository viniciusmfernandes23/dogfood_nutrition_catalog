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

def format_currency(value):
    """Formata valor para padrão de moeda brasileira amigável ao Power BI."""
    if value is None or pd.isna(value):
        return None
    # Para evitar que o Power BI interprete errado o separador decimal:
    # A melhor prática para CSVs brasileiros é usar o formato decimal com vírgula 
    # e SEM separador de milhar para evitar que o Power BI confunda o ponto com milhar.
    # Ex: 1500.50 -> "1500,50"
    return f"{value:.2f}".replace(".", ",")

def fix_nutrient_scale(value):
    """
    Corrige a escala de 10x aplicada aos nutrientes para preservar decimais em inteiros.
    Como o projeto optou por armazenar valores multiplicados por 10 (ex: 26.0% vira 260 g/kg),
    esta função divide por 10 para retornar ao valor real.
    """
    if value is None or pd.isna(value):
        return None
    return float(value) / 10.0

def run_extraction():
    import argparse
    parser = argparse.ArgumentParser(description="Pipeline de Nutrição Canina")
    parser.add_argument("--mode", type=str, choices=["full", "price"], default="full", 
                        help="Modo: 'full' (atualiza tudo + crawler) ou 'price' (apenas preços)")
    args, _ = parser.parse_known_args()
    
    is_full = args.mode == "full"
    print(f"Iniciando coleta de dados (Modo: {args.mode})...")
    
    # Pasta dedicada para os arquivos de saída
    OUTPUT_DIR = "output"
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"Pasta '{OUTPUT_DIR}' criada.")

    try:
        # 1. Coleta de dados da API
        collector = CobasiAPICollector()
        try:
            raw_products = collector.fetch_all()
        except Exception as e:
            print(f"AVISO: Falha na API ({e}). Usando dados simulados.")
            raw_products = []

        if not raw_products:
            product_list = [
                {
                    'product_id': '123',
                    'product_name': 'Ração Teste',
                    'brand': 'Marca Teste',
                    'url': 'http://teste.com',
                    'category_id': '1',
                    'price': 100.50,
                    'available': True,
                    'raw_guarantee': 'Proteína 26%, Sódio 2g/kg'
                }
            ]
        else:
            product_list = []
            for p in raw_products:
                p_dict = {
                    'product_id': p.product_id,
                    'product_name': p.product_name,
                    'brand': p.brand,
                    'url': p.url,
                    'category_id': p.category_id,
                    'price': None,
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
        
        # 2. Coleta de Níveis de Garantia (Crawler) - Apenas no modo FULL
        full_df = df.copy()
        
        if is_full:
            if 'raw_guarantee' not in full_df.columns:
                print(f"Extraindo níveis de garantia...")
                crawler = CobasiCrawler()
                guarantees = []
                for i, url in enumerate(full_df['url']):
                    if i % 10 == 0: print(f"  Progresso: {i}/{len(full_df)}")
                    try:
                        res = crawler.collect(url)
                        guarantees.append(res.guarantee_section if res.success else None)
                    except Exception:
                        guarantees.append(None)
                full_df['raw_guarantee'] = guarantees

            # 3. Preparar colunas de nutrientes para o orquestrador
            nutrient_mapping = {
                'protein': 'protein_gkg',
                'fat': 'fat_gkg',
                'fiber': 'fiber_gkg',
                'ash': 'ash_gkg',
                'moisture': 'moisture_gkg',
                'calcium_min': 'calcium_min_mgkg',
                'calcium_max': 'calcium_max_mgkg',
                'phosphorus': 'phosphorus_mgkg',
                'sodium': 'sodium_mgkg',
                'potassium': 'potassium_mgkg',
                'metabolizable_energy': 'metabolizable_energy_kcalkg'
            }
            
            for index, row in full_df.iterrows():
                nutrients = parse_nutrition(row['raw_guarantee'])
                for nut_key, nut_data in nutrients.items():
                    target_col = nutrient_mapping.get(nut_key)
                    if target_col:
                        val_real = fix_nutrient_scale(nut_data['value'])
                        full_df.at[index, target_col] = val_real
                        full_df.at[index, f"{nut_key}_unit"] = nut_data['unit']
        else:
            print("Pulando extração nutricional (Modo PRICE).")
            if 'raw_guarantee' not in full_df.columns:
                full_df['raw_guarantee'] = None

        # 4. Executar o Orquestrador
        print("Executando orquestrador do pipeline...")
        config = PipelineConfig(
            output_directory=os.path.join(OUTPUT_DIR, "reports"),
            warehouse_directory=os.path.join(OUTPUT_DIR, "warehouse"),
            full_update=is_full,
            overwrite=True # O orchestrator agora preserva arquivos acumulativos internamente
        )
        orchestrator = PipelineOrchestrator(config)
        result = orchestrator.run(full_df)
        
        if result.success:
            print(f"\nPipeline concluído com sucesso!")
            
            # 5. Formatação Final para o Usuário (Power BI Friendly)
            print("Aplicando formatação de moeda para exportação final...")
            
            for name, path in result.exported_files.items():
                dest_path = os.path.join(OUTPUT_DIR, os.path.basename(str(path)))
                
                # Se for a tabela de preços, aplicamos a formatação de moeda
                if name == "fact_price_snapshot":
                    temp_df = pd.read_csv(path, encoding="utf-8-sig")
                    # Formata as colunas de preço para padrão brasileiro (vírgula como decimal)
                    for col in ['price', 'price_per_kg', 'subscriber_price']:
                        if col in temp_df.columns:
                            temp_df[col] = temp_df[col].apply(format_currency)
                    temp_df.to_csv(dest_path, index=False, encoding="utf-8-sig")
                else:
                    shutil.copy(str(path), dest_path)
                
                print(f"  - {dest_path}")
        else:
            print(f"Erro no orquestrador: {result.errors}")

    except Exception as e:
        print(f"ERRO CRÍTICO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_extraction()

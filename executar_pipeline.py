import pandas as pd
import numpy as np
from datetime import datetime
import sys
from app.collectors.cobasi_api import CobasiAPICollector
from app.collectors.crawler import CobasiCrawler
from app.parsers.nutrition_parser import parse_nutrition
from app.semantic.engine import SemanticEngine

def run_extraction():
    print("Iniciando coleta de dados...")
    
    try:
        # 1. Coleta de dados da API
        collector = CobasiAPICollector()
        raw_products = collector.fetch_all()
        
        if not raw_products:
            print("AVISO: Nenhum produto foi retornado pela API da Cobasi. Verifique sua conexão ou os IDs das categorias.")
            # Criar arquivos vazios com cabeçalhos para cumprir o objetivo
            gerar_arquivos_vazios()
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
                'price_per_kg': 0
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
                            # Tentar extrair preço de assinante se houver Teasers
                            teasers = comm.get('Teasers', [])
                            if teasers:
                                p_dict['subscriber_price'] = p_dict['price'] * 0.9 # Geralmente 10% na Cobasi
                except Exception:
                    pass
            product_list.append(p_dict)
            
        df = pd.DataFrame(product_list)
        
        # 2. Coleta de Níveis de Garantia (Crawler)
        print(f"Extraindo níveis de garantia de {len(df)} páginas...")
        crawler = CobasiCrawler()
        guarantees = []
        for url in df['url']:
            if url:
                try:
                    res = crawler.collect(url)
                    guarantees.append(res.guarantee_section if res.success else None)
                except Exception:
                    guarantees.append(None)
            else:
                guarantees.append(None)
        df['raw_guarantee'] = guarantees
        
        # 3. Enriquecimento Semântico
        print("Aplicando inteligência semântica...")
        semantic_engine = SemanticEngine()
        # Garantir colunas para o engine
        for col in ['description', 'ingredients', 'category']:
            if col not in df.columns:
                df[col] = ""
                
        full_df = semantic_engine.enrich_dataframe(df)

        # --- GERAÇÃO DOS ARQUIVOS FINAIS ---
        gerar_csvs(full_df)

    except Exception as e:
        print(f"ERRO CRÍTICO NO PIPELINE: {e}")
        import traceback
        traceback.print_exc()

def gerar_csvs(full_df):
    print("Gerando arquivos CSV...")
    now = datetime.now()

    # 1. dim_product.csv
    dim_cols = {
        'product_id': 'product_id', 'product_name': 'product_name', 'brand': 'brand',
        'url': 'url', 'ingredients': 'ingredients', 'life_stage': 'fase_vida',
        'breed_size': 'porte', 'clinical_category': 'categoria_clinica',
        'product_tier': 'nivel_produto', 'protein_source': 'fonte_proteina',
        'product_category': 'categoria_produto'
    }
    dim_product = full_df[list(dim_cols.keys())].rename(columns=dim_cols)
    dim_product['linha_veterinaria'] = dim_product['categoria_clinica'].apply(lambda x: 'Sim' if x and x != 'Nenhuma' else 'Não')
    dim_product.to_csv('dim_product.csv', index=False, encoding='utf-8-sig')

    # 2. fact_nutrient.csv
    nutrient_records = []
    for _, row in full_df.iterrows():
        nutrients = parse_nutrition(row.get('raw_guarantee'))
        for key, data in nutrients.items():
            if data.get('value') is not None:
                nutrient_records.append({
                    'product_id': row['product_id'],
                    'product_name': row['product_name'],
                    'manufacturer': row.get('brand', 'N/A'),
                    'nutrient_key': key,
                    'nutrient_value': data['value'],
                    'nutrient_name': data.get('matched_alias', key),
                    'unit': data['unit']
                })
    pd.DataFrame(nutrient_records).to_csv('fact_nutrient.csv', index=False, encoding='utf-8-sig')

    # 3. fact_price_snapshot.csv
    fact_price = pd.DataFrame([{
        'snapshot_date': now.strftime('%Y-%m-%d'),
        'collection_timestamp': now.strftime('%Y-%m-%d %H:%M:%S'),
        'product_id': row['product_id'],
        'price_brl': row.get('price'),
        'subscriber_price_brl': row.get('subscriber_price'),
        'price_per_kg_brl': row.get('price_per_kg', 0),
        'availability': row.get('available', False),
        'source': 'Cobasi'
    } for _, row in full_df.iterrows()])
    fact_price.to_csv('fact_price_snapshot.csv', index=False, encoding='utf-8-sig')

    print("\nSucesso! Arquivos gerados: dim_product.csv, fact_nutrient.csv, fact_price_snapshot.csv")

def gerar_arquivos_vazios():
    # Cria os arquivos apenas com cabeçalhos caso a coleta falhe
    pd.DataFrame(columns=['product_id','product_name','brand','url','ingredients','fase_vida','porte','categoria_clinica','linha_veterinaria','fonte_proteina','nivel_produto','categoria_produto']).to_csv('dim_product.csv', index=False)
    pd.DataFrame(columns=['product_id','product_name','manufacturer','nutrient_key','nutrient_value','nutrient_name','unit']).to_csv('fact_nutrient.csv', index=False)
    pd.DataFrame(columns=['snapshot_date','collection_timestamp','product_id','price_brl','subscriber_price_brl','price_per_kg_brl','availability','source']).to_csv('fact_price_snapshot.csv', index=False)
    print("Arquivos vazios gerados com cabeçalhos.")

if __name__ == "__main__":
    run_extraction()

import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os
import re
import shutil

# Garantir que o diretório app está no path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.collectors.cobasi_api import CobasiAPICollector
from app.collectors.crawler import CobasiCrawler
from app.pipeline.orchestrator import PipelineOrchestrator
from app.pipeline.models import PipelineConfig
from app.parsers.nutrition_parser import parse_nutrition

# Padrão para extrair peso em kg a partir do nome do SKU.
_WEIGHT_PATTERN = re.compile(
    r"(?:(\d+(?:[.,]\d+)?)\s*x\s*)?(\d+(?:[.,]\d+)?)\s*(kg|g)\b",
    re.IGNORECASE,
)


def format_currency(value):
    """Formata valor para padrão de moeda brasileira amigável ao Power BI."""
    if value is None or pd.isna(value):
        return None
    
    try:
        num_value = float(str(value).replace(",", "."))
        return f"{num_value:.2f}".replace(".", ",")
    except (ValueError, TypeError):
        return str(value)


def _parse_weight_kg(sku_name: str | None) -> float | None:
    """Extrai o peso em kg a partir do nome do SKU."""
    if not sku_name:
        return None
    match = _WEIGHT_PATTERN.search(sku_name)
    if not match:
        return None
    multiplier_str, value_str, unit = match.groups()
    value = float(value_str.replace(",", "."))
    if unit.lower() == "g":
        value = value / 1000.0
    if multiplier_str:
        multiplier = float(multiplier_str.replace(",", "."))
        value = multiplier * value
    return round(value, 4)


def _extract_sku_variations(api_payload: dict, marketplace: str = "Cobasi") -> list[dict]:
    """Extrai todas as variações de SKU de um produto da Cobasi."""
    variations = []
    
    if marketplace == "Cobasi":
        items = api_payload.get("items", [])
        for item in items:
            sku_id = item.get("itemId")
            sku_name = item.get("name")
            package_weight_kg = _parse_weight_kg(sku_name)
            ean = item.get("ean")

            price = None
            list_price = None
            available = False

            sellers = item.get("sellers", [])
            if sellers:
                comm = sellers[0].get("commertialOffer", {})
                price = comm.get("Price")
                list_price = comm.get("ListPrice")
                available = comm.get("AvailableQuantity", 0) > 0

            price_per_kg = None
            if price is not None and package_weight_kg and package_weight_kg > 0:
                price_per_kg = round(price / package_weight_kg, 4)

            variations.append({
                "sku_id": sku_id,
                "sku_name": sku_name,
                "ean": ean,
                "package_weight_kg": package_weight_kg,
                "price": price,
                "list_price": list_price,
                "subscriber_price": round(price * 0.9, 2) if price else None,
                "price_per_kg": price_per_kg,
                "available": available,
                "marketplace": marketplace
            })
            
    return variations


def run_extraction():
    import argparse
    parser = argparse.ArgumentParser(description="Pipeline de Nutrição Canina")
    parser.add_argument("--mode", type=str, choices=["full", "price"], default="full", 
                        help="Modo: 'full' (atualiza tudo + crawler) ou 'price' (apenas preços)")
    args, _ = parser.parse_known_args()
    
    is_full = args.mode == "full"
    
    # Pasta dedicada para os arquivos de saída
    OUTPUT_DIR = "output"
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    print(f"\n--- Dogfood Nutrition Pipeline (Cobasi Only) ---")
    print(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

    try:
        raw_products = []

        # 1. Coleta de dados da API (Cobasi)
        print("Coletando catálogo da Cobasi...")
        cobasi_collector = CobasiAPICollector()
        try:
            cobasi_products = cobasi_collector.fetch_all()
            if cobasi_products:
                print(f"  Sucesso: {len(cobasi_products)} produtos encontrados.")
                raw_products.extend(cobasi_products)
        except Exception as e:
            print(f"  ERRO CRÍTICO: {e}")
            raise

        if not raw_products:
            print("AVISO: Nenhum produto retornado. Encerrando.")
            return

        product_list = []
        for p in raw_products:
            sku_variations = []
            if hasattr(p, 'api_payload') and p.api_payload:
                try:
                    sku_variations = _extract_sku_variations(p.api_payload, marketplace=p.marketplace)
                except Exception:
                    pass

            if not sku_variations:
                sku_variations = [{
                    "sku_id": None, "sku_name": None, "ean": p.ean,
                    "package_weight_kg": None, "price": None, "list_price": None,
                    "subscriber_price": None, "price_per_kg": None,
                    "available": False, "marketplace": p.marketplace
                }]

            # v1.4.0: Extração de campos da Ficha Técnica e Imagem do api_payload
            specifications = {}
            image_url = None
            if hasattr(p, 'api_payload') and p.api_payload:
                # Extrair Imagem
                items = p.api_payload.get("items", [])
                if items:
                    images = items[0].get("images", [])
                    if images:
                        image_url = images[0].get("imageUrl")
                
                # Extrair Especificações (Ficha Técnica)
                # Na VTEX, especificações costumam vir em campos como 'Porte', 'Idade', etc.
                # ou dentro de uma lista de especificações se o mapeamento for genérico.
                spec_map = {
                    'Porte': 'breed_size',
                    'Tipo da ração': 'product_type',
                    'Peso da Ração': 'package_weight',
                    'Idade': 'life_stage',
                    'Corante': 'contains_coloring',
                    'Raças de cachorro': 'target_breeds',
                    'Indicação': 'indication',
                    'Linha': 'product_line',
                    'Transgênico': 'is_transgenic',
                    'Marca': 'brand_spec',
                    'Gênero': 'gender',
                    'Seção': 'product_category'
                }
                
                for vtex_key, internal_key in spec_map.items():
                    val = p.api_payload.get(vtex_key)
                    if isinstance(val, list) and val:
                        specifications[internal_key] = val[0]
                    elif val:
                        specifications[internal_key] = val

            # v1.5.1: Proteção contra product_id vazio
            if not p.product_id:
                print(f"  AVISO: Ignorando produto sem ID: {p.product_name}")
                continue

            p_dict = {
                'product_id': p.product_id,
                'marketplace': p.marketplace,
                'ean': p.ean or next((v.get('ean') for v in sku_variations if v.get('ean')), None),
                'product_name': p.product_name,
                'brand': specifications.get('brand_spec') or p.brand,
                'url': p.url,
                'category_id': p.category_id,
                'sku_variations': sku_variations,
                'price': next((v['price'] for v in sku_variations if v.get('price') is not None), None),
                'available': any(v.get('available', False) for v in sku_variations),
                'image_url': image_url,
                **specifications
            }
            product_list.append(p_dict)
            
        df = pd.DataFrame(product_list)
        full_df = df.copy()
        
        if is_full:
            print(f"Extraindo níveis de garantia (Crawler)...")
            crawler = CobasiCrawler()
            guarantees = []
            for i, url in enumerate(full_df['url']):
                if i % 20 == 0: print(f"  Progresso: {i}/{len(full_df)}")
                try:
                    res = crawler.collect(url)
                    guarantees.append(res.guarantee_section if res.success else None)
                except Exception:
                    guarantees.append(None)
            full_df['raw_guarantee'] = guarantees

            # Mapeamento de nutrientes expandido
            from app.normalization.rules import NORMALIZATION_RULES
            nutrient_mapping = {rule.split('_')[0]: rule for rule in NORMALIZATION_RULES.keys()}
            # Ajustes manuais para chaves especiais
            nutrient_mapping.update({
                'protein': 'protein_gkg', 'fat': 'fat_gkg', 'fiber': 'fiber_gkg',
                'ash': 'ash_gkg', 'moisture': 'moisture_gkg',
                'calcium_min': 'calcium_min_mgkg', 'calcium_max': 'calcium_max_mgkg',
                'metabolizable_energy': 'metabolizable_energy_kcalkg'
            })
            
            print(f"Processando {len(full_df)} produtos para extração de nutrientes...")
            for index, row in full_df.iterrows():
                nutrients = parse_nutrition(row['raw_guarantee'])
                print(f"  Nutrientes brutos encontrados para {row['product_name']}: {len(nutrients)}")
                best_matches = {}
                for _, nut_data in nutrients.items():
                    nut_type = nut_data['nutrient']
                    target_col = nutrient_mapping.get(nut_type)
                    if not target_col: continue
                    # v1.4.0: Removido bloqueio de kcal/sache para permitir normalização no Resolver
                    
                    val_real = nut_data['value']
                    alias = nut_data['matched_alias'].lower()
                    priority = 2 if any(x in alias for x in ['mín', 'min', 'máx', 'max']) else 1
                    
                    if target_col not in best_matches or priority > best_matches[target_col]['priority']:
                        best_matches[target_col] = {'value': val_real, 'unit': nut_data.get('unit'), 'priority': priority}
                
                for col, data in best_matches.items():
                    full_df.at[index, col] = data['value']
                    # Persiste a unidade original para que a barreira biológica
                    # do NormalizationEngine possa validar a unidade no resolver.
                    unit_col = f"{col}_unit"
                    if unit_col not in full_df.columns:
                        full_df[unit_col] = None
                    full_df.at[index, unit_col] = data.get('unit')

        # 4. Executar Orquestrador
        print("Finalizando processamento no Warehouse...")
        config = PipelineConfig(
            full_update=is_full,
            output_directory=OUTPUT_DIR,
            warehouse_directory=os.path.join(OUTPUT_DIR, "warehouse")
        )
        orchestrator = PipelineOrchestrator(config)
        orchestrator.run(full_df)

        # 5. Formatação Final
        print("Aplicando formatação de moeda...")
        warehouse_files = [
            'dim_product.csv', 'fact_nutrient.csv', 
            'fact_price_snapshot.csv', 'sanity_audit_logs.csv'
        ]
        
        for file in warehouse_files:
            path = os.path.join(OUTPUT_DIR, 'warehouse', file)
            if os.path.exists(path):
                w_df = pd.read_csv(path)
                currency_cols = [c for c in w_df.columns if 'price' in c.lower()]
                for col in currency_cols:
                    w_df[col] = w_df[col].apply(format_currency)
                w_df.to_csv(path, index=False)

        print("\nPipeline concluído com sucesso!")
        print(f"Arquivos gerados na pasta: {OUTPUT_DIR}/warehouse/")

    except Exception as e:
        print(f"\nERRO NO PIPELINE: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_extraction()

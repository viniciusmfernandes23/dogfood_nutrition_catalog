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
# Exemplos reconhecidos: "15kg", "10,1 kg", "1.5kg", "500g", "2x15kg"
_WEIGHT_PATTERN = re.compile(
    r"(?:(\d+(?:[.,]\d+)?)\s*x\s*)?(\d+(?:[.,]\d+)?)\s*(kg|g)\b",
    re.IGNORECASE,
)


def format_currency(value):
    """Formata valor para padrão de moeda brasileira amigável ao Power BI."""
    if value is None or pd.isna(value):
        return None
    # Para evitar que o Power BI interprete errado o separador decimal:
    # A melhor prática para CSVs brasileiros é usar o formato decimal com vírgula 
    # e SEM separador de milhar para evitar que o Power BI confunda o ponto com milhar.
    # Ex: 1500.50 -> "1500,50"
    return f"{value:.2f}".replace(".", ",")


def _parse_weight_kg(sku_name: str | None) -> float | None:
    """
    Extrai o peso em kg a partir do nome do SKU.

    Suporta formatos como "15kg", "10,1 kg", "500g", "2x15kg".
    Retorna None quando não é possível determinar o peso.
    """
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


def _extract_sku_variations(api_payload: dict) -> list[dict]:
    """
    Extrai todas as variações de SKU (items) de um payload VTEX, retornando
    uma lista de dicionários com os campos de preço de cada variação.

    Para rações, cada item representa uma embalagem diferente (ex: 10,1kg, 15kg, 20kg),
    cada uma com seu próprio preço, preço de lista e disponibilidade.

    Estrutura VTEX relevante:
        product.items[]                     → lista de SKUs/variações
            .itemId                         → ID único do SKU
            .name                           → nome da variação (ex: "Frango e Carne 15kg")
            .sellers[].commertialOffer
                .Price                      → preço de venda atual
                .ListPrice                  → preço de tabela (sem desconto)
                .AvailableQuantity          → quantidade disponível em estoque
    """
    variations = []
    items = api_payload.get("items", [])

    for item in items:
        sku_id = item.get("itemId")
        sku_name = item.get("name")
        package_weight_kg = _parse_weight_kg(sku_name)

        price = None
        list_price = None
        available = False

        sellers = item.get("sellers", [])
        if sellers:
            # Prioriza o seller principal (índice 0, geralmente a própria loja)
            comm = sellers[0].get("commertialOffer", {})
            price = comm.get("Price")
            list_price = comm.get("ListPrice")
            available = comm.get("AvailableQuantity", 0) > 0

        # Calcula price_per_kg quando peso e preço estão disponíveis
        price_per_kg = None
        if price is not None and package_weight_kg and package_weight_kg > 0:
            price_per_kg = round(price / package_weight_kg, 4)

        variations.append({
            "sku_id": sku_id,
            "sku_name": sku_name,
            "package_weight_kg": package_weight_kg,
            "price": price,
            "list_price": list_price,
            "subscriber_price": None,  # Não disponível na API pública VTEX
            "price_per_kg": price_per_kg,
            "available": available,
        })

    return variations


# fix_nutrient_scale removido pois o parser atual já retorna o valor real

def run_extraction():
    import argparse
    parser = argparse.ArgumentParser(description="Pipeline de Nutrição Canina")
    parser.add_argument("--mode", type=str, choices=["full", "price"], default="full", 
                        help="Modo: 'full' (atualiza tudo + crawler) ou 'price' (apenas preços)")
    args, _ = parser.parse_known_args()
    
    is_full = args.mode == "full"
    print(f"Iniciando coleta de dados (Modo: {args.mode})...")
    
    # Limpeza de Cache de Módulos Python (Bomba de Limpeza)
    # No Windows/OneDrive, pastas de cache podem estar travadas. Usamos ignore_errors=True.
    for root, dirs, files in os.walk("."):
        for d in dirs:
            if d == "__pycache__":
                try:
                    shutil.rmtree(os.path.join(root, d), ignore_errors=True)
                except Exception:
                    pass
        for f in files:
            if f.endswith(".pyc"):
                try:
                    os.remove(os.path.join(root, f))
                except Exception:
                    pass

    # Pasta dedicada para os arquivos de saída
    OUTPUT_DIR = "output"
    ABS_OUTPUT_DIR = os.path.abspath(OUTPUT_DIR)
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"Pasta '{OUTPUT_DIR}' criada em: {ABS_OUTPUT_DIR}")
    else:
        print(f"Usando pasta de saída em: {ABS_OUTPUT_DIR}")
    
    print(f"--- Pipeline Dogfood Nutrition Catalog v1.3.0 ---")
    print(f"Data/Hora local: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

    try:
        # 1. Coleta de dados da API
        collector = CobasiAPICollector()
        try:
            raw_products = collector.fetch_all()
        except Exception as e:
            print(f"\nERRO NA API COBASI: {e}")
            print("Não foi possível coletar os produtos reais. Interrompendo para evitar dados corrompidos.")
            # Em vez de injetar dados simulados silenciosamente, agora lançamos o erro
            # para que o usuário saiba que a extração falhou.
            raise RuntimeError(f"Falha crítica na extração da API: {e}")

        if not raw_products:
            print("AVISO: Nenhum produto retornado pela API. Verifique os filtros ou status do serviço.")
            product_list = []
        else:
            product_list = []
            for p in raw_products:
                # Extrai todas as variações de SKU do payload VTEX.
                # Cada variação representa uma embalagem diferente (ex: 10,1kg, 15kg, 20kg)
                # com seu próprio preço, preço de lista e disponibilidade.
                sku_variations = []
                if hasattr(p, 'api_payload') and p.api_payload:
                    try:
                        sku_variations = _extract_sku_variations(p.api_payload)
                    except Exception:
                        pass

                # Fallback: se não houver variações extraídas, cria uma entrada vazia
                # para manter o produto no catálogo mesmo sem dados de preço
                if not sku_variations:
                    sku_variations = [{
                        "sku_id": None,
                        "sku_name": None,
                        "package_weight_kg": None,
                        "price": None,
                        "list_price": None,
                        "subscriber_price": None,
                        "price_per_kg": None,
                        "available": False,
                    }]

                p_dict = {
                    'product_id': p.product_id,
                    'product_name': p.product_name,
                    'brand': p.brand,
                    'url': p.url,
                    'category_id': p.category_id,
                    # sku_variations: lista de dicts com dados de preço por variação.
                    # O PriceSnapshotFactBuilder expande cada variação em uma linha separada.
                    'sku_variations': sku_variations,
                    # Campos escalares de preço mantidos para compatibilidade com outros
                    # módulos do pipeline (normalização, semântica, dim_product, etc.)
                    # Usa a primeira variação disponível como valor representativo.
                    'price': next(
                        (v['price'] for v in sku_variations if v.get('price') is not None),
                        None,
                    ),
                    'available': any(v.get('available', False) for v in sku_variations),
                }
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
                # Dicionário para rastrear o melhor match para cada nutriente canônico
                best_matches = {}
                
                for _, nut_data in nutrients.items():
                    nut_type = nut_data['nutrient']
                    target_col = nutrient_mapping.get(nut_type)
                    if not target_col:
                        continue
                    
                    # Ignora unidades que não são por kg para evitar agregação errada
                    # Ex: Energia por sachê não deve ser usada como energia por kg
                    if nut_data['unit'] == 'kcal/sache' and nut_type == 'metabolizable_energy':
                        continue
                        
                    val_real = nut_data['value']
                    alias = nut_data['matched_alias'].lower()
                    
                    # Heurística de prioridade: aliases com 'mín' ou 'máx' são mais específicos
                    # do que aliases genéricos.
                    priority = 1
                    if 'mín' in alias or 'min' in alias or 'máx' in alias or 'max' in alias:
                        priority = 2
                    
                    if nut_type not in best_matches or priority > best_matches[nut_type]['priority']:
                        best_matches[nut_type] = {
                            'value': val_real,
                            'unit': nut_data['unit'],
                            'priority': priority
                        }
                
                # Aplica os melhores matches encontrados no DataFrame
                for nut_type, data in best_matches.items():
                    target_col = nutrient_mapping.get(nut_type)
                    full_df.at[index, target_col] = data['value']
                    full_df.at[index, f"{nut_type}_unit"] = data['unit']
        else:
            print("Pulando extração nutricional (Modo PRICE).")
            if 'raw_guarantee' not in full_df.columns:
                full_df['raw_guarantee'] = None

        # 4. Executar o Orquestrador
        print("Executando orquestrador do pipeline...")
        
        # Forçar limpeza absoluta de nutrientes se for modo full
        if is_full:
            warehouse_path = os.path.join(OUTPUT_DIR, "warehouse")
            nut_file = os.path.join(warehouse_path, "fact_nutrient.csv")
            if os.path.exists(nut_file):
                print(f"Limpando cache de nutrientes antigo: {nut_file}")
                os.remove(nut_file)

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
            print("Aplicando formatação de moeda para arquivos no Warehouse...")
            
            for name, path in result.exported_files.items():
                # Se for a tabela de preços, aplicamos a formatação de moeda diretamente no arquivo do warehouse
                if name == "fact_price_snapshot":
                    temp_df = pd.read_csv(path, encoding="utf-8-sig")
                    # Formata as colunas de preço para padrão brasileiro (vírgula como decimal)
                    for col in ['price', 'list_price', 'subscriber_price', 'price_per_kg']:
                        if col in temp_df.columns:
                            temp_df[col] = temp_df[col].apply(format_currency)
                    temp_df.to_csv(path, index=False, encoding="utf-8-sig")
                
                print(f"  - {path}")
        else:
            print(f"Erro no orquestrador: {result.errors}")

    except Exception as e:
        print(f"ERRO CRÍTICO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_extraction()

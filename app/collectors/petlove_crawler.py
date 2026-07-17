from __future__ import annotations

import json
import re
from bs4 import BeautifulSoup
from app.collectors.http_client import HttpClient
from app.collectors.models import ProductCollection
from app.core.logging import logger

class PetloveCrawlerCollector:
    """
    Coletor para a Petlove focado em extrair preços e EAN para comparação.
    """
    
    BASE_URL = "https://www.petlove.com.br"
    SEARCH_URL = "https://www.petlove.com.br/busca?q="

    def __init__(self):
        self.client = HttpClient()

    def fetch_search_results(self, query: str) -> list[ProductCollection]:
        """
        Busca produtos na Petlove e extrai as informações básicas.
        """
        logger.info(f"Buscando na Petlove: {query}")
        url = f"{self.SEARCH_URL}{query.replace(' ', '+')}"
        
        try:
            try:
                response = self.client.get(url)
                html = response.text
            except Exception as e:
                if "403" in str(e):
                    msg = "BLOQUEIO 403 DETECTADO na Petlove. O site está recusando conexões automatizadas deste ambiente."
                    tip = "DICA: Para coletar dados da Petlove, execute o pipeline em um ambiente com IP residencial ou use um serviço de proxy."
                    logger.error(msg)
                    logger.info(tip)
                    # Força impressão no stdout para garantir visibilidade mesmo se o logger estiver silenciado
                    print(f"\n[PETLOVE] {msg}")
                    print(f"[PETLOVE] {tip}\n")
                raise e

            soup = BeautifulSoup(html, 'html.parser')
            
            # A Petlove armazena os dados em um script JSON chamado __NEXT_DATA__
            script = soup.find('script', id='__NEXT_DATA__')
            if not script:
                # Tenta buscar por padrões de texto se o script não estiver no DOM direto
                match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html)
                if match:
                    data = json.loads(match.group(1))
                else:
                    logger.warning("Script __NEXT_DATA__ não encontrado na Petlove.")
                    return []
            else:
                data = json.loads(script.string)
            
            # Navega no JSON para encontrar os produtos
            # Estrutura: props -> pageProps -> initialData -> products
            try:
                # Tenta diferentes caminhos comuns em aplicações Next.js
                products_data = None
                paths = [
                    ['props', 'pageProps', 'initialData', 'products'],
                    ['props', 'pageProps', 'products'],
                    ['props', 'pageProps', 'data', 'products']
                ]
                for path in paths:
                    curr = data
                    for key in path:
                        if isinstance(curr, dict) and key in curr:
                            curr = curr[key]
                        else:
                            curr = None
                            break
                    if curr:
                        products_data = curr
                        break
                
                if not products_data:
                    raise KeyError("products")
            except KeyError:
                logger.warning("Estrutura de produtos não encontrada no JSON da Petlove.")
                return []

            results = []
            for p in products_data:
                # Extrai EAN do primeiro SKU disponível como padrão
                ean = None
                variants = p.get('variants', [])
                if variants:
                    ean = variants[0].get('ean')

                results.append(
                    ProductCollection(
                        product_id=p.get('id'),
                        product_name=p.get('name'),
                        brand=p.get('brand', {}).get('name'),
                        url=f"{self.BASE_URL}{p.get('url')}",
                        category_id=None, # Não capturamos categoria nutricional da Petlove
                        marketplace="Petlove",
                        ean=ean,
                        api_payload=p # Armazena o JSON completo para extração de SKUs posterior
                    )
                )
            
            logger.info(f"Encontrados {len(results)} produtos na Petlove para '{query}'")
            return results

        except Exception as e:
            logger.error(f"Erro ao coletar Petlove: {e}")
            return []

    def fetch_all(self, queries: list[str]) -> list[ProductCollection]:
        """
        Executa a busca para uma lista de termos (ex: marcas de ração).
        """
        all_products = []
        for q in queries:
            all_products.extend(self.fetch_search_results(q))
        
        return self.remove_duplicates(all_products)

    @staticmethod
    def remove_duplicates(products: list[ProductCollection]) -> list[ProductCollection]:
        unique = {}
        for p in products:
            unique[p.product_id] = p
        return list(unique.values())

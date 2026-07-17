from __future__ import annotations
import json
import re
from bs4 import BeautifulSoup
from app.collectors.http_client import HttpClient
from app.collectors.models import ProductCollection
from app.core.logging import logger

class PetzCollector:
    """
    Coletor para a Petz focado em extrair preços e metadados de produtos.
    """
    
    BASE_URL = "https://www.petz.com.br"
    SEARCH_URL = "https://www.petz.com.br/busca?q="

    def __init__(self):
        self.client = HttpClient()

    def fetch_all(self, queries: list[str]) -> list[ProductCollection]:
        """
        Executa a coleta para múltiplas queries.
        """
        all_products = []
        for query in queries:
            try:
                products = self.fetch_search_results(query)
                all_products.extend(products)
            except Exception as e:
                logger.error(f"Erro ao coletar Petz para query '{query}': {e}")
        
        # Remove duplicatas por ID
        seen_ids = set()
        unique_products = []
        for p in all_products:
            if p.product_id not in seen_ids:
                unique_products.append(p)
                seen_ids.add(p.product_id)
                
        return unique_products

    def fetch_search_results(self, query: str) -> list[ProductCollection]:
        """
        Busca produtos na Petz e extrai as informações básicas.
        """
        logger.info(f"Buscando na Petz: {query}")
        url = f"{self.SEARCH_URL}{query.replace(' ', '+')}"
        
        try:
            try:
                response = self.client.get(url)
                html = response.text
            except Exception as e:
                if "403" in str(e):
                    msg = "BLOQUEIO 403 DETECTADO na Petz. O site está recusando conexões automatizadas."
                    tip = "DICA: Tente executar localmente ou use um serviço de proxy."
                    logger.error(msg)
                    print(f"\n[PETZ] {msg}")
                    print(f"[PETZ] {tip}\n")
                raise e

            soup = BeautifulSoup(html, 'html.parser')
            
            # A Petz costuma ter os produtos em uma estrutura de lista li.li-product
            # ou via script de prateleira. Vamos tentar extrair do HTML retornado.
            results = []
            
            # Tenta encontrar itens de produto
            product_items = soup.select('li.li-product')
            if not product_items:
                # Tenta seletor alternativo
                product_items = soup.select('.product-item')

            for item in product_items:
                try:
                    # Link e ID
                    link_tag = item.select_one('a')
                    if not link_tag: continue
                    
                    product_url = link_tag.get('href', '')
                    if not product_url.startswith('http'):
                        product_url = f"{self.BASE_URL}{product_url}"
                    
                    # ID do produto (geralmente no final da URL ou em data-id)
                    product_id = item.get('data-id')
                    if not product_id:
                        id_match = re.search(r'-(\d+)$', product_url)
                        product_id = id_match.group(1) if id_match else product_url.split('/')[-1]

                    # Nome
                    name_tag = item.select_one('.product-name, h3, .name')
                    name = name_tag.get_text(strip=True) if name_tag else "Produto sem nome"
                    
                    # Preço
                    # Na Petz tem preço normal e preço assinante
                    price_tag = item.select_one('.price-current, .current-price, .price')
                    price_text = price_tag.get_text(strip=True) if price_tag else None
                    price = self._parse_price(price_text)
                    
                    sub_price_tag = item.select_one('.price-subscriber, .subscriber-price')
                    sub_price_text = sub_price_tag.get_text(strip=True) if sub_price_tag else None
                    sub_price = self._parse_price(sub_price_text)

                    # Marca (opcional no card)
                    brand = None
                    brand_tag = item.select_one('.brand, .product-brand')
                    if brand_tag:
                        brand = brand_tag.get_text(strip=True)

                    results.append(ProductCollection(
                        product_id=str(product_id),
                        product_name=name,
                        brand=brand,
                        url=product_url,
                        category_id=None,
                        marketplace="Petz",
                        ean=None, # EAN raramente está no card de busca
                        api_payload={
                            "price": price,
                            "subscriptionPrice": sub_price,
                            "name": name,
                            "id": product_id
                        }
                    ))
                except Exception as e:
                    logger.debug(f"Erro ao parsear item de produto Petz: {e}")
                    continue
            
            return results

        except Exception as e:
            logger.error(f"Erro ao acessar Petz ({url}): {e}")
            return []

    def _parse_price(self, price_str: str | None) -> float | None:
        if not price_str: return None
        # Remove R$, espaços e converte vírgula para ponto
        try:
            cleaned = re.sub(r'[^\d,]', '', price_str).replace(',', '.')
            return float(cleaned)
        except (ValueError, TypeError):
            return None

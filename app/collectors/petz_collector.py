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

    def fetch_all(self, queries: list[str], categories: list[str] | None = None) -> list[ProductCollection]:
        """
        Executa a coleta para múltiplas queries e/ou categorias.
        """
        all_products = []
        
        # Busca por queries (marcas/termos)
        for query in queries:
            try:
                products = self.fetch_search_results(query)
                all_products.extend(products)
            except Exception as e:
                logger.error(f"Erro ao coletar Petz para query '{query}': {e}")
        
        # Busca por categorias (espelhamento Cobasi)
        if categories:
            for cat in categories:
                try:
                    # Na Petz, categorias são URLs amigáveis: /cachorro/racao/racao-seca
                    url = f"{self.BASE_URL}/{cat.strip('/')}"
                    products = self._scrape_page(url)
                    all_products.extend(products)
                except Exception as e:
                    logger.debug(f"Erro ao coletar categoria Petz '{cat}': {e}")

        # Remove duplicatas por ID
        seen_ids = set()
        unique_products = []
        for p in all_products:
            if p.product_id not in seen_ids:
                unique_products.append(p)
                seen_ids.add(p.product_id)
                
        return unique_products

    def _scrape_page(self, url: str) -> list[ProductCollection]:
        """Método genérico para extrair produtos de qualquer página da Petz."""
        try:
            response = self.client.get(url)
            return self._parse_html(response.text)
        except Exception as e:
            if "403" in str(e):
                print(f"[PETZ] BLOQUEIO 403 na URL: {url}")
            return []

    def _parse_html(self, html: str) -> list[ProductCollection]:
        """Parser robusto para extrair produtos do HTML da Petz."""
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        
        # A Petz usa cards de produto com várias classes possíveis
        product_items = soup.select('li.li-product, .product-item, div[data-id], .card-product')
        
        for item in product_items:
            try:
                # Link
                link_tag = item.select_one('a[href*="/produto/"]') or item.select_one('a')
                if not link_tag: continue
                
                product_url = link_tag.get('href', '')
                if not product_url.startswith('http'):
                    product_url = f"{self.BASE_URL}{product_url}"
                
                # ID
                product_id = item.get('data-id') or item.get('id')
                if not product_id:
                    id_match = re.search(r'-(\d+)$', product_url)
                    product_id = id_match.group(1) if id_match else product_url.split('/')[-1]

                # Nome
                name_tag = item.select_one('.product-name, h3, .name, [itemprop="name"]')
                name = name_tag.get_text(strip=True) if name_tag else ""
                if not name and link_tag.get('title'):
                    name = link_tag.get('title')
                
                # Preços
                price = None
                sub_price = None
                
                # Busca por padrões de R$ no texto para maior robustez
                text = item.get_text()
                price_matches = re.findall(r'R\$\s*(\d+(?:[.,]\d{2})?)', text)
                if price_matches:
                    # Geralmente o primeiro é o preço de, o segundo o por, o terceiro assinante
                    # Mas varia muito. Vamos tentar pegar os dois menores valores.
                    vals = sorted([self._parse_price(m) for m in price_matches if self._parse_price(m)])
                    if vals:
                        price = vals[-1] # Assume o maior como preço base (ou único)
                        if len(vals) > 1:
                            sub_price = vals[0] # Assume o menor como assinante

                if not name: continue

                results.append(ProductCollection(
                    product_id=str(product_id),
                    product_name=name,
                    brand=None,
                    url=product_url,
                    category_id=None,
                    marketplace="Petz",
                    ean=None,
                    api_payload={
                        "price": price,
                        "subscriptionPrice": sub_price,
                        "name": name,
                        "id": product_id
                    }
                ))
            except Exception:
                continue
        return results

    def fetch_search_results(self, query: str) -> list[ProductCollection]:
        """Busca produtos na Petz via URL de busca."""
        url = f"{self.SEARCH_URL}{query.replace(' ', '+')}"
        return self._scrape_page(url)

    def _parse_price(self, price_str: str | None) -> float | None:
        if not price_str: return None
        # Remove R$, espaços e converte vírgula para ponto
        try:
            cleaned = re.sub(r'[^\d,]', '', price_str).replace(',', '.')
            return float(cleaned)
        except (ValueError, TypeError):
            return None

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
        """Parser ultra-robusto para extrair produtos da Petz via HTML ou JSON embutido."""
        results = []
        
        # ESTRATÉGIA 1: Tenta extrair do script window.dataLayer (comum em sites Linx/Petz)
        try:
            # Procura por listas de produtos no dataLayer
            json_matches = re.findall(r'\"list\":\s*(\[.*?\])', html, re.DOTALL)
            for json_str in json_matches:
                try:
                    data = json.loads(json_str)
                    for item in data:
                        if isinstance(item, dict) and 'id' in item and ('price' in item or 'price_subscriber' in item):
                            results.append(self._create_product_from_dict(item))
                except: continue
        except: pass

        # ESTRATÉGIA 2: Tenta extrair do __NEXT_DATA__ (Next.js)
        if not results:
            try:
                next_data = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html)
                if next_data:
                    data = json.loads(next_data.group(1))
                    # Navega recursivamente no JSON em busca de objetos que pareçam produtos
                    def find_products(obj):
                        if isinstance(obj, dict):
                            if 'id' in obj and 'name' in obj and ('price' in obj or 'salePrice' in obj):
                                results.append(self._create_product_from_dict(obj))
                            for v in obj.values(): find_products(v)
                        elif isinstance(obj, list):
                            for v in obj: find_products(v)
                    find_products(data)
            except: pass

        # ESTRATÉGIA 3: Fallback para o parser de HTML (BS4) se os JSONs falharem
        if not results:
            soup = BeautifulSoup(html, 'html.parser')
            product_items = soup.select('li.li-product, .product-item, div[data-id], .card-product')
            for item in product_items:
                try:
                    link_tag = item.select_one('a[href*="/produto/"]') or item.select_one('a')
                    if not link_tag: continue
                    product_url = link_tag.get('href', '')
                    if not product_url.startswith('http'): product_url = f"{self.BASE_URL}{product_url}"
                    
                    product_id = item.get('data-id') or item.get('id')
                    if not product_id:
                        id_match = re.search(r'-(\d+)$', product_url)
                        product_id = id_match.group(1) if id_match else product_url.split('/')[-1]

                    name_tag = item.select_one('.product-name, h3, .name, [itemprop="name"]')
                    name = name_tag.get_text(strip=True) if name_tag else ""
                    if not name and link_tag.get('title'): name = link_tag.get('title')
                    
                    # Preços via texto bruto
                    text = item.get_text()
                    price_matches = re.findall(r'R\$\s*(\d+(?:[.,]\d{2})?)', text)
                    price, sub_price = None, None
                    if price_matches:
                        vals = sorted([self._parse_price(m) for m in price_matches if self._parse_price(m)])
                        if vals:
                            price = vals[-1]
                            if len(vals) > 1: sub_price = vals[0]

                    if name:
                        results.append(ProductCollection(
                            product_id=str(product_id),
                            product_name=name,
                            brand=None,
                            url=product_url,
                            category_id=None,
                            marketplace="Petz",
                            ean=None,
                            api_payload={"price": price, "subscriptionPrice": sub_price, "name": name, "id": product_id}
                        ))
                except: continue
        
        return results

    def _create_product_from_dict(self, item: dict) -> ProductCollection:
        """Helper para criar objeto de produto a partir de um dicionário JSON."""
        return ProductCollection(
            product_id=str(item.get('id') or item.get('sku') or item.get('productId')),
            product_name=item.get('name') or item.get('title'),
            brand=item.get('brand'),
            url=f"{self.BASE_URL}/produto/{item.get('id')}",
            category_id=None,
            marketplace="Petz",
            ean=item.get('ean'),
            api_payload={
                "price": self._parse_price(str(item.get('price') or item.get('salePrice'))),
                "subscriptionPrice": self._parse_price(str(item.get('price_subscriber') or item.get('subscriptionPrice'))),
                "name": item.get('name'),
                "id": item.get('id')
            }
        )

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

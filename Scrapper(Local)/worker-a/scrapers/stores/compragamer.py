"""
Scraper para CompraGamer (https://compragamer.com).

CompraGamer carga todos sus productos desde un JSON estático en:
    https://static.compragamer.com/productos

Esto nos permite hacer scraping sin Playwright ni renderizado de JS:
    1. Fetch del JSON completo con requests (todos los productos).
    2. Filtrado local por el query de búsqueda.
    3. Construcción de los resultados.

Librerías necesarias:
    - requests  (pip install requests)
"""

import re
from urllib.parse import quote_plus

from scrapers.base_scraper import BaseScraper, Product
from scrapers.registry import ScraperRegistry


@ScraperRegistry.register
class CompraGamerScraper(BaseScraper):
    """
    Scraper para CompraGamer.

    Usa el endpoint estático https://static.compragamer.com/productos
    que devuelve un JSON con TODOS los productos de la tienda.
    El filtrado por búsqueda se hace localmente.
    """

    # URL del JSON estático con todos los productos
    PRODUCTS_JSON_URL = "https://static.compragamer.com/productos"

    # URL base para construir links a productos individuales
    BASE_URL = "https://compragamer.com"
    PRODUCT_URL_TEMPLATE = "https://compragamer.com/producto/{id_producto}"

    # URL de búsqueda (usada solo para logging, no para scraping)
    SEARCH_URL = "https://compragamer.com/productos?criterio={query}"

    # Cantidad máxima de resultados a devolver
    MAX_RESULTS = 20

    @property
    def store_name(self) -> str:
        return "compragamer"

    def build_search_url(self, query: str) -> str:
        """Construye la URL de búsqueda (solo para referencia/logging)."""
        encoded = quote_plus(query)
        return self.SEARCH_URL.format(query=encoded)

    def search(self, query: str) -> list[dict]:
        """
        Sobreescribe el método search() de BaseScraper porque
        CompraGamer no necesita el flujo fetch→parse tradicional.

        En vez de eso:
            1. Descarga el JSON estático de todos los productos.
            2. Filtra localmente por el query.
            3. Devuelve los resultados.
        """
        print(f"[{self.store_name}] Buscando: {query}")
        print(f"[{self.store_name}] Descargando catálogo desde: {self.PRODUCTS_JSON_URL}")

        # Descargar catálogo completo
        all_products = self._fetch_catalog()

        if not all_products:
            print(f"[{self.store_name}] Error: no se pudo obtener el catálogo")
            return []

        print(f"[{self.store_name}] Catálogo: {len(all_products)} productos totales")

        # Filtrar por búsqueda
        matched = self._filter_products(all_products, query)

        print(f"[{self.store_name}] Productos encontrados para '{query}': {len(matched)}")

        # Convertir a formato de salida
        results = []
        for item in matched[:self.MAX_RESULTS]:
            product = self._item_to_product(item)
            if product:
                results.append({
                    "name": product.name,
                    "price": product.price,
                    "url": product.url,
                })

        return results

    def _fetch_catalog(self) -> list[dict]:
        """Descarga el JSON estático con todos los productos."""
        import requests

        try:
            response = requests.get(
                self.PRODUCTS_JSON_URL,
                headers=self.headers,
                timeout=15,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"[{self.store_name}] Error descargando catálogo: {e}")
            return []

    def _filter_products(self, products: list[dict], query: str) -> list[dict]:
        """
        Filtra productos cuyo nombre contenga TODAS las palabras del query.
        Ordena por relevancia (productos con match más exacto primero).
        """
        query_words = query.lower().split()
        matched = []

        for product in products:
            name = (product.get("nombre") or "").lower()

            if not name:
                continue

            # Verificar que TODAS las palabras del query estén en el nombre
            if all(word in name for word in query_words):
                # Calcular score de relevancia:
                #   - Bonus si el nombre empieza con la query
                #   - Bonus si la query aparece como frase exacta
                #   - Penalidad por largo del nombre (más corto = más relevante)
                score = 0
                full_query = query.lower()

                if name.startswith(full_query):
                    score += 100
                if full_query in name:
                    score += 50
                score -= len(name) * 0.1  # Penalidad por largo

                matched.append((score, product))

        # Ordenar por score descendente
        matched.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in matched]

    def _item_to_product(self, item: dict) -> Product | None:
        """Convierte un item del JSON del catálogo en un Product."""
        name = item.get("nombre")
        if not name:
            return None

        # Precio: probar diferentes campos
        price = (
            item.get("precioEspecial")
            or item.get("precio")
            or item.get("precio_especial")
            or item.get("precio_final")
            or 0
        )

        # Convertir precio a entero
        if isinstance(price, str):
            price = int(re.sub(r"[^\d]", "", price) or "0")
        else:
            price = int(price)

        # URL del producto
        product_id = item.get("id_producto") or item.get("id") or ""
        
        # CompraGamer ahora requiere el nombre en la URL: /producto/Nombre_Del_Producto_1234
        name_clean = re.sub(r'[^a-zA-Z0-9\s-]', '', str(name))
        name_slug = re.sub(r'\s+', '_', name_clean.strip())
        
        url = f"https://compragamer.com/producto/{name_slug}_{product_id}"

        return Product(name=str(name), price=price, url=url)

    # Estos métodos son requeridos por la clase base pero no se usan
    # porque sobreescribimos search() directamente.

    def parse_products(self, html: str, query: str) -> list[Product]:
        """No utilizado — CompraGamer usa el flujo directo via JSON."""
        return []

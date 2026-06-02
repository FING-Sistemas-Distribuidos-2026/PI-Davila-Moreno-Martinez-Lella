"""
Scraper de ejemplo — plantilla para implementar una tienda nueva.

Para crear un scraper de una tienda real:
    1. Copiar este archivo y renombrarlo (ej. mercadolibre.py).
    2. Implementar store_name, build_search_url y parse_products.
    3. Importar la clase en stores/__init__.py para que se auto-registre.
"""

from scrapers.base_scraper import BaseScraper, Product
from scrapers.registry import ScraperRegistry

# Para parsear HTML
# from bs4 import BeautifulSoup


@ScraperRegistry.register
class ExampleStoreScraper(BaseScraper):
    """
    Scraper de ejemplo que muestra la estructura esperada.
    Reemplazar con lógica real de scraping.
    """

    @property
    def store_name(self) -> str:
        return "example-store"

    def build_search_url(self, query: str) -> str:
        # Construir la URL de búsqueda de la tienda.
        # Ejemplo: https://www.example-store.com/search?q=zapatillas+running
        encoded_query = query.replace(" ", "+")
        return f"https://www.example-store.com/search?q={encoded_query}"

    def parse_products(self, html: str, query: str) -> list[Product]:
        """
        Parsear el HTML de la página de resultados.

        Ejemplo con BeautifulSoup:

            soup = BeautifulSoup(html, "html.parser")

            products = []
            for item in soup.select(".product-card"):
                name = item.select_one(".product-title").get_text(strip=True)
                price_text = item.select_one(".product-price").get_text(strip=True)
                price = int(price_text.replace("$", "").replace(".", "").strip())
                url = item.select_one("a.product-link")["href"]

                products.append(Product(name=name, price=price, url=url))

            return products
        """
        # Placeholder — devuelve lista vacía hasta implementar el parseo real.
        return []

"""
Scraper para GamingCity (https://www.gamingcity.com.ar).

GamingCity usa un endpoint PHP clásico para la búsqueda:
    https://www.gamingcity.com.ar/busqueda_avanzada.php?buscar=1&palabra={query}

Esto devuelve HTML server-rendered con los productos, por lo que
se parsea directamente con BeautifulSoup sin necesidad de Playwright.

Librerías necesarias:
    - requests       (pip install requests)
    - beautifulsoup4 (pip install beautifulsoup4)
"""

import re
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from scrapers.base_scraper import BaseScraper, Product
from scrapers.registry import ScraperRegistry


@ScraperRegistry.register
class GamingCityScraper(BaseScraper):
    """
    Scraper para GamingCity.

    Usa el endpoint de búsqueda avanzada que devuelve HTML con los
    productos filtrados. Se parsea con BeautifulSoup.
    """

    BASE_URL = "https://www.gamingcity.com.ar"
    SEARCH_URL = (
        "https://www.gamingcity.com.ar/busqueda_avanzada.php"
        "?buscar=1&palabra={query}"
    )

    # Cantidad máxima de resultados a devolver
    MAX_RESULTS = 20

    @property
    def store_name(self) -> str:
        return "gamingcity"

    def build_search_url(self, query: str) -> str:
        """Construye la URL de búsqueda para GamingCity."""
        encoded = quote_plus(query)
        return self.SEARCH_URL.format(query=encoded)

    def parse_products(self, html: str, query: str) -> list[Product]:
        """
        Parsea el HTML de la página de resultados de búsqueda.

        La estructura de cada producto en GamingCity es:
            <div class="cajasoferta">
                <div class="product">
                    <div class="description">
                        <h4><a class="titprod" href="...">Nombre</a></h4>
                    </div>
                    <div class="price"><span>$ 135.849</span></div>
                </div>
            </div>
        """
        soup = BeautifulSoup(html, "html.parser")

        products = []

        # Cada producto está dentro de un div con clase "cajasoferta"
        items = soup.select("div.cajasoferta")

        for item in items[:self.MAX_RESULTS]:
            product = self._parse_single_product(item)
            if product:
                products.append(product)

        return products

    def _parse_single_product(self, item) -> Product | None:
        """Extrae un Product de un elemento HTML de producto individual."""

        # --- Nombre y URL ---
        link = item.select_one("h4 a.titprod")
        if not link:
            return None

        name = link.get_text(strip=True)
        if not name:
            return None

        href = link.get("href", "")
        # Construir URL absoluta si es relativa
        if href and not href.startswith("http"):
            url = f"{self.BASE_URL}/{href.lstrip('/')}"
        else:
            url = href

        # --- Precio ---
        # Algunos productos tienen precios anidados (precio tachado + precio oferta).
        # Priorizar: precio oferta (price-sales) > precio estándar (price-standard) > primer span
        price_sales = item.select_one("span.price-sales")
        price_standard = item.select_one("span.price-standard")
        price_fallback = item.select_one("div.price span")

        price_el = price_sales or price_standard or price_fallback
        if price_el:
            # Usar solo el texto directo del elemento, no de hijos anidados
            price_text = price_el.string or price_el.get_text(strip=True)
            price = int(re.sub(r"[^\d]", "", price_text) or "0")
        else:
            price = 0

        return Product(name=name, price=price, url=url)

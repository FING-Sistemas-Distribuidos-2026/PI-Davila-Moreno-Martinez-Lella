"""
Clase base (wrapper) para todos los scrapers de tiendas.

Cada tienda concreta debe heredar de BaseScraper e implementar
los métodos abstractos para definir cómo se construye la URL de
búsqueda y cómo se extraen los productos del HTML de respuesta.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
import requests


@dataclass
class Product:
    """Resultado individual extraído de una tienda."""
    name: str
    price: int
    url: str


class BaseScraper(ABC):
    """
    Wrapper base para scrapers de tiendas.

    Subclases deben implementar:
        - store_name:    nombre identificador de la tienda.
        - build_search_url: construir la URL de búsqueda a partir del query.
        - parse_products:   extraer lista de Product del HTML obtenido.

    Opcionalmente pueden sobreescribir:
        - headers:  headers HTTP personalizados.
        - fetch:    lógica de request personalizada (ej. Playwright).
    """

    # ------------------------------------------------------------------ #
    #  Propiedades abstractas
    # ------------------------------------------------------------------ #

    @property
    @abstractmethod
    def store_name(self) -> str:
        """Identificador único de la tienda (ej. 'mercadolibre')."""
        ...

    # ------------------------------------------------------------------ #
    #  Métodos abstractos
    # ------------------------------------------------------------------ #

    @abstractmethod
    def build_search_url(self, query: str) -> str:
        """
        Construye la URL de búsqueda para el query dado.

        Args:
            query: término de búsqueda del usuario.

        Returns:
            URL completa para realizar el GET.
        """
        ...

    @abstractmethod
    def parse_products(self, html: str, query: str) -> list[Product]:
        """
        Extrae una lista de productos del HTML de la página de resultados.

        Args:
            html:  contenido HTML de la respuesta.
            query: término de búsqueda original (útil para filtrar).

        Returns:
            Lista de Product encontrados.
        """
        ...

    # ------------------------------------------------------------------ #
    #  Métodos con implementación por defecto (sobreescribibles)
    # ------------------------------------------------------------------ #

    @property
    def headers(self) -> dict:
        """Headers HTTP usados en el request. Sobreescribir si la tienda
        necesita headers específicos (User-Agent, cookies, etc.)."""
        return {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "es-AR,es;q=0.9,en;q=0.8",
        }

    def fetch(self, url: str) -> str:
        """
        Realiza el HTTP GET y devuelve el HTML.

        Sobreescribir si la tienda requiere renderizado JS
        (ej. usando Playwright o Selenium).

        Args:
            url: URL a consultar.

        Returns:
            Contenido HTML de la respuesta.

        Raises:
            requests.HTTPError: si el status code no es 2xx.
        """
        response = requests.get(url, headers=self.headers, timeout=15)
        response.raise_for_status()
        return response.text

    # ------------------------------------------------------------------ #
    #  Método público principal
    # ------------------------------------------------------------------ #

    def search(self, query: str) -> list[dict]:
        """
        Ejecuta el flujo completo de scraping:
            1. Construir URL de búsqueda.
            2. Hacer el request HTTP.
            3. Parsear los productos del HTML.

        Args:
            query: término de búsqueda del usuario.

        Returns:
            Lista de dicts con keys: name, price, url.
        """
        url = self.build_search_url(query)

        print(f"[{self.store_name}] Buscando: {query}")
        print(f"[{self.store_name}] URL: {url}")

        html = self.fetch(url)

        products = self.parse_products(html, query)

        print(f"[{self.store_name}] Productos encontrados: {len(products)}")

        return [
            {
                "name": p.name,
                "price": p.price,
                "url": p.url,
            }
            for p in products
        ]

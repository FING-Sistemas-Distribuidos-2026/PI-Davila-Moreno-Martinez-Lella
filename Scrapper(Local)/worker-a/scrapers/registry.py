"""
Registro central de scrapers disponibles.

Permite registrar nuevas tiendas con un decorador y obtener
la instancia del scraper correcto dado un nombre de tienda.
"""

from .base_scraper import BaseScraper


class ScraperRegistry:
    """
    Factory / Registry de scrapers.

    Uso:
        # Registrar un scraper (se hace con el decorador @register)
        @ScraperRegistry.register
        class MiTiendaScraper(BaseScraper):
            ...

        # Obtener un scraper por nombre
        scraper = ScraperRegistry.get("mi-tienda")
        results = scraper.search("zapatillas running")

        # Listar tiendas disponibles
        tiendas = ScraperRegistry.available_stores()
    """

    _scrapers: dict[str, type[BaseScraper]] = {}

    @classmethod
    def register(cls, scraper_class: type[BaseScraper]) -> type[BaseScraper]:
        """
        Decorador para registrar una subclase de BaseScraper.

        Ejemplo:
            @ScraperRegistry.register
            class MercadoLibreScraper(BaseScraper):
                ...
        """
        instance = scraper_class()
        cls._scrapers[instance.store_name] = scraper_class
        return scraper_class

    @classmethod
    def get(cls, store_name: str) -> BaseScraper:
        """
        Devuelve una instancia del scraper para la tienda indicada.

        Args:
            store_name: nombre de la tienda registrada.

        Returns:
            Instancia del scraper correspondiente.

        Raises:
            ValueError: si la tienda no está registrada.
        """
        scraper_class = cls._scrapers.get(store_name)

        if scraper_class is None:
            available = ", ".join(cls._scrapers.keys()) or "(ninguna)"
            raise ValueError(
                f"Scraper '{store_name}' no registrado. "
                f"Disponibles: {available}"
            )

        return scraper_class()

    @classmethod
    def available_stores(cls) -> list[str]:
        """Retorna la lista de nombres de tiendas registradas."""
        return list(cls._scrapers.keys())

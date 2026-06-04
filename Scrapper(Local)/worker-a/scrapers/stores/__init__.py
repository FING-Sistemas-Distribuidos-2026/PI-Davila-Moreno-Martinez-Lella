# Importar todas las tiendas para que se auto-registren al cargar el paquete.
# Agregar un import por cada nueva tienda implementada.

from .example_store import ExampleStoreScraper
from .compragamer import CompraGamerScraper
from .maximus import MaximusScraper
from .gamingcity import GamingCityScraper

__all__ = ["ExampleStoreScraper", "CompraGamerScraper", "MaximusScraper", "GamingCityScraper"]

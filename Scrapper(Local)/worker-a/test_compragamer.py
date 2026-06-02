"""
Script de prueba para verificar el scraper de CompraGamer.

Uso:
    cd worker-a
    pip install playwright beautifulsoup4 requests
    playwright install chromium
    python test_compragamer.py
"""

import sys
import os

# Agregar el directorio actual al path para las imports
sys.path.insert(0, os.path.dirname(__file__))

from scrapers import ScraperRegistry
# Importar stores para que se auto-registren
import scrapers.stores  # noqa: F401


def main():
    print("=" * 60)
    print("Test del Scraper de CompraGamer")
    print("=" * 60)

    # Verificar que el scraper está registrado
    print(f"\nTiendas disponibles: {ScraperRegistry.available_stores()}")

    # Obtener el scraper
    scraper = ScraperRegistry.get("compragamer")
    print(f"Scraper obtenido: {scraper.__class__.__name__}")
    print(f"Tienda: {scraper.store_name}")

    # Ejecutar búsqueda
    query = "disco duro"
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])

    print(f"\nBuscando: '{query}'")
    print("-" * 60)

    try:
        results = scraper.search(query)

        if not results:
            print("\n⚠  No se encontraron productos.")
            print("   Esto puede deberse a:")
            print("   - Protección anti-bot del sitio")
            print("   - Selectores CSS desactualizados")
            print("   - Timeout de carga")
        else:
            print(f"\n✓  Se encontraron {len(results)} productos:\n")
            for i, product in enumerate(results, 1):
                print(f"  {i}. {product['name']}")
                print(f"     Precio: ${product['price']:,}")
                print(f"     URL: {product['url']}")
                print()

    except Exception as e:
        print(f"\n✗  Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

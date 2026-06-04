"""
Test de validación del scraper de Maximus.

Verifica que el scraper funciona correctamente llamando al
método search() y validando la estructura de los resultados.
"""

import sys
import os

# Agregar el directorio del worker al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scrapers.registry import ScraperRegistry
import scrapers.stores  # Auto-registra todos los scrapers


def separator(title: str):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def test_registry():
    """Verifica que el scraper de Maximus está registrado."""
    separator("TEST 1: Registro en ScraperRegistry")

    stores = ScraperRegistry.available_stores()
    print(f"  Tiendas registradas: {stores}")

    assert "maximus" in stores, "❌ 'maximus' no está registrado"
    print("  ✅ 'maximus' está registrado correctamente")


def test_search(query: str, min_results: int = 1):
    """Ejecuta una búsqueda y valida los resultados."""
    separator(f"TEST: Buscar '{query}'")

    scraper = ScraperRegistry.get("maximus")
    results = scraper.search(query)

    print(f"\n  Resultados: {len(results)}")

    # Validar que hay resultados
    assert len(results) >= min_results, (
        f"❌ Se esperaban al menos {min_results} resultados, "
        f"pero se obtuvieron {len(results)}"
    )

    # Validar estructura de cada resultado
    for i, result in enumerate(results[:5]):
        assert "name" in result, f"❌ Resultado {i} no tiene 'name'"
        assert "price" in result, f"❌ Resultado {i} no tiene 'price'"
        assert "url" in result, f"❌ Resultado {i} no tiene 'url'"

        assert isinstance(result["name"], str), f"❌ 'name' no es string"
        assert isinstance(result["price"], int), f"❌ 'price' no es int"
        assert isinstance(result["url"], str), f"❌ 'url' no es string"

        assert result["price"] > 0, f"❌ Precio <= 0: {result['price']}"
        assert "maximus.com.ar" in result["url"], f"❌ URL inválida: {result['url']}"

        print(f"  ✅ {i+1}. {result['name'][:60]}...")
        print(f"       Precio: ${result['price']:,} | URL válida")

    print(f"\n  ✅ Todos los resultados son válidos")


def test_store_name():
    """Verifica que store_name es correcto."""
    separator("TEST: store_name")

    scraper = ScraperRegistry.get("maximus")
    assert scraper.store_name == "maximus", (
        f"❌ store_name incorrecto: '{scraper.store_name}'"
    )
    print("  ✅ store_name = 'maximus'")


def test_build_search_url():
    """Verifica que build_search_url genera una URL válida."""
    separator("TEST: build_search_url")

    scraper = ScraperRegistry.get("maximus")
    url = scraper.build_search_url("ryzen 5")

    assert "maximus.com.ar" in url, f"❌ URL inválida: {url}"
    assert "ryzen" in url, f"❌ Query no está en URL: {url}"
    print(f"  ✅ URL generada: {url}")


if __name__ == "__main__":
    print("🧪 TESTS DEL SCRAPER DE MAXIMUS")
    print("=" * 70)

    test_registry()
    test_store_name()
    test_build_search_url()

    # Tests de búsqueda real
    test_search("5080", min_results=3)
    test_search("teclado", min_results=5)
    test_search("ryzen 5", min_results=5)

    separator("TODOS LOS TESTS PASARON ✅")

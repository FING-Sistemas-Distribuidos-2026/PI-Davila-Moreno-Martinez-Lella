"""
Scraper para Maximus Gaming Hardware (https://www.maximus.com.ar).

Maximus usa un backend ASP.NET (GlobalBluePoint© ERP) con un frontend
Vue.js 2 que carga los productos dinámicamente desde una API interna.

Estrategia de scraping (sin Playwright ni parseo de HTML):
    1. Crear una sesión HTTP para obtener cookies ASP.NET válidas.
    2. Llamar al endpoint POST /wfmWebSite2.aspx/wsNRW_Script con
       el script "web.MAX.GetItemList4Search_v5".
    3. Parsear el JSON de respuesta (doble-nested) para extraer items.
    4. Construir los resultados con nombre, precio y URL.

Librerías necesarias:
    - requests  (pip install requests)
"""

import json
import re

from scrapers.base_scraper import BaseScraper, Product
from scrapers.registry import ScraperRegistry


@ScraperRegistry.register
class MaximusScraper(BaseScraper):
    """
    Scraper para Maximus Gaming Hardware.

    Usa la API interna de ASP.NET PageMethods para obtener los productos
    directamente como JSON, sin necesidad de renderizado de JS.

    Requiere una sesión HTTP con cookies ASP.NET válidas, que se obtienen
    haciendo un GET inicial a la home page.
    """

    # ------------------------------------------------------------------ #
    #  Constantes
    # ------------------------------------------------------------------ #

    # GUID del WebSite de Maximus (identificador del ERP GlobalBluePoint)
    WS_GUID = "a632009a-7686-4fcb-a0b4-24b18caf5234"

    # Endpoint del PageMethod que ejecuta scripts server-side
    API_URL = "https://www.maximus.com.ar/wfmWebSite2.aspx/wsNRW_Script"

    # URL base para la home (usada para obtener cookies de sesión)
    BASE_URL = "https://www.maximus.com.ar"

    # Template para construir la URL de un producto individual
    PRODUCT_URL_TEMPLATE = (
        "https://www.maximus.com.ar/Producto/"
        "{item_desc4link}/ITEM={item_id}/maximus.aspx?PN={item_code4web}"
    )

    # URL de búsqueda (usada solo para logging, no para scraping)
    SEARCH_URL = (
        "https://www.maximus.com.ar/Productos/maximus.aspx?"
        "/CAT=-1/SCAT=-1/M=-1/BUS={query}/OR=1/PAGE=1/"
    )

    # Cantidad máxima de resultados a devolver
    MAX_RESULTS = 20

    # Identificador del script server-side que retorna los productos
    SCRIPT_LABEL = "web.MAX.GetItemList4Search_v5"

    # ------------------------------------------------------------------ #
    #  Propiedades
    # ------------------------------------------------------------------ #

    @property
    def store_name(self) -> str:
        return "maximus"

    def build_search_url(self, query: str) -> str:
        """Construye la URL de búsqueda (solo para referencia/logging)."""
        encoded = query.replace(" ", "%20")
        return self.SEARCH_URL.format(query=encoded)

    # ------------------------------------------------------------------ #
    #  Método principal: sobreescribe search() de BaseScraper
    # ------------------------------------------------------------------ #

    def search(self, query: str) -> list[dict]:
        """
        Sobreescribe el método search() de BaseScraper porque
        Maximus no necesita el flujo fetch→parse tradicional.

        En vez de eso:
            1. Crea una sesión HTTP con cookies ASP.NET.
            2. Llama a la API interna con el query de búsqueda.
            3. Parsea el JSON de respuesta y devuelve los resultados.
        """
        import requests

        print(f"[{self.store_name}] Buscando: {query}")
        print(f"[{self.store_name}] Obteniendo sesión...")

        # Paso 1: Crear sesión con cookies válidas
        session = self._create_session(requests)
        if session is None:
            print(f"[{self.store_name}] Error: no se pudo crear la sesión")
            return []

        # Paso 2: Llamar a la API de búsqueda
        all_items = self._fetch_products(session, query)

        if not all_items:
            print(f"[{self.store_name}] No se encontraron productos para '{query}'")
            return []

        print(f"[{self.store_name}] Productos encontrados: {len(all_items)}")

        # Paso 3: Convertir a formato de salida
        results = []
        for item in all_items[:self.MAX_RESULTS]:
            product = self._item_to_product(item)
            if product:
                results.append({
                    "name": product.name,
                    "price": product.price,
                    "url": product.url,
                })

        return results

    # ------------------------------------------------------------------ #
    #  Métodos privados
    # ------------------------------------------------------------------ #

    def _create_session(self, requests_module) -> "requests.Session | None":
        """
        Crea una sesión HTTP visitando la home de Maximus para obtener
        las cookies ASP.NET necesarias para las llamadas a la API.

        Returns:
            requests.Session con cookies válidas, o None si falla.
        """
        try:
            session = requests_module.Session()
            session.headers.update(self.headers)

            # GET a la home para obtener cookies de sesión
            response = session.get(self.BASE_URL, timeout=15)
            response.raise_for_status()

            print(f"[{self.store_name}] Sesión creada (cookies: {len(session.cookies)})")
            return session

        except Exception as e:
            print(f"[{self.store_name}] Error creando sesión: {e}")
            return None

    def _fetch_products(self, session, query: str) -> list[dict]:
        """
        Llama a la API interna de Maximus para obtener los productos
        que coinciden con el query de búsqueda.

        La API usa el patrón ASP.NET PageMethods:
            - Endpoint: POST /wfmWebSite2.aspx/wsNRW_Script
            - Script: web.MAX.GetItemList4Search_v5
            - Parámetros de búsqueda en JSON anidado

        Args:
            session: sesión HTTP con cookies válidas.
            query: término de búsqueda del usuario.

        Returns:
            Lista de dicts con los datos crudos de los productos.
        """
        # Parámetros de búsqueda (misma estructura que Vue.js usa)
        search_params = {
            "ws_id": self.WS_GUID,
            "comp_id": 1,
            "prli_id": 17,
            "cust_id": -1,
            "page": 1,
            "cat_id": -1,
            "subcat_id": -1,
            "brand_id": -1,
            "local": 0,
            "search": query,
            "order": 1,          # 1=más vendidos, 3=menor precio
            "price_min": "",
            "price_max": "",
            "wco_tV": []
        }

        # Payload del PageMethod wsNRW_Script
        payload = {
            "guidWS_Id": self.WS_GUID,
            "strScriptLabel": self.SCRIPT_LABEL,
            "JSonParameters": json.dumps(search_params),
        }

        # Headers específicos para la llamada AJAX
        api_headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": self.BASE_URL,
            "Referer": f"{self.BASE_URL}/Productos/maximus.aspx",
        }

        try:
            response = session.post(
                self.API_URL,
                json=payload,
                headers=api_headers,
                timeout=15,
            )
            response.raise_for_status()

            # Parsear la respuesta (doble-nested JSON)
            return self._parse_api_response(response.json())

        except Exception as e:
            print(f"[{self.store_name}] Error llamando API: {e}")
            return []

    def _parse_api_response(self, data: dict) -> list[dict]:
        """
        Parsea la respuesta de la API de Maximus.

        La respuesta tiene esta estructura de JSON anidado:
            {
                "d": "{\"scName\":\"...\", \"data\": \"{...}\"}"
            }

        Donde 'd' es un string JSON que contiene otro string JSON 'data'
        con los items del catálogo.

        Args:
            data: dict con la respuesta JSON del endpoint.

        Returns:
            Lista de dicts con los items de productos.
        """
        if not data:
            return []

        # Primer nivel: extraer el campo "d"
        d_value = data.get("d", "")

        if not isinstance(d_value, str):
            return []

        try:
            d_parsed = json.loads(d_value)
        except (json.JSONDecodeError, TypeError):
            print(f"[{self.store_name}] Error parseando respuesta 'd': {d_value[:200]}")
            return []

        if not isinstance(d_parsed, dict):
            return []

        # Segundo nivel: extraer el campo "data"
        items_raw = d_parsed.get("data", "")

        if isinstance(items_raw, str):
            try:
                items_data = json.loads(items_raw)
            except (json.JSONDecodeError, TypeError):
                print(f"[{self.store_name}] Error parseando 'data': {items_raw[:200]}")
                return []
        else:
            items_data = items_raw

        if isinstance(items_data, dict):
            # Si match es 0, los items devueltos son sugerencias no relacionadas
            match_value = items_data.get("match")
            if match_value == 0 or match_value == "0":
                print(f"[{self.store_name}] Búsqueda sin resultados reales (sugerencias ignoradas)")
                return []
                
            return items_data.get("items", [])

        return []

    def _item_to_product(self, item: dict) -> Product | None:
        """
        Convierte un item del JSON de la API en un Product.

        Campos relevantes del item:
            - item_desc: nombre del producto
            - prli_price_original: precio numérico (float)
            - item_id: ID del producto
            - item_desc4link: slug para la URL
            - item_code4web: código web para la URL

        Args:
            item: dict con los datos crudos del producto.

        Returns:
            Product con nombre, precio (entero) y URL.
        """
        name = item.get("item_desc")
        if not name:
            return None

        # Precio: usar el valor numérico original (float → int)
        price_original = item.get("prli_price_original", 0)
        try:
            price = int(float(price_original))
        except (ValueError, TypeError):
            # Si el precio original falla, intentar parsear el formateado
            price_str = str(item.get("prli_price", "0"))
            price = int(re.sub(r"[^\d]", "", price_str) or "0")

        # URL del producto
        item_id = item.get("item_id", "")
        desc4link = item.get("item_desc4link", "")
        code4web = item.get("item_code4web", "")

        url = self.PRODUCT_URL_TEMPLATE.format(
            item_desc4link=desc4link,
            item_id=item_id,
            item_code4web=code4web,
        )

        return Product(name=str(name), price=price, url=url)

    # ------------------------------------------------------------------ #
    #  Métodos requeridos por BaseScraper (no utilizados)
    # ------------------------------------------------------------------ #

    def parse_products(self, html: str, query: str) -> list[Product]:
        """No utilizado — Maximus usa el flujo directo via API JSON."""
        return []

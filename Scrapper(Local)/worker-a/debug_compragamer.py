"""
Script de debug para inspeccionar qué ve Playwright al cargar CompraGamer.
Guarda el HTML renderizado y muestra todas las respuestas HTTP interceptadas.
"""

import sys
import os
from playwright.sync_api import sync_playwright

URL = "https://compragamer.com/productos?criterio=disco+duro"
if len(sys.argv) > 1:
    query = "+".join(sys.argv[1:])
    URL = f"https://compragamer.com/productos?criterio={query}"

OUTPUT_HTML = os.path.join(os.path.dirname(__file__), "debug_output.html")
OUTPUT_SCREENSHOT = os.path.join(os.path.dirname(__file__), "debug_screenshot.png")

captured_responses = []


def on_response(response):
    url = response.url
    status = response.status
    content_type = response.headers.get("content-type", "")
    captured_responses.append({
        "url": url,
        "status": status,
        "content_type": content_type,
    })

    # Mostrar todas las respuestas JSON
    if "json" in content_type:
        try:
            body = response.json()
            size = len(str(body))
            print(f"  📦 JSON [{status}] ({size} chars): {url}")
            # Si es una lista, mostrar cuántos items tiene
            if isinstance(body, list):
                print(f"     → Lista con {len(body)} items")
                if body and isinstance(body[0], dict):
                    print(f"     → Keys del primer item: {list(body[0].keys())[:10]}")
            elif isinstance(body, dict):
                print(f"     → Keys: {list(body.keys())[:10]}")
                # Buscar listas dentro del dict
                for k, v in body.items():
                    if isinstance(v, list) and len(v) > 0:
                        print(f"     → '{k}' contiene lista de {len(v)} items")
                        if isinstance(v[0], dict):
                            print(f"       Keys: {list(v[0].keys())[:10]}")
        except Exception as e:
            print(f"  📦 JSON [{status}] (error leyendo: {e}): {url}")


def main():
    print(f"🔍 Navegando a: {URL}")
    print(f"{'='*70}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
        )
        page = context.new_page()
        page.on("response", on_response)

        print("\n📡 Respuestas HTTP interceptadas:\n")

        # Navegar y esperar
        page.goto(URL, wait_until="networkidle", timeout=30000)

        # Esperar más por si Angular sigue cargando
        print("\n⏳ Esperando 5s adicionales...")
        page.wait_for_timeout(5000)

        # Scroll
        for i in range(3):
            page.mouse.wheel(0, 1000)
            page.wait_for_timeout(1000)

        # Capturar screenshot
        page.screenshot(path=OUTPUT_SCREENSHOT, full_page=True)
        print(f"\n📸 Screenshot guardado en: {OUTPUT_SCREENSHOT}")

        # Guardar HTML
        html = page.content()
        with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"📄 HTML guardado en: {OUTPUT_HTML} ({len(html)} chars)")

        # Estadísticas de respuestas
        print(f"\n{'='*70}")
        print(f"📊 Total respuestas interceptadas: {len(captured_responses)}")

        json_responses = [r for r in captured_responses if "json" in r["content_type"]]
        print(f"   De las cuales JSON: {len(json_responses)}")

        # Buscar elementos de producto en el HTML
        print(f"\n{'='*70}")
        print("🔎 Buscando patrones de productos en el HTML renderizado:\n")

        patterns = [
            ("a[href*='/producto/']", "Links a /producto/"),
            (".product-card", "class product-card"),
            ("mat-card", "mat-card (Angular Material)"),
            ("[class*='product']", "Cualquier class con 'product'"),
            ("[class*='producto']", "Cualquier class con 'producto'"),
            ("[class*='card']", "Cualquier class con 'card'"),
            ("[class*='item']", "Cualquier class con 'item'"),
            ("[class*='precio']", "Cualquier class con 'precio'"),
            ("[class*='price']", "Cualquier class con 'price'"),
            ("[class*='nombre']", "Cualquier class con 'nombre'"),
            ("[class*='name']", "Cualquier class con 'name'"),
            ("img[src*='imagenes.compragamer']", "Imágenes de productos"),
        ]

        for selector, desc in patterns:
            try:
                elements = page.query_selector_all(selector)
                count = len(elements)
                if count > 0:
                    print(f"  ✅ {desc}: {count} elementos")
                    # Mostrar el primero
                    first = elements[0]
                    tag = first.evaluate("el => el.tagName")
                    classes = first.evaluate("el => el.className")
                    text = first.inner_text()[:100] if first.inner_text() else ""
                    print(f"     Primero: <{tag} class='{classes}'>")
                    print(f"     Texto: {text}")
                    if count > 1 and count <= 5:
                        for i, el in enumerate(elements[1:], 2):
                            t = el.inner_text()[:80] if el.inner_text() else ""
                            print(f"     #{i}: {t}")
                else:
                    print(f"  ❌ {desc}: 0 elementos")
            except Exception as e:
                print(f"  ⚠  {desc}: Error - {e}")

        # Intentar ver la estructura del DOM principal
        print(f"\n{'='*70}")
        print("🏗  Estructura del DOM (hijos de <body>):\n")
        try:
            body_children = page.evaluate("""() => {
                const body = document.body;
                return Array.from(body.children).map(el => ({
                    tag: el.tagName,
                    id: el.id,
                    class: el.className.substring(0, 80),
                    childCount: el.children.length,
                    textLength: el.innerText ? el.innerText.length : 0,
                }));
            }""")
            for child in body_children:
                print(f"  <{child['tag']} id='{child['id']}' "
                      f"class='{child['class']}'> "
                      f"children={child['childCount']} "
                      f"textLen={child['textLength']}")
        except Exception as e:
            print(f"  Error: {e}")

        # Deep dive: buscar todos los elementos con texto largo (posibles productos)
        print(f"\n{'='*70}")
        print("🔬 Elementos con texto que contiene '$' (posibles precios):\n")
        try:
            price_elements = page.evaluate("""() => {
                const walker = document.createTreeWalker(
                    document.body,
                    NodeFilter.SHOW_TEXT,
                    null
                );
                const results = [];
                let node;
                while (node = walker.nextNode()) {
                    const text = node.textContent.trim();
                    if (text.includes('$') && text.length < 50) {
                        const parent = node.parentElement;
                        results.push({
                            text: text,
                            parentTag: parent ? parent.tagName : 'none',
                            parentClass: parent ? parent.className.substring(0, 60) : '',
                            parentId: parent ? parent.id : '',
                        });
                    }
                }
                return results.slice(0, 20);
            }""")
            if price_elements:
                for el in price_elements:
                    print(f"  '{el['text']}' → <{el['parentTag']} "
                          f"class='{el['parentClass']}'>")
            else:
                print("  Ningún elemento con '$' encontrado en el texto.")
        except Exception as e:
            print(f"  Error: {e}")

        browser.close()

    print(f"\n{'='*70}")
    print("✅ Debug completo. Revisá debug_output.html y debug_screenshot.png")


if __name__ == "__main__":
    main()

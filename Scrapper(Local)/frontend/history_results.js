const API_URL = "http://localhost:8080/api/search";
const resultsGrid = document.getElementById("resultsGrid");
const loadingIndicator = document.getElementById("loadingIndicator");
const queryDisplay = document.getElementById("queryDisplay");

// Helper para parsear la URL
const urlParams = new URLSearchParams(window.location.search);
const searchId = urlParams.get('id');
const query = urlParams.get('query') || "Búsqueda desconocida";

// Formateador de moneda
const currencyFormatter = new Intl.NumberFormat('es-AR', {
    style: 'currency',
    currency: 'ARS',
    maximumFractionDigits: 0
});

// Reutilizar la función de tiempo relativo
function getTimeAgo(dateString) {
    if (!dateString) return null;
    let dateStr = dateString;
    if (!dateStr.endsWith("Z")) {
        dateStr += "Z";
    }
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return "hace menos de un minuto";
    if (diffMins < 60) return `hace ${diffMins} minutos`;
    
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `hace ${diffHours} horas`;
    
    const diffDays = Math.floor(diffHours / 24);
    return `hace ${diffDays} días`;
}

function createProductCard(product) {
    const timeText = product.scrapedAt ? getTimeAgo(product.scrapedAt) : "Desconocido";
    
    return `
        <div class="card">
            <h3 title="${product.name}">${product.name}</h3>
            <div style="font-size: 0.75rem; color: #94a3b8; margin-bottom: 1rem;">${timeText}</div>
            <div class="card-footer">
                <span class="price">${currencyFormatter.format(product.price)}</span>
                <a href="${product.url}" class="btn-link" target="_blank">Ver Oferta</a>
            </div>
        </div>
    `;
}

function createStoreColumn(storeName, products) {
    const col = document.createElement("div");
    col.className = "store-column";
    
    const storeTitle = storeName.charAt(0).toUpperCase() + storeName.slice(1);
    
    col.innerHTML = `
        <h2>${storeTitle} <span class="result-count">${products.length}</span></h2>
        <div class="results-list">
            ${products.length === 0 
                ? '<div class="no-results">No se encontraron resultados en esta tienda.</div>'
                : products.map(p => createProductCard(p)).join('')}
        </div>
    `;
    
    return col;
}

async function fetchResults() {
    if (!searchId) {
        loadingIndicator.innerHTML = "ID de búsqueda no proporcionado.";
        return;
    }
    
    queryDisplay.textContent = query;
    
    try {
        const response = await fetch(`${API_URL}/${searchId}/results`);
        if (!response.ok) throw new Error("Error al obtener los resultados");
        
        const groupedResults = await response.json();
        
        loadingIndicator.classList.add("hidden");
        resultsGrid.classList.remove("hidden");
        
        if (Object.keys(groupedResults).length === 0) {
            resultsGrid.innerHTML = `
                <div style="grid-column: 1 / -1;" class="empty-history">
                    No se guardaron productos para esta búsqueda.
                </div>
            `;
            return;
        }
        
        resultsGrid.innerHTML = "";
        
        for (const [store, products] of Object.entries(groupedResults)) {
            const column = createStoreColumn(store, products);
            resultsGrid.appendChild(column);
        }
        
    } catch (error) {
        console.error("Error:", error);
        loadingIndicator.innerHTML = "Error al cargar los resultados. Intenta nuevamente.";
    }
}

// Inicializar
document.addEventListener("DOMContentLoaded", fetchResults);

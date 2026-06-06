const API_URL = "/api/search";
const resultsGrid = document.getElementById("resultsGrid");
const loadingIndicator = document.getElementById("loadingIndicator");
const queryDisplay = document.getElementById("queryDisplay");

// Filter elements
const filtersSection = document.getElementById("filtersSection");
const filterText = document.getElementById("filterText");
const filterPriceMin = document.getElementById("filterPriceMin");
const filterPriceMax = document.getElementById("filterPriceMax");
const filterSort = document.getElementById("filterSort");
const clearFiltersBtn = document.getElementById("clearFiltersBtn");
const totalResultsCount = document.getElementById("totalResultsCount");


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

// In-memory data store for filtering
let allProducts = [];
let activeStores = [];

// --- Debounce utility ---
function debounce(fn, delay) {
    let timer;
    return function (...args) {
        clearTimeout(timer);
        timer = setTimeout(() => fn.apply(this, args), delay);
    };
}


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

function renderResults(groupedResults) {
    resultsGrid.innerHTML = "";

    let totalVisible = 0;
    const textFilter = filterText.value.trim().toLowerCase();
    const priceMin = filterPriceMin.value !== "" ? parseInt(filterPriceMin.value) : null;
    const priceMax = filterPriceMax.value !== "" ? parseInt(filterPriceMax.value) : null;
    const sortMode = filterSort.value;

    for (const store of activeStores) {
        let products = groupedResults[store] || [];

        // Filter
        let filtered = products.filter(p => {
            if (textFilter && !p.name.toLowerCase().includes(textFilter)) return false;
            if (priceMin !== null && p.price < priceMin) return false;
            if (priceMax !== null && p.price > priceMax) return false;
            return true;
        });

        // Sort
        if (sortMode === "price-asc") {
            filtered.sort((a, b) => a.price - b.price);
        } else if (sortMode === "price-desc") {
            filtered.sort((a, b) => b.price - a.price);
        } else if (sortMode === "name-asc") {
            filtered.sort((a, b) => a.name.localeCompare(b.name, 'es'));
        } else if (sortMode === "name-desc") {
            filtered.sort((a, b) => b.name.localeCompare(a.name, 'es'));
        }

        const col = document.createElement("div");
        col.className = "store-column";

        const storeTitle = store.charAt(0).toUpperCase() + store.slice(1);

        col.innerHTML = `
            <div class="store-header">
                ${storeTitle}
                <span class="count">${filtered.length}</span>
            </div>
            <div class="store-items">
                ${filtered.length === 0
                    ? '<div class="store-empty-filter">Sin resultados con estos filtros</div>'
                    : filtered.map(p => createProductCard(p)).join('')}
            </div>

        `;

        resultsGrid.appendChild(col);
        totalVisible += filtered.length;
    }

    // Update grid columns
    resultsGrid.style.gridTemplateColumns = `repeat(${activeStores.length}, 1fr)`;

    // Update total counter
    totalResultsCount.textContent = totalVisible;
}

// --- Filter Logic ---
function applyFilters() {
    // Re-group from allProducts
    const groupedResults = {};
    allProducts.forEach(p => {
        if (!groupedResults[p.store]) groupedResults[p.store] = [];
        groupedResults[p.store].push(p);
    });
    renderResults(groupedResults);
}

function clearFilters() {
    filterText.value = "";
    filterPriceMin.value = "";
    filterPriceMax.value = "";
    filterSort.value = "default";
    applyFilters();
}

// Attach filter listeners
const debouncedApply = debounce(applyFilters, 250);
filterText.addEventListener("input", debouncedApply);
filterPriceMin.addEventListener("input", debouncedApply);
filterPriceMax.addEventListener("input", debouncedApply);
filterSort.addEventListener("change", applyFilters);
clearFiltersBtn.addEventListener("click", clearFilters);

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
        
        // Store all products in memory
        activeStores = Object.keys(groupedResults);
        allProducts = [];
        for (const [store, products] of Object.entries(groupedResults)) {
            products.forEach(p => {
                allProducts.push({ ...p, store });
            });
        }

        // Show filters and render
        filtersSection.classList.remove("hidden");
        totalResultsCount.textContent = allProducts.length;
        renderResults(groupedResults);
        
    } catch (error) {
        console.error("Error:", error);
        loadingIndicator.innerHTML = "Error al cargar los resultados. Intenta nuevamente.";
    }
}

// Inicializar
document.addEventListener("DOMContentLoaded", fetchResults);

const form = document.getElementById("searchForm");
const queryInput = document.getElementById("queryInput");
const submitBtnSpan = document.querySelector("#submitBtn span");
const searchLoader = document.getElementById("searchLoader");
const statusBadge = document.getElementById("statusBadge");
const statusText = document.getElementById("status");
const cachedBadge = document.getElementById("cachedBadge");
const cachedText = document.getElementById("cachedText");
const resultsGrid = document.getElementById("resultsGrid");
const forceUpdateBtn = document.getElementById("forceUpdateBtn");

const MAX_SCRAPERS = 3;
let stompClient = null;
let shownResults = new Set();
let activeStores = new Set();

// Filter elements
const filtersSection = document.getElementById("filtersSection");
const filterText = document.getElementById("filterText");
const filterPriceMin = document.getElementById("filterPriceMin");
const filterPriceMax = document.getElementById("filterPriceMax");
const filterSort = document.getElementById("filterSort");
const clearFiltersBtn = document.getElementById("clearFiltersBtn");
const totalResultsCount = document.getElementById("totalResultsCount");

// --- In-memory data store for filtering ---
// Each entry: { store, name, price, url, uniqueKey }
let allProducts = [];

// --- Checkbox Logic ---
const checkboxes = document.querySelectorAll('input[name="scraper"]');

function updateCheckboxStates() {
    const checkedCount = document.querySelectorAll('input[name="scraper"]:checked').length;
    checkboxes.forEach(cb => {
        if (!cb.checked) {
            cb.disabled = checkedCount >= MAX_SCRAPERS;
        }
    });
}

checkboxes.forEach(cb => {
    cb.addEventListener('change', updateCheckboxStates);
});
// Initialize states on load
updateCheckboxStates();


// --- Format Price ---
function formatPrice(price) {
    return new Intl.NumberFormat('es-AR', {
        style: 'currency',
        currency: 'ARS',
        minimumFractionDigits: 0
    }).format(price);
}

// --- Debounce utility ---
function debounce(fn, delay) {
    let timer;
    return function (...args) {
        clearTimeout(timer);
        timer = setTimeout(() => fn.apply(this, args), delay);
    };
}

// --- Filter Logic ---
function applyFilters() {
    const textFilter = filterText.value.trim().toLowerCase();
    const priceMin = filterPriceMin.value !== "" ? parseInt(filterPriceMin.value) : null;
    const priceMax = filterPriceMax.value !== "" ? parseInt(filterPriceMax.value) : null;
    const sortMode = filterSort.value;

    // Group products by store
    const storeMap = {};
    allProducts.forEach(p => {
        if (!storeMap[p.store]) storeMap[p.store] = [];
        storeMap[p.store].push(p);
    });

    let totalVisible = 0;

    // Apply filters to each store
    for (const store of activeStores) {
        const products = storeMap[store] || [];

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

        // Re-render the store column items
        const itemsContainer = document.getElementById(`items-${store}`);
        if (!itemsContainer) continue;

        itemsContainer.innerHTML = "";

        if (filtered.length === 0) {
            const emptyMsg = document.createElement("div");
            emptyMsg.className = "store-empty-filter";
            emptyMsg.textContent = "Sin resultados con estos filtros";
            itemsContainer.appendChild(emptyMsg);
        } else {
            filtered.forEach(producto => {
                const card = document.createElement("div");
                card.className = "card";
                card.innerHTML = `
                    <h3>${producto.name}</h3>
                    <div class="card-footer">
                        <span class="price">${formatPrice(producto.price)}</span>
                        <a href="${producto.url}" class="btn-link" target="_blank">Ver Oferta</a>
                    </div>
                `;
                itemsContainer.appendChild(card);
            });
        }

        totalVisible += filtered.length;

        // Update store count
        const countElement = document.getElementById(`count-${store}`);
        if (countElement) {
            countElement.textContent = filtered.length;
        }
    }

    // Update total counter
    totalResultsCount.textContent = totalVisible;
}

function clearFilters() {
    filterText.value = "";
    filterPriceMin.value = "";
    filterPriceMax.value = "";
    filterSort.value = "default";
    applyFilters();
}

// Attach filter listeners with debounce
const debouncedApply = debounce(applyFilters, 250);
filterText.addEventListener("input", debouncedApply);
filterPriceMin.addEventListener("input", debouncedApply);
filterPriceMax.addEventListener("input", debouncedApply);
filterSort.addEventListener("change", applyFilters);
clearFiltersBtn.addEventListener("click", clearFilters);

// --- DOM Manipulation for Columns ---
function getOrCreateStoreColumn(storeName) {
    let col = document.getElementById(`col-${storeName}`);
    if (!col) {
        col = document.createElement("div");
        col.id = `col-${storeName}`;
        col.className = "store-column";
        
        const cleanStoreName = storeName.replace("-", " ");
        
        col.innerHTML = `
            <div class="store-header">
                ${cleanStoreName}
                <span class="count" id="count-${storeName}">0</span>
            </div>
            <div class="store-items" id="items-${storeName}"></div>
        `;
        
        resultsGrid.appendChild(col);
        activeStores.add(storeName);
        
        // Update Grid Layout dynamically based on column count
        resultsGrid.style.gridTemplateColumns = `repeat(${activeStores.size}, 1fr)`;
    }
    return document.getElementById(`items-${storeName}`);
}

function updateStoreCount(storeName) {
    const itemsContainer = document.getElementById(`items-${storeName}`);
    const countElement = document.getElementById(`count-${storeName}`);
    if (itemsContainer && countElement) {
        countElement.textContent = itemsContainer.children.length;
    }
}
function generateSearchId() {
    if (window.crypto && typeof window.crypto.randomUUID === "function") {
        return window.crypto.randomUUID();
    }

    return "search-" + Date.now() + "-" + Math.random().toString(36).substring(2, 15);
}


function triggerSearch(forceUpdate = false) {
    const query = queryInput.value.trim();
    if (query === "") {
        alert("Por favor, ingresa un término de búsqueda.");
        return;
    }

    const selectedScrapers = Array.from(document.querySelectorAll('input[name="scraper"]:checked')).map(cb => cb.value);
    
    if (selectedScrapers.length === 0) {
        alert("Debes seleccionar al menos una tienda para buscar.");
        return;
    }

    resultsGrid.innerHTML = "";
    shownResults.clear();
    activeStores.clear();
    allProducts = [];
    cachedBadge.classList.add("hidden");
    filtersSection.classList.add("hidden");
    clearFilters();
    submitBtnSpan.textContent = "Conectando...";
    searchLoader.classList.remove("hidden");
    statusBadge.classList.remove("hidden");
    statusText.textContent = "Estableciendo conexión segura...";

    const searchId = generateSearchId();
    connectWebSocket(searchId, query, selectedScrapers, forceUpdate);
}

form.addEventListener("submit", async function (event) {
    event.preventDefault();
    triggerSearch(false);
});

forceUpdateBtn.addEventListener("click", function () {
    triggerSearch(true);
});

function connectWebSocket(searchId, query, selectedScrapers, forceUpdate) {
    if (stompClient !== null) {
        stompClient.deactivate();
    }

    const wsProtocol = window.location.protocol === "https:" ? "wss" : "ws";
    const wsUrl = `${wsProtocol}://${window.location.host}/ws`;

    stompClient = new StompJs.Client({
        brokerURL: wsUrl,

        onConnect: function () {
            statusText.textContent = "Buscando mejores precios...";
            submitBtnSpan.textContent = "Buscando...";

            stompClient.subscribe(`/topic/search/${searchId}`, function (message) {
                const resultMessage = JSON.parse(message.body);
                showResultMessage(resultMessage);
            });

            // Darle tiempo al broker STOMP para confirmar la suscripción (500ms)
            setTimeout(() => {
                console.log(`[DEBUG] Enviando POST /api/search para query: '${query}', forceUpdate: ${forceUpdate}`);
                fetch("/api/search", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({ 
                        query: query, 
                        searchId: searchId,
                        stores: selectedScrapers,
                        forceUpdate: forceUpdate
                    })
                }).then(response => {
                    console.log(`[DEBUG] API HTTP Response status: ${response.status}`);
                }).catch(error => {
                    console.error("[DEBUG] Error en POST /api/search:", error);
                    statusText.textContent = "Servicio no disponible";
                    resetBtn();
                });
            }, 500);
        },

        onWebSocketError: function (error) {
            statusText.textContent = "Error de conexión WebSocket";
            resetBtn();
        },

        onStompError: function (frame) {
            statusText.textContent = "Error de STOMP";
            resetBtn();
        }
    });

    stompClient.activate();
}

function getTimeAgo(dateString) {
    if (!dateString) return null;
    
    console.log(`[DEBUG] getTimeAgo: Received dateString = ${dateString}`);
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    
    console.log(`[DEBUG] getTimeAgo: date = ${date.toISOString()}, now = ${now.toISOString()}, diffMs = ${diffMs}, diffMins = ${diffMins}`);
    
    if (diffMins < 1) return "hace menos de un minuto";
    if (diffMins < 60) return `hace ${diffMins} minutos`;
    
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `hace ${diffHours} horas`;
    
    const diffDays = Math.floor(diffHours / 24);
    return `hace ${diffDays} días`;
}

function showResultMessage(resultMessage) {
    console.log("[DEBUG] showResultMessage: resultMessage received", resultMessage);
    
    if (!resultMessage.results || resultMessage.results.length === 0) {
        return;
    }

    if (resultMessage.cachedAt) {
        console.log(`[DEBUG] showResultMessage: cachedAt is present = ${resultMessage.cachedAt}`);
        cachedBadge.classList.remove("hidden");
        cachedText.textContent = `Resultados en caché (${getTimeAgo(resultMessage.cachedAt)})`;
    } else {
        console.log("[DEBUG] showResultMessage: cachedAt is NOT present.");
    }

    const store = resultMessage.store;
    const itemsContainer = getOrCreateStoreColumn(store);

    resultMessage.results.forEach(producto => {
        const uniqueKey = `${resultMessage.searchId}-${store}-${producto.name}-${producto.price}`;

        if (shownResults.has(uniqueKey)) {
            return;
        }

        shownResults.add(uniqueKey);

        // Store product data in memory for filtering
        allProducts.push({
            store: store,
            name: producto.name,
            price: producto.price,
            url: producto.url,
            uniqueKey: uniqueKey
        });

        const card = document.createElement("div");
        card.className = "card";

        card.innerHTML = `
            <h3>${producto.name}</h3>
            <div class="card-footer">
                <span class="price">${formatPrice(producto.price)}</span>
                <a href="${producto.url}" class="btn-link" target="_blank">Ver Oferta</a>
            </div>
        `;

        itemsContainer.appendChild(card);
    });

    updateStoreCount(store);
    
    // Show filters panel and update total count
    if (allProducts.length > 0) {
        filtersSection.classList.remove("hidden");
        totalResultsCount.textContent = allProducts.length;
    }

    // Once results start flowing, we can reset the search button text
    if (submitBtnSpan.textContent === "Buscando...") {
        statusText.textContent = "Recibiendo resultados...";
        setTimeout(() => {
            resetBtn();
            statusBadge.classList.add("hidden");
        }, 3000); // Hide status after 3 seconds of receiving first result
    }
}

function resetBtn() {
    submitBtnSpan.textContent = "Buscar Precios";
    searchLoader.classList.add("hidden");
}
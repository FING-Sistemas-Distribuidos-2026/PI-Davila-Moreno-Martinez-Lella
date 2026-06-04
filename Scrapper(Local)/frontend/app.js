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
    cachedBadge.classList.add("hidden");
    submitBtnSpan.textContent = "Conectando...";
    searchLoader.classList.remove("hidden");
    statusBadge.classList.remove("hidden");
    statusText.textContent = "Estableciendo conexión segura...";

    const searchId = crypto.randomUUID();
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

    stompClient = new StompJs.Client({
        brokerURL: "ws://localhost:8080/ws",

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
                fetch("http://localhost:8080/api/search", {
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
                    statusText.textContent = "Error conectando con la API";
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
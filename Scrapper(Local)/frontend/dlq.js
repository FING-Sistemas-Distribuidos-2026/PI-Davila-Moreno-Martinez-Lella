const API_URL = "/api/dlq";
const dlqList = document.getElementById("dlqList");
const loadingIndicator = document.getElementById("loadingIndicator");

let stompClient = null;

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
    
    if (diffMins < 1) return "hace unos segundos";
    if (diffMins < 60) return `hace ${diffMins} minutos`;
    
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `hace ${diffHours} horas`;
    
    const diffDays = Math.floor(diffHours / 24);
    return `hace ${diffDays} días`;
}

function formatDate(dateString) {
    let dateStr = dateString;
    if (!dateStr.endsWith("Z")) {
        dateStr += "Z";
    }
    const date = new Date(dateStr);
    return date.toLocaleString('es-AR', { 
        day: '2-digit', 
        month: '2-digit', 
        year: 'numeric',
        hour: '2-digit', 
        minute: '2-digit',
        second: '2-digit'
    });
}

function createDlqCard(message, isNew = false) {
    const card = document.createElement("div");
    card.className = "dlq-card" + (isNew ? " new-item" : "");
    
    const timeAgo = getTimeAgo(message.failedAt);
    const absoluteDate = formatDate(message.failedAt);
    const storeName = message.store.charAt(0).toUpperCase() + message.store.slice(1);
    
    card.innerHTML = `
        <div class="dlq-info">
            <div class="dlq-query">${message.query}</div>
            <div class="dlq-store">
                <svg xmlns="http://www.w3.org/2000/svg" style="display:inline; width:16px; height:16px; vertical-align:-3px; margin-right:4px;" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
                ${storeName}
            </div>
            <div class="dlq-meta">
                <span title="${absoluteDate}">
                    <svg xmlns="http://www.w3.org/2000/svg" style="display:inline; width:14px; height:14px; vertical-align:-2px; margin-right:4px;" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    ${timeAgo}
                </span>
                <span>
                    <svg xmlns="http://www.w3.org/2000/svg" style="display:inline; width:14px; height:14px; vertical-align:-2px; margin-right:4px;" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    ${message.attempts} intentos
                </span>
            </div>
        </div>
        <div class="dlq-status">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            Falló
        </div>
    `;
    
    return card;
}

function checkEmpty() {
    if (dlqList.children.length === 0 || (dlqList.children.length === 1 && dlqList.children[0].classList.contains('empty-dlq'))) {
        dlqList.innerHTML = `
            <div class="empty-dlq">
                <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" fill="none" viewBox="0 0 24 24" stroke="currentColor" style="margin: 0 auto 1rem auto; display: block; opacity: 0.5;">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                No hay búsquedas fallidas registradas.<br>El sistema está funcionando correctamente.
            </div>
        `;
    }
}

async function fetchInitialData() {
    try {
        const response = await fetch(API_URL);
        if (!response.ok) throw new Error("Error al obtener datos");
        
        const data = await response.json();
        
        loadingIndicator.classList.add("hidden");
        dlqList.classList.remove("hidden");
        
        dlqList.innerHTML = ""; // Limpiar antes de insertar
        
        if (data.length === 0) {
            checkEmpty();
            return;
        }
        
        data.forEach(msg => {
            const card = createDlqCard(msg);
            dlqList.appendChild(card);
        });
        
    } catch (error) {
        console.error("Error:", error);
        loadingIndicator.innerHTML = "Error al cargar los datos. Intenta nuevamente.";
    }
}

function connectWebSocket() {
    const wsProtocol = window.location.protocol === "https:" ? "wss" : "ws";
    const wsUrl = `${wsProtocol}://${window.location.host}/ws`;

    stompClient = new StompJs.Client({
        brokerURL: wsUrl,
        onConnect: function () {
            console.log("Conectado a WebSocket para DLQ");
            stompClient.subscribe(`/topic/dlq`, function (message) {
                const dlqMessage = JSON.parse(message.body);
                
                // Si estaba vacío, limpiar el mensaje de vacío
                const emptyMsg = dlqList.querySelector('.empty-dlq');
                if (emptyMsg) {
                    dlqList.innerHTML = "";
                }
                
                // Crear y animar la nueva tarjeta
                const card = createDlqCard(dlqMessage, true);
                dlqList.insertBefore(card, dlqList.firstChild);
            });
        },
        onStompError: function (frame) {
            console.error('Broker reported error: ' + frame.headers['message']);
            console.error('Additional details: ' + frame.body);
        }
    });

    stompClient.activate();
}

// Inicializar
document.addEventListener("DOMContentLoaded", () => {
    fetchInitialData();
    connectWebSocket();
});

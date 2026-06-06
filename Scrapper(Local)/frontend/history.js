const API_URL = "http://localhost:8080/api/search";
const historyList = document.getElementById("historyList");
const loadingIndicator = document.getElementById("loadingIndicator");

// Reutilizar la función de tiempo relativo
function getTimeAgo(dateString) {
    if (!dateString) return null;
    
    // El backend debe devolver las fechas con Z para UTC. Si no, forzamos UTC asumiendo que el backend envía UTC.
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

// Formatear fecha absoluta
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
        minute: '2-digit'
    });
}

async function fetchHistory() {
    try {
        const response = await fetch(`${API_URL}/history`);
        if (!response.ok) throw new Error("Error al obtener el historial");
        
        const history = await response.json();
        
        loadingIndicator.classList.add("hidden");
        historyList.classList.remove("hidden");
        
        if (history.length === 0) {
            historyList.innerHTML = `
                <div class="empty-history">
                    No hay búsquedas recientes.
                </div>
            `;
            return;
        }
        
        historyList.innerHTML = "";
        
        history.forEach(search => {
            const card = document.createElement("a");
            card.className = "history-card";
            card.href = `history_results.html?id=${search.id}&query=${encodeURIComponent(search.query)}`;
            
            const timeAgo = getTimeAgo(search.createdAt);
            const absoluteDate = formatDate(search.createdAt);
            const statusClass = search.status === "PROCESSING" ? "PROCESSING" : "";
            const statusText = search.status === "COMPLETED" ? "Completado" : "Procesando";
            
            card.innerHTML = `
                <div class="history-info">
                    <div class="history-query">${search.query}</div>
                    <div class="history-meta">
                        <span title="${absoluteDate}">
                            <svg xmlns="http://www.w3.org/2000/svg" style="display:inline; width:14px; height:14px; vertical-align:-2px; margin-right:4px;" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            ${timeAgo}
                        </span>
                    </div>
                </div>
                <div class="history-status ${statusClass}">${statusText}</div>
            `;
            
            historyList.appendChild(card);
        });
        
    } catch (error) {
        console.error("Error:", error);
        loadingIndicator.innerHTML = "Error al cargar el historial. Intenta nuevamente.";
    }
}

// Inicializar
document.addEventListener("DOMContentLoaded", fetchHistory);

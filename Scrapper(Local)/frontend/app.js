const form = document.getElementById("searchForm");
const queryInput = document.getElementById("queryInput");
const statusText = document.getElementById("status");
const resultsDiv = document.getElementById("results");

let stompClient = null;
let pollingInterval = null;
let shownResults = new Set();

form.addEventListener("submit", async function (event) {
    event.preventDefault();

    const query = queryInput.value.trim();

    if (query === "") {
        alert("Ingresá una búsqueda");
        return;
    }

    statusText.textContent = "Enviando búsqueda...";
    resultsDiv.innerHTML = "";
    shownResults.clear();

    try {
        const response = await fetch("http://localhost:8080/api/search", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ query: query })
        });

        if (!response.ok) {
            throw new Error("Error creando la búsqueda");
        }

        const data = await response.json();

        const searchId = data.searchId;

        statusText.textContent = "Búsqueda creada. Esperando resultados... ID: " + searchId;

        connectWebSocket(searchId);
        startPollingResults(searchId);

    } catch (error) {   
        statusText.textContent = "Error conectando con la API";
        console.error(error);
    }
});

function connectWebSocket(searchId) {
    if (stompClient !== null) {
        stompClient.deactivate();
    }

    stompClient = new StompJs.Client({
        brokerURL: "ws://localhost:8080/ws",

        onConnect: function () {
            console.log("WebSocket conectado");

            statusText.textContent = "WebSocket conectado. Esperando resultados...";

            stompClient.subscribe(`/topic/search/${searchId}`, function (message) {
                const resultMessage = JSON.parse(message.body);

                console.log("Resultado recibido por WebSocket:", resultMessage);

                showResultMessage(resultMessage);
            });
        },

        onWebSocketError: function (error) {
            console.error("Error WebSocket:", error);
            statusText.textContent = "Error en WebSocket";
        },

        onStompError: function (frame) {
            console.error("Error STOMP:", frame);
            statusText.textContent = "Error STOMP";
        }
    });

    stompClient.activate();
}

function showResultMessage(resultMessage) {
    if (!resultMessage.results || resultMessage.results.length === 0) {
        return;
    }

    resultMessage.results.forEach(producto => {
        const result = {
            searchId: resultMessage.searchId,
            store: resultMessage.store,
            name: producto.name,
            price: producto.price,
            url: producto.url
        };

        showResultIfNew(result);
    });
}

function startPollingResults(searchId) {
    if (pollingInterval !== null) {
        clearInterval(pollingInterval);
    }

    pollingInterval = setInterval(async () => {
        try {
            const response = await fetch(`http://localhost:8080/api/search/${searchId}/results`);

            if (!response.ok) {
                console.error("Error consultando resultados guardados");
                return;
            }

            const results = await response.json();

            results.forEach(result => {
                showResultIfNew(result);
            });

        } catch (error) {
            console.error("Error en polling de resultados:", error);
        }
    }, 2000);
}


function showResultIfNew(result) {
    const uniqueKey = `${result.searchId}-${result.store}-${result.name}-${result.price}`;

    if (shownResults.has(uniqueKey)) {
        return;
    }

    shownResults.add(uniqueKey);

    const card = document.createElement("div");
    card.className = "card";

    card.innerHTML = `
        <h3>${result.name}</h3>
        <p>${result.store}</p>
        <p class="price">$${result.price}</p>
        <a href="${result.url}" target="_blank">Ver producto</a>
    `;

    resultsDiv.appendChild(card);
}
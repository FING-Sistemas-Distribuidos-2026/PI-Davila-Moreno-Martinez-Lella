Servicio	Puerto local	Descripción
Frontend	5500	       Interfaz web
Backend-API	8080	       API REST y WebSocket
RabbitMQ	5672	       Comunicación AMQP
RabbitMQ.M	15672	       Panel web de RabbitMQ
PostgreSQL	5432	       Base de datos


docker tag prueba-proyecto-sd-backend-api facul/scraper-backend-api:1.0
docker tag prueba-proyecto-sd-worker-a facul/scraper-worker-a:1.0
docker tag prueba-proyecto-sd-frontend facul/scraper-frontend:1.0

docker push facul/scraper-backend-api:1.0
docker push facul/scraper-worker-a:1.0
docker push facul/scraper-frontend:1.0

# Comparador Distribuido de Productos

Proyecto integrador para la materia Sistemas Distribuidos.

La aplicación permite realizar búsquedas de productos desde un frontend web. El backend recibe la consulta, genera trabajos de scraping y los envía a una cola de mensajes en RabbitMQ. Un worker consume esos trabajos, procesa la búsqueda y publica resultados en otra cola. El backend recibe los resultados, los guarda en PostgreSQL y los envía al frontend mediante WebSocket para mostrarlos automáticamente.

---

## Arquitectura general

Componentes
Frontend

Aplicación web simple con HTML, CSS y JavaScript.

Funciones principales:

Permite ingresar una consulta de búsqueda.
Envía la búsqueda al backend mediante HTTP.
Se conecta al backend mediante WebSocket.
Muestra resultados automáticamente sin recargar la página.
Consulta periódicamente resultados guardados como respaldo.
-----------------------

Backend API

Aplicación Java Spring Boot.

Responsabilidades:

Recibir búsquedas desde el frontend.
Generar un searchId.
Guardar la búsqueda en PostgreSQL.
Publicar trabajos en RabbitMQ.
Escuchar resultados desde RabbitMQ.
Guardar resultados en PostgreSQL.
Enviar resultados al frontend mediante WebSocket.
-----------------------

RabbitMQ

Message broker usado para desacoplar backend y worker.

Colas utilizadas:

scraping.jobs
scraping.results

scraping.jobs contiene los trabajos que deben procesar los workers.

scraping.results contiene los resultados producidos por los workers.
-----------------------

Worker

Servicio Python que consume mensajes desde RabbitMQ.

Responsabilidades:

Consumir trabajos desde scraping.jobs.
Simular procesamiento de búsqueda.
Generar resultados de productos.
Publicar resultados en scraping.results.
Confirmar mensajes procesados mediante ACK.
-----------------------

PostgreSQL

Base de datos relacional usada para persistir búsquedas y resultados.

Tablas principales:

searches
search_results

searches guarda las búsquedas realizadas.

search_results guarda los productos encontrados por cada búsqueda.
-----------------------
Flujo de una búsqueda
1. El usuario escribe una consulta en el frontend.
2. El frontend envía la consulta al backend mediante POST /api/search.
3. El backend crea un searchId y guarda la búsqueda en PostgreSQL.
4. El backend publica un mensaje por tienda en la cola scraping.jobs.
5. El worker consume mensajes desde scraping.jobs.
6. El worker procesa la búsqueda y genera resultados.
7. El worker publica los resultados en scraping.results.
8. El backend escucha scraping.results.
9. El backend guarda los resultados en PostgreSQL.
10. El backend envía los resultados al frontend mediante WebSocket.
11. El frontend muestra los resultados automáticamente.

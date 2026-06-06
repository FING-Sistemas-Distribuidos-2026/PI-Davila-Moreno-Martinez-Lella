# Walkthrough: Observabilidad de RabbitMQ

Hemos implementado la infraestructura de observabilidad para RabbitMQ utilizando Prometheus y Grafana (Apartado A).

> [!NOTE]
> Debido a que la ejecución de Docker en tu sistema requiere permisos de `sudo`, el entorno no pudo ser iniciado automáticamente. Deberás seguir los pasos a continuación.

## Cambios Realizados

1. **RabbitMQ**: Se creó un `Dockerfile` (`rabbitmq/Dockerfile`) para habilitar automáticamente el plugin `rabbitmq_prometheus` de forma offline.
2. **Prometheus**: Se agregó el servicio `prometheus` al `docker-compose.yml` y se configuró (`monitoring/prometheus/prometheus.yml`) para leer métricas del puerto `15692` de RabbitMQ.
3. **Grafana**: Se añadió `grafana` al `docker-compose.yml` e incluimos auto-aprovisionamiento (`monitoring/grafana/provisioning/datasources/datasource.yml`) para que Prometheus ya esté configurado como origen de datos.

## Cómo levantar el sistema

Abre una terminal en el directorio `Scrapper(Local)` y ejecuta el siguiente comando con `sudo`:

```bash
sudo docker compose up -d --build
```

## Cómo visualizar las métricas (Verificación)

Una vez que los contenedores estén corriendo, sigue estos pasos para tener tu Dashboard listo en 2 minutos:

1. **Verificar Prometheus**: Entra a `http://localhost:9090/targets`. Deberías ver el *target* de `rabbitmq` en estado **UP**.
2. **Entrar a Grafana**: Accede a `http://localhost:3000`.
   - **Usuario:** `admin`
   - **Contraseña:** `admin`
3. **Importar el Dashboard Oficial de RabbitMQ**:
   - En el menú lateral izquierdo, ve al ícono de **Dashboards** (cuatro cuadraditos) o presiona el botón "+" y elige **Import**.
   - Donde dice "Import via grafana.com", ingresa el ID: `10991` y dale al botón "Load".
   - En la siguiente pantalla, abajo del todo te pedirá seleccionar un origen de datos ("Prometheus"). Selecciona la opción que aparece desplegable (que creamos automáticamente) y dale a **Import**.

> [!TIP]
> Una vez importado, tendrás inmediatamente un panel interactivo mostrando: Mensajes publicados, entregados, encolados (por cola, ideal para tus `scraping.jobs` y `scraping.results`), consumo de memoria, y operaciones por segundo.

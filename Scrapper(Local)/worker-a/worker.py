import json
import pika
import time
import os

from scrapers.registry import ScraperRegistry
import scrapers.stores

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RETRY_QUEUE = os.getenv("RETRY_QUEUE", "scraping.jobs.retry")
QUEUE_NAME = os.getenv("QUEUE_NAME", "scraping.jobs")
RESULTS_QUEUE = os.getenv("RESULTS_QUEUE", "scraping.results")
DLQ_QUEUE = os.getenv("DLQ_QUEUE", "scraping.jobs.dlq")
MAX_ATTEMPTS = int(os.getenv("MAX_ATTEMPTS", "3"))


def process_message(message, channel):
    search_id = message["searchId"]
    query = message["query"]
    store = message["store"]

    print("====================================")
    print(f"Search ID: {search_id}")
    print(f"Query: {query}")
    print(f"Store: {store}")
    print("Procesando scraping real...")
    
    try:
        scraper = ScraperRegistry.get(store)
        results = scraper.search(query)
    except ValueError as e:
        print(f"Error de scraper: {e}")
        results = []
    except Exception as e:
        print(f"Error inesperado scrapeando {store}: {e}")
        results = []

    result_message = {
        "searchId": search_id,
        "store": store,
        "status": "COMPLETED",
        "results": results
    }
    publish_result(channel, result_message, RESULTS_QUEUE)
    print("Procesamiento finalizado")
    print("====================================")


def publish_result(channel, result_message,queue_name):
    """
    Publica el resultado del worker en la cola.
    """

    body = json.dumps(result_message)

    channel.basic_publish(
        exchange="",
        routing_key=queue_name,
        body=body,
        properties=pika.BasicProperties(
            delivery_mode=2,
            content_type="application/json"
        )
    )

    print(f"Resultado publicado en {queue_name}")


def callback(ch, method, properties, body):
    try:
        message = json.loads(body)
        process_message(message, ch)

        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        print(f"Error procesando mensaje: {e}")

        message = json.loads(body)
        attempts = message.get("attempts", 0)
       
        if attempts < MAX_ATTEMPTS:
            message["attempts"] = attempts + 1
            publish_result(ch, message, RETRY_QUEUE)
        else:
            publish_result(ch, message, DLQ_QUEUE)

        ch.basic_ack(delivery_tag=method.delivery_tag)

       
def connect_to_rabbitmq():
    while True:
        try:
            print(f"Intentando conectar a RabbitMQ en {RABBITMQ_HOST}...")

            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=RABBITMQ_HOST)
            )

            print("Conectado a RabbitMQ")
            return connection

        except pika.exceptions.AMQPConnectionError:
            print("RabbitMQ no está listo. Reintentando en 5 segundos...")
            time.sleep(5)

def main():
    connection = connect_to_rabbitmq()

    channel = connection.channel()

    channel.queue_declare(
        queue=QUEUE_NAME,
        durable=True
    )

    channel.queue_declare(
        queue=RESULTS_QUEUE,
        durable=True
    )

    channel.queue_declare(
        queue=DLQ_QUEUE,
        durable=True
    )

    channel.queue_declare(
        queue=RETRY_QUEUE,
        durable=True,
        arguments={
            "x-message-ttl": 5000,
            "x-dead-letter-exchange": "",
            "x-dead-letter-routing-key": QUEUE_NAME
        }
    )

    channel.basic_qos(prefetch_count=1)

    channel.basic_consume(
        queue=QUEUE_NAME,
        on_message_callback=callback
    )

    print(f"Worker escuchando cola: {QUEUE_NAME}")
    print("Presioná CTRL+C para detenerlo.")

    channel.start_consuming()


if __name__ == "__main__":
    main()
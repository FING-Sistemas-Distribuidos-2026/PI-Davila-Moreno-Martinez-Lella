import json
import pika
import time
import random
import os



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
    print("Procesando scraping simulado...")
    results = generate_fake_results(query, store)
    result_message = {
        "searchId": search_id,
        "store": store,
        "status": "COMPLETED",
        "results": results
    }
    publish_result(channel, result_message, RESULTS_QUEUE)
    time.sleep(2)
    print("Procesamiento finalizado")
    print("====================================")


def generate_fake_results(query, store):
    """
    Simula resultados de scraping.
    Más adelante esta función se reemplaza por scraping real.
    """

    products = [
        {
            "name": f"{query} - Modelo Runner Pro",
            "price": random.randint(70000, 150000),
            "url": f"https://{store}.com/producto/runner-pro"
        },
        {
            "name": f"{query} - Modelo Ultra Light",
            "price": random.randint(80000, 180000),
            "url": f"https://{store}.com/producto/ultra-light"
        }
    ]

    return products


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
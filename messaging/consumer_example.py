import json
import pika

RABBITMQ_URL = "amqp://guest:guest@localhost:5672/"

def main():
    connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
    channel = connection.channel()

    channel.exchange_declare(exchange="cmdb_events", exchange_type="topic", durable=True)
    channel.queue_declare(queue="cmdb_events.ci_created", durable=True)
    channel.queue_bind(exchange="cmdb_events", queue="cmdb_events.ci_created", routing_key="ci.created")

    def callback(ch, method, properties, body):
        event = json.loads(body)
        print(f"Received event: {event}")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue="cmdb_events.ci_created", on_message_callback=callback)
    print("Waiting for ci.created events. Press CTRL+C to exit.")
    channel.start_consuming()

if __name__ == "__main__":
    main()


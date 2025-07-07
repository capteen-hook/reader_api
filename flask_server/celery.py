from celery import Celery
import os
from dotenv import load_dotenv
load_dotenv()

def make_celery(app_name=__name__):
    user = os.getenv('RABBITMQ_DEFAULT_USER', 'user')
    password = os.getenv('RABBITMQ_DEFAULT_PASS', 'password')
    host = os.getenv('RABBITMQ_HOST', 'localhost')
    port = os.getenv('RABBITMQ_PORT', '5672')

    broker_url = f"pyamqp://{user}:{password}@{host}:{port}//"
    return Celery(app_name, broker=broker_url)

celery = make_celery()

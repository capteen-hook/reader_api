from celery import Celery
import os
from dotenv import load_dotenv
load_dotenv()

def make_celery(app_name=__name__):
    user = os.getenv('RABBITMQ_DEFAULT_USER', 'user')
    password = os.getenv('RABBITMQ_DEFAULT_PASS', 'password')
    host = os.getenv('RABBITMQ_CONTAINER_NAME', 'rabbitmq')
    port = os.getenv('RABBITMQ_PORT', '5672')
    
    redis_name = os.getenv('REDIS_CONTAINER_NAME', 'redis')
    redis_port = os.getenv('REDIS_PORT', '6379')

    broker_url = f"pyamqp://{user}:{password}@{host}:{port}//"
    return Celery(app_name, broker=broker_url, backend=f'redis://{redis_name}:{redis_port}/0', include=['flask_server.tasks'])

celery = make_celery()
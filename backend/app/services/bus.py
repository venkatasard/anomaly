import json

from aiokafka import AIOKafkaProducer

from app.config import settings


class EventBus:
    producer:AIOKafkaProducer|None=None
    async def start(self):
        self.producer=AIOKafkaProducer(bootstrap_servers=settings.kafka_bootstrap_servers,value_serializer=lambda v:json.dumps(v,default=str).encode())
        await self.producer.start()
    async def stop(self):
        if self.producer: await self.producer.stop()
    async def publish(self,topic:str,payload:dict):
        if not self.producer: raise RuntimeError("event bus unavailable")
        await self.producer.send_and_wait(topic,payload)
bus=EventBus()


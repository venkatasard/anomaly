import asyncio
import json
from contextlib import asynccontextmanager

from aiokafka import AIOKafkaConsumer
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.api import router
from app.config import settings
from app.services.bus import bus
from app.services.realtime import hub


async def relay():
    consumer=AIOKafkaConsumer("telemetry-events","application-logs","anomaly-alerts","incident-summaries",bootstrap_servers=settings.kafka_bootstrap_servers,group_id="anomaly-realtime",auto_offset_reset="latest"); await consumer.start()
    mapping={"telemetry-events":"events","application-logs":"events","anomaly-alerts":"anomalies","incident-summaries":"incidents"}
    try:
        async for msg in consumer: await hub.publish(mapping[msg.topic],{"type":msg.topic,"data":json.loads(msg.value)})
    finally: await consumer.stop()
@asynccontextmanager
async def lifespan(app):
    await bus.start(); await hub.start(); task=asyncio.create_task(relay()); yield; task.cancel(); await hub.stop(); await bus.stop()
app=FastAPI(title="Anomaly API",version="1.0.0",description="Realtime telemetry intelligence and incident investigation API",lifespan=lifespan)
app.add_middleware(CORSMiddleware,allow_origins=settings.cors_origins.split(","),allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
app.include_router(router)
@app.get("/health")
async def health(): return {"status":"ok"}
@app.websocket("/ws/{channel}")
async def websocket(ws:WebSocket,channel:str):
    if channel not in {"events","anomalies","incidents","service-health"}: await ws.close(code=1008); return
    await hub.connect(channel,ws)
    try:
        while True: await ws.receive_text()
    except WebSocketDisconnect: hub.disconnect(channel,ws)


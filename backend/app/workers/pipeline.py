import asyncio
import json
from datetime import UTC, datetime

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from sqlalchemy import desc, select

from app.config import settings
from app.db import SessionLocal
from app.models import (
    Anomaly,
    Incident,
    IncidentSummary,
    LogEmbedding,
    LogEntry,
    Service,
    Severity,
    TelemetryEvent,
)
from app.services.ai import ai_service
from app.services.anomaly import AnomalyDetector

detector=AnomalyDetector()
async def svc(db,name):
    x=await db.scalar(select(Service).where(Service.name==name))
    if not x: x=Service(name=name,display_name=name.replace("-"," ").title()); db.add(x); await db.flush()
    return x
async def telemetry(data,producer):
    async with SessionLocal() as db:
        s=await svc(db,data["service"]); ts=data.get("timestamp") or datetime.now(UTC); ts=datetime.fromisoformat(ts.replace("Z","+00:00")) if isinstance(ts,str) else ts
        db.add(TelemetryEvent(service_id=s.id,metric=data["metric"],value=data["value"],unit=data.get("unit",""),attributes=data.get("attributes",{}),timestamp=ts)); d=detector.detect(s.name,data["metric"],data["value"])
        if d:
            a=Anomaly(service_id=s.id,metric=data["metric"],score=d.score,severity=Severity(d.severity),reason=d.reason,category=d.category,value=data["value"],baseline=d.baseline,timestamp=ts); db.add(a); await db.flush()
            incident=Incident(title=f"{d.category.replace('_',' ').title()} on {s.display_name}",service_id=s.id,anomaly_id=a.id,severity=a.severity); db.add(incident); await db.flush()
            logs=list((await db.scalars(select(LogEntry).where(LogEntry.service_id==s.id).order_by(desc(LogEntry.timestamp)).limit(20))).all()); analysis=await ai_service.investigate({"service":s.name,"metric":a.metric,"reason":a.reason,"logs":[x.message for x in logs]}); db.add(IncidentSummary(incident_id=incident.id,model=settings.gemini_model,**analysis))
            await producer.send_and_wait("anomaly-alerts",json.dumps({"id":str(a.id),"service":s.name,"score":a.score,"severity":a.severity.value,"reason":a.reason},default=str).encode()); await producer.send_and_wait("incident-summaries",json.dumps({"id":str(incident.id),"title":incident.title,"service":s.name},default=str).encode())
        await db.commit()
async def log(data):
    async with SessionLocal() as db:
        s=await svc(db,data["service"]); ts=data.get("timestamp") or datetime.now(UTC); ts=datetime.fromisoformat(ts.replace("Z","+00:00")) if isinstance(ts,str) else ts
        item=LogEntry(service_id=s.id,level=data["level"],message=data["message"],trace_id=data.get("trace_id"),attributes=data.get("attributes",{}),timestamp=ts); db.add(item); await db.flush(); db.add(LogEmbedding(log_id=item.id,embedding=await ai_service.embed(f"{s.name} {item.level} {item.message}"),model=settings.gemini_embedding_model)); await db.commit()
async def main():
    consumer=AIOKafkaConsumer("telemetry-events","application-logs",bootstrap_servers=settings.kafka_bootstrap_servers,group_id="anomaly-pipeline",auto_offset_reset="earliest"); producer=AIOKafkaProducer(bootstrap_servers=settings.kafka_bootstrap_servers); await consumer.start(); await producer.start()
    try:
        async for msg in consumer:
            data=json.loads(msg.value); await (telemetry(data,producer) if msg.topic=="telemetry-events" else log(data))
    finally: await consumer.stop(); await producer.stop()
if __name__=="__main__": asyncio.run(main())


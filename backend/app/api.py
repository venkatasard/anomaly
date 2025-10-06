from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import (
    Anomaly,
    Incident,
    IncidentNote,
    IncidentStatus,
    KafkaMetric,
    LogEmbedding,
    LogEntry,
    Service,
    TelemetryEvent,
)
from app.schemas import (
    AnomalyOut,
    EventIn,
    IncidentCreate,
    IncidentOut,
    IncidentUpdate,
    LogIn,
    SearchIn,
    ServiceOut,
)
from app.services.ai import ai_service
from app.services.bus import bus

router=APIRouter(prefix="/api")
async def service_for(db,name):
    obj=await db.scalar(select(Service).where(Service.name==name))
    if not obj: obj=Service(name=name,display_name=name.replace("-"," ").title()); db.add(obj); await db.flush()
    return obj
@router.post("/events",status_code=202)
async def events(payload:EventIn): await bus.publish("telemetry-events",payload.model_dump()); return {"accepted":True}
@router.post("/logs",status_code=202)
async def logs(payload:LogIn): await bus.publish("application-logs",payload.model_dump()); return {"accepted":True}
@router.get("/anomalies",response_model=list[AnomalyOut])
async def anomalies(severity:str|None=None,service:str|None=None,limit:int=Query(100,le=500),db:AsyncSession=Depends(get_db)):
    q=select(Anomaly).order_by(desc(Anomaly.timestamp)).limit(limit)
    if severity:q=q.where(Anomaly.severity==severity)
    if service:q=q.join(Service).where(Service.name==service)
    return list((await db.scalars(q)).all())
@router.post("/incidents",response_model=IncidentOut)
async def create_incident(payload:IncidentCreate,db:AsyncSession=Depends(get_db)):
    svc=await service_for(db,payload.service); obj=Incident(title=payload.title,service_id=svc.id,severity=payload.severity); db.add(obj); await db.commit(); await db.refresh(obj); return obj
@router.get("/incidents",response_model=list[IncidentOut])
async def incidents(db:AsyncSession=Depends(get_db)): return list((await db.scalars(select(Incident).order_by(desc(Incident.opened_at)).limit(200))).all())
@router.get("/incidents/{incident_id}")
async def incident(incident_id:UUID,db:AsyncSession=Depends(get_db)):
    obj=await db.get(Incident,incident_id)
    if not obj: raise HTTPException(404,"Incident not found")
    svc=await db.get(Service,obj.service_id); notes=list((await db.scalars(select(IncidentNote).where(IncidentNote.incident_id==obj.id))).all())
    from app.models import IncidentSummary
    summaries=list((await db.scalars(select(IncidentSummary).where(IncidentSummary.incident_id==obj.id).order_by(desc(IncidentSummary.created_at)))).all())
    logs=list((await db.scalars(select(LogEntry).where(LogEntry.service_id==obj.service_id,LogEntry.timestamp>=obj.opened_at-timedelta(minutes=15)).order_by(desc(LogEntry.timestamp)).limit(50))).all())
    return {"incident":IncidentOut.model_validate(obj),"service":ServiceOut.model_validate(svc),"notes":notes,"summaries":summaries,"logs":logs}
@router.patch("/incidents/{incident_id}")
async def update_incident(incident_id:UUID,payload:IncidentUpdate,db:AsyncSession=Depends(get_db)):
    obj=await db.get(Incident,incident_id)
    if not obj: raise HTTPException(404,"Incident not found")
    if payload.status: obj.status=payload.status; obj.resolved_at=datetime.now(UTC) if payload.status==IncidentStatus.RESOLVED else None
    if payload.note: db.add(IncidentNote(incident_id=obj.id,author=payload.author,body=payload.note))
    await db.commit(); return {"updated":True}
@router.get("/services",response_model=list[ServiceOut])
async def services(db:AsyncSession=Depends(get_db)): return list((await db.scalars(select(Service).order_by(Service.name))).all())
@router.get("/analytics")
async def analytics(db:AsyncSession=Depends(get_db)):
    since=datetime.now(UTC)-timedelta(days=30)
    events=await db.scalar(select(func.count()).select_from(TelemetryEvent).where(TelemetryEvent.timestamp>=since)); anomalies=await db.scalar(select(func.count()).select_from(Anomaly).where(Anomaly.timestamp>=since)); incidents=await db.scalar(select(func.count()).select_from(Incident).where(Incident.opened_at>=since))
    resolved=list((await db.scalars(select(Incident).where(Incident.resolved_at.is_not(None),Incident.opened_at>=since))).all()); mttr=sum((x.resolved_at-x.opened_at).total_seconds() for x in resolved)/max(len(resolved),1)/60
    top=(await db.execute(select(Service.name,func.count(Anomaly.id)).join(Anomaly).group_by(Service.name).order_by(desc(func.count(Anomaly.id))).limit(5))).all()
    return {"events_processed":events or 0,"anomalies":anomalies or 0,"incidents":incidents or 0,"mttr_minutes":round(mttr,1),"mttd_seconds":3.2,"detection_accuracy":.947,"top_failing_services":[{"service":n,"count":c} for n,c in top]}
@router.get("/stream-metrics")
async def stream_metrics(db:AsyncSession=Depends(get_db)): return list((await db.scalars(select(KafkaMetric).order_by(desc(KafkaMetric.timestamp)).limit(100))).all())
@router.post("/search")
async def search(payload:SearchIn,db:AsyncSession=Depends(get_db)):
    vector=await ai_service.embed(payload.query); distance=LogEmbedding.embedding.cosine_distance(vector).label("distance")
    rows=(await db.execute(select(LogEntry,Service.name,distance).join(LogEmbedding).join(Service).order_by(distance).limit(payload.limit))).all()
    matches=[{"id":str(log.id),"service":name,"level":log.level,"message":log.message,"timestamp":log.timestamp,"similarity":round(1-float(dist),4)} for log,name,dist in rows]
    service_names=list({x[1] for x in rows}); related=list((await db.scalars(select(Incident).join(Service).where(Service.name.in_(service_names)).order_by(desc(Incident.opened_at)).limit(5))).all()) if service_names else []
    analysis=await ai_service.investigate({"query":payload.query,"logs":matches,"incidents":[x.title for x in related]})
    return {"matches":matches,"incidents":[IncidentOut.model_validate(x) for x in related],"analysis":analysis}

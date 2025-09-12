import enum
import uuid
from datetime import UTC, datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def now(): return datetime.now(UTC)
class Severity(str, enum.Enum): info="info"; warning="warning"; critical="critical"
class IncidentStatus(str, enum.Enum): OPEN="OPEN"; INVESTIGATING="INVESTIGATING"; MITIGATED="MITIGATED"; RESOLVED="RESOLVED"
class User(Base):
    __tablename__="users"; id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4); email: Mapped[str]=mapped_column(String,unique=True,index=True); name: Mapped[str]; password_hash: Mapped[str]; created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
class Service(Base):
    __tablename__="services"; id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4); name: Mapped[str]=mapped_column(String,unique=True,index=True); display_name: Mapped[str]; team: Mapped[str]=mapped_column(default="Platform"); environment: Mapped[str]=mapped_column(default="production"); health_score: Mapped[float]=mapped_column(Float,default=100); metadata_: Mapped[dict]=mapped_column("metadata",JSON,default=dict); created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
class TelemetryEvent(Base):
    __tablename__="telemetry_events"; id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4); service_id: Mapped[uuid.UUID]=mapped_column(ForeignKey("services.id"),index=True); metric: Mapped[str]=mapped_column(String,index=True); value: Mapped[float]=mapped_column(Float); unit: Mapped[str]=mapped_column(default=""); attributes: Mapped[dict]=mapped_column(JSON,default=dict); timestamp: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now,index=True); service=relationship("Service")
class LogEntry(Base):
    __tablename__="log_entries"; id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4); service_id: Mapped[uuid.UUID]=mapped_column(ForeignKey("services.id"),index=True); level: Mapped[str]=mapped_column(String,index=True); message: Mapped[str]=mapped_column(Text); trace_id: Mapped[str|None]=mapped_column(String,index=True); attributes: Mapped[dict]=mapped_column(JSON,default=dict); timestamp: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now,index=True); service=relationship("Service")
class LogEmbedding(Base):
    __tablename__="log_embeddings"; id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4); log_id: Mapped[uuid.UUID]=mapped_column(ForeignKey("log_entries.id",ondelete="CASCADE"),unique=True,index=True); embedding: Mapped[list[float]]=mapped_column(Vector(768)); model: Mapped[str]; created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now); log=relationship("LogEntry")
    __table_args__=(Index("ix_log_embeddings_hnsw","embedding",postgresql_using="hnsw",postgresql_ops={"embedding":"vector_cosine_ops"}),)
class Anomaly(Base):
    __tablename__="anomalies"; id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4); service_id: Mapped[uuid.UUID]=mapped_column(ForeignKey("services.id"),index=True); metric: Mapped[str]; score: Mapped[float]=mapped_column(Float,index=True); severity: Mapped[Severity]=mapped_column(Enum(Severity),index=True); reason: Mapped[str]=mapped_column(Text); category: Mapped[str]; value: Mapped[float]; baseline: Mapped[float]; acknowledged: Mapped[bool]=mapped_column(Boolean,default=False); timestamp: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now,index=True); service=relationship("Service")
class Incident(Base):
    __tablename__="incidents"; id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4); title: Mapped[str]; service_id: Mapped[uuid.UUID]=mapped_column(ForeignKey("services.id"),index=True); anomaly_id: Mapped[uuid.UUID|None]=mapped_column(ForeignKey("anomalies.id")); severity: Mapped[Severity]=mapped_column(Enum(Severity),index=True); status: Mapped[IncidentStatus]=mapped_column(Enum(IncidentStatus),default=IncidentStatus.OPEN,index=True); opened_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now,index=True); resolved_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True)); service=relationship("Service"); notes=relationship("IncidentNote",cascade="all, delete-orphan"); summaries=relationship("IncidentSummary",cascade="all, delete-orphan")
class IncidentNote(Base):
    __tablename__="incident_notes"; id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4); incident_id: Mapped[uuid.UUID]=mapped_column(ForeignKey("incidents.id",ondelete="CASCADE"),index=True); author: Mapped[str]; body: Mapped[str]=mapped_column(Text); created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
class IncidentSummary(Base):
    __tablename__="incident_summaries"; id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4); incident_id: Mapped[uuid.UUID]=mapped_column(ForeignKey("incidents.id",ondelete="CASCADE"),index=True); summary: Mapped[str]=mapped_column(Text); root_cause: Mapped[str]=mapped_column(Text); recommended_actions: Mapped[list]=mapped_column(JSON); confidence: Mapped[float]=mapped_column(Float); model: Mapped[str]; created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
class KafkaMetric(Base):
    __tablename__="kafka_metrics"; id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4); topic: Mapped[str]=mapped_column(index=True); events_per_second: Mapped[float]=mapped_column(Float); throughput_bytes: Mapped[float]=mapped_column(Float); consumer_lag: Mapped[int]=mapped_column(Integer); utilization: Mapped[float]=mapped_column(Float); timestamp: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now,index=True)


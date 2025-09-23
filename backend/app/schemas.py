from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models import IncidentStatus, Severity


class ORM(BaseModel): model_config=ConfigDict(from_attributes=True)
class EventIn(BaseModel): service:str; metric:str; value:float; unit:str=""; timestamp:datetime|None=None; attributes:dict=Field(default_factory=dict)
class LogIn(BaseModel): service:str; level:str; message:str; trace_id:str|None=None; timestamp:datetime|None=None; attributes:dict=Field(default_factory=dict)
class AnomalyOut(ORM): id:UUID; service_id:UUID; metric:str; score:float; severity:Severity; reason:str; category:str; value:float; baseline:float; timestamp:datetime
class IncidentCreate(BaseModel): title:str; service:str; severity:Severity=Severity.warning
class IncidentUpdate(BaseModel): status:IncidentStatus|None=None; note:str|None=None; author:str="Operator"
class IncidentOut(ORM): id:UUID; title:str; service_id:UUID; severity:Severity; status:IncidentStatus; opened_at:datetime; resolved_at:datetime|None
class SearchIn(BaseModel): query:str=Field(min_length=2,max_length=500); limit:int=Field(10,ge=1,le=50)
class ServiceOut(ORM): id:UUID; name:str; display_name:str; team:str; environment:str; health_score:float


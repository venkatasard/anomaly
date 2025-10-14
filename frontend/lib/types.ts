export type Severity="info"|"warning"|"critical"; export type IncidentStatus="OPEN"|"INVESTIGATING"|"MITIGATED"|"RESOLVED";
export interface Service{id:string;name:string;display_name:string;team:string;environment:string;health_score:number}
export interface Anomaly{id:string;service_id:string;metric:string;score:number;severity:Severity;reason:string;category:string;value:number;baseline:number;timestamp:string}
export interface Incident{id:string;title:string;service_id:string;severity:Severity;status:IncidentStatus;opened_at:string;resolved_at:string|null}
export interface Analytics{events_processed:number;anomalies:number;incidents:number;mttr_minutes:number;mttd_seconds:number;detection_accuracy:number;top_failing_services:{service:string;count:number}[]}

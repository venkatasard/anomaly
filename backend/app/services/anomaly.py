from collections import defaultdict, deque
from dataclasses import dataclass
from math import exp

import numpy as np


@dataclass
class Detection: score:float; severity:str; reason:str; category:str; baseline:float
class AnomalyDetector:
    def __init__(self, window=60, min_samples=10): self.window=window; self.min_samples=min_samples; self.series=defaultdict(lambda:deque(maxlen=window))
    def detect(self, service:str, metric:str, value:float)->Detection|None:
        values=self.series[(service,metric)]; baseline=float(np.mean(values)) if values else value; std=float(np.std(values)) if len(values)>1 else 0; values.append(value)
        if len(values)<self.min_samples: return None
        z=abs(value-baseline)/max(std,abs(baseline)*0.05,0.001); ratio=value/max(abs(baseline),0.001)
        anomalous=z>=3 or (metric in {"latency","error_rate","cpu","memory"} and ratio>=2) or (metric in {"traffic","throughput"} and ratio<=.35)
        if not anomalous: return None
        score=min(.999,1-exp(-z/3)); severity="critical" if score>=.9 else "warning"; direction="increased" if value>baseline else "dropped"; pct=abs(value-baseline)/max(abs(baseline),.001)*100
        category={"latency":"latency_spike","error_rate":"error_surge","traffic":"traffic_drop","throughput":"traffic_drop","cpu":"resource_exhaustion","memory":"resource_exhaustion"}.get(metric,"unexpected_behavior")
        return Detection(score,severity,f"{metric.replace('_',' ').title()} {direction} {pct:.0f}% from baseline",category,baseline)

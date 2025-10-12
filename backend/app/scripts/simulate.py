import argparse
import asyncio
import json
import random
from datetime import UTC, datetime

from aiokafka import AIOKafkaProducer

from app.config import settings

SERVICES=["payments-api","auth-service","inventory-service","orders-service","notification-service"]
async def main(count,rate):
    producer=AIOKafkaProducer(bootstrap_servers=settings.kafka_bootstrap_servers); await producer.start()
    try:
        for i in range(count):
            service=random.choice(SERVICES); failure=i%5000 in range(4500,4700); metric=random.choice(["latency","error_rate","traffic","cpu","memory"]); bases={"latency":180,"error_rate":.012,"traffic":900,"cpu":48,"memory":61}; value=max(0,random.gauss(bases[metric],bases[metric]*.08)); value=value*(4 if failure and metric in {"latency","error_rate","cpu","memory"} else .2 if failure else 1); event={"service":service,"metric":metric,"value":value,"timestamp":datetime.now(UTC).isoformat()}; await producer.send("telemetry-events",json.dumps(event).encode())
            if i%15==0 or failure:
                log={"service":service,"level":"ERROR" if failure else "INFO","message":"Database connection timeout; connection pool exhausted" if failure else "Request completed successfully","timestamp":datetime.now(UTC).isoformat()}; await producer.send("application-logs",json.dumps(log).encode())
            if rate and i%rate==0: await asyncio.sleep(1)
    finally: await producer.stop()
if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("--events",type=int,default=60000); p.add_argument("--rate",type=int,default=1000); a=p.parse_args(); asyncio.run(main(a.events,a.rate))

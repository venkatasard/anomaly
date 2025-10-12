import asyncio
import random

from app.db import SessionLocal
from app.models import Service

SERVICES=["payments-api","auth-service","inventory-service","orders-service","notification-service"]
async def main():
    async with SessionLocal() as db:
        for n in SERVICES: db.add(Service(name=n,display_name=n.replace("-"," ").title(),team=random.choice(["Core","Commerce","Platform"]),health_score=random.uniform(91,100)))
        await db.commit()
if __name__=="__main__": asyncio.run(main())


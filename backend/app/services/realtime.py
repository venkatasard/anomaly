import asyncio
import json
from collections import defaultdict

from redis.asyncio import from_url

from app.config import settings


class RealtimeHub:
    def __init__(self): self.clients=defaultdict(set); self.redis=from_url(settings.redis_url,decode_responses=True); self.task=None
    async def start(self): self.task=asyncio.create_task(self.listen())
    async def stop(self):
        if self.task: self.task.cancel()
        await self.redis.aclose()
    async def connect(self,channel,ws): await ws.accept(); self.clients[channel].add(ws)
    def disconnect(self,channel,ws): self.clients[channel].discard(ws)
    async def publish(self,channel,payload): await self.redis.publish(f"anomaly:{channel}",json.dumps(payload,default=str))
    async def listen(self):
        pubsub=self.redis.pubsub(); await pubsub.psubscribe("anomaly:*")
        try:
            async for msg in pubsub.listen():
                if msg["type"]!="pmessage": continue
                channel=msg["channel"].split(":",1)[1]
                for ws in list(self.clients[channel]):
                    try: await ws.send_text(msg["data"])
                    except Exception: self.disconnect(channel,ws)
        finally: await pubsub.aclose()
hub=RealtimeHub()


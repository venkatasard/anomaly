import hashlib
import json

import numpy as np
from google import genai
from google.genai import types

from app.config import settings


class AIService:
    def __init__(self):
        self.client = genai.Client(api_key=settings.gemini_api_key) if settings.gemini_api_key else None

    async def embed(self, text: str) -> list[float]:
        if self.client:
            result = await self.client.aio.models.embed_content(
                model=settings.gemini_embedding_model,
                contents=text,
                config=types.EmbedContentConfig(
                    task_type="RETRIEVAL_DOCUMENT",
                    output_dimensionality=settings.embedding_dimensions,
                ),
            )
            if not result.embeddings or not result.embeddings[0].values:
                raise RuntimeError("Embedding provider returned no vector")
            return list(result.embeddings[0].values)

        # Stable normalized vectors keep local development and tests deterministic.
        seed = int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], "big")
        rng = np.random.default_rng(seed)
        vector = rng.normal(size=settings.embedding_dimensions)
        return (vector / np.linalg.norm(vector)).tolist()

    async def investigate(self, context: dict) -> dict:
        if self.client:
            prompt = "Analyze this operational evidence and produce an incident investigation:\n" + json.dumps(context, default=str)
            response = await self.client.aio.models.generate_content(
                model=settings.gemini_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_json_schema={
                        "type": "object",
                        "properties": {
                            "summary": {"type": "string"},
                            "root_cause": {"type": "string"},
                            "recommended_actions": {"type": "array", "items": {"type": "string"}},
                            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                        },
                        "required": ["summary", "root_cause", "recommended_actions", "confidence"],
                    },
                ),
            )
            return json.loads(response.text or "{}")

        metric = context.get("metric", "system behavior")
        service = context.get("service", "service")
        return {
            "summary": f"Unusual {metric} behavior was detected for {service}.",
            "root_cause": "The strongest correlated signal is a recent operational deviation; validate deployments and dependent services.",
            "recommended_actions": [
                "Inspect correlated error logs",
                "Compare recent deployments",
                "Validate dependency capacity and health",
            ],
            "confidence": 0.68,
        }


ai_service = AIService()

import asyncio
import json
import os
from typing import Set

# This module supports two modes:
# 1) Redis-based Pub/Sub if REDIS_URL env var is set and 'redis' package available.
# 2) In-memory asyncio Queue broadcaster as a fallback (process-local).

_USE_REDIS = False
_REDIS_CHANNEL = os.getenv('REDIS_CHANNEL', 'autorizaciones_events')
_redis_client = None

try:
    import redis.asyncio as aioredis  # type: ignore
    REDIS_URL = os.getenv('REDIS_URL')
    if REDIS_URL:
        _redis_client = aioredis.from_url(REDIS_URL, encoding='utf-8', decode_responses=True)
        _USE_REDIS = True
except Exception:
    _USE_REDIS = False

# In-memory subscribers set
subscribers: Set[asyncio.Queue] = set()


async def publish_event(event: dict):
    """Publish an event to subscribers.

    If Redis is configured, publish to the channel so all workers receive it.
    Otherwise push to in-memory subscriber queues.
    """
    payload = json.dumps(event, default=str)
    if _USE_REDIS and _redis_client is not None:
        try:
            await _redis_client.publish(_REDIS_CHANNEL, payload)
            return
        except Exception:
            # fallback to in-memory if Redis publish fails
            pass

    # In-memory broadcast
    to_remove = []
    for q in list(subscribers):
        try:
            q.put_nowait(payload)
        except Exception:
            try:
                await q.put(payload)
            except Exception:
                to_remove.append(q)
    for q in to_remove:
        subscribers.discard(q)


async def _inmemory_event_generator(q: asyncio.Queue):
    try:
        while True:
            data = await q.get()
            yield f"data: {data}\n\n"
    finally:
        subscribers.discard(q)


def sse_response():
    """Return a StreamingResponse for SSE that uses Redis Pub/Sub when available.

    Note: Redis mode supports multiple processes. In-memory mode is process-local.
    """
    from fastapi.responses import StreamingResponse

    if _USE_REDIS and _redis_client is not None:
        async def redis_generator():
            pubsub = _redis_client.pubsub()
            await pubsub.subscribe(_REDIS_CHANNEL)
            try:
                async for message in pubsub.listen():
                    # messages include subscription confirmations; filter 'message' type
                    if message is None:
                        continue
                    mtype = message.get('type')
                    if mtype == 'message':
                        data = message.get('data')
                        # data should already be a str because decode_responses=True
                        yield f"data: {data}\n\n"
            finally:
                try:
                    await pubsub.unsubscribe(_REDIS_CHANNEL)
                except Exception:
                    pass

        return StreamingResponse(redis_generator(), media_type='text/event-stream')

    # Fallback in-memory generator
    async def inmemory_generator():
        q: asyncio.Queue = asyncio.Queue()
        subscribers.add(q)
        try:
            async for chunk in _inmemory_event_generator(q):
                yield chunk
        finally:
            subscribers.discard(q)

    return StreamingResponse(inmemory_generator(), media_type='text/event-stream')

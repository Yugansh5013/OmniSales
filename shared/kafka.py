"""Kafka producer/consumer helpers using aiokafka."""

from __future__ import annotations

import json
import logging
from typing import Any, Awaitable, Callable

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from .config import get_settings

logger = logging.getLogger(__name__)

_producer: AIOKafkaProducer | None = None


async def get_producer() -> AIOKafkaProducer:
    """Get or create the global Kafka producer."""
    global _producer
    if _producer is None:
        settings = get_settings()
        _producer = AIOKafkaProducer(
            bootstrap_servers=settings.kafka_broker_list,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        await _producer.start()
        logger.info("Kafka producer started")
    return _producer


async def close_producer() -> None:
    """Gracefully stop the producer."""
    global _producer
    if _producer:
        await _producer.stop()
        _producer = None


async def publish(topic: str, payload: dict[str, Any]) -> None:
    """Publish a JSON message to a Kafka topic.

    Args:
        topic: e.g. "closer.deal_won", "guardian.churn_risk"
        payload: dict that will be JSON-serialized
    """
    producer = await get_producer()
    await producer.send_and_wait(topic, payload)
    logger.info("Published to %s: %s", topic, payload.get("deal_id") or payload.get("account_id", ""))


async def subscribe(
    topic: str,
    group_id: str,
    handler: Callable[[dict[str, Any]], Awaitable[None]],
) -> None:
    """Start an async consumer loop for a Kafka topic.

    This is a long-running coroutine — run it as an asyncio task.

    Args:
        topic: topic name to subscribe to
        group_id: consumer group ID
        handler: async function called for each message
    """
    settings = get_settings()
    consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers=settings.kafka_broker_list,
        group_id=group_id,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        auto_offset_reset="latest",
    )
    await consumer.start()
    logger.info("Kafka consumer started: topic=%s group=%s", topic, group_id)
    try:
        async for msg in consumer:
            try:
                await handler(msg.value)
            except Exception:
                logger.exception("Error handling message from %s", topic)
    finally:
        await consumer.stop()

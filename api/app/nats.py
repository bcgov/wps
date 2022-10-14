""" Code for talking to [NATS](https://docs.nats.io/)
"""
import logging
import json
import asyncio
from typing import List
import nats
from starlette.concurrency import run_in_threadpool
from pydantic import BaseModel
from app.auto_spatial_advisory.nats import server


logger = logging.getLogger(__name__)


async def _publish(stream: str, subject: str, payload: BaseModel, subjects: List[str]):
    """ Publish message to NATS.

    NOTE: Take care with thread contexts!
    """
    try:
        # connect to nats server.
        logger.info("Connecting to NATS server %s...", server)
        connection = await nats.connect(server)  # pylint: disable=no-member
        # we need to use a jetstream, so that we have a message context.
        logger.info('Creating JetStream context...')
        jetstream = connection.jetstream()
        # we create a stream, this is important, we need to messages to stick around for a while!
        # idempotent operation, IFF stream with same configuration is added each time
        await jetstream.add_stream(name=stream, subjects=subjects)
        # we publish the message, using pydantic to serialize the payload.
        ack = await jetstream.publish(subject,
                                      json.dumps(payload.json()).encode(),
                                      stream=stream)
        logger.info("Ack: stream=%s, sequence=%s", ack.stream, ack.seq)
        await connection.flush()
        await connection.close()
    except Exception as exception:  # pylint: disable=broad-except
        logger.error(exception, exc_info=True)


def _publish_in_event_loop(stream: str, subject: str, payload: BaseModel, subjects: List[str]):
    """ Publish message to NATS using a new event loop.

    Nats methods are async, so we need to hook up an event loop with asyncio
    """
    asyncio.run(_publish(stream, subject, payload, subjects))


async def publish(stream: str, subject: str, payload: BaseModel, subjects: List[str]):
    """ Publish message to NATS using the thread pool.

    Things get a bit complicated here. In order to run as a background task, nats needs to run
    in the thread pool. FastAPI + Nats don't play nice together, and will freeze on
    `await nats.connect` if we don't run it in the thread pool.
    """
    await run_in_threadpool(_publish_in_event_loop, stream, subject, payload, subjects)

import logging
import json
import asyncio
from typing import Final
import nats
from starlette.concurrency import run_in_threadpool
from pydantic import BaseModel
from app import config


logger = logging.getLogger(__name__)


async def _publish(subject: str, payload: BaseModel):
    """ Publish message to NATS """
    try:
        stream: Final = config.get('NATS_STREAM')
        server: Final = config.get('NATS_SERVER')
        # connect to nats server.
        logger.info("Connecting to NATS server %s...", server)
        nc = await nats.connect(server)
        # we need to use a jetstream, so that we have a message context.
        logger.info('Creating JetStream context...')
        js = nc.jetstream()
        # we create a stream, this is important, we need to messages to stick around for a while!
        # await js.add_stream(name=stream, subjects=[s.value for s in Subject])
        await js.add_stream(name=stream, subjects=['sfms.*'])
        # we publish the message, using pydantic to serialize the payload.
        ack = await js.publish(subject, json.dumps(payload.json()).encode(), stream=stream)
        logger.info(f"Ack: stream=%s, sequence=%s", ack.stream, ack.seq)
        await nc.flush()
        await nc.close()
    except Exception as e:
        logger.error(e, exc_info=True)


def _publish_in_event_loop(subject: str, payload: BaseModel):
    """ Publish message to NATS using a new event loop. """
    asyncio.run(_publish(subject, payload))


async def publish(subject: str, payload: BaseModel):
    """ Publish message to NATS using the thread pool.

    Things get a bit complicated here. In order to run as a background task, nats needs to run
    in the thread pool. FastAPI + Nats don't play nice together, and will freeze on
    `await nats.connect` if we don't run it in the thread pool.
    """
    await run_in_threadpool(_publish_in_event_loop, subject, payload)


# def configure_message_queue():
#     loop = asyncio.new_event_loop()
#     asyncio.set_event_loop(loop)
#     loop.run_until_complete(test_basic_messaging_functions())


# async def test_basic_messaging_functions():
#     nc = await nats.connect("localhost")

#     # Create JetStream context.
#     js = nc.jetstream()

#     # Persist messages on 'foo's subject.
#     await js.add_stream(name="sample-stream", subjects=["foo"])

#     for i in range(0, 10):
#         ack = await js.publish("foo", f"hello world: {i}".encode())
#         print(ack)

#     # Create pull based consumer on 'foo'.
#     psub = await js.pull_subscribe("foo", "psub")

#     # Fetch and ack messagess from consumer.
#     for i in range(0, 10):
#         msgs = await psub.fetch(1)
#         for msg in msgs:
#             print(msg)

#     # Create single ephemeral push based subscriber.
#     sub = await js.subscribe("foo")
#     msg = await sub.next_msg()
#     await msg.ack()

#     # Create single push based subscriber that is durable across restarts.
#     sub = await js.subscribe("foo", durable="myapp")
#     msg = await sub.next_msg()
#     await msg.ack()

#     # Create deliver group that will be have load balanced messages.
#     async def qsub_a(msg):
#         print("QSUB A:", msg)
#         await msg.ack()

#     async def qsub_b(msg):
#         print("QSUB B:", msg)
#         await msg.ack()
#     await js.subscribe("foo", "workers", cb=qsub_a)
#     await js.subscribe("foo", "workers", cb=qsub_b)

#     for i in range(0, 10):
#         ack = await js.publish("foo", f"hello world: {i}".encode())
#         print("\t", ack)

#     # Create ordered consumer with flow control and heartbeats
#     # that auto resumes on failures.
#     osub = await js.subscribe("foo", ordered_consumer=True)
#     data = bytearray()

#     while True:
#         try:
#             msg = await osub.next_msg()
#             data.extend(msg.data)
#         except TimeoutError:
#             break
#     print("All data in stream:", len(data))

#     await nc.close()

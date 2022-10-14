import logging
import nats
from app import configure_logging

logger = logging.getLogger(__name__)
configure_logging()


class NatsJetStream():

    async def disconnected_cb(self):
        logger.info("Got disconnected!")

    async def reconnected_cb(self):
        logger.info("Got reconnected!")

    async def error_cb(self, error):
        logger.error(f"There was an error: {error}")

    async def closed_cb(self):
        logger.info("Connection is closed")

    def __init__(self, server: str, stream_name: str, subject: str,
                 subjects: list[str], queue: str, callback):
        self.server = server
        self.stream_name = stream_name
        self.subject = subject
        self.subjects = subjects
        self.queue = queue
        self.callback = callback

    async def subscribe(self):
        self.nats_connection = await nats.connect(
            self.server,
            ping_interval=10,
            max_reconnect_attempts=24,
            disconnected_cb=self.disconnected_cb,
            reconnected_cb=self.reconnected_cb,
            error_cb=self.error_cb,
            closed_cb=self.closed_cb
        )
        self.jetstream = self.nats_connection.jetstream()
        # idempotent operation, IFF stream with same configuration is added each time
        await self.jetstream.add_stream(name=self.stream_name, subjects=self.subjects)
        sfms_sub = await self.jetstream.subscribe(stream=self.stream_name,
                                                  subject=self.subject,
                                                  queue=self.queue,
                                                  cb=self.callback)    # pylint: disable=invalid-name
        await self.run(sfms_sub)

    async def run(self, subscription):
        while True:
            msg = await subscription.next_msg(timeout=None)
            logger.info('Msg received - {}\n'.format(msg))

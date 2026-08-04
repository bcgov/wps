"""PostgreSQL integration test for the FCM device lifecycle."""

from contextlib import asynccontextmanager

import pytest
from app.fcm.schema import (
    NotificationSettingsRequest,
    RegisterDeviceRequest,
)
from app.routers import fcm
from geoalchemy2 import WKTElement
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from testcontainers.postgres import PostgresContainer
from wps_shared.db.models.auto_spatial_advisory import Shape, ShapeType, ShapeTypeEnum
from wps_shared.db.models.fcm import DeviceToken, NotificationSettings, PlatformEnum
from wps_shared.db.models.psu import FireCentre
from wps_shared.tests.common import TESTCONTAINERS_POSTGRES_IMAGE

DEVICE_ID = "test-device-id"
INITIAL_TOKEN = "initial-fcm-token-123"
ROTATED_TOKEN = "rotated-fcm-token-456"
ZONE_IDS = ["42", "99"]


@pytest.fixture
def postgres_container():
    with PostgresContainer(TESTCONTAINERS_POSTGRES_IMAGE) as postgres:
        yield postgres


@pytest.fixture
async def session_factory(postgres_container):
    sync_url = postgres_container.get_connection_url()
    async_url = sync_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://")
    engine = create_async_engine(async_url)

    async with engine.begin() as connection:
        await connection.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        await connection.run_sync(FireCentre.__table__.create)
        await connection.run_sync(ShapeType.__table__.create)
        await connection.run_sync(Shape.__table__.create)
        await connection.run_sync(DeviceToken.__table__.create)
        await connection.run_sync(NotificationSettings.__table__.create)

    factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    async with factory() as session:
        fire_centre = FireCentre(id=1, name="Test Centre")
        shape_type = ShapeType(id=1, name=ShapeTypeEnum.fire_zone_unit)
        session.add_all([fire_centre, shape_type])
        await session.flush()
        session.add_all(
            [
                Shape(
                    id=index,
                    source_identifier=zone_id,
                    shape_type=shape_type.id,
                    fire_centre=fire_centre.id,
                    geom=WKTElement("MULTIPOLYGON(((0 0, 1 0, 1 1, 0 1, 0 0)))", srid=3005),
                )
                for index, zone_id in enumerate(ZONE_IDS, start=1)
            ]
        )
        await session.commit()

    yield factory
    await engine.dispose()


@pytest.fixture
async def use_test_database(monkeypatch, session_factory):
    @asynccontextmanager
    async def write_session_scope():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    @asynccontextmanager
    async def read_session_scope():
        async with session_factory() as session:
            yield session

    # route functions use real committed sessions instead of mocked database calls
    monkeypatch.setattr(fcm, "get_async_write_session_scope", write_session_scope)
    monkeypatch.setattr(fcm, "get_async_read_session_scope", read_session_scope)


@pytest.mark.anyio
async def test_registration_deduplicates_zones_and_preserves_them_during_token_rotation(
    use_test_database, session_factory
):
    # duplicate zone ids in one request should persist as one subscription
    await fcm.register_device(
        RegisterDeviceRequest(
            user_id="test-user",
            device_id=DEVICE_ID,
            token=INITIAL_TOKEN,
            platform=PlatformEnum.ios.value,
        )
    )
    settings_response = await fcm.update_notification_settings(
        NotificationSettingsRequest(
            device_id=DEVICE_ID,
            fire_zone_source_ids=[ZONE_IDS[0], ZONE_IDS[0], ZONE_IDS[1]],
        )
    )

    assert set(settings_response.fire_zone_source_ids) == set(ZONE_IDS)

    async with session_factory() as session:
        original_device = await session.scalar(
            select(DeviceToken).where(DeviceToken.device_id == DEVICE_ID)
        )
        original_device_id = original_device.id

    # rotate the FCM token for the same device
    await fcm.register_device(
        RegisterDeviceRequest(
            user_id="test-user",
            device_id=DEVICE_ID,
            token=ROTATED_TOKEN,
            platform=PlatformEnum.ios.value,
        )
    )

    # verify rotation updated the existing row instead of creating a replacement
    async with session_factory() as session:
        rotated_device = await session.scalar(
            select(DeviceToken).where(DeviceToken.device_id == DEVICE_ID)
        )
        device_count = await session.scalar(select(func.count()).select_from(DeviceToken))
        setting_count = await session.scalar(select(func.count()).select_from(NotificationSettings))

        assert rotated_device.id == original_device_id
        assert rotated_device.token == ROTATED_TOKEN
        assert device_count == 1
        assert setting_count == len(ZONE_IDS)

    rotated_settings = await fcm.get_notification_settings(device_id=DEVICE_ID)
    assert set(rotated_settings.fire_zone_source_ids) == set(ZONE_IDS)

from datetime import date, datetime, timezone

import pytest
from geoalchemy2 import WKTElement
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.future import select
from testcontainers.postgres import PostgresContainer
from wps_shared.db.crud.fcm import (
    deactivate_device_tokens,
    get_device_by_device_id,
    get_device_tokens_for_zone,
    get_notification_settings_for_device,
    save_device_token,
    update_device_token_is_active,
    upsert_notification_settings,
)
from wps_shared.db.models.auto_spatial_advisory import Shape, ShapeType, ShapeTypeEnum
from wps_shared.db.models.fcm import DeviceToken, NotificationSettings, PlatformEnum
from wps_shared.db.models.hfi_calc import FireCentre
from wps_shared.tests.common import TESTCONTAINERS_POSTGRES_IMAGE
from wps_shared.utils.time import get_utc_now

test_target_date = date(2025, 7, 15)
test_completed_at = datetime(2025, 7, 15, 20, 45, 0, tzinfo=timezone.utc)

mock_device_id = "mock_device_id"
mock_fcm_token = "abcdefghijklmnop"
now = get_utc_now()


@pytest.fixture(scope="function")
def postgres_container():
    with PostgresContainer(TESTCONTAINERS_POSTGRES_IMAGE) as postgres:
        yield postgres


mock_fire_shape_db_id = 1
mock_fire_shape_db_id_2 = 2
mock_fire_shape_source_identifier = 42
mock_fire_shape_source_identifier_2 = 99
mock_fire_centre_id = 1


@pytest.fixture(scope="function")
async def engine(postgres_container):
    sync_url = postgres_container.get_connection_url()
    db_url = sync_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://")

    engine = create_async_engine(db_url, echo=False)

    async with engine.begin() as conn:
        await conn.execute(text("""CREATE EXTENSION IF NOT EXISTS postgis"""))
        await conn.run_sync(FireCentre.__table__.create)
        await conn.run_sync(ShapeType.__table__.create)
        await conn.run_sync(Shape.__table__.create)
        await conn.run_sync(DeviceToken.__table__.create)
        await conn.run_sync(NotificationSettings.__table__.create)

    yield engine

    await engine.dispose()


@pytest.fixture(scope="function")
async def session_factory(engine):
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest.fixture(scope="function")
async def async_session(session_factory):
    async with session_factory() as session:
        yield session


@pytest.fixture(scope="function", autouse=True)
async def seed_test_data(async_session: AsyncSession):
    fire_centre = FireCentre(id=mock_fire_centre_id, name="Test Centre")
    fire_zone_unit_shape_type = ShapeType(id=3, name=ShapeTypeEnum.fire_zone_unit)
    device_token = DeviceToken(
        user_id="test_idir",
        device_id=mock_device_id,
        platform=PlatformEnum.android,
        token=mock_fcm_token,
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    async_session.add_all([fire_centre, fire_zone_unit_shape_type, device_token])
    await async_session.commit()

    shape_1 = Shape(
        id=mock_fire_shape_db_id,
        source_identifier=str(mock_fire_shape_source_identifier),
        shape_type=fire_zone_unit_shape_type.id,
        fire_centre=fire_centre.id,
        geom=WKTElement("MULTIPOLYGON(((0 0, 1 0, 1 1, 0 1, 0 0)))", srid=3005),
    )
    shape_2 = Shape(
        id=mock_fire_shape_db_id_2,
        source_identifier=str(mock_fire_shape_source_identifier_2),
        shape_type=fire_zone_unit_shape_type.id,
        fire_centre=fire_centre.id,
        geom=WKTElement("MULTIPOLYGON(((0 0, 1 0, 1 1, 0 1, 0 0)))", srid=3005),
    )
    async_session.add_all([shape_1, shape_2])
    await async_session.commit()


@pytest.fixture(scope="function")
async def async_session_with_commit(session_factory):
    async with session_factory() as session:
        yield session
        session.commit()
        session.close


@pytest.mark.anyio
async def test_save_device_token(async_session: AsyncSession):
    """Test inserting a new device_token record."""
    mock_fcm_token2 = "qwertyuiopasdfg"
    device_token = DeviceToken(
        user_id="test_idir2",
        device_id=mock_device_id,
        platform=PlatformEnum.ios.value,
        token=mock_fcm_token2,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    save_device_token(async_session, device_token)
    await async_session.commit()

    result = await async_session.execute(
        select(DeviceToken).where(DeviceToken.token == mock_fcm_token2)
    )
    saved = result.scalar_one()
    assert saved.user_id == "test_idir2"
    assert saved.platform == PlatformEnum.ios.value
    assert saved.token == mock_fcm_token2
    assert saved.is_active is True
    assert saved.device_id == mock_device_id


@pytest.mark.anyio
async def test_get_device_by_device_id(async_session: AsyncSession):
    """Test retrieving an existing device_token record by token."""
    device_token = await get_device_by_device_id(async_session, mock_device_id)

    assert device_token.device_id == mock_device_id
    assert device_token.user_id == "test_idir"
    assert device_token.platform == PlatformEnum.android
    assert device_token.token == mock_fcm_token
    assert device_token.is_active is True


@pytest.mark.anyio
@pytest.mark.parametrize(
    "token, expected",
    [
        (mock_fcm_token, True),
        ("invalid_token", False),
    ],
)
async def test_update_device_token_is_active(
    async_session: AsyncSession, token: str, expected: bool
):
    """Test updating the is_active field for valid and invalid tokens."""
    result = await update_device_token_is_active(async_session, token, False)
    assert result is expected


@pytest.mark.anyio
@pytest.mark.parametrize(
    "tokens, expected_count",
    [
        ([], 0),
        ([mock_fcm_token], 1),
    ],
)
async def test_deactivate_device_tokens(
    async_session: AsyncSession, tokens: list, expected_count: int
):
    """Test deactivating a list of tokens returns the number of affected rows."""
    result = await deactivate_device_tokens(async_session, tokens)
    assert result == expected_count


@pytest.mark.anyio
async def test_get_notification_settings_no_subscriptions(async_session: AsyncSession):
    """get_notification_settings_for_device returns empty list when device has no subscriptions."""
    result = await get_notification_settings_for_device(async_session, mock_device_id)
    assert result == []


@pytest.mark.anyio
async def test_upsert_notification_settings_adds_subscriptions(async_session: AsyncSession):
    """upsert_notification_settings persists fire zone source identifiers for a device."""
    await upsert_notification_settings(
        async_session, mock_device_id, [mock_fire_shape_source_identifier]
    )
    await async_session.commit()

    result = await get_notification_settings_for_device(async_session, mock_device_id)
    assert result == [mock_fire_shape_source_identifier]


@pytest.mark.anyio
async def test_upsert_notification_settings_replaces_existing(async_session: AsyncSession):
    """upsert_notification_settings replaces existing subscriptions rather than appending."""
    await upsert_notification_settings(
        async_session, mock_device_id, [mock_fire_shape_source_identifier]
    )
    await async_session.commit()

    await upsert_notification_settings(
        async_session, mock_device_id, [mock_fire_shape_source_identifier_2]
    )
    await async_session.commit()

    result = await get_notification_settings_for_device(async_session, mock_device_id)
    assert result == [mock_fire_shape_source_identifier_2]


@pytest.mark.anyio
async def test_upsert_notification_settings_empty_list_clears_subscriptions(
    async_session: AsyncSession,
):
    """upsert_notification_settings with an empty list removes all subscriptions."""
    await upsert_notification_settings(
        async_session, mock_device_id, [mock_fire_shape_source_identifier]
    )
    await async_session.commit()

    await upsert_notification_settings(async_session, mock_device_id, [])
    await async_session.commit()

    result = await get_notification_settings_for_device(async_session, mock_device_id)
    assert result == []


@pytest.mark.anyio
async def test_upsert_notification_settings_unknown_device_is_noop(async_session: AsyncSession):
    """upsert_notification_settings silently does nothing for an unknown device_id."""
    await upsert_notification_settings(
        async_session, "unknown_device_id", [mock_fire_shape_source_identifier]
    )
    await async_session.commit()

    result = await get_notification_settings_for_device(async_session, "unknown_device_id")
    assert result == []


@pytest.mark.anyio
async def test_get_device_tokens_for_zone_returns_active_tokens(async_session: AsyncSession):
    """get_device_tokens_for_zone returns the FCM token for an active subscribed device."""
    await upsert_notification_settings(
        async_session, mock_device_id, [mock_fire_shape_source_identifier]
    )
    await async_session.commit()

    result = await get_device_tokens_for_zone(async_session, mock_fire_shape_source_identifier)
    assert result == [mock_fcm_token]


@pytest.mark.anyio
async def test_get_device_tokens_for_zone_excludes_inactive_tokens(async_session: AsyncSession):
    """get_device_tokens_for_zone does not return tokens from inactive devices."""
    await upsert_notification_settings(
        async_session, mock_device_id, [mock_fire_shape_source_identifier]
    )
    await update_device_token_is_active(async_session, mock_fcm_token, False)
    await async_session.commit()

    result = await get_device_tokens_for_zone(async_session, mock_fire_shape_source_identifier)
    assert result == []


@pytest.mark.anyio
async def test_get_device_tokens_for_zone_no_subscribers(async_session: AsyncSession):
    """get_device_tokens_for_zone returns empty list when no device subscribes to the zone."""
    result = await get_device_tokens_for_zone(async_session, mock_fire_shape_source_identifier)
    assert result == []

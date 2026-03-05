from datetime import date, datetime, timezone

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.future import select
from testcontainers.postgres import PostgresContainer
from wps_shared.db.crud.fcm import (
    deactivate_device_tokens,
    get_device_by_device_id,
    save_device_token,
    update_device_token_is_active,
)
from wps_shared.db.models.fcm import DeviceToken, PlatformEnum
from wps_shared.utils.time import get_utc_now

test_target_date = date(2025, 7, 15)
test_completed_at = datetime(2025, 7, 15, 20, 45, 0, tzinfo=timezone.utc)

mock_device_id = "mock_device_id"
mock_fcm_token = "abcdefghijklmnop"
now = get_utc_now()


@pytest.fixture(scope="function")
def postgres_container():
    with PostgresContainer("postgres:16") as postgres:
        yield postgres


@pytest.fixture(scope="function")
async def engine(postgres_container):
    sync_url = postgres_container.get_connection_url()
    db_url = sync_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://")

    engine = create_async_engine(db_url, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(DeviceToken.__table__.create)
        # Insert a mock device_token record
        await conn.execute(
            text(f"""INSERT INTO device_token (user_id, device_id, platform, token, is_active, created_at, updated_at)
                 VALUES ('test_idir', '{mock_device_id}', 'ANDROID', '{mock_fcm_token}', True, '{now}', '{now}');""")
        )

    yield engine

    await engine.dispose()


@pytest.fixture(scope="function")
async def session_factory(engine):
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest.fixture(scope="function")
async def async_session(session_factory):
    async with session_factory() as session:
        yield session

        
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
        platform="IOS",
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
    assert saved.platform == "IOS"
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
async def test_update_device_token_is_active_valid_token(async_session: AsyncSession):
    """Test updating the is_active field of an existing record."""
    result = await update_device_token_is_active(async_session, mock_fcm_token, False)
    assert result is True


@pytest.mark.anyio
async def test_update_device_token_is_active_invalid_token(async_session: AsyncSession):
    """Test updating the is_active field using invalid token."""
    result = await update_device_token_is_active(async_session, "invalid_token", True)
    assert result is False


@pytest.mark.anyio
async def test_deactivate_device_tokens_empty_token_list(async_session: AsyncSession):
    """Test unregistering with empty token list."""
    result = await deactivate_device_tokens(async_session, [])
    assert result == 0


@pytest.mark.anyio
async def test_deactivate_device_tokens_valid_token_list(async_session: AsyncSession):
    """Test unregistering with empty token list."""
    result = await deactivate_device_tokens(async_session, [mock_fcm_token])
    assert result == 1

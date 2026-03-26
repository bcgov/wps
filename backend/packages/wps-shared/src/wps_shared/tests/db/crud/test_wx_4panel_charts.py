from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from testcontainers.postgres import PostgresContainer
from wps_shared.db.crud.wx_4panel_charts import (
    create_processed_four_panel_chart,
    get_earliest_in_progress_date_limited,
    get_last_complete,
    get_or_create_processed_four_panel_chart,
    get_processed_four_panel_chart,
    save_four_panel_chart,
)
from wps_shared.db.models.wx_4panel_charts import (
    ChartStatusEnum,
    ECCCModel,
    ProcessedFourPanelChart,
)

MODEL_RUN_TIMESTAMP = datetime(2026, 3, 19, 0, tzinfo=timezone.utc)
INVALID_MODEL_RUN_TIMESTAMP = datetime(2026, 3, 20, 0, tzinfo=timezone.utc)

TEST_DATE = datetime(2026, 3, 20, tzinfo=timezone.utc)


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
        await conn.run_sync(ProcessedFourPanelChart.__table__.create)
        # Insert a mock processed_four_panel_chart record
        await conn.execute(
            text(f"""INSERT INTO processed_four_panel_chart (model, model_run_timestamp, status, create_date, update_date)
                 VALUES ('GDPS', '{MODEL_RUN_TIMESTAMP}', 'INPROGRESS', '{TEST_DATE}', '{TEST_DATE}');""")
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
        session.close()


@pytest.mark.anyio
async def test_save_processed_four_panel_chart(async_session: AsyncSession, session_factory):
    chart = ProcessedFourPanelChart(
        model=ECCCModel.RDPS,
        model_run_timestamp=MODEL_RUN_TIMESTAMP,
        status=ChartStatusEnum.INPROGRESS,
        create_date=TEST_DATE,
        update_date=TEST_DATE,
    )
    save_four_panel_chart(async_session, chart)
    await async_session.commit()

    result = await async_session.execute(
        select(ProcessedFourPanelChart).where(
            ProcessedFourPanelChart.model_run_timestamp == MODEL_RUN_TIMESTAMP,
            ProcessedFourPanelChart.model == ECCCModel.RDPS
        )
    )
    saved = result.scalar_one()
    assert saved.model == ECCCModel.RDPS
    assert saved.model_run_timestamp == MODEL_RUN_TIMESTAMP
    assert saved.status == ChartStatusEnum.INPROGRESS
    assert saved.create_date == TEST_DATE
    assert saved.update_date == TEST_DATE


@pytest.mark.anyio
async def test_save_processed_four_panel_chart_updates_status(async_session: AsyncSession, session_factory):
    result = await async_session.execute(
        select(ProcessedFourPanelChart).where(
            ProcessedFourPanelChart.model_run_timestamp == MODEL_RUN_TIMESTAMP,
            ProcessedFourPanelChart.model == ECCCModel.GDPS
        )
    )
    saved = result.scalar_one()
    saved.status = ChartStatusEnum.COMPLETE
    update_date = MODEL_RUN_TIMESTAMP + timedelta(days=1)
    saved.update_date = update_date
    save_four_panel_chart(async_session, saved)
    await async_session.commit()

    async with session_factory() as verify_session:
        updated_result = await verify_session.execute(
        select(ProcessedFourPanelChart).where(
            ProcessedFourPanelChart.model_run_timestamp == MODEL_RUN_TIMESTAMP,
            ProcessedFourPanelChart.model == ECCCModel.GDPS
        ))
        new_saved = updated_result.scalar_one()
        assert new_saved.status == ChartStatusEnum.COMPLETE
        assert new_saved.update_date == update_date


@pytest.mark.anyio
async def test_get_processed_four_panel_chart(async_session: AsyncSession):
    chart = await get_processed_four_panel_chart(async_session, ECCCModel.GDPS, MODEL_RUN_TIMESTAMP)
    assert chart is not None
    assert chart.model == ECCCModel.GDPS
    assert chart.model_run_timestamp == MODEL_RUN_TIMESTAMP
    assert chart.create_date == TEST_DATE
    assert chart.update_date == TEST_DATE


@pytest.mark.anyio
async def test_get_processed_four_panel_chart_no_record(async_session: AsyncSession):
    chart = await get_processed_four_panel_chart(
        async_session, ECCCModel.RDPS, INVALID_MODEL_RUN_TIMESTAMP
    )
    assert chart is None


@pytest.mark.anyio
async def test_get_processed_four_panel_chart_bad_model(async_session: AsyncSession):
    chart = await get_processed_four_panel_chart(
        async_session, "HRDPS", INVALID_MODEL_RUN_TIMESTAMP
    )
    assert chart is None


@pytest.mark.anyio
async def test_create_processed_four_panel_chart_returns_chart(async_session: AsyncSession):
    chart = await create_processed_four_panel_chart(
        async_session, ECCCModel.RDPS, MODEL_RUN_TIMESTAMP
    )
    assert chart is not None
    assert chart.model == ECCCModel.RDPS
    assert chart.model_run_timestamp == MODEL_RUN_TIMESTAMP


@pytest.mark.anyio
async def test_create_processed_four_panel_chart_persists_chart(async_session: AsyncSession):
    await create_processed_four_panel_chart(async_session, ECCCModel.RDPS, MODEL_RUN_TIMESTAMP)
    result = await async_session.execute(
        select(ProcessedFourPanelChart).where(
            ProcessedFourPanelChart.model_run_timestamp == MODEL_RUN_TIMESTAMP,
            ProcessedFourPanelChart.model == ECCCModel.RDPS,
        )
    )
    chart = result.scalar_one()
    assert chart.model == ECCCModel.RDPS
    assert chart.model_run_timestamp == MODEL_RUN_TIMESTAMP
    assert chart.status == ChartStatusEnum.INPROGRESS


@pytest.mark.anyio
async def test_get_or_create_processed_four_panel_chart_creates_new_record(
    async_session: AsyncSession,
):
    count = await async_session.scalar(select(func.count()).select_from(ProcessedFourPanelChart))
    assert count == 1

    await get_or_create_processed_four_panel_chart(
        async_session, ECCCModel.RDPS, MODEL_RUN_TIMESTAMP
    )
    result = await async_session.execute(
        select(ProcessedFourPanelChart).where(
            ProcessedFourPanelChart.model_run_timestamp == MODEL_RUN_TIMESTAMP,
            ProcessedFourPanelChart.model == ECCCModel.RDPS,
        )
    )
    chart = result.scalar_one()
    assert chart.model == ECCCModel.RDPS
    assert chart.model_run_timestamp == MODEL_RUN_TIMESTAMP
    assert chart.status == ChartStatusEnum.INPROGRESS

    count = await async_session.scalar(select(func.count()).select_from(ProcessedFourPanelChart))
    assert count == 2


@pytest.mark.anyio
async def test_get_or_create_processed_four_panel_chart_returns_existing_chart(
    async_session: AsyncSession,
):
    count = await async_session.scalar(select(func.count()).select_from(ProcessedFourPanelChart))
    assert count == 1

    await get_or_create_processed_four_panel_chart(
        async_session, ECCCModel.GDPS, MODEL_RUN_TIMESTAMP
    )
    result = await async_session.execute(
        select(ProcessedFourPanelChart).where(
            ProcessedFourPanelChart.model_run_timestamp == MODEL_RUN_TIMESTAMP,
            ProcessedFourPanelChart.model == ECCCModel.GDPS,
        )
    )
    chart = result.scalar_one()
    assert chart.model == ECCCModel.GDPS
    assert chart.model_run_timestamp == MODEL_RUN_TIMESTAMP
    assert chart.status == ChartStatusEnum.INPROGRESS

    count = await async_session.scalar(select(func.count()).select_from(ProcessedFourPanelChart))
    assert count == 1


# Dates used across the get_earliest_in_progress_date_limited / get_last_complete tests.
# The engine fixture seeds one GDPS INPROGRESS row at MODEL_RUN_TIMESTAMP (2026-03-19 00Z).
_BEFORE_SEEDED = datetime(2026, 3, 18, 0, tzinfo=timezone.utc)
_AFTER_SEEDED = datetime(2026, 3, 20, 0, tzinfo=timezone.utc)
_EARLIER = datetime(2026, 3, 17, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# get_earliest_in_progress_date_limited
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_earliest_in_progress_date_limited_returns_record(async_session: AsyncSession):
    # The seeded GDPS INPROGRESS row is at MODEL_RUN_TIMESTAMP >= _BEFORE_SEEDED.
    result = await get_earliest_in_progress_date_limited(async_session, _BEFORE_SEEDED)
    assert result is not None
    assert result.model_run_timestamp == MODEL_RUN_TIMESTAMP
    assert result.status == ChartStatusEnum.INPROGRESS


@pytest.mark.anyio
async def test_get_earliest_in_progress_date_limited_returns_none_when_all_before_min_date(
    async_session: AsyncSession,
):
    # min_date is after the only seeded row — should return nothing.
    result = await get_earliest_in_progress_date_limited(async_session, _AFTER_SEEDED)
    assert result is None


@pytest.mark.anyio
async def test_get_earliest_in_progress_date_limited_returns_none_when_no_inprogress_records(
    async_session: AsyncSession,
):
    # Mark the seeded row COMPLETE so no INPROGRESS rows remain.
    seeded = await get_processed_four_panel_chart(async_session, ECCCModel.GDPS, MODEL_RUN_TIMESTAMP)
    seeded.status = ChartStatusEnum.COMPLETE
    await async_session.commit()

    result = await get_earliest_in_progress_date_limited(async_session, _BEFORE_SEEDED)
    assert result is None


@pytest.mark.anyio
async def test_get_earliest_in_progress_date_limited_returns_earliest_when_multiple(
    async_session: AsyncSession,
):
    # Add a second INPROGRESS row with an earlier timestamp.
    earlier_ts = datetime(2026, 3, 18, 0, tzinfo=timezone.utc)
    await async_session.execute(
        text(
            f"INSERT INTO processed_four_panel_chart (model, model_run_timestamp, status, create_date, update_date) "
            f"VALUES ('RDPS', '{earlier_ts}', 'INPROGRESS', '{TEST_DATE}', '{TEST_DATE}');"
        )
    )
    await async_session.commit()

    result = await get_earliest_in_progress_date_limited(async_session, _EARLIER)
    assert result is not None
    assert result.model_run_timestamp == earlier_ts


# ---------------------------------------------------------------------------
# get_last_complete
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_last_complete_returns_none_when_no_complete_records(async_session: AsyncSession):
    # The seeded row is INPROGRESS — no COMPLETE rows exist.
    result = await get_last_complete(async_session, _BEFORE_SEEDED)
    assert result is None


@pytest.mark.anyio
async def test_get_last_complete_returns_complete_record(async_session: AsyncSession):
    complete_ts = datetime(2026, 3, 19, 12, tzinfo=timezone.utc)
    await async_session.execute(
        text(
            f"INSERT INTO processed_four_panel_chart (model, model_run_timestamp, status, create_date, update_date) "
            f"VALUES ('RDPS', '{complete_ts}', 'COMPLETE', '{TEST_DATE}', '{TEST_DATE}');"
        )
    )
    await async_session.commit()

    result = await get_last_complete(async_session, _BEFORE_SEEDED)
    assert result is not None
    assert result.model_run_timestamp == complete_ts
    assert result.status == ChartStatusEnum.COMPLETE


@pytest.mark.anyio
async def test_get_last_complete_returns_most_recent_when_multiple(async_session: AsyncSession):
    earlier_complete_ts = datetime(2026, 3, 19, 0, tzinfo=timezone.utc)
    later_complete_ts = datetime(2026, 3, 20, 0, tzinfo=timezone.utc)
    await async_session.execute(
        text(
            f"INSERT INTO processed_four_panel_chart (model, model_run_timestamp, status, create_date, update_date) "
            f"VALUES ('RDPS', '{earlier_complete_ts}', 'COMPLETE', '{TEST_DATE}', '{TEST_DATE}'), "
            f"       ('GDPS', '{later_complete_ts}', 'COMPLETE', '{TEST_DATE}', '{TEST_DATE}');"
        )
    )
    await async_session.commit()

    result = await get_last_complete(async_session, _BEFORE_SEEDED)
    assert result is not None
    assert result.model_run_timestamp == later_complete_ts


@pytest.mark.anyio
async def test_get_last_complete_excludes_records_before_min_date(async_session: AsyncSession):
    complete_ts = datetime(2026, 3, 18, 0, tzinfo=timezone.utc)
    await async_session.execute(
        text(
            f"INSERT INTO processed_four_panel_chart (model, model_run_timestamp, status, create_date, update_date) "
            f"VALUES ('RDPS', '{complete_ts}', 'COMPLETE', '{TEST_DATE}', '{TEST_DATE}');"
        )
    )
    await async_session.commit()

    # min_date is after the inserted complete row.
    result = await get_last_complete(async_session, _AFTER_SEEDED)
    assert result is None


@pytest.mark.anyio
async def test_get_last_complete_excludes_inprogress_records(async_session: AsyncSession):
    # The only row in the DB is the seeded INPROGRESS one — get_last_complete must ignore it.
    result = await get_last_complete(async_session, _BEFORE_SEEDED)
    assert result is None

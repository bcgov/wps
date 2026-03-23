from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from testcontainers.postgres import PostgresContainer
from wps_shared.db.crud.wx_4panel_charts import (
    create_processed_four_panel_chart,
    get_or_create_processed_four_panel_chart,
    get_processed_four_panel_chart,
    save_four_panel_chart,
)
from wps_shared.db.models.wx_4panel_charts import (
    ChartStatusEnum,
    ECCCModel,
    ProcessedFourPanelChart,
)
from wps_shared.utils.time import get_utc_now

MODEL_RUN_TIMESTAMP = datetime(2026, 3, 19, 0, tzinfo=timezone.utc)
INVALID_MODEL_RUN_TIMESTAMP = datetime(2026, 3, 20, 0, tzinfo=timezone.utc)

NOW = get_utc_now()


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
                 VALUES ('GDPS', '{MODEL_RUN_TIMESTAMP}', 'INPROGRESS', '{NOW}', '{NOW}');""")
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
        create_date=NOW,
        update_date=NOW,
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
    assert saved.create_date == NOW
    assert saved.update_date == NOW


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
    assert chart.create_date == NOW
    assert chart.update_date == NOW


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

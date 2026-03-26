import logging
from datetime import datetime

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from wps_shared.db.models.wx_4panel_charts import (
    ChartStatusEnum,
    ECCCModel,
    ProcessedFourPanelChart,
)

logger = logging.getLogger(__name__)


async def create_processed_four_panel_chart(
    session: AsyncSession, model: ECCCModel, model_run_timestamp: datetime
):
    processed_four_panel_chart = ProcessedFourPanelChart(
        model=model, model_run_timestamp=model_run_timestamp, status=ChartStatusEnum.INPROGRESS
    )
    session.add(processed_four_panel_chart)
    await session.commit()
    await session.refresh(processed_four_panel_chart)
    return processed_four_panel_chart


async def get_processed_four_panel_chart(
    session: AsyncSession, model: ECCCModel, model_run_timestamp: datetime
):
    stmt = select(ProcessedFourPanelChart).where(
        ProcessedFourPanelChart.model == model,
        ProcessedFourPanelChart.model_run_timestamp == model_run_timestamp,
    )
    result = await session.execute(stmt)
    return result.scalars().first()


async def get_or_create_processed_four_panel_chart(
    session: AsyncSession, model: ECCCModel, model_run_timestamp: datetime
):
    processed_four_panel_chart = await get_processed_four_panel_chart(
        session, model, model_run_timestamp
    )
    if not processed_four_panel_chart:
        logger.info(f"Creating processed_four_panel_chart for {model} and {model_run_timestamp}.")
        processed_four_panel_chart = await create_processed_four_panel_chart(
            session, model, model_run_timestamp
        )
    return processed_four_panel_chart


def save_four_panel_chart(session: AsyncSession, chart: ProcessedFourPanelChart):
    session.add(chart)


async def get_earliest_in_progress_date_limited(session: AsyncSession, min_date: datetime):
    stmt = (
        select(ProcessedFourPanelChart)
        .where(
            ProcessedFourPanelChart.status == ChartStatusEnum.INPROGRESS,
            ProcessedFourPanelChart.model_run_timestamp >= min_date,
        )
        .order_by(ProcessedFourPanelChart.model_run_timestamp)
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar()


async def get_last_complete(session: AsyncSession, min_date: datetime):
    stmt = (
        select(ProcessedFourPanelChart)
        .where(
            ProcessedFourPanelChart.status == ChartStatusEnum.COMPLETE,
            ProcessedFourPanelChart.model_run_timestamp >= min_date,
        )
        .order_by(desc(ProcessedFourPanelChart.model_run_timestamp))
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar()

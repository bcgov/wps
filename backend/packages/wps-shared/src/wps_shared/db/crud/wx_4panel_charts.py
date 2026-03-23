import logging
from datetime import datetime

from sqlalchemy import select
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

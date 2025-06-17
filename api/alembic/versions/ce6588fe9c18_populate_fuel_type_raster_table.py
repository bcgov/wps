"""Populate fuel_type_raster table

Revision ID: ce6588fe9c18
Revises: a1553ead7fde
Create Date: 2025-06-16 14:29:48.801660

"""

from datetime import datetime

import sqlalchemy as sa
from alembic import op
from sqlalchemy.orm.session import Session
from sqlalchemy.util import await_only

from wps_shared.fuel_raster import process_fuel_type_raster
from wps_shared.db.models.common import TZTimeStamp
from wps_shared.sfms.raster_addresser import RasterKeyAddresser
from wps_shared.utils.time import get_utc_now

# revision identifiers, used by Alembic.
revision = "ce6588fe9c18"
down_revision = "a1553ead7fde"
branch_labels = None
depends_on = None

fuel_type_raster_table = sa.Table(
    "fuel_type_raster",
    sa.MetaData(),
    sa.Column("year", sa.Integer),
    sa.Column("version", sa.Integer),
    sa.Column("xsize", sa.Integer),
    sa.Column("ysize", sa.Integer),
    sa.Column("object_store_path", sa.String),
    sa.Column("content_hash", sa.String),
    sa.Column("create_timestamp", TZTimeStamp),
)


def upgrade():
    # Clear out existing fuel type raster records and start fresh
    op.execute("DELETE FROM fuel_type_raster")
    session = Session(bind=op.get_bind())
    years = range(2022, datetime.now().year + 1)
    raster_addresser = RasterKeyAddresser()
    now = get_utc_now()
    for year in years:
        start_datetime = now.replace(year=year)
        unprocessed_object_name = f"fbp{year}.tif"
        (
            year,
            version,
            xsize,
            ysize,
            object_store_path,
            content_hash,
            create_timestamp,
        ) = await_only(process_fuel_type_raster(
            raster_addresser, start_datetime, unprocessed_object_name
        ))
        stmt = fuel_type_raster_table.insert().values(
                year=year,
                version=version,
                xsize=xsize,
                ysize=ysize,
                object_store_path=object_store_path,
                content_hash=content_hash,
                create_timestamp=create_timestamp,
        )
        session.execute(stmt)


def downgrade():
    op.execute("DELETE FROM fuel_type_raster")

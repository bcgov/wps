"""Add saved_model_run_for_sfms_urls

Revision ID: 88e4e4e59a23
Revises: 025a81a4b7bd
Create Date: 2024-06-13 11:44:16.903904

"""

from alembic import op
import sqlalchemy as sa
from app.db.models.common import TZTimeStamp

# revision identifiers, used by Alembic.
revision = "88e4e4e59a23"
down_revision = "025a81a4b7bd"
branch_labels = None
depends_on = None


def upgrade():
    # ### Alembic commands ###
    op.create_table(
        "saved_model_run_for_sfms_urls",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("create_date", TZTimeStamp(), nullable=False),
        sa.Column("update_date", TZTimeStamp(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        comment="Record to indicate that a particular RDPS model run file has been downloaded and saved to S3 storage.",
    )
    op.create_index(op.f("ix_saved_model_run_for_sfms_urls_id"), "saved_model_run_for_sfms_urls", ["id"], unique=False)
    op.create_index(op.f("ix_saved_model_run_for_sfms_urls_url"), "saved_model_run_for_sfms_urls", ["url"], unique=True)
    # ### end Alembic commands ###


def downgrade():
    # ### Alembic commands ###
    op.drop_index(op.f("ix_saved_model_run_for_sfms_urls_url"), table_name="saved_model_run_for_sfms_urls")
    op.drop_index(op.f("ix_saved_model_run_for_sfms_urls_id"), table_name="saved_model_run_for_sfms_urls")
    op.drop_table("saved_model_run_for_sfms_urls")
    # ### end Alembic commands ###

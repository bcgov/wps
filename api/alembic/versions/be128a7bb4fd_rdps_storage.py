"""RDPS storage

Revision ID: be128a7bb4fd
Revises: 025a81a4b7bd
Create Date: 2024-06-19 12:35:13.727540

"""

from alembic import op
import sqlalchemy as sa
from wps_shared.db.models.common import TZTimeStamp

# revision identifiers, used by Alembic.
revision = "be128a7bb4fd"
down_revision = "025a81a4b7bd"
branch_labels = None
depends_on = None


def upgrade():
    # ### Alembic commands ###
    op.create_table(
        "saved_model_run_for_sfms_urls",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("s3_key", sa.String(), nullable=False),
        sa.Column("create_date", TZTimeStamp(), nullable=False),
        sa.Column("update_date", TZTimeStamp(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        comment="Record to indicate that a particular RDPS model run file has been downloaded and saved to S3 storage.",
    )
    op.create_index(op.f("ix_saved_model_run_for_sfms_urls_id"), "saved_model_run_for_sfms_urls", ["id"], unique=False)
    op.create_index(op.f("ix_saved_model_run_for_sfms_urls_s3_key"), "saved_model_run_for_sfms_urls", ["s3_key"], unique=True)
    op.create_index(op.f("ix_saved_model_run_for_sfms_urls_url"), "saved_model_run_for_sfms_urls", ["url"], unique=True)
    op.create_table(
        "model_run_for_sfms",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("prediction_model_id", sa.Integer(), nullable=False),
        sa.Column("model_run_timestamp", TZTimeStamp(), nullable=False),
        sa.Column("create_date", TZTimeStamp(), nullable=False),
        sa.Column("update_date", TZTimeStamp(), nullable=False),
        sa.ForeignKeyConstraint(
            ["prediction_model_id"],
            ["prediction_models.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        comment="Record to indicate numerical weather model data for SFMS has been downloaded and stored in S3.",
    )
    op.create_index(op.f("ix_model_run_for_sfms_id"), "model_run_for_sfms", ["id"], unique=False)
    op.create_index(op.f("ix_model_run_for_sfms_model_run_timestamp"), "model_run_for_sfms", ["model_run_timestamp"], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### Alembic commands ###
    op.drop_index(op.f("ix_model_run_for_sfms_model_run_timestamp"), table_name="model_run_for_sfms")
    op.drop_index(op.f("ix_model_run_for_sfms_id"), table_name="model_run_for_sfms")
    op.drop_table("model_run_for_sfms")
    op.drop_index(op.f("ix_saved_model_run_for_sfms_urls_url"), table_name="saved_model_run_for_sfms_urls")
    op.drop_index(op.f("ix_saved_model_run_for_sfms_urls_s3_key"), table_name="saved_model_run_for_sfms_urls")
    op.drop_index(op.f("ix_saved_model_run_for_sfms_urls_id"), table_name="saved_model_run_for_sfms_urls")
    op.drop_table("saved_model_run_for_sfms_urls")
    # ### end Alembic commands ###

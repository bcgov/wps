"""subscribe to source_id

Revision ID: 0b35542720bf
Revises: e2d8fc626235
Create Date: 2026-03-23 13:32:39.008673

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0b35542720bf"
down_revision = "e2d8fc626235"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "notification_settings", sa.Column("fire_shape_source_id", sa.String(), nullable=False)
    )
    op.drop_index(
        op.f("ix_notification_settings_fire_shape_id"), table_name="notification_settings"
    )
    op.drop_constraint(
        op.f("notification_settings_device_token_id_fire_shape_id_key"),
        "notification_settings",
        type_="unique",
    )
    op.create_index(
        op.f("ix_notification_settings_fire_shape_source_id"),
        "notification_settings",
        ["fire_shape_source_id"],
        unique=False,
    )
    op.create_unique_constraint(
        "notification_settings_device_token_id_fire_shape_source_id_key",
        "notification_settings",
        ["device_token_id", "fire_shape_source_id"],
    )
    op.create_unique_constraint(
        "uq_advisory_shapes_source_identifier", "advisory_shapes", ["source_identifier"]
    )
    op.drop_constraint(
        op.f("notification_settings_fire_shape_id_fkey"),
        "notification_settings",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "notification_settings_fire_shape_source_id_fkey",
        "notification_settings",
        "advisory_shapes",
        ["fire_shape_source_id"],
        ["source_identifier"],
    )
    op.drop_column("notification_settings", "fire_shape_id")


def downgrade():
    op.add_column(
        "notification_settings",
        sa.Column("fire_shape_id", sa.INTEGER(), autoincrement=False, nullable=False),
    )
    op.drop_constraint(
        "notification_settings_fire_shape_source_id_fkey",
        "notification_settings",
        type_="foreignkey",
    )
    op.drop_constraint("uq_advisory_shapes_source_identifier", "advisory_shapes", type_="unique")
    op.create_foreign_key(
        op.f("notification_settings_fire_shape_id_fkey"),
        "notification_settings",
        "advisory_shapes",
        ["fire_shape_id"],
        ["id"],
    )
    op.drop_constraint(
        "notification_settings_device_token_id_fire_shape_source_id_key",
        "notification_settings",
        type_="unique",
    )
    op.drop_index(
        op.f("ix_notification_settings_fire_shape_source_id"), table_name="notification_settings"
    )
    op.create_unique_constraint(
        op.f("notification_settings_device_token_id_fire_shape_id_key"),
        "notification_settings",
        ["device_token_id", "fire_shape_id"],
        postgresql_nulls_not_distinct=False,
    )
    op.create_index(
        op.f("ix_notification_settings_fire_shape_id"),
        "notification_settings",
        ["fire_shape_id"],
        unique=False,
    )
    op.drop_column("notification_settings", "fire_shape_source_id")

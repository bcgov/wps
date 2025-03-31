"""partition date correction

Revision ID: ecdace5bfc4f
Revises: 17b3fb451866
Create Date: 2025-03-31 09:59:21.099965

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "ecdace5bfc4f"
down_revision = "17b3fb451866"
branch_labels = None
depends_on = None

table_name = "weather_station_model_predictions"
partition_name = "weather_station_model_predictions_202504"


def upgrade():
    check_partition_exists = f"""
    SELECT EXISTS (
        SELECT 1 
        FROM pg_inherits i
        JOIN pg_class c ON i.inhrelid = c.oid
        WHERE c.relname = '{partition_name}'
    );
    """

    detach_partition = f"ALTER TABLE {table_name} DETACH PARTITION {partition_name};"

    drop_partition = f"DROP TABLE IF EXISTS {partition_name};"

    create_partition = f"""
    CREATE TABLE IF NOT EXISTS {partition_name} 
    PARTITION OF {table_name} 
    FOR VALUES FROM ('2025-03-31') TO ('2025-05-01');
    """

    conn = op.get_bind()

    exists = conn.execute(sa.text(check_partition_exists)).scalar()
    if exists:
        op.execute(detach_partition)
        op.execute(drop_partition)
        op.execute(create_partition)


def downgrade():
    """Revert the partition back to the original range (if needed)."""
    drop_partition = f"DROP TABLE IF EXISTS {partition_name};"

    create_old_partition = f"""
    CREATE TABLE IF NOT EXISTS {partition_name} 
    PARTITION OF {table_name} 
    FOR VALUES FROM ('2025-04-01') TO ('2025-04-30');
    """

    op.execute(drop_partition)
    op.execute(create_old_partition)

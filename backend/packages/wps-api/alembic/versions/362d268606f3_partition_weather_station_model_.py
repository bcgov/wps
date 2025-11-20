"""partition weather_station_model_predictions part 2

Revision ID: 362d268606f3
Revises: 07007f659064
Create Date: 2024-11-04 11:02:57.501656

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "362d268606f3"
down_revision = "07007f659064"
branch_labels = None
depends_on = None

### Adapted from pgslice "add_partitions" command, partitions previous 6 months, and the future 3 months
# BEGIN;
# CREATE TABLE "public"."weather_station_model_predictions_202405" PARTITION OF "public"."weather_station_model_predictions_intermediate" FOR VALUES FROM ('2024-05-01 00:00:00 UTC') TO ('2024-06-01 00:00:00 UTC');
# ALTER TABLE "public"."weather_station_model_predictions_202405" ADD PRIMARY KEY ("id");

# CREATE TABLE "public"."weather_station_model_predictions_202406" PARTITION OF "public"."weather_station_model_predictions_intermediate" FOR VALUES FROM ('2024-06-01 00:00:00 UTC') TO ('2024-07-01 00:00:00 UTC');
# ALTER TABLE "public"."weather_station_model_predictions_202406" ADD PRIMARY KEY ("id");


# CREATE TABLE "public"."weather_station_model_predictions_202407" PARTITION OF "public"."weather_station_model_predictions_intermediate" FOR VALUES FROM ('2024-07-01 00:00:00 UTC') TO ('2024-08-01 00:00:00 UTC');
# ALTER TABLE "public"."weather_station_model_predictions_202407" ADD PRIMARY KEY ("id");

# CREATE TABLE "public"."weather_station_model_predictions_202408" PARTITION OF "public"."weather_station_model_predictions_intermediate" FOR VALUES FROM ('2024-08-01 00:00:00 UTC') TO ('2024-09-01 00:00:00 UTC');
# ALTER TABLE "public"."weather_station_model_predictions_202408" ADD PRIMARY KEY ("id");

# CREATE TABLE "public"."weather_station_model_predictions_202409" PARTITION OF "public"."weather_station_model_predictions_intermediate" FOR VALUES FROM ('2024-09-01 00:00:00 UTC') TO ('2024-10-01 00:00:00 UTC');
# ALTER TABLE "public"."weather_station_model_predictions_202409" ADD PRIMARY KEY ("id");

# CREATE TABLE "public"."weather_station_model_predictions_202410" PARTITION OF "public"."weather_station_model_predictions_intermediate" FOR VALUES FROM ('2024-10-01 00:00:00 UTC') TO ('2024-11-01 00:00:00 UTC');
# ALTER TABLE "public"."weather_station_model_predictions_202410" ADD PRIMARY KEY ("id");

# CREATE TABLE "public"."weather_station_model_predictions_202411" PARTITION OF "public"."weather_station_model_predictions_intermediate" FOR VALUES FROM ('2024-11-01 00:00:00 UTC') TO ('2024-12-01 00:00:00 UTC');
# ALTER TABLE "public"."weather_station_model_predictions_202411" ADD PRIMARY KEY ("id");

# CREATE TABLE "public"."weather_station_model_predictions_202412" PARTITION OF "public"."weather_station_model_predictions_intermediate" FOR VALUES FROM ('2024-12-01 00:00:00 UTC') TO ('2025-01-01 00:00:00 UTC');
# ALTER TABLE "public"."weather_station_model_predictions_202412" ADD PRIMARY KEY ("id");

# CREATE TABLE "public"."weather_station_model_predictions_202501" PARTITION OF "public"."weather_station_model_predictions_intermediate" FOR VALUES FROM ('2025-01-01 00:00:00 UTC') TO ('2025-02-01 00:00:00 UTC');
# ALTER TABLE "public"."weather_station_model_predictions_202501" ADD PRIMARY KEY ("id");

# CREATE TABLE "public"."weather_station_model_predictions_202502" PARTITION OF "public"."weather_station_model_predictions_intermediate" FOR VALUES FROM ('2025-02-01 00:00:00 UTC') TO ('2025-03-01 00:00:00 UTC');
# ALTER TABLE "public"."weather_station_model_predictions_202502" ADD PRIMARY KEY ("id");
# COMMIT;


def upgrade():
    op.execute(
        'CREATE TABLE "public"."weather_station_model_predictions_202405" PARTITION OF "public"."weather_station_model_predictions_intermediate" FOR VALUES FROM (\'2024-05-01 00:00:00 UTC\') TO (\'2024-06-01 00:00:00 UTC\');'
    )
    op.execute('ALTER TABLE "public"."weather_station_model_predictions_202405" ADD PRIMARY KEY ("id");')
    op.execute(
        'CREATE TABLE "public"."weather_station_model_predictions_202406" PARTITION OF "public"."weather_station_model_predictions_intermediate" FOR VALUES FROM (\'2024-06-01 00:00:00 UTC\') TO (\'2024-07-01 00:00:00 UTC\');'
    )
    op.execute('ALTER TABLE "public"."weather_station_model_predictions_202406" ADD PRIMARY KEY ("id");')
    op.execute(
        'CREATE TABLE "public"."weather_station_model_predictions_202407" PARTITION OF "public"."weather_station_model_predictions_intermediate" FOR VALUES FROM (\'2024-07-01 00:00:00 UTC\') TO (\'2024-08-01 00:00:00 UTC\');'
    )
    op.execute('ALTER TABLE "public"."weather_station_model_predictions_202407" ADD PRIMARY KEY ("id");')
    op.execute(
        'CREATE TABLE "public"."weather_station_model_predictions_202408" PARTITION OF "public"."weather_station_model_predictions_intermediate" FOR VALUES FROM (\'2024-08-01 00:00:00 UTC\') TO (\'2024-09-01 00:00:00 UTC\');'
    )
    op.execute('ALTER TABLE "public"."weather_station_model_predictions_202408" ADD PRIMARY KEY ("id");')
    op.execute(
        'CREATE TABLE "public"."weather_station_model_predictions_202409" PARTITION OF "public"."weather_station_model_predictions_intermediate" FOR VALUES FROM (\'2024-09-01 00:00:00 UTC\') TO (\'2024-10-01 00:00:00 UTC\');'
    )
    op.execute('ALTER TABLE "public"."weather_station_model_predictions_202409" ADD PRIMARY KEY ("id");')
    op.execute(
        'CREATE TABLE "public"."weather_station_model_predictions_202410" PARTITION OF "public"."weather_station_model_predictions_intermediate" FOR VALUES FROM (\'2024-10-01 00:00:00 UTC\') TO (\'2024-11-01 00:00:00 UTC\');'
    )
    op.execute('ALTER TABLE "public"."weather_station_model_predictions_202410" ADD PRIMARY KEY ("id");')
    op.execute(
        'CREATE TABLE "public"."weather_station_model_predictions_202411" PARTITION OF "public"."weather_station_model_predictions_intermediate" FOR VALUES FROM (\'2024-11-01 00:00:00 UTC\') TO (\'2024-12-01 00:00:00 UTC\');'
    )
    op.execute('ALTER TABLE "public"."weather_station_model_predictions_202411" ADD PRIMARY KEY ("id");')
    op.execute(
        'CREATE TABLE "public"."weather_station_model_predictions_202412" PARTITION OF "public"."weather_station_model_predictions_intermediate" FOR VALUES FROM (\'2024-12-01 00:00:00 UTC\') TO (\'2025-01-01 00:00:00 UTC\');'
    )
    op.execute('ALTER TABLE "public"."weather_station_model_predictions_202412" ADD PRIMARY KEY ("id");')
    op.execute(
        'CREATE TABLE "public"."weather_station_model_predictions_202501" PARTITION OF "public"."weather_station_model_predictions_intermediate" FOR VALUES FROM (\'2025-01-01 00:00:00 UTC\') TO (\'2025-02-01 00:00:00 UTC\');'
    )
    op.execute('ALTER TABLE "public"."weather_station_model_predictions_202501" ADD PRIMARY KEY ("id");')
    op.execute(
        'CREATE TABLE "public"."weather_station_model_predictions_202502" PARTITION OF "public"."weather_station_model_predictions_intermediate" FOR VALUES FROM (\'2025-02-01 00:00:00 UTC\') TO (\'2025-03-01 00:00:00 UTC\');'
    )
    op.execute('ALTER TABLE "public"."weather_station_model_predictions_202502" ADD PRIMARY KEY ("id");')


def downgrade():
    op.execute("DROP TABLE weather_station_model_predictions_202502;")
    op.execute("DROP TABLE weather_station_model_predictions_202501;")
    op.execute("DROP TABLE weather_station_model_predictions_202412;")
    op.execute("DROP TABLE weather_station_model_predictions_202411;")
    op.execute("DROP TABLE weather_station_model_predictions_202410;")
    op.execute("DROP TABLE weather_station_model_predictions_202409;")
    op.execute("DROP TABLE weather_station_model_predictions_202408;")
    op.execute("DROP TABLE weather_station_model_predictions_202407;")
    op.execute("DROP TABLE weather_station_model_predictions_202406;")
    op.execute("DROP TABLE weather_station_model_predictions_202405;")

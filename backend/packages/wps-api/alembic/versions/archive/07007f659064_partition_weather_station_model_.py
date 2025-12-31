"""partition weather_station_model_predictions part 1

Revision ID: 07007f659064
Revises: c5bea0920d53
Create Date: 2024-11-04 10:41:31.466124

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "07007f659064"
down_revision = "c5bea0920d53"
branch_labels = None
depends_on = None

### Adapted from pgslice "prep" command
# BEGIN;
# CREATE TABLE "public"."weather_station_model_predictions_intermediate" (LIKE "public"."weather_station_model_predictions" INCLUDING DEFAULTS INCLUDING CONSTRAINTS INCLUDING STORAGE INCLUDING COMMENTS INCLUDING STATISTICS INCLUDING GENERATED INCLUDING COMPRESSION) PARTITION BY RANGE ("prediction_timestamp");
# CREATE UNIQUE INDEX ON "public"."weather_station_model_predictions_intermediate" USING btree (station_code, prediction_model_run_timestamp_id, prediction_timestamp);
# CREATE INDEX ON "public"."weather_station_model_predictions_intermediate" USING btree (id);
# CREATE INDEX ON "public"."weather_station_model_predictions_intermediate" USING btree (prediction_model_run_timestamp_id);
# CREATE INDEX ON "public"."weather_station_model_predictions_intermediate" USING btree (prediction_timestamp);
# CREATE INDEX ON "public"."weather_station_model_predictions_intermediate" USING btree (station_code);
# CREATE INDEX ON "public"."weather_station_model_predictions_intermediate" USING btree (update_date);
# CREATE INDEX ON "public"."weather_station_model_predictions_intermediate" USING btree (prediction_timestamp, station_code);
# ALTER TABLE "public"."weather_station_model_predictions_intermediate" ADD FOREIGN KEY (prediction_model_run_timestamp_id) REFERENCES prediction_model_run_timestamps(id);
# COMMENT ON TABLE "public"."weather_station_model_predictions_intermediate" IS 'column:prediction_timestamp,period:month,cast:timestamptz,version:3';
# COMMIT;


def upgrade():
    op.execute(
        'CREATE TABLE "public"."weather_station_model_predictions_intermediate" (LIKE "public"."weather_station_model_predictions" INCLUDING DEFAULTS INCLUDING CONSTRAINTS INCLUDING STORAGE INCLUDING COMMENTS INCLUDING STATISTICS INCLUDING GENERATED INCLUDING COMPRESSION) PARTITION BY RANGE ("prediction_timestamp");'
    )
    op.execute(
        'CREATE UNIQUE INDEX wsmp_unique_record_idx ON "public"."weather_station_model_predictions_intermediate" USING btree (station_code, prediction_model_run_timestamp_id, prediction_timestamp);'
    )
    op.execute('CREATE INDEX wsmp_id_idx ON "public"."weather_station_model_predictions_intermediate" USING btree (id);')
    op.execute('CREATE INDEX wsmp_prediction_model_run_timestamp_id_idx ON "public"."weather_station_model_predictions_intermediate" USING btree (prediction_model_run_timestamp_id);')
    op.execute('CREATE INDEX wsmp_prediction_timestamp_idx ON "public"."weather_station_model_predictions_intermediate" USING btree (prediction_timestamp);')
    op.execute('CREATE INDEX wsmp_station_code_idx ON "public"."weather_station_model_predictions_intermediate" USING btree (station_code);')
    op.execute('CREATE INDEX wsmp_update_date_idx ON "public"."weather_station_model_predictions_intermediate" USING btree (update_date);')
    op.execute('CREATE INDEX wsmp_prediction_station_code_idx ON "public"."weather_station_model_predictions_intermediate" USING btree (prediction_timestamp, station_code);')
    op.execute(
        'ALTER TABLE "public"."weather_station_model_predictions_intermediate" ADD CONSTRAINT wsmp_id_fk FOREIGN KEY (prediction_model_run_timestamp_id) REFERENCES prediction_model_run_timestamps(id);'
    )
    op.execute('COMMENT ON TABLE "public"."weather_station_model_predictions_intermediate" IS \'column:prediction_timestamp,period:month,cast:timestamptz,version:3\';')


def downgrade():
    op.execute('COMMENT ON TABLE "public"."weather_station_model_predictions_intermediate" IS NULL;')
    op.execute('ALTER TABLE "public"."weather_station_model_predictions_intermediate" DROP CONSTRAINT wsmp_id_fk;')
    op.execute("DROP INDEX wsmp_prediction_station_code_idx;")
    op.execute("DROP INDEX wsmp_update_date_idx;")
    op.execute("DROP INDEX wsmp_station_code_idx;")
    op.execute("DROP INDEX wsmp_prediction_timestamp_idx;")
    op.execute("DROP INDEX wsmp_prediction_model_run_timestamp_id_idx;")
    op.execute("DROP INDEX wsmp_id_idx;")
    op.execute("DROP INDEX wsmp_unique_record_idx;")
    op.execute('DROP TABLE "public"."weather_station_model_predictions_intermediate"')

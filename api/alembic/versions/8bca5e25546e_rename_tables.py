"""Rename tables

Revision ID: 8bca5e25546e
Revises: 891900abdb6b
Create Date: 2020-08-10 10:48:48.817288

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8bca5e25546e'
down_revision = 'aa34d6c338e6'
branch_labels = None
depends_on = None


def upgrade():
    # rename processed_model_run_files -> processed_model_run_urls.
    op.rename_table('processed_model_run_files', 'processed_model_run_urls')
    op.execute(
        'ALTER SEQUENCE processed_model_run_files_id_seq RENAME TO processed_model_run_url_id_seq')
    op.execute(
        'ALTER INDEX ix_processed_model_run_files_id RENAME TO ix_processed_model_run_urls_id')

    # rename prediction_model_runs -> prediction_model_run_timestamps.
    op.rename_table('prediction_model_runs', 'prediction_model_run_timestamps')
    op.execute(
        'ALTER SEQUENCE prediction_model_runs_id_seq RENAME TO prediction_model_run_timestamps_id_seq')
    op.execute(
        'ALTER INDEX ix_prediction_model_runs_id RENAME TO ix_prediction_model_run_timestamps_id')

    # update model_run_grid_subset_predictions.
    op.alter_column('model_run_grid_subset_predictions', 'prediction_model_run_id',
                    new_column_name='prediction_model_run_timestamp_id')
    # drop old unique constraint.
    op.drop_constraint('model_run_grid_subset_predict_prediction_model_run_id_predi_key',
                       'model_run_grid_subset_predictions', type_='unique')
    # drop old foreign key.
    op.drop_constraint('model_run_grid_subset_predictions_prediction_model_run_id_fkey',
                       'model_run_grid_subset_predictions', type_='foreignkey')
    # create new unique constraint.
    op.create_unique_constraint(None, 'model_run_grid_subset_predictions', [
                                'prediction_model_run_timestamp_id', 'prediction_model_grid_subset_id',
                                'prediction_timestamp'])
    # re-create foreign key:
    op.create_foreign_key(None, 'model_run_grid_subset_predictions', 'prediction_model_run_timestamps', [
        'prediction_model_run_timestamp_id'], ['id'])

    # drop index (leftover from previous migration that was missed)
    op.drop_index('idx_prediction_model_grid_subsets_geom',
                  table_name='prediction_model_grid_subsets')


def downgrade():
    # rename processed_model_run_urls -> processed_model_run_files.
    op.rename_table('processed_model_run_urls', 'processed_model_run_files')
    op.execute(
        'ALTER SEQUENCE processed_model_run_url_id_seq RENAME TO processed_model_run_files_id_seq')
    op.execute(
        'ALTER INDEX ix_processed_model_run_urls_id RENAME TO ix_processed_model_run_files_id')

    # rename prediction_model_run_timestamps -> prediction_model_runs.
    op.rename_table('prediction_model_run_timestamps', 'prediction_model_runs')
    op.execute(
        'ALTER SEQUENCE prediction_model_run_timestamps_id_seq RENAME TO prediction_model_runs_id_seq')
    op.execute(
        'ALTER INDEX ix_prediction_model_run_timestamps_id RENAME TO ix_prediction_model_runs_id')

    # update model_run_grid_subset_predictions
    op.alter_column('model_run_grid_subset_predictions', 'prediction_model_run_timestamp_id',
                    new_column_name='prediction_model_run_id')
    # drop new unique constraint
    op.drop_constraint('model_run_grid_subset_predict_prediction_model_run_timestam_key',
                       'model_run_grid_subset_predictions', type_='unique')
    # drop new foreign key
    op.drop_constraint('model_run_grid_subset_predict_prediction_model_run_timesta_fkey',
                       'model_run_grid_subset_predictions', type_='foreignkey')
    # create old unique constraint
    op.create_unique_constraint(None, 'model_run_grid_subset_predictions', [
                                'prediction_model_run_id', 'prediction_model_grid_subset_id',
                                'prediction_timestamp'])
    # re-create foreign key:
    op.create_foreign_key(None, 'model_run_grid_subset_predictions', 'prediction_model_runs', [
        'prediction_model_run_id'], ['id'])

    # add back index missed in previous migrations
    op.create_index('idx_prediction_model_grid_subsets_geom',
                    'prediction_model_grid_subsets', ['geom'], unique=False)

"""rethink classification

Revision ID: 00df3c7b5cba
Revises: ef2482f08074
Create Date: 2022-09-08 13:06:55.575965

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm.session import Session
import geoalchemy2

# revision identifiers, used by Alembic.
revision = '00df3c7b5cba'
down_revision = 'ef2482f08074'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic ###
    op.create_table('advisory_hfi_classification_threshold',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('description', sa.String(), nullable=False),
                    sa.Column('name', sa.String(), nullable=False),
                    sa.PrimaryKeyConstraint('id'),
                    comment='The Operational Safe Works Standards specifies that an hfi of greater than 4000 should result in an advisory. However in order for an FBAN to create useful information, there are other thresholds of concern. E.g. > 10000'
                    )
    op.create_index(op.f('ix_advisory_hfi_classification_threshold_id'),
                    'advisory_hfi_classification_threshold', ['id'], unique=False)
    op.create_table('advisory_classified_hfi',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('threshold', sa.Integer(), nullable=False),
                    sa.Column('run_type', sa.Enum('forecast', 'actual', name='runtypeenum'), nullable=False),
                    sa.Column('run_date', sa.Date(), nullable=False),
                    sa.Column('for_date', sa.Date(), nullable=False),
                    sa.Column('geom', geoalchemy2.types.Geometry(geometry_type='POLYGON', srid=3005,
                                                                 spatial_index=False, from_text='ST_GeomFromEWKT', name='geometry'), nullable=True),
                    sa.ForeignKeyConstraint(['threshold'], ['advisory_hfi_classification_threshold.id'], ),
                    sa.PrimaryKeyConstraint('id'),
                    comment='HFI classification for some forecast/advisory run on some day, for some date'
                    )
    op.create_index('idx_advisory_classified_hfi_geom', 'advisory_classified_hfi',
                    ['geom'], unique=False, postgresql_using='gist')
    op.create_index(op.f('ix_advisory_classified_hfi_id'), 'advisory_classified_hfi', ['id'], unique=False)
    op.create_index(op.f('ix_advisory_classified_hfi_run_type'), 'advisory_classified_hfi', ['run_type'], unique=False)
    op.create_index(op.f('ix_advisory_classified_hfi_threshold'),
                    'advisory_classified_hfi', ['threshold'], unique=False)
    op.drop_index('ix_advisory_fire_zones_id', table_name='advisory_fire_zones')
    op.drop_index('ix_advisory_fire_zones_mof_fire_zone_id', table_name='advisory_fire_zones')
    op.drop_table('advisory_fire_zones')
    # ### end Alembic commands ###
    # Advisory shapes was missing an SRID:
    session = Session(bind=op.get_bind())
    session.execute(sa.text("SELECT UpdateGeometrySRID('advisory_shapes','geom',3005);"))


def downgrade():
    # ### commands auto generated by Alembic ###
    op.create_table('advisory_fire_zones',
                    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
                    sa.Column('mof_fire_zone_id', sa.INTEGER(), autoincrement=False, nullable=False),
                    sa.Column('elevated_hfi_area', postgresql.DOUBLE_PRECISION(
                        precision=53), autoincrement=False, nullable=False),
                    sa.Column('elevated_hfi_percentage', postgresql.DOUBLE_PRECISION(
                        precision=53), autoincrement=False, nullable=False),
                    sa.PrimaryKeyConstraint('id', name='advisory_fire_zones_pkey'),
                    comment='Information about advisories.'
                    )
    op.create_index('ix_advisory_fire_zones_mof_fire_zone_id',
                    'advisory_fire_zones', ['mof_fire_zone_id'], unique=False)
    op.create_index('ix_advisory_fire_zones_id', 'advisory_fire_zones', ['id'], unique=False)
    op.drop_index(op.f('ix_advisory_classified_hfi_threshold'), table_name='advisory_classified_hfi')
    op.drop_index(op.f('ix_advisory_classified_hfi_run_type'), table_name='advisory_classified_hfi')
    op.drop_index(op.f('ix_advisory_classified_hfi_id'), table_name='advisory_classified_hfi')
    op.drop_index('idx_advisory_classified_hfi_geom', table_name='advisory_classified_hfi', postgresql_using='gist')
    op.drop_table('advisory_classified_hfi')
    op.drop_index(op.f('ix_advisory_hfi_classification_threshold_id'),
                  table_name='advisory_hfi_classification_threshold')
    op.drop_table('advisory_hfi_classification_threshold')
    # ### end Alembic commands ###
    # Alembic autogenerate doesn't pick up on the enum, so we have to add it manually:
    sa.Enum(name='runtypeenum').drop(op.get_bind())

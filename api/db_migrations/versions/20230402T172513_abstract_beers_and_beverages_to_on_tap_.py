"""abstract beers and beverages to on-tap map table

Revision ID: e2f049fb8d18
Revises: d3fb27e0ae7d
Create Date: 2023-04-02 17:25:13.921542+01:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e2f049fb8d18'
down_revision = 'd3fb27e0ae7d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('batches',
        sa.Column('created_app', sa.String(), server_default=sa.text("current_setting('application_name')"), nullable=False),
        sa.Column('created_user', sa.String(), server_default=sa.text('CURRENT_USER'), nullable=False),
        sa.Column('created_on', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_app', sa.String(), server_default=sa.text("current_setting('application_name')"), nullable=False),
        sa.Column('updated_user', sa.String(), server_default=sa.text('CURRENT_USER'), nullable=False),
        sa.Column('updated_on', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('id', postgresql.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('tap_id', postgresql.UUID(), nullable=True), #used for migration
        sa.Column('tapped_on', sa.Date(), nullable=True),  #used for migration
        sa.Column('beer_id', postgresql.UUID(), nullable=True),
        sa.Column('beverage_id', postgresql.UUID(), nullable=True),
        sa.Column("external_brewing_tool", sa.String(), nullable=True),
        sa.Column("external_brewing_tool_meta", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("brew_date", sa.Date(), nullable=True),
        sa.Column("keg_date", sa.Date(), nullable=True),
        sa.Column("archived_on", sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(['beer_id'], ['beers.id'], ),
        sa.ForeignKeyConstraint(['beverage_id'], ['beverages.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_batches_beer_id', 'batches', ['beer_id'], unique=False)
    op.create_index('ix_batches_beverage_id', 'batches', ['beverage_id'], unique=False)

    op.create_table('batch_overrides',
        sa.Column('created_app', sa.String(), server_default=sa.text("current_setting('application_name')"), nullable=False),
        sa.Column('created_user', sa.String(), server_default=sa.text('CURRENT_USER'), nullable=False),
        sa.Column('created_on', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_app', sa.String(), server_default=sa.text("current_setting('application_name')"), nullable=False),
        sa.Column('updated_user', sa.String(), server_default=sa.text('CURRENT_USER'), nullable=False),
        sa.Column('updated_on', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('id', postgresql.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('batch_id', postgresql.UUID(), nullable=True),
        sa.Column('key', sa.String(), nullable=False),
        sa.Column('value', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['batch_id'], ['batches.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_batch_overrides_batch_id', 'batch_overrides', ['batch_id'], unique=False)

    op.create_table('on_tap',
        sa.Column('created_app', sa.String(), server_default=sa.text("current_setting('application_name')"), nullable=False),
        sa.Column('created_user', sa.String(), server_default=sa.text('CURRENT_USER'), nullable=False),
        sa.Column('created_on', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_app', sa.String(), server_default=sa.text("current_setting('application_name')"), nullable=False),
        sa.Column('updated_user', sa.String(), server_default=sa.text('CURRENT_USER'), nullable=False),
        sa.Column('updated_on', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('id', postgresql.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('tap_id', postgresql.UUID(), nullable=True), #used for migration
        sa.Column('batch_id', postgresql.UUID(), nullable=True),
        sa.Column('tapped_on', sa.Date(), nullable=True),  
        sa.Column('untapped_on', sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(['batch_id'], ['batches.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_on_tap_batch_id', 'on_tap', ['batch_id'], unique=False)
    
    op.add_column('taps', sa.Column('on_tap_id', postgresql.UUID(), nullable=True))

    op.execute("insert into batches (tap_id, beer_id, beverage_id, tapped_on) (select id, beer_id, beverage_id, now() from taps where not (beer_id is null and beverage_id is null))")
    op.execute("insert into on_tap (batch_id, tap_id, tapped_on) (select id, tap_id, tapped_on from batches)")
    op.execute("update taps set on_tap_id=sq.id from (select id, tap_id from on_tap) AS sq where taps.id=sq.tap_id")
    op.execute("update batches set external_brewing_tool=b.external_brewing_tool, external_brewing_tool_meta=b.external_brewing_tool_meta from (select id, external_brewing_tool, external_brewing_tool_meta from beers) AS b where batches.beer_id=b.id")
    op.execute("update beers set external_brewing_tool=null, external_brewing_tool_meta=null")


    op.drop_index('ix_taps_beer_id', table_name='taps')
    op.drop_index('ix_taps_beverage_id', table_name='taps')
    op.create_index('ix_taps_on_tap_id', 'taps', ['on_tap_id'], unique=False)
    op.drop_constraint('taps_beer_id_fkey', 'taps', type_='foreignkey')
    op.drop_constraint('taps_beverage_id_fkey', 'taps', type_='foreignkey')
    op.create_foreign_key("taps_on_tap_id_fkey", 'taps', 'on_tap', ['on_tap_id'], ['id'])
    op.drop_column('taps', 'beer_id')
    op.drop_column('taps', 'beverage_id')
    op.drop_column('beers', 'brew_date')
    op.drop_column('beers', 'keg_date')
    op.drop_column('beverages', 'brew_date')
    op.drop_column('beverages', 'keg_date')
    op.drop_column('on_tap', 'tap_id')  #only used for migration
    op.drop_column('batches', 'tap_id')  #only used for migration
    op.drop_column('batches', 'tapped_on')  #only used for migration
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute("update beers set external_brewing_tool=b.external_brewing_tool, external_brewing_tool_meta=b.external_brewing_tool_meta from (select distinct beer_id, external_brewing_tool, external_brewing_tool_meta from batches) AS b where beers.id=b.beer_id")

    op.add_column('taps', sa.Column('beverage_id', postgresql.UUID(), autoincrement=False, nullable=True))
    op.add_column('taps', sa.Column('beer_id', postgresql.UUID(), autoincrement=False, nullable=True))
    op.execute("update taps set beer_id=sq.beer_id, beverage_id=sq.beverage_id from (select ot.id, b.beer_id, b.beverage_id from on_tap as ot join batches as b on ot.batch_id=b.id) AS sq where taps.on_tap_id=sq.id")

    op.add_column('beers', sa.Column('brew_date', sa.Date(), nullable=True))
    op.add_column('beers', sa.Column('keg_date', sa.Date(), nullable=True))
    op.execute("update beers set brew_date=sq.brew_date, keg_date=sq.keg_date from (select id, brew_date, keg_date, beer_id from batches) AS sq where beers.id=sq.beer_id")

    op.add_column('beverages', sa.Column('brew_date', sa.Date(), nullable=True))
    op.add_column('beverages', sa.Column('keg_date', sa.Date(), nullable=True))
    op.execute("update beverages set brew_date=sq.brew_date, keg_date=sq.keg_date from (select id, brew_date, keg_date, beverage_id from batches) AS sq where beverages.id=sq.beverage_id")

    op.drop_constraint("taps_on_tap_id_fkey", 'taps', type_='foreignkey')
    op.create_foreign_key('taps_beverage_id_fkey', 'taps', 'beverages', ['beverage_id'], ['id'])
    op.create_foreign_key('taps_beer_id_fkey', 'taps', 'beers', ['beer_id'], ['id'])
    op.drop_index('ix_taps_on_tap_id', table_name='taps')
    op.create_index('ix_taps_beverage_id', 'taps', ['beverage_id'], unique=False)
    op.create_index('ix_taps_beer_id', 'taps', ['beer_id'], unique=False)
    op.drop_column('taps', 'on_tap_id')
    op.drop_index('ix_batches_beverage_id', table_name='batches')
    op.drop_index('ix_batches_beer_id', table_name='batches')
    op.drop_index('ix_batch_overrides_batch_id', table_name='batch_overrides')
    op.drop_table('on_tap')
    op.drop_table('batch_overrides')
    op.drop_table('batches')
    # ### end Alembic commands ###

"""init

Revision ID: 068b0261c11f
Revises: 
Create Date: 2021-07-21 04:26:32.236176+01:00

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "068b0261c11f"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "audit",
        sa.Column("created_app", sa.String(), server_default=sa.text("current_setting('application_name')"), nullable=False),
        sa.Column("created_user", sa.String(), server_default=sa.text("CURRENT_USER"), nullable=False),
        sa.Column("created_on", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_app", sa.String(), server_default=sa.text("current_setting('application_name')"), nullable=False),
        sa.Column("updated_user", sa.String(), server_default=sa.text("CURRENT_USER"), nullable=False),
        sa.Column("updated_on", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("id", postgresql.UUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("content", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "data_changes",
        sa.Column("created_app", sa.String(), server_default=sa.text("current_setting('application_name')"), nullable=False),
        sa.Column("created_user", sa.String(), server_default=sa.text("CURRENT_USER"), nullable=False),
        sa.Column("created_on", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_app", sa.String(), server_default=sa.text("current_setting('application_name')"), nullable=False),
        sa.Column("updated_user", sa.String(), server_default=sa.text("CURRENT_USER"), nullable=False),
        sa.Column("updated_on", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("id", postgresql.UUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("schema", sa.String(), nullable=True),
        sa.Column("table_name", sa.String(), nullable=True),
        sa.Column("operation", sa.String(), nullable=True),
        sa.Column("new", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("old", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "locations",
        sa.Column("created_app", sa.String(), server_default=sa.text("current_setting('application_name')"), nullable=False),
        sa.Column("created_user", sa.String(), server_default=sa.text("CURRENT_USER"), nullable=False),
        sa.Column("created_on", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_app", sa.String(), server_default=sa.text("current_setting('application_name')"), nullable=False),
        sa.Column("updated_user", sa.String(), server_default=sa.text("CURRENT_USER"), nullable=False),
        sa.Column("updated_on", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("id", postgresql.UUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "beers",
        sa.Column("created_app", sa.String(), server_default=sa.text("current_setting('application_name')"), nullable=False),
        sa.Column("created_user", sa.String(), server_default=sa.text("CURRENT_USER"), nullable=False),
        sa.Column("created_on", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_app", sa.String(), server_default=sa.text("current_setting('application_name')"), nullable=False),
        sa.Column("updated_user", sa.String(), server_default=sa.text("CURRENT_USER"), nullable=False),
        sa.Column("updated_on", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("id", postgresql.UUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("external_brewing_tool", sa.String(), nullable=True),
        sa.Column("external_brewing_tool_meta", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("style", sa.String(), nullable=True),
        sa.Column("abv", sa.Float(), nullable=True),
        sa.Column("ibu", sa.Float(), nullable=True),
        sa.Column("srm", sa.Float(), nullable=True),
        sa.Column("img_url", sa.String(), nullable=True),
        sa.Column("brew_date", sa.Date(), nullable=True),
        sa.Column("keg_date", sa.Date(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "sensors",
        sa.Column("created_app", sa.String(), server_default=sa.text("current_setting('application_name')"), nullable=False),
        sa.Column("created_user", sa.String(), server_default=sa.text("CURRENT_USER"), nullable=False),
        sa.Column("created_on", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_app", sa.String(), server_default=sa.text("current_setting('application_name')"), nullable=False),
        sa.Column("updated_user", sa.String(), server_default=sa.text("CURRENT_USER"), nullable=False),
        sa.Column("updated_on", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("id", postgresql.UUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("meta", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("location_id", postgresql.UUID(), nullable=False),
        sa.Column("sensor_type", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["location_id"],
            ["locations.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sensor_location_id", "sensors", ["location_id"], unique=False)
    op.create_table(
        "taps",
        sa.Column("created_app", sa.String(), server_default=sa.text("current_setting('application_name')"), nullable=False),
        sa.Column("created_user", sa.String(), server_default=sa.text("CURRENT_USER"), nullable=False),
        sa.Column("created_on", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_app", sa.String(), server_default=sa.text("current_setting('application_name')"), nullable=False),
        sa.Column("updated_user", sa.String(), server_default=sa.text("CURRENT_USER"), nullable=False),
        sa.Column("updated_on", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("id", postgresql.UUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("tap_number", sa.Integer(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("location_id", postgresql.UUID(), nullable=False),
        sa.Column("tap_type", sa.String(), nullable=False),
        sa.Column("beer_id", postgresql.UUID(), nullable=True),
        sa.Column("sensor_id", postgresql.UUID(), nullable=True),
        sa.ForeignKeyConstraint(
            ["beer_id"],
            ["beers.id"],
        ),
        sa.ForeignKeyConstraint(
            ["location_id"],
            ["locations.id"],
        ),
        sa.ForeignKeyConstraint(
            ["sensor_id"],
            ["sensors.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_taps_beer_id", "taps", ["beer_id"], unique=False)
    op.create_index("ix_taps_location_id", "taps", ["location_id"], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index("ix_taps_location_id", table_name="taps")
    op.drop_index("ix_taps_beer_id", table_name="taps")
    op.drop_index("ix_sensor_location_id", table_name="sensors")
    op.drop_table("taps")
    op.drop_table("sensors")
    op.drop_table("beers")
    op.drop_table("locations")
    op.drop_table("data_changes")
    op.drop_table("audit")
    # ### end Alembic commands ###

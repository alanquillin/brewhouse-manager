"""added-ferm-ctrl-devices-api

Revision ID: a684c1ffb776
Revises: 55e00c2955e5
Create Date: 2022-04-20 20:28:35.759974+01:00

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "a684c1ffb776"
down_revision = "55e00c2955e5"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "fermentation_controller",
        sa.Column("created_app", sa.String(), server_default=sa.text("current_setting('application_name')"), nullable=False),
        sa.Column("created_user", sa.String(), server_default=sa.text("CURRENT_USER"), nullable=False),
        sa.Column("created_on", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_app", sa.String(), server_default=sa.text("current_setting('application_name')"), nullable=False),
        sa.Column("updated_user", sa.String(), server_default=sa.text("CURRENT_USER"), nullable=False),
        sa.Column("updated_on", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("id", postgresql.UUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("manufacturer_id", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("manufacturer", sa.String(), nullable=False),
        sa.Column("model", sa.String(), nullable=False),
        sa.Column("target_temperature", sa.Float(), nullable=True),
        sa.Column("calibration_differential", sa.Float(), nullable=True),
        sa.Column("temperature_precision", sa.Float(), nullable=True),
        sa.Column("cooling_differential", sa.Float(), nullable=True),
        sa.Column("heating_differential", sa.Float(), nullable=True),
        sa.Column("program", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_unique_manufacturer_manufacturer_id_model", "fermentation_controller", ["manufacturer_id", "manufacturer", "model"], unique=True)
    op.create_table(
        "fermentation_controller_stats",
        sa.Column("id", postgresql.UUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("fermentation_controller_id", postgresql.UUID(), nullable=False),
        sa.Column("event_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("temperature", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(
            ["fermentation_controller_id"],
            ["fermentation_controller.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_fermentation_controller_stats_parent_id", "fermentation_controller_stats", ["fermentation_controller_id"], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index("ix_fermentation_controller_stats_parent_id", table_name="fermentation_controller_stats")
    op.drop_table("fermentation_controller_stats")
    op.drop_index("ix_unique_manufacturer_manufacturer_id_model", table_name="fermentation_controller")
    op.drop_table("fermentation_controller")
    # ### end Alembic commands ###

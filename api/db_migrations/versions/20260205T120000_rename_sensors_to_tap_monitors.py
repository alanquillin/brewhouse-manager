"""Rename sensors to tap_monitors

Revision ID: 8a2b3c4d5e6f
Revises: 08ffd519fbca
Create Date: 2026-02-05 12:00:00.000000+00:00

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "8a2b3c4d5e6f"
down_revision = "08ffd519fbca"
branch_labels = None
depends_on = None


def upgrade():
    # Rename the sensors table to tap_monitors
    op.rename_table("sensors", "tap_monitors")

    # Drop the old index and create a new one with the updated name
    op.drop_index("ix_sensor_location_id", table_name="tap_monitors")
    op.create_index("ix_tap_monitor_location_id", "tap_monitors", ["location_id"], unique=False)

    # Rename sensor_type column to monitor_type
    op.alter_column("tap_monitors", "sensor_type", new_column_name="monitor_type")

    # Rename sensor_id column in taps table to tap_monitor_id
    op.alter_column("taps", "sensor_id", new_column_name="tap_monitor_id")

    # Drop and recreate the FK constraint with the updated name
    op.drop_constraint("taps_sensor_id_fkey", "taps", type_="foreignkey")
    op.create_foreign_key(
        "taps_tap_monitor_id_fkey", "taps", "tap_monitors", ["tap_monitor_id"], ["id"]
    )


def downgrade():
    # Drop and recreate the FK constraint with the original name
    op.drop_constraint("taps_tap_monitor_id_fkey", "taps", type_="foreignkey")
    op.create_foreign_key(
        "taps_sensor_id_fkey", "taps", "sensors", ["sensor_id"], ["id"]
    )

    # Rename tap_monitor_id column back to sensor_id in taps table
    op.alter_column("taps", "tap_monitor_id", new_column_name="sensor_id")

    # Rename monitor_type column back to sensor_type
    op.alter_column("tap_monitors", "monitor_type", new_column_name="sensor_type")

    # Drop the new index and recreate the old one
    op.drop_index("ix_tap_monitor_location_id", table_name="tap_monitors")
    op.create_index("ix_sensor_location_id", "tap_monitors", ["location_id"], unique=False)

    # Rename the tap_monitors table back to sensors
    op.rename_table("tap_monitors", "sensors")

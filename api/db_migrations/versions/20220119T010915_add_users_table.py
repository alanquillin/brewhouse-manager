"""add-user-users-table

Revision ID: d92ab9dc026d
Revises: 068b0261c11f
Create Date: 2022-01-19 01:09:15.152340+00:00

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "d92ab9dc026d"
down_revision = "068b0261c11f"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "users",
        sa.Column("created_app", sa.String(), server_default=sa.text("current_setting('application_name')"), nullable=False),
        sa.Column("created_user", sa.String(), server_default=sa.text("CURRENT_USER"), nullable=False),
        sa.Column("created_on", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_app", sa.String(), server_default=sa.text("current_setting('application_name')"), nullable=False),
        sa.Column("updated_user", sa.String(), server_default=sa.text("CURRENT_USER"), nullable=False),
        sa.Column("updated_on", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("id", postgresql.UUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("first_name", sa.String(), nullable=True),
        sa.Column("last_name", sa.String(), nullable=True),
        sa.Column("profile_pic", sa.String(), nullable=True),
        sa.Column("google_oidc_id", sa.String(), nullable=True),
        sa.Column("password_hash", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_email", "users", ["email"], unique=True)
    op.create_index("ix_user_google_oidc_id", "users", ["google_oidc_id"], unique=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index("ix_user_google_oidc_id", table_name="users")
    op.drop_index("ix_user_email", table_name="users")
    op.drop_table("users")
    # ### end Alembic commands ###

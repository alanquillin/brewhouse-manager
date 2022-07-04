"""added brewery link and meta to beverage table

Revision ID: 61c656ff9642
Revises: 902b4fc409a7
Create Date: 2022-06-24 20:44:17.751417+01:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '61c656ff9642'
down_revision = '902b4fc409a7'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('beverages', sa.Column('brewery_link', sa.String(), nullable=True))
    op.add_column('beverages', sa.Column('meta', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('beverages', 'meta')
    op.drop_column('beverages', 'brewery_link')
    # ### end Alembic commands ###

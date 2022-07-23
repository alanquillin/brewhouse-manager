"""add-name-prefix-and-suffix-to-tap

Revision ID: 6c0e4cf18c37
Revises: 61c656ff9642
Create Date: 2022-07-04 02:07:28.745526+01:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6c0e4cf18c37'
down_revision = '61c656ff9642'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('taps', sa.Column('name_prefix', sa.String(), nullable=True))
    op.add_column('taps', sa.Column('name_suffix', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('taps', 'name_suffix')
    op.drop_column('taps', 'name_prefix')
    # ### end Alembic commands ###
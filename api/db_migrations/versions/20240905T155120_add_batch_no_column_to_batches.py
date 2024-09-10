"""add-batch-no-column-to-batches

Revision ID: e3d0e743d284
Revises: e32a62bcc0f5
Create Date: 2024-09-05 15:51:20.800497+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e3d0e743d284'
down_revision = 'e32a62bcc0f5'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('batches', sa.Column('batch_number', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('batches', 'batch_number')
    # ### end Alembic commands ###

from alembic import op
import sqlalchemy as sa

revision = '20251123_01_add_damage_notes'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Add damage_notes column to assignment table"""
    op.add_column(
        'assignment',
        sa.Column('damage_notes', sa.Text(), nullable=True),
    )


def downgrade():
    """Remove damage_notes column from assignment table"""
    op.drop_column('assignment', 'damage_notes')

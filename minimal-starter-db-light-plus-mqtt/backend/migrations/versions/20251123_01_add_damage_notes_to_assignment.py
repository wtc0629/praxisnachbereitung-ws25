"""add damage_notes to assignment

Revision ID: 20251123_01
Revises:
Create Date: 2025-11-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20251123_01'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Fachliche Begründung:
    Bei der Rückgabe eines Geräts muss dokumentiert werden können, ob das Gerät
    beschädigt wurde. Das Feld 'damage_notes' ist optional (NULL erlaubt), da
    nicht bei jeder Rückgabe ein Schaden vorliegt.

    Überlegungen:
    - Name: 'damage_notes' (englisch, konsistent mit 'notes')
    - Typ: TEXT (flexible Länge für detaillierte Schadensbeschreibungen)
    - Optionalität: NULL erlaubt, da Feld nur bei Rückgabe mit Schaden gefüllt wird
    - Platzierung: in 'assignment' Tabelle, da Schäden bei Rückgabe erfasst werden
    """
    op.add_column('assignment', sa.Column('damage_notes', sa.Text(), nullable=True))


def downgrade() -> None:
    """Remove damage_notes column"""
    op.drop_column('assignment', 'damage_notes')

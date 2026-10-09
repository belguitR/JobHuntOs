"""Establish the database migration baseline.

Revision ID: 0001_baseline
Revises:
Create Date: 2026-10-10
"""

from typing import Sequence, Union

revision: str = "0001_baseline"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create no product tables until a context owns them."""


def downgrade() -> None:
    """The baseline deliberately has no schema changes to reverse."""

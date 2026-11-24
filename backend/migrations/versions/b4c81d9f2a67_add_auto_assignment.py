
"""add automatic ticket assignment support

Adds tickets.assignment_source so the system can tell an automatic
assignment apart from one an admin made by hand, and allows
ticket_assignments.assigned_by to be NULL for assignments that no user
performed.

Revision ID: b4c81d9f2a67
Revises: 6013dc830ec6
Create Date: 2026-11-23 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b4c81d9f2a67'
down_revision: Union[str, Sequence[str], None] = '6013dc830ec6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # 1. Record how the ticket's current agent was chosen.
    # NULL means the ticket has never been assigned.
    op.add_column(
        'tickets',
        sa.Column('assignment_source', sa.String(length=10), nullable=True),
    )

    op.create_check_constraint(
        'check_ticket_assignment_source',
        'tickets',
        "assignment_source IN ('AUTO', 'ADMIN')",
    )

    # 2. Existing assignments were made manually by admins.
    op.execute(
        """
        UPDATE tickets
        SET assignment_source = 'ADMIN'
        WHERE assigned_agent_id IS NOT NULL
        """
    )

    # 3. Allow system-created assignment history rows.
    op.alter_column(
        'ticket_assignments',
        'assigned_by',
        existing_type=sa.UUID(),
        nullable=True,
    )


def downgrade() -> None:
    """Downgrade schema."""

    # Remove system-created history rows before restoring NOT NULL.
    op.execute(
        "DELETE FROM ticket_assignments WHERE assigned_by IS NULL"
    )

    op.alter_column(
        'ticket_assignments',
        'assigned_by',
        existing_type=sa.UUID(),
        nullable=False,
    )

    op.drop_constraint(
        'check_ticket_assignment_source',
        'tickets',
        type_='check',
    )

    op.drop_column('tickets', 'assignment_source')

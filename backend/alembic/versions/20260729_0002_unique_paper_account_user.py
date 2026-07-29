"""Allow one paper-trading account per authenticated user.

Revision ID: 20260729_0002
Revises: 20260726_0001
Create Date: 2026-07-29
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260729_0002"
down_revision: str | None = "20260726_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("paper_accounts") as batch_op:
        batch_op.create_unique_constraint(
            "uq_paper_accounts_user_id",
            ["user_id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("paper_accounts") as batch_op:
        batch_op.drop_constraint(
            "uq_paper_accounts_user_id",
            type_="unique",
        )

"""Split notification delivery state from read state."""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b2e1c0d5c0f1"
down_revision = "9d91bdf3a5f0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "notification_outbox",
        sa.Column("delivery_status", sa.Text(), nullable=True, server_default="queued"),
    )
    op.add_column(
        "notification_outbox",
        sa.Column("read_status", sa.Text(), nullable=True, server_default="unread"),
    )
    op.add_column(
        "notification_outbox",
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "notification_outbox",
        sa.Column("last_error", sa.Text(), nullable=True),
    )
    op.add_column(
        "notification_outbox",
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.execute(
        sa.text(
            """
            UPDATE notification_outbox
            SET
                delivery_status = COALESCE(status, 'queued'),
                read_status = COALESCE(read_status, 'unread')
            """
        )
    )

    op.alter_column("notification_outbox", "delivery_status", nullable=False, server_default=None)
    op.alter_column("notification_outbox", "read_status", nullable=False, server_default=None)

    op.drop_column("notification_outbox", "status")


def downgrade() -> None:
    op.add_column(
        "notification_outbox",
        sa.Column("status", sa.Text(), nullable=True, server_default="queued"),
    )

    op.execute(
        sa.text(
            """
            UPDATE notification_outbox
            SET status = COALESCE(delivery_status, 'queued')
            """
        )
    )

    op.alter_column("notification_outbox", "status", nullable=False, server_default=None)

    op.drop_column("notification_outbox", "last_attempt_at")
    op.drop_column("notification_outbox", "last_error")
    op.drop_column("notification_outbox", "read_at")
    op.drop_column("notification_outbox", "read_status")
    op.drop_column("notification_outbox", "delivery_status")

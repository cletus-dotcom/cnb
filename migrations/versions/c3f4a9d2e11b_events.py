"""events

Revision ID: c3f4a9d2e11b
Revises: b7e2a1c0d3f4
Create Date: 2026-04-25 14:50:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "c3f4a9d2e11b"
down_revision = "b7e2a1c0d3f4"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())

    # This migration may be applied on databases that already have the table
    # (e.g. manual creation during development). Make it idempotent.
    if "events" not in tables:
        op.create_table(
            "events",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("title", sa.String(length=220), nullable=False),
            sa.Column("slug", sa.String(length=260), nullable=False),
            sa.Column("summary", sa.String(length=500), nullable=True),
            sa.Column("body", sa.Text(), nullable=False),
            sa.Column("cover_image", sa.String(length=500), nullable=True),
            sa.Column("starts_at", sa.DateTime(), nullable=True),
            sa.Column("ends_at", sa.DateTime(), nullable=True),
            sa.Column("location", sa.String(length=300), nullable=True),
            sa.Column("registration_url", sa.String(length=600), nullable=True),
            sa.Column("is_published", sa.Boolean(), nullable=False),
            sa.Column("published_at", sa.DateTime(), nullable=False),
            sa.Column("author_id", sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(["author_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    # Ensure slug index exists
    existing_indexes = {ix.get("name") for ix in inspector.get_indexes("events")}
    if "ix_events_slug" not in existing_indexes:
        with op.batch_alter_table("events", schema=None) as batch_op:
            batch_op.create_index(batch_op.f("ix_events_slug"), ["slug"], unique=True)


def downgrade():
    with op.batch_alter_table("events", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_events_slug"))
    op.drop_table("events")

